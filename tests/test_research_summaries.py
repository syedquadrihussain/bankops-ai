from app import research_graph as rg

STATE = {
    "verification_status": "passed",
    "results": [{"policy_id": "P1", "version": "1", "content": "Show a valid ID."}],
}


def test_summarize_node_skips_unverified():
    state = {**STATE, "verification_status": "failed"}
    out = rg.summarize_node(state)
    assert out == {"summaries": [], "summary_status": "not_run"}


def test_summarize_node_uses_fake_llm_for_verified(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    out = rg.summarize_node(STATE)
    assert out["summary_status"] == "generated"
    assert out["summaries"][0]["policy_id"] == "P1"
    assert out["summaries"][0]["summary"].startswith("FAKE SUMMARY:")


def test_summarize_node_survives_llm_failure(monkeypatch):
    class Broken:
        def summarize(self, text):
            raise RuntimeError("model offline")

    monkeypatch.setattr(rg, "get_llm", lambda: Broken())
    out = rg.summarize_node(STATE)
    assert out == {"summaries": [], "summary_status": "unavailable"}
