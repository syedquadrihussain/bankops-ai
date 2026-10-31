from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def summarize(self, text: str) -> str:
        """Take policy text, return a short summary."""


class FakeLLM(LLMClient):
    def summarize(self, text: str) -> str:
        return "FAKE SUMMARY: " + text[:50]


class OllamaLLM(LLMClient):
    def __init__(self, model: str = "qwen2.5:3b", chat=None):
        if chat is None:
            from langchain_ollama import ChatOllama
            chat = ChatOllama(model=model, temperature=0)
        self.chat = chat

    def summarize(self, text: str) -> str:
        prompt = (
            "Summarize this bank policy in two short sentences. "
            "Use only the text below.\n\n" + text
        )
        reply = self.chat.invoke(prompt)
        return reply.content
