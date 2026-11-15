"""Audit threshold calibration split and data."""

import json

data = json.load(open("evaluations/stage8_phase4_2/threshold_calibration.json", encoding="utf-8"))

print("Keys:", data.keys())
metadata = data.get("calibration_metadata", {})
print("\nMetadata:")
for k, v in metadata.items():
    print(f"  {k}: {v}")

splits = data.get("splits", {})
for s_name, s_data in splits.items():
    qs = s_data.get("queries", [])
    supp = sum(1 for q in qs if q.get("is_supported"))
    unsupp = sum(1 for q in qs if not q.get("is_supported"))
    print(f"\nSplit: {s_name} (Total: {len(qs)}, Supported: {supp}, Unsupported: {unsupp})")
    for q in qs:
        print(f"  {q.get('id')}: Supp={q.get('is_supported')} | Score={q.get('dense_similarity_score')} | {q.get('query')[:50]}...")

grid = data.get("threshold_grid_search", {})
print("\nGrid Search Results:")
for th, res in grid.items():
    print(f"  Threshold {th}: Combined Acc = {res.get('combined_accuracy')} | FAR={res.get('false_acceptance_rate_ood')} | FRR={res.get('false_rejection_rate_supported')}")
