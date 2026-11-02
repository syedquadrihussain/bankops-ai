import pytest
from langchain_core.language_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda
from pydantic import ValidationError

from app import research_graph as rg
from app.llm_client import (
    STRUCTURED_PROMPT,
    FakeLLM,
    LLMClient,
    OllamaLLM,
    PolicySummary,
)


class OnlySummarize(LLMClient):
    def summarize(self, text):
        return "plain summary"


def test_policy_summary_requires_both_fields():
    with pytest.raises(ValidationError):
        PolicySummary(summary="only a summary")


def test_fake_llm_gives_summary_and_key_rules():
    result = FakeLLM().summarize_policy("Show a valid ID.")
    assert result.summary.startswith("FAKE SUMMARY:")
    assert result.key_rules


def test_simple_llm_falls_back_to_plain_summary():
    result = OnlySummarize().summarize_policy("text")
    assert result.summary == "plain summary"
    assert result.key_rules == []


def test_ollama_llm_returns_the_structured_result():
    expected = PolicySummary(
        summary="S", key_rules=["Do not approve on assertion alone."]
    )
    llm = OllamaLLM(
        chat=FakeListChatModel(responses=["unused"]),
        structured_chain=RunnableLambda(lambda inputs: expected),
    )
    assert llm.summarize_policy("Any text.") == expected


def test_structured_prompt_asks_for_prohibition_rules():
    messages = STRUCTURED_PROMPT.format_messages(policy_text="X {y}")
    assert "X {y}" in messages[1].content
    assert "must not be done" in messages[0].content


def test_summarize_node_adds_key_rules(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    state = {
        "verification_status": "passed",
        "results": [
            {"policy_id": "P1", "version": "1", "content": "Show a valid ID."}
        ],
    }
    item = rg.summarize_node(state)["summaries"][0]
    assert item["summary"].startswith("FAKE SUMMARY:")
    assert item["key_rules"]
