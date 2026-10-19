import sys
from types import SimpleNamespace

import pytest

import providers


def test_provider_selection_and_missing_groq_key(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert providers.selected_provider() == "groq"
    with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
        providers.chat("prompt", "system")
    monkeypatch.setenv("LLM_PROVIDER", "invalid")
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        providers.selected_provider()


def test_groq_retries_rate_limits_with_existing_policy(monkeypatch):
    class RateLimit(Exception):
        pass

    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RateLimit()
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=" ok "))])

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(
        Groq=lambda api_key: SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create))), RateLimitError=RateLimit))
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    waits = []
    monkeypatch.setattr(providers.time, "sleep", waits.append)
    assert providers.chat("q", "s", max_tokens=9) == "ok"
    assert waits == [5]
    assert len(calls) == 2
    assert calls[0]["temperature"] == 0
    assert calls[0]["model"] == providers.GROQ_MODEL


def test_ollama_payload_and_configured_model(monkeypatch):
    sent = []

    def post(url, **kwargs):
        sent.append((url, kwargs))
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"message": {"content": " local answer "}})

    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(
        post=post, RequestException=RuntimeError))
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "local-model")
    assert providers.chat("prompt", "system", model=providers.GROQ_MODEL, max_tokens=99) == "local answer"
    url, kwargs = sent[0]
    assert url == "http://localhost:11434/api/chat"
    assert kwargs["json"] == {"model": "local-model", "stream": False,
                               "messages": [{"role": "system", "content": "system"},
                                            {"role": "user", "content": "prompt"}],
                               "options": {"temperature": 0, "num_predict": 99}}
    assert kwargs["timeout"] == (5, 120)
    providers.chat("prompt", "system", model="custom-model")
    assert sent[-1][1]["json"]["model"] == "custom-model"


@pytest.mark.parametrize("failure", ["timeout", "http", "malformed"])
def test_ollama_errors_are_catchable_and_identify_url(monkeypatch, failure):
    class RequestFailure(Exception):
        pass

    def post(url, **kwargs):
        if failure == "timeout":
            raise RequestFailure("private response body")
        def status():
            if failure == "http":
                raise RequestFailure("private response body")
        return SimpleNamespace(raise_for_status=status, json=lambda: {"wrong": "shape"})

    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(
        post=post, RequestException=RequestFailure))
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    with pytest.raises(providers.ProviderError, match="http://localhost:11434/api/chat") as caught:
        providers.chat("prompt", "system")
    assert "private response body" not in str(caught.value)
