#!/usr/bin/env python3
"""
Generate the Human Review Template for Stage 8 Phase 4.5.

Produces evaluations/stage8_phase4_5/human_review_phase4_5.csv with a stratified
sample of 32 queries across SUFFICIENT, PARTIAL, and INSUFFICIENT evidence statuses.
Leaves human rater columns strictly blank for independent audit and verification,
preventing any fabricated scores.
"""

import csv
import json
from pathlib import Path

def generate_human_review_csv():
    # Load historical results for samples
    recon_path = Path("evaluations/stage8_phase4_5/benchmark_reconciliation.json")
    with open(recon_path, "r", encoding="utf-8") as f:
        recon_data = json.load(f)

    all_audited = recon_data.get("records", [])
    print(f"Loaded {len(all_audited)} audited queries for stratified sampling.")

    # Stratified selection
    # Select:
    # 12 SUFFICIENT
    # 10 PARTIAL
    # 10 INSUFFICIENT
    sample = []
    counts = {"SUFFICIENT": 0, "PARTIAL": 0, "INSUFFICIENT": 0}
    target_counts = {"SUFFICIENT": 12, "PARTIAL": 10, "INSUFFICIENT": 10}

    # First from compound/partial queries
    for q in all_audited:
        status = q.get("actual_status")
        if status in target_counts and counts[status] < target_counts[status]:
            sample.append(q)
            counts[status] += 1

    print(f"Sampled {len(sample)} queries: {counts}")

    csv_path = Path("evaluations/stage8_phase4_5/human_review_phase4_5.csv")
    fieldnames = [
        "query_id",
        "benchmark_suite",
        "query_text",
        "evidence_status",
        "is_compound",
        "sub_questions",
        "retrieved_passages_preview",
        "generated_answer",
        "citation_tags",
        # Human evaluation blank columns
        "rater_id",
        "decomposition_accuracy_1_to_5",
        "evidence_sufficiency_classification_correct_yn",
        "factual_grounding_score_1_to_5",
        "hallucination_detected_yn",
        "citation_validity_yn",
        "answer_fluency_1_to_5",
        "overall_quality_rating_1_to_5",
        "release_verdict_accept_reject",
        "reviewer_notes"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for item in sample:
            writer.writerow({
                "query_id": item.get("query_id", ""),
                "benchmark_suite": item.get("suite", ""),
                "query_text": item.get("query", "").replace("\n", " "),
                "evidence_status": item.get("actual_status", ""),
                "is_compound": "YES" if item.get("is_compound") else "NO",
                "sub_questions": "; ".join(item.get("actual_sub_questions", [])) if item.get("actual_sub_questions") else "",
                "retrieved_passages_preview": f"{item.get('retrieved_chunk_count', 0)} chunks retrieved",
                "generated_answer": item.get("answer_preview", "").replace("\n", " ").strip(),
                "citation_tags": f"Verified citations: {item.get('verified_citation_count', 0)}",
                # Blank rater columns
                "rater_id": "",
                "decomposition_accuracy_1_to_5": "",
                "evidence_sufficiency_classification_correct_yn": "",
                "factual_grounding_score_1_to_5": "",
                "hallucination_detected_yn": "",
                "citation_validity_yn": "",
                "answer_fluency_1_to_5": "",
                "overall_quality_rating_1_to_5": "",
                "release_verdict_accept_reject": "",
                "reviewer_notes": ""
            })

    print(f"Successfully generated {csv_path} with {len(sample)} stratified review rows.")

if __name__ == "__main__":
    generate_human_review_csv()
