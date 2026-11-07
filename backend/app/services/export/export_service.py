import io
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ReportLab for PDF generation
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
    KeepTogether
)

# python-docx for DOCX generation
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.factual_qc import FactualQCReport
from app.models.instructional_qc import InstructionalQCReport


class ExportService:
    """
    Comprehensive Multi-Format Lesson & QC Export Service.
    Compiles complete structured lessons, research bibliographies, claim-level factual verification,
    pedagogical rubric evaluations, and explicit stale-status warnings into JSON, PDF, and DOCX formats.
    """

    def compile_export_package(
        self,
        lesson: Lesson,
        sources: List[ResearchSource],
        factual_qc: Optional[FactualQCReport] = None,
        instructional_qc: Optional[InstructionalQCReport] = None
    ) -> Dict[str, Any]:
        """Compiles unified export dictionary."""
        is_stale = bool(
            (factual_qc and factual_qc.is_stale) or
            (instructional_qc and instructional_qc.is_stale)
        )
        stale_reasons = []
        if factual_qc and factual_qc.is_stale and factual_qc.stale_reason:
            stale_reasons.append(f"Factual QC: {factual_qc.stale_reason}")
        if instructional_qc and instructional_qc.is_stale and instructional_qc.stale_reason:
            stale_reasons.append(f"Instructional QC: {instructional_qc.stale_reason}")

        objectives = lesson.learning_objectives
        if isinstance(objectives, str):
            objectives = [objectives]

        return {
            "metadata": {
                "platform": "LearnForge AI",
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "lesson_id": lesson.id,
                "lesson_version": lesson.current_version,
                "lesson_status": lesson.status,
                "is_stale": is_stale,
                "stale_warning": (
                    "WARNING: Lesson content was modified after QC evaluation. "
                    "The enclosed QC reports reflect a previous version and do NOT certify current content."
                    if is_stale else None
                ),
                "stale_reasons": stale_reasons
            },
            "lesson": {
                "title": lesson.title,
                "learning_objectives": objectives,
                "target_audience": lesson.target_audience,
                "difficulty_level": lesson.difficulty_level,
                "total_estimated_duration_mins": lesson.estimated_duration_mins,
                "content_blocks": lesson.content_blocks or {}
            },
            "research_bibliography": [
                {
                    "citation_tag": s.citation_tag,
                    "title": s.title,
                    "source_type": s.source_type,
                    "url_or_identifier": s.url_or_identifier,
                    "is_content_accessible": s.is_content_accessible,
                    "preview_type": s.preview_type,
                    "relevance_score": s.relevance_score,
                    "verification_scope_note": s.verification_scope_note
                }
                for s in sources
            ],
            "quality_control": {
                "factual_qc": {
                    "status": factual_qc.status if factual_qc else "NOT_EVALUATED",
                    "score": factual_qc.factual_accuracy_score if factual_qc else None,
                    "claim_verification_rate": factual_qc.claim_verification_rate if factual_qc else None,
                    "citation_fidelity_score": factual_qc.citation_fidelity_score if factual_qc else None,
                    "hallucination_penalty": factual_qc.hallucination_penalty if factual_qc else None,
                    "total_claims_analyzed": factual_qc.total_claims_analyzed if factual_qc else 0,
                    "verified_claims_count": factual_qc.verified_claims_count if factual_qc else 0,
                    "partially_supported_count": factual_qc.partially_supported_count if factual_qc else 0,
                    "unsubstantiated_count": factual_qc.unsubstantiated_count if factual_qc else 0,
                    "contradicted_count": factual_qc.contradicted_count if factual_qc else 0,
                    "claim_verifications": factual_qc.claim_verifications if factual_qc else [],
                    "hallucination_flags": factual_qc.hallucination_flags if factual_qc else [],
                    "missing_citations": factual_qc.missing_citations if factual_qc else [],
                    "executive_summary": factual_qc.executive_summary if factual_qc else "No factual audit recorded.",
                    "recommended_corrections": factual_qc.recommended_corrections if factual_qc else [],
                    "is_stale": factual_qc.is_stale if factual_qc else False,
                    "stale_reason": factual_qc.stale_reason if factual_qc else None
                } if factual_qc else None,
                "instructional_qc": {
                    "status": instructional_qc.status if instructional_qc else "NOT_EVALUATED",
                    "score": instructional_qc.pedagogical_score if instructional_qc else None,
                    "bloom_alignment_score": instructional_qc.bloom_alignment_score if instructional_qc else None,
                    "scaffolding_score": instructional_qc.scaffolding_score if instructional_qc else None,
                    "clarity_score": instructional_qc.clarity_score if instructional_qc else None,
                    "assessment_fidelity_score": instructional_qc.assessment_fidelity_score if instructional_qc else None,
                    "engagement_score": instructional_qc.engagement_score if instructional_qc else None,
                    "target_bloom_level": instructional_qc.target_bloom_level if instructional_qc else None,
                    "achieved_bloom_level": instructional_qc.achieved_bloom_level if instructional_qc else None,
                    "rubric_breakdown": instructional_qc.rubric_breakdown if instructional_qc else [],
                    "strengths": instructional_qc.strengths if instructional_qc else [],
                    "actionable_improvements": instructional_qc.actionable_improvements if instructional_qc else [],
                    "executive_summary": instructional_qc.executive_summary if instructional_qc else "No instructional design audit recorded.",
                    "is_stale": instructional_qc.is_stale if instructional_qc else False,
                    "stale_reason": instructional_qc.stale_reason if instructional_qc else None
                } if instructional_qc else None
            }
        }

    def export_json(
        self,
        lesson: Lesson,
        sources: List[ResearchSource],
        factual_qc: Optional[FactualQCReport] = None,
        instructional_qc: Optional[InstructionalQCReport] = None
    ) -> Dict[str, Any]:
        """Generates JSON export payload."""
        return self.compile_export_package(lesson, sources, factual_qc, instructional_qc)

    def export_pdf(
        self,
        lesson: Lesson,
        sources: List[ResearchSource],
        factual_qc: Optional[FactualQCReport] = None,
        instructional_qc: Optional[InstructionalQCReport] = None
    ) -> io.BytesIO:
        """Generates professionally formatted PDF document."""
        pkg = self.compile_export_package(lesson, sources, factual_qc, instructional_qc)
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'DocSub',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )
        code_style = ParagraphStyle(
            'CodeBlock',
            parent=styles['Code'],
            fontName='Courier',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#0f172a'),
            backColor=colors.HexColor('#f1f5f9'),
            spaceAfter=6
        )
        alert_style = ParagraphStyle(
            'Alert',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#b45309'),
            backColor=colors.HexColor('#fef3c7'),
            borderPadding=8,
            spaceAfter=10
        )

        elements = []

        # Header Title
        elements.append(Paragraph(f"LearnForge AI — {lesson.title}", title_style))
        meta_line = (
            f"<b>Revision:</b> v{lesson.current_version} &nbsp;|&nbsp; "
            f"<b>Status:</b> {lesson.status} &nbsp;|&nbsp; "
            f"<b>Duration:</b> {lesson.estimated_duration_mins} mins (Max: 45m) &nbsp;|&nbsp; "
            f"<b>Target:</b> {lesson.target_audience} ({lesson.difficulty_level})"
        )
        elements.append(Paragraph(meta_line, subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=10))

        # Stale Warning Banner (if applicable)
        if pkg["metadata"]["is_stale"]:
            warning_text = (
                f"<b>⚠️ STALE QUALITY CONTROL WARNING:</b> {pkg['metadata']['stale_warning']}<br/>"
                f"<i>Reasons:</i> {'; '.join(pkg['metadata']['stale_reasons'])}"
            )
            elements.append(Paragraph(warning_text, alert_style))

        # Executive QC Scorecard Summary Table
        f_score = f"{factual_qc.factual_accuracy_score}% ({factual_qc.status})" if factual_qc else "Not Evaluated"
        i_score = f"{instructional_qc.pedagogical_score}% ({instructional_qc.status})" if instructional_qc else "Not Evaluated"
        
        score_data = [
            [
                Paragraph("<b>QC-1: Factual & Research Accuracy</b>", body_style),
                Paragraph(f"<b>{f_score}</b>", body_style),
                Paragraph(
                    f"Verified: {factual_qc.verified_claims_count}/{factual_qc.total_claims_analyzed} claims | "
                    f"Fidelity: {factual_qc.citation_fidelity_score}%" if factual_qc else "N/A",
                    body_style
                )
            ],
            [
                Paragraph("<b>QC-2: Instructional Design & Pedagogy</b>", body_style),
                Paragraph(f"<b>{i_score}</b>", body_style),
                Paragraph(
                    f"Bloom Depth: {instructional_qc.target_bloom_level} → {instructional_qc.achieved_bloom_level} | "
                    f"Scaffolding: {instructional_qc.scaffolding_score}%" if instructional_qc else "N/A",
                    body_style
                )
            ]
        ]
        score_table = Table(score_data, colWidths=[180, 100, 250])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 10))

        # Section 1: Overview & Learning Objectives
        content = lesson.content_blocks or {}
        elements.append(Paragraph("1. Course Overview & Stated Learning Objectives", h2_style))
        overview_text = content.get("overview", "Comprehensive educational module.")
        elements.append(Paragraph(overview_text, body_style))

        objectives = pkg["lesson"]["learning_objectives"]
        obj_html = "<b>Learning Objectives:</b><ul>" + "".join([f"<li>{o}</li>" for o in objectives]) + "</ul>"
        elements.append(Paragraph(obj_html, body_style))

        # Section 2: Prerequisites
        prereqs = content.get("prerequisite_knowledge", [])
        if prereqs:
            elements.append(Paragraph("2. Prerequisite Knowledge & Refreshers", h2_style))
            prereq_html = "<ul>" + "".join([f"<li><b>{p.get('concept')}:</b> {p.get('brief_refresher')}</li>" for p in prereqs]) + "</ul>"
            elements.append(Paragraph(prereq_html, body_style))

        # Section 3: Core Concepts
        concepts = content.get("core_concepts", [])
        elements.append(Paragraph("3. Core Conceptual Explanations", h2_style))
        for idx, c in enumerate(concepts, 1):
            tags = " ".join(c.get("supporting_citation_tags", []))
            c_text = f"<b>3.{idx} {c.get('title')}</b> {f'[{tags}]' if tags else ''}<br/>{c.get('explanation')}<br/><i>Key Takeaway:</i> {c.get('key_takeaway')}"
            elements.append(Paragraph(c_text, body_style))

        # Section 4: Practical Examples
        examples = content.get("practical_examples", [])
        if examples:
            elements.append(Paragraph("4. Practical Walk-Through Examples", h2_style))
            for idx, ex in enumerate(examples, 1):
                elements.append(Paragraph(f"<b>Example 4.{idx}: {ex.get('title')}</b> ({ex.get('scenario')})", body_style))
                elements.append(Paragraph(f"<i>Explanation:</i> {ex.get('explanation')}", body_style))
                code_text = ex.get("code_or_walkthrough", "").replace("<", "&lt;").replace(">", "&gt;")
                if code_text:
                    elements.append(Paragraph(f"<font face='Courier'>{code_text}</font>", code_style))

        # Section 5: Real-World Applications
        apps = content.get("real_world_applications", [])
        if apps:
            elements.append(Paragraph("5. Real-World Applications & Architecture Trade-Offs", h2_style))
            for a in apps:
                elements.append(Paragraph(f"<b>Domain:</b> {a.get('domain')} &nbsp;|&nbsp; <b>Use Case:</b> {a.get('use_case')}<br/><b>Trade-Offs:</b> {a.get('trade_offs')}", body_style))

        # Section 6: Formative Knowledge Checks
        checks = content.get("knowledge_checks", [])
        if checks:
            elements.append(Paragraph("6. Formative Knowledge Checks & Rationales", h2_style))
            for idx, k in enumerate(checks, 1):
                options_str = " | ".join(k.get("options", []))
                q_text = f"<b>Q{idx}: {k.get('question')}</b><br/><i>Options:</i> {options_str}<br/><b>Correct Answer:</b> {k.get('correct_answer')} — <i>Rationale:</i> {k.get('rationale')}"
                elements.append(Paragraph(q_text, body_style))

        # Section 7: Research Bibliography
        elements.append(Paragraph("7. Research Bibliography & Source Grounding", h2_style))
        for s in sources:
            acc_label = "ACCESSIBLE" if s.is_content_accessible and s.preview_type != "metadata_only" else "METADATA ONLY"
            b_text = f"<b>{s.citation_tag} ({s.source_type.upper()} - [{acc_label}]):</b> {s.title} ({s.url_or_identifier or 'No URL'})"
            elements.append(Paragraph(b_text, body_style))

        # Section 8: Quality Control Verification Findings
        if factual_qc:
            elements.append(Paragraph("8. Factual & Research Accuracy Audit Findings", h2_style))
            claim_rows = [["Claim Assertion", "Source", "Verdict", "Confidence"]]
            for c in factual_qc.claim_verifications[:8]:  # Top claims
                claim_rows.append([
                    Paragraph(c.get("claim", "")[:120], body_style),
                    c.get("source_reference_tag") or "None",
                    c.get("verdict"),
                    f"{int(c.get('confidence_score', 0) * 100)}%"
                ])
            claim_table = Table(claim_rows, colWidths=[260, 60, 110, 60])
            claim_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(claim_table)

        if instructional_qc:
            elements.append(Paragraph("9. Instructional Design Rubric Breakdown", h2_style))
            rubric_rows = [["Criterion", "Weight", "Score", "Evaluated Evidence"]]
            for r in instructional_qc.rubric_breakdown:
                rubric_rows.append([
                    Paragraph(r.get("name", ""), body_style),
                    f"{int(r.get('weight', 0) * 100)}%",
                    f"{r.get('score')}%",
                    Paragraph(r.get("evidence", "")[:140], body_style)
                ])
            rubric_table = Table(rubric_rows, colWidths=[140, 50, 50, 250])
            rubric_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(rubric_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def export_docx(
        self,
        lesson: Lesson,
        sources: List[ResearchSource],
        factual_qc: Optional[FactualQCReport] = None,
        instructional_qc: Optional[InstructionalQCReport] = None
    ) -> io.BytesIO:
        """Generates professionally formatted DOCX document."""
        pkg = self.compile_export_package(lesson, sources, factual_qc, instructional_qc)
        buffer = io.BytesIO()

        doc = docx.Document()

        # Document Title
        title_p = doc.add_paragraph()
        title_run = title_p.add_run(f"LearnForge AI: {lesson.title}")
        title_run.font.size = Pt(22)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(15, 23, 42)

        meta_p = doc.add_paragraph()
        meta_run = meta_p.add_run(
            f"Revision: v{lesson.current_version} | Status: {lesson.status} | "
            f"Duration: {lesson.estimated_duration_mins} mins (Max: 45m) | Audience: {lesson.target_audience}"
        )
        meta_run.font.size = Pt(10)
        meta_run.font.italic = True
        meta_run.font.color.rgb = RGBColor(71, 85, 105)

        # Stale Warning Banner (if applicable)
        if pkg["metadata"]["is_stale"]:
            stale_p = doc.add_paragraph()
            stale_run = stale_p.add_run(
                f"⚠️ STALE QUALITY CONTROL WARNING: {pkg['metadata']['stale_warning']}\n"
                f"Reasons: {'; '.join(pkg['metadata']['stale_reasons'])}"
            )
            stale_run.font.bold = True
            stale_run.font.color.rgb = RGBColor(180, 83, 9)

        # QC Scorecard
        doc.add_heading("Executive Quality Control Scorecard", level=2)
        qc_table = doc.add_table(rows=3, cols=3)
        qc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["Quality Engine", "Score & Status", "Key Metrics"]
        for i, h in enumerate(headers):
            cell = qc_table.cell(0, i)
            cell.text = h
            cell.paragraphs[0].runs[0].font.bold = True

        qc_table.cell(1, 0).text = "QC-1: Factual & Research Accuracy"
        qc_table.cell(1, 1).text = f"{factual_qc.factual_accuracy_score}% ({factual_qc.status})" if factual_qc else "N/A"
        qc_table.cell(1, 2).text = f"Verified: {factual_qc.verified_claims_count}/{factual_qc.total_claims_analyzed} | Fidelity: {factual_qc.citation_fidelity_score}%" if factual_qc else "N/A"

        qc_table.cell(2, 0).text = "QC-2: Instructional Design & Pedagogy"
        qc_table.cell(2, 1).text = f"{instructional_qc.pedagogical_score}% ({instructional_qc.status})" if instructional_qc else "N/A"
        qc_table.cell(2, 2).text = f"Bloom: {instructional_qc.target_bloom_level} → {instructional_qc.achieved_bloom_level} | Scaffolding: {instructional_qc.scaffolding_score}%" if instructional_qc else "N/A"

        # Content Sections
        content = lesson.content_blocks or {}

        # 1. Overview
        doc.add_heading("1. Course Overview & Learning Objectives", level=2)
        doc.add_paragraph(content.get("overview", ""))
        doc.add_paragraph("Stated Learning Objectives:").runs[0].font.bold = True
        for o in pkg["lesson"]["learning_objectives"]:
            doc.add_paragraph(f"• {o}")

        # 2. Prerequisites
        prereqs = content.get("prerequisite_knowledge", [])
        if prereqs:
            doc.add_heading("2. Prerequisite Knowledge", level=2)
            for p in prereqs:
                doc.add_paragraph(f"• {p.get('concept')}: {p.get('brief_refresher')}")

        # 3. Core Concepts
        concepts = content.get("core_concepts", [])
        doc.add_heading("3. Core Conceptual Explanations", level=2)
        for idx, c in enumerate(concepts, 1):
            tags = " ".join(c.get("supporting_citation_tags", []))
            p = doc.add_paragraph()
            p.add_run(f"3.{idx} {c.get('title')} {f'[{tags}]' if tags else ''}\n").font.bold = True
            p.add_run(f"{c.get('explanation')}\n")
            p.add_run(f"Key Takeaway: {c.get('key_takeaway')}").font.italic = True

        # 4. Practical Examples
        examples = content.get("practical_examples", [])
        if examples:
            doc.add_heading("4. Practical Walk-Through Examples", level=2)
            for idx, ex in enumerate(examples, 1):
                p = doc.add_paragraph()
                p.add_run(f"Example 4.{idx}: {ex.get('title')} ({ex.get('scenario')})\n").font.bold = True
                p.add_run(f"Explanation: {ex.get('explanation')}\n")
                if ex.get("code_or_walkthrough"):
                    code_p = doc.add_paragraph(ex.get("code_or_walkthrough"))
                    code_p.style = 'Quote'

        # 5. Formative Knowledge Checks
        checks = content.get("knowledge_checks", [])
        if checks:
            doc.add_heading("5. Formative Knowledge Checks", level=2)
            for idx, k in enumerate(checks, 1):
                p = doc.add_paragraph()
                p.add_run(f"Question {idx}: {k.get('question')}\n").font.bold = True
                p.add_run(f"Options: {' | '.join(k.get('options', []))}\n")
                p.add_run(f"Correct Answer: {k.get('correct_answer')} — Rationale: {k.get('rationale')}")

        # 6. Research Bibliography
        doc.add_heading("6. Research Bibliography", level=2)
        for s in sources:
            acc = "ACCESSIBLE" if s.is_content_accessible and s.preview_type != "metadata_only" else "METADATA ONLY"
            doc.add_paragraph(f"• [{s.citation_tag}] ({s.source_type.upper()} - {acc}): {s.title} ({s.url_or_identifier or 'N/A'})")

        # 7. Quality Control Claim Findings
        if factual_qc:
            doc.add_heading("7. Factual Verification Findings", level=2)
            for c in factual_qc.claim_verifications:
                p = doc.add_paragraph()
                p.add_run(f"Claim: \"{c.get('claim')}\"\n").font.bold = True
                p.add_run(f"Verdict: {c.get('verdict')} | Citation: {c.get('source_reference_tag') or 'None'} | Confidence: {int(c.get('confidence_score', 0) * 100)}%\n")
                if c.get("evidence_quote"):
                    p.add_run(f"Evidence Excerpt: \"{c.get('evidence_quote')}\"\n").font.italic = True
                if c.get("recommended_correction"):
                    p.add_run(f"Recommended Correction: {c.get('recommended_correction')}\n")

        # 8. Instructional Rubric Breakdown
        if instructional_qc:
            doc.add_heading("8. Instructional Design Rubric Evaluation", level=2)
            for r in instructional_qc.rubric_breakdown:
                p = doc.add_paragraph()
                p.add_run(f"• {r.get('name')} (Weight: {int(r.get('weight', 0)*100)}% | Score: {r.get('score')}%)\n").font.bold = True
                p.add_run(f"Evidence: {r.get('evidence')}")

        doc.save(buffer)
        buffer.seek(0)
        return buffer
