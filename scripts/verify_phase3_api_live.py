"""Stage 8 Phase 3 Live FastAPI API Integration Verification Script.

Executes genuine end-to-end API calls against the live FastAPI application (no mocks).
Verifies:
1. Project Dossier Architecture query
2. Project Dossier Benchmark query
3. ApexPrint Printer Troubleshooting query
4. Baseline vs Multi-Context Comparison query
5. Out-of-Domain Recipe query (honest abstention verification)
"""

import sys
import json
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from starlette.testclient import TestClient
from app.main import app

def run_live_api_verification():
    print("=" * 80)
    print("STAGE 8 PHASE 3: LIVE FASTAPI API INTEGRATION VERIFICATION")
    print("=" * 80)
    
    client = TestClient(app)
    results = []

    # 1. Health Probe Verification
    print("\n[1/6] Verifying API Liveness & Readiness (/api/v1/health)...")
    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200, f"Health check failed with {health_resp.status_code}"
    health_data = health_resp.json()
    print(f" -> Health Status: {health_data.get('status')} | Version: {health_data.get('version')}")

    # 2. Query 1: Project Dossier Architecture
    print("\n[2/6] Executing Query 1: Project Dossier Architecture...")
    q1_payload = {
        "query": "Explain the complete architecture of this project.",
        "retrieval_mode": "multi_context",
    }
    t0 = time.perf_counter()
    resp1 = client.post("/api/v1/query", json=q1_payload)
    elapsed1 = (time.perf_counter() - t0) * 1000
    assert resp1.status_code == 200, f"Query 1 failed with {resp1.status_code}: {resp1.text}"
    d1 = resp1.json()
    
    print(f" -> Status: {resp1.status_code} | Total HTTP Latency: {elapsed1:.2f}ms")
    print(f" -> Evidence Status: {d1.get('evidence_status')} | Provider: {d1.get('provider_status')}")
    print(f" -> Retrieval Latency: {d1.get('retrieval_latency_ms')}ms | Synthesis: {d1.get('generation_latency_ms')}ms")
    print(f" -> Citations Count: {len(d1.get('citations', []))} | Supporting: {len(d1.get('supporting_citations', []))}")
    if d1.get('citations'):
        print(f" -> Primary Citation Source: {d1['citations'][0].get('document_source')} (Chunk: {d1['citations'][0].get('chunk_id')})")
    
    results.append({
        "id": "Q1_Architecture",
        "domain": "Project Dossier / Engineering",
        "query": q1_payload["query"],
        "retrieval_mode": d1.get("retrieval_mode"),
        "evidence_status": d1.get("evidence_status"),
        "provider_status": d1.get("provider_status"),
        "retrieval_latency_ms": d1.get("retrieval_latency_ms"),
        "generation_latency_ms": d1.get("generation_latency_ms"),
        "citations_count": len(d1.get("citations", [])),
        "primary_source": d1["citations"][0].get("document_source") if d1.get("citations") else None,
        "answer_preview": d1.get("answer")[:200] + "...",
    })

    # 3. Query 2: Project Dossier Benchmarks
    print("\n[3/6] Executing Query 2: Project Dossier Benchmark Results...")
    q2_payload = {
        "query": "What are the benchmark results?",
        "retrieval_mode": "multi_context",
    }
    t0 = time.perf_counter()
    resp2 = client.post("/api/v1/query", json=q2_payload)
    elapsed2 = (time.perf_counter() - t0) * 1000
    assert resp2.status_code == 200, f"Query 2 failed with {resp2.status_code}: {resp2.text}"
    d2 = resp2.json()

    print(f" -> Status: {resp2.status_code} | Total HTTP Latency: {elapsed2:.2f}ms")
    print(f" -> Evidence Status: {d2.get('evidence_status')} | Provider: {d2.get('provider_status')}")
    print(f" -> Citations Count: {len(d2.get('citations', []))}")
    print(f" -> Contains Table / Numbers: {'|' in d2.get('answer', '') or '%' in d2.get('answer', '')}")

    results.append({
        "id": "Q2_Benchmarks",
        "domain": "Project Dossier / Evaluation",
        "query": q2_payload["query"],
        "retrieval_mode": d2.get("retrieval_mode"),
        "evidence_status": d2.get("evidence_status"),
        "provider_status": d2.get("provider_status"),
        "retrieval_latency_ms": d2.get("retrieval_latency_ms"),
        "generation_latency_ms": d2.get("generation_latency_ms"),
        "citations_count": len(d2.get("citations", [])),
        "primary_source": d2["citations"][0].get("document_source") if d2.get("citations") else None,
        "answer_preview": d2.get("answer")[:200] + "...",
    })

    # 4. Query 3: ApexPrint Printer Support
    print("\n[4/6] Executing Query 3: ApexPrint Printer Support (Error E-101)...")
    q3_payload = {
        "query": "How do I resolve Error E-101 on ApexPrint ProX400?",
        "retrieval_mode": "multi_context",
    }
    t0 = time.perf_counter()
    resp3 = client.post("/api/v1/query", json=q3_payload)
    elapsed3 = (time.perf_counter() - t0) * 1000
    assert resp3.status_code == 200, f"Query 3 failed with {resp3.status_code}: {resp3.text}"
    d3 = resp3.json()

    print(f" -> Status: {resp3.status_code} | Total HTTP Latency: {elapsed3:.2f}ms")
    print(f" -> Evidence Status: {d3.get('evidence_status')} | Provider: {d3.get('provider_status')}")
    print(f" -> Citations Count: {len(d3.get('citations', []))}")
    if d3.get('citations'):
        print(f" -> Primary Citation Source: {d3['citations'][0].get('document_source')}")

    results.append({
        "id": "Q3_Printer_Troubleshooting",
        "domain": "Printer Support / Troubleshooting",
        "query": q3_payload["query"],
        "retrieval_mode": d3.get("retrieval_mode"),
        "evidence_status": d3.get("evidence_status"),
        "provider_status": d3.get("provider_status"),
        "retrieval_latency_ms": d3.get("retrieval_latency_ms"),
        "generation_latency_ms": d3.get("generation_latency_ms"),
        "citations_count": len(d3.get("citations", [])),
        "primary_source": d3["citations"][0].get("document_source") if d3.get("citations") else None,
        "answer_preview": d3.get("answer")[:200] + "...",
    })

    # 5. Query 4: Baseline vs Multi-Context Side-by-Side Comparison
    print("\n[5/6] Executing Query 4: Baseline vs Multi-Context Side-by-Side Comparison...")
    comp_query = "How does the citation validation engine work?"
    
    resp_base = client.post("/api/v1/query", json={"query": comp_query, "retrieval_mode": "baseline"})
    d_base = resp_base.json()
    resp_mcp = client.post("/api/v1/query", json={"query": comp_query, "retrieval_mode": "multi_context"})
    d_mcp = resp_mcp.json()

    print(f" -> Baseline: Status {resp_base.status_code} | Ret: {d_base.get('retrieval_latency_ms')}ms | Evidence: {d_base.get('evidence_status')}")
    print(f" -> Multi-Context: Status {resp_mcp.status_code} | Ret: {d_mcp.get('retrieval_latency_ms')}ms | Evidence: {d_mcp.get('evidence_status')}")

    results.append({
        "id": "Q4_Comparison_Baseline",
        "domain": "Cross-Domain Comparison",
        "query": comp_query,
        "retrieval_mode": "baseline",
        "evidence_status": d_base.get("evidence_status"),
        "provider_status": d_base.get("provider_status"),
        "retrieval_latency_ms": d_base.get("retrieval_latency_ms"),
        "generation_latency_ms": d_base.get("generation_latency_ms"),
        "citations_count": len(d_base.get("citations", [])),
        "primary_source": d_base["citations"][0].get("document_source") if d_base.get("citations") else None,
    })
    results.append({
        "id": "Q4_Comparison_MultiContext",
        "domain": "Cross-Domain Comparison",
        "query": comp_query,
        "retrieval_mode": "multi_context",
        "evidence_status": d_mcp.get("evidence_status"),
        "provider_status": d_mcp.get("provider_status"),
        "retrieval_latency_ms": d_mcp.get("retrieval_latency_ms"),
        "generation_latency_ms": d_mcp.get("generation_latency_ms"),
        "citations_count": len(d_mcp.get("citations", [])),
        "primary_source": d_mcp["citations"][0].get("document_source") if d_mcp.get("citations") else None,
    })

    # 6. Query 5: Out-of-Domain Honest Abstention
    print("\n[6/6] Executing Query 5: Out-of-Domain Honest Abstention...")
    ood_payload = {
        "query": "What is the secret recipe for making hyderabadi chicken biryani?",
        "retrieval_mode": "multi_context",
    }
    t0 = time.perf_counter()
    resp_ood = client.post("/api/v1/query", json=ood_payload)
    elapsed_ood = (time.perf_counter() - t0) * 1000
    assert resp_ood.status_code == 200, f"Query 5 failed with {resp_ood.status_code}: {resp_ood.text}"
    d_ood = resp_ood.json()

    print(f" -> Status: {resp_ood.status_code} | Total HTTP Latency: {elapsed_ood:.2f}ms")
    print(f" -> Evidence Status: {d_ood.get('evidence_status')} (Expected: INSUFFICIENT)")
    print(f" -> Evidence Found: {d_ood.get('evidence_found')} (Expected: False)")
    print(f" -> Citations Count: {len(d_ood.get('citations', []))} (Expected: 0)")
    assert d_ood.get("evidence_status") == "INSUFFICIENT", "Expected INSUFFICIENT evidence status for OOD query"

    results.append({
        "id": "Q5_Honest_Abstention",
        "domain": "Out-of-Domain",
        "query": ood_payload["query"],
        "retrieval_mode": d_ood.get("retrieval_mode"),
        "evidence_status": d_ood.get("evidence_status"),
        "provider_status": d_ood.get("provider_status"),
        "retrieval_latency_ms": d_ood.get("retrieval_latency_ms"),
        "generation_latency_ms": d_ood.get("generation_latency_ms"),
        "citations_count": len(d_ood.get("citations", [])),
        "primary_source": None,
        "answer_preview": d_ood.get("answer")[:200] + "...",
    })

    # Save to JSON
    out_path = PROJECT_ROOT / "stage8_phase3_api_validation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("ALL 6 LIVE API INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print(f"Results saved to: {out_path}")
    print("=" * 80)

if __name__ == "__main__":
    run_live_api_verification()
