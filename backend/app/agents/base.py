"""Abstract base class for all healthcare agents."""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.workflows.state import HealthcareWorkflowState

settings = get_settings()


class BaseHealthcareAgent(ABC):
    """Abstract base for all healthcare domain agents.

    Each agent receives the shared workflow state and returns a partial
    state dict with its output fields populated.
    """

    def __init__(
        self,
        agent_name: str,
        llm: BaseLanguageModel | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.logger = get_logger(f"agent.{agent_name}")
        self.llm = llm or self._default_llm()

    def _default_llm(self) -> ChatOpenAI:
        kwargs: dict = dict(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=0.1,
        )
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        return ChatOpenAI(**kwargs)

    @abstractmethod
    async def run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        """Execute the agent logic and return a partial state update dict."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=False,
    )
    async def _invoke_with_retry(self, chain: Any, input_data: dict[str, Any]) -> Any:
        """Invoke a LangChain chain with exponential backoff retry."""
        try:
            return await chain.ainvoke(input_data)
        except Exception as exc:
            self.logger.warning(
                "agent_invocation_failed",
                agent=self.agent_name,
                error=str(exc),
            )
            raise

    def _count_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars ≈ 1 token)."""
        return max(1, len(text) // 4)

    def _build_patient_context(self, state: HealthcareWorkflowState) -> str:
        """Render a concise patient summary string for LLM context."""
        pd = state["patient_data"]
        meds = ", ".join(m.get("name", "") for m in pd.get("current_medications", []))
        allergies = ", ".join(pd.get("allergies", [])) or "NKDA"
        symptoms = ", ".join(pd.get("symptoms", []))
        return (
            f"Patient: {pd.get('full_name', 'Unknown')}, "
            f"Age: {pd.get('age', '?')}, Gender: {pd.get('gender', '?')}\n"
            f"Chief Complaint: {pd.get('chief_complaint', 'Not specified')}\n"
            f"Symptoms: {symptoms}\n"
            f"Duration: {pd.get('symptom_duration', 'Unknown')}, "
            f"Severity: {pd.get('severity', '?')}/10\n"
            f"Allergies: {allergies}\n"
            f"Current Medications: {meds or 'None'}\n"
        )

    async def safe_run(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        """Wrapper around run() that catches all exceptions and returns errors."""
        self.logger.info("agent_starting", agent=self.agent_name, run_id=state["agent_run_id"])
        try:
            result = await self.run(state)
            self.logger.info("agent_completed", agent=self.agent_name)
            return result
        except Exception as exc:
            self.logger.error(
                "agent_failed",
                agent=self.agent_name,
                error=str(exc),
                exc_info=True,
            )
            return {
                "errors": [f"{self.agent_name}: {str(exc)}"],
                "steps_completed": [],
            }
