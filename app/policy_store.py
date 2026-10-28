from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICY_FILE = Path(__file__).resolve().parent.parent / "data" / "policies.json"
REQUIRED_FIELDS = (
    "policy_id",
    "title",
    "version",
    "effective_date",
    "category",
    "content",
)


def load_policies() -> list[dict[str, Any]]:
    """Load and validate the synthetic policy catalogue."""
    if not POLICY_FILE.exists():
        raise FileNotFoundError(f"Policy file not found: {POLICY_FILE}")

    try:
        with POLICY_FILE.open("r", encoding="utf-8-sig") as file:
            policies = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Policy file contains invalid JSON: {exc}") from exc

    if not isinstance(policies, list):
        raise ValueError("Policy file must contain a JSON list.")

    seen: set[tuple[str, str]] = set()
    for index, policy in enumerate(policies):
        if not isinstance(policy, dict):
            raise ValueError(f"Policy at index {index} must be an object.")

        for field in REQUIRED_FIELDS:
            value = policy.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Policy at index {index} has a missing or blank '{field}'."
                )

        key = (policy["policy_id"].casefold(), policy["version"].casefold())
        if key in seen:
            raise ValueError(
                f"Duplicate policy/version pair: {policy['policy_id']} "
                f"version {policy['version']}."
            )
        seen.add(key)

    return policies


def get_policy_versions(policy_id: str) -> list[dict[str, Any]]:
    """Return versions for a policy, newest effective date first."""
    wanted = policy_id.strip().casefold()
    matches = [
        policy for policy in load_policies()
        if policy["policy_id"].casefold() == wanted
    ]
    return sorted(
        matches,
        key=lambda policy: (policy["effective_date"], policy["version"]),
        reverse=True,
    )


def get_policy(policy_id: str) -> dict[str, Any] | None:
    """Return the latest version of a policy, or None if not found."""
    versions = get_policy_versions(policy_id)
    return versions[0] if versions else None


def compare_policy_versions(policy_id: str) -> dict[str, Any] | None:
    """Compare the two newest versions; return None if fewer than two exist."""
    versions = get_policy_versions(policy_id)
    if len(versions) < 2:
        return None

    newer, older = versions[0], versions[1]
    fields = ("title", "effective_date", "category", "content")
    changes = {
        field: {
            "old": older[field],
            "new": newer[field],
            "changed": older[field] != newer[field],
        }
        for field in fields
    }

    return {
        "policy_id": newer["policy_id"],
        "old_version": older["version"],
        "new_version": newer["version"],
        "changes": changes,
    }


def search_policies(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Simple case-insensitive keyword search across synthetic policies."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    query = query.strip().casefold()
    if not query:
        return []

    terms = [term for term in query.split() if term]
    scored: list[tuple[int, dict[str, Any]]] = []

    for policy in load_policies():
        searchable = " ".join(
            str(policy[field]) for field in REQUIRED_FIELDS
        ).casefold()
        score = sum(searchable.count(term) for term in terms)
        if score:
            scored.append((score, policy))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1]["policy_id"],
            item[1]["effective_date"],
            item[1]["version"],
        )
    )
    return [policy for _, policy in scored[:limit]]
