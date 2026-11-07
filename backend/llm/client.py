"""LLM client: the only place that talks to the model provider.

Handles structured output, tool calls, retry with backoff, fallback model, on-disk caching of
live responses (replayable offline), a mock mode for tests, and an audit callback for every call.
Standard library only; works with any OpenAI-compatible endpoint (see backend/config.py).

    client = LLMClient.from_env()
    r = client.complete([{"role": "user", "content": "..."}], json_mode=True, agent="safety")
    r.parsed, r.model, r.cached
"""
import hashlib
import json
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from backend import config

RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}


class LLMError(Exception):
    """Non-recoverable failure (bad request, auth, invalid output after retries)."""


class LLMUnavailable(LLMError):
    """Provider unreachable or overloaded on every model tried."""


class MockMiss(LLMError):
    """Mock mode had no scripted or cached response for this request."""


@dataclass
class LLMResponse:
    content: str
    parsed: Any = None
    tool_calls: list[dict] = field(default_factory=list)
    raw_tool_calls: list[dict] = field(default_factory=list)  # provider format, replayed verbatim in tool loops
    model: str = ""
    mode: str = "live"
    cached: bool = False
    attempts: int = 1
    latency_s: float = 0.0
    usage: dict = field(default_factory=dict)

    def as_message(self) -> dict:
        """This reply as an assistant message, for continuing a tool-calling conversation."""
        return {"role": "assistant", "content": self.content or None, "tool_calls": self.raw_tool_calls}


def _http_transport(base_url: str, key: str, payload: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _strip_fences(text: str) -> str:
    m = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", text, re.S)
    return m.group(1) if m else text.strip()


class LLMClient:
    def __init__(self, *, mode: str = "live", base_url: str = "", api_key: str = "", model: str = "",
                 fallback_model: str = "", cache_dir: Path | str | None = None,
                 mock_responses: "Callable[[dict], str | dict] | list | None" = None,
                 on_call: Callable[[dict], None] | None = None, retries: int = 3, backoff_s: float = 2.0,
                 timeout_s: float = 60.0, transport: Callable | None = None, sleep: Callable = time.sleep):
        self.mode, self.base_url, self.api_key = mode, base_url, api_key
        self.model, self.fallback_model = model, fallback_model
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.mock_responses = list(mock_responses) if isinstance(mock_responses, list) else mock_responses
        self.on_call, self.retries, self.backoff_s, self.timeout_s = on_call, retries, backoff_s, timeout_s
        self.transport = transport or (lambda b, k, p: _http_transport(b, k, p, timeout_s))
        self.sleep = sleep

    @classmethod
    def from_env(cls, **overrides) -> "LLMClient":
        config.load_dotenv()
        provider = config.PROVIDER_ALIASES.get(config.env("LLM_PROVIDER").lower(), config.env("LLM_PROVIDER").lower())
        kw = dict(
            mode=config.env("LLM_MODE", "mock").lower(),
            base_url=config.env("LLM_BASE_URL") or config.BASE_URLS.get(provider, ""),
            api_key=config.env("LLM_API_KEY") or ("none" if provider == "ollama" else ""),
            model=config.env("LLM_MODEL"), fallback_model=config.env("LLM_FALLBACK_MODEL"),
            cache_dir=config.env("LLM_CACHE_DIR") or config.ROOT / "data" / "llm_cache")
        kw.update(overrides)
        return cls(**kw)

    # ---- public API ----------------------------------------------------------------------
    def complete(self, messages: list[dict], *, json_mode: bool = False, tools: list[dict] | None = None,
                 temperature: float = 0.0, agent: str = "", validate: Callable[[Any], Any] | None = None,
                 use_cache: bool = True) -> LLMResponse:
        """Run one completion. `validate` may raise to reject parsed JSON (e.g. a Pydantic model)."""
        t0 = time.time()
        request = {"messages": messages, "json_mode": json_mode, "tools": tools, "temperature": temperature}
        if self.mode == "mock":
            resp = self._mock(request)
        else:
            resp = self._live(request, use_cache)
        if json_mode and not tools:
            resp = self._ensure_json(resp, request, validate, use_cache)
        resp.latency_s = round(time.time() - t0, 3)
        self._audit(agent, request, resp)
        return resp

    # ---- mock ----------------------------------------------------------------------------
    def _mock(self, request: dict) -> LLMResponse:
        scripted = self.mock_responses
        out = None
        if callable(scripted):
            out = scripted(request)
        elif scripted:
            out = scripted.pop(0)
        if out is None:
            cached = self._cache_read(self._key(request))
            if cached:
                resp = self._from_raw(cached["raw"], cached["model"])
                resp.mode, resp.cached = "mock", True
                return resp
            raise MockMiss("No scripted or cached response for this request in mock mode.")
        if isinstance(out, dict) and "tool_calls" in out:
            raw = [{"id": c.get("id", f"mock{i}"), "type": "function",
                    "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
                   for i, c in enumerate(out["tool_calls"])]
            calls = [{"id": r["id"], "name": r["function"]["name"], "arguments": c["arguments"]}
                     for r, c in zip(raw, out["tool_calls"])]
            return LLMResponse(content=out.get("content", ""), tool_calls=calls, raw_tool_calls=raw,
                               model="mock", mode="mock")
        text = out if isinstance(out, str) else json.dumps(out)
        return LLMResponse(content=text, model="mock", mode="mock")

    # ---- live ----------------------------------------------------------------------------
    def _live(self, request: dict, use_cache: bool) -> LLMResponse:
        if not (self.base_url and self.api_key and self.model):
            raise LLMError("LLM not configured: set LLM_PROVIDER, LLM_API_KEY and LLM_MODEL in .env")
        key = self._key(request)
        if use_cache:
            cached = self._cache_read(key)
            if cached:
                resp = self._from_raw(cached["raw"], cached["model"])
                resp.cached = True
                return resp
        raw, model, attempts = self._call_with_fallback(request)
        resp = self._from_raw(raw, model)
        resp.attempts = attempts
        return resp

    def _payload(self, request: dict, model: str) -> dict:
        p = {"model": model, "messages": request["messages"], "temperature": request["temperature"]}
        if request["tools"]:
            p["tools"], p["tool_choice"] = request["tools"], "auto"
        elif request["json_mode"]:
            p["response_format"] = {"type": "json_object"}
        return p

    def _call_with_fallback(self, request: dict) -> tuple[dict, str, int]:
        models = [m for m in (self.model, self.fallback_model) if m]
        attempts, last = 0, None
        for model in models:
            for i in range(self.retries):
                attempts += 1
                try:
                    return self.transport(self.base_url, self.api_key, self._payload(request, model)), model, attempts
                except urllib.error.HTTPError as e:
                    body = e.read().decode(errors="replace")[:300]
                    last = f"HTTP {e.code} from {model}: {body}"
                    if e.code == 404 or (e.code == 429 and "quota" in body.lower()):
                        break  # model gone, or its (daily) quota is spent: retrying is pointless, use the fallback
                    if e.code not in RETRYABLE_HTTP:
                        raise LLMError(last) from e
                except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as e:
                    last = f"{type(e).__name__} from {model}: {e}"
                if i < self.retries - 1:
                    self.sleep(self.backoff_s * (2 ** i))
        raise LLMUnavailable(f"All models failed after {attempts} attempt(s). Last error: {last}")

    def _from_raw(self, raw: dict, model: str) -> LLMResponse:
        msg = raw["choices"][0]["message"]
        calls = []
        for c in msg.get("tool_calls") or []:
            try:
                args = json.loads(c["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {"_raw": c["function"]["arguments"]}
            calls.append({"id": c.get("id", ""), "name": c["function"]["name"], "arguments": args})
        return LLMResponse(content=msg.get("content") or "", tool_calls=calls,
                           raw_tool_calls=list(msg.get("tool_calls") or []), model=model,
                           usage=raw.get("usage", {}))

    # ---- JSON handling -------------------------------------------------------------------
    def _ensure_json(self, resp: LLMResponse, request: dict, validate, use_cache: bool) -> LLMResponse:
        for attempt in range(2):
            try:
                resp.parsed = json.loads(_strip_fences(resp.content))
                if validate:
                    resp.parsed = validate(resp.parsed)
                return resp
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                if attempt == 1 or self.mode == "mock":
                    raise LLMError(f"Model output was not valid JSON for the schema: {e}") from e
                retry_req = {**request, "messages": request["messages"] + [
                    {"role": "assistant", "content": resp.content},
                    {"role": "user", "content": f"That was invalid ({e}). Reply with ONLY valid JSON, no prose."}]}
                resp = self._live(retry_req, use_cache=False)
        return resp  # unreachable

    # ---- cache ---------------------------------------------------------------------------
    def _key(self, request: dict) -> str:
        blob = json.dumps({"model": self.model, **request}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode()).hexdigest()[:32]

    def _cache_read(self, key: str):
        if not self.cache_dir:
            return None
        f = self.cache_dir / f"{key}.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    def _cache_write(self, key: str, raw: dict, model: str, request: dict) -> None:
        if not self.cache_dir:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / f"{key}.json").write_text(
            json.dumps({"model": model, "request": request, "raw": raw, "cached_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                       indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- audit ---------------------------------------------------------------------------
    def _audit(self, agent: str, request: dict, resp: LLMResponse) -> None:
        # Persist real (non-cached, non-mock) responses so the run can be replayed offline.
        if resp.mode == "live" and not resp.cached and self.cache_dir:
            raw = {"choices": [{"message": {"content": resp.content, "tool_calls": resp.raw_tool_calls or None}}],
                   "usage": resp.usage}
            self._cache_write(self._key(request), raw, resp.model, request)
        if self.on_call:
            self.on_call({"agent": agent, "mode": resp.mode, "model": resp.model, "cached": resp.cached,
                          "attempts": resp.attempts, "latency_s": resp.latency_s, "usage": resp.usage,
                          "request": request, "response": {"content": resp.content, "tool_calls": resp.tool_calls}})
