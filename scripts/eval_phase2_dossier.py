"""Stage 8 Phase 2 Evaluation Script: 15-Question Dossier Grounded Generation Benchmark.

Executes end-to-end RAG workflow across 15 comprehensive technical, architectural,
comparative, multi-page, and out-of-domain evaluation questions against the live
knowledge base (including AI Customer Support Intelligence Platform - Project Dossier.pdf).

Measures:
- Intent detection and routing
- End-to-end latency breakdown (retrieval, synthesis, validation)
- Context retrieval hits and page coverage
- Adaptive structured answer sections
- Citation precision and groundedness metrics
- Unsupported topic abstention
"""

import asyncio
import json
import os
import time
from typing import List, Dict, Any

from app.services.rag_service import RAGService
from app.retrieval.query_analyzer import query_analyzer


async def run_evaluation():
    rag = RAGService()

    queries = [
        {
            "id": "Q01",
            "category": "Architecture",
            "query": "Explain the complete system architecture of this project.",
            "expected_page": 2,
        },
        {
            "id": "Q02",
            "category": "Technology Stack",
            "query": "What technologies are used in the frontend and presentation layer?",
            "expected_page": 3,
        },
        {
            "id": "Q03",
            "category": "Backend Architecture",
            "query": "Explain the backend architecture, application server, and endpoint routing.",
            "expected_page": 2,
        },
        {
            "id": "Q04",
            "category": "Multi-Context Prompting",
            "query": "What is Multi-Context Prompting and how does it prevent context starvation?",
            "expected_page": 4,
        },
        {
            "id": "Q05",
            "category": "Hybrid Retrieval",
            "query": "Explain the hybrid retrieval pipeline and Reciprocal Rank Fusion.",
            "expected_page": 1,
        },
        {
            "id": "Q06",
            "category": "Reciprocal Rank Fusion",
            "query": "How does Reciprocal Rank Fusion combine dense and sparse rankings?",
            "expected_page": 1,
        },
        {
            "id": "Q07",
            "category": "Citation Validation",
            "query": "How does the citation validation engine work and ensure zero hallucinations?",
            "expected_page": 6,
        },
        {
            "id": "Q08",
            "category": "Benchmark Results",
            "query": "Summarize the benchmark results comparing Mode A and Mode B.",
            "expected_page": 3,
        },
        {
            "id": "Q09",
            "category": "Engineering Decisions",
            "query": "Explain the core engineering decisions made in this project.",
            "expected_page": 5,
        },
        {
            "id": "Q10",
            "category": "Storage Constraints",
            "query": "What are the storage constraints and how is the 1024 MB budget enforced?",
            "expected_page": 5,
        },
        {
            "id": "Q11",
            "category": "Accessibility",
            "query": "Explain the accessibility decisions and WCAG compliance features.",
            "expected_page": 5,
        },
        {
            "id": "Q12",
            "category": "Technical Interview Questions",
            "query": "What are the key technical interview questions and elevator pitch for this project?",
            "expected_page": 6,
        },
        {
            "id": "Q13",
            "category": "Comparison",
            "query": "Compare Baseline RAG and Multi-Context Prompting.",
            "expected_page": 3,
        },
        {
            "id": "Q14",
            "category": "Multi-Page Synthesis",
            "query": "Explain the system architecture and its benchmark results across precision and hallucination rate.",
            "expected_page": "2 and 3",
        },
        {
            "id": "Q15",
            "category": "Unsupported / Abstention",
            "query": "Provide a culinary recipe for chocolate chip cookies with quantum computing principles.",
            "expected_page": "None (Honest Abstention)",
        },
    ]

    out_dir = os.path.join("evaluation", "stage8_phase2")
    os.makedirs(out_dir, exist_ok=True)

    results = []
    print(f"\n========================================================")
    print(f"STARTING STAGE 8 PHASE 2 DOSSIER GENERATION BENCHMARK ({len(queries)} QUERIES)")
    print(f"========================================================\n")

    for item in queries:
        qid = item["id"]
        q_text = item["query"]
        expected = item["expected_page"]

        analysis = query_analyzer.analyze_query(q_text)

        t0 = time.perf_counter()
        resp = await rag.process_query(q_text, retrieval_mode="multi_context")
        total_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Check sections present
        answer_text = resp.answer
        sections_detected = []
        for line in answer_text.split("\n"):
            line_s = line.strip()
            if line_s.startswith("### ") or line_s.startswith("1. ") or line_s.startswith("2. ") or line_s.startswith("3. ") or line_s.startswith("4. "):
                sections_detected.append(line_s)

        # Context details
        contexts_meta = []
        dossier_chunks_count = 0
        pages_retrieved = set()
        for c in resp.citations:
            src = c.document_source or ""
            cid = c.chunk_id or ""
            page = c.page_or_section or ""
            cat = c.category or ""
            is_dossier = "dossier" in src.lower()
            if is_dossier:
                dossier_chunks_count += 1
                if page:
                    pages_retrieved.add(page)
            contexts_meta.append({
                "chunk_id": cid,
                "source": src,
                "page": page,
                "category": cat,
                "score": c.relevance_score,
                "is_dossier": is_dossier,
            })

        val_dict = {
            "evidence_status": resp.evidence_status,
            "citation_precision": resp.citation_precision,
            "context_utilization": resp.context_utilization,
            "supporting_citations_count": len(resp.supporting_citations),
            "total_citations_count": len(resp.citations),
        }

        eval_entry = {
            "id": qid,
            "category": item["category"],
            "query": q_text,
            "expected_page": expected,
            "intent_detected": analysis.primary_intent,
            "is_customer_support": analysis.is_customer_support,
            "latency_ms": {
                "total": resp.execution_time_ms,
                "retrieval": resp.retrieval_latency_ms,
                "generation": resp.generation_latency_ms,
                "timing_breakdown": resp.timing_breakdown,
            },
            "retrieval_stats": {
                "total_retrieved": len(resp.citations),
                "dossier_chunks_retrieved": dossier_chunks_count,
                "pages_retrieved": sorted(list(pages_retrieved)),
                "chunks": contexts_meta,
            },
            "validation_metrics": val_dict,
            "sections_detected": sections_detected,
            "answer_preview": answer_text[:280].strip() + ("..." if len(answer_text) > 280 else ""),
            "full_answer": answer_text,
        }
        results.append(eval_entry)

        print(f"[{qid}] {item['category']}: {q_text[:60]}...")
        print(f"      Intent: {analysis.primary_intent} | Support: {analysis.is_customer_support}")
        print(f"      Latency: {resp.execution_time_ms}ms (Ret: {resp.retrieval_latency_ms}ms, Gen: {resp.generation_latency_ms}ms)")
        print(f"      Dossier hits: {dossier_chunks_count}/{len(resp.citations)} | Pages: {sorted(list(pages_retrieved))}")
        print(f"      Citation Precision: {resp.citation_precision} | Evidence Status: {resp.evidence_status}")
        print(f"      Sections: {len(sections_detected)} found\n")

    output_path = os.path.join(out_dir, "phase2_dossier_generation_evaluation.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n========================================================")
    print(f"EVALUATION COMPLETE. Results saved to: {output_path}")
    print(f"========================================================\n")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
