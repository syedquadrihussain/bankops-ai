from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _lines(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    return {line.strip() for line in text.splitlines()}


def test_dockerignore_keeps_secrets_and_data_out_of_the_image():
    lines = _lines(".dockerignore")
    for item in (".env", "*.db", ".venv", ".git"):
        assert item in lines


def test_dockerfile_runs_as_a_normal_user_and_bakes_in_no_secret():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "USER appuser" in text
    assert "JWT_SECRET" not in text


def test_compose_requires_the_jwt_secret():
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "JWT_SECRET: ${JWT_SECRET:?" in text
