"""Inspect the 32 queries in the independent validation dataset."""

import json

data = json.load(open("evaluations/stage8_phase4_2/independent_validation_dataset.json", encoding="utf-8"))
questions = data["questions"]

print(f"Total questions: {len(questions)}")
print("\nQuestions breakdown:")
for q in questions:
    print(f"[{q['id']}] Cat: {q['taxonomy_category']:<30} | Supp: {str(q['is_supported']):<5} | Exp: {q['expected_evidence_status']:<12}")
    print(f"  Q: {q['query']}")
    print(f"  Rationale: {q.get('labeling_rationale')}")
    print()
