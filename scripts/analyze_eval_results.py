import json

def analyze():
    for name in ["original_benchmark_results.json", "regression_benchmark_results.json", "independent_validation_results.json"]:
        path = f"evaluations/stage8_phase4_2/{name}"
        data = json.load(open(path, encoding="utf-8"))
        print("="*60)
        print(name)
        print("Summary:", data["summary_metrics"])
        fails = [r for r in data["detailed_results"] if r["verdict"] == "FAIL"]
        print(f"Total Fails: {len(fails)}")
        for r in fails:
            print(f"  {r['id']}: Exp={r['expected_status']} Act={r['actual_status']} | {r['query']}")

if __name__ == "__main__":
    analyze()
