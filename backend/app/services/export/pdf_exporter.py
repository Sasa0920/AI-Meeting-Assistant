import io
import html
from typing import Any, Dict, List

# pyrefly: ignore [missing-import]
from reportlab.lib import colors
# pyrefly: ignore [missing-import]
from reportlab.lib.pagesizes import letter
# pyrefly: ignore [missing-import]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
# pyrefly: ignore [missing-import]
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _escape(text: Any) -> str:
    """Safely escape text for ReportLab XML paragraph parsing."""
    if text is None:
        return ""
    return html.escape(str(text))


def generate_pdf_report(data: Dict[str, Any]) -> io.BytesIO:
    """Generate a professionally styled PDF report for meeting intelligence."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    primary_color = colors.HexColor("#4f46e5")  # Indigo
    dark_slate = colors.HexColor("#0f172a")     # Header slate
    text_color = colors.HexColor("#334155")     # Body slate
    muted_color = colors.HexColor("#64748b")    # Subtitles
    bg_tint = colors.HexColor("#f8fafc")        # Card background
    border_color = colors.HexColor("#e2e8f0")   # Soft border
    accent_green = colors.HexColor("#059669")   # Decision badge green

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=dark_slate,
        spaceAfter=4,
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=muted_color,
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=text_color,
    )

    summary_callout_style = ParagraphStyle(
        "SummaryCallout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=dark_slate,
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=text_color,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    decision_style = ParagraphStyle(
        "DecisionCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=14,
        textColor=dark_slate,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=text_color,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=dark_slate,
    )

    table_cell_muted = ParagraphStyle(
        "TableCellMuted",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=muted_color,
    )

    story: List[Any] = []

    # 1. Header & Metadata
    filename = _escape(data.get("filename", "Meeting Recording"))
    date_str = _escape(data.get("date_str", "N/A"))
    meeting_id = _escape(data.get("meeting_id", "N/A"))

    story.append(Paragraph(f"Meeting Report: {filename}", title_style))
    story.append(Paragraph(f"<b>Date:</b> {date_str} &nbsp;|&nbsp; <b>Meeting ID:</b> <code>{meeting_id}</code>", meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=12))

    # 2. Executive Summary
    summary_text = _escape(data.get("summary", "No executive summary available."))
    story.append(Paragraph("EXECUTIVE SUMMARY", section_heading_style))

    summary_p = Paragraph(summary_text, summary_callout_style)
    summary_table = Table([[summary_p]], colWidths=[532])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_tint),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("LINELEFT", (0, 0), (0, -1), 3.5, primary_color),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ])
    )
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # 3. Key Discussion Points
    key_points = data.get("key_points", [])
    if key_points:
        story.append(Paragraph("KEY DISCUSSION POINTS", section_heading_style))
        for point in key_points:
            story.append(Paragraph(f"&bull; {_escape(point)}", bullet_style))
        story.append(Spacer(1, 10))

    # 4. Decisions Made
    decisions = data.get("decisions", [])
    if decisions:
        story.append(Paragraph("DECISIONS MADE", section_heading_style))
        for decision in decisions:
            story.append(Paragraph(f"&bull; <font color='{accent_green}'>[AGREED]</font> {_escape(decision)}", decision_style))
        story.append(Spacer(1, 10))

    # 5. Action Items Table
    action_items = data.get("action_items", [])
    story.append(Paragraph(f"ACTION ITEMS ({len(action_items)})", section_heading_style))

    if not action_items:
        story.append(Paragraph("<i>No action items were identified in this meeting.</i>", body_style))
    else:
        # Table columns: Task (~60%), Assignee (~22%), Deadline (~18%)
        table_data = [
            [
                Paragraph("TASK", table_header_style),
                Paragraph("ASSIGNEE", table_header_style),
                Paragraph("DEADLINE", table_header_style),
            ]
        ]

        for item in action_items:
            task_desc = _escape(item.get("task", ""))
            assignee = item.get("assignee")
            deadline = item.get("deadline")

            assignee_p = (
                Paragraph(_escape(assignee), table_cell_bold)
                if assignee
                else Paragraph("Unassigned", table_cell_muted)
            )
            deadline_p = (
                Paragraph(_escape(deadline), table_cell_style)
                if deadline
                else Paragraph("None", table_cell_muted)
            )

            table_data.append([
                Paragraph(task_desc, table_cell_style),
                assignee_p,
                deadline_p,
            ])

        col_widths = [312, 120, 100]
        action_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, border_color),
        ]

        # Alternating row shading
        for r_idx in range(1, len(table_data)):
            if r_idx % 2 == 0:
                t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), bg_tint))
            else:
                t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), colors.white))

        action_table.setStyle(TableStyle(t_style))
        story.append(action_table)

    # 6. Build document
    doc.build(story)
    buffer.seek(0)
    return buffer
