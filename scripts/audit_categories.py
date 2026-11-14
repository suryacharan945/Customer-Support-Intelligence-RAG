import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ingestion_service import IngestionService
from app.ingestion.loader import VALID_CATEGORIES, DocumentLoader, InvalidCategoryError

categories = [
    "general",
    "engineering",
    "architecture",
    "evaluation",
    "product_manual",
    "troubleshooting",
    "warranty",
    "faq",
]

print("=" * 70)
print("AUDITING CURRENT BACKEND CATEGORY COMPATIBILITY")
print("=" * 70)
print(f"Current VALID_CATEGORIES: {sorted(list(VALID_CATEGORIES))}\n")

print("--- 1. Testing DocumentLoader.validate_category directly ---")
loader = DocumentLoader()
for cat in categories:
    try:
        norm = loader.validate_category(cat)
        print(f"  {cat:16}: ACCEPTED -> '{norm}'")
    except InvalidCategoryError as e:
        print(f"  {cat:16}: REJECTED by DocumentLoader.validate_category ({e})")

print("\n--- 2. Testing IngestionService.process_uploaded_file ---")
with tempfile.TemporaryDirectory() as tmp_dir:
    manifest_path = Path(tmp_dir) / "test_manifest.json"
    service = IngestionService(manifest_path=manifest_path)
    
    for cat in categories:
        content = f"# Test Document for {cat}\n\nTesting category metadata preservation for {cat}.\n".encode("utf-8")
        filename = f"test_{cat}.md"
        try:
            res = service.process_uploaded_file(
                filename=filename,
                content=content,
                category=cat,
                vector_retriever=None,
                bm25_retriever=None
            )
            saved_cat = res.get("category")
            if saved_cat == cat:
                print(f"  {cat:16}: SUCCESS -> Persisted as '{saved_cat}'")
            else:
                print(f"  {cat:16}: SILENT OVERRIDE -> Requested '{cat}' but persisted as '{saved_cat}'")
        except Exception as e:
            print(f"  {cat:16}: EXCEPTION -> {e}")
