import json
from fastapi.testclient import TestClient
import api


def test_api_title_and_brand_identity():
    assert api.app.title == "CiteFirst — Research Assistant with Citations API"
    assert hasattr(api, "PIPELINE_AVAILABLE")
    assert hasattr(api, "crag_available")
    assert api.crag_available == api.PIPELINE_AVAILABLE


def test_health_endpoint_truthful_when_pipeline_available(monkeypatch):
    monkeypatch.setattr(api, "PIPELINE_AVAILABLE", True)
    monkeypatch.setattr(api, "crag_available", True)
    client = TestClient(api.app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["pipeline_available"] is True
    assert data["crag_available"] is True
    assert data["ready"] is True
    assert "operational" in data["detail"].lower() or "ready" in data["detail"].lower()


def test_health_endpoint_degraded_when_pipeline_unavailable(monkeypatch):
    monkeypatch.setattr(api, "PIPELINE_AVAILABLE", False)
    monkeypatch.setattr(api, "crag_available", False)
    client = TestClient(api.app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["pipeline_available"] is False
    assert data["crag_available"] is False
    assert data["ready"] is False
    assert "unavailable" in data["detail"].lower() or "stub" in data["detail"].lower()


def test_chat_history_migration_logic():
    """
    Simulate the localStorage migration logic implemented in useChatHistory.ts:
    If citefirst_chat_sessions exists, load it.
    If only crag_chat_sessions exists, migrate it to citefirst_chat_sessions without losing data.
    """
    mock_storage = {}
    legacy_key = "crag_chat_sessions"
    primary_key = "citefirst_chat_sessions"

    saved_session = [{
        "id": "sess_1",
        "title": "Quantum Entanglement",
        "createdAt": 1700000000000,
        "updatedAt": 1700000000000,
        "messages": [{"id": "m1", "role": "user", "content": "Explain entanglement"}]
    }]

    # Case 1: Legacy key present, primary key absent
    mock_storage[legacy_key] = json.dumps(saved_session)

    # Migration function matching loadStoredSessions in useChatHistory.ts
    def load_stored_sessions(storage):
        current_raw = storage.get(primary_key)
        if current_raw:
            try:
                parsed = json.loads(current_raw)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass

        legacy_raw = storage.get(legacy_key)
        if legacy_raw:
            try:
                parsed = json.loads(legacy_raw)
                if isinstance(parsed, list):
                    storage[primary_key] = legacy_raw
                    return parsed
            except Exception:
                pass
        return []

    loaded = load_stored_sessions(mock_storage)
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Quantum Entanglement"
    assert primary_key in mock_storage
    assert mock_storage[primary_key] == mock_storage[legacy_key]

    # Case 2: Primary key already present
    mock_storage[primary_key] = json.dumps([{"id": "sess_2", "title": "New CiteFirst Chat"}])
    loaded_new = load_stored_sessions(mock_storage)
    assert len(loaded_new) == 1
    assert loaded_new[0]["title"] == "New CiteFirst Chat"
