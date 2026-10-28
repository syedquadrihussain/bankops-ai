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


class ResearchState(TypedDict, total=False):
    question: str
    limit: int
    results: list[dict[str, Any]]
    status: str
    verification_status: str
    review_status: str


def supervisor_node(state: ResearchState) -> dict:
    question = state.get("question", "")
    if not isinstance(question, str) or not question.strip():
        return {
            "results": [],
            "status": "invalid_question",
            "verification_status": "not_run",
            "review_status": "not_required",
        }
    return {}


def route_after_supervisor(state: ResearchState) -> str:
    return "stop" if state.get("status") == "invalid_question" else "research"


def research_node(state: ResearchState) -> dict:
    results = search_policies(state["question"], limit=state["limit"])
    return {
        "results": results,
        "status": "research_completed" if results else "no_matching_policies",
    }


def verification_node(state: ResearchState) -> dict:
    results = state.get("results", [])

    if not results:
        return {
            "verification_status": "no_results_to_verify",
            "review_status": "not_required",
        }

    if not isinstance(results, list):
        return {
            "verification_status": "failed",
            "review_status": "not_required",
        }

    for result in results:
        if not isinstance(result, dict):
            return {
                "verification_status": "failed",
                "review_status": "not_required",
            }

        for field in REQUIRED_POLICY_FIELDS:
            value = result.get(field)
            if not isinstance(value, str) or not value.strip():
                return {
                    "verification_status": "failed",
                    "review_status": "not_required",
                }

    return {"verification_status": "passed"}


def route_after_verification(state: ResearchState) -> str:
    return (
        "human_review"
        if state.get("verification_status") == "passed"
        else "stop"
    )


def human_review_node(state: ResearchState) -> dict:
    """Mark verified research as awaiting review, never as approved."""
    if state.get("verification_status") == "passed" and state.get("results"):
        return {"review_status": "pending_review"}
    return {"review_status": "not_required"}


builder = StateGraph(ResearchState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("research", research_node)
builder.add_node("verification", verification_node)
builder.add_node("human_review", human_review_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {"research": "research", "stop": END},
)
builder.add_edge("research", "verification")
builder.add_conditional_edges(
    "verification",
    route_after_verification,
    {"human_review": "human_review", "stop": END},
)
builder.add_edge("human_review", END)

research_graph = builder.compile()
