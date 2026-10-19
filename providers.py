"""Generation providers. Retrieval, prompts, and evaluation remain unchanged."""
import logging
import os
import time
from urllib.parse import urlsplit

log = logging.getLogger(__name__)
GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_DEFAULT_MODEL = "llama3.1:8b"


class ProviderError(RuntimeError):
    """A configured generation service could not return a usable answer."""


def selected_provider() -> str:
    name = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    if name not in {"groq", "ollama"}:
        raise ValueError(f"Unsupported LLM_PROVIDER: {name!r}")
    return name


def chat(prompt: str, system: str, model: str | None = None,
         max_tokens: int = 1024, retries: int = 2) -> str:
    if selected_provider() == "groq":
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
