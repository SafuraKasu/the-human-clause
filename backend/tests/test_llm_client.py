"""LLM client tests with a fake transport (no network, no real sleeping)."""
import io
import json
import urllib.error

import pytest

from backend.llm.client import LLMClient, LLMError, LLMUnavailable, MockMiss


def ok(content="", tool_calls=None):
    msg = {"content": content}
    if tool_calls:
        msg["tool_calls"] = [{"id": "c1", "function": {"name": n, "arguments": json.dumps(a)}} for n, a in tool_calls]
    return {"choices": [{"message": msg}], "usage": {"total_tokens": 7}}


def http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(b'{"error":"boom"}'))


class FakeTransport:
    """Replays a list of results; Exceptions are raised, dicts returned. Records (model) per call."""
    def __init__(self, results):
        self.results, self.models = list(results), []

    def __call__(self, base_url, key, payload):
        self.models.append(payload["model"])
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def make(results, **kw):
    t = FakeTransport(results)
    c = LLMClient(mode="live", base_url="http://x", api_key="k", model="main", fallback_model="backup",
                  transport=t, sleep=lambda s: None, **kw)
    return c, t


MSG = [{"role": "user", "content": "hi"}]


def test_json_mode_parses_and_strips_code_fences():
    c, _ = make([ok('```json\n{"a": 1}\n```')])
    assert c.complete(MSG, json_mode=True).parsed == {"a": 1}


def test_invalid_json_gets_one_repair_retry():
    c, t = make([ok("not json"), ok('{"a": 2}')])
    r = c.complete(MSG, json_mode=True)
    assert r.parsed == {"a": 2} and len(t.models) == 2


def test_invalid_json_twice_raises():
    c, _ = make([ok("nope"), ok("still nope")])
    with pytest.raises(LLMError):
        c.complete(MSG, json_mode=True)


def test_validate_callback_can_reject():
    def need_key(d):
        if "severity" not in d:
            raise ValueError("missing severity")
        return d
    c, _ = make([ok('{"x": 1}'), ok('{"severity": "high"}')])
    assert c.complete(MSG, json_mode=True, validate=need_key).parsed == {"severity": "high"}


def test_retries_transient_errors_then_succeeds():
    c, t = make([http_error(503), TimeoutError("slow"), ok("fine")])
    r = c.complete(MSG)
    assert r.content == "fine" and r.attempts == 3 and t.models == ["main"] * 3 and r.model == "main"


def test_falls_back_to_backup_model_after_retries_exhausted():
    c, t = make([http_error(503)] * 3 + [ok("from backup")])
    r = c.complete(MSG)
    assert r.model == "backup" and r.content == "from backup" and t.models[-1] == "backup"


def test_404_model_gone_goes_straight_to_fallback():
    c, t = make([http_error(404), ok("backup ok")])
    assert c.complete(MSG).model == "backup" and t.models == ["main", "backup"]


def test_non_retryable_error_raises_immediately():
    c, t = make([http_error(401)])
    with pytest.raises(LLMError) as e:
        c.complete(MSG)
    assert "401" in str(e.value) and len(t.models) == 1


def test_all_models_failing_raises_unavailable():
    c, _ = make([http_error(503)] * 6)
    with pytest.raises(LLMUnavailable):
        c.complete(MSG)


def test_tool_calls_are_parsed():
    c, _ = make([ok("", [("search_policy", {"query": "consent"})])])
    r = c.complete(MSG, tools=[{"type": "function", "function": {"name": "search_policy"}}])
    assert r.tool_calls == [{"id": "c1", "name": "search_policy", "arguments": {"query": "consent"}}]


def test_live_responses_are_cached_and_replayed_without_network(tmp_path):
    c, t = make([ok('{"a": 1}')], cache_dir=tmp_path)
    first = c.complete(MSG, json_mode=True)
    assert not first.cached and list(tmp_path.glob("*.json"))
    c2, t2 = make([], cache_dir=tmp_path)  # transport would raise IndexError if called
    second = c2.complete(MSG, json_mode=True)
    assert second.cached and second.parsed == {"a": 1} and t2.models == []


def test_cached_tool_calls_round_trip(tmp_path):
    c, _ = make([ok("", [("search_policy", {"query": "q"})])], cache_dir=tmp_path)
    c.complete(MSG, tools=[{"type": "function"}])
    c2, _ = make([], cache_dir=tmp_path)
    assert c2.complete(MSG, tools=[{"type": "function"}]).tool_calls[0]["arguments"] == {"query": "q"}


def test_mock_mode_scripted_and_no_network():
    c = LLMClient(mode="mock", mock_responses=[{"severity": "low"}, "plain text"])
    assert c.complete(MSG, json_mode=True).parsed == {"severity": "low"}
    r = c.complete(MSG)
    assert r.content == "plain text" and r.mode == "mock"


def test_mock_mode_callable_and_miss(tmp_path):
    c = LLMClient(mode="mock", mock_responses=lambda req: {"echo": req["messages"][0]["content"]})
    assert c.complete(MSG, json_mode=True).parsed == {"echo": "hi"}
    with pytest.raises(MockMiss):
        LLMClient(mode="mock", cache_dir=tmp_path).complete(MSG)


def test_mock_mode_replays_cache_from_a_live_run(tmp_path):
    live, _ = make([ok("recorded")], cache_dir=tmp_path)
    live.complete(MSG)
    mock = LLMClient(mode="mock", cache_dir=tmp_path, model="main")
    r = mock.complete(MSG)
    assert r.content == "recorded" and r.mode == "mock" and r.cached


def test_audit_callback_receives_each_call():
    seen = []
    c, _ = make([ok("a"), http_error(503), ok("b")], on_call=seen.append)
    c.complete(MSG, agent="safety")
    c.complete(MSG, agent="policy")
    assert [s["agent"] for s in seen] == ["safety", "policy"]
    assert seen[1]["attempts"] == 2 and seen[0]["request"]["messages"] == MSG


def test_unconfigured_live_client_gives_clear_error():
    with pytest.raises(LLMError, match="not configured"):
        LLMClient(mode="live").complete(MSG)
