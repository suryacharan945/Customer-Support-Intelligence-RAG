import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.retrieval.vector_store import VectorStoreRetriever
from app.services.ingestion_service import ingestion_service

manifest = ingestion_service.manifest
active_docs = list(manifest.manifest_data.get("documents", {}).values())
print("=" * 80)
print(f"TOTAL ACTIVE DOCUMENTS IN MANIFEST: {len(active_docs)}")
print("=" * 80)

for d in active_docs:
    print(f"File: {d['filename']}")
    print(f"  Category: {d.get('category')} | Type: {d.get('document_type')} | Chunks: {d.get('chunk_count')} | Status: {d.get('lifecycle_status')}")

retriever = VectorStoreRetriever()
print(f"\nChromaDB Collection: '{retriever.collection_name}' | Total Chunks: {retriever._collection.count()}")

# Get all chunks
res = retriever._collection.get(include=["documents", "metadatas"])
print(f"\nRetrieved {len(res['ids'])} chunks from ChromaDB:")
chunks_by_file = {}
for cid, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
    fname = meta.get("filename") or meta.get("source") or "unknown"
    if fname not in chunks_by_file:
        chunks_by_file[fname] = []
    chunks_by_file[fname].append((cid, meta.get("page", meta.get("section", 1)), doc[:100].replace("\n", " ")))

for fname, chs in sorted(chunks_by_file.items()):
    print(f"\nDocument: {fname} ({len(chs)} chunks)")
    for cid, loc, preview in chs:
        print(f"   [{cid}] (Loc: {loc}): {preview}...")
