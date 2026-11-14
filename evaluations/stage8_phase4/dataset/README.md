# Stage 8 Phase 4 Multi-Domain Evaluation Benchmark Dataset

## 1. Overview
This dataset contains **50 rigorously designed evaluation questions** spanning all 10 indexed documents in the active knowledge base across 8 question categories.
Every question has verified chunk-level ground truth extracted directly from ChromaDB.

## 2. Question Distribution by Type
- **Type A (Direct Factual)**: 8 questions (Q01–Q08)
- **Type B (Multi-Step Synthesis)**: 7 questions (Q09–Q15)
- **Type C (Cross-Document Multi-Context)**: 7 questions (Q16–Q22)
- **Type D (Numerical & Benchmark Extraction)**: 7 questions (Q23–Q29)
- **Type E (Comparison)**: 6 questions (Q30–Q35)
- **Type F (Conflicting Information & Exclusions)**: 5 questions (Q36–Q40)
- **Type G (Ambiguous or Partially Supported)**: 5 questions (Q41–Q45)
- **Type H (Unsupported & Out-of-Domain)**: 5 questions (Q46–Q50)

## 3. Evidence Status Breakdown
- **SUFFICIENT**: 40 questions (80.0%)
- **PARTIAL**: 5 questions (10.0%)
- **INSUFFICIENT (Honest Abstention Target)**: 5 questions (10.0%)

## 4. Ground Truth Construction Methodology
- **Chunk-Level Mapping**: For every supported question, the exact ChromaDB `chunk_id` and source filename were mapped using the persistent index catalog (`scripts/inspect_corpus_for_phase4.py`).
- **Zero Hallucinated Keys**: Expected facts are derived strictly from verbatim text in indexed files.
- **Strict Abstention Standards**: Unsupported questions have empty `expected_chunks` and mandate `INSUFFICIENT` evidence status.
