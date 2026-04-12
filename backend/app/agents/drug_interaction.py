"""Drug Interaction Agent — checks medication safety."""
from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are a clinical pharmacist with specialized expertise in drug interactions, pharmacokinetics, and medication safety.

Your responsibilities:
1. Check ALL medication pairs for clinically significant interactions
2. Identify allergy-medication conflicts
3. Assess medication appropriateness for patient demographics
4. Consider drug-drug, drug-disease, and drug-allergy interactions
5. Review dosing appropriateness based on renal/hepatic function indicators

Interaction Severity Classification:
- CONTRAINDICATED: Must not be used together (e.g., MAOIs + SSRIs = serotonin syndrome)
- MAJOR: Risk of severe adverse effects; requires monitoring or substitution
- MODERATE: May require dose adjustment or monitoring
- MINOR: Clinical significance is minimal

Common critical interaction pairs to check:
- Anticoagulants (warfarin, heparin) + NSAIDs → bleeding risk
- QT-prolonging drugs (amiodarone, haloperidol) + other QT prolongers → arrhythmia
- ACE inhibitors + potassium-sparing diuretics → hyperkalemia
- Methotrexate + NSAIDs → methotrexate toxicity
- Digoxin + amiodarone → digoxin toxicity
- Lithium + diuretics → lithium toxicity
- Statins + CYP3A4 inhibitors → rhabdomyolysis risk

Always provide specific, actionable recommendations."""


class DrugInteractionFinding(BaseModel):
    drug1: str
    drug2: str
    severity: str  # minor, moderate, major, contraindicated
    mechanism: str
    clinical_effects: str
    recommendation: str


class AllergyConflict(BaseModel):
    medication: str
    allergen: str
    cross_reactivity: str
    recommendation: str


class DrugInteractionResult(BaseModel):
    interactions: list[DrugInteractionFinding] = Field(description="All drug-drug interactions found")
    allergy_conflicts: list[AllergyConflict] = Field(description="Medication-allergy conflicts")
    dose_concerns: list[dict[str, Any]] = Field(default_factory=list, description="Dosing appropriateness concerns")
    monitoring_requirements: list[str] = Field(default_factory=list, description="Required lab monitoring")
    recommendations: list[str] = Field(description="Specific actionable recommendations")
    overall_medication_safety: str = Field(description="safe / caution / unsafe")
    safety_narrative: str = Field(description="Overall medication safety narrative")
    has_contraindications: bool


class DrugInteractionAgent(BaseHealthcareAgent):
    """Evaluates medication safety including interactions and allergy conflicts."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="drug_interaction", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Perform a comprehensive medication safety review for this patient.

{patient_context}

Current Medications (detailed):
{medications_detail}

Known Allergies: {allergies}

Relevant Lab Context (for renal/hepatic assessment):
{lab_context}

Please check all medication interactions, allergy conflicts, and provide safety recommendations.""")
        ])
        return prompt | self.llm.with_structured_output(DrugInteractionResult)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        pd = state["patient_data"]
        medications = pd.get("current_medications", [])

        if not medications:
            return {
                "drug_interactions": [],
                "steps_completed": ["drug_interaction"],
                "tokens_used": 10,
            }

        meds_detail = "\n".join(
            f"- {m.get('name', 'Unknown')} {m.get('dose', '')} {m.get('frequency', '')} "
            f"({m.get('route', 'oral')}) - Indication: {m.get('indication', 'Not specified')}"
            for m in medications
        )
        lab_interp = state.get("lab_interpretation", {})
        lab_context = lab_interp.get("overall_lab_summary", "No lab data available") if lab_interp else "No lab data"

        result: DrugInteractionResult = await self._invoke_with_retry(self.chain, {
            "patient_context": self._build_patient_context(state),
            "medications_detail": meds_detail,
            "allergies": ", ".join(pd.get("allergies", [])) or "No known drug allergies",
            "lab_context": lab_context,
        })

        # Map to workflow state format
        interactions = [
            {
                "drug1": i.drug1,
                "drug2": i.drug2,
                "severity": i.severity,
                "description": f"{i.mechanism} — {i.clinical_effects}",
                "recommendation": i.recommendation,
            }
            for i in result.interactions
        ]

        tokens = self._count_tokens(meds_detail)
        return {
            "drug_interactions": interactions,
            "steps_completed": ["drug_interaction"],
            "tokens_used": tokens,
        }
