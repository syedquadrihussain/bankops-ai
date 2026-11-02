from app.llm_client import FakeLLM


def test_fake_llm_returns_summary():
    llm = FakeLLM()
    result = llm.summarize("Customers must show a valid ID to open an account.")
    assert result.startswith("FAKE SUMMARY:")


def test_ollama_llm_uses_chat_reply():
    from langchain_core.language_models import FakeListChatModel

    from app.llm_client import OllamaLLM

    llm = OllamaLLM(chat=FakeListChatModel(responses=["STUB REPLY"]))
    assert llm.summarize("Any policy text.") == "STUB REPLY"


def test_get_llm_defaults_to_fake(monkeypatch):
    from app.llm_client import get_llm

    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert isinstance(get_llm(), FakeLLM)


def test_get_llm_rejects_unknown_provider(monkeypatch):
    import pytest
    from app.llm_client import get_llm

    monkeypatch.setenv("LLM_PROVIDER", "nope")
    with pytest.raises(ValueError):
        get_llm()


def test_summary_prompt_keeps_policy_text_and_prohibition_rule():
    from app.llm_client import SUMMARY_PROMPT

    policy = "Do not approve unsupported claims. {x}"
    messages = SUMMARY_PROMPT.format_messages(policy_text=policy)
    assert policy in messages[1].content
    assert "must not be done" in messages[0].content
