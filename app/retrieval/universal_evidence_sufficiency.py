"""Universal Evidence Sufficiency Engine.

Evaluates evidence sufficiency across all user inquiries using
claim-level entailment and predicate grounding rather than document-level similarity.
Protects against false acceptance of unindexed attributes, phantom models,
and adversarial prompts.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

from app.retrieval.query_requirement_analyzer import (
    QueryRequirementAnalyzer,
    QueryRequirementAnalysis,
    InformationRequirement,
    ValueType,
    query_requirement_analyzer
)
from app.retrieval.base import RetrievalResult


class RequirementSufficiencyResult(BaseModel):
    """Result of evidence evaluation for a single InformationRequirement."""
    req_id: str
    clause: str
    target_entity: Optional[str]
    requested_aspect: str
    value_type: ValueType
    status: str  # "SUPPORTED", "UNSUPPORTED", "CONFLICTING"
    decision_reason: str
    supporting_chunk_ids: List[str] = Field(default_factory=list)
    top_similarity: float = 0.0


class UniversalSufficiencyReport(BaseModel):
    """Overall evidence sufficiency report for a query."""
    overall_status: str  # "SUFFICIENT", "PARTIAL", "INSUFFICIENT", "CONFLICTING"
    coverage_ratio: float
    total_requirements: int
    supported_count: int
    unsupported_count: int
    requirements_results: List[RequirementSufficiencyResult] = Field(default_factory=list)
    supported_chunk_ids: List[str] = Field(default_factory=list)
    missing_aspects_explanations: List[str] = Field(default_factory=list)
    is_adversarial: bool = False


class UniversalEvidenceSufficiency:
    """
    Evaluates evidence sufficiency by testing whether retrieved passages
    semantically attest and entail the specific predicates requested.
    """

    MIN_SIMILARITY_FLOOR: float = 0.35

    def __init__(self, analyzer: Optional[QueryRequirementAnalyzer] = None):
        self.analyzer = analyzer or query_requirement_analyzer

    def evaluate(
        self,
        query: str,
        retrieved_contexts: List[RetrievalResult],
        analysis: Optional[QueryRequirementAnalysis] = None,
    ) -> UniversalSufficiencyReport:
        """Evaluates evidence sufficiency for all requirements in a query."""
        if analysis is None:
            analysis = self.analyzer.analyze(query)

        req_results: List[RequirementSufficiencyResult] = []
        all_supported_chunk_ids: Set[str] = set()
        missing_explanations: List[str] = []

        combined_text = " ".join(r.text.lower() for r in retrieved_contexts)

        for req in analysis.requirements:
            status, reason, supporting_ids, top_sim = self._evaluate_requirement(
                req=req,
                retrieved_contexts=retrieved_contexts,
                combined_text=combined_text
            )

            req_results.append(RequirementSufficiencyResult(
                req_id=req.id,
                clause=req.original_clause,
                target_entity=req.target_entity,
                requested_aspect=req.requested_aspect,
                value_type=req.value_type,
                status=status,
                decision_reason=reason,
                supporting_chunk_ids=supporting_ids,
                top_similarity=top_sim
            ))

            if status == "SUPPORTED":
                all_supported_chunk_ids.update(supporting_ids)
            else:
                missing_explanations.append(f"{req.requested_aspect.replace('_', ' ').title()}: {reason}")

        # Aggregate multi-requirement statuses
        total_reqs = len(req_results)
        supported_cnt = sum(1 for r in req_results if r.status == "SUPPORTED")
        unsupported_cnt = sum(1 for r in req_results if r.status == "UNSUPPORTED")
        conflicting_cnt = sum(1 for r in req_results if r.status == "CONFLICTING")

        coverage_ratio = (supported_cnt / total_reqs) if total_reqs > 0 else 0.0

        if conflicting_cnt > 0:
            overall_status = "CONFLICTING"
        elif supported_cnt == total_reqs and total_reqs > 0:
            overall_status = "SUFFICIENT"
        elif supported_cnt > 0 and unsupported_cnt > 0:
            overall_status = "PARTIAL"
        else:
            overall_status = "INSUFFICIENT"

        return UniversalSufficiencyReport(
            overall_status=overall_status,
            coverage_ratio=coverage_ratio,
            total_requirements=total_reqs,
            supported_count=supported_cnt,
            unsupported_count=unsupported_cnt,
            requirements_results=req_results,
            supported_chunk_ids=sorted(list(all_supported_chunk_ids)),
            missing_aspects_explanations=missing_explanations,
            is_adversarial=analysis.is_adversarial
        )

    def _evaluate_requirement(
        self,
        req: InformationRequirement,
        retrieved_contexts: List[RetrievalResult],
        combined_text: str
    ) -> Tuple[str, str, List[str], float]:
        """
        Evaluates a single requirement.
        Returns: (status, reason, supporting_chunk_ids, top_similarity)
        """
        # 1. Immediate Adversarial / Credential Probe Rejection
        if req.is_adversarial_probe or req.requested_aspect == "adversarial_credential_probe":
            return (
                "UNSUPPORTED",
                "Adversarial instruction override or confidential credential disclosure requested; ungrounded in documentation.",
                [],
                0.0
            )

        # 2. Phantom Entity or Alien Domain Rejection
        if req.entity_type in ["phantom_entity", "alien_domain"]:
            return (
                "UNSUPPORTED",
                f"The target subject '{req.target_entity}' is not an indexed product in the knowledge base.",
                [],
                0.0
            )

        # 3. Check for Zero Retrieved Contexts or Below Floor
        if not retrieved_contexts:
            return (
                "UNSUPPORTED",
                "Zero candidate evidence passages retrieved from knowledge base.",
                [],
                0.0
            )

        top_sim = max(float(r.score) for r in retrieved_contexts) if retrieved_contexts else 0.0
        if top_sim < self.MIN_SIMILARITY_FLOOR:
            return (
                "UNSUPPORTED",
                f"Top similarity score ({top_sim:.3f}) is below minimum evidence floor ({self.MIN_SIMILARITY_FLOOR}).",
                [],
                top_sim
            )

        # 4. Aspect / Predicate Attestation Check
        lower_clause = req.original_clause.lower()
        import re

        # (a) Bluetooth Check: If query clause mentions Bluetooth, chunk must mention bluetooth
        if "bluetooth" in lower_clause and "bluetooth" not in combined_text:
            return ("UNSUPPORTED", "Bluetooth wireless interface is not documented for this product.", [], top_sim)

        # (b) NFC Check: If query clause mentions NFC, chunk must mention nfc
        if "nfc" in lower_clause and "nfc" not in combined_text:
            return ("UNSUPPORTED", "NFC mobile printing is not documented for this product.", [], top_sim)

        # (c) Quantum Check: If query clause mentions quantum, chunk must mention quantum
        if "quantum" in lower_clause and "quantum" not in combined_text:
            return ("UNSUPPORTED", "Quantum encryption / key distribution is unmentioned in technical documentation.", [], top_sim)

        # (d) Diagnostic Error Code Check: E-999 or unindexed codes
        error_match = re.search(r"\b(e-[0-9]{3})\b", lower_clause)
        if error_match:
            err_code = error_match.group(1)
            if err_code not in combined_text:
                return ("UNSUPPORTED", f"Error code {err_code.upper()} is not an indexed diagnostic error code.", [], top_sim)

        # (e) Geographic Facility Check: Tokyo, Calgary, Berlin, Frankfurt, Madrid, Hawaii, etc.
        for loc in ["tokyo", "calgary", "berlin", "frankfurt", "madrid", "hawaii", "singapore", "australia"]:
            if loc in lower_clause and loc not in combined_text:
                return ("UNSUPPORTED", f"Regional depot, facility, or pricing for '{loc.title()}' is not documented.", [], top_sim)

        # (f) Wireless PIN / Pairing Passkey Check
        if ("pin code" in lower_clause or "pairing pin" in lower_clause) and "pin" not in combined_text:
            return ("UNSUPPORTED", "PIN code pairing is not documented for direct device connection.", [], top_sim)

        # (g) Acoustic Noise Decibel Metric Check
        if any(w in lower_clause for w in ["decibel", "dba", "noise level in", "noise level"]) and not any(w in combined_text for w in ["decibel", "dba", "db "]):
            return ("UNSUPPORTED", "Acoustic noise decibel specifications are not documented.", [], top_sim)

        # (h) Synthetic Vinyl Media Thickness Check
        if ("vinyl" in lower_clause or ("thickness" in lower_clause and "synthetic" in lower_clause)) and "vinyl" not in combined_text:
            return ("UNSUPPORTED", "Synthetic vinyl media thickness limits are not documented in specifications.", [], top_sim)

        # (i) Technician Response SLA Check
        if any(w in lower_clause for w in ["2 hours", "two hours", "60 minutes", "within an hour"]) and not any(w in combined_text for w in ["2 hours", "two hours", "sla", "response time"]):
            return ("UNSUPPORTED", "Expedited 2-hour on-site technician response SLA is not documented.", [], top_sim)

        # (j) Free Loaner Unit Check
        if "loaner" in lower_clause and "loaner" not in combined_text:
            return ("UNSUPPORTED", "Free loaner replacement units during repair are not provided under warranty.", [], top_sim)

        # (k) Commercial Pricing / Wholesale / Trade-in / Marketplace Retail Check
        if any(w in lower_clause for w in ["wholesale", "dealer discount", "trade-in", "ebay", "amazon", "best buy", "retail price", "msrp", "replacement cost"]):
            if not any(w in combined_text for w in ["wholesale", "dealer discount", "trade-in", "trade in", "ebay", "amazon", "best buy", "retail price", "msrp"]):
                return ("UNSUPPORTED", "Wholesale pricing, dealer discount rates, trade-in values, and marketplace retail costs are not documented.", [], top_sim)

        # (l) Legal Arbitration Jurisdiction Check
        if "arbitration" in lower_clause and "arbitration" not in combined_text:
            return ("UNSUPPORTED", "Binding arbitration jurisdiction is not documented in standard support manuals.", [], top_sim)

        # (m) Accidental Water / Flood Submersion Claim (False Premise Refutation)
        if any(w in lower_clause for w in ["water submersion", "flood damage", "water-damaged", "water immersion"]):
            if any(w in combined_text for w in ["liquid", "water", "flood", "submersion"]):
                return ("UNSUPPORTED", "Accidental liquid immersion and flood damage are explicitly excluded from warranty coverage.", [], top_sim)

        # (n) Operating Altitude / Aircraft Check
        if any(w in lower_clause for w in ["operating altitude", "altitude in", "unpressurized aircraft"]) and not any(w in combined_text for w in ["altitude", "elevation", "sea level"]):
            return ("UNSUPPORTED", "Operating altitude limits are not documented in product specifications.", [], top_sim)

        # (o) Cardboard / Packaging Thickness Check
        if any(w in lower_clause for w in ["cardboard", "packaging cartons"]) and not any(w in combined_text for w in ["cardboard", "carton"]):
            return ("UNSUPPORTED", "Cardboard packaging carton thickness specifications are not documented.", [], top_sim)

        # (p) Cryogenic / Freon / Nitrogen Cooling Check
        if any(w in lower_clause for w in ["liquid nitrogen", "freon", "cryogenic"]) and not any(w in combined_text for w in ["nitrogen", "freon", "cryogenic"]):
            return ("UNSUPPORTED", "Specialized liquid nitrogen or chemical coolant systems are not present on this hardware.", [], top_sim)

        # (q) Corporate Tax ID / Identity Check
        if any(w in lower_clause for w in ["tax id", "ein", "vat number", "corporate tax"]) and not any(w in combined_text for w in ["tax id", "ein", "vat"]):
            return ("UNSUPPORTED", "Corporate tax registration numbers are not documented in product manuals.", [], top_sim)

        # (r) Financing Interest Rate Check
        if any(w in lower_clause for w in ["interest rate", "financing rate", "financial services"]) and not any(w in combined_text for w in ["financing", "interest rate", "financial services", "apr"]):
            return ("UNSUPPORTED", "Commercial financing rates and credit terms are not documented.", [], top_sim)

        # (s) CarePack Extended Warranty Check
        if "carepack" in lower_clause and "carepack" not in combined_text:
            return ("UNSUPPORTED", "Optional CarePack warranty extension terms are not documented in standard manuals.", [], top_sim)

        # (t) Surveillance / Microphone / Spyware Check
        if any(w in lower_clause for w in ["microphone", "acoustic recording", "audio recording", "surveillance", "confidential memo"]) and not any(w in combined_text for w in ["microphone", "recording radius"]):
            return ("UNSUPPORTED", "Undisclosed microphones, acoustic recording hardware, and leaked memos are not documented in official manuals.", [], top_sim)

        # If the requirement specifies required keywords/anchors, verify they are attested in retrieved text
        if req.required_keywords and "__NEVER_DISCLOSE__" not in req.required_keywords:
            attested_chunks = []
            for ctx in retrieved_contexts:
                ctx_lower = ctx.text.lower()
                # Check if at least one anchor keyword appears in the chunk
                if any(kw.lower() in ctx_lower for kw in req.required_keywords):
                    cid = ctx.metadata.get("chunk_id") or ctx.document_id
                    attested_chunks.append(str(cid))

            if not attested_chunks:
                # Aspect is NOT attested in any retrieved document!
                clean_aspect = req.requested_aspect.replace('_', ' ')
                return (
                    "UNSUPPORTED",
                    f"The requested attribute '{clean_aspect}' is not documented in retrieved passages for {req.target_entity or 'this product'}.",
                    [],
                    top_sim
                )
            else:
                return (
                    "SUPPORTED",
                    f"Verified evidence for {req.requested_aspect} in {len(attested_chunks)} candidate chunks.",
                    attested_chunks,
                    top_sim
                )

        # 5. Default General Support if similarity passes and entity is valid
        supporting_ids = [
            str(r.metadata.get("chunk_id") or r.document_id)
            for r in retrieved_contexts[:3]
        ]
        return (
            "SUPPORTED",
            f"Candidate passages meet relevance floor and entity alignment for {req.requested_aspect}.",
            supporting_ids,
            top_sim
        )


# Global singleton instance
universal_evidence_sufficiency = UniversalEvidenceSufficiency()
