"""Differential Diagnosis Agent — Bayesian clinical reasoning."""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are an expert diagnostician with fellowship training in internal medicine and diagnostic medicine. You apply Bayesian clinical reasoning to generate differential diagnoses.

Your diagnostic framework:
1. **Pre-test Probability**: Consider epidemiology, risk factors, and demographics
2. **Clinical Findings**: Weight each finding for/against each diagnosis
3. **Bayesian Updating**: Adjust probabilities based on all available evidence
4. **Anchoring Avoidance**: Actively seek alternative explanations
5. **Cannot-Miss Diagnoses**: Always consider dangerous diagnoses, even if less likely

Diagnosis likelihood thresholds:
- HIGH (>60%): Strong evidence supports this diagnosis
- MEDIUM (30-60%): Consistent with presentation, reasonable probability
- LOW (<30%): Possible but less likely; important to consider

Always include:
- At minimum 3, maximum 8 diagnoses
- At least one "cannot miss" diagnosis
- Proper ICD-10 coding
- Urgency classification for each diagnosis
- Recommended diagnostic workup

Be comprehensive but ranked — the most likely diagnosis should be first."""


class DiagnosisEntry(BaseModel):
    condition: str
    likelihood: str  # high, medium, low
    icd_10_code: Optional[str]
    reasoning: str
    supporting_findings: list[str]
    against_findings: list[str]
    urgency: str  # emergency, urgent, routine
    recommended_confirmatory_tests: list[str]
    cannot_miss: bool = False


class DifferentialDiagnosisResult(BaseModel):
    diagnoses: list[DiagnosisEntry] = Field(description="Ranked differential diagnoses, most likely first")
    primary_diagnosis: str = Field(description="Most likely diagnosis")
    cannot_miss_diagnoses: list[str] = Field(description="Dangerous diagnoses requiring active exclusion")
    diagnostic_reasoning: str = Field(description="Overall clinical reasoning narrative")
    recommended_immediate_workup: list[str] = Field(description="Most urgent diagnostic steps")
    confidence_level: str = Field(description="Overall confidence: high/medium/low")
    clinical_uncertainty: str = Field(description="Key uncertainties affecting diagnosis")


class DifferentialDiagnosisAgent(BaseHealthcareAgent):
    """Generates ranked differential diagnoses using Bayesian clinical reasoning."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="differential_diagnosis", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Generate a comprehensive differential diagnosis for this patient.

{patient_context}

Clinical Findings:
{clinical_findings}

Laboratory Data:
{lab_summary}

Medication Safety:
{drug_summary}

Generate your ranked differential diagnoses with Bayesian reasoning.""")
        ])
        return prompt | self.llm.with_structured_output(DifferentialDiagnosisResult)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        symptom_analysis = state.get("symptom_analysis") or {}
        lab_interp = state.get("lab_interpretation") or {}
        drug_int = state.get("drug_interactions") or []

        clinical_findings = (
            f"Symptom Pattern: {symptom_analysis.get('clinical_pattern', 'Not analyzed')}\n"
            f"Key Findings: {', '.join(symptom_analysis.get('key_findings', []))}\n"
            f"Systems Involved: {', '.join(symptom_analysis.get('systems_involved', []))}\n"
            f"Urgency: {symptom_analysis.get('urgency_assessment', 'Unknown')}"
        )

        lab_summary = lab_interp.get("overall_lab_summary", "No lab data available")
        if lab_interp.get("critical_values"):
            critical = [c.get("test_name") for c in lab_interp["critical_values"]]
            lab_summary += f"\nCritical Values: {', '.join(critical)}"

        major_interactions = [d for d in drug_int if d.get("severity") in ("major", "contraindicated")]
        drug_summary = (
            f"Major drug interactions: {len(major_interactions)}" if major_interactions
            else "No major drug interactions identified"
        )

        result: DifferentialDiagnosisResult = await self._invoke_with_retry(self.chain, {
            "patient_context": self._build_patient_context(state),
            "clinical_findings": clinical_findings,
            "lab_summary": lab_summary,
            "drug_summary": drug_summary,
        })

        # Map to workflow state format
        diagnoses = [
            {
                "condition": d.condition,
                "likelihood": d.likelihood,
                "reasoning": d.reasoning,
                "supporting_findings": d.supporting_findings,
                "against_findings": d.against_findings,
                "icd_code": d.icd_10_code,
                "urgency": d.urgency,
            }
            for d in result.diagnoses
        ]

        tokens = self._count_tokens(clinical_findings + lab_summary)
        return {
            "differential_diagnoses": diagnoses,
            "steps_completed": ["differential_diagnosis"],
            "tokens_used": tokens,
        }
