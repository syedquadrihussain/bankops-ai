import json

from langchain_core.tools import tool

from app import policy_store


def _as_json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


@tool
def search_policies(query: str) -> str:
    """Search the synthetic bank policies by keyword. Returns up to 3 matching policies as JSON."""
    results = policy_store.search_policies(query, limit=3)
    return _as_json({"count": len(results), "results": results})


@tool
def get_policy(policy_id: str) -> str:
    """Get the latest version of one synthetic bank policy by its policy_id, for example KYC-001."""
    policy = policy_store.get_policy(policy_id)
    if policy is None:
        return _as_json({"error": f"Policy '{policy_id}' not found."})
    return _as_json(policy)


@tool
def compare_policy_versions(policy_id: str) -> str:
    """Compare the two newest versions of one synthetic bank policy. Returns the field differences as JSON."""
    comparison = policy_store.compare_policy_versions(policy_id)
    if comparison is None:
        return _as_json(
            {"error": f"At least two versions of policy '{policy_id}' are required."}
        )
    return _as_json(comparison)


# Read-only tools only. Nothing here can change data or approve anything.
TOOLS = [search_policies, get_policy, compare_policy_versions]
