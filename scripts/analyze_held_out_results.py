"""Aggregate and analyze Stage 8B Held-Out benchmark results."""

import json
from pathlib import Path

results_file = Path("C:/Users/surya/Internship_RAG_MCP_Capstone/evaluation/stage8b_held_out_live_results.json")
with open(results_file, "r", encoding="utf-8") as f:
    data = json.load(f)

queries = data["held_out_benchmark_results"]
print(f"Total Held-Out Queries: {len(queries)}")

# Metrics accumulators
b_latencies = []
m_latencies = []
b_gen_latencies = []
m_gen_latencies = []
b_precisions = []
m_precisions = []
b_chars = []
m_chars = []

b_citations_asserted = 0
b_citations_verified = 0
m_citations_asserted = 0
m_citations_verified = 0

print("\n" + "=" * 90)
print(f"{'Query ID':<25} | {'Mode':<14} | {'Cat Routed':<20} | {'Prec':<5} | {'Lat (s)':<7} | {'Chars':<5} | {'Citations':<10}")
print("=" * 90)

for q in queries:
    qid = q["query_id"]
    b = q["baseline"]
    m = q["multi_context"]

    # Baseline metrics
    b_lat = b["total_latency_ms"] / 1000.0
    b_gen = b["generation_latency_ms"] / 1000.0
    b_prec = b["citation_precision"]
    b_char = len(b["answer_text"])
    b_cits = len(b["supporting_citations"])

    b_latencies.append(b_lat)
    b_gen_latencies.append(b_gen)
    b_precisions.append(b_prec)
    b_chars.append(b_char)

    # Multi-Context metrics
    m_lat = m["total_latency_ms"] / 1000.0
    m_gen = m["generation_latency_ms"] / 1000.0
    m_prec = m["citation_precision"]
    m_char = len(m["answer_text"])
    m_cits = len(m["supporting_citations"])
    m_cats = ",".join(m["selected_categories"])

    m_latencies.append(m_lat)
    m_gen_latencies.append(m_gen)
    m_precisions.append(m_prec)
    m_chars.append(m_char)

    print(f"{qid:<25} | {'BASELINE':<14} | {'(all/dense)':<20} | {b_prec:<5.2f} | {b_lat:<7.2f} | {b_char:<5} | {b_cits:<10}")
    print(f"{'':<25} | {'MULTI-CONTEXT':<14} | {m_cats:<20} | {m_prec:<5.2f} | {m_lat:<7.2f} | {m_char:<5} | {m_cits:<10}")
    print("-" * 90)

print("\n" + "=" * 50)
print("AGGREGATE METRICS SUMMARY")
print("=" * 50)
print(f"BASELINE:")
print(f"  Mean Total Latency:       {sum(b_latencies)/len(b_latencies):.2f} s")
print(f"  Mean Generation Latency:  {sum(b_gen_latencies)/len(b_gen_latencies):.2f} s")
print(f"  Mean Citation Precision:  {sum(b_precisions)/len(b_precisions):.2%}")
print(f"  Mean Answer Length:       {sum(b_chars)/len(b_chars):.1f} chars")

print(f"\nMULTI-CONTEXT (MCP):")
print(f"  Mean Total Latency:       {sum(m_latencies)/len(m_latencies):.2f} s")
print(f"  Mean Generation Latency:  {sum(m_gen_latencies)/len(m_gen_latencies):.2f} s")
print(f"  Mean Citation Precision:  {sum(m_precisions)/len(m_precisions):.2%}")
print(f"  Mean Answer Length:       {sum(m_chars)/len(m_chars):.1f} chars")
