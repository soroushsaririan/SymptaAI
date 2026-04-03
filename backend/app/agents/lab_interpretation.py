"""Lab Interpretation Agent — analyzes lab results and flags abnormal values."""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are a clinical pathologist and laboratory medicine specialist with expertise in interpreting diagnostic laboratory results.

Your analysis must:
1. Identify CRITICAL VALUES requiring immediate physician notification:
   - Glucose: < 40 or > 500 mg/dL
   - Potassium: < 2.5 or > 6.5 mEq/L
   - Sodium: < 120 or > 160 mEq/L
   - Hemoglobin: < 7 g/dL
   - Platelet count: < 20,000/µL
   - INR: > 5.0
   - Troponin: Any elevation
   - Creatinine: > 10 mg/dL

2. Contextualize results with patient demographics (age, gender affect reference ranges)

3. Identify LAB PATTERNS:
   - Complete blood count patterns (anemia, infection, thrombocytopenia)
   - Metabolic patterns (AKI, CKD, electrolyte disturbances)
   - Hepatic patterns (hepatitis, cholestasis, synthetic dysfunction)
   - Inflammatory markers (CRP, ESR, procalcitonin)
   - Coagulation disorders

4. Correlate lab findings with clinical presentation

5. Suggest additional tests that would aid diagnosis

Apply clinical laboratory medicine standards and flag results requiring urgent attention."""


class LabFinding(BaseModel):
    test_name: str
    value: str
    unit: Optional[str]
    reference_range: Optional[str]
    status: str  # normal, abnormal, critical
    clinical_significance: str
    interpretation: str
    severity: Optional[str] = None  # mild, moderate, severe


class LabInterpretationResult(BaseModel):
    critical_values: list[LabFinding] = Field(description="Values requiring immediate attention")
    abnormal_values: list[LabFinding] = Field(description="Abnormal but non-critical values")
    normal_values: list[LabFinding] = Field(description="Values within normal range")
    lab_patterns: list[dict[str, Any]] = Field(description="Identified lab patterns/syndromes")
    clinical_correlation: str = Field(description="How lab results relate to symptoms")
    recommended_additional_tests: list[str] = Field(description="Additional labs to consider")
    overall_lab_summary: str = Field(description="Narrative summary of lab findings")
    requires_urgent_review: bool = Field(description="True if critical values present")


class LabInterpretationAgent(BaseHealthcareAgent):
    """Analyzes laboratory results and identifies clinically significant abnormalities."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="lab_interpretation", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Interpret these laboratory results for the patient below.

{patient_context}

Laboratory Results:
{lab_results}

Symptom Context:
{symptom_context}

Provide your complete laboratory interpretation.""")
        ])
        return prompt | self.llm.with_structured_output(LabInterpretationResult)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        labs = state.get("lab_results", [])
        if not labs:
            return {
                "lab_interpretation": {
                    "critical_values": [],
                    "abnormal_values": [],
                    "normal_values": [],
                    "lab_patterns": [],
                    "clinical_correlation": "No lab results provided for this patient.",
                    "recommended_additional_tests": [],
                    "overall_lab_summary": "No laboratory data available.",
                    "requires_urgent_review": False,
                },
                "steps_completed": ["lab_interpretation"],
                "tokens_used": 10,
            }

        lab_text = "\n".join(
            f"- {l['test_name']}: {l['value']} {l.get('unit', '')} "
            f"(Ref: {l.get('reference_range', 'N/A')}, "
            f"Abnormal: {l.get('is_abnormal', False)})"
            for l in labs
        )
        symptom_ctx = str(state.get("symptom_analysis", {}).get("clinical_pattern", ""))

        result: LabInterpretationResult = await self._invoke_with_retry(self.chain, {
            "patient_context": self._build_patient_context(state),
            "lab_results": lab_text,
            "symptom_context": symptom_ctx or "Symptom analysis not yet available",
        })

        tokens = self._count_tokens(lab_text)
        return {
            "lab_interpretation": result.model_dump(),
            "steps_completed": ["lab_interpretation"],
            "tokens_used": tokens,
        }
