"""Smoke test for a free, OpenAI-compatible LLM provider.

Checks the two things the agents depend on: valid structured JSON output and tool calling.
Standard library only. Configure via environment variables (see .env.example).

    Copy .env.example to .env, fill in LLM_PROVIDER (gemini | groq | openrouter | ollama | custom),
    LLM_API_KEY and LLM_MODEL, then:
    python backend/scripts/llm_smoke_test.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
}


def chat(base_url: str, key: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def test_json(base_url, key, model):
    r = chat(base_url, key, {
        "model": model,
        "messages": [{"role": "user", "content":
            'Return ONLY a JSON object with keys "drug" (string) and "severity" (one of '
            '"low","moderate","high") for a hypothetical interaction. No prose.'}],
        "response_format": {"type": "json_object"},
    })
    obj = json.loads(r["choices"][0]["message"]["content"])
    assert isinstance(obj.get("drug"), str) and obj.get("severity") in ("low", "moderate", "high"), obj
    return obj


def test_tool_call(base_url, key, model):
    r = chat(base_url, key, {
        "model": model,
        "messages": [{"role": "user", "content": "Look up the policy for sharing health data with consent."}],
        "tools": [{"type": "function", "function": {
            "name": "search_policy",
            "description": "Search the policy knowledge base.",
            "parameters": {"type": "object",
                           "properties": {"query": {"type": "string"}},
                           "required": ["query"]}}}],
        "tool_choice": "auto",
    })
    calls = r["choices"][0]["message"].get("tool_calls") or []
    assert calls, "model did not call the tool"
    args = json.loads(calls[0]["function"]["arguments"])
    assert "query" in args, args
    return args


def load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE lines from .env without overriding variables already set."""
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8-sig"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if v.strip():  # values in .env win over stale shell variables
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def env(name: str) -> str:
    return os.environ.get(name, "").strip()


def main() -> int:
    load_dotenv()
    provider = env("LLM_PROVIDER").lower()
    provider = {"google": "gemini", "google-ai-studio": "gemini"}.get(provider, provider)
    key = env("LLM_API_KEY") or ("none" if provider == "ollama" else "")
    model = env("LLM_MODEL")
    base_url = env("LLM_BASE_URL") or BASE_URLS.get(provider, "")
    if not (base_url and key and model):
        missing = [n for n, v in (("LLM_PROVIDER (known: " + ", ".join(BASE_URLS) + ") or LLM_BASE_URL", base_url),
                                  ("LLM_API_KEY", key), ("LLM_MODEL", model)) if not v]
        print(f"Missing or unrecognised: {', '.join(missing)}  (provider seen: {provider!r}, cwd: {os.getcwd()})")
        return 2

    print(f"provider={provider or 'custom'} model={model}")
    failures = 0
    for name, fn in (("structured JSON", test_json), ("tool calling", test_tool_call)):
        t0 = time.time()
        try:
            out = fn(base_url, key, model)
            print(f"PASS  {name} ({time.time() - t0:.1f}s): {out}")
        except urllib.error.HTTPError as e:
            failures += 1
            print(f"FAIL  {name}: HTTP {e.code} {e.read().decode(errors='replace')[:300]}")
        except Exception as e:  # noqa: BLE001 - report any failure mode
            failures += 1
            print(f"FAIL  {name}: {type(e).__name__}: {e}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
