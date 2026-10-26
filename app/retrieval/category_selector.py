"""Deterministic category-aware query analysis and multi-category selector.

Classifies incoming user inquiries into one or more relevant knowledge-base categories:
- product_manual: Technical specifications, dimensions, hardware features, yields
- troubleshooting: Error codes, paper jams, Wi-Fi issues, mechanical faults, diagnostics
- warranty: Coverage, standard/extended terms, exclusions, RMA procedure, claims
- faq: General capabilities, mobile printing, routine usage questions, maintenance intervals

Operates deterministically using keyword frequencies, regex patterns, and domain intent scoring
without requiring an external LLM call.
"""

import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field


class CategorySelectionResult(BaseModel):
    """Structured decision record of category selection."""
    query: str
    selected_categories: List[str] = Field(..., description="Ordered list of selected document categories")
    primary_category: Optional[str] = Field(None, description="Dominant category if clearly identified")
    is_multi_category: bool = Field(False, description="True if query spans multiple distinct domains")
    category_scores: Dict[str, float] = Field(default_factory=dict, description="Raw normalized intent scores")
    matched_cues: Dict[str, List[str]] = Field(default_factory=dict, description="Identified keywords/patterns per category")
    decision_reasoning: str = Field("", description="Human-readable explanation of the routing decision")


class CategorySelector:
    """
    Deterministic rule- and lexical-scoring engine for routing customer inquiries
    to relevant documentation categories.
    """

    SUPPORTED_CATEGORIES: Set[str] = {
        "product_manual",
        "troubleshooting",
        "warranty",
        "faq",
    }

    # Lexical patterns and weights for category identification
    CATEGORY_LEXICON: Dict[str, Dict[str, float]] = {
        "troubleshooting": {
            r"\berror\b": 3.0,
            r"\be-\d{3}\b": 4.0,  # e.g., E-101, E-204
            r"\bjam\b": 3.0,
            r"\bpaper jam\b": 4.0,
            r"\boverheat\b": 3.5,
            r"\bfuser\b": 2.5,
            r"\bnot connect(ing)?\b": 3.0,
            r"\bwi-?fi\b": 2.5,
            r"\boffline\b": 3.0,
            r"\bfix\b": 2.0,
            r"\breset\b": 2.5,
            r"\btroubleshoot(ing)?\b": 3.5,
            r"\bissue\b": 2.0,
            r"\bfault\b": 2.5,
            r"\bflashing\b": 2.0,
            r"\bblink(ing)?\b": 2.0,
            r"\bfailed\b": 2.0,
            r"\bwon'?t\b": 2.0,
            r"\bstreak\b": 2.5,
            r"\bsmudge\b": 2.5,
            r"\bstatic ip\b": 3.0,
            r"\bwpa[23]?\b": 3.0,
        },
        "warranty": {
            r"\bwarranty\b": 4.0,
            r"\bguarantee\b": 3.0,
            r"\bcovered\b": 2.5,
            r"\bcoverage\b": 3.0,
            r"\brma\b": 4.0,
            r"\breplacement part\b": 2.5,
            r"\bclaim\b": 2.5,
            r"\brefund\b": 2.5,
            r"\b1-?year\b": 2.5,
            r"\bextended\b": 2.5,
            r"\bexclusion\b": 3.0,
            r"\bexclude(d)?\b": 3.0,
            r"\bvoid\b": 3.5,
            r"\bspill\b": 3.0,
            r"\baccidental\b": 3.0,
            r"\bnon-oem\b": 3.0,
            r"\bthird-?party\b": 2.5,
            r"\bwear and tear\b": 3.0,
            r"\bproof of purchase\b": 3.5,
            r"\breceipt\b": 2.0,
        },
        "product_manual": {
            r"\bspec(ification)?s?\b": 3.5,
            r"\bppm\b": 3.5,
            r"\bdpi\b": 3.0,
            r"\bprint speed\b": 4.0,
            r"\bpages per minute\b": 4.0,
            r"\bprox-?400\b": 2.5,
            r"\bcolorwave\b": 3.0,
            r"\bcolorwave 850\b": 4.0,
            r"\bdimension\b": 3.0,
            r"\bweight\b": 2.5,
            r"\binput tray\b": 2.5,
            r"\btray capacity\b": 3.5,
            r"\bduplex\b": 2.5,
            r"\bpower consumption\b": 3.0,
            r"\bvoltage\b": 2.5,
            r"\bcmyk\b": 3.0,
            r"\bink tank\b": 3.0,
            r"\bcalibrate\b": 2.5,
            r"\bhardware manual\b": 3.5,
            r"\btechnical spec\b": 3.5,
        },
        "faq": {
            r"\bhow do i\b": 2.0,
            r"\bcan i\b": 2.0,
            r"\bdoes it support\b": 2.5,
            r"\bairprint\b": 3.5,
            r"\bmopria\b": 3.5,
            r"\biphone\b": 2.5,
            r"\bandroid\b": 2.5,
            r"\bmobile print(ing)?\b": 3.5,
            r"\bdrum unit\b": 2.5,
            r"\blifecycle\b": 2.5,
            r"\blifespan\b": 2.5,
            r"\bfrequently asked\b": 3.5,
            r"\broutine\b": 2.0,
            r"\bcleaning cycle\b": 2.5,
            r"\bcompatible\b": 2.0,
        },
    }

    def __init__(
        self,
        min_score_threshold: float = 2.0,
        multi_category_ratio: float = 0.5,
    ):
        """
        Args:
            min_score_threshold: Minimum accumulated score required to select a category.
            multi_category_ratio: Threshold ratio of secondary score to top score (e.g. 0.5)
                                  required to include secondary category in multi-category mode.
        """
        self.min_score_threshold = min_score_threshold
        self.multi_category_ratio = multi_category_ratio

    def analyze_query(self, query: str) -> CategorySelectionResult:
        """
        Analyzes the query and returns a structured CategorySelectionResult.
        """
        cleaned_query = query.strip()
        lower_query = cleaned_query.lower()

        scores: Dict[str, float] = {cat: 0.0 for cat in self.SUPPORTED_CATEGORIES}
        matched_cues: Dict[str, List[str]] = {cat: [] for cat in self.SUPPORTED_CATEGORIES}

        # Match lexical patterns
        for cat, patterns in self.CATEGORY_LEXICON.items():
            for pat, weight in patterns.items():
                matches = re.findall(pat, lower_query)
                if matches:
                    scores[cat] += weight * len(matches)
                    matched_cues[cat].append(pat.replace(r"\b", "").replace(r"\?", "?"))

        # Sort categories by descending score
        sorted_cats = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top_cat, top_score = sorted_cats[0]

        selected_categories: List[str] = []

        if top_score >= self.min_score_threshold:
            selected_categories.append(top_cat)
            # Check for secondary and tertiary categories for multi-category queries
            for cat, score in sorted_cats[1:]:
                if (
                    score >= self.min_score_threshold
                    and (score / top_score) >= self.multi_category_ratio
                ):
                    selected_categories.append(cat)
        else:
            # Low confidence or broad query: select all categories to ensure no evidence is missed
            selected_categories = list(self.SUPPORTED_CATEGORIES)

        is_multi = len(selected_categories) > 1 and top_score >= self.min_score_threshold

        # Reasoning string
        if top_score < self.min_score_threshold:
            reasoning = "Query does not contain distinct category keywords; defaulting to all categories."
        elif is_multi:
            reasoning = (
                f"Multi-domain query detected: primary '{top_cat}' (score {top_score:.1f}) "
                f"with supporting categories {[c for c in selected_categories if c != top_cat]}."
            )
        else:
            reasoning = f"Single-domain query routed to primary category '{top_cat}' (score {top_score:.1f})."

        return CategorySelectionResult(
            query=cleaned_query,
            selected_categories=selected_categories,
            primary_category=top_cat if top_score >= self.min_score_threshold else None,
            is_multi_category=is_multi,
            category_scores={k: round(v, 2) for k, v in scores.items()},
            matched_cues={k: v for k, v in matched_cues.items() if v},
            decision_reasoning=reasoning,
        )


category_selector = CategorySelector()
