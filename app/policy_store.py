import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
POLICY_FILE = PROJECT_ROOT / "data" / "policies.json"


def load_policies() -> list[dict[str, Any]]:
    """Load the synthetic policies from the JSON file."""
    if not POLICY_FILE.exists():
        raise FileNotFoundError(f"Policy file not found: {POLICY_FILE}")

    with POLICY_FILE.open("r", encoding="utf-8-sig") as file:
        policies = json.load(file)

    if not isinstance(policies, list):
        raise ValueError("The policy file must contain a JSON list.")

    required_fields = {
        "policy_id",
        "title",
        "version",
        "effective_date",
        "category",
        "content",
    }

    for index, policy in enumerate(policies):
        if not isinstance(policy, dict):
            raise ValueError(f"Policy at index {index} must be an object.")

        missing = required_fields - policy.keys()
        if missing:
            raise ValueError(
                f"Policy at index {index} is missing: {', '.join(sorted(missing))}"
            )

    return policies


def search_policies(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search synthetic policies using simple case-insensitive keyword matching."""
    if not query or not query.strip():
        return []

    if limit < 1:
        raise ValueError("limit must be at least 1.")

    terms = query.casefold().split()
    results = []

    for policy in load_policies():
        searchable_text = " ".join(
            str(policy[field])
            for field in ("policy_id", "title", "category", "content")
        ).casefold()

        matched_terms = sum(term in searchable_text for term in terms)

        if matched_terms:
            result = dict(policy)
            result["matched_terms"] = matched_terms
            results.append(result)

    results.sort(
        key=lambda policy: (
            -policy["matched_terms"],
            policy["policy_id"],
        )
    )

    return results[:limit]


def get_policy(policy_id: str) -> dict[str, Any] | None:
    """Return a policy by its exact policy ID, or None if it is not found."""
    requested_id = policy_id.strip().casefold()

    for policy in load_policies():
        if policy["policy_id"].casefold() == requested_id:
            return policy

    return None
