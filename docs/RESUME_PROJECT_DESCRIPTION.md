# Resume Project Description & Portfolio Highlights

**Project:** Customer Support Intelligence Platform (Evidence-Grounded Document Intelligence)  
**Role:** AI / RAG Systems Engineer & Full-Stack Developer  
**Technologies:** Python, FastAPI, React 18, TypeScript, ChromaDB, SentenceTransformers (`all-MiniLM-L6-v2`), BM25, Mistral-7B, SQLite, Uvicorn, Vite, Tailwind CSS, Pytest, Vitest  

---

## 1. Resume Bullet Points (Tailored for Engineering Roles)

### Option A: AI / Machine Learning Engineer Focus
- Architected an end-to-end evidence-grounded document intelligence platform using **FastAPI**, **React 18**, and **ChromaDB**, integrating dual-channel hybrid retrieval (dense vector embeddings + sparse BM25) fused via **Reciprocal Rank Fusion (RRF, $k=60$)**.
- Engineered a **Universal Evidence Sufficiency Gate** and compound query decomposition pipeline that analyzes entity-aspect coverage across multi-clause questions, eliminating false acceptances on unsupported questions (0/14 false acceptances on held-out blind benchmark).
- Implemented a programmatic **Claim-Level Citation Validator** that cross-examines generated assertions against retrieved text chunks, achieving 100% precision across a 142-claim entailment audit without synthetic mock fallbacks (`ALLOW_MOCK_FALLBACK = False`).
- Designed a decoupled LLM inference architecture supporting local deterministic grounded synthesis and remote GPU-accelerated **Mistral-7B-Instruct-v0.3** inference with automatic failover, achieving $< 1,500\text{ ms}$ average response latency.
- Built a crash-safe backup and disaster recovery framework with automated SQLite integrity validation, adhering to strict $< 1,024\text{ MB}$ local storage budget constraints.
- Validated system robustness across a 233-test backend test suite (100% pass rate) and a 50-query held-out benchmark suite spanning supported, unsupported, compound, and adversarial injection queries.

### Option B: Full-Stack / Backend Systems Engineer Focus
- Developed a high-performance customer support intelligence assistant utilizing **FastAPI (ASGI)**, **Uvicorn**, and **React 18 (TypeScript)** with real-time evidence drawer inspection and multi-context comparative analysis.
- Implemented a robust 6-state document management lifecycle (`uploaded`, `pending_index`, `indexing`, `indexed`, `failed`, `deleted`) with strict searchability gating, preventing unindexed documents from polluting retrieval results.
- Hardened API endpoints against adversarial attacks and infrastructure abuse: enforced path traversal defense, 10 MB payload ceiling, MIME magic byte validation, and preflight CORS policy compliance.
- Orchestrated comprehensive testing pipelines including 233 backend unit/integration tests in Pytest and 12 frontend component tests in Vitest, achieving 100% passing rates.
- Integrated automated storage monitoring and ephemeral caching protocols to guarantee local workspace footprint remained $< 20\text{ MB}$ while archiving persistent snapshots to cloud storage.

---

## 2. Executive Summary (Portfolio / LinkedIn Project Description)

**Customer Support Intelligence Platform** is an enterprise-grade, evidence-grounded document intelligence system designed to answer complex customer inquiries with verifiable citations while strictly abstaining when reference evidence is insufficient.

Unlike generic RAG prototypes that hallucinate answers when knowledge is missing, this platform incorporates an algorithmic **Query Requirement Analyzer**, **Compound Query Decomposer**, and **Universal Evidence Sufficiency Gate**. The system verifies whether candidate documents contain sufficient factual grounding before generation begins. If evidence is lacking or questions contain false premises, the system produces a calibrated abstention notice with explicit rationale.

The architecture features a **FastAPI** backend and a responsive **React 18 / TypeScript** frontend with an interactive Evidence Drawer displaying chunk-level citations, similarity scores, and retrieval channels. The system is validated through a 233-test backend test suite, a 12-test frontend suite, a 142-claim entailment audit, and a 50-query evaluation benchmark across development, validation, blind held-out, and adversarial injection test sets.

---

## 3. Key Technical Contributions & Architecture Decisions

| Architectural Component | Engineering Challenge | Technical Solution & Implementation |
|---|---|---|
| **Hybrid Retrieval Fusion** | Dense vector search alone suffers on exact part numbers/error codes; keyword search fails on semantic phrasing. | Implemented dual-channel retrieval blending ChromaDB (`all-MiniLM-L6-v2`) and BM25Okapi, fused using Reciprocal Rank Fusion ($k=60$) with configurable weighting ($\alpha=0.6$). |
| **Evidence Sufficiency Gating** | Traditional RAG systems generate hallucinated or speculative answers when retrieved chunks are semantically adjacent but factually insufficient. | Engineered an entity-aspect coverage analyzer that maps query constraints against candidate chunks, classifying queries into `SUFFICIENT`, `PARTIAL`, or `INSUFFICIENT` states prior to synthesis. |
| **Compound Query Decomposition** | Multi-part queries (e.g. asking for resolution, speed, and warranty) often retrieve chunks biased toward only one clause. | Implemented automated sub-query decomposition, executing independent hybrid retrieval for each sub-clause and unifying evidence contexts. |
| **Citation Entailment Validation** | LLM citations are frequently superficial or fabricated. | Implemented a deterministic post-synthesis citation validator that verifies whether cited chunk IDs actually entail the specific assertions made in the text. |
| **Zero Mock Policy & Safety** | Test mocks or synthetic fallbacks can quietly mask retrieval failures in production. | Hardcoded `ALLOW_MOCK_FALLBACK = False` across all application modules, ensuring every response is backed by real retrieval or explicit abstention. |
| **Storage Governance** | Local machine storage constraints required keeping local working tree under 1,024 MB. | Built split storage topology: local ephemeral cache (`.chroma_live`) paired with persistent cloud backups on Google Drive, verified with SQLite PRAGMA checks. |

---

## 4. Key Metrics & Evaluation Highlights

- **Unit & Integration Test Coverage:** 233 backend Pytest tests (100% pass rate) + 12 frontend Vitest tests (100% pass rate).
- **Held-Out Blind Benchmark Accuracy:** 25/25 (100.0%) on the Phase 4.6 blind benchmark.
- **False Acceptance Resistance:** 0/14 false acceptances on held-out unsupported single-clause queries.
- **Adversarial Injection Defense:** 5/5 (100.0%) defense against direct instruction overrides, roleplay injection, false premise lures, and chimeric entities.
- **Claim Entailment Precision:** 142/142 (100.0%) verified claims supported by cited evidence chunks.
- **Response Latency:** $< 1,500\text{ ms}$ average end-to-end response time on CPU in local deterministic mode.
- **Local Storage Footprint:** $< 20\text{ MB}$ local git repository footprint.

---

## 5. Technical Interview Talking Points & Questions

### Q1: "How does your RAG system prevent hallucinations when the user asks an unanswerable question?"
> *"Instead of passing raw retrieved passages directly to an LLM and hoping it follows an abstention prompt, our system interposes a Universal Evidence Sufficiency Gate. The gate performs query requirement analysis to identify required target entities and requested aspects. It then verifies whether the retrieved passages explicitly cover those aspects. If coverage falls below our decision boundary, the pipeline bypasses answer generation and returns a calibrated abstention notice explaining what information was missing. In our held-out blind benchmark, this reduced false acceptances from over 60% down to 0% across 14 unsupported queries."*

### Q2: "Why did you choose Reciprocal Rank Fusion (RRF) over simple linear score combination?"
> *"Dense cosine similarity scores from SentenceTransformers and BM25 relevance scores operate on completely different numerical scales and score distributions. Dense similarity is bounded between 0 and 1 (or -1 to 1), while BM25 produces unbounded scores dependent on term frequency and document length. Linear score normalization is sensitive to outliers. RRF operates purely on ordinal ranks ($1 / (k + \text{rank})$), providing scale-invariant, robust fusion that reliably blends semantic and exact keyword signals."*

### Q3: "What were the security boundaries you implemented?"
> *"We implemented strict defense-in-depth at the API gateway: input filenames are sanitized to prevent directory traversal (`../`), upload payload sizes are capped at 10 MB with HTTP 413, file contents are checked for magic bytes (preventing binary masquerades), documents enter a non-searchable `pending_index` state until explicitly indexed, and CORS preflight headers are strictly verified. Furthermore, we enforced `ALLOW_MOCK_FALLBACK = False` across all modules so that test stubs can never silently mask production failures."*
