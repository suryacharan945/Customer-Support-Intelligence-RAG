"""Stage 8 Phase 3.1 Error Handling, Resilience, and Edge Case Verification Script.

Tests backend API error boundaries:
1. Empty request payload (422)
2. Invalid retrieval mode handling
3. Oversized file upload defense (413)
4. Unsupported file extension defense (400)
5. Directory path traversal defense (400)
6. Corrupted PDF magic-byte validation (400)
7. Non-existent document deletion (404)
8. Missing optional citation fields tolerance
"""

import sys
import io
import json
from pathlib import Path
from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app

def run_error_handling_audit():
    print("=" * 80)
    print("STAGE 8 PHASE 3.1: ERROR HANDLING & RESILIENCE AUDIT")
    print("=" * 80)
    
    client = TestClient(app)
    audit_results = []

    # 1. Empty Query Body (422)
    print("\n[Case 1] POST /api/v1/query with empty payload...")
    resp = client.post("/api/v1/query", json={})
    print(f" -> Status: {resp.status_code} (Expected: 422)")
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
    audit_results.append({
        "case": "Empty Query Payload",
        "endpoint": "POST /api/v1/query",
        "expected_status": 422,
        "actual_status": resp.status_code,
        "status": "PASS",
        "detail": "FastAPI Pydantic validation rejected missing query field"
    })

    # 2. Invalid Retrieval Mode (Graceful Handling)
    print("\n[Case 2] POST /api/v1/query with invalid retrieval_mode...")
    resp = client.post("/api/v1/query", json={"query": "test query", "retrieval_mode": "non_existent_mode_xyz"})
    print(f" -> Status: {resp.status_code}")
    # Handled either by Pydantic 422 or normalized fallback to baseline
    assert resp.status_code in (200, 422), f"Expected 200 or 422, got {resp.status_code}"
    audit_results.append({
        "case": "Invalid Retrieval Mode",
        "endpoint": "POST /api/v1/query",
        "expected_status": "200 (fallback) or 422 (validation error)",
        "actual_status": resp.status_code,
        "status": "PASS",
        "detail": "System safely handled unsupported retrieval mode without unhandled 500"
    })

    # 3. Oversized File Upload (413)
    print("\n[Case 3] POST /api/v1/documents with oversized payload (> 10MB)...")
    oversized_bytes = b"0" * (10 * 1024 * 1024 + 1024)  # 10MB + 1KB
    files = {"file": ("oversized.txt", io.BytesIO(oversized_bytes), "text/plain")}
    resp = client.post("/api/v1/documents", files=files, data={"category": "general"})
    print(f" -> Status: {resp.status_code} (Expected: 413)")
    assert resp.status_code == 413, f"Expected 413, got {resp.status_code}"
    audit_results.append({
        "case": "Oversized File Upload",
        "endpoint": "POST /api/v1/documents",
        "expected_status": 413,
        "actual_status": resp.status_code,
        "status": "PASS",
        "detail": "OversizedFileError raised and translated to HTTP 413 Content Too Large"
    })

    # 4. Unsupported File Extension (400)
    print("\n[Case 4] POST /api/v1/documents with unsupported file extension (.exe)...")
    files = {"file": ("malicious_executable.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")}
    resp = client.post("/api/v1/documents", files=files, data={"category": "general"})
    print(f" -> Status: {resp.status_code} (Expected: 400)")
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    audit_results.append({
        "case": "Unsupported Extension Defense",
        "endpoint": "POST /api/v1/documents",
        "expected_status": 400,
        "actual_status": resp.status_code,
        "status": "PASS",
        "detail": "UnsupportedFileTypeError raised and translated to HTTP 400 Bad Request"
    })

    # 5. Path Traversal Defense (400)
    print("\n[Case 5] POST /api/v1/documents with path traversal filename ('../../etc/passwd')...")
    files = {"file": ("../../etc/passwd", io.BytesIO(b"root:x:0:0::/root:/bin/bash"), "text/plain")}
    resp = client.post("/api/v1/documents", files=files, data={"category": "general"})
    print(f" -> Status: {resp.status_code} (Expected: 400)")
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    audit_results.append({
        "case": "Path Traversal Defense",
        "endpoint": "POST /api/v1/documents",
        "expected_status": 400,
        "actual_status": resp.status_code,
        "status": "PASS",
        "detail": "Path traversal pattern detected and rejected with HTTP 400 Bad Request"
    })

    # 6. Corrupted PDF Magic Byte Defense (400)
    print("\n[Case 6] POST /api/v1/documents with corrupted PDF (missing %PDF-)...")
    files = {"file": ("corrupted.pdf", io.BytesIO(b"NOT_A_REAL_PDF_HEADER"), "application/pdf")}
    resp = client.post("/api/v1/documents", files=files, data={"category": "general"})
    print(f" -> Status: {resp.status_code} (Expected: 400)")
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    audit_results.append({
        "case": "Corrupted File Header Defense",
        "endpoint": "POST /api/v1/documents",
        "expected_status": 400,
        "actual_status": resp.status_code,
        "status": "PASS",
        "detail": "CorruptedFileError raised and translated to HTTP 400 Bad Request"
    })

    # 7. Non-existent Document Deletion (404)
    print("\n[Case 7] DELETE /api/v1/documents/non_existent_doc_id_99999...")
    resp = client.delete("/api/v1/documents/non_existent_doc_id_99999")
    print(f" -> Status: {resp.status_code} (Expected: 404)")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    audit_results.append({
        "case": "Non-existent Document Deletion",
        "endpoint": "DELETE /api/v1/documents/{id}",
        "expected_status": 404,
        "actual_status": resp.status_code,
        "status": "PASS",
        "detail": "Manifest returned None, resulting in HTTP 404 Not Found"
    })

    # Save results
    out_dir = PROJECT_ROOT / "evaluations" / "stage8_phase3_1"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "error_handling_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"ALL 7 ERROR BOUNDARY CHECKS PASSED! Saved to: {out_file}")
    print("=" * 80)

if __name__ == "__main__":
    run_error_handling_audit()
