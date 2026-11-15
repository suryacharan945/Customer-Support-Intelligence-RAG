# Project Summary — Customer Support Intelligence Platform

**Release Candidate:** `v1.0.0-rc1`  
**Classification:** Controlled Pilot Ready  
**Repository:** [Customer-Support-Intelligence-RAG](https://github.com/suryacharan945/Customer-Support-Intelligence-RAG)  
**Date:** November 16, 2026  

---

## 1. Project Objective

The primary objective of the **Customer Support Intelligence Assistant / General-Purpose Document Intelligence Platform** is to deliver an evidence-grounded technical question-answering system capable of ingesting diverse documentation formats (`.pdf`, `.txt`, `.md`) across multiple operational domains (product manuals, technical specifications, troubleshooting workflows, warranty agreements, and FAQs).

The system addresses the fundamental limitation of standard RAG pipelines: the tendency to generate ungrounded, plausible-sounding hallucinations when questions involve familiar domain entities but request undocumented attributes.

---

## 2. Problem Statement

Standard enterprise RAG systems face three critical failure modes in technical support settings:

1. **False Acceptance via Lexical Overlap:** Queries that mention recognized products (e.g., *ApexPrint ProX-400*) alongside undocumented predicates (e.g., *Amazon retail price*, *Tokyo repair warehouse address*) frequently retrieve adjacent passages with high vector similarity. Standard LLM generators attempt to answer regardless, hallucinating unsupported facts.
2. **Compound Query Dilution:** Multi-clause questions (e.g., *"What is the print resolution and what is the retail price?"*) are processed as single monolithic queries. Partial evidence is retrieved, and generators either hallucinate the missing part or ignore it without explicit disclosure.
3. **Uncalibrated Confidence:** Vector cosine similarity indicates directional semantic proximity in embedding space, not factual entailment or correctness probability.

---

## 3. Main Capabilities

- **Hybrid Retrieval Fusion:** Combines dense semantic vector search (`sentence-transformers/all-MiniLM-L6-v2` in ChromaDB) with sparse keyword search (in-memory BM25Okapi) using Reciprocal Rank Fusion ($\alpha = 0.6$).
- **Multi-Context Prompting (MCP):** Dynamically routes queries across multiple documentation categories (product manuals, troubleshooting, warranties, FAQs) and merges diverse contexts into balanced synthesis prompts.
- **Compound Query Decomposition:** Automatically decomposes multi-part and comparative queries into atomic sub-questions with pronoun anaphora resolution, evaluating evidence sufficiency independently per sub-question.
- **Universal Evidence Sufficiency Gate:** Evaluates retrieved passages against an empirical relevance floor ($s \ge 0.280$ general, $s \ge 0.350$ aspect-specific) and verifies entity-aspect co-occurrence, classifying query grounding into four explicit states:
  - `SUFFICIENT`: Full factual evidence attested across all query clauses.
  - `PARTIAL`: One or more sub-questions covered; missing attributes explicitly flagged as undocumented.
  - `INSUFFICIENT`: Evidence missing or query out-of-domain; triggers calibrated abstention.
  - `UNCERTAIN`: Ambiguous evidence triggering human clarification review.
- **Claim-Level Citation Validation:** Programmatically confirms chunk ID validity, source document integrity, and verifies that asserted claims correspond to retrieved context.
- **Interactive React 18 Evidence Drawer:** Dark-mode web interface featuring real-time backend telemetry, dynamic evidence grounding badges (`SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`), and a sliding drawer displaying verbatim passage excerpts, chunk IDs, and relevance scores.

---

## 4. Architecture Overview

```
[ User / React Frontend (:5173) ]
             │
             ▼
[ FastAPI Backend Gateway (:8000) ]
             │
             ├──► [ Query Decomposer ] ──► [ Category Router ]
             │                                    │
             │                                    ▼
             ├──► [ Hybrid Retrieval: ChromaDB (0.6) + BM25 (0.4) ]
             │                                    │
             │                                    ▼
             ├──► [ Universal Evidence Sufficiency Gate ]
             │             ├── SUFFICIENT   ──► [ Grounded Synthesis ]
             │             ├── PARTIAL      ──► [ Sub-Answer + Disclosures ]
             │             └── INSUFFICIENT ──► [ Calibrated Abstention ]
             │                                    │
             └──► [ Citation & Entailment Validator ]
                           │
                           ▼
             [ Grounded Response + Verified Citations + Evidence Badges ]
```

---

## 5. Implementation Status

| Component | Status | Implementation Details |
|---|---|---|
| **Backend API** | Complete | FastAPI ASGI gateway with 6 endpoint groups, dependency injection, and error handling. |
| **Document Ingestion** | Complete | Multi-format loader (`.pdf`, `.txt`, `.md`), path traversal defense, 10MB limit, 6-state manifest lifecycle. |
| **Hybrid Retrieval** | Complete | ChromaDB persistent vector store + BM25Okapi with Reciprocal Rank Fusion. |
| **Evidence Sufficiency** | Complete | 4-class gate with entity-aspect co-occurrence and empirical relevance floor. |
| **Synthesis Paths** | Verified | Native local deterministic synthesis verified; remote Colab Mistral-7B inference supported via API endpoint. |
| **React Frontend** | Complete | React 18, TypeScript, Vite, Tailwind CSS, sliding Evidence Drawer, feedback modal. |
| **Automated Tests** | 100% Pass | 233 backend pytest tests passed; 12 frontend Vitest tests passed; clean production build. |

---

## 6. Release Classification

**Classification:** **Controlled Pilot Ready** (`v1.0.0-rc1`)

The release candidate has completed end-to-end integration testing, verified automated test suites, and documented boundary constraints. It is suitable for controlled internal pilots and supervised technical evaluations. Unrestricted public open-internet deployment requires enterprise authentication (SSO) and persistent cloud-hosted database clusters.

---

## 7. Important Limitations

- **Automated Decision, Not Proof of Truth:** The evidence sufficiency gate makes an automated heuristic assessment based on lexical co-occurrence and similarity scores; it does not constitute a formal mathematical proof of real-world truth.
- **Relevance Signals, Not Probabilities:** Cosine similarity scores represent vector space proximity and must not be interpreted as correctness probabilities.
- **Corpus Boundedness:** The system answers strictly from indexed documents. Requests for live internet data, commercial marketplace pricing (Amazon, eBay), or unindexed facilities correctly trigger calibrated abstentions.
- **Execution Path:** The default verified execution path in this release is local deterministic synthesis. Remote Mistral-7B inference requires an active Colab GPU runtime.
