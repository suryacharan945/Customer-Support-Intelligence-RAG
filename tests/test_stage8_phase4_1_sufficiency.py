"""Stage 8 Phase 4.1 Regression Tests: Evidence Sufficiency, Entity Compatibility, and Policy Grounding.

Verifies:
1. Calibrated similarity floor (0.2800) properly identifies alien out-of-domain queries.
2. Generalized entity compatibility detects competitor brand mismatches (e.g., HP LaserJet vs. ApexPrint).
3. Generic questions without entity binding are allowed to use generic evidence.
4. Policy / warranty negative-claim handling detects missing clauses and prevents ungrounded answers.
5. End-to-end RAGService accurately abstains on all Phase 4 false-positive queries while preserving supported queries.
"""

import pytest
from app.retrieval.base import RetrievalResult
from app.retrieval.evidence_gate import evidence_gate, EvidenceGate
from app.services.rag_service import rag_service


@pytest.fixture
def sample_prox400_chunk():
    return RetrievalResult(
        document_id="doc_trou_prox400_01",
        text="ApexPrint ProX-400 Paper Jam Recovery: If media jams in the fuser assembly, open Door A and clear the roller path.",
        score=0.62,
        source="apexprint_error_codes_and_hardware_troubleshooting.md",
        metadata={
            "chunk_id": "doc_trou_prox400_01",
            "filename": "apexprint_error_codes_and_hardware_troubleshooting.md",
            "category": "troubleshooting",
            "dense_score": 0.62,
        },
    )


@pytest.fixture
def sample_warranty_chunk():
    return RetrievalResult(
        document_id="doc_warr_std_01",
        text="ApexPrint Limited Warranty covers defects in materials for 1 year. Exclusions include unauthorized disassembly and non-OEM ink cartridges.",
        score=0.65,
        source="apexprint_standard_limited_warranty_policy.md",
        metadata={
            "chunk_id": "doc_warr_std_01",
            "filename": "apexprint_standard_limited_warranty_policy.md",
            "category": "warranty",
            "dense_score": 0.65,
        },
    )


@pytest.fixture
def sample_dossier_chunk():
    return RetrievalResult(
        document_id="doc_dossier_arch_01",
        text="The Customer Support Intelligence Platform integrates Multi-Context Prompting, FastAPI, and ChromaDB vector store.",
        score=0.72,
        source="AI Customer Support Intelligence Platform - Project Dossier.pdf",
        metadata={
            "chunk_id": "doc_dossier_arch_01",
            "filename": "AI Customer Support Intelligence Platform - Project Dossier.pdf",
            "category": "engineering",
            "dense_score": 0.72,
        },
    )


class TestEvidenceGateUnit:
    """Unit tests for EvidenceGate multi-signal decision logic."""

    def test_calibrated_similarity_floor_rejects_sub_threshold(self, sample_prox400_chunk):
        """Alien query with sub-threshold similarity (< 0.28) must be marked INSUFFICIENT."""
        low_score_chunk = RetrievalResult(
            document_id="doc_low_01",
            text="General printer specifications and environmental operating temperatures.",
            score=0.12,
            source="general_specs.md",
            metadata={"dense_score": 0.12, "sparse_score": 0.0},
        )
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="What is the distance between the Earth and the planet Mars at closest approach?",
            retrieved_contexts=[low_score_chunk],
        )
        assert decision.status == "INSUFFICIENT"
        assert decision.similarity_floor_passed is False
        assert "below empirical relevance floor" in decision.decision_reasons[0]
        assert "insufficient evidence" in decision.abstention_message.lower()

    def test_calibrated_similarity_floor_accepts_supported_relevance(self, sample_dossier_chunk):
        """In-domain supported query exceeding similarity floor must pass relevance check."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="Explain the system architecture of this project.",
            retrieved_contexts=[sample_dossier_chunk],
        )
        assert decision.similarity_floor_passed is True
        assert decision.status == "SUFFICIENT"

    def test_entity_compatibility_same_product(self, sample_prox400_chunk):
        """Query targeting ApexPrint ProX-400 with ProX-400 documentation must be COMPATIBLE."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="How do you clear a paper jam on an ApexPrint ProX-400 printer?",
            retrieved_contexts=[sample_prox400_chunk],
        )
        assert decision.entity_result.is_compatible is True
        assert decision.status == "SUFFICIENT"

    def test_entity_compatibility_competitor_mismatch(self, sample_prox400_chunk):
        """Query targeting HP LaserJet with ApexPrint documentation must trigger entity mismatch."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="How do you clear a paper jam on a Hewlett-Packard HP LaserJet Enterprise M608?",
            retrieved_contexts=[sample_prox400_chunk],
        )
        assert decision.status == "INSUFFICIENT"
        assert decision.entity_result.is_compatible is False
        assert any("Entity mismatch" in r for r in decision.decision_reasons)
        assert "m608" in decision.decision_reasons[0].lower() or "hewlett-packard" in decision.decision_reasons[0].lower()

    def test_entity_compatibility_generic_question_allowed(self, sample_prox400_chunk):
        """Generic question without brand binding must be accepted as generic inquiry."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="What causes a paper jam in a laser printer?",
            retrieved_contexts=[sample_prox400_chunk],
        )
        assert decision.entity_result.is_compatible is True
        assert decision.status == "SUFFICIENT"

    def test_entity_compatibility_absent_organization(self, sample_warranty_chunk):
        """Query targeting an organization absent from KB (e.g. Delta Airlines) must trigger entity mismatch."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="What are the rules and baggage allowance policies for transatlantic flights on Delta Airlines?",
            retrieved_contexts=[sample_warranty_chunk],
        )
        assert decision.status == "INSUFFICIENT"
        assert decision.entity_result.is_compatible is False

    def test_policy_explicit_inclusion_documented(self, sample_warranty_chunk):
        """Query inquiring about documented warranty coverage (1 year materials) is verified as documented."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="Does the ApexPrint limited warranty cover defects in materials?",
            retrieved_contexts=[sample_warranty_chunk],
        )
        assert decision.policy_result.is_policy_query is True
        assert decision.policy_result.is_explicitly_documented is True
        assert decision.status == "SUFFICIENT"

    def test_policy_explicit_exclusion_documented(self, sample_warranty_chunk):
        """Query inquiring about documented exclusion (unauthorized disassembly) is verified as documented."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="Does the warranty policy exclude damage from unauthorized disassembly?",
            retrieved_contexts=[sample_warranty_chunk],
        )
        assert decision.policy_result.is_policy_query is True
        assert decision.policy_result.is_explicitly_documented is True
        assert decision.status == "SUFFICIENT"

    def test_policy_missing_clause_triggers_abstention(self, sample_warranty_chunk):
        """Query inquiring about unmentioned perils (meteor strikes, nuclear radiation) must trigger abstention."""
        decision = evidence_gate.evaluate_evidence_sufficiency(
            query="Does the ApexPrint warranty policy cover damage caused by extraterrestrial meteor strikes or nuclear radiation?",
            retrieved_contexts=[sample_warranty_chunk],
        )
        assert decision.status == "INSUFFICIENT"
        assert decision.policy_result.is_policy_query is True
        assert decision.policy_result.is_explicitly_documented is False
        assert any("meteor" in m for m in decision.policy_result.missing_conditions)
        assert any("nuclear" in m for m in decision.policy_result.missing_conditions)
        assert "not documented" in decision.decision_reasons[0].lower()


@pytest.mark.asyncio
class TestRAGServiceSufficiencyIntegration:
    """End-to-end integration tests through rag_service.process_query()."""

    async def test_p4_q47_hp_laserjet_abstention(self):
        """P4_Q47 (HP LaserJet) must return evidence_status='INSUFFICIENT' and honest abstention text."""
        res = await rag_service.process_query(
            "How do you clear a paper jam on a Hewlett-Packard HP LaserJet Enterprise M608?",
            retrieval_mode="multi_context",
        )
        assert res.evidence_status == "INSUFFICIENT"
        assert res.evidence_found is False
        assert len(res.supporting_citations) == 0
        assert "insufficient evidence" in res.answer.lower() or "cannot be safely substituted" in res.answer.lower()

    async def test_p4_q48_mars_distance_abstention(self):
        """P4_Q48 (Earth-Mars distance) must return evidence_status='INSUFFICIENT' due to sub-threshold similarity."""
        res = await rag_service.process_query(
            "What is the distance between the Earth and the planet Mars at closest approach?",
            retrieval_mode="multi_context",
        )
        assert res.evidence_status == "INSUFFICIENT"
        assert res.evidence_found is False
        assert len(res.supporting_citations) == 0
        assert "insufficient evidence" in res.answer.lower()

    async def test_p4_q49_delta_airlines_abstention(self):
        """P4_Q49 (Delta Airlines baggage) must return evidence_status='INSUFFICIENT'."""
        res = await rag_service.process_query(
            "What are the rules and baggage allowance policies for transatlantic flights on Delta Airlines?",
            retrieval_mode="multi_context",
        )
        assert res.evidence_status == "INSUFFICIENT"
        assert res.evidence_found is False
        assert len(res.supporting_citations) == 0
        assert "insufficient evidence" in res.answer.lower()

    async def test_p4_q50_meteor_warranty_abstention(self):
        """P4_Q50 (Meteor strikes warranty) must return evidence_status='INSUFFICIENT' without fabricating clauses."""
        res = await rag_service.process_query(
            "Does the ApexPrint warranty policy cover damage caused by extraterrestrial meteor strikes or nuclear radiation?",
            retrieval_mode="multi_context",
        )
        assert res.evidence_status == "INSUFFICIENT"
        assert res.evidence_found is False
        assert "no terms or clauses were found addressing" in res.answer.lower() or "not specified" in res.answer.lower()

    async def test_p4_q46_biryani_abstention(self):
        """P4_Q46 (Hyderabadi chicken dum biryani) continues to return evidence_status='INSUFFICIENT'."""
        res = await rag_service.process_query(
            "What is the traditional recipe and cooking duration for Hyderabadi chicken dum biryani?",
            retrieval_mode="multi_context",
        )
        assert res.evidence_status == "INSUFFICIENT"
        assert res.evidence_found is False
        assert len(res.supporting_citations) == 0

    async def test_supported_architecture_query_preserved(self):
        """Supported query (P4_Q01 architecture) remains SUFFICIENT with full grounded citations."""
        res = await rag_service.process_query(
            "Explain the complete system architecture of this project.",
            retrieval_mode="multi_context",
        )
        assert res.evidence_status == "SUFFICIENT"
        assert res.evidence_found is True
        assert len(res.supporting_citations) > 0
        assert len(res.answer) > 200

    async def test_supported_printer_query_preserved(self):
        """Supported query (P4_Q03 ProX-400 specs) remains SUFFICIENT with verified citations."""
        res = await rag_service.process_query(
            "What is the monochrome print speed and monthly duty cycle of the ApexPrint ProX-400?",
            retrieval_mode="multi_context",
        )
        assert res.evidence_status == "SUFFICIENT"
        assert res.evidence_found is True
        assert len(res.supporting_citations) > 0
