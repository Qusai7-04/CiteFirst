import sys
from types import SimpleNamespace

import pytest

import providers


def test_provider_selection_and_missing_keys(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert providers.selected_provider() == "openrouter"
    with pytest.raises(EnvironmentError, match="OPENROUTER_API_KEY"):
        providers.chat("prompt", "system")
    monkeypatch.setenv("OPENROUTER_API_KEY", "PASTE_YOUR_OPENROUTER_API_KEY_HERE")
    with pytest.raises(EnvironmentError, match="OPENROUTER_API_KEY"):
        providers.chat("prompt", "system")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert providers.selected_provider() == "gemini"
    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        providers.chat("prompt", "system")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert providers.selected_provider() == "groq"
    with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
        providers.chat("prompt", "system")
    monkeypatch.setenv("LLM_PROVIDER", "invalid")
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        providers.selected_provider()


def test_openrouter_chat_success_and_model_forwarding(monkeypatch):
    calls = []
    traces = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                model=kwargs["model"],
                choices=[SimpleNamespace(message=SimpleNamespace(content="  openrouter response text  "), finish_reason="stop")],
                usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15, cost=0.0001)
            )

    class FakeOpenAI:
        def __init__(self, api_key, base_url):
            calls.append({"api_key": api_key, "base_url": base_url})
            self.chat = SimpleNamespace(completions=FakeCompletions())

    fake_openai_mod = SimpleNamespace(
        OpenAI=FakeOpenAI,
        APIError=type("APIError", (Exception,), {}),
        RateLimitError=type("RateLimitError", (Exception,), {}),
        AuthenticationError=type("AuthenticationError", (Exception,), {}),
    )
    monkeypatch.setitem(sys.modules, "openai", fake_openai_mod)

    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "valid-openrouter-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")

    out = providers.chat("test prompt", "test system", model="custom-model", max_tokens=256,
                         on_trace=lambda event, data: traces.append((event, data)))
    assert out == "openrouter response text"
    assert calls[0]["api_key"] == "valid-openrouter-key"
    assert calls[0]["base_url"] == "https://openrouter.ai/api/v1"
    assert calls[1]["model"] == "custom-model"
    assert calls[1]["max_tokens"] == 256
    assert calls[1]["temperature"] == 0.0
    assert calls[1]["messages"] == [{"role": "system", "content": "test system"}, {"role": "user", "content": "test prompt"}]
    assert len(traces) == 1
    assert traces[0][0] == "provider_call"
    assert traces[0][1]["cost"] == 0.0001

    # Legacy model mapping check
    calls.clear()
    out = providers.chat("prompt2", "system2", model="gemini-2.5-flash")
    assert out == "openrouter response text"
    assert calls[1]["model"] == "meta-llama/llama-3.3-70b-instruct"

    # Empty OPENROUTER_MODEL falls back to default supported model
    calls.clear()
    monkeypatch.setenv("OPENROUTER_MODEL", "")
    out = providers.chat("prompt3", "system3")
    assert out == "openrouter response text"
    assert calls[1]["model"] == providers.OPENROUTER_DEFAULT_MODEL


def test_openrouter_error_classification_and_retries(monkeypatch):
    class FakeAuthError(Exception):
        pass
    class FakeRateLimit(Exception):
        pass
    class FakeAPIError(Exception):
        def __init__(self, code, message):
            self.code = code
            self.message = message

    calls = []
    state = {"mode": "auth"}

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if state["mode"] == "auth":
                raise FakeAuthError("Invalid credentials")
            elif state["mode"] == "credits":
                raise FakeRateLimit("insufficient credits / payment required")
            elif state["mode"] == "forbidden":
                raise FakeAPIError(403, "Model access forbidden")
            elif state["mode"] == "not_found":
                raise FakeAPIError(404, "Model not found")
            elif state["mode"] == "transient":
                if len(calls) == 1:
                    raise FakeRateLimit("rate limit exceeded, please slow down")
                return SimpleNamespace(
                    model="meta-llama/llama-3.3-70b-instruct",
                    choices=[SimpleNamespace(message=SimpleNamespace(content="recovered"), finish_reason="stop")],
                    usage=None
                )
            elif state["mode"] == "blocked":
                return SimpleNamespace(
                    model="meta-llama/llama-3.3-70b-instruct",
                    choices=[SimpleNamespace(message=SimpleNamespace(content="blocked"), finish_reason="content_filter")],
                    usage=None
                )
            elif state["mode"] == "empty":
                return SimpleNamespace(
                    model="meta-llama/llama-3.3-70b-instruct",
                    choices=[SimpleNamespace(message=SimpleNamespace(content="   "), finish_reason="stop")],
                    usage=None
                )

    fake_openai_mod = SimpleNamespace(
        OpenAI=lambda api_key, base_url: SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions())),
        APIError=FakeAPIError,
        RateLimitError=FakeRateLimit,
        AuthenticationError=FakeAuthError,
    )
    monkeypatch.setitem(sys.modules, "openai", fake_openai_mod)

    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "valid-key")
    waits = []
    monkeypatch.setattr(providers.time, "sleep", waits.append)

    # 1. 401 Authentication
    with pytest.raises(providers.ProviderError, match="authentication failed \\(401\\)"):
        providers.chat("p", "s")

    # 2. 402 Insufficient credits
    state["mode"] = "credits"
    calls.clear()
    with pytest.raises(providers.ProviderError, match="insufficient credits \\(402\\)"):
        providers.chat("p", "s")

    # 3. 403 Forbidden
    state["mode"] = "forbidden"
    calls.clear()
    with pytest.raises(providers.ProviderError, match="forbidden / model access denied \\(403\\)"):
        providers.chat("p", "s")

    # 4. 404 Model Not Found
    state["mode"] = "not_found"
    calls.clear()
    with pytest.raises(providers.ProviderError, match="model not found \\(404\\)"):
        providers.chat("p", "s")

    # 5. Blocked finish reason
    state["mode"] = "blocked"
    calls.clear()
    with pytest.raises(providers.ProviderError, match="blocked with finish reason: content_filter"):
        providers.chat("p", "s")

    # 6. Empty response
    state["mode"] = "empty"
    calls.clear()
    with pytest.raises(providers.ProviderError, match="empty response"):
        providers.chat("p", "s")

    # 7. Transient 429 recovers
    state["mode"] = "transient"
    calls.clear()
    res = providers.chat("p", "s")
    assert res == "recovered"
    assert len(calls) == 2
    assert waits == [2]


def test_gemini_chat_success_and_model_forwarding(monkeypatch):
    calls = []

    class FakeModels:
        def generate_content(self, model, contents, config):
            calls.append({"model": model, "contents": contents, "config": config})
            return SimpleNamespace(
                text="  gemini generated text  ",
                candidates=[SimpleNamespace(finish_reason="STOP")]
            )

    class FakeClient:
        def __init__(self, api_key):
            calls.append({"api_key": api_key})
            self.models = FakeModels()

    fake_genai = SimpleNamespace(
        Client=FakeClient,
        types=SimpleNamespace(GenerateContentConfig=lambda **kw: kw),
        errors=SimpleNamespace(APIError=type("APIError", (Exception,), {}))
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_genai.types)
    monkeypatch.setitem(sys.modules, "google.genai.errors", fake_genai.errors)

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "valid-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")

    out = providers.chat("prompt", "system", model="custom-gemini-model", max_tokens=256)
    assert out == "gemini generated text"
    assert calls[0]["api_key"] == "valid-test-key"
    assert calls[1]["model"] == "custom-gemini-model"
    assert calls[1]["contents"] == "prompt"
    assert calls[1]["config"]["system_instruction"] == "system"
    assert calls[1]["config"]["max_output_tokens"] == 256

    # Test that a legacy Llama model name routes to GEMINI_MODEL
    calls.clear()
    out = providers.chat("prompt2", "system2", model="llama-3.3-70b-versatile")
    assert out == "gemini generated text"
    assert calls[1]["model"] == "gemini-2.5-flash"


def test_gemini_blocked_or_empty_response(monkeypatch):
    class BlockedModels:
        def __init__(self, blocked=True, empty=False):
            self.blocked = blocked
            self.empty = empty
        def generate_content(self, model, contents, config):
            if self.empty:
                return SimpleNamespace(text="", candidates=[SimpleNamespace(finish_reason="STOP")])
            return SimpleNamespace(text="", candidates=[SimpleNamespace(finish_reason="SAFETY")])

    fake_genai = SimpleNamespace(
        Client=lambda api_key: SimpleNamespace(models=BlockedModels(blocked=True)),
        types=SimpleNamespace(GenerateContentConfig=lambda **kw: kw),
        errors=SimpleNamespace(APIError=type("APIError", (Exception,), {}))
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_genai.types)
    monkeypatch.setitem(sys.modules, "google.genai.errors", fake_genai.errors)

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "valid-test-key")

    with pytest.raises(providers.ProviderError, match="blocked or truncated"):
        providers.chat("prompt", "system")

    # Empty response test
    fake_genai.Client = lambda api_key: SimpleNamespace(models=BlockedModels(blocked=False, empty=True))
    with pytest.raises(providers.ProviderError, match="empty response"):
        providers.chat("prompt", "system")


def test_gemini_retries_transient_errors(monkeypatch):
    class FakeAPIError(Exception):
        def __init__(self, code, message):
            self.code = code
            self.message = message

    calls = []
    class RetryModels:
        def generate_content(self, model, contents, config):
            calls.append(1)
            if len(calls) == 1:
                raise FakeAPIError(429, "Resource exhausted")
            return SimpleNamespace(text="recovered", candidates=[SimpleNamespace(finish_reason="STOP")])

    fake_genai = SimpleNamespace(
        Client=lambda api_key: SimpleNamespace(models=RetryModels()),
        types=SimpleNamespace(GenerateContentConfig=lambda **kw: kw),
        errors=SimpleNamespace(APIError=FakeAPIError)
    )
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_genai.types)
    monkeypatch.setitem(sys.modules, "google.genai.errors", fake_genai.errors)

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "valid-test-key")
    waits = []
    monkeypatch.setattr(providers.time, "sleep", waits.append)

    res = providers.chat("prompt", "system")
    assert res == "recovered"
    assert waits == [5]
    assert len(calls) == 2


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
