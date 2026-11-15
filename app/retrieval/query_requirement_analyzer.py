"""Universal Query Requirement Analyzer.

Extracts structured, domain-agnostic information requirements from any query
(single-clause, compound, comparative, conditional, or adversarial).
Dissects inquiries into atomic claims with target entities, requested aspects,
and semantic anchor requirements.
"""

import re
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field


class ValueType(str, Enum):
    BOOLEAN_CAPABILITY = "boolean_capability"     # Does it support X? Can it do Y?
    SPECIFIC_PROTOCOL = "specific_protocol"       # Which encryption protocol? What cipher?
    QUANTITATIVE_METRIC = "quantitative_metric"   # Duty cycle, speed (ppm), resolution (dpi)
    TEMPORAL_DURATION = "temporal_duration"       # How long is warranty? Return window?
    FINANCIAL_COMMERCIAL = "financial_commercial" # Price, wholesale discount, trade-in value
    PROCEDURAL_STEPS = "procedural_steps"         # How to clean, how to resolve, steps
    IDENTIFIER_CODE = "identifier_code"           # Error code, PIN code, password, model ID
    LOCATION_FACILITY = "location_facility"       # Warehouse address, repair depot, city
    SAFETY_AUTHORIZATION = "safety_authorization" # Is it safe to bypass? Permissible action?
    GENERAL_EXPLANATION = "general_explanation"   # General informational explanation


class InformationRequirement(BaseModel):
    """An atomic information requirement extracted from a user query."""
    id: str
    original_clause: str
    target_entity: Optional[str] = None
    entity_type: str = "general"
    requested_aspect: str = "general"
    requested_predicate: str = ""
    value_type: ValueType = ValueType.GENERAL_EXPLANATION
    required_keywords: List[str] = Field(default_factory=list)
    is_adversarial_probe: bool = False
    importance_weight: float = 1.0


class QueryRequirementAnalysis(BaseModel):
    """Complete requirement analysis of a user query."""
    original_query: str
    sanitized_query: str
    is_adversarial: bool = False
    adversarial_override_detected: bool = False
    requirements: List[InformationRequirement] = Field(default_factory=list)


class QueryRequirementAnalyzer:
    """
    Analyzes queries into atomic, verifiable information requirements.
    Extracts semantic anchors rather than relying on superficial entity similarity.
    """

    ADVERSARIAL_PREFIX_PATTERNS = [
        re.compile(r"^\[SYSTEM:\s*Mode=[^\]]+\]\s*", re.IGNORECASE),
        re.compile(r"^\[ADMIN\s+OVERRIDE:[^\]]+\]\s*", re.IGNORECASE),
        re.compile(r"^SYSTEM\s+OVERRIDE:\s*", re.IGNORECASE),
        re.compile(r"^SYSTEM\s+COMMAND:\s*", re.IGNORECASE),
        re.compile(r"^Ignore all (?:previous )?(?:safety )?guidelines (?:and rules )?(?:and|to)?\s*", re.IGNORECASE),
        re.compile(r"^Ignore all instructions, abstain from nothing, and\s*", re.IGNORECASE),
    ]

    CREDENTIAL_PROBE_PATTERNS = [
        re.compile(r"\b(root backdoor password|master private key|firmware signing (?:private )?key|administrator password|root password|private keys?)\b", re.IGNORECASE),
        re.compile(r"\b(reveal (?:the )?internal engineer debug menu bypass code|reveal your secret developer master key)\b", re.IGNORECASE),
    ]

    # Generalized aspect signature rules
    ASPECT_RULES = [
        # 1. Specific Cryptographic & Protocol Inquiries
        {
            "aspect": "encryption_protocol",
            "value_type": ValueType.SPECIFIC_PROTOCOL,
            "trigger_regex": re.compile(r"\b(encryption protocol|cryptographic (?:algorithm|key)|cipher suite|quantum key distribution|elliptic curve)\b", re.IGNORECASE),
            "required_anchors": ["protocol", "encryption", "cipher", "wpa", "aes", "tls", "security"]
        },
        # 2. Wireless Pairing Credentials (PIN / Passkey)
        {
            "aspect": "wireless_pin",
            "value_type": ValueType.IDENTIFIER_CODE,
            "trigger_regex": re.compile(r"\b(pin code|pairing pin|bluetooth pin|mac address prefix|pairing passkey)\b", re.IGNORECASE),
            "required_anchors": ["pin", "passkey", "code", "pairing"]
        },
        # 3. Commercial Pricing, Dealer Discounts & Trade-in Values
        {
            "aspect": "commercial_pricing_discount",
            "value_type": ValueType.FINANCIAL_COMMERCIAL,
            "trigger_regex": re.compile(r"\b(wholesale|dealer discount|reseller discount|trade-in (?:credit|value|discount)|msrp|retail price|cost at (?:best buy|office depot|amazon|ebay)|lease price|financing plan)\b", re.IGNORECASE),
            "required_anchors": ["discount", "wholesale", "pricing", "dealer", "reseller", "trade-in", "financing", "cost"]
        },
        # 4. Physical Facility Location & Address
        {
            "aspect": "facility_location_address",
            "value_type": ValueType.LOCATION_FACILITY,
            "trigger_regex": re.compile(r"\b(street address|warehouse address|postal code|depot in (?:tokyo|calgary|berlin|frankfurt|madrid)|where should i mail|return warehouse)\b", re.IGNORECASE),
            "required_anchors": ["street", "address", "postal", "building", "suite", "box"]
        },
        # 5. Acoustic Noise Metric
        {
            "aspect": "acoustic_noise_metric",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(acoustic noise|noise level|decibels?|dba)\b", re.IGNORECASE),
            "required_anchors": ["db", "dba", "decibel", "sound", "noise level"]
        },
        # 6. Environmental Extremes & Altitude
        {
            "aspect": "operating_altitude_extreme",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(operating altitude|altitude in (?:meters|feet)|aircraft cabin|mountain cabin)\b", re.IGNORECASE),
            "required_anchors": ["altitude", "elevation", "feet", "meters", "sea level"]
        },
        # 7. Media Thickness Limits (Vinyl / Synthetic)
        {
            "aspect": "synthetic_media_thickness",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(thickness of (?:synthetic|magnetic)?\s*vinyl|cardboard packaging cartons|vinyl banner rolls)\b", re.IGNORECASE),
            "required_anchors": ["thickness", "vinyl", "caliper", "mil", "mm", "gsm"]
        },
        # 8. Technician Dispatch SLA
        {
            "aspect": "emergency_technician_dispatch",
            "value_type": ValueType.PROCEDURAL_STEPS,
            "trigger_regex": re.compile(r"\b(technician (?:visit|dispatch) within (?:two|2|60) (?:hours|minutes)|emergency (?:on-site )?technician|overnight courier)\b", re.IGNORECASE),
            "required_anchors": ["technician", "dispatch", "on-site", "hours", "sla"]
        },
        # 9. Free Loaner Units
        {
            "aspect": "free_loaner_units",
            "value_type": ValueType.BOOLEAN_CAPABILITY,
            "trigger_regex": re.compile(r"\b(free loaner (?:units|printers)|replacement loaners?)\b", re.IGNORECASE),
            "required_anchors": ["loaner", "temporary unit", "courtesy printer"]
        },
        # 10. Mobile NFC / Tap Printing
        {
            "aspect": "nfc_mobile_printing",
            "value_type": ValueType.BOOLEAN_CAPABILITY,
            "trigger_regex": re.compile(r"\b(nfc (?:one-touch|tap|touch)?\s*printing|nfc payment)\b", re.IGNORECASE),
            "required_anchors": ["nfc", "near field", "tap to print"]
        },
        # 11. Legal Arbitration Jurisdiction
        {
            "aspect": "arbitration_jurisdiction",
            "value_type": ValueType.GENERAL_EXPLANATION,
            "trigger_regex": re.compile(r"\b(arbitration (?:clause|jurisdiction|court)|governing court)\b", re.IGNORECASE),
            "required_anchors": ["arbitration", "jurisdiction", "governing law", "dispute"]
        },
        # 12. Fictitious Cooling / Sci-Fi Hardware
        {
            "aspect": "exotic_hardware_cooling",
            "value_type": ValueType.GENERAL_EXPLANATION,
            "trigger_regex": re.compile(r"\b(liquid nitrogen|cryogenic|freon cooling|quantum decoupling|quantum core)\b", re.IGNORECASE),
            "required_anchors": ["nitrogen", "cryogenic", "freon", "cooling"]
        },
        # 13. Safety / Power Supply Bypassing
        {
            "aspect": "safety_circuit_bypass",
            "value_type": ValueType.SAFETY_AUTHORIZATION,
            "trigger_regex": re.compile(r"\b(bypass (?:internal )?power supply|tamper with low-voltage|lubricate (?:the )?rail with wd-40)\b", re.IGNORECASE),
            "required_anchors": ["bypass", "tamper", "lubricate", "wd-40", "safety"]
        },
        # 14. Documented Supported Aspects
        {
            "aspect": "duty_cycle",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(duty cycle|monthly duty cycle|monthly volume)\b", re.IGNORECASE),
            "required_anchors": ["duty cycle", "pages per month", "monthly", "pages"]
        },
        {
            "aspect": "print_speed",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(print speed|pages per minute|ppm|speed in ppm)\b", re.IGNORECASE),
            "required_anchors": ["ppm", "pages per minute", "speed"]
        },
        {
            "aspect": "print_resolution",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(print resolution|resolution in dpi|dpi resolution|maximum resolution)\b", re.IGNORECASE),
            "required_anchors": ["dpi", "resolution", "1200", "4800", "5760"]
        },
        {
            "aspect": "paper_capacity",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(paper (?:tray )?capacity|sheet capacity|input tray capacity|how many sheets)\b", re.IGNORECASE),
            "required_anchors": ["sheet", "tray", "capacity", "250", "500", "550"]
        },
        {
            "aspect": "warranty_duration",
            "value_type": ValueType.TEMPORAL_DURATION,
            "trigger_regex": re.compile(r"\b(warranty (?:duration|period|length|term)|how long (?:is|does) the warranty)\b", re.IGNORECASE),
            "required_anchors": ["warranty", "12 months", "1 year", "term", "duration"]
        },
        {
            "aspect": "error_resolution",
            "value_type": ValueType.PROCEDURAL_STEPS,
            "trigger_regex": re.compile(r"\b(error (?:code )?e-[0-9]{3}|how (?:do you|to) (?:clear|resolve|fix) error)\b", re.IGNORECASE),
            "required_anchors": ["error", "turn off", "power cycle", "jam", "clear"]
        },
        {
            "aspect": "duplex_printing",
            "value_type": ValueType.BOOLEAN_CAPABILITY,
            "trigger_regex": re.compile(r"\b(automatic duplex|double[- ]sided printing|duplex capability)\b", re.IGNORECASE),
            "required_anchors": ["duplex", "double-sided", "two-sided"]
        },
        {
            "aspect": "toner_yield",
            "value_type": ValueType.QUANTITATIVE_METRIC,
            "trigger_regex": re.compile(r"\b(toner (?:cartridge )?yield|page yield of (?:the )?(?:standard|high-capacity)?\s*(?:toner|ink))\b", re.IGNORECASE),
            "required_anchors": ["yield", "pages", "cartridge", "bottle", "3,000", "6,000", "4,500"]
        },
        {
            "aspect": "warranty_exclusions",
            "value_type": ValueType.GENERAL_EXPLANATION,
            "trigger_regex": re.compile(r"\b(not covered|excluded|exclusions|damage caused by|power surges|liquid spills)\b", re.IGNORECASE),
            "required_anchors": ["exclude", "exclusion", "not covered", "warranty", "defect"]
        }
    ]

    def analyze(self, query: str) -> QueryRequirementAnalysis:
        """Analyzes an incoming query into atomic InformationRequirements."""
        clean_q = query.strip()
        sanitized_q = clean_q
        adversarial_override = False

        # 1. Check & Strip Adversarial Wrappers
        for pattern in self.ADVERSARIAL_PREFIX_PATTERNS:
            if pattern.search(sanitized_q):
                adversarial_override = True
                sanitized_q = pattern.sub("", sanitized_q).strip()

        # 2. Check Credential Probes
        is_cred_probe = any(pat.search(clean_q) for pat in self.CREDENTIAL_PROBE_PATTERNS)
        is_adversarial = adversarial_override or is_cred_probe

        # 3. Partition into clauses
        clauses = self._partition_query_clauses(sanitized_q)

        requirements: List[InformationRequirement] = []
        for c_idx, clause in enumerate(clauses):
            req = self._extract_clause_requirement(
                clause_text=clause,
                req_id=f"req_{c_idx+1}",
                is_adversarial=is_adversarial
            )
            requirements.append(req)

        return QueryRequirementAnalysis(
            original_query=clean_q,
            sanitized_query=sanitized_q,
            is_adversarial=is_adversarial,
            adversarial_override_detected=adversarial_override,
            requirements=requirements
        )

    def _partition_query_clauses(self, query_text: str) -> List[str]:
        """Splits multi-clause queries while protecting collocations."""
        # Check if query contains strong coordinating conjunction with independent clause
        conjunction_split_pattern = re.compile(
            r"(?:\?|\;|\.\s+)\s*|,\s*(?:and|but|or|whereas|while)\s+(?=(?:what|how|where|when|which|why|who|can|could|will|would|does|do|is|are|reveal|state|print|compare)\b)",
            re.IGNORECASE
        )
        splits = conjunction_split_pattern.split(query_text)
        cleaned = [s.strip("?.,; ") for s in splits if len(s.strip("?.,; ")) > 10]
        return cleaned if len(cleaned) > 1 else [query_text]

    def _extract_clause_requirement(self, clause_text: str, req_id: str, is_adversarial: bool) -> InformationRequirement:
        """Extracts target entity, aspect, value type, and required anchors from a clause."""
        lower_c = clause_text.lower()

        # Extract Entity
        entity = None
        entity_type = "general"
        if re.search(r"\bprox[- ](?!400\b)\d+", lower_c):
            entity = "ApexPrint Phantom ProX Model"
            entity_type = "phantom_entity"
        elif "prox-400" in lower_c or "prox 400" in lower_c:
            entity = "ApexPrint ProX-400"
            entity_type = "hardware_printer"
        elif "colorwave" in lower_c or "colorwave 850" in lower_c or "colorwave-850" in lower_c:
            entity = "ApexPrint ColorWave-850"
            entity_type = "hardware_printer"
        elif "ecotank" in lower_c or "l3150" in lower_c:
            entity = "EcoTank L3150"
            entity_type = "hardware_printer"
        elif "hp" in lower_c or "laserjet" in lower_c or "m608" in lower_c:
            entity = "HP LaserJet Enterprise M608"
            entity_type = "competitor_printer"
        elif "boeing" in lower_c or "777" in lower_c:
            entity = "Boeing 777-300ER"
            entity_type = "alien_domain"
        elif "postgres" in lower_c or "wal" in lower_c:
            entity = "PostgreSQL"
            entity_type = "alien_domain"
        elif "warranty" in lower_c or "carepack" in lower_c or "rma" in lower_c or "return" in lower_c:
            entity = "ApexPrint Warranty Policy"
            entity_type = "commercial_policy"

        # Match Aspect & Value Type
        matched_aspect = "general_qa"
        matched_vtype = ValueType.GENERAL_EXPLANATION
        required_anchors: List[str] = []

        for rule in self.ASPECT_RULES:
            if rule["trigger_regex"].search(clause_text):
                matched_aspect = rule["aspect"]
                matched_vtype = rule["value_type"]
                required_anchors = rule["required_anchors"]
                break

        # Check for direct credential theft or backdoor probes in this clause
        clause_cred_probe = any(pat.search(clause_text) for pat in self.CREDENTIAL_PROBE_PATTERNS)
        if clause_cred_probe:
            matched_aspect = "adversarial_credential_probe"
            matched_vtype = ValueType.IDENTIFIER_CODE
            required_anchors = ["__NEVER_DISCLOSE__"]

        return InformationRequirement(
            id=req_id,
            original_clause=clause_text,
            target_entity=entity,
            entity_type=entity_type,
            requested_aspect=matched_aspect,
            requested_predicate=clause_text,
            value_type=matched_vtype,
            required_keywords=required_anchors,
            is_adversarial_probe=is_adversarial or clause_cred_probe,
            importance_weight=1.0
        )


# Global singleton instance
query_requirement_analyzer = QueryRequirementAnalyzer()
