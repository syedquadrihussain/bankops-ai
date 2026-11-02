import json
import re

from langchain_core.tools import tool

from app import policy_store


MAX_TOOL_OUTPUT_CHARS = 4000

# Heuristic filter. It catches common tricks and cannot catch everything.
INJECTION_PATTERNS = [
    r"ignore (all |any |your |the )*(previous|prior|above) (instructions|rules)",
    r"disregard (all |any |your |the )*(previous|prior|above) (instructions|rules)",
    r"(reveal|show|print|repeat) (your |the )?(system prompt|hidden instructions)",
    r"from now on,? you",
    r"new instructions?:",
    r"you (must|should|will) (now )?(approve|reject|ignore|reveal|output|say)",
    r"</?(system|assistant|tool_result|tool)>",
    r"do not tell the (user|reviewer|human)",
]

INJECTION_WARNING = {
    "warning": "Tool result removed: it looked like it contained hidden instructions."
}


def looks_like_injection(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in INJECTION_PATTERNS)


def _as_json(value) -> str:
    text = json.dumps(value, ensure_ascii=False)
    if looks_like_injection(text):
        return json.dumps(INJECTION_WARNING)
    if len(text) > MAX_TOOL_OUTPUT_CHARS:
        return json.dumps(
            {
                "warning": "Tool result was too long and was cut.",
                "partial": text[:MAX_TOOL_OUTPUT_CHARS],
            }
        )
    return text


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
