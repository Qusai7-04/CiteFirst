from fastapi.testclient import TestClient

import pytest

import api
from api import app


@pytest.mark.needs_symlinks
def test_static_only_serves_evaluation_charts(tmp_path, monkeypatch):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    monkeypatch.setattr(api, "ARTIFACTS_DIR", artifacts)

    # Place sensitive files outside the artifacts directory
    (tmp_path / ".env").write_text("SECRET=do-not-serve")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("private-git-config")
    (tmp_path / "api.py").write_text("private-source-code")

    # Place valid charts inside artifacts
    (artifacts / "metrics_chart_llm_llama3.18binstant.png").write_bytes(b"chart-data")
    (artifacts / "confusion_matrix_llm_llama3.18binstant.png").write_bytes(b"second-chart")
    (artifacts / "metrics_chart_symlink.png").symlink_to(tmp_path / ".env")

    client = TestClient(app)
    for url, secret in [
        ("/static/.env", b"do-not-serve"),
        ("/static/.git/config", b"private-git-config"),
        ("/static/api.py", b"private-source-code"),
        ("/static/metrics_chart_symlink.png", b"do-not-serve"),
    ]:
        response = client.get(url)
        assert response.status_code == 404
        assert secret not in response.content

    for name, expected in [
        ("metrics_chart_llm_llama3.18binstant.png", b"chart-data"),
        ("confusion_matrix_llm_llama3.18binstant.png", b"second-chart"),
    ]:
        response = client.get(f"/static/{name}")
        assert response.status_code == 200
        assert response.content == expected
        assert response.headers["content-type"] == "image/png"
