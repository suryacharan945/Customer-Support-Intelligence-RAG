"""CLI entrypoint for standalone knowledge base ingestion and preprocessing."""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ingestion_service import IngestionService
from app.ingestion.loader import VALID_CATEGORIES


def main():
    parser = argparse.ArgumentParser(
        description="Customer Support Knowledge Base Ingestion CLI"
    )
    parser.add_argument("path", help="Path to file or directory to ingest")
    parser.add_argument(
        "--category",
        choices=sorted(list(VALID_CATEGORIES)),
        help="Document category (mandatory if ingesting a single file)",
    )
    parser.add_argument("--force", action="store_true", help="Force re-indexing of duplicate files")
    parser.add_argument("--manifest", help="Custom path for manifest file")

    args = parser.parse_args()
    target_path = Path(args.path)

    if not target_path.exists():
        print(f"[ERROR] Path does not exist: {target_path}")
        sys.exit(1)

    service = IngestionService(manifest_path=args.manifest)

    if target_path.is_file():
        if not args.category:
            print("[ERROR] --category is required when ingesting a single file.")
            sys.exit(1)
        res = service.ingest_file(target_path, category=args.category, force_reindex=args.force)
        print("Ingestion result:")
        print(f"  Status: {res['status']}")
        print(f"  Doc ID: {res['document_id']}")
        print(f"  Chunks: {res['chunk_count']}")
    else:
        summary = service.ingest_directory(target_path, category=args.category, force_reindex=args.force)
        print("Batch Ingestion Summary:")
        print(f"  Files Scanned:       {summary['total_files_scanned']}")
        print(f"  Processed / Updated: {summary['processed']}")
        print(f"  Duplicates Skipped:  {summary['skipped_duplicates']}")
        print(f"  Total Chunks:        {summary['total_chunks_created']}")
        if summary["errors"]:
            print(f"  Errors ({len(summary['errors'])}):")
            for err in summary["errors"]:
                print(f"    - {err['filename']}: {err['error']}")


if __name__ == "__main__":
    main()
