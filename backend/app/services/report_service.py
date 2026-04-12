"""Report service — report CRUD and PDF generation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.report import Report

logger = get_logger("service.report")


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_report(self, report_id: uuid.UUID) -> Report:
        report = await self.db.get(Report, report_id)
        if not report:
            raise NotFoundError("Report", report_id)
        return report

    async def list_reports(
        self,
        patient_id: Optional[uuid.UUID] = None,
        report_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Report], int]:
        from sqlalchemy import func
        query = select(Report)
        if patient_id:
            query = query.where(Report.patient_id == patient_id)
        if report_type:
            query = query.where(Report.report_type == report_type)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        query = query.order_by(Report.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def add_physician_notes(
        self, report_id: uuid.UUID, notes: str, reviewer_id: uuid.UUID
    ) -> Report:
        report = await self.get_report(report_id)
        report.physician_notes = notes
        report.reviewed_by = reviewer_id
        report.reviewed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return report

    async def delete_report(self, report_id: uuid.UUID) -> None:
        report = await self.get_report(report_id)
        await self.db.delete(report)
        await self.db.flush()

    async def export_pdf(self, report_id: uuid.UUID) -> bytes:
        """Generate a physician-ready clinical PDF report using ReportLab."""
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            HRFlowable,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        report = await self.get_report(report_id)
        content = report.content or {}
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title", parent=styles["Title"], fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1e293b")
        )
        heading_style = ParagraphStyle(
            "Heading", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=4,
            textColor=colors.HexColor("#1e40af"),
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"], fontSize=10, spaceAfter=4, leading=14
        )
        warning_style = ParagraphStyle(
            "Warning", parent=styles["Normal"], fontSize=10, backColor=colors.HexColor("#fef3c7"),
            borderColor=colors.HexColor("#f59e0b"), borderWidth=1, borderPadding=6,
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer", parent=styles["Normal"], fontSize=8, textColor=colors.gray,
            spaceAfter=4, leading=11,
        )

        elements = []
        # Header
        elements.append(Paragraph("SymptaAI Clinical Report", title_style))
        elements.append(Paragraph(report.title, styles["Heading3"]))
        elements.append(Paragraph(f"Generated: {report.generated_at or datetime.now(timezone.utc)}", body_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
        elements.append(Spacer(1, 8))

        # Patient summary
        ps = content.get("patient_summary", {})
        if ps:
            elements.append(Paragraph("Patient Information", heading_style))
            patient_data = [
                ["Name", ps.get("name", "N/A")],
                ["MRN", ps.get("mrn", "N/A")],
                ["Age / Gender", f"{ps.get('age', '?')} / {ps.get('gender', '?')}"],
                ["Date of Birth", ps.get("dob", "N/A")],
            ]
            t = Table(patient_data, colWidths=[1.5 * inch, 4 * inch])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 8))

        # Executive summary
        if content.get("executive_summary"):
            elements.append(Paragraph("Executive Summary", heading_style))
            elements.append(Paragraph(content["executive_summary"], body_style))
            elements.append(Spacer(1, 6))

        # Chief complaint
        if content.get("chief_complaint"):
            elements.append(Paragraph("Chief Complaint", heading_style))
            elements.append(Paragraph(content["chief_complaint"], body_style))

        # Drug interactions warning
        drug_interactions = content.get("drug_interactions", [])
        major_ints = [d for d in drug_interactions if d.get("severity") in ("major", "contraindicated")]
        if major_ints:
            elements.append(Paragraph("⚠ Drug Interaction Alerts", heading_style))
            for di in major_ints:
                elements.append(Paragraph(
                    f"<b>{di['drug1']} + {di['drug2']}</b> [{di['severity'].upper()}]: {di.get('description', '')}",
                    warning_style,
                ))
                elements.append(Spacer(1, 4))

        # Differential diagnoses table
        differentials = content.get("differential_diagnoses", [])
        if differentials:
            elements.append(Paragraph("Differential Diagnoses", heading_style))
            dx_data = [["Rank", "Condition", "Likelihood", "ICD-10", "Urgency"]]
            for i, dx in enumerate(differentials, 1):
                dx_data.append([
                    str(i),
                    dx.get("condition", ""),
                    dx.get("likelihood", "").upper(),
                    dx.get("icd_code", ""),
                    dx.get("urgency", ""),
                ])
            dx_table = Table(dx_data, colWidths=[0.4 * inch, 2.5 * inch, 1 * inch, 0.9 * inch, 0.8 * inch])
            dx_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(dx_table)
            elements.append(Spacer(1, 8))

        # Care plan
        care_plan = content.get("care_plan", [])
        if care_plan:
            elements.append(Paragraph("Care Plan", heading_style))
            for item in care_plan:
                priority = item.get("priority", "").upper()
                color = "#dc2626" if priority == "IMMEDIATE" else "#d97706" if priority == "SHORT_TERM" else "#16a34a"
                elements.append(Paragraph(
                    f'<font color="{color}"><b>[{priority}]</b></font> {item.get("action", "")} '
                    f'<i>({item.get("timeframe", "")})</i>',
                    body_style,
                ))

        # Physician summary
        if content.get("physician_summary"):
            elements.append(Paragraph("Physician Summary", heading_style))
            elements.append(Paragraph(content["physician_summary"], body_style))

        # Physician notes (if reviewed)
        if report.physician_notes:
            elements.append(Paragraph("Attending Physician Notes", heading_style))
            elements.append(Paragraph(report.physician_notes, body_style))

        # Signature line
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="40%", thickness=0.5, color=colors.gray))
        elements.append(Paragraph("Attending Physician Signature / Date", ParagraphStyle(
            "sig", parent=styles["Normal"], fontSize=9, textColor=colors.gray
        )))

        # Disclaimer
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        disclaimer = content.get("disclaimer", "This AI-generated report is for clinical decision support only.")
        elements.append(Paragraph(f"DISCLAIMER: {disclaimer}", disclaimer_style))

        doc.build(elements)
        return buffer.getvalue()
