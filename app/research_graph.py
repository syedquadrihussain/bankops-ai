from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.policy_store import search_policies


REQUIRED_POLICY_FIELDS = [
    "policy_id",
    "title",
    "version",
    "effective_date",
    "category",
    "content",
]


class ResearchState(TypedDict):
    question: str
    limit: int
    results: list[dict[str, Any]]
    status: str
    verification_status: str


def supervisor_node(state: ResearchState) -> dict:
    """Validate the question before starting research."""
    question = state.get("question", "")

    if not isinstance(question, str) or not question.strip():
        return {
            "results": [],
            "status": "invalid_question",
            "verification_status": "not_run",
        }

    return {}


def route_after_supervisor(state: ResearchState) -> str:
    """Choose whether research should start."""
    if state.get("status") == "invalid_question":
        return "stop"

    return "research"


def research_node(state: ResearchState) -> dict:
    """Search for matching synthetic banking policies."""
    results = search_policies(
        state["question"],
        limit=state["limit"],
    )

    if results:
        status = "research_completed"
    else:
        status = "no_matching_policies"

    return {
        "results": results,
        "status": status,
    }


def verification_node(state: ResearchState) -> dict:
    """Check required fields in each research result."""
    results = state.get("results", [])

    if results is None or results == []:
        return {
            "verification_status": "no_results_to_verify"
        }

    if not isinstance(results, list):
        return {
            "verification_status": "failed"
        }

    for result in results:
        if not isinstance(result, dict):
            return {
                "verification_status": "failed"
            }

        for field in REQUIRED_POLICY_FIELDS:
            value = result.get(field)

            if not isinstance(value, str) or not value.strip():
                return {
                    "verification_status": "failed"
                }

    return {
        "verification_status": "passed"
    }


builder = StateGraph(ResearchState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("research", research_node)
builder.add_node("verification", verification_node)

builder.add_edge(START, "supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {
        "research": "research",
        "stop": END,
    },
)

builder.add_edge("research", "verification")
builder.add_edge("verification", END)

research_graph = builder.compile()