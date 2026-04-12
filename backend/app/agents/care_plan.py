"""Care Plan Agent — evidence-based clinical management recommendations."""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are an attending physician with expertise in clinical management and care coordination. You create evidence-based care plans following clinical practice guidelines.

Your care plan framework:
1. **Immediate Actions** (within hours): Life-threatening issues, pain control, stabilization
2. **Short-term Management** (days to weeks): Diagnostic workup, initial treatment, monitoring
3. **Long-term Management** (months): Chronic disease management, prevention, lifestyle

Care plan components:
- Diagnostic workup (ordered by priority)
- Treatment recommendations (evidence-based, referencing guidelines)
- Specialist referrals (with clinical indication)
- Patient education (condition-specific, actionable)
- Follow-up schedule (with specific monitoring parameters)
- Safety netting (red flags to watch for)
- Medication management (start/stop/adjust)

Reference relevant guidelines:
- ACC/AHA for cardiovascular
- ADA for diabetes
- GOLD for COPD
- JNC/AHA for hypertension
- ACOG for obstetrics/gynecology
- Infectious diseases society guidelines as appropriate

Always justify recommendations with clinical evidence."""


class CareAction(BaseModel):
    priority: str  # immediate, short_term, long_term
    category: str  # diagnostic, therapeutic, monitoring, referral, education
    action: str
    rationale: str
    timeframe: str
    responsible_party: Optional[str] = None
    guideline_reference: Optional[str] = None


class SpecialistReferral(BaseModel):
    specialty: str
    indication: str
    urgency: str  # emergent, urgent, routine
    specific_question: str


class CarePlanResult(BaseModel):
    care_actions: list[CareAction] = Field(description="All care actions prioritized and categorized")
    specialist_referrals: list[SpecialistReferral] = Field(description="Specialist referrals needed")
    patient_education_points: list[str] = Field(description="Key education points for the patient")
    follow_up_timeline: str = Field(description="Recommended follow-up schedule")
    monitoring_parameters: list[str] = Field(description="Parameters to monitor during treatment")
    safety_netting: list[str] = Field(description="Red flags patient/family should watch for")
    prognosis_statement: str = Field(description="Brief prognosis statement for primary diagnosis")


class CarePlanAgent(BaseHealthcareAgent):
    """Creates evidence-based, prioritized care plans."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="care_plan", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Create a comprehensive care plan for this patient.

{patient_context}

Primary Diagnosis: {primary_diagnosis}

Differential Diagnoses:
{differential_summary}

Drug Safety Issues:
{drug_safety}

Lab Findings:
{lab_summary}

Develop an evidence-based, prioritized care plan.""")
        ])
        return prompt | self.llm.with_structured_output(CarePlanResult)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        differentials = state.get("differential_diagnoses") or []
        primary = differentials[0]["condition"] if differentials else "Undetermined"

        diff_summary = "\n".join(
            f"- {d['condition']} (Likelihood: {d['likelihood']}, Urgency: {d.get('urgency', 'routine')})"
            for d in differentials[:5]
        )

        drug_int = state.get("drug_interactions") or []
        major_issues = [d for d in drug_int if d.get("severity") in ("major", "contraindicated")]
        drug_safety = (
            "\n".join(f"- {i['drug1']} + {i['drug2']}: {i['severity'].upper()}" for i in major_issues)
            if major_issues else "No major drug safety issues"
        )

        lab_interp = state.get("lab_interpretation") or {}
        lab_summary = lab_interp.get("overall_lab_summary", "No lab data")

        result: CarePlanResult = await self._invoke_with_retry(self.chain, {
            "patient_context": self._build_patient_context(state),
            "primary_diagnosis": primary,
            "differential_summary": diff_summary or "No differentials generated",
            "drug_safety": drug_safety,
            "lab_summary": lab_summary,
        })

        care_plan = [
            {
                "priority": a.priority,
                "action": a.action,
                "rationale": a.rationale,
                "timeframe": a.timeframe,
                "responsible_party": a.responsible_party,
            }
            for a in result.care_actions
        ]

        tokens = self._count_tokens(diff_summary + drug_safety)
        return {
            "care_plan": care_plan,
            "steps_completed": ["care_plan"],
            "tokens_used": tokens,
        }
