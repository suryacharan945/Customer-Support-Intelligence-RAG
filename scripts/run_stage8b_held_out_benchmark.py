"""Live Colab Mistral 7B Benchmark Runner for Stage 8B Held-Out Dataset.

Executes genuine evaluation queries against the live Google Colab Mistral GPU service
via authenticated Cloudflare tunnel across the 10 held-out evaluation queries in both
Mode A (Baseline RAG) and Mode B (Multi-Context RAG), targeting 20 real generations.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path("C:/Users/surya/Internship_RAG_MCP_Capstone")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.loader import DocumentLoader
from app.ingestion.chunker import DocumentChunker
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.hybrid import HybridRetriever
from app.generation.llm_client import LLMClient
from app.services.rag_service import RAGService
from app.core.config import settings

HELD_OUT_DATASET_PATH = PROJECT_ROOT / "evaluation" / "held_out_dataset.json"
RESULTS_OUTPUT_PATH = PROJECT_ROOT / "evaluation" / "stage8b_held_out_live_results.json"


async def check_colab_availability(llm: LLMClient) -> bool:
    """Probes the configured remote endpoint to verify real GPU service availability."""
    import httpx
    endpoint = llm.endpoint.rstrip("/")
    probe_url = f"{endpoint}/models"
    headers = {"Authorization": f"Bearer {llm.api_key}"} if llm.api_key else {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(probe_url, headers=headers)
            if resp.status_code == 200:
                print(f"[ONLINE] Remote inference endpoint verified: {endpoint}")
                return True
            else:
                print(f"[OFFLINE] Remote endpoint returned status {resp.status_code}: {resp.text[:100]}")
                return False
    except Exception as e:
        print(f"[OFFLINE] Could not reach remote inference endpoint: {e}")
        return False


async def run_held_out_benchmark():
    print("=" * 70)
    print("STAGE 8B: HELD-OUT DATASET LIVE GPU EVALUATION BENCHMARK")
    print("=" * 70)

    # 1. Load Knowledge Base & Index Chunks
    print("\n[STEP 1] Ingesting documents from Google Drive...")
    kb_path = Path("G:/My Drive/Internship_RAG_MCP_Capstone/03_Knowledge_Base")
    loader = DocumentLoader()
    chunker = DocumentChunker()
    docs = loader.load_directory(kb_path)
    all_chunks = []
    for d in docs:
        all_chunks.extend(chunker.chunk_document(d))
    print(f"Loaded {len(docs)} documents into {len(all_chunks)} deterministic chunks.")

    # 2. Initialize Retriever & Live LLM Client
    bm25 = BM25Retriever(all_chunks)
    v_ret = VectorStoreRetriever(allow_mock=True)
    hybrid = HybridRetriever(vector_retriever=v_ret, bm25_retriever=bm25)
    llm = LLMClient(provider="colab_remote", allow_mock=False)
    print(f"Configured Remote Endpoint: {llm.endpoint}")
    print(f"Configured Model ID: {llm.model_name}")

    # 3. Check Live Availability
    is_online = await check_colab_availability(llm)
    if not is_online:
        print("\n[BLOCKED] Remote Colab GPU service is offline or unreachable.")
        print("To run live benchmark:")
        print("1. Open notebooks/02_colab_mistral_rag_inference.ipynb in Google Colab.")
        print("2. Run all cells on GPU.")
        print("3. Export fresh tunnel URL to .env or colab_endpoint.json.")
        print("Aborting benchmark execution without modifying or fabricating results.")
        return False

    svc = RAGService(vector_retriever=v_ret, llm_client=llm, allow_mock=True)
    svc.hybrid_retriever = hybrid

    # 4. Read Held-Out Evaluation Queries
    with open(HELD_OUT_DATASET_PATH, "r", encoding="utf-8") as f:
        ho_data = json.load(f)

    held_out_queries = ho_data.get("held_out_queries", [])
    print(f"Loaded {len(held_out_queries)} held-out queries (20 target generations).\n")

    benchmark_records = []

    # 5. Execute 10 Queries in Both Modes
    for idx, item in enumerate(held_out_queries, start=1):
        qid = item["query_id"]
        q_text = item["query"]
        cat = item["domain_category"]
        print(f"\n--- [{idx}/{len(held_out_queries)}] Query: {qid} ({cat}) ---")
        print(f"Question: {q_text[:75]}...")

        query_record = {
            "query_id": qid,
            "query": q_text,
            "domain_category": cat,
            "ground_truth_claims": item.get("ground_truth_claims", []),
            "baseline": {},
            "multi_context": {},
        }

        for mode in ["baseline", "multi_context"]:
            print(f"   Executing [{mode.upper()}] mode...")
            try:
                t0 = time.perf_counter()
                resp = await svc.process_query(q_text, retrieval_mode=mode)
                total_ms = round((time.perf_counter() - t0) * 1000, 2)

                citations_list = []
                for c in resp.supporting_citations:
                    if hasattr(c, "model_dump"):
                        citations_list.append(c.model_dump())
                    elif hasattr(c, "dict"):
                        citations_list.append(c.dict())
                    else:
                        citations_list.append(dict(c))

                query_record[mode] = {
                    "status": "COMPLETED",
                    "model": llm.model_name,
                    "answer_text": resp.answer,
                    "retrieval_mode": mode,
                    "selected_categories": resp.selected_categories if mode == "multi_context" else [],
                    "evidence_status": resp.evidence_status,
                    "retrieval_latency_ms": resp.retrieval_latency_ms,
                    "generation_latency_ms": resp.generation_latency_ms,
                    "total_latency_ms": total_ms,
                    "timing_breakdown": resp.timing_breakdown or {},
                    "citation_precision": resp.citation_precision,
                    "context_utilization": resp.context_utilization,
                    "supporting_citations": citations_list,
                    "requires_human_clarification": resp.requires_human_clarification,
                }
                print(f"      [OK] Latency: {total_ms} ms | Chars: {len(resp.answer)} | Precision: {resp.citation_precision}")

            except Exception as e:
                print(f"      [ERROR] Generation failed: {e}")
                query_record[mode] = {
                    "status": "FAILED",
                    "error": str(e),
                    "retrieval_mode": mode,
                }

        benchmark_records.append(query_record)

        # Atomic incremental write after every query
        output_data = {
            "benchmark_metadata": {
                "benchmark_name": "Stage 8B Held-Out Live Evaluation",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "model": llm.model_name,
                "endpoint": llm.endpoint,
                "total_queries": len(held_out_queries),
                "completed_queries": len(benchmark_records),
            },
            "held_out_benchmark_results": benchmark_records,
        }
        with open(RESULTS_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

    print("\n" + "=" * 70)
    print(f"[COMPLETE] Held-out live evaluation finished! Results saved to: {RESULTS_OUTPUT_PATH}")
    print("=" * 70)
    return True


if __name__ == "__main__":
    asyncio.run(run_held_out_benchmark())
