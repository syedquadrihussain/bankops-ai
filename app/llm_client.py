from abc import ABC, abstractmethod

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class PolicySummary(BaseModel):
    """A short summary of one policy, plus its rules as separate lines."""

    summary: str = Field(description="At most three short sentences.")
    key_rules: list[str] = Field(
        description=(
            "One short line per rule, including every rule that says "
            "what must not be done."
        )
    )


class LLMClient(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Take policy text, return a short summary."""

    def summarize_policy(self, text: str) -> PolicySummary:
        """Return a summary and key rules. Simple models give no key rules."""
        return PolicySummary(summary=self.summarize(text), key_rules=[])


class FakeLLM(LLMClient):
    def summarize(self, text: str) -> str:
        return "FAKE SUMMARY: " + text[:50]

    def summarize_policy(self, text: str) -> PolicySummary:
        return PolicySummary(
            summary=self.summarize(text),
            key_rules=["FAKE RULE: " + text[:30]],
        )


SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You summarize synthetic bank policies for a human reviewer. "
            "Use only the policy text. Write at most three short sentences. "
            "Always keep any rule that says what must not be done.",
        ),
        ("human", "Policy text:\n{policy_text}"),
    ]
)


STRUCTURED_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You read synthetic bank policies for a human reviewer. "
            "Use only the policy text. Fill summary with at most three short "
            "sentences. Fill key_rules with one short line per rule, and "
            "include every rule that says what must not be done.",
        ),
        ("human", "Policy text:\n{policy_text}"),
    ]
)


class OllamaLLM(LLMClient):
    def __init__(self, model: str = "qwen2.5:3b", chat=None, structured_chain=None):
        if chat is None:
            from langchain_ollama import ChatOllama

            chat = ChatOllama(model=model, temperature=0)
        self._chat = chat
        self.chain = SUMMARY_PROMPT | chat | StrOutputParser()
        self._structured_chain = structured_chain

    def summarize(self, text: str) -> str:
        return self.chain.invoke({"policy_text": text})

    def summarize_policy(self, text: str) -> PolicySummary:
        if self._structured_chain is None:
            self._structured_chain = STRUCTURED_PROMPT | self._chat.with_structured_output(
                PolicySummary
            )
        return self._structured_chain.invoke({"policy_text": text})


def get_llm() -> LLMClient:
    import os

    provider = os.getenv("LLM_PROVIDER", "fake").lower()
    if provider == "ollama":
        return OllamaLLM(model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    if provider == "fake":
        return FakeLLM()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
