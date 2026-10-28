"""Audit all 10 held-out questions against the 9 synthetic source documents.

Verifies:
1. Whether their answers exist in the original 9 source documents.
2. Whether they duplicate development questions semantically.
3. Whether reference answers are supported by actual source passages.
4. Whether any question is ambiguous or unanswerable.
"""

import json
from pathlib import Path

KB_DIR = Path("G:/My Drive/Internship_RAG_MCP_Capstone/03_Knowledge_Base")
HO_PATH = Path("evaluation/held_out_dataset.json")
DEV_PATH = Path("evaluation/stage7b_live_results.json")

with open(HO_PATH, "r", encoding="utf-8") as f:
    ho_data = json.load(f)

with open(DEV_PATH, "r", encoding="utf-8") as f:
    dev_data = json.load(f)

ho_queries = ho_data["held_out_queries"]
dev_queries = dev_data["queries_benchmark_results"]

# Load all 9 documents text
all_kb_text = {}
for md_file in KB_DIR.rglob("*.md"):
    with open(md_file, "r", encoding="utf-8") as f:
        all_kb_text[md_file.name] = f.read()

print(f"Loaded {len(all_kb_text)} KB documents from Google Drive.")

audit_records = []
for q in ho_queries:
    qid = q["query_id"]
    query = q["query"]
    cat = q["domain_category"]
    expected_sources = q["expected_sources"]
    ground_truth_claims = q["ground_truth_claims"]

    # Check existence in KB
    found_in_docs = []
    missing_claims = []
    for claim in ground_truth_claims:
        claim_lower = claim.lower()
        matched = False
        for fname, text in all_kb_text.items():
            text_lower = text.lower()
            # check key token overlap
            tokens = [t for t in claim_lower.split() if len(t) > 3 and t not in ["under", "from", "with", "that", "this", "only"]]
            match_count = sum(1 for t in tokens if t in text_lower)
            if tokens and (match_count / len(tokens)) >= 0.6:
                found_in_docs.append(fname)
                matched = True
                break
        if not matched and cat not in ["out_of_domain", "prompt_injection"]:
            missing_claims.append(claim)

    # Check semantic duplication with Dev queries
    semantic_overlap = []
    for dq in dev_queries:
        dq_text = dq["query"].lower()
        # Check overlap of significant tokens
        q_tokens = set(query.lower().split())
        dq_tokens = set(dq_text.split())
        overlap = q_tokens.intersection(dq_tokens) - {"what", "is", "the", "how", "do", "i", "a", "to", "for", "and", "or", "on"}
        if len(overlap) >= 4:
            semantic_overlap.append((dq["query_id"], dq["query"]))

    audit_records.append({
        "query_id": qid,
        "query": query,
        "category": cat,
        "expected_sources": expected_sources,
        "claims_count": len(ground_truth_claims),
        "found_sources": list(set(found_in_docs)),
        "missing_claims": missing_claims,
        "semantic_overlap_count": len(semantic_overlap),
        "semantic_overlap_details": semantic_overlap,
        "is_answerable": cat != "out_of_domain",
    })

print(f"\n--- HELD-OUT AUDIT SUMMARY ({len(audit_records)} Questions) ---")
for r in audit_records:
    status = "OK" if not r["missing_claims"] and r["semantic_overlap_count"] == 0 else "FLAGGED"
    print(f"[{r['query_id']}] Category={r['category']} | Status={status} | MissingClaims={len(r['missing_claims'])} | DevOverlap={r['semantic_overlap_count']}")
    if r["semantic_overlap_details"]:
        print(f"   Potential Dev Overlap: {r['semantic_overlap_details']}")
