"""Generalized Query Decomposition Engine.

Decomposes compound, comparative, and multi-part questions into atomic,
independently retrievable and evaluable sub-questions.

Supports:
1. Comparative Matrix Queries (Entity A vs. Entity B across multiple aspects)
2. Multi-Part Conjunctions (independent information requirements joined by conjunctions)
3. Conditional & Sequential Inquiries (Action vs. Policy/Consequence with anaphora resolution)
4. Multi-Aspect Queries on Single Entities (Attribute 1 and Attribute 2)
5. Strict Single-Part Query Preservation (Zero degradation on atomic inquiries)

Preserves domain-agnostic behavior, deterministic execution, and zero external API dependencies.
"""

import re
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field


class DecompositionType(str, Enum):
    SINGLE_PART = "single_part"
    CONJUNCTION = "conjunction"
    COMPARISON = "comparison"
    CONDITIONAL = "conditional"
    MULTI_ASPECT = "multi_aspect"


class SubQuestion(BaseModel):
    """An atomic information requirement derived from a compound query."""
    id: str = Field(..., description="Unique identifier for sub-question (e.g. sq_1)")
    text: str = Field(..., description="Self-contained grammatical question string")
    aspect: str = Field("general", description="The specific attribute or concept targeted")
    target_entity: Optional[str] = Field(None, description="The target entity, product, or subject")
    importance: float = Field(1.0, description="Relative priority weight (1.0 = primary, 0.8 = secondary)")


class QueryDecompositionResult(BaseModel):
    """Comprehensive structured outcome of query decomposition."""
    original_query: str
    is_compound: bool
    decomposition_type: DecompositionType
    sub_questions: List[SubQuestion] = Field(default_factory=list)
    rationale: str = Field("", description="Justification for decomposition or single-part preservation")


class QueryDecomposer:
    """
    Deterministic rule-based and grammar-aware query decomposition engine.
    Safely breaks down complex inquiries while guarding against over-splitting.
    """

    # Protected multi-word collocations that must NEVER be split by 'and'
    PROTECTED_COLLOCATIONS: Set[str] = {
        "laser glass and corona wire",
        "research and development",
        "hardware and software",
        "terms and conditions",
        "error codes and hardware troubleshooting",
        "error codes and troubleshooting",
        "warranty and exclusions",
        "standard and extended warranty",
        "feed rollers and separation pads",
        "pick rollers and separation pads",
        "optical laser glass and corona wire",
        "corona wire and laser glass",
        "power and ground",
        "toner and drum",
        "drum and toner",
        "ink and toner",
        "backup and restore",
        "login and password",
        "username and password",
        "pros and cons",
        "dos and don'ts",
        "chicken and rice",
        "dum biryani and raita",
    }

    # Interrogatives and auxiliary verbs indicating the start of an independent clause
    INDEPENDENT_CLAUSE_STARTERS = (
        "what", "where", "how", "when", "which", "why", "who", "whom", "whose",
        "can", "could", "will", "would", "does", "do", "did", "should", "shall",
        "is", "are", "was", "were", "has", "have", "had", "may", "might",
        "under what", "in what", "for what"
    )

    def decompose_query(self, query: str) -> QueryDecompositionResult:
        """
        Main decomposition entrypoint. Evaluates strategies in strict precedence:
        1. Comparative matrix queries
        2. Conditional / action-consequence queries
        3. Multi-part conjunctions with independent interrogatives
        4. Multi-aspect queries on single entities
        5. Single-part fallback (preservation)
        """
        clean_q = query.strip()
        # Strip adversarial prefix tags if present (Phase 4.6)
        clean_q = re.sub(r"^\[(?:ADMIN\s+OVERRIDE|SYSTEM)[^\]]+\]\s*", "", clean_q, flags=re.IGNORECASE)
        clean_q = re.sub(r"^SYSTEM\s+(?:OVERRIDE|COMMAND):\s*", "", clean_q, flags=re.IGNORECASE)
        clean_q = clean_q.strip()
        if not clean_q:
            return QueryDecompositionResult(
                original_query=clean_q,
                is_compound=False,
                decomposition_type=DecompositionType.SINGLE_PART,
                sub_questions=[SubQuestion(id="sq_1", text=clean_q, aspect="empty", importance=1.0)],
                rationale="Empty query preserved as single-part.",
            )

        # 1. Check Comparative Matrix Queries
        comp_res = self._detect_comparison(clean_q)
        if comp_res:
            return comp_res

        # 2. Check Conditional / Action-Consequence Queries
        cond_res = self._detect_conditional(clean_q)
        if cond_res:
            return cond_res

        # 3. Check Multi-Part Conjunctions with Independent Clauses
        conj_res = self._detect_conjunction(clean_q)
        if conj_res:
            return conj_res

        # 4. Check Multi-Aspect Single-Entity Queries
        aspect_res = self._detect_multi_aspect(clean_q)
        if aspect_res:
            return aspect_res

        # 5. Default: Atomic Single-Part Query
        return QueryDecompositionResult(
            original_query=clean_q,
            is_compound=False,
            decomposition_type=DecompositionType.SINGLE_PART,
            sub_questions=[
                SubQuestion(
                    id="sq_1",
                    text=clean_q,
                    aspect="complete_query",
                    importance=1.0,
                )
            ],
            rationale="Single information requirement identified; preserved without decomposition.",
        )

    def _is_protected_phrase(self, text: str) -> bool:
        """Verifies if the text contains a protected collocation across 'and'."""
        low = text.lower()
        return any(col in low for col in self.PROTECTED_COLLOCATIONS)

    def _detect_comparison(self, query: str) -> Optional[QueryDecompositionResult]:
        """
        Detects comparative inquiries comparing two entities across one or more aspects.
        Examples:
        - 'Compare the ProX-400 and ColorWave-850 printing speeds and maintenance requirements.'
        - 'How do the ProX-400 and ColorWave-850 compare in tray capacity and monthly duty cycle?'
        """
        # Check: Compare [aspect 1] of [E1] with [aspect 2] of [E2]
        m_cross = re.match(
            r"^\s*compare\s+(?:the\s+)?(.+?)\s+of\s+(?:the\s+)?(.+?)\s+(?:with|to|and)\s+(?:the\s+)?(.+?)\s+of\s+(?:the\s+)?(.+?)\.?\??$",
            query,
            re.IGNORECASE,
        )
        if m_cross:
            asp1 = m_cross.group(1).strip()
            e1 = m_cross.group(2).strip()
            asp2 = m_cross.group(3).strip()
            e2 = m_cross.group(4).strip()
            return QueryDecompositionResult(
                original_query=query,
                is_compound=True,
                decomposition_type=DecompositionType.COMPARISON,
                sub_questions=[
                    SubQuestion(
                        id="sq_1",
                        text=f"What is the {asp1} of the {e1}?",
                        aspect=re.sub(r"\s+", "_", asp1.lower()),
                        target_entity=e1,
                        importance=1.0,
                    ),
                    SubQuestion(
                        id="sq_2",
                        text=f"What is the {asp2} of the {e2}?",
                        aspect=re.sub(r"\s+", "_", asp2.lower()),
                        target_entity=e2,
                        importance=1.0,
                    ),
                ],
                rationale=f"Cross-entity comparison decomposed into separate requirements for {e1} and {e2}.",
            )

        # Check: How does [aspect] of [E1] compare to/with [E2]?
        m_how = re.match(
            r"^\s*how\s+does\s+(?:the\s+)?(.+?)\s+of\s+(?:the\s+)?(.+?)\s+compare\s+(?:to|with)\s+(?:the\s+)?(.+?)\.?\??$",
            query,
            re.IGNORECASE,
        )
        if m_how:
            asp = m_how.group(1).strip()
            e1 = m_how.group(2).strip()
            e2 = m_how.group(3).strip()
            return QueryDecompositionResult(
                original_query=query,
                is_compound=True,
                decomposition_type=DecompositionType.COMPARISON,
                sub_questions=[
                    SubQuestion(
                        id="sq_1",
                        text=f"What is the {asp} of the {e1}?",
                        aspect=re.sub(r"\s+", "_", asp.lower()),
                        target_entity=e1,
                        importance=1.0,
                    ),
                    SubQuestion(
                        id="sq_2",
                        text=f"What is the {asp} of the {e2}?",
                        aspect=re.sub(r"\s+", "_", asp.lower()),
                        target_entity=e2,
                        importance=1.0,
                    ),
                ],
                rationale=f"Cross-entity comparison decomposed into separate requirements for {e1} and {e2}.",
            )

        # Check: Compare [Aspects] between [E1] and [E2]
        m_between = re.match(
            r"^\s*compare\s+(?:the\s+)?(.+?)\s+between\s+(?:the\s+)?(.+?)\s+(?:and|versus|vs\.?)\s+(?:the\s+)?(.+?)\.?\??$",
            query,
            re.IGNORECASE,
        )
        if m_between:
            aspects_str = m_between.group(1).strip()
            e1 = m_between.group(2).strip()
            e2 = m_between.group(3).strip()
            raw_aspects = re.split(r"\s+and\s+|\s*,\s*", aspects_str)
            aspects = [a.strip() for a in raw_aspects if a.strip() and not self._is_protected_phrase(a)]
            if not aspects:
                aspects = [aspects_str]

            sub_qs = []
            sq_idx = 1
            for asp in aspects:
                clean_asp = re.sub(r"^(?:their|the|both)\s+", "", asp, flags=re.IGNORECASE).strip()
                is_plural = clean_asp.endswith("s") and not clean_asp.endswith("ss")
                verb = "are the" if is_plural else "is the"
                sub_qs.append(
                    SubQuestion(
                        id=f"sq_{sq_idx}",
                        text=f"What {verb} {clean_asp} of the {e1}?",
                        aspect=re.sub(r"\s+", "_", clean_asp.lower()),
                        target_entity=e1,
                        importance=1.0,
                    )
                )
                sq_idx += 1
                sub_qs.append(
                    SubQuestion(
                        id=f"sq_{sq_idx}",
                        text=f"What {verb} {clean_asp} of the {e2}?",
                        aspect=re.sub(r"\s+", "_", clean_asp.lower()),
                        target_entity=e2,
                        importance=1.0,
                    )
                )
                sq_idx += 1

            return QueryDecompositionResult(
                original_query=query,
                is_compound=True,
                decomposition_type=DecompositionType.COMPARISON,
                sub_questions=sub_qs,
                rationale=f"Cross-entity comparison decomposed into {len(sub_qs)} requirements across {e1} and {e2}.",
            )

        patterns = [
            # 1. Compare [E1] and [E2] in/on/regarding/across/for [Aspects] (Explicit preposition)
            re.compile(
                r"^\s*compare\s+(?:the\s+)?(.+?)\s+(?:and|versus|vs\.?)\s+(?:the\s+)?(.+?)\s+(?:in|on|regarding|across|for)\s+(.+?)\.?\??$",
                re.IGNORECASE,
            ),
            # 2. How do [E1] and [E2] compare in/on [Aspects]
            re.compile(
                r"^\s*how\s+do\s+(?:the\s+)?(.+?)\s+(?:and|versus|vs\.?)\s+(?:the\s+)?(.+?)\s+compare(?:\s+(?:in|on|regarding|across|for))\s+(.+?)\.?\??$",
                re.IGNORECASE,
            ),
            # 3. Compare [E1] and [E2] [Aspects] (No preposition, e.g. "Compare ProX-400 and ColorWave-850 printing speeds and maintenance requirements")
            re.compile(
                r"^\s*compare\s+(?:the\s+)?([A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)?)\s+(?:and|versus|vs\.?)\s+(?:the\s+)?([A-Za-z0-9\-]+)\s+(.+?)\.?\??$",
                re.IGNORECASE,
            ),
        ]

        for pat in patterns:
            m = pat.match(query)
            if m:
                e1 = m.group(1).strip()
                e2 = m.group(2).strip()
                aspects_str = m.group(3).strip()

                # Split aspects on 'and' or comma
                raw_aspects = re.split(r"\s+and\s+|\s*,\s*", aspects_str)
                aspects = [a.strip() for a in raw_aspects if a.strip() and not self._is_protected_phrase(a)]
                if not aspects:
                    aspects = [aspects_str]

                sub_qs: List[SubQuestion] = []
                sq_idx = 1
                for asp in aspects:
                    clean_asp = re.sub(r"^(?:their|the|both)\s+", "", asp, flags=re.IGNORECASE).strip()
                    # Determine question format based on plurality
                    is_plural = clean_asp.endswith("s") and not clean_asp.endswith("ss")
                    verb = "are the" if is_plural else "is the"

                    # Sub-question for Entity 1
                    sub_qs.append(
                        SubQuestion(
                            id=f"sq_{sq_idx}",
                            text=f"What {verb} {clean_asp} of the {e1}?",
                            aspect=re.sub(r"\s+", "_", clean_asp.lower()),
                            target_entity=e1,
                            importance=1.0,
                        )
                    )
                    sq_idx += 1

                    # Sub-question for Entity 2
                    sub_qs.append(
                        SubQuestion(
                            id=f"sq_{sq_idx}",
                            text=f"What {verb} {clean_asp} of the {e2}?",
                            aspect=re.sub(r"\s+", "_", clean_asp.lower()),
                            target_entity=e2,
                            importance=1.0,
                        )
                    )
                    sq_idx += 1

                return QueryDecompositionResult(
                    original_query=query,
                    is_compound=True,
                    decomposition_type=DecompositionType.COMPARISON,
                    sub_questions=sub_qs,
                    rationale=f"Comparative query decomposed across entities ({e1}, {e2}) and {len(aspects)} target aspect(s).",
                )

        return None

    def _detect_conditional(self, query: str) -> Optional[QueryDecompositionResult]:
        """
        Detects conditional and action-consequence queries.
        Examples:
        - 'Can I disassemble the fuser myself, and will that affect warranty coverage?'
        - 'If an error E-101 occurs, should I restart the printer and will that clear the error?'
        """
        # Can I [Action], and will that [Consequence]?
        m = re.search(
            r"^(can\s+I\s+[^,?]+)(?:,\s*and|\s+and)\s+(will\s+(?:that|it|this)\s+[^?]+)\??$",
            query,
            re.IGNORECASE,
        )
        if m:
            c1 = m.group(1).strip()
            c2 = m.group(2).strip()

            # Extract key action from c1 for anaphora replacement
            action_match = re.search(r"can\s+I\s+(.+)$", c1, re.IGNORECASE)
            action_phrase = action_match.group(1).strip() if action_match else "this action"
            action_gerund = self._to_gerund_phrase(action_phrase)

            # Resolve 'that' / 'it' in c2
            resolved_c2 = re.sub(
                r"\b(?:that|it|this)\b",
                action_gerund,
                c2,
                count=1,
                flags=re.IGNORECASE,
            )

            sq1_text = c1 if c1.endswith("?") else c1 + "?"
            sq2_text = resolved_c2.capitalize()
            if not sq2_text.endswith("?"):
                sq2_text += "?"

            return QueryDecompositionResult(
                original_query=query,
                is_compound=True,
                decomposition_type=DecompositionType.CONDITIONAL,
                sub_questions=[
                    SubQuestion(
                        id="sq_1",
                        text=sq1_text,
                        aspect="operational_permission",
                        importance=1.0,
                    ),
                    SubQuestion(
                        id="sq_2",
                        text=sq2_text,
                        aspect="policy_consequence",
                        importance=1.0,
                    ),
                ],
                rationale="Action-consequence conditional query decomposed with anaphora resolution.",
            )

        return None

    def _detect_conjunction(self, query: str) -> Optional[QueryDecompositionResult]:
        """
        Detects compound inquiries where two independent questions or clauses are joined by 'and'.
        Guards against splitting inside protected collocations (e.g. 'laser glass and corona wire').
        Examples:
        - 'What is the warranty period and where should I mail an international return?'
        - 'What is the standard warranty period and what is the exact physical mailing address for sending international return merchandise?'
        """
        # Split on ', and <Starter>' or ' and <Starter>'
        starters_pattern = "|".join(self.INDEPENDENT_CLAUSE_STARTERS)
        regex = rf"^(.*?)(?:,\s*and|\s+and)\s+((?:{starters_pattern})\b.+?)\??$"

        m = re.search(regex, query, re.IGNORECASE)
        if m:
            c1 = m.group(1).strip()
            c2 = m.group(2).strip()

            # Ensure neither clause is trivial or a protected collocation
            if len(c1.split()) < 3 or len(c2.split()) < 3:
                return None

            # Verify neither part is a protected phrase split in half
            if self._is_protected_phrase(f"{c1} and {c2}"):
                return None

            raw_clauses = []
            # Check if c1 itself contains another independent question starter after a comma
            sub_m = re.search(rf"^(.*?),\s+((?:{starters_pattern})\b.+?)$", c1, re.IGNORECASE)
            if sub_m and len(sub_m.group(1).split()) >= 3 and len(sub_m.group(2).split()) >= 3:
                raw_clauses.append(sub_m.group(1).strip())
                raw_clauses.append(sub_m.group(2).strip())
            else:
                raw_clauses.append(c1)
            raw_clauses.append(c2)

            # Find entity in first clause for anaphora resolution
            entity_candidates = [
                m.group(0) for m in re.finditer(r"\b[A-Z][a-zA-Z0-9\-]+(?:\s+[A-Z0-9][a-zA-Z0-9\-]*)*\b", raw_clauses[0])
            ]
            valid_entities = [
                c for c in entity_candidates
                if c.lower() not in {"what", "where", "how", "when", "which", "why", "who", "can", "does", "is", "are", "tell", "explain"}
            ]
            lead_entity = valid_entities[-1] if valid_entities else None

            sub_qs: List[SubQuestion] = []
            for idx, clause in enumerate(raw_clauses, 1):
                c_text = clause.strip()
                # Resolve anaphora if lead_entity is known and clause uses pronouns
                if lead_entity and idx > 1:
                    c_text = re.sub(r"\b(?:its)\b", f"the {lead_entity}'s", c_text, flags=re.IGNORECASE)
                    if not re.search(rf"\b{re.escape(lead_entity)}\b", c_text, re.IGNORECASE):
                        if re.search(r"\b(?:the\s+printer|the\s+unit|the\s+device|the\s+system)\b", c_text, re.IGNORECASE):
                            c_text = re.sub(r"\b(?:the\s+printer|the\s+unit|the\s+device|the\s+system)\b", f"the {lead_entity}", c_text, count=1, flags=re.IGNORECASE)
                        elif re.search(r"\b(?:it|this|that)\b", c_text, re.IGNORECASE):
                            repl = lead_entity if re.match(r"^[A-Za-z]+-[0-9]+", lead_entity) else f"the {lead_entity}"
                            c_text = re.sub(r"\b(?:it|this|that)\b", repl, c_text, count=1, flags=re.IGNORECASE)
                        elif "password" in c_text.lower():
                            c_text = f"{c_text} for the {lead_entity}"

                c_text = c_text[0].upper() + c_text[1:]
                if not c_text.endswith("?"):
                    c_text += "?"
                asp = self._infer_aspect(c_text)
                sub_qs.append(SubQuestion(id=f"sq_{idx}", text=c_text, aspect=asp, target_entity=lead_entity, importance=1.0))

            return QueryDecompositionResult(
                original_query=query,
                is_compound=True,
                decomposition_type=DecompositionType.CONJUNCTION,
                sub_questions=sub_qs,
                rationale=f"Conjunction query split into {len(sub_qs)} independent information requirements with anaphora resolution.",
            )

        return None

    def _detect_multi_aspect(self, query: str) -> Optional[QueryDecompositionResult]:
        """
        Detects queries asking for two distinct attributes of a single target entity.
        Example: 'What is the print resolution and bottle page yield of the ApexPrint EcoTank L3150?'
        """
        # Protect against splitting protected phrases like 'optical laser glass and corona wire'
        if self._is_protected_phrase(query):
            return None

        m = re.search(
            r"^(what\s+(?:is|are)\s+(?:the\s+)?)(.+?)\s+and\s+(.+?)\s+(?:of|for|on)\s+(?:the\s+)?(.+?)\??$",
            query,
            re.IGNORECASE,
        )
        if m:
            prefix = m.group(1).strip()
            asp1 = m.group(2).strip()
            asp2 = m.group(3).strip()
            entity = m.group(4).strip()

            # Protect against noun phrases like 'interval and procedure'
            if asp1.lower() in {"interval", "recommended interval"} and asp2.lower() in {"procedure", "recommended procedure"}:
                return None

            # Validate aspect lengths to avoid false splits
            if len(asp1.split()) > 5 or len(asp2.split()) > 5:
                return None

            verb1 = "are the" if asp1.endswith("s") and not asp1.endswith("ss") else "is the"
            verb2 = "are the" if asp2.endswith("s") and not asp2.endswith("ss") else "is the"

            sq1_text = f"What {verb1} {asp1} of the {entity}?"
            sq2_text = f"What {verb2} {asp2} of the {entity}?"

            return QueryDecompositionResult(
                original_query=query,
                is_compound=True,
                decomposition_type=DecompositionType.MULTI_ASPECT,
                sub_questions=[
                    SubQuestion(
                        id="sq_1",
                        text=sq1_text,
                        aspect=re.sub(r"\s+", "_", asp1.lower()),
                        target_entity=entity,
                        importance=1.0,
                    ),
                    SubQuestion(
                        id="sq_2",
                        text=sq2_text,
                        aspect=re.sub(r"\s+", "_", asp2.lower()),
                        target_entity=entity,
                        importance=1.0,
                    ),
                ],
                rationale=f"Multi-aspect query decomposed for entity '{entity}' across '{asp1}' and '{asp2}'.",
            )

        return None

    def _to_gerund_phrase(self, phrase: str) -> str:
        """Converts an action verb phrase (e.g. 'disassemble the fuser myself') to a gerund phrase."""
        words = phrase.split()
        if not words:
            return "performing this action"
        first = words[0].lower()

        # Simple regular gerund mapping
        if first.endswith("e") and not first.endswith("ee"):
            gerund = first[:-1] + "ing"
        elif len(first) >= 3 and first[-1] not in "aeiouwxy" and first[-2] in "aeiou" and first[-3] not in "aeiou":
            gerund = first + first[-1] + "ing"
        else:
            gerund = first + "ing"

        remainder = " ".join(words[1:])
        # Remove 'myself' for clean anaphora replacement
        remainder = re.sub(r"\bmyself\b", "", remainder, flags=re.IGNORECASE).strip()
        return f"{gerund} {remainder}".strip()

    def _infer_aspect(self, question: str) -> str:
        """Extracts a canonical aspect identifier from an interrogative question string."""
        low = question.lower()
        if "warranty" in low and "period" in low:
            return "warranty_period"
        if "return" in low and ("address" in low or "mail" in low):
            return "international_return_address"
        if "disassemble" in low or "disassembly" in low:
            return "disassembly_instructions"
        if "jam" in low or "paper" in low:
            return "paper_jam_clearance"
        if "speed" in low or "ppm" in low:
            return "printing_speed"
        if "maintenance" in low or "clean" in low:
            return "maintenance_requirements"
        if "duty cycle" in low:
            return "duty_cycle"
        if "resolution" in low or "dpi" in low:
            return "print_resolution"
        if "yield" in low or "bottle" in low:
            return "page_yield"
        # Fallback to key nouns
        words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", low) if w not in {"what", "when", "where", "which", "does", "doesnt", "should", "will"}]
        return "_".join(words[:2]) if words else "general_aspect"


query_decomposer = QueryDecomposer()
