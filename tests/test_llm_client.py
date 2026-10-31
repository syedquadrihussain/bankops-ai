from app.llm_client import FakeLLM


def test_fake_llm_returns_summary():
    llm = FakeLLM()
    result = llm.summarize("Customers must show a valid ID to open an account.")
    assert result.startswith("FAKE SUMMARY:")


class StubChat:
    def invoke(self, prompt):
        class Reply:
            content = "STUB REPLY"
        return Reply()


def test_ollama_llm_uses_chat_reply():
    from app.llm_client import OllamaLLM
    llm = OllamaLLM(chat=StubChat())
    assert llm.summarize("Any policy text.") == "STUB REPLY"
