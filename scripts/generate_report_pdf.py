"""Convert FINAL_TECHNICAL_REPORT.md into a professional PDF using ReportLab."""

import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.units import inch

REPO_ROOT = Path("C:/Users/surya/Internship_RAG_MCP_Capstone")
md_path = REPO_ROOT / "submission" / "FINAL_TECHNICAL_REPORT.md"
pdf_path = REPO_ROOT / "submission" / "FINAL_TECHNICAL_REPORT.pdf"

print(f"Reading markdown from: {md_path}")
with open(md_path, "r", encoding="utf-8") as f:
    text = f.read()

doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=letter,
    leftMargin=0.75 * inch,
    rightMargin=0.75 * inch,
    topMargin=0.75 * inch,
    bottomMargin=0.75 * inch,
)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    "DocTitle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#1e3a8a"),
    spaceAfter=8,
)

subtitle_style = ParagraphStyle(
    "DocSubTitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#475569"),
    spaceAfter=12,
)

h1_style = ParagraphStyle(
    "DocH1",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=17,
    textColor=colors.HexColor("#1e3a8a"),
    spaceBefore=14,
    spaceAfter=6,
    keepWithNext=True,
)

h2_style = ParagraphStyle(
    "DocH2",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#334155"),
    spaceBefore=10,
    spaceAfter=4,
    keepWithNext=True,
)

h3_style = ParagraphStyle(
    "DocH3",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=9.5,
    leading=13,
    textColor=colors.HexColor("#475569"),
    spaceBefore=8,
    spaceAfter=3,
    keepWithNext=True,
)

body_style = ParagraphStyle(
    "DocBody",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor("#1e293b"),
    spaceAfter=6,
)

bullet_style = ParagraphStyle(
    "DocBullet",
    parent=body_style,
    leftIndent=15,
    spaceAfter=3,
)

code_style = ParagraphStyle(
    "DocCode",
    parent=styles["Normal"],
    fontName="Courier",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#0f172a"),
    spaceBefore=4,
    spaceAfter=6,
)

table_header_style = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#ffffff"),
)

table_cell_style = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#1e293b"),
)

flowables = []

lines = text.split("\n")
i = 0
in_code = False
code_lines = []

while i < len(lines):
    line = lines[i]

    # Code block toggles
    if line.strip().startswith("```"):
        if in_code:
            in_code = False
            code_text = "<br/>".join(
                [c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;") for c in code_lines]
            )
            # Create a code block table
            code_p = Paragraph(code_text, code_style)
            t = Table([[code_p]], colWidths=[7.0 * inch])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            flowables.append(t)
            flowables.append(Spacer(1, 6))
            code_lines = []
        else:
            in_code = True
            code_lines = []
        i += 1
        continue

    if in_code:
        code_lines.append(line)
        i += 1
        continue

    line_stripped = line.strip()

    # Empty line
    if not line_stripped:
        i += 1
        continue

    # Horizontal rule
    if line_stripped in ("---", "***", "___"):
        flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=8, spaceAfter=8))
        i += 1
        continue

    # Markdown Table detection
    if line_stripped.startswith("|") and line_stripped.endswith("|"):
        table_raw_lines = []
        while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
            table_raw_lines.append(lines[i].strip())
            i += 1

        if len(table_raw_lines) >= 2:
            # Parse header, separator, data
            headers = [c.strip() for c in table_raw_lines[0][1:-1].split("|")]
            # skip separator row if present
            start_row = 1
            if len(table_raw_lines) > 1 and "---" in table_raw_lines[1]:
                start_row = 2

            table_data = []
            # Header row
            header_row = [Paragraph(re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", h), table_header_style) for h in headers]
            table_data.append(header_row)

            for r_line in table_raw_lines[start_row:]:
                cells = [c.strip() for c in r_line[1:-1].split("|")]
                row_flow = []
                for idx_c, cell in enumerate(cells):
                    cell_clean = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", cell)
                    cell_clean = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", cell_clean)
                    row_flow.append(Paragraph(cell_clean, table_cell_style))
                # Pad if mismatch
                while len(row_flow) < len(headers):
                    row_flow.append(Paragraph("", table_cell_style))
                table_data.append(row_flow[: len(headers)])

            num_cols = len(headers)
            col_w = (7.0 * inch) / max(num_cols, 1)
            t = Table(table_data, colWidths=[col_w] * num_cols)
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("PADDING", (0, 0), (-1, -1), 4),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ]
                )
            )
            flowables.append(t)
            flowables.append(Spacer(1, 6))
            continue

    # Title
    if line_stripped.startswith("# ") and not line_stripped.startswith("## "):
        title_text = line_stripped[2:].strip()
        flowables.append(Paragraph(title_text, title_style))
        i += 1
        continue

    # H2
    if line_stripped.startswith("## "):
        h2_text = line_stripped[3:].strip()
        flowables.append(Paragraph(h2_text, h1_style))
        i += 1
        continue

    # H3
    if line_stripped.startswith("### "):
        h3_text = line_stripped[4:].strip()
        flowables.append(Paragraph(h3_text, h2_style))
        i += 1
        continue

    # H4
    if line_stripped.startswith("#### "):
        h4_text = line_stripped[5:].strip()
        flowables.append(Paragraph(h4_text, h3_style))
        i += 1
        continue

    # Bullet point
    if line_stripped.startswith("- ") or line_stripped.startswith("* "):
        bullet_text = line_stripped[2:].strip()
        bullet_text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", bullet_text)
        bullet_text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", bullet_text)
        flowables.append(Paragraph(f"&bull;&nbsp; {bullet_text}", bullet_style))
        i += 1
        continue

    # Numbered list
    num_match = re.match(r"^(\d+)\.\s+(.*)", line_stripped)
    if num_match:
        num_str = num_match.group(1)
        item_text = num_match.group(2)
        item_text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", item_text)
        item_text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", item_text)
        flowables.append(Paragraph(f"{num_str}.&nbsp; {item_text}", bullet_style))
        i += 1
        continue

    # Alert / blockquote
    if line_stripped.startswith(">"):
        quote_text = line_stripped.lstrip("> [!NOTE]").lstrip(">").strip()
        quote_text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", quote_text)
        qp = Paragraph(f"<b>Note:</b> {quote_text}", body_style)
        qt = Table([[qp]], colWidths=[7.0 * inch])
        qt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#93c5fd")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        flowables.append(qt)
        flowables.append(Spacer(1, 6))
        i += 1
        continue

    # Normal paragraph
    p_text = line_stripped
    p_text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", p_text)
    p_text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", p_text)
    p_text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", p_text)
    p_text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<u>\1</u>", p_text)
    flowables.append(Paragraph(p_text, body_style))
    i += 1

print(f"Building PDF with {len(flowables)} flowable elements...")
doc.build(flowables)
print(f"Successfully generated: {pdf_path} ({pdf_path.stat().st_size:,} bytes)")
