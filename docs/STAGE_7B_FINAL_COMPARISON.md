# Stage 7B Final Comparative Evaluation: Baseline RAG vs Multi-Context RAG

## 1. Evaluation Overview & Dataset Scope

This document presents the empirical comparative evaluation conducted during **Stage 7B** using:
- **Inference Model**: `mistralai/Mistral-7B-Instruct-v0.3` (4-bit NF4 quantized, running on Google Colab NVIDIA Tesla T4 GPU).
- **Knowledge Base**: 9 synthetic ApexPrint customer support documents (21 deterministic chunks across 4 categories: `product_manual`, `troubleshooting`, `warranty`, `faq`).
- **Evaluation Callset**: 16 structured benchmark queries spanning 7 functional dimensions.

> [!IMPORTANT]
> **Scope Boundary**: These empirical observations reflect performance on the synthetic ApexPrint printer support dataset. Generalized domain claims beyond this benchmark must not be inferred without wider evaluation on real-world heterogenous corpora.

## 2. Quantitative Performance & Latency Telemetry

| Metric | Mode A: Baseline RAG (Dense Only) | Mode B: Multi-Context RAG (MCP Hybrid) | Observation & Differential |
| :--- | :---: | :---: | :--- |
| **Answer Coverage** | 16/16 (100%) | 16/16 (100%) | Complete coverage across all 16 queries in both modes |
| **Mean Retrieval Latency** | 0.17 ms | 0.63 ms | Multi-context includes query intent classification & BM25 lookup |
| **P95 Retrieval Latency** | 0.27 ms | 0.93 ms | Fast sub-millisecond retrieval on indexed corpus |
| **Mean Generation Latency** | 12385.87 ms (~12.39s) | 26514.24 ms (~26.51s) | MCP structures 3-part responses + multi-category context |
| **P95 Generation Latency** | 17397.83 ms (~17.4s) | 29155.22 ms (~29.16s) | Bounded by `MAX_GENERATION_TOKENS=256` |
| **Total Mean Request Latency** | 12387.2 ms (~12.39s) | 26519.45 ms (~26.52s) | Tradeoff: MCP requires ~2x compute time for structured synthesis |
| **Total P95 Request Latency** | 17399.47 ms (~17.4s) | 29159.97 ms (~29.16s) | Consistent GPU generation throughput |
| **Mean Citation Precision** | 1.0 | 0.4125 | Baseline cites 1 doc; MCP balances candidate evidence across domains |
| **Appropriate Abstention Rate** | 1/2 (50.0%) | 2/2 (100.0%) | MCP explicitly abstained on both out-of-domain inquiries |

## 3. Qualitative Architectural Comparison

### Mode A: Baseline RAG
- **Retrieval Mechanism**: Single-channel dense retrieval across all documents regardless of category.
- **Strengths**: Faster response generation latency (~12.4s mean) due to shorter prompt context.
- **Weaknesses**: In queries requiring information from two separate manuals (e.g. troubleshooting a jam while verifying warranty coverage), single-channel retrieval often missed the secondary domain passage, resulting in incomplete answers.

### Mode B: Multi-Context Prompting (MCP)
- **Retrieval Mechanism**: Analyzes user query to detect multiple category intents (`troubleshooting`, `warranty`, `product_manual`, `faq`), executes hybrid dense + sparse BM25 retrieval, and merges evidence with balanced round-robin representation.
- **Strengths**: Excels at cross-domain queries (`s7_09`, `s7_10`, `s7_13`). Formats answers into structured sections: (1) Executive Summary, (2) Step-by-Step Technical Instructions, and (3) Policy / Warranty Cross-Reference.
- **Adversarial Defusal**: Successfully resisted prompt injection attacks (`s7_15`, `s7_16`), refusing overrides and maintaining grounded warranty limits.
- **Tradeoffs**: Higher context length results in higher generation latency (~26.5s mean).
