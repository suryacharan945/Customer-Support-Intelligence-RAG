# Disclosed Project Limitations & Architectural Boundaries

**Project**: Customer Support Intelligence Assistant (RAG + Multi-Contextual Prompting)  
**Evaluation Baseline**: Commit `ee2f694`  
**Date**: 2026-10-28  

In accordance with academic integrity standards and internship submission guidelines, this document explicitly details all known limitations, operational assumptions, and architectural boundaries of the system.

---

## 1. Knowledge Base & Corpus Limitations

1. **Synthetic Document Corpus**:
   - The primary evaluation corpus comprises **9 synthetic Markdown documents** (~15,000 words total) representing a fictional hardware corporation (*ApexPrint Technologies*).
   - While these documents accurately mimic real-world enterprise formats (troubleshooting guides, warranty terms, product manuals, and FAQs), they do not capture the multi-gigabyte scale, layout complexities, formatting anomalies, or scan artifacts found in real industrial document lakes.

2. **Absence of Raster Image OCR**:
   - The document ingestion pipeline natively processes Markdown (`.md`), plain text (`.txt`), and clean text-based PDFs (`.pdf`).
   - Scanned raster PDFs and raw hardware photos (e.g. user-submitted photos of broken gears) cannot be processed directly without an optical character recognition (OCR) preprocessor such as Tesseract or AWS Textract.

---

## 2. Retrieval & Algorithmic Boundaries

1. **Deterministic Intent Classifier**:
   - Category routing is implemented via deterministic keyword and regular expression matching (`CategorySelector`).
   - While this achieves near-zero latency (<5 ms) and 100% determinism, highly subtle or colloquial phrasing that avoids technical keywords may default to unrouted search across all categories.

2. **In-Memory BM25 Indexing**:
   - The BM25Okapi sparse lexical index currently resides in-memory and is populated during application startup or document ingestion.
   - For enterprise repositories exceeding 100,000 chunks, a distributed inverted index (such as Elasticsearch or OpenSearch) would be required.

3. **ChromaDB Windows Fallback**:
   - On Windows environments lacking C++ build tools or SQLite3 binary extensions, ChromaDB operates in a deterministic in-memory mock fallback mode.
   - Full vector search operates natively in Linux / Colab container environments.

---

## 3. Large Language Model & Inference Limitations

1. **Remote GPU Generation Latency**:
   - Average generation latency for Multi-Context mode on the remote Google Colab NVIDIA T4 GPU is **25.44 seconds** (due to autoregressive token generation across 878-character structured responses).
   - This latency is acceptable for asynchronous support ticket drafting, but exceeds the optimal <3-second threshold for real-time live customer chat. Real-time production deployment would require an inference engine such as vLLM or TensorRT-LLM on dedicated hardware.

2. **Helpfulness Bias on Out-of-Domain Queries (`ho_09`)**:
   - When presented with inquiries outside the knowledge base (e.g., streaming music via printer Bluetooth speakers), the rigid MCP prompt template—which explicitly instructs the model to generate an Executive Summary and Step-by-Step Resolution—induced a **helpfulness bias**, leading the LLM to invent generic iOS Bluetooth steps.
   - Future prompt engineering must enforce negative constraint verification before procedural instructions are generated.

3. **Session Ephemerality on Free-Tier Colab**:
   - Free Google Colab sessions time out after 90–120 minutes of inactivity. When the session terminates, the Cloudflare tunnel URL expires and must be refreshed.

---

## 4. Evaluation & Human Review Scope

1. **Sample Size Boundaries**:
   - The empirical evaluation is based on **26 unique inquiries** (16 development + 10 held-out), yielding **52 total live GPU inferences**.
   - While statistically informative and strictly audited, larger benchmarks (hundreds of queries) would be necessary for formal confidence intervals across rare error codes.

2. **Automated vs Human Factual Assessment**:
   - Automated citation precision verifies that asserted citations match candidate chunk IDs.
   - It does not replace independent human verification of factual truth. Full human scoring sheets have been prepared with blank fields (`[ ]`) and remain **PENDING** evaluation by domain experts.
