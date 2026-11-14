import json

with open("evaluations/stage8_phase4/abstention_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)
print("ABSTENTION SUMMARY:")
print(json.dumps(d, indent=2))

with open("evaluations/stage8_phase4/answer_quality_results.json", "r", encoding="utf-8") as f:
    q = json.load(f)

print("\nOOD QUESTIONS DETAILS (Q46-Q50):")
for item in q["detailed_results"][45:]:
    print(f"\nID: {item['id']}")
    print(f"Query: {item['query']}")
    print(f"Actual Status: {item['actual_status']}")
    print(f"Classification: {item['abstention_classification']}")
    print(f"Preview: {item['answer_preview']}")
