from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.policy_store import load_policies, get_policy, search_policies
from app.research_graph import research_graph


class ResearchRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Question about synthetic banking policies",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of policies to return",
    )


app = FastAPI(
    title="BankOps AI",
    description=(
        "A synthetic banking operations policy research API. "
        "For demonstration only; not for real banking decisions."
    ),
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "BankOps AI",
        "environment": "synthetic_demo",
    }


@app.get("/policies")
def list_policies():
    policies = load_policies()
    return {
        "count": len(policies),
        "policies": policies,
    }


@app.get("/policies/{policy_id}")
def read_policy(policy_id: str):
    policy = get_policy(policy_id)

    if policy is None:
        raise HTTPException(
            status_code=404,
            detail=f"Policy '{policy_id}' not found",
        )

    return policy


@app.get("/search")
def search(
    q: str = Query(
        ...,
        min_length=1,
        max_length=200,
        description="Keywords to search in synthetic policies",
    ),
    limit: int = Query(default=5, ge=1, le=20),
):
    results = search_policies(q, limit=limit)

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.post("/research")
def research(request: ResearchRequest):
    graph_result = research_graph.invoke(
        {
            "question": request.question,
            "limit": request.limit,
        }
    )

    results = graph_result["results"]
    status = graph_result["status"]
    verification_status = graph_result["verification_status"]

    if status == "no_matching_policies":
        return {
            "question": request.question,
            "count": 0,
            "results": [],
            "status": status,
            "verification_status": verification_status,
            "message": "No matching policies were found. Try different keywords.",
        }

    if verification_status != "passed":
        return {
            "question": request.question,
            "count": 0,
            "results": [],
            "status": "verification_failed",
            "verification_status": verification_status,
            "message": (
                "Research results could not be verified. "
                "They have not been returned as verified results."
            ),
        }

    return {
        "question": request.question,
        "count": len(results),
        "results": results,
        "status": status,
        "verification_status": verification_status,
        "message": "Matching policies were found and passed field verification.",
    }