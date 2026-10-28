"""Inspect ho_09 and ho_10 answers."""
import json
from pathlib import Path

results_file = Path("C:/Users/surya/Internship_RAG_MCP_Capstone/evaluation/stage8b_held_out_live_results.json")
with open(results_file, "r", encoding="utf-8") as f:
    data = json.load(f)

for q in data["held_out_benchmark_results"]:
    if q["query_id"] in ["ho_09_unsupported_bluetooth_audio", "ho_10_prompt_injection_safety"]:
        print("=" * 80)
        print(f"QUERY ID: {q['query_id']}")
        print(f"QUERY:    {q['query']}")
        print("-" * 80)
        print("BASELINE ANSWER:")
        print(q["baseline"]["answer_text"])
        print("-" * 80)
        print("MULTI-CONTEXT ANSWER:")
        print(q["multi_context"]["answer_text"])
        print("=" * 80)
