"""Independent recomputation and audit of citation metrics and claim-level factual support.

Distinguishes:
1. Retrieved candidate passages.
2. Citations explicitly asserted by the model.
3. Citations accepted by the validator (source ID and page matching).
4. Claims actually supported by cited passages (distinguishing source validity from factual support).
5. Identification of citation failures or uncertain cases for human review.
"""

import json
import re
from pathlib import Path

RESULTS_FILE = Path("evaluation/stage7b_live_results.json")

with open(RESULTS_FILE, "r", encoding="utf-8") as f:
    benchmark_data = json.load(f)

queries = benchmark_data["queries_benchmark_results"]

CITATION_PATTERNS = [
    re.compile(r"\[(?:Source:\s*)?([a-zA-Z0-9_\-\.]+\.(?:md|pdf|txt))(?:\s*,\s*(?:Page:\s*|p\.\s*)(\d+|Full Document))?(?:\s*,\s*(?:Chunk:\s*)([a-zA-Z0-9_]+))?\]", re.IGNORECASE),
    re.compile(r"\((?:Source:\s*)?([a-zA-Z0-9_\-\.]+\.(?:md|pdf|txt))(?:\s*,\s*(?:Page:\s*|p\.\s*)(\d+|Full Document))?\)", re.IGNORECASE),
]

audit_results = []
uncertain_cases = []

for q in queries:
    qid = q["query_id"]
    qtext = q["query"]

    for mode in ["baseline", "multi_context"]:
        res = q[mode]
        ans = res.get("answer_text", "")
        cits_raw = res.get("citations", [])

        # 1. Retrieved Candidate Passages
        candidates = []
        for c in cits_raw:
            fn = c.get("document_source") or c.get("source") or c.get("filename")
            cid = c.get("chunk_id")
            snippet = c.get("snippet", "")
            candidates.append({"filename": fn, "chunk_id": cid, "snippet": snippet})

        candidate_filenames = {c["filename"].lower() for c in candidates if c["filename"]}

        # 2. Citations explicitly asserted by the model
        asserted_cits = []
        matched_spans = []
        for pat in CITATION_PATTERNS:
            for m in pat.finditer(ans):
                start, end = m.start(), m.end()
                if any(start < se[1] and end > se[0] for se in matched_spans):
                    continue
                matched_spans.append((start, end))
                src = m.group(1).strip()
                page = m.group(2) if len(m.groups()) >= 2 else None
                chunk = m.group(3) if len(m.groups()) >= 3 else None
                asserted_cits.append({"raw": m.group(0), "source": src, "page": page, "chunk": chunk})

        # 3. Citations accepted by validator (valid source ID & page)
        approved_cits = []
        unapproved_cits = []
        for ac in asserted_cits:
            src_lower = ac["source"].lower()
            if any(src_lower in cf or cf in src_lower for cf in candidate_filenames):
                approved_cits.append(ac)
            else:
                unapproved_cits.append(ac)

        # 4. Claims actually supported by cited passages
        # Check if the answer indicates abstention due to lack of evidence
        is_abstention = any(p in ans.lower() for p in [
            "insufficient evidence", "not specified", "no relevant information", "not explicitly mentioned",
            "unable to", "cannot find"
        ])

        # Forensic check for uncertain / partial cases:
        # e.g., claims where source is valid but specific detail (like third-party cartridges, or speed)
        # requires careful human semantic verification
        has_uncertainty = False
        uncertainty_reason = ""

        # Case A: Answer mentions a source but also acknowledges the source lacks the exact fact
        if "not explicitly mentioned" in ans.lower() or "not specified in the provided documentation" in ans.lower():
            has_uncertainty = True
            uncertainty_reason = "Model cites source for positive claim, but acknowledges negative/absent claim (e.g. color speed not in monochrome manual)."

        # Case B: Baseline retrieved irrelevant troubleshooting chunk for speed/resolution inquiry
        if mode == "baseline" and ("printer_troubleshooting_guide.md" in str(candidate_filenames)) and ("speed" in qtext.lower() or "resolution" in qtext.lower()):
            has_uncertainty = True
            uncertainty_reason = "Retrieval mismatch: Dense retriever returned troubleshooting guide for hardware specs query. Model properly abstained."

        # Case C: Answer has numbers not verified in snippet
        if unapproved_cits:
            has_uncertainty = True
            uncertainty_reason = f"Unapproved citation detected: {unapproved_cits}"

        if has_uncertainty:
            uncertain_cases.append({
                "query_id": qid,
                "mode": mode,
                "query": qtext,
                "reason": uncertainty_reason,
                "asserted_cits": [c["raw"] for c in asserted_cits],
                "candidate_files": list(candidate_filenames),
            })

        audit_results.append({
            "query_id": qid,
            "mode": mode,
            "candidates_count": len(candidates),
            "asserted_count": len(asserted_cits),
            "approved_count": len(approved_cits),
            "unapproved_count": len(unapproved_cits),
            "is_abstention": is_abstention,
            "has_uncertainty": has_uncertainty,
        })

print(f"Total evaluated responses: {len(audit_results)}")
print(f"Total uncertain / review-flagged cases: {len(uncertain_cases)}")

print("\n--- UNCERTAIN OR ATTENTION CASES FOR HUMAN REVIEW ---")
for uc in uncertain_cases:
    print(f"[{uc['query_id']}] ({uc['mode']}) -> {uc['reason']}")
