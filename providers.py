"""Generation providers. Retrieval, prompts, and evaluation remain unchanged."""
from collections.abc import Callable
import logging
import os
import time
from urllib.parse import urlsplit

log = logging.getLogger(__name__)
OPENROUTER_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"
OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_DEFAULT_MODEL = "llama3.1:8b"


class ProviderError(RuntimeError):
    """A configured generation service could not return a usable answer."""


def selected_provider() -> str:
    name = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    if name not in {"openrouter", "gemini", "groq", "ollama"}:
        raise ValueError(f"Unsupported LLM_PROVIDER: {name!r}")
    return name


def chat(prompt: str, system: str, model: str | None = None,
         max_tokens: int = 1024, retries: int = 2, on_trace: Callable | None = None) -> str:
    provider = selected_provider()

    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if not key or not key.strip() or key.startswith("PASTE_YOUR_") or key.startswith("your_"):
            raise EnvironmentError("OPENROUTER_API_KEY not found or not configured. Add it to your .env file.")

        from openai import OpenAI, APIError, RateLimitError, AuthenticationError

        base_url = os.getenv("OPENROUTER_BASE_URL", OPENROUTER_DEFAULT_BASE_URL).strip()
        client = OpenAI(api_key=key.strip(), base_url=base_url)

        configured_model = (os.getenv("OPENROUTER_MODEL") or "").strip() or OPENROUTER_DEFAULT_MODEL
        target_model = (model or "").strip() or configured_model
        if any(legacy in target_model.lower() for legacy in ["gemini-", "llama-3.3-70b-versatile"]):
            target_model = configured_model

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]

        for attempt in range(1, retries + 2):
            t0 = time.perf_counter()
            try:
                response = client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=max_tokens,
                )
                latency = time.perf_counter() - t0
                if not response.choices:
                    raise ProviderError("OpenRouter returned no choices")
                choice = response.choices[0]
                finish_reason = getattr(choice, "finish_reason", None)
                if finish_reason in {"content_filter", "error"}:
                    raise ProviderError(f"OpenRouter generation blocked with finish reason: {finish_reason}")
                content = choice.message.content
                if content is None or not content.strip():
                    raise ProviderError("OpenRouter returned an empty response")
                text = content.strip()

                if on_trace:
                    usage_dict = {}
                    cost = None
                    if hasattr(response, "usage") and response.usage:
                        u = response.usage
                        usage_dict = {
                            "prompt_tokens": getattr(u, "prompt_tokens", None),
                            "completion_tokens": getattr(u, "completion_tokens", None),
                            "total_tokens": getattr(u, "total_tokens", None),
                        }
                        cost = getattr(u, "cost", None)
                    on_trace("provider_call", {
                        "provider": "openrouter",
                        "model": target_model,
                        "model_returned": getattr(response, "model", target_model),
                        "prompt": prompt,
                        "system": system,
                        "max_tokens": max_tokens,
                        "output": text,
                        "finish_reason": finish_reason,
                        "usage": usage_dict,
                        "cost": cost,
                        "latency_seconds": round(latency, 3),
                    })
                return text

            except AuthenticationError as exc:
                if on_trace:
                    on_trace("provider_call", {
                        "provider": "openrouter",
                        "model": target_model,
                        "prompt": prompt,
                        "system": system,
                        "max_tokens": max_tokens,
                        "error": "AuthenticationError",
                        "error_message": str(exc),
                        "latency_seconds": round(time.perf_counter() - t0, 3)
                    })
                raise ProviderError(f"OpenRouter authentication failed (401): {exc}") from exc
            except RateLimitError as exc:
                err_msg = str(exc)
                if "credit" in err_msg.lower() or "payment" in err_msg.lower():
                    if on_trace:
                        on_trace("provider_call", {
                            "provider": "openrouter", "model": target_model, "prompt": prompt,
                            "system": system, "max_tokens": max_tokens, "error": "InsufficientCredits",
                            "error_message": err_msg, "latency_seconds": round(time.perf_counter() - t0, 3)
                        })
                    raise ProviderError(f"OpenRouter payment required / insufficient credits (402): {err_msg}") from exc
                if attempt <= retries:
                    wait = 2 * attempt
                    log.warning("OpenRouter rate limit hit (%s). Retrying in %ds...", err_msg, wait)
                    time.sleep(wait)
                    continue
                if on_trace:
                    on_trace("provider_call", {
                        "provider": "openrouter", "model": target_model, "prompt": prompt,
                        "system": system, "max_tokens": max_tokens, "error": "RateLimitError",
                        "error_message": err_msg, "latency_seconds": round(time.perf_counter() - t0, 3)
                    })
                raise ProviderError(f"OpenRouter rate limit / quota exceeded (429): {err_msg}") from exc
            except APIError as exc:
                code = getattr(exc, "code", getattr(exc, "status_code", None))
                err_msg = getattr(exc, "message", str(exc))
                if code == 401:
                    if on_trace:
                        on_trace("provider_call", {"provider": "openrouter", "model": target_model, "prompt": prompt, "system": system, "max_tokens": max_tokens, "error": "AuthenticationError", "error_message": err_msg, "latency_seconds": round(time.perf_counter() - t0, 3)})
                    raise ProviderError(f"OpenRouter authentication failed (401): {err_msg}") from exc
                elif code == 402 or "credit" in err_msg.lower() or "payment" in err_msg.lower():
                    if on_trace:
                        on_trace("provider_call", {"provider": "openrouter", "model": target_model, "prompt": prompt, "system": system, "max_tokens": max_tokens, "error": "InsufficientCredits", "error_message": err_msg, "latency_seconds": round(time.perf_counter() - t0, 3)})
                    raise ProviderError(f"OpenRouter payment required / insufficient credits (402): {err_msg}") from exc
                elif code == 403:
                    if on_trace:
                        on_trace("provider_call", {"provider": "openrouter", "model": target_model, "prompt": prompt, "system": system, "max_tokens": max_tokens, "error": "Forbidden", "error_message": err_msg, "latency_seconds": round(time.perf_counter() - t0, 3)})
                    raise ProviderError(f"OpenRouter forbidden / model access denied (403): {err_msg}") from exc
                elif code == 404:
                    if on_trace:
                        on_trace("provider_call", {"provider": "openrouter", "model": target_model, "prompt": prompt, "system": system, "max_tokens": max_tokens, "error": "ModelNotFound", "error_message": err_msg, "latency_seconds": round(time.perf_counter() - t0, 3)})
                    raise ProviderError(f"OpenRouter model not found (404): {err_msg}") from exc
                elif code in (429, 502, 503, 504) and attempt <= retries:
                    wait = 2 * attempt
                    log.warning("OpenRouter transient error (%s). Retrying in %ds...", code, wait)
                    time.sleep(wait)
                    continue
                if on_trace:
                    on_trace("provider_call", {"provider": "openrouter", "model": target_model, "prompt": prompt, "system": system, "max_tokens": max_tokens, "error": f"APIError_{code}", "error_message": err_msg, "latency_seconds": round(time.perf_counter() - t0, 3)})
                raise ProviderError(f"OpenRouter API error ({code}): {err_msg}") from exc
            except ProviderError as exc:
                if on_trace:
                    on_trace("provider_call", {"provider": "openrouter", "model": target_model, "prompt": prompt, "system": system, "max_tokens": max_tokens, "error": "ProviderError", "error_message": str(exc), "latency_seconds": round(time.perf_counter() - t0, 3)})
                raise
            except Exception as exc:
                if on_trace:
                    on_trace("provider_call", {"provider": "openrouter", "model": target_model, "prompt": prompt, "system": system, "max_tokens": max_tokens, "error": type(exc).__name__, "error_message": str(exc), "latency_seconds": round(time.perf_counter() - t0, 3)})
                raise ProviderError(f"OpenRouter request failed: {type(exc).__name__}: {exc}") from exc

    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if not key or not key.strip() or key.startswith("PASTE_YOUR_") or key.startswith("your_"):
            raise EnvironmentError("GEMINI_API_KEY not found or not configured. Add it to your .env file.")

        from google import genai
        from google.genai import types
        from google.genai.errors import APIError

        client = genai.Client(api_key=key.strip())
        target_model = model or os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
        if "llama" in target_model.lower():
            target_model = os.getenv("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)

        config_kwargs = {
            "system_instruction": system,
            "temperature": 0.0,
            "max_output_tokens": max_tokens,
        }
        try:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            config = types.GenerateContentConfig(**config_kwargs)
        except (TypeError, AttributeError):
            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.0,
                max_output_tokens=max_tokens,
            )

        for attempt in range(1, retries + 2):
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config,
                )
                if response.candidates:
                    cand = response.candidates[0]
                    finish_reason = getattr(cand, "finish_reason", None)
                    reason_name = getattr(finish_reason, "name", str(finish_reason)).upper()
                    if finish_reason and reason_name not in {"STOP", "FINISH_REASON_UNSPECIFIED"}:
                        raise ProviderError(f"Gemini generation blocked or truncated with finish reason: {finish_reason}")
                text = (response.text or "").strip()
                if not text:
                    raise ProviderError("Gemini returned an empty response")
                return text
            except APIError as exc:
                code = getattr(exc, "code", None)
                message = getattr(exc, "message", str(exc))
                if code in (429, 503) and attempt <= retries:
                    wait = 5 * attempt
                    log.warning("Gemini transient API error (%s). Retrying in %ds...", code, wait)
                    time.sleep(wait)
                    continue
                raise ProviderError(f"Gemini API error ({code}): {message}") from exc
            except ProviderError:
                raise
            except Exception as exc:
                raise ProviderError(f"Gemini request failed: {type(exc).__name__}: {exc}") from exc

    if provider == "groq":
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise EnvironmentError("GROQ_API_KEY not found. Add it to your .env file.")
        from groq import Groq, RateLimitError
        client = Groq(api_key=key)
        for attempt in range(1, retries + 2):
            try:
                response = client.chat.completions.create(
                    model=model or GROQ_MODEL,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": prompt}],
                    temperature=0, max_tokens=max_tokens)
                return response.choices[0].message.content.strip()
            except RateLimitError:
                if attempt > retries:
                    raise
                wait = 5 * attempt
                log.warning("Rate limit hit. Waiting %ds before retry…", wait)
                time.sleep(wait)

    if provider == "ollama":
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        parsed = urlsplit(base_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.netloc or
                parsed.username or parsed.password or parsed.path not in {"", "/"} or
                parsed.query or parsed.fragment):
            raise ProviderError("OLLAMA_BASE_URL must be a server HTTP(S) URL without credentials or a path")
        url = f"{parsed.scheme}://{parsed.netloc}/api/chat"
        # Existing pipeline call sites explicitly pass the Groq default model name.
        # Map that default to the configured local model while allowing custom names.
        chosen_model = os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL) if model in (None, GROQ_MODEL) else model
        try:
            response = requests.post(url, json={
                "model": chosen_model,
                "stream": False,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": prompt}],
                "options": {"temperature": 0, "num_predict": max_tokens},
            }, timeout=(5, 120))
            response.raise_for_status()
            data = response.json()
            content = data["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("Missing message content")
            return content.strip()
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            raise ProviderError(f"Ollama request failed at {url}: {type(exc).__name__}") from exc

    raise ValueError(f"Unhandled provider: {provider!r}")
