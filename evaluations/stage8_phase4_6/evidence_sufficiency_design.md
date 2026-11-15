# Universal Evidence Sufficiency Engine Design Specification

**Phase**: Stage 8 Phase 4.6  
**Document**: `evidence_sufficiency_design.md`  
**Module**: `app/retrieval/universal_evidence_sufficiency.py`  
**Purpose**: Generalized, mathematically grounded evidence sufficiency evaluation for all user queries. Replaces ad-hoc keyword lists with a multi-stage entailment pipeline.

---

## 1. CHROMADB VECTOR DISTANCE & SIMILARITY INTERPRETATION

### 1.1 Distance Metric Formulation
ChromaDB utilizes the `all-MiniLM-L6-v2` dense embedding space with **Cosine Distance**:
$$\text{Distance}(\mathbf{u}, \mathbf{v}) = 1 - \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2} = 1 - \cos(\theta)$$
where:
- $\text{Cosine Similarity} \in [-1.0, 1.0]$ (typically $[0.0, 1.0]$ for normalized document text).
- $\text{Chroma Distance} \in [0.0, 2.0]$.
- Effective dense similarity score:
  $$S_{\text{dense}} = 1.0 - \text{Distance}$$

### 1.2 Mathematical Floor & Score Calibration
- **Absolute Floor ($S_{\text{floor}} = 0.35$)**: Any candidate passage with $S_{\text{dense}} < 0.35$ is statistically indistinguishable from background noise and is immediately pruned.
- **Top-1 Relevance Threshold ($S_{\text{top1}} = 0.42$)**: Candidate passages must achieve at least $0.42$ dense similarity (or high BM25 rank) to be considered for attribute extraction.
- **Critical Principle**: High similarity is a **necessary** condition for evidence, but **NEVER** a sufficient condition. An evidence passage with similarity $0.65$ that discusses general Wi-Fi setup does not support a claim regarding quantum key distribution.

---

## 2. MULTI-STAGE EVIDENCE ENTAILMENT PIPELINE

For each discrete `InformationRequirement` extracted by `QueryRequirementAnalyzer`:

```
           Candidate Retrieved Passages (Dense + BM25 + RRF)
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │ Stage 1: Entity Alignment & Compatibility    │
        │ - Does the passage mention the target entity?│
        │ - Reject competitor/alien brand substitutes  │
        └──────────────────────┬───────────────────────┘
                               │ (Pass)
                               ▼
        ┌──────────────────────────────────────────────┐
        │ Stage 2: Aspect & Predicate Attestation      │
        │ - Does passage attest the specific aspect?   │
        │ - Anchor token check (e.g., protocol,        │
        │   duration, discount %, error code)          │
        └──────────────────────┬───────────────────────┘
                               │ (Pass)
                               ▼
        ┌──────────────────────────────────────────────┐
        │ Stage 3: Factual Value Entailment            │
        │ - Does passage contain a definitive answer?  │
        │ - Check for unmentioned perils/values        │
        └──────────────────────┬───────────────────────┘
                               │ (Pass)
                               ▼
        ┌──────────────────────────────────────────────┐
        │ Stage 4: Contradiction & Authority Check     │
        │ - Compare assertions across top passages     │
        │ - Resolve via document authority / version   │
        └──────────────────────┬───────────────────────┘
                               │
                               ▼
                  Sub-Requirement Verdict:
            [SUPPORTED, UNSUPPORTED, CONFLICTING]
```

---

## 3. STAGE-BY-STAGE SPECIFICATION

### Stage 1: Entity Alignment
- If `req.target_entity` is specified (e.g., "ApexPrint ProX-400"), candidate passages must contain the entity or its direct aliases ("ProX-400", "this printer" in manual context).
- If the passage solely references an unrelated entity (e.g., "ColorWave 850" when query specifically asks about "EcoTank L3150"), entity match fails.

### Stage 2: Aspect & Predicate Attestation
- Evaluates whether the passage discusses the exact aspect requested:
  - If query asks for `wifi_encryption_protocol`, passage must mention security/encryption terms (`"wpa"`, `"wpa2"`, `"wpa3"`, `"aes"`, `"tkip"`, `"encryption"`, `"security"`, `"tls"`). Merely mentioning `"press WPS button"` fails aspect attestation.
  - If query asks for `wholesale_discount`, passage must contain discount/pricing terms (`"discount"`, `"wholesale"`, `"dealer price"`, `"%"`, `"margin"`). Merely mentioning `"warranty"` fails aspect attestation.
  - If query asks for `acoustic_noise_decibels`, passage must contain acoustic metrics (`"db"`, `"dba"`, `"decibel"`, `"noise level"`, `"acoustic"`).
  - If query asks for `synthetic_vinyl_thickness`, passage must contain media thickness specifications (`"mil"`, `"mm"`, `"gsm"`, `"g/m²"`, `"vinyl"`).

### Stage 3: Factual Value Entailment
- Verifies that the text does not merely state the existence of a category, but provides an actionable answer or explicit rule.
- Explicit exclusions in policy (e.g., *"liquid spills, water immersion, and lightning are excluded from warranty"*) are treated as **SUPPORTED** for exclusion inquiries, and properly refute false coverage claims.

### Stage 4: Multi-Requirement Aggregation
Across all atomic requirements:
- If **ALL** requirements are `SUPPORTED` $\rightarrow$ Overall Status: **`SUFFICIENT`**.
- If **SOME** are `SUPPORTED` and at least one is `UNSUPPORTED` $\rightarrow$ Overall Status: **`PARTIAL`**.
- If **NONE** are `SUPPORTED` $\rightarrow$ Overall Status: **`INSUFFICIENT`**.
- If genuine irreconcilable contradictions exist $\rightarrow$ Overall Status: **`CONFLICTING`**.

---

## 4. PARTIAL ANSWER SYNTHESIS PROTOCOL

When the aggregated status is `PARTIAL`:
1. **Executive Summary / Direct Answer**: Synthesizes clear, grounded factual answers for all `SUPPORTED` requirements, appending explicit bracketed citations `[Source: file, Page: X, Chunk: Y]`.
2. **Missing Information & Limitations**: Explicitly lists every `UNSUPPORTED` requirement with a transparent explanation of what is unmentioned in indexed documentation (e.g., *"The knowledge base does not specify commercial wholesale discount rates or dealer pricing schedules."*).
3. **Verified Citations**: Lists citations exclusively for the supported facts. Zero hallucinated citations for unsupported clauses.
