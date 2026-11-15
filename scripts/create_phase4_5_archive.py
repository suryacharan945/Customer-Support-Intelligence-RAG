"""Package Stage 8 Phase 4.5 Independent Validation Artifacts into ZIP Archive."""

import os
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GDRIVE_DIR = Path("G:/My Drive/Internship_RAG_MCP_Capstone")
ARCHIVE_PATH = GDRIVE_DIR / "Stage8_Phase4_5_Validation_Audit.zip"

FILES_TO_INCLUDE = [
    # All 13 Deliverables in evaluations/stage8_phase4_5
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "phase4_5_validation_plan.md",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "phase4_5_baseline_manifest.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "benchmark_reconciliation.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "benchmark_reconciliation_report.md",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "blind_compound_query_dataset.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "blind_compound_query_results.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "decomposition_metrics.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "claim_grounding_audit.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "human_review_phase4_5.csv",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "adversarial_test_results.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "latency_profile.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "regression_comparison.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "evaluation_report_phase4_5.md",
    # Evaluation execution scripts
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "reconcile_benchmarks.py",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "create_blind_dataset.py",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "evaluate_blind_queries.py",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "generate_human_review_csv.py",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "run_adversarial_suite.py",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_5" / "compile_regression_comparison.py",
    # Core baseline implementation
    PROJECT_ROOT / "app" / "retrieval" / "query_decomposer.py",
    PROJECT_ROOT / "app" / "retrieval" / "evidence_coverage.py",
    PROJECT_ROOT / "app" / "retrieval" / "evidence_gate.py",
    PROJECT_ROOT / "app" / "services" / "rag_service.py",
    PROJECT_ROOT / "app" / "generation" / "local_synthesizer.py",
    PROJECT_ROOT / "app" / "generation" / "citation_validator.py",
    PROJECT_ROOT / "tests" / "test_stage8_phase4_4_decomposition.py",
]

def create_archive():
    GDRIVE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Creating archive at: {ARCHIVE_PATH}")
    with zipfile.ZipFile(ARCHIVE_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in FILES_TO_INCLUDE:
            if not f.exists():
                print(f"WARNING: File missing: {f}")
                continue
            arcname = f.relative_to(PROJECT_ROOT)
            zf.write(f, arcname=str(arcname))
            print(f"  Added: {arcname} ({f.stat().st_size} bytes)")

    print(f"\nVerifying archive: {ARCHIVE_PATH} ({ARCHIVE_PATH.stat().st_size} bytes)")
    with zipfile.ZipFile(ARCHIVE_PATH, "r") as zf:
        namelist = zf.namelist()
        print(f"Archive contains {len(namelist)} files.")
        for name in namelist:
            info = zf.getinfo(name)
            print(f"  [OK] {name} ({info.file_size} -> {info.compress_size} bytes)")

if __name__ == "__main__":
    create_archive()
