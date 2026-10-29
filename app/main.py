from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app import policy_store
from app.research_graph import research_graph


app = FastAPI(
    title="BankOps AI",
    description=(
        "A portfolio MVP demonstrating evidence-backed search over "
        "synthetic banking policies, policy version comparison, and "
        "an explicit human-review decision workflow. "
        "Not for real banking or compliance decisions."
    ),
    version="0.3.0",
)


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

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question must not be empty or whitespace.")
        return value.strip()


class ReviewDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"] = Field(
        ...,
        description="Explicit human review decision",
    )
    reviewer: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Reviewer identifier for this demo",
    )

    @field_validator("reviewer")
    @classmethod
    def reviewer_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Reviewer must not be empty or whitespace.")
        return value.strip()


# Process-local demonstration storage.
# Records disappear when the application process restarts.
review_records: dict[str, dict] = {}
review_lock = Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def public_review_record(record: dict) -> dict:
    """Return a copy so callers cannot mutate the stored record."""
    return {
        "review_id": record["review_id"],
        "question": record["question"],
        "count": len(record["results"]),
        "results": record["results"],
        "review_status": record["review_status"],
        "created_at": record["created_at"],
        "decided_at": record["decided_at"],
        "reviewer": record["reviewer"],
    }


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
        ...,
        min_length=1,
        max_length=200,
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

    # Fail closed: unverified results are never exposed as verified.
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

    if not results:
        return {
            "question": request.question,
            "count": 0,
            "results": [],
            "status": status,
            "verification_status": verification_status,
            "review_status": "not_required",
            "message": "No results are available for human review.",
        }

    review_id = str(uuid4())
    record = {
        "review_id": review_id,
        "question": request.question,
        "results": results,
        "review_status": "pending_review",
        "created_at": utc_now(),
        "decided_at": None,
        "reviewer": None,
    }

    with review_lock:
        review_records[review_id] = record

    return {
        "question": request.question,
        "count": len(results),
        "results": results,
        "status": status,
        "verification_status": verification_status,
        "review_status": "pending_review",
        "review_id": review_id,
        "message": (
            "Matching policies passed field verification and are awaiting "
            "human review. No approval or banking action has been performed."
        ),
    }


@app.get("/reviews/{review_id}")
def get_review(review_id: str):
    with review_lock:
        record = review_records.get(review_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Review not found.")
        return public_review_record(record)


@app.post("/reviews/{review_id}/decision")
def decide_review(review_id: str, request: ReviewDecisionRequest):
    with review_lock:
        record = review_records.get(review_id)

        if record is None:
            raise HTTPException(status_code=404, detail="Review not found.")

        if record["review_status"] != "pending_review":
            raise HTTPException(
                status_code=409,
                detail="This review already has a final decision.",
            )

        record["review_status"] = (
            "approved" if request.decision == "approve" else "rejected"
        )
        record["reviewer"] = request.reviewer
        record["decided_at"] = utc_now()

        response = public_review_record(record)

    response["decision"] = request.decision
    response["message"] = (
        "Review decision recorded. No banking action was executed."
    )
    return response
