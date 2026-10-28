import json
from pathlib import Path

nb_path = Path("notebooks/02_colab_mistral_rag_inference.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
for i, cell in enumerate(nb["cells"]):
    src = "".join(cell.get("source", []))
    lines = src.split("\n")
    matches = [l for l in lines if any(k in l.lower() for k in ["model_id", "zephyr", "fallback", "secret", "token", "auth", "cloudflare", "trycloudflare"])]
    if matches:
        print(f"\n--- Cell {i} ({cell.get('cell_type')}) ---")
        for m in matches[:6]:
            print("   ", m.strip())
