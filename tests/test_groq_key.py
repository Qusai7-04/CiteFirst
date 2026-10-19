import importlib.util
import sys
from types import SimpleNamespace

import pytest


def test_groq_key_is_required_only_at_call_time(monkeypatch):
    calls = []

    class FakeGroq:
        def __init__(self, api_key):
            calls.append(api_key)
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs:
                SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=" answer "))])))

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "dotenv", SimpleNamespace(load_dotenv=lambda: None))
    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=FakeGroq, RateLimitError=RuntimeError))
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(CrossEncoder=lambda *args: object()))
    monkeypatch.setitem(sys.modules, "database", SimpleNamespace(
        search_vault=lambda *args, **kwargs: None, DOMAIN_KEYWORDS={},
        check_vault_schema=lambda: "new"))

    spec = importlib.util.spec_from_file_location("logic_engine_key_test", "logic_engine.py")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    assert calls == []
    with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
        engine.call_llm("question")
    monkeypatch.setenv("GROQ_API_KEY", "configured-test-key")
    assert engine.call_llm("question") == "answer"
    assert calls == ["configured-test-key"]
    routed = []
    monkeypatch.setattr(engine.providers, "chat", lambda *args, **kwargs:
                        routed.append((args, kwargs)) or "routed")
    assert engine.call_llm("prompt", system="system", model="model", max_tokens=22, retries=1) == "routed"
    assert routed == [(("prompt", "system"), {"model": "model", "max_tokens": 22, "retries": 1})]
