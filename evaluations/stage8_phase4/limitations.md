# Stage 8 Phase 4: Limitations and Threats to Validity

**Evaluation Date**: 2026-11-14  
**Commit Baseline**: `dcde878`  
**Evaluation Scope**: 50 Multi-Domain Benchmark Questions against 43 Indexed Knowledge Base Chunks  

---

## 1. Threats to Validity in Retrieval Evaluation

### A. Corpus Size and Chunk Granularity
- **Current Corpus Scale**: The knowledge base currently contains 10 documents partitioned into 43 chunks (20 from Project Dossier, 23 across 9 printer customer-support documents).
- **Impact on Metrics**: While 43 chunks provide a complete representation of all documented system features and error codes, it represents a compact enterprise collection. In smaller collections, top-5 retrieval represents ~11.6% of the entire corpus ($\frac{5}{43}$), naturally yielding higher coverage than would be observed in corpora containing tens of thousands of chunks.
- **Top-1 vs Top-5 Tradeoff**: For direct single-chunk lookup queries, Dense retrieval achieved slightly higher Precision@1 (0.4444 vs 0.4000) because global cosine similarity placed the top semantic chunk first. However, for multi-step and cross-document queries, Multi-Context RAG achieved superior Recall@3 (0.6000 vs 0.5593), Recall@5 (0.7519 vs 0.7407), and nDCG@5 (0.5980 vs 0.5889).

---

## 2. Limitations in Out-of-Domain Detection & Abstention

### A. Absence of Absolute Similarity Threshold in Retrieval
- **Critical Finding**: Out of 5 unsupported / out-of-domain questions (Q46–Q50), the system correctly abstained on only **1 question (20.0%)**: `P4_Q46` (*"Hyderabadi chicken biryani"*).
- **False Positive Answers**: On the remaining 4 OOD questions, the system produced false positive grounded answers:
  1. `P4_Q47` (*"How do you clear a paper jam on a Hewlett-Packard HP LaserJet Enterprise M608?"*): The system matched keyword tokens "paper jam" and "clear", retrieved the ApexPrint ProX-400 Error E-101 chunk, and answered with ApexPrint steps instead of abstaining.
  2. `P4_Q48` (*"What is the distance between the Earth and the planet Mars at closest approach?"*): The dense retriever returned low-similarity chunks from the Project Dossier (similarity ~0.22), but without a relevance threshold cut-off, the top-5 chunks were treated as evidence.
  3. `P4_Q49` (*"Baggage allowance policies on Delta Airlines"*): Matched toner cartridge maintenance chunks.
  4. `P4_Q50` (*"Warranty coverage for meteor strikes or nuclear radiation"*): Matched general warranty exclusion chunks.
- **Root Cause**: The current `process_query` pipeline does not enforce a strict minimum cosine similarity threshold (e.g. $\text{similarity} \ge 0.45$) or minimum RRF score before declaring `evidence_found = True`. When zero relevant evidence exists, the retriever still returns the top-5 highest-scoring chunks from the collection, and the local synthesizer attempts to extract sentences from them.

---

## 3. Heuristic vs Semantic Evaluation Limitations

### A. Lexical Containment vs True Natural Language Entailment
- The automated citation validator computes chunk delivery verification and lexical token overlap ($\ge 20\%$).
- **Limitation**: A 20% token overlap confirms that words from the retrieved passage appear in the generated sentence. It does **not** prove semantic entailment (i.e. that the claim logically follows from the premises without alteration or unwarranted extrapolations). True semantic validation requires human expert review or heavy NLI cross-encoders.

### B. Local Synthesizer vs Full Parametric LLM
- The local grounded synthesizer (`local_synthesizer.py`) generates answers via deterministic sentence scoring, section templates, and regex extraction.
- **Advantages**: 100% offline, deterministic, verified chunk IDs, ~11.8 ms latency, zero API costs.
- **Limitations**: Sentences are extracted directly from chunks rather than rephrased into fluent, multi-paragraph synthesis. For complex reasoning across contradictory clauses, a generative instruction-tuned LLM (e.g. Mistral-7B) is required.

---

## 4. Latency Measurement Boundaries

- **Local Synthesis**: Consistently executes in **10 to 20 ms** in Python memory.
- **Cold vs Warm Retrieval**:
  - The first query against an uninitialized SentenceTransformer and ChromaDB engine took **~15,112 ms** (15.1s) due to one-time PyTorch weights loading into CPU memory.
  - Subsequent warm queries executed consistently in **~615 to 640 ms**.
- **Remote Colab GPU Inference**: Takes **12 to 26 seconds** per query due to autoregressive token generation across network tunnels. They must never be conflated.
