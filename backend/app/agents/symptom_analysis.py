"""Symptom Analysis Agent — clinical reasoning over presenting symptoms."""
from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are a board-certified internal medicine physician with expertise in clinical reasoning and diagnostic medicine.

Your role is to perform systematic symptom analysis using established clinical frameworks:

1. **OPQRST Analysis** for each symptom:
   - Onset (sudden vs gradual)
   - Provocation/Palliation
   - Quality (sharp, dull, burning, etc.)
   - Radiation/Region
   - Severity (1-10)
   - Timing (constant, intermittent, progressive)

2. **Systems Review**: Identify which body systems are involved

3. **Symptom Clustering**: Group related symptoms into clinical syndromes

4. **Pattern Recognition**: Apply clinical pattern recognition to identify:
   - Inflammatory vs. mechanical presentations
   - Acute vs. chronic processes
   - Local vs. systemic involvement

5. **Urgency Assessment**: Based on symptom pattern, assess clinical urgency

Be systematic, evidence-based, and think like a seasoned clinician."""


class SymptomCluster(BaseModel):
    name: str
    symptoms: list[str]
    clinical_significance: str
    associated_systems: list[str]


class SymptomAnalysisResult(BaseModel):
    symptom_clusters: list[SymptomCluster] = Field(description="Groups of related symptoms")
    systems_involved: list[str] = Field(description="Body systems implicated")
    clinical_pattern: str = Field(description="Overall clinical picture description")
    urgency_assessment: str = Field(description="emergency/urgent/routine with reasoning")
    key_findings: list[str] = Field(description="Most clinically significant findings")
    reasoning_chain: str = Field(description="Step-by-step clinical reasoning narrative")
    opqrst_summary: dict[str, Any] = Field(description="OPQRST analysis of primary symptom")
    temporal_pattern: str = Field(description="How symptoms evolve over time")
    aggravating_factors: list[str] = Field(default_factory=list)
    relieving_factors: list[str] = Field(default_factory=list)


class SymptomAnalysisAgent(BaseHealthcareAgent):
    """Performs structured clinical reasoning over patient symptoms."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="symptom_analysis", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Perform a comprehensive symptom analysis for this patient.

{patient_context}

Intake Assessment:
{intake_summary}

Please provide your systematic symptom analysis using OPQRST and clinical pattern recognition.""")
        ])
        return prompt | self.llm.with_structured_output(SymptomAnalysisResult)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        intake_summary = state.get("intake_summary") or {}

        result: SymptomAnalysisResult = await self._invoke_with_retry(self.chain, {
            "patient_context": self._build_patient_context(state),
            "intake_summary": str(intake_summary),
        })

        tokens = self._count_tokens(self._build_patient_context(state))
        return {
            "symptom_analysis": result.model_dump(),
            "steps_completed": ["symptom_analysis"],
            "tokens_used": tokens,
        }
