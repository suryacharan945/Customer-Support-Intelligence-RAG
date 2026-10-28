# Architectural Blueprint & System Diagrams

**Project**: Customer Support Intelligence Assistant (RAG + Multi-Contextual Prompting)  
**Repository**: `C:\Users\surya\Internship_RAG_MCP_Capstone`  
**Diagram Format**: GitHub-Flavored Markdown / Mermaid v10  
**Verification Baseline**: Commit `ee2f694`  
**Date**: 2026-10-28  

---

## 1. Overall System Architecture

The following diagram illustrates the three-tier decoupled architecture: Streamlit presentation layer, FastAPI application backend, and decoupled Google Colab remote GPU compute tier.

```mermaid
flowchart TD
    subgraph Presentation["Presentation Tier (Port 8501)"]
        UI["Streamlit Frontend (app.py)"]
        V1["Chat View"]
        V2["Comparison View"]
        V3["Documents View"]
        V4["Knowledge Base View"]
        UI --> V1
        UI --> V2
        UI --> V3
        UI --> V4
        CLIENT["Decoupled APIClient (frontend/api_client.py)"]
        V1 & V2 & V3 & V4 --> CLIENT
    end

    subgraph Backend["Application Backend Tier (FastAPI, Port 8000)"]
        ROUTER["API Router (app/api/router.py)"]
        CLIENT -->|"HTTP /api/v1/*"| ROUTER
        
        EP_RAG["/query & /rag/query"]
        EP_DOC["/documents"]
        EP_KB["/knowledge-base/status"]
        EP_FB["/feedback"]
        EP_HLT["/health & /ready"]
        
        ROUTER --> EP_RAG
        ROUTER --> EP_DOC
        ROUTER --> EP_KB
        ROUTER --> EP_FB
        ROUTER --> EP_HLT
        
        SERVICE_RAG["RAGService (app/services/rag_service.py)"]
        SERVICE_ING["IngestionService (app/services/ingestion_service.py)"]
        SERVICE_FB["FeedbackService (app/services/feedback_service.py)"]
        
        EP_RAG --> SERVICE_RAG
        EP_DOC --> SERVICE_ING
        EP_KB --> SERVICE_ING
        EP_FB --> SERVICE_FB
    end

    subgraph DataRetrieval["Local / Stream Storage Tier"]
        MANIFEST["Document Manifest (app/ingestion/manifest.py)"]
        BM25_IDX["BM25Okapi Sparse Index (app/retrieval/bm25.py)"]
        CHROMA_STORE["ChromaDB Vector Store (apexprint_knowledge_base)"]
        GDRIVE["Persistent Storage (G:/My Drive/Internship_RAG_MCP_Capstone)"]
        
        SERVICE_ING --> MANIFEST
        SERVICE_ING --> GDRIVE
        SERVICE_RAG --> BM25_IDX
        SERVICE_RAG --> CHROMA_STORE
    end

    subgraph RemoteCompute["Remote GPU Compute Tier (Google Colab)"]
        TUNNEL["Encrypted Cloudflare Tunnel (HTTPS)"]
        UVICORN_REMOTE["FastAPI Inference Server (Port 8000)"]
        MODEL["mistralai/Mistral-7B-Instruct-v0.3 (NF4 Quantized)"]
        GPU["NVIDIA T4 GPU (16 GB VRAM)"]
        
        SERVICE_RAG -->|"HTTPS Bearer Auth"| TUNNEL
        TUNNEL --> UVICORN_REMOTE
        UVICORN_REMOTE --> MODEL
        MODEL --> GPU
    end
```

---

## 2. Document Ingestion Workflow

Demonstrates document processing, validation, SHA-256 duplicate detection, semantic chunking, and metadata extraction.

```mermaid
flowchart TD
    RAW["Raw Document (.pdf, .txt, .md)"] --> UPLOAD["Document Ingestion API (/api/v1/documents)"]
    UPLOAD --> SEC["Security & Magic-Byte Validation (<=10 MB, no path traversal)"]
    SEC --> HASH["Compute SHA-256 Digest"]
    
    HASH --> DUP_CHECK{"Digest in Manifest?"}
    DUP_CHECK -->|"Yes (Duplicate)"| REJECT["Reject Upload (400 Bad Request)"]
    DUP_CHECK -->|"No (Unique)"| MANIFEST_REC["Record Lifecycle State: uploaded / pending_embedding"]
    
    MANIFEST_REC --> CHUNK["Semantic & Header Chunker (app/ingestion/chunker.py)"]
    CHUNK --> CHUNK_RULES["Chunking Rules:
    - Target: ~300 tokens (1,200 chars)
    - Overlap: 50 tokens (200 chars)
    - Clean whitespace & normalise headers"]
    
    CHUNK_RULES --> CHUNKS["Deterministic Chunks List
    (chunk_id, doc_id, category, page, content)"]
    CHUNKS --> BM25_UPDATE["Update In-Memory BM25 Index"]
    CHUNKS --> DISK_SAVE["Save to Primary Storage (Google Drive)"]
```

---

## 3. Embedding Generation & Vector Indexing

Illustrates the embedding pipeline and ChromaDB vector persistence.

```mermaid
flowchart LR
    CHUNKS["Deterministic Document Chunks"] --> EMB_SERVICE["Embedding Provider (app/retrieval/embeddings.py)"]
    
    EMB_SERVICE --> MODEL_SELECT{"Provider Mode?"}
    MODEL_SELECT -->|"Production / Colab"| ST_MODEL["sentence-transformers/all-MiniLM-L6-v2 (384-d)"]
    MODEL_SELECT -->|"Unit Test Fallback"| HASH_EMB["Deterministic Hash Embedder (384-d float)"]
    
    ST_MODEL --> NORM["L2 Vector Normalization"]
    HASH_EMB --> NORM
    
    NORM --> UPSERT["Controlled Vector Upsert (app/retrieval/vector_store.py)"]
    UPSERT --> COLLECTION["ChromaDB Collection: 'apexprint_knowledge_base'"]
    COLLECTION --> DIST["Distance Metric: Cosine Similarity"]
    
    COLLECTION --> BACKUP["Chroma Backup Service (app/retrieval/chroma_backup.py)"]
    BACKUP --> ARCHIVE["Tarball Snapshot -> Google Drive Storage"]
```

---

## 4. Dense Baseline Retrieval (Mode A)

Illustrates single-channel unconstrained dense vector search across the entire corpus.

```mermaid
flowchart TD
    QUERY["User Query"] --> EMB["Embed Query (all-MiniLM-L6-v2)"]
    EMB --> DENSE_SEARCH["ChromaDB Vector Search (top_k=5)"]
    
    DENSE_SEARCH --> UNFILTERED["Unconstrained Similarity Ranking
    (All Categories Mixed)"]
    
    UNFILTERED --> CANDIDATES["Top Candidate Excerpts"]
    CANDIDATES --> PROMPT["Baseline Prompt Formatter (Single Text Block)"]
    PROMPT --> LLM_CALL["Remote LLM Dispatch (Mistral-7B)"]
    LLM_CALL --> ANSWER["Generated Answer (Prone to Source Hallucination)"]
```

---

## 5. Multi-Context Intent Routing & Hybrid Retrieval (Mode B)

Illustrates category-aware query decomposition, dual-channel retrieval, and Reciprocal Rank Fusion.

```mermaid
flowchart TD
    USER_QUERY["User Query"] --> INTENT["Category Selector (app/retrieval/category_selector.py)"]
    
    INTENT --> CATS{"Category Match?"}
    CATS -->|"Single"| SINGLE_CAT["Focus: ['product_manual'] or ['warranty']"]
    CATS -->|"Multi-Intent"| MULTI_CAT["Focus: ['troubleshooting', 'warranty']"]
    CATS -->|"Unmatched"| ALL_CATS["Fallback: All Categories"]
    
    USER_QUERY --> EXPAND["Query Rewriter & Synonym Injection"]
    
    EXPAND --> DENSE_CH["Channel 1: Dense Semantic Search (ChromaDB)
    - Cosine Distance
    - Category Metadata Filter"]
    
    EXPAND --> SPARSE_CH["Channel 2: Sparse Lexical Search (BM25Okapi)
    - Token Frequency / Inverse Document Freq
    - Technical Acronym Weighting"]
    
    DENSE_CH --> RANK_D["Rank List R_dense"]
    SPARSE_CH --> RANK_S["Rank List R_sparse"]
    
    RANK_D & RANK_S --> RRF["Reciprocal Rank Fusion (app/retrieval/hybrid.py)
    RRF_score(d) = sum( 1 / (60 + rank_i(d)) )"]
    
    RRF --> DEDUP["Chunk Deduplication & Cross-Category Balancing"]
    DEDUP --> FINAL_CHUNKS["Balanced Top-K Evidence Chunks"]
```

---

## 6. Multi-Context Partitioning & Context Assembly

Illustrates how retrieved chunks are assembled into structured blocks with strict budgeting and prompt injection defenses.

```mermaid
flowchart TD
    CHUNKS["Balanced Evidence Chunks (from RRF)"] --> BUILDER["MCPContextBuilder (app/generation/mcp_context.py)"]
    
    BUILDER --> PARTITION["Partition Chunks by Category:
    - [PRODUCT MANUAL EXCERPTS]
    - [TROUBLESHOOTING GUIDE EXCERPTS]
    - [WARRANTY & POLICY EXCERPTS]
    - [FAQ EXCERPTS]"]
    
    PARTITION --> SANITIZE["Prompt Injection Defense & Token Normalization:
    - Strip control characters & escape tags
    - Compact redundant whitespace (~12% savings)"]
    
    SANITIZE --> BUDGET["Context Budget Manager:
    - Hard limit: 2,048 tokens
    - Round-robin allocation across present categories
    - Cross-domain conflict preservation"]
    
    BUDGET --> FORMAT_BLOCKS["Formatted Evidence Block with Strict Chunk IDs:
    [Source: <filename>, Page: <p>, Chunk: <id>]"]
    
    FORMAT_BLOCKS --> FINAL_PROMPT["Structured MCP Prompt Template:
    1. Executive Summary / Direct Answer
    2. Step-by-Step Resolution / Technical Specs
    3. Warranty & Policy Cross-Reference
    4. Verified Source Citations"]
```

---

## 7. Remote Mistral-7B Inference Workflow

Illustrates authenticated remote inference offloaded to Google Colab T4 GPU.

```mermaid
sequenceDiagram
    autonumber
    participant App as FastAPI Backend (Local)
    participant Client as LLMClient (app/generation/llm_client.py)
    participant Tunnel as Cloudflare Tunnel (HTTPS)
    participant Colab as Colab Server (notebooks/02_*)
    participant Model as Mistral-7B-Instruct-v0.3 (NF4)

    App->>Client: generate_response(prompt, max_tokens=512)
    Client->>Client: Inject Authorization: Bearer <secure_token>
    Client->>Tunnel: POST /v1/chat/completions
    Tunnel->>Colab: Forward Request
    Colab->>Colab: Validate Bearer Token
    Colab->>Model: Tokenize & Autoregressive GPU Generation
    Model-->>Colab: Generated Tokens
    Colab-->>Tunnel: HTTP 200 { id, choices: [{ message: { content } }], usage }
    Tunnel-->>Client: Return JSON Payload
    Client->>Client: Calculate Generation Latency (monotonic timer)
    Client-->>App: LLMResponse(content, latency_ms)
```

---

## 8. FastAPI Backend & Streamlit Interaction

Illustrates request handling, session state management, and view rendering.

```mermaid
sequenceDiagram
    autonumber
    participant User as End User / Browser
    participant Streamlit as Streamlit Frontend (:8501)
    participant APIClient as APIClient (HTTP)
    participant FastAPI as FastAPI Backend (:8000)
    participant RAG as RAGService Pipeline

    User->>Streamlit: Selects Multi-Context Mode, Enters Question
    Streamlit->>APIClient: query(query_text, mode="multi_context", top_k=5)
    APIClient->>FastAPI: POST /api/v1/query { query, retrieval_mode, top_k }
    FastAPI->>RAG: process_query(query, mode="multi_context")
    RAG-->>FastAPI: QueryResponse(answer, citations, timing_breakdown)
    FastAPI-->>APIClient: HTTP 200 OK (JSON)
    APIClient-->>Streamlit: Structured Query Dict
    Streamlit->>Streamlit: Update st.session_state.chat_history
    Streamlit->>User: Render Answer + Badges + Citation Cards + Feedback Controls
```

---

## 9. Citation Validation & Self-Improving Feedback Loop

Illustrates automated citation extraction, candidate verification, and human active learning logging.

```mermaid
flowchart TD
    MODEL_OUT["Model Generated Answer Text"] --> EXTRACT["Regex Citation Parser:
    Extract [Source: <doc>, Page: <p>, Chunk: <id>]"]
    
    EXTRACT --> ASSERTED["Asserted Citations Set (A_model)"]
    CANDIDATES["Retrieved Evidence Pool (C_ret)"] --> VALIDATE{"Match in Candidate Pool?"}
    ASSERTED --> VALIDATE
    
    VALIDATE -->|"Yes (Exact Match)"| VERIFIED["Accepted Citation (V_app = A_model ∩ C_ret)"]
    VALIDATE -->|"No (Hallucinated)"| REJECTED["Flagged Citation Hallucination"]
    
    VERIFIED & REJECTED --> METRICS["Compute True Citation Precision:
    P_true = |V_app| / |A_model|"]
    
    MODEL_OUT --> UI_RENDER["Render in Streamlit Chat View"]
    UI_RENDER --> HUMAN["Human Agent Inspection (1-5 Stars, Comments, Flag)"]
    HUMAN --> SUBMIT_FB["Submit Feedback (POST /api/v1/feedback)"]
    SUBMIT_FB --> FB_SERVICE["FeedbackService (app/services/feedback_service.py)"]
    FB_SERVICE --> FB_LOG["Append to feedback_logs.jsonl (Active Learning Corpus)"]
```

---

## 10. Security & Operational Boundaries

Illustrates trust boundaries, credential containment, and execution limits.

```mermaid
flowchart TD
    subgraph PublicInternet["Untrusted / Public Domain"]
        ATTACKER["Adversarial Prompt Injection / Attacker"]
        USER["Legitimate Customer Support User"]
    end

    subgraph TrustBoundaryLocal["Local System Boundary (Strictly Firewalled)"]
        FASTAPI["FastAPI Backend (:8000)
        - Strict Pydantic Payload Validation
        - Path Traversal Defense on Uploads
        - 10MB File Size Bound
        - In-Memory Non-Persistent Vector Fallback"]
        
        STREAMLIT["Streamlit Frontend (:8501)
        - Zero Direct Database Imports
        - Isolated Browser Session State"]
        
        ENV[".env Secrets File
        - Strictly in .gitignore
        - Zero Secrets Committed to Git"]
    end

    subgraph TrustBoundaryCloud["Encrypted Cloud Boundary"]
        CLOUDFLARE["Cloudflare Tunnel (TLS 1.3 / HTTPS)"]
        BEARER["Bearer Token Authentication Guard"]
        COLAB["Google Colab T4 Runtime
        - Bounded max_tokens = 512
        - 30-Second Inference Timeout
        - Dynamic ephemeral tokens only"]
    end

    ATTACKER & USER -->|"Web Browser"| STREAMLIT
    STREAMLIT -->|"Localhost Only"| FASTAPI
    FASTAPI -->|"Reads Secrets"| ENV
    FASTAPI -->|"HTTPS with Bearer Token"| CLOUDFLARE
    CLOUDFLARE --> BEARER
    BEARER --> COLAB
```
