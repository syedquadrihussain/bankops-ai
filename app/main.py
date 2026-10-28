from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app import policy_store
from app.research_graph import research_graph


app = FastAPI(
    title="BankOps AI",
    description=(
        "A portfolio MVP demonstrating evidence-backed search over "
        "synthetic banking policies, policy version comparison, and "
        "a human-review-oriented research workflow. "
        "Not for real banking or compliance decisions."
    ),
    version="0.2.0",
)


class ResearchRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=500,
        description="Question about synthetic banking policies",
    )
    limit: int = Field(
        default=5, ge=1, le=20,
        description="Maximum number of policies to return",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be empty or whitespace.")
        return value.strip()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "BankOps AI",
        "environment": "synthetic_demo",
    }


@app.get("/policies")
def list_policies():
    policies = policy_store.load_policies()
    return {"count": len(policies), "policies": policies}


@app.get("/policies/{policy_id}/compare")
def compare_policy_versions(policy_id: str):
    comparison = policy_store.compare_policy_versions(policy_id)
    if comparison is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"At least two versions of policy '{policy_id}' "
                "are required for comparison."
            ),
        )
    return comparison


@app.get("/policies/{policy_id}")
def read_policy(policy_id: str):
    policy = policy_store.get_policy(policy_id)
    if policy is None:
        raise HTTPException(
            status_code=404,
            detail=f"Policy '{policy_id}' not found",
        )
    return policy


@app.get("/search")
def search(
    q: str = Query(
        ..., min_length=1, max_length=200,
        description="Keywords to search in synthetic policies",
    ),
    limit: int = Query(default=5, ge=1, le=20),
):
    results = policy_store.search_policies(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@app.post("/research")
def research(request: ResearchRequest):
    result = research_graph.invoke({
        "question": request.question,
        "limit": request.limit,
    })

    status = result.get("status", "research_completed")
    verification_status = result.get("verification_status", "not_run")
    review_status = result.get("review_status", "not_required")
    results = result.get("results", [])

    if status == "no_matching_policies" and not results:
        return {
            "question": request.question,
            "count": 0,
            "results": [],
            "status": "no_matching_policies",
            "verification_status": verification_status,
            "review_status": "not_required",
            "message": "No matching policies were found. Try different keywords.",
        }

    # Fail closed: never return results as verified if verification fails.
    if verification_status != "passed":
        return {
            "question": request.question,
            "count": 0,
            "results": [],
            "status": "verification_failed",
            "verification_status": verification_status,
            "review_status": "not_required",
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
        "review_status": review_status,
        "message": (
            "Matching policies passed field verification and are awaiting "
            "human review. No approval or banking action has been performed."
        ),
    }
