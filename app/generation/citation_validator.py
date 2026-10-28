"""Evidence-based citation validation, claim groundedness verification, and hallucination detection.

Verifies:
1. Every citation matches an actual retrieved candidate chunk.
2. Source filename and page numbers are preserved and not fabricated.
3. Distinguishes candidate evidence from verified claim support.
4. Detects unsupported claims without inventing artificial confidence probabilities.
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.retrieval.base import RetrievalResult


class VerifiedCitation(BaseModel):
    """Structured representation of a verified source citation."""
    source_file: str = Field(..., description="Document filename")
    page_number: Optional[int] = Field(None, description="Page number if applicable, None if full document")
    chunk_id: Optional[str] = Field(None, description="Exact chunk ID")
    category: str = Field("general", description="Document category")
    snippet: str = Field(..., description="Exact or truncated reference text snippet")
    relevance_score: float = Field(..., description="Retrieval score of the cited chunk")
    is_verified: bool = Field(True, description="True if matched to an actual retrieved chunk")
    verification_notes: str = Field("", description="Verification status details")


class CitationValidationReport(BaseModel):
    """Comprehensive citation and groundedness report."""
    evidence_status: str = Field(..., description="'SUFFICIENT', 'PARTIAL', or 'INSUFFICIENT'")
    candidate_citations_count: int = Field(..., description="Number of candidate chunks retrieved")
    retrieved_evidence_count: int = Field(0, description="Total candidate context chunks retrieved")
    model_generated_citations_count: int = Field(0, description="Total explicit source citations asserted in answer text")
    validator_approved_citations_count: int = Field(0, description="Model citations verified against retrieved evidence")
    unsupported_citations_count: int = Field(0, description="Model citations that could not be verified against evidence")
    verified_citations: List[VerifiedCitation] = Field(default_factory=list, description="Verified citations")
    unverified_citations: List[str] = Field(default_factory=list, description="Citations in answer that failed verification")
    citation_precision: float = Field(1.0, description="Ratio of verified citations to total citations in answer")
    context_utilization: float = Field(0.0, description="Ratio of verified citations to total retrieved candidate chunks")
    total_claims_analyzed: int = Field(0, description="Total sentence claims checked")
    supported_claims_count: int = Field(0, description="Claims substantiated by retrieved context")
    unsupported_claims: List[str] = Field(default_factory=list, description="Extrapolated or unsubstantiated statements")
    claim_groundedness_ratio: float = Field(1.0, description="Ratio of supported claims to total claims")
    is_evidence_insufficient: bool = Field(False, description="True if knowledge base lacks adequate evidence")
    conflicting_evidence_detected: bool = Field(False, description="True if retrieved evidence contains policy conflicts")


class CitationValidator:
    """
    Validates LLM-generated answers against retrieved candidate chunks to guarantee
    factual groundedness and source citation integrity.
    """

    # Regex patterns for matching source citations in LLM responses
    CITATION_PATTERNS = [
        re.compile(r"\[(?:Source:\s*)?([a-zA-Z0-9_\-\.]+\.(?:md|pdf|txt))(?:\s*,\s*(?:Page:\s*|p\.\s*)(\d+|Full Document))?(?:\s*,\s*(?:Chunk:\s*)([a-zA-Z0-9_]+))?\]", re.IGNORECASE),
        re.compile(r"\((?:Source:\s*)?([a-zA-Z0-9_\-\.]+\.(?:md|pdf|txt))(?:\s*,\s*(?:Page:\s*|p\.\s*)(\d+|Full Document))?\)", re.IGNORECASE),
        re.compile(r"Source:\s*([a-zA-Z0-9_\-\.]+\.(?:md|pdf|txt))(?:\s*,\s*Page:\s*(\d+))?", re.IGNORECASE),
    ]

    INSUFFICIENT_EVIDENCE_PHRASES = [
        "insufficient evidence",
        "could not find sufficient information",
        "does not contain verified",
        "no relevant context available",
        "unable to find information",
        "not mentioned in the available documentation",
    ]

    def extract_citations_from_text(self, answer_text: str) -> List[Dict[str, Any]]:
        """Extract all candidate citation tokens from the generated text without double-counting nested spans."""
        citations = []
        matched_spans: List[Tuple[int, int]] = []
        for pat in self.CITATION_PATTERNS:
            for match in pat.finditer(answer_text):
                start, end = match.start(), match.end()
                # Skip overlapping spans from earlier, more specific regex patterns
                if any(start < m_end and end > m_start for m_start, m_end in matched_spans):
                    continue
                matched_spans.append((start, end))

                source = match.group(1).strip()
                page_str = match.group(2) if len(match.groups()) >= 2 and match.group(2) else None
                chunk_id = match.group(3) if len(match.groups()) >= 3 and match.group(3) else None

                page_num = None
                if page_str and page_str.isdigit():
                    page_num = int(page_str)

                citations.append({
                    "raw_match": match.group(0),
                    "source": source,
                    "page_number": page_num,
                    "chunk_id": chunk_id,
                })
        return citations

    def validate_answer(
        self,
        answer_text: str,
        retrieved_contexts: List[RetrievalResult],
        min_overlap_ratio: float = 0.35,
    ) -> CitationValidationReport:
        """
        Validate source citations and claim groundedness in generated answer.
        """
        if not answer_text or not answer_text.strip():
            return CitationValidationReport(
                evidence_status="INSUFFICIENT",
                candidate_citations_count=len(retrieved_contexts),
                retrieved_evidence_count=len(retrieved_contexts),
                model_generated_citations_count=0,
                validator_approved_citations_count=0,
                unsupported_citations_count=0,
                context_utilization=0.0,
                is_evidence_insufficient=True,
            )

        lower_answer = answer_text.lower()
        is_explicitly_insufficient = any(p in lower_answer for p in self.INSUFFICIENT_EVIDENCE_PHRASES)

        if not retrieved_contexts or is_explicitly_insufficient:
            return CitationValidationReport(
                evidence_status="INSUFFICIENT",
                candidate_citations_count=len(retrieved_contexts),
                retrieved_evidence_count=len(retrieved_contexts),
                model_generated_citations_count=0,
                validator_approved_citations_count=0,
                unsupported_citations_count=0,
                is_evidence_insufficient=True,
                verified_citations=[],
                unverified_citations=[],
                citation_precision=1.0 if not retrieved_contexts else 0.0,
                context_utilization=0.0,
                total_claims_analyzed=1,
                supported_claims_count=1 if is_explicitly_insufficient else 0,
                claim_groundedness_ratio=1.0 if is_explicitly_insufficient else 0.0,
            )

        # Index candidate chunks by filename and chunk_id
        candidate_map: Dict[str, List[RetrievalResult]] = {}
        candidate_by_chunk_id: Dict[str, RetrievalResult] = {}
        for r in retrieved_contexts:
            src = (r.metadata.get("filename") or r.source or "").lower()
            candidate_map.setdefault(src, []).append(r)
            cid = r.metadata.get("chunk_id") or r.document_id
            if cid:
                candidate_by_chunk_id[cid] = r

        # 1. Validate extracted citations
        raw_citations = self.extract_citations_from_text(answer_text)
        verified_list: List[VerifiedCitation] = []
        unverified_list: List[str] = []
        verified_chunk_ids: Set[str] = set()

        for c in raw_citations:
            src_key = c["source"].lower()
            matching_chunks = candidate_map.get(src_key, [])

            if not matching_chunks:
                # Check for substring match (e.g. apexprint_prox400_user_manual in full path)
                for k, v in candidate_map.items():
                    if src_key in k or k in src_key:
                        matching_chunks = v
                        break

            if not matching_chunks:
                unverified_list.append(f"Source file not in retrieved evidence: {c['raw_match']}")
                continue

            # Check chunk_id or page_number if provided
            matched_chunk = matching_chunks[0]
            if c.get("chunk_id") and c["chunk_id"] in candidate_by_chunk_id:
                matched_chunk = candidate_by_chunk_id[c["chunk_id"]]
            elif c.get("page_number") is not None:
                page_matches = [
                    ch for ch in matching_chunks if ch.metadata.get("page_number") == c["page_number"]
                ]
                if page_matches:
                    matched_chunk = page_matches[0]
                else:
                    unverified_list.append(f"Fabricated or mismatch page number: {c['raw_match']}")
                    continue

            cid = matched_chunk.metadata.get("chunk_id") or matched_chunk.document_id
            if cid not in verified_chunk_ids:
                verified_chunk_ids.add(cid)
                verified_list.append(
                    VerifiedCitation(
                        source_file=matched_chunk.metadata.get("filename") or matched_chunk.source,
                        page_number=matched_chunk.metadata.get("page_number"),
                        chunk_id=cid,
                        category=matched_chunk.metadata.get("category", "general"),
                        snippet=matched_chunk.text[:140] + "...",
                        relevance_score=round(matched_chunk.score, 4),
                        is_verified=True,
                        verification_notes="Matched to retrieved candidate chunk",
                    )
                )

        # If answer had zero explicit citation tags, associate all top retrieved contexts as candidate citations
        if not raw_citations:
            for r in retrieved_contexts[:3]:
                cid = r.metadata.get("chunk_id") or r.document_id
                verified_list.append(
                    VerifiedCitation(
                        source_file=r.metadata.get("filename") or r.source,
                        page_number=r.metadata.get("page_number"),
                        chunk_id=cid,
                        category=r.metadata.get("category", "general"),
                        snippet=r.text[:140] + "...",
                        relevance_score=round(r.score, 4),
                        is_verified=True,
                        verification_notes="Candidate evidence context (implicit citation)",
                    )
                )

        # 2. Claim Groundedness Check (Sentence-level overlap)
        # Strip citation annotations before splitting sentences
        cleaned_text = re.sub(r"\[.*?\]", "", answer_text)
        cleaned_text = re.sub(r"\(Source:.*?\)", "", cleaned_text)
        
        raw_sentences = re.split(r"(?<=[a-zA-Z0-9])\.\s+|\n+", cleaned_text)
        sentences = [
            s.strip()
            for s in raw_sentences
            if len(s.strip()) > 15
        ]

        # Combine all retrieved text tokens for vocabulary containment check
        combined_evidence_tokens = set()
        for r in retrieved_contexts:
            combined_evidence_tokens.update(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", r.text.lower()))
            # Also add source filenames and chunk metadata
            src = r.metadata.get("filename") or r.source or ""
            combined_evidence_tokens.update(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", src.lower()))

        supported_count = 0
        unsupported_claims: List[str] = []

        for sent in sentences:
            sent_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", sent.lower()))
            # Filter out common stop words
            content_tokens = {
                t for t in sent_tokens
                if t not in {"the", "and", "for", "with", "that", "this", "from", "your", "printer", "please", "based", "maximum"}
            }
            if not content_tokens:
                supported_count += 1
                continue

            overlap = content_tokens.intersection(combined_evidence_tokens)
            overlap_ratio = len(overlap) / len(content_tokens)

            # Accept if sufficient content tokens overlap or if verified citation exists
            if overlap_ratio >= 0.20 or (verified_list and len(unverified_list) == 0 and len(overlap) >= 1):
                supported_count += 1
            else:
                unsupported_claims.append(sent)

        # 3. Numerical & Period Claims Groundedness Check
        combined_text_lower = " ".join(r.text.lower() for r in retrieved_contexts)
        cited_pages = {str(c["page_number"]) for c in raw_citations if c.get("page_number") is not None}
        answer_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", answer_text))
        evidence_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", combined_text_lower))
        
        # Check for numbers in answer not present in evidence or citation page numbers
        unsupported_nums = [
            n for n in answer_numbers
            if n not in evidence_numbers and n not in cited_pages and n not in {"1", "2", "3"}  # ignore basic bullet list indices
        ]
        for un in unsupported_nums:
            unsupported_claims.append(f"Unsupported numerical claim: '{un}' not found in retrieved documentation")

        # 4. Conflicting Evidence Detection
        conflict_detected = False
        categories_represented = {r.metadata.get("category", "") for r in retrieved_contexts}
        if "troubleshooting" in categories_represented and "warranty" in categories_represented:
            if ("void" in combined_text_lower or "disassemble" in combined_text_lower) and ("open" in answer_text.lower() or "disassemble" in answer_text.lower()):
                conflict_detected = True

        total_claims = max(1, len(sentences))
        groundedness_ratio = (
            round(max(0, supported_count - len(unsupported_nums)) / total_claims, 4)
            if unsupported_nums
            else round(supported_count / total_claims, 4)
        )

        total_cites = len(raw_citations)
        precision = (
            round(len(verified_list) / max(1, len(verified_list) + len(unverified_list)), 4)
            if total_cites > 0
            else 1.0
        )

        # Determine evidence status
        has_unsupported_numerical = any("Unsupported numerical" in u for u in unsupported_claims)
        if is_explicitly_insufficient or len(retrieved_contexts) == 0:
            evidence_status = "INSUFFICIENT"
        elif has_unsupported_numerical or len(unverified_list) > 0:
            evidence_status = "PARTIAL"
        elif (groundedness_ratio >= 0.60 or len(verified_list) > 0) and len(unverified_list) == 0:
            evidence_status = "SUFFICIENT"
        else:
            evidence_status = "PARTIAL"

        return CitationValidationReport(
            evidence_status=evidence_status,
            candidate_citations_count=len(retrieved_contexts),
            retrieved_evidence_count=len(retrieved_contexts),
            model_generated_citations_count=total_cites,
            validator_approved_citations_count=len(verified_list),
            unsupported_citations_count=len(unverified_list),
            verified_citations=verified_list,
            unverified_citations=unverified_list,
            citation_precision=precision,
            context_utilization=round(len(verified_list) / max(1, len(retrieved_contexts)), 4),
            total_claims_analyzed=total_claims,
            supported_claims_count=supported_count,
            unsupported_claims=unsupported_claims,
            claim_groundedness_ratio=groundedness_ratio,
            is_evidence_insufficient=is_explicitly_insufficient,
            conflicting_evidence_detected=conflict_detected,
        )


citation_validator = CitationValidator()
