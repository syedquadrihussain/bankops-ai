from abc import ABC, abstractmethod

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


class LLMClient(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Take policy text, return a short summary."""


class FakeLLM(LLMClient):
    def summarize(self, text: str) -> str:
        return "FAKE SUMMARY: " + text[:50]


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


class OllamaLLM(LLMClient):
    def __init__(self, model: str = "qwen2.5:3b", chat=None):
        if chat is None:
            from langchain_ollama import ChatOllama

            chat = ChatOllama(model=model, temperature=0)
        self.chain = SUMMARY_PROMPT | chat | StrOutputParser()

    def summarize(self, text: str) -> str:
        return self.chain.invoke({"policy_text": text})


def get_llm() -> LLMClient:
    import os

    provider = os.getenv("LLM_PROVIDER", "fake").lower()
    if provider == "ollama":
        return OllamaLLM(model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
    if provider == "fake":
        return FakeLLM()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
