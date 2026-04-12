"""Patient Intake Agent — validates and structures initial clinical data."""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are an experienced clinical triage nurse with 15+ years in emergency and primary care settings.

Your role is to review patient intake information and:
1. Validate the completeness and clinical coherence of the data
2. Identify RED FLAG symptoms that may indicate life-threatening conditions
3. Assess clinical priority (emergency/urgent/routine)
4. Flag any missing critical information
5. Provide structured intake notes using SBAR format

RED FLAG symptoms requiring EMERGENCY classification:
- Chest pain with radiation, diaphoresis, or dyspnea
- Sudden severe headache ("worst headache of life")
- Altered mental status or sudden confusion
- Signs of stroke (facial droop, arm weakness, speech difficulty)
- Severe abdominal pain with rigidity
- Anaphylaxis signs
- SpO2 < 90%
- HR > 150 or < 40, SBP < 80 or > 200

Always prioritize patient safety. When in doubt, escalate priority."""


class IntakeSummary(BaseModel):
    validated_data: dict[str, Any] = Field(description="Cleaned and validated patient data")
    red_flags: list[str] = Field(default_factory=list, description="Critical symptom red flags identified")
    missing_info: list[str] = Field(default_factory=list, description="Important missing clinical information")
    clinical_priority: str = Field(description="emergency, urgent, or routine")
    priority_reasoning: str = Field(description="Clinical reasoning for the priority assessment")
    symptom_burden_score: int = Field(ge=0, le=10, description="Overall clinical burden 0-10")
    intake_notes: str = Field(description="SBAR-formatted intake notes")
    requires_immediate_attention: bool = Field(description="True if any red flags present")


class PatientIntakeAgent(BaseHealthcareAgent):
    """Validates patient intake data and identifies clinical red flags."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="patient_intake", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Please review this patient intake information and provide your clinical assessment.

{patient_context}

Vitals:
{vitals_summary}

Medical History: {medical_history}
Family History: {family_history}
Current Medications: {medications}
Allergies: {allergies}

Perform your clinical intake assessment.""")
        ])
        return prompt | self.llm.with_structured_output(IntakeSummary)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        pd = state["patient_data"]
        vitals = pd.get("vitals", {})
        vitals_summary = (
            f"BP: {vitals.get('blood_pressure_systolic', '?')}/{vitals.get('blood_pressure_diastolic', '?')} mmHg, "
            f"HR: {vitals.get('heart_rate', '?')} bpm, "
            f"Temp: {vitals.get('temperature_celsius', '?')}°C, "
            f"SpO2: {vitals.get('oxygen_saturation', '?')}%, "
            f"RR: {vitals.get('respiratory_rate', '?')}/min"
        )

        result: IntakeSummary = await self._invoke_with_retry(self.chain, {
            "patient_context": self._build_patient_context(state),
            "vitals_summary": vitals_summary,
            "medical_history": str(pd.get("medical_history", "None provided")),
            "family_history": ", ".join(pd.get("family_history", [])) or "Not reported",
            "medications": str(pd.get("current_medications", "None")),
            "allergies": ", ".join(pd.get("allergies", [])) or "NKDA",
        })

        tokens = self._count_tokens(self._build_patient_context(state))
        return {
            "intake_summary": result.model_dump(),
            "steps_completed": ["patient_intake"],
            "tokens_used": tokens,
        }
