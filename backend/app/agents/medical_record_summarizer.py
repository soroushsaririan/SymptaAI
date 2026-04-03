"""Medical Record Summarizer Agent — extracts structured info from clinical documents."""
from __future__ import annotations

from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.agents.base import BaseHealthcareAgent
from app.workflows.state import HealthcareWorkflowState

SYSTEM_PROMPT = """You are an expert medical transcriptionist and clinical documentation specialist with 20+ years of experience processing clinical records.

For each medical record, extract and structure:
1. **Diagnoses**: Active, historical, and resolved diagnoses with dates
2. **Treatments**: Medications prescribed, procedures performed, therapies given
3. **Outcomes**: Treatment responses, complications, discharge status
4. **Key Clinical Data**: Vital signs trends, weight changes, functional status
5. **Follow-up Requirements**: Pending tests, scheduled procedures, specialist recommendations
6. **Clinical Timeline**: Chronological sequence of events

Across multiple records:
- Identify disease progression and patterns
- Note changes in clinical status over time
- Flag inconsistencies or clinically significant changes
- Summarize the longitudinal clinical picture

Be precise — extract exact values, dates, and clinical terminology as documented."""


class RecordSummary(BaseModel):
    record_type: str
    summary_date: Optional[str]
    key_diagnoses: list[str]
    treatments_given: list[str]
    clinical_findings: list[str]
    outcomes: str
    follow_up_required: list[str]
    clinical_notes: str
    significant_events: list[str] = Field(default_factory=list)


class MultiRecordSummary(BaseModel):
    individual_summaries: list[RecordSummary]
    longitudinal_summary: str = Field(description="Overall clinical trajectory across all records")
    recurring_issues: list[str] = Field(description="Problems appearing in multiple records")
    disease_progression: str = Field(description="How the patient's condition has evolved")
    previous_workup: list[str] = Field(description="Diagnostic tests already performed")
    prior_treatments: list[str] = Field(description="All prior treatments and their outcomes")


class MedicalRecordSummarizerAgent(BaseHealthcareAgent):
    """Processes and summarizes uploaded clinical documents."""

    def __init__(self, llm=None) -> None:
        super().__init__(agent_name="medical_record_summarizer", llm=llm)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Summarize these medical records for patient: {patient_name}

RECORDS TO PROCESS:
{records_text}

Provide structured summaries for each record and an overall longitudinal summary.""")
        ])
        return prompt | self.llm.with_structured_output(MultiRecordSummary)

    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        records = state.get("medical_records", [])
        if not records:
            return {
                "record_summaries": [],
                "steps_completed": ["medical_record_summarizer"],
                "tokens_used": 10,
            }

        pd = state["patient_data"]
        # Truncate records to avoid token limits
        records_text = "\n\n---RECORD BREAK---\n\n".join(
            f"Record {i+1}:\n{rec[:3000]}" for i, rec in enumerate(records[:5])
        )

        result: MultiRecordSummary = await self._invoke_with_retry(self.chain, {
            "patient_name": pd.get("full_name", "Unknown"),
            "records_text": records_text,
        })

        summaries = [s.model_dump() for s in result.individual_summaries]
        summaries.append({
            "record_type": "longitudinal_summary",
            "summary_date": None,
            "key_diagnoses": result.recurring_issues,
            "treatments_given": result.prior_treatments,
            "clinical_findings": [],
            "outcomes": result.longitudinal_summary,
            "follow_up_required": [],
            "clinical_notes": result.disease_progression,
            "significant_events": [],
        })

        tokens = self._count_tokens(records_text)
        return {
            "record_summaries": summaries,
            "steps_completed": ["medical_record_summarizer"],
            "tokens_used": tokens,
        }
