import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models import FakeListChatModel

from app import agent_graph, auth, llm_client
from app.llm_client import GroqLLM, OllamaLLM, get_llm
from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parent.parent


def test_groq_without_a_key_is_refused(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError):
        get_llm()


def test_groq_with_a_key_gives_a_groq_llm_and_hides_the_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value_for_test")
    monkeypatch.setenv("GROQ_MODEL", "")
    llm = get_llm()
    assert isinstance(llm, GroqLLM)
    assert "gsk_secret_value_for_test" not in repr(llm._chat)


def test_groq_llm_works_with_any_langchain_chat_model():
    llm = GroqLLM(chat=FakeListChatModel(responses=["HOSTED REPLY"]))
    assert llm.summarize("text") == "HOSTED REPLY"


def test_ollama_and_groq_share_the_same_behavior():
    assert issubclass(OllamaLLM, llm_client.ChatModelLLM)
    assert issubclass(GroqLLM, llm_client.ChatModelLLM)


def test_agent_model_for_groq_needs_a_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError):
        agent_graph.default_model()


def test_agent_endpoint_accepts_the_groq_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setattr(
        agent_graph,
        "run_agent",
        lambda question: {
            "status": "completed",
            "answer": "ok",
            "tool_calls": [],
            "flagged": 0,
        },
    )
    headers = {"Authorization": "Bearer " + auth.create_access_token("asha", "analyst")}
    response = client.post("/agent/ask", json={"question": "hi"}, headers=headers)
    assert response.status_code == 200


def test_no_groq_key_is_stored_in_project_files():
    pattern = re.compile(r"gsk_[A-Za-z0-9]{20,}")
    skip = {".git", ".venv", "BankOpsAI_New", "__pycache__", ".pytest_cache"}
    suffixes = {".py", ".md", ".yml", ".yaml", ".txt", ".json", ".example"}
    names = {"Dockerfile", ".dockerignore", ".env.example"}
    found = []
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            if Path(name).suffix not in suffixes and name not in names:
                continue
            path = Path(folder) / name
            text = path.read_text(encoding="utf-8", errors="ignore")
            if pattern.search(text):
                found.append(str(path.relative_to(ROOT)))
    assert not found, found
