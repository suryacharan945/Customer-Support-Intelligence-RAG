# Capstone Submission Package: Customer Support Intelligence Assistant

**Project Title**: Multi-Context Intelligent RAG System: Self-Improving, Agentic Platform for Advanced Customer Support  
**Candidate**: Surya Charan  
**Repository**: `C:\Users\surya\Internship_RAG_MCP_Capstone`  
**Primary Backup**: `G:\My Drive\Internship_RAG_MCP_Capstone`  
**Latest Git Commit**: `ee2f694`  
**Test Suite**: 148 / 148 Passing Tests (100%)  
**Submission Date**: 2026-10-28  

---

## 1. Submission Overview

This directory (`submission/`) contains the complete documentation, architectural diagrams, reproducible demonstration runbook, presentation materials, and evaluation artifacts for the Customer Support Intelligence Assistant internship capstone project.

The system implements a production-grade, decoupled Retrieval-Augmented Generation (RAG) platform enhanced with **Multi-Contextual Prompting (MCP)**. It solves the critical enterprise challenge of answering inquiries that simultaneously span technical specifications, troubleshooting workflows, and warranty contracts, achieving a **+57.5% improvement in citation precision** over standard single-channel dense RAG.

---

## 2. Directory Contents & Artifact Navigation

| File | Description & Purpose |
| :--- | :--- |
| [`FINAL_TECHNICAL_REPORT.md`](FINAL_TECHNICAL_REPORT.md) | Comprehensive 24-section technical report in academic markdown format. |
| [`FINAL_TECHNICAL_REPORT.pdf`](FINAL_TECHNICAL_REPORT.pdf) | Compiled PDF version of the technical report generated via ReportLab. |
| [`REQUIREMENTS_COMPLIANCE_MATRIX.md`](REQUIREMENTS_COMPLIANCE_MATRIX.md) | Detailed audit of all 29 specification requirements with supporting code and test evidence. |
| [`ARCHITECTURE_DIAGRAMS.md`](ARCHITECTURE_DIAGRAMS.md) | 10 reproducible Mermaid diagrams detailing system components, data flows, and security boundaries. |
| [`DEMONSTRATION_RUNBOOK.md`](DEMONSTRATION_RUNBOOK.md) | Step-by-step PowerShell guide for local setup, Colab GPU connection, and workflow demonstration. |
| [`FINAL_PRESENTATION_OUTLINE.md`](FINAL_PRESENTATION_OUTLINE.md) | 14-slide viva presentation outline with slide content and speaker notes. |
| [`EVALUATION_RESULTS_AND_METHODOLOGY.md`](EVALUATION_RESULTS_AND_METHODOLOGY.md) | Empirical analysis of development (32 inferences) and held-out (20 inferences) benchmarks. |
| [`HUMAN_EVALUATION_REVIEW_SHEET.md`](HUMAN_EVALUATION_REVIEW_SHEET.md) | Reviewer package with blank scoring fields (`[ ]`) for 20 held-out generations. |
| [`TEST_SUMMARY.md`](TEST_SUMMARY.md) | Regression test execution report across all 13 test suites (148 tests). |
| [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) | Honest disclosure of corpus scale, generation latency, and helpfulness bias on edge cases. |
| [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) | Pre-submission verification checklist confirming completion of all mandates. |

---

## 3. Quick Start (Reproducing the Project)

To run the local application and execute tests:

```powershell
# 1. Clone or navigate to the repository
cd C:\Users\surya\Internship_RAG_MCP_Capstone

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run automated tests (148 tests)
python -m pytest tests/

# 4. Start FastAPI backend (:8000)
uvicorn app.main:app --port 8000

# 5. In a second terminal, start Streamlit frontend (:8501)
streamlit run frontend/app.py --server.port 8501
```

For connecting live remote GPU inference with Mistral-7B, refer to the complete walkthrough in [`DEMONSTRATION_RUNBOOK.md`](DEMONSTRATION_RUNBOOK.md).
