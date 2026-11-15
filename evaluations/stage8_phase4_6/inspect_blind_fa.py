#!/usr/bin/env python3
import json

def inspect_fa():
    with open("evaluations/stage8_phase4_5/blind_compound_query_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    fa_list = [
        r for r in results 
        if r["expected_evidence_status"] in ["PARTIAL", "INSUFFICIENT"] 
        and r["predicted_evidence_status"] == "SUFFICIENT"
    ]
    print(f"Total False Acceptances in Blind Results: {len(fa_list)} / {len(results)}")
    for i, r in enumerate(fa_list, 1):
        print(f"\n[{i:02d}] ID: {r['id']} | Scenario: {r['scenario_name']}")
        print(f"    Query: {r['query']}")
        print(f"    Expected: {r['expected_evidence_status']} | Predicted: {r['predicted_evidence_status']}")
        print(f"    Is Compound: {r['decomposition']['is_compound']}")
        print(f"    Sub-questions detected: {r['decomposition']['sub_questions_detected']}")
        print(f"    Citations count: {len(r.get('citations', []))}")
        print(f"    Answer preview: {r.get('answer_preview')[:120]}...")

if __name__ == "__main__":
    inspect_fa()
