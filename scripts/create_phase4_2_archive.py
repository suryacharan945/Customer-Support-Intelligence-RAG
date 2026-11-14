"""Package Stage 8 Phase 4.2 Independent Validation Artifacts into ZIP Archive."""

import os
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GDRIVE_DIR = Path("G:/My Drive/Internship_RAG_MCP_Capstone")
ARCHIVE_PATH = GDRIVE_DIR / "Stage8_Phase4_2_Independent_Validation.zip"

FILES_TO_INCLUDE = [
    # Deliverables & Audits
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "evaluation_report_phase4_2.md",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "implementation_audit.md",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "entity_compatibility_audit.md",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "policy_gate_audit.md",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "stage7b_metric_reconciliation.md",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "threshold_calibration.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "independent_validation_dataset.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "independent_validation_results.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "original_benchmark_results.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "regression_benchmark_results.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "latency_comparison.json",
    PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "claim_level_grounding_review.csv",
    # Implementation & Tests
    PROJECT_ROOT / "app" / "retrieval" / "evidence_gate.py",
    PROJECT_ROOT / "app" / "services" / "rag_service.py",
    PROJECT_ROOT / "app" / "generation" / "citation_validator.py",
    PROJECT_ROOT / "tests" / "test_stage8_phase4_2_hardening.py",
    PROJECT_ROOT / "scripts" / "run_stage8_phase4_2_evaluations.py",
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
            print(f"  - {name} ({info.file_size} bytes)")
    print("\nSUCCESS: Stage8_Phase4_2_Independent_Validation.zip created and verified successfully.")

if __name__ == "__main__":
    create_archive()
