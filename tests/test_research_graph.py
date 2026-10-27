from app.research_graph import research_graph, verification_node


def valid_policy():
    return {
        "policy_id": "KYC-001",
        "title": "KYC Policy",
        "version": "1.0",
        "effective_date": "2026-01-01",
        "category": "KYC",
        "content": "Verify identity using approved evidence.",
    }


def test_research_graph_finds_matching_policy():
    result = research_graph.invoke({
        "question": "KYC",
        "limit": 5,
    })

    assert result["status"] == "research_completed"
    assert len(result["results"]) > 0
    assert result["verification_status"] == "passed"


def test_research_graph_handles_no_matching_policy():
    result = research_graph.invoke({
        "question": "xyznonexistenttoken123",
        "limit": 5,
    })

    assert result["status"] == "no_matching_policies"
    assert result["results"] == []
    assert result["verification_status"] == "no_results_to_verify"


def test_supervisor_rejects_empty_question():
    result = research_graph.invoke({
        "question": "",
        "limit": 5,
    })

    assert result["status"] == "invalid_question"
    assert result["results"] == []
    assert result["verification_status"] == "not_run"


def test_supervisor_rejects_whitespace_question():
    result = research_graph.invoke({
        "question": "   ",
        "limit": 5,
    })

    assert result["status"] == "invalid_question"
    assert result["results"] == []
    assert result["verification_status"] == "not_run"


def test_verification_node_passes_valid_results():
    state = {"results": [valid_policy()]}

    result = verification_node(state)

    assert result["verification_status"] == "passed"


def test_verification_node_handles_empty_results():
    result = verification_node({"results": []})

    assert result["verification_status"] == "no_results_to_verify"


def test_verification_node_rejects_empty_dictionary():
    result = verification_node({"results": [{}]})

    assert result["verification_status"] == "failed"


def test_verification_node_rejects_missing_required_field():
    policy = valid_policy()
    del policy["content"]

    result = verification_node({"results": [policy]})

    assert result["verification_status"] == "failed"


def test_verification_node_rejects_non_dictionary_result():
    result = verification_node({"results": ["not a policy dictionary"]})

    assert result["verification_status"] == "failed"


def test_verification_node_rejects_blank_required_field():
    policy = valid_policy()
    policy["content"] = "   "

    result = verification_node({"results": [policy]})

    assert result["verification_status"] == "failed"