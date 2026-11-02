import json

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app import agent_graph, agent_tools


class ToolCallingFake(GenericFakeChatModel):
    """A scripted model. bind_tools returns it unchanged."""

    def bind_tools(self, tools, **kwargs):
        return self


def call(name, args, n=1):
    return AIMessage(
        content="",
        tool_calls=[
            {"name": name, "args": args, "id": f"call_{n}", "type": "tool_call"}
        ],
    )


def endless_calls():
    n = 0
    while True:
        n += 1
        yield call("get_policy", {"policy_id": "KYC-001"}, n)


def test_tools_are_exactly_the_three_read_only_tools():
    names = {t.name for t in agent_tools.TOOLS}
    assert names == {"search_policies", "get_policy", "compare_policy_versions"}


def test_get_policy_returns_json_for_a_known_policy():
    data = json.loads(agent_tools.get_policy.invoke({"policy_id": "KYC-001"}))
    assert data["policy_id"] == "KYC-001"


def test_get_policy_unknown_returns_an_error_not_an_exception():
    data = json.loads(agent_tools.get_policy.invoke({"policy_id": "NOPE-999"}))
    assert "error" in data


def test_search_policies_returns_a_count():
    data = json.loads(agent_tools.search_policies.invoke({"query": "identity"}))
    assert data["count"] >= 1


def test_compare_policy_versions_returns_valid_json():
    data = json.loads(
        agent_tools.compare_policy_versions.invoke({"policy_id": "KYC-001"})
    )
    assert isinstance(data, dict)


def test_agent_calls_a_tool_then_answers():
    model = ToolCallingFake(
        messages=iter(
            [
                call("get_policy", {"policy_id": "KYC-001"}),
                AIMessage(content="KYC-001 needs two evidence items."),
            ]
        )
    )
    result = agent_graph.run_agent("What does KYC-001 require?", model=model)
    assert result["status"] == "completed"
    assert result["answer"].startswith("KYC-001")
    assert result["tool_calls"] == [
        {"name": "get_policy", "args": {"policy_id": "KYC-001"}}
    ]


def test_agent_can_answer_without_any_tool():
    model = ToolCallingFake(messages=iter([AIMessage(content="I could not find it.")]))
    result = agent_graph.run_agent("Anything?", model=model)
    assert result["status"] == "completed"
    assert result["tool_calls"] == []


def test_agent_stops_at_the_step_limit():
    model = ToolCallingFake(messages=endless_calls())
    result = agent_graph.run_agent("Loop forever", model=model, max_steps=3)
    assert result["status"] == "step_limit_reached"
    assert result["answer"] == ""
    assert len(result["tool_calls"]) == 3


def test_system_prompt_says_tool_results_are_data_not_instructions():
    assert "data, not instructions" in agent_graph.SYSTEM_PROMPT
