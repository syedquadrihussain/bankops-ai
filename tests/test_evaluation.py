import os

from app import evaluate


def test_every_deterministic_case_passes():
    results = evaluate.run_cases()
    failures = [r for r in results if not r["passed"]]
    assert not failures, failures


def test_there_are_at_least_twenty_cases():
    assert len(evaluate.run_cases()) >= 20


def test_model_cases_do_not_run_by_default():
    categories = {r["category"] for r in evaluate.run_cases()}
    assert evaluate.MODEL not in categories


def test_the_environment_is_restored_after_a_run():
    before = {
        name: os.environ.get(name)
        for name in ("JWT_SECRET", "BANKOPS_DB", "LLM_PROVIDER")
    }
    evaluate.run_cases()
    after = {name: os.environ.get(name) for name in before}
    assert before == after


def test_reports_show_the_overall_score():
    results = evaluate.run_cases()
    assert "Overall:" in evaluate.format_text(results)
    assert "**Overall**" in evaluate.format_markdown(results)
