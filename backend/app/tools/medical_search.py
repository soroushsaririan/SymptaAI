"""Medical knowledge RAG tools for agent use."""
from __future__ import annotations

from typing import Any

from langchain_core.documents import Document
from langchain_core.tools import tool


def get_medical_tools(retriever: Any) -> list:
    """Return a list of LangChain tools backed by the medical knowledge retriever."""

    @tool
    async def search_medical_guidelines(query: str) -> str:
        """Search medical guidelines and clinical practice recommendations.

        Use this to find evidence-based clinical guidelines for diagnosis and treatment.
        """
        docs: list[Document] = await retriever.ainvoke(query)
        if not docs:
            return "No relevant guidelines found."
        return "\n\n".join(
            f"[{doc.metadata.get('source', 'Medical Guideline')}]\n{doc.page_content}"
            for doc in docs[:3]
        )

    @tool
    async def search_drug_information(drug_name: str) -> str:
        """Search drug information including interactions, contraindications, and dosing.

        Use this when checking medication safety or looking up drug-specific information.
        """
        docs: list[Document] = await retriever.ainvoke(f"drug information {drug_name} interactions")
        if not docs:
            return f"No drug information found for {drug_name}."
        return "\n\n".join(doc.page_content for doc in docs[:3])

    @tool
    async def search_diagnostic_criteria(condition: str) -> str:
        """Search diagnostic criteria and clinical decision rules for medical conditions.

        Use this to find established diagnostic criteria (e.g., DSM-5, Rome IV, Wells criteria).
        """
        docs: list[Document] = await retriever.ainvoke(f"diagnostic criteria {condition}")
        if not docs:
            return f"No diagnostic criteria found for {condition}."
        return "\n\n".join(doc.page_content for doc in docs[:3])

    return [search_medical_guidelines, search_drug_information, search_diagnostic_criteria]
