"""Clinical Report Agent — synthesizes all outputs into a physician-ready report."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are a senior physician specializing in clinical documentation and medical report generation.

Your role is to synthesize all available clinical data into a comprehensive, physician-ready clinical report.

Report sections must follow standard clinical documentation format:
1. Executive Summary (2-3 sentence overview for rapid review)
2. Patient Summary (demographics, chief complaint, clinical context)
3. Clinical Findings (symptom analysis, physical examination context)
4. Laboratory Analysis (interpreted results with clinical significance)
5. Medication Safety Review (interactions and allergy alerts)
6. Differential Diagnoses (ranked with reasoning)
7. Care Plan (prioritized, evidence-based recommendations)
8. Physician Summary (narrative synthesis)

Style requirements:
- Use clear, professional medical language
- Avoid jargon without explanation
- Be concise but complete
- Highlight actionable items
- Use standard medical abbreviations appropriately
- Include clinical reasoning, not just conclusions"""


class ClinicalReportResult(BaseModel):
    executive_summary: str = Field(description="2-3 sentence summary for rapid review")
    patient_summary: dict[str, Any] = Field(description="Structured patient demographics and context")
    chief_complaint: str
    clinical_findings_narrative: str = Field(description="Narrative of all clinical findings")
    key_recommendations: list[str] = Field(description="Top 3-5 most important recommendations")
    overall_assessment: str = Field(description="Physician-level overall assessment")
    confidence_statement: str = Field(description="Statement about diagnostic confidence and limitations")


class ClinicalReportAgent(BaseHealthcareAgent):
    """Synthesizes all agent outputs into a cohesive clinical report."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="clinical_report", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Generate a comprehensive clinical report synthesizing all findings.

{patient_context}

Symptom Analysis Summary:
{symptom_summary}

Laboratory Findings:
{lab_summary}

Drug Safety:
{drug_summary}

Differential Diagnoses (top 3):
{diagnosis_summary}

Care Plan Highlights:
{care_summary}

Generate the complete clinical report synthesis.""")
        ])
        return prompt | self.llm.with_structured_output(ClinicalReportResult)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        pd = state["patient_data"]
        symptom_analysis = state.get("symptom_analysis") or {}
        lab_interp = state.get("lab_interpretation") or {}
        drug_int = state.get("drug_interactions") or []
        differentials = state.get("differential_diagnoses") or []
        care_plan = state.get("care_plan") or []

        symptom_summary = (
            f"Pattern: {symptom_analysis.get('clinical_pattern', 'Not analyzed')}\n"
            f"Key Findings: {', '.join(symptom_analysis.get('key_findings', []))}"
        )
        lab_summary = lab_interp.get("overall_lab_summary", "No lab data")
        critical = lab_interp.get("critical_values", [])
        if critical:
            lab_summary += f"\n⚠️ CRITICAL VALUES: {', '.join(c.get('test_name','') for c in critical)}"

        major_drugs = [d for d in drug_int if d.get("severity") in ("major", "contraindicated")]
        drug_summary = (
            "\n".join(f"⚠️ {d['drug1']} + {d['drug2']}: {d['severity'].upper()}" for d in major_drugs)
            if major_drugs else "No major interactions"
        )

        diagnosis_summary = "\n".join(
            f"{i+1}. {d['condition']} [{d['likelihood'].upper()}] - {d['reasoning'][:100]}..."
            for i, d in enumerate(differentials[:3])
        )

        immediate_actions = [c for c in care_plan if c.get("priority") == "immediate"]
        care_summary = "\n".join(
            f"- [{c['priority'].upper()}] {c['action']}"
            for c in (immediate_actions or care_plan)[:5]
        )

        result: ClinicalReportResult = await self._invoke_with_retry(self.chain, {
            "patient_context": self._build_patient_context(state),
            "symptom_summary": symptom_summary,
            "lab_summary": lab_summary,
            "drug_summary": drug_summary,
            "diagnosis_summary": diagnosis_summary or "No differential diagnoses generated",
            "care_summary": care_summary or "No care plan generated",
        })

        # Assemble full structured report
        report = {
            "patient_summary": {
                "name": pd.get("full_name"),
                "age": pd.get("age"),
                "gender": pd.get("gender"),
                "mrn": pd.get("mrn"),
                "dob": pd.get("date_of_birth"),
            },
            "chief_complaint": pd.get("chief_complaint", ""),
            "executive_summary": result.executive_summary,
            "symptom_analysis": symptom_analysis,
            "lab_interpretation": lab_interp.get("abnormal_values", []) + lab_interp.get("critical_values", []),
            "drug_interactions": drug_int,
            "differential_diagnoses": differentials,
            "care_plan": care_plan,
            "physician_summary": result.overall_assessment,
            "key_recommendations": result.key_recommendations,
            "confidence_statement": result.confidence_statement,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_used": state.get("model_used", "gpt-4o"),
            "disclaimer": (
                "IMPORTANT: This AI-generated report is a clinical decision support tool only. "
                "It does not replace the judgment of a qualified healthcare professional. "
                "All findings must be reviewed and validated by a licensed physician."
            ),
        }

        tokens = self._count_tokens(symptom_summary + lab_summary + diagnosis_summary)
        return {
            "clinical_report": report,
            "steps_completed": ["clinical_report"],
            "tokens_used": tokens,
        }
