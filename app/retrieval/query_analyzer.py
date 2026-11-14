"""Generalized Query Understanding, Multi-Intent Analysis, and Routing Engine.

Analyzes user questions to determine:
- Primary and secondary query intents (e.g., ARCHITECTURE, TECHNOLOGY_STACK, BENCHMARK_ANALYSIS,
  FEATURE_EXPLANATION, COMPARISON, NUMERICAL_EXTRACTION, STEP_BY_STEP, TROUBLESHOOTING,
  WARRANTY_POLICY, INTERVIEW_PREP, GENERAL_QA).
- Domain classification: whether the query targets customer-support/hardware troubleshooting
  or general document intelligence/engineering/research.
- Key subjects, entities, and technical terminology extracted from the query.
- Multi-intent / multi-information requirement detection.
- Multi-document / multi-section cross-reference indicator.

Preserves full backward compatibility with CategorySelector for existing customer support queries.
"""

import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from app.retrieval.category_selector import CategorySelector, category_selector


class QueryIntent(BaseModel):
    """Structured representation of an identified query intent with confidence score."""
    name: str = Field(..., description="Canonical intent name (e.g., architecture, benchmark_analysis)")
    confidence: float = Field(..., description="Normalized confidence score (0.0 to 1.0)")
    matched_cues: List[str] = Field(default_factory=list, description="Specific terms that triggered this intent")


class QueryAnalysisResult(BaseModel):
    """Comprehensive decision and semantic record of query analysis."""
    query: str
    primary_intent: str = Field("general_qa", description="Dominant identified intent")
    intents: List[QueryIntent] = Field(default_factory=list, description="All detected intents with scores")
    is_customer_support: bool = Field(False, description="True if query specifically targets printer/hardware support")
    extracted_subjects: List[str] = Field(default_factory=list, description="Extracted technical concepts, entities, and keywords")
    is_multi_requirement: bool = Field(False, description="True if query contains multiple distinct information requirements")
    requires_cross_reference: bool = Field(False, description="True if answering requires multiple sections or documents")
    category_preferences: List[str] = Field(default_factory=list, description="Target document categories if domain-specific, empty if broad/unconstrained")
    soft_preference_only: bool = Field(True, description="True if category preferences should act as soft boost rather than hard exclusion")
    decision_reasoning: str = Field("", description="Human-readable explanation of the understanding decision")


class QueryAnalyzer:
    """
    General-purpose query understanding engine supporting both broad document intelligence
    and domain-specific customer support inquiries.
    """

    INTENT_LEXICON: Dict[str, Dict[str, float]] = {
        "architecture": {
            r"\barchitect(ure)?\b": 4.0,
            r"\bsystem design\b": 4.0,
            r"\bpresentation layer\b": 3.5,
            r"\bcomponent(s)?\b": 3.0,
            r"\blayer(s)?\b": 3.0,
            r"\bdata flow\b": 3.0,
            r"\bpipeline\b": 3.0,
            r"\bdiagram\b": 2.5,
            r"\bhigh-?level\b": 2.5,
            r"\bmodule(s)?\b": 2.5,
            r"\bbackend architecture\b": 4.0,
            r"\bfrontend architecture\b": 4.0,
        },
        "technology_stack": {
            r"\btech(nology)?\s+stack\b": 4.0,
            r"\btechnolog(y|ies)\b": 3.0,
            r"\bframework(s)?\b": 3.0,
            r"\blibrar(y|ies)\b": 2.5,
            r"\bpython\b": 3.0,
            r"\bfastapi\b": 3.5,
            r"\breact\b": 3.5,
            r"\btypescript\b": 3.0,
            r"\btailwind(css)?\b": 3.0,
            r"\bchromadb\b": 3.5,
            r"\bvite\b": 2.5,
            r"\bpydantic\b": 2.5,
            r"\bdependencies\b": 2.5,
        },
        "benchmark_analysis": {
            r"\bbenchmark(s)?\b": 4.0,
            r"\bevaluation\b": 3.5,
            r"\bmetrics?\b": 3.0,
            r"\blatenc(y|ies)\b": 3.0,
            r"\baccuracy\b": 3.0,
            r"\bprecision\b": 3.0,
            r"\brecall\b": 3.0,
            r"\bmrr\b": 3.5,
            r"\bhit[- ]rate\b": 3.5,
            r"\btest results?\b": 3.0,
            r"\bgroundedness ratio\b": 3.5,
            r"\bperformance results?\b": 3.5,
        },
        "feature_explanation": {
            r"\bmulti[- ]context prompting\b": 4.5,
            r"\bmcp\b": 3.5,
            r"\bcitation validation\b": 4.0,
            r"\bhybrid retrieval\b": 3.5,
            r"\breciprocal rank fusion\b": 4.0,
            r"\brrf\b": 3.0,
            r"\bhow does .* work\b": 3.0,
            r"\bwhat is\b": 2.0,
            r"\bexplain\b": 2.0,
            r"\bconcept\b": 2.5,
            r"\bprompt injection defense\b": 4.0,
        },
        "comparison": {
            r"\bcompare\b": 4.0,
            r"\bcomparison\b": 4.0,
            r"\bvs\.?\b": 3.5,
            r"\bdifference(s)? between\b": 4.0,
            r"\bbaseline (vs|and) mcp\b": 4.5,
            r"\btrade-?offs?\b": 3.5,
            r"\bpros and cons\b": 3.5,
            r"\badvantages?\b": 2.5,
        },
        "numerical_extraction": {
            r"\bhow many\b": 3.0,
            r"\bnumbers?\b": 2.5,
            r"\bpercentage\b": 3.0,
            r"\bstorage budget\b": 4.0,
            r"\b1024\s*mb\b": 4.0,
            r"\b1\s*gb\b": 3.5,
            r"\bthreshold\b": 3.0,
            r"\blimit(s)?\b": 2.5,
            r"\bchunk size\b": 3.5,
            r"\boverlap\b": 3.0,
        },
        "step_by_step": {
            r"\bstep[- ]by[- ]step\b": 4.0,
            r"\bhow to\b": 2.5,
            r"\bprocedure\b": 3.0,
            r"\binstructions\b": 3.0,
            r"\bworkflow\b": 3.0,
            r"\bguide\b": 2.5,
            r"\bsetup\b": 2.5,
            r"\binstall(ation)?\b": 3.0,
        },
        "interview_prep": {
            r"\binterview\b": 4.5,
            r"\belevator pitch\b": 4.0,
            r"\bengineering decisions?\b": 4.0,
            r"\barchitectural decisions?\b": 4.0,
            r"\bcore challenges?\b": 3.5,
            r"\btechnical interview\b": 4.5,
        },
        "troubleshooting": {
            r"\berror\b": 3.0,
            r"\be-\d{3}\b": 4.0,
            r"\bjam\b": 3.5,
            r"\bpaper jam\b": 4.0,
            r"\boverheat\b": 3.5,
            r"\bfuser\b": 3.0,
            r"\bnot connect(ing)?\b": 3.0,
            r"\bwi-?fi\b": 2.5,
            r"\boffline\b": 3.0,
            r"\bfix\b": 2.0,
            r"\breset\b": 2.5,
            r"\btroubleshoot(ing)?\b": 3.5,
            r"\bfault\b": 2.5,
            r"\bstreak\b": 2.5,
            r"\bsmudge\b": 2.5,
        },
        "warranty_policy": {
            r"\bwarranty\b": 4.0,
            r"\bguarantee\b": 3.0,
            r"\bcovered\b": 2.5,
            r"\bcoverage\b": 3.0,
            r"\brma\b": 4.0,
            r"\breplacement part\b": 2.5,
            r"\bclaim\b": 2.5,
            r"\brefund\b": 2.5,
            r"\bextended warranty\b": 3.5,
            r"\bexclusion\b": 3.0,
            r"\bvoid\b": 3.5,
        },
    }

    # Lexical triggers indicating hardware printer support specifically
    CUSTOMER_SUPPORT_CUES: Set[str] = {
        "prox-400",
        "prox400",
        "colorwave",
        "colorwave 850",
        "colorwave850",
        "ecotank",
        "ecotank l3150",
        "toner",
        "cartridge",
        "fuser",
        "drum unit",
        "feed tray",
        "printhead",
        "print head",
        "cmyk",
        "paper jam",
        "rma",
        "duplexer",
        "ppm",
        "airprint",
        "mopria",
    }

    KNOWN_ENTITIES: List[str] = [
        "multi-context prompting",
        "reciprocal rank fusion",
        "citation validation",
        "prompt injection defense",
        "hybrid retrieval",
        "vector database",
        "bm25",
        "chromadb",
        "fastapi",
        "react",
        "typescript",
        "tailwind",
        "vite",
        "all-minilm-l6-v2",
        "mistral-7b",
        "apexprint",
        "prox-400",
        "colorwave 850",
        "ecotank l3150",
        "error e-101",
        "error e-204",
        "storage budget",
        "1024 mb",
    ]

    def __init__(self, category_delegate: Optional[CategorySelector] = None):
        self.category_delegate = category_delegate or category_selector

    def analyze_query(self, query: str) -> QueryAnalysisResult:
        """
        Analyzes the query and returns a structured QueryAnalysisResult.
        """
        cleaned_query = query.strip()
        lower_query = cleaned_query.lower()

        # 1. Detect Intents
        intent_scores: Dict[str, float] = {}
        intent_cues: Dict[str, List[str]] = {}

        for intent_name, patterns in self.INTENT_LEXICON.items():
            score = 0.0
            cues = []
            for pat, weight in patterns.items():
                matches = re.findall(pat, lower_query)
                if matches:
                    score += weight * len(matches)
                    clean_cue = pat.replace(r"\b", "").replace(r"\?", "?").replace(r"(s)?", "s").replace(r"(-)?", "-")
                    cues.append(clean_cue)
            if score > 0.0:
                intent_scores[intent_name] = score
                intent_cues[intent_name] = cues

        intents_list: List[QueryIntent] = []
        if intent_scores:
            max_score = max(intent_scores.values())
            sorted_intents = sorted(intent_scores.items(), key=lambda kv: kv[1], reverse=True)
            for name, score in sorted_intents:
                conf = min(1.0, score / max(1.0, max_score))
                intents_list.append(QueryIntent(
                    name=name,
                    confidence=round(conf, 3),
                    matched_cues=intent_cues.get(name, []),
                ))
            primary_intent = sorted_intents[0][0]
        else:
            primary_intent = "general_qa"
            intents_list.append(QueryIntent(
                name="general_qa",
                confidence=1.0,
                matched_cues=[],
            ))

        # 2. Extract Technical Subjects & Entities
        extracted_subjects: List[str] = []
        for ent in self.KNOWN_ENTITIES:
            if ent in lower_query:
                extracted_subjects.append(ent)

        # Also extract quoted phrases or capitalized tech words
        quoted = re.findall(r'["\']([^"\']+)["\']', cleaned_query)
        for q in quoted:
            if q.lower() not in [s.lower() for s in extracted_subjects]:
                extracted_subjects.append(q)

        # 3. Check Domain: Customer Support vs General Document Intelligence
        has_printer_hardware_cue = any(
            bool(re.search(r"\b" + re.escape(cue) + r"\b", lower_query))
            for cue in self.CUSTOMER_SUPPORT_CUES
        )
        has_error_code = bool(re.search(r"\be-\d{3}\b", lower_query))
        
        # Explicit customer support domains
        is_hardware_support_intent = primary_intent in ("troubleshooting", "warranty_policy")
        is_software_or_doc_intent = primary_intent in (
            "architecture", "technology_stack", "benchmark_analysis",
            "feature_explanation", "comparison", "interview_prep"
        )

        if is_software_or_doc_intent and not (has_printer_hardware_cue or has_error_code):
            is_customer_support = False
        elif has_printer_hardware_cue or has_error_code:
            is_customer_support = True
        elif is_hardware_support_intent:
            is_customer_support = True
        else:
            is_customer_support = False

        # 4. Multi-requirement & Cross-reference Detection
        has_conjunction = any(conj in lower_query for conj in [" and ", " as well as ", " along with ", " compare ", " vs ", " both "])
        num_major_intents = sum(1 for item in intents_list if item.confidence >= 0.7)
        is_multi_req = (num_major_intents > 1) or (has_conjunction and len(extracted_subjects) >= 2)
        
        requires_cross_ref = (
            primary_intent == "comparison"
            or (primary_intent in ("architecture", "technology_stack") and "benchmark" in lower_query)
            or ("warranty" in intent_scores and "troubleshooting" in intent_scores)
            or is_multi_req
        )

        # 5. Category Preferences Integration
        category_preferences: List[str] = []
        soft_preference_only = True

        if is_customer_support:
            cat_result = self.category_delegate.analyze_query(cleaned_query)
            category_preferences = cat_result.selected_categories
            # For specific printer queries with clear category, allow soft filtering
            soft_preference_only = False if (cat_result.primary_category and len(category_preferences) <= 2) else True
            reasoning = (
                f"Customer support query identified with primary intent '{primary_intent}'. "
                f"Routed to category preferences {category_preferences}."
            )
        else:
            # For general document intelligence queries, do not constrain by customer-support categories
            category_preferences = []
            soft_preference_only = True
            reasoning = (
                f"General document intelligence query identified with primary intent '{primary_intent}'. "
                f"Unconstrained retrieval across all indexed documents."
            )

        return QueryAnalysisResult(
            query=cleaned_query,
            primary_intent=primary_intent,
            intents=intents_list,
            is_customer_support=is_customer_support,
            extracted_subjects=extracted_subjects,
            is_multi_requirement=is_multi_req,
            requires_cross_reference=requires_cross_ref,
            category_preferences=category_preferences,
            soft_preference_only=soft_preference_only,
            decision_reasoning=reasoning,
        )


query_analyzer = QueryAnalyzer()
