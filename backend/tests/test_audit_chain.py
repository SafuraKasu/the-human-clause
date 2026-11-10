import copy

from backend.agents.audit import AuditTrail, GENESIS, read_jsonl, seal, verify


def _entries(n=5):
    t = AuditTrail()
    for i in range(n):
        t.add("decision", "orchestrator", i, "2026-11-0%dT09:00" % (i + 1), f"step {i}", detail={"k": i})
    return [dict(e) for e in t.entries]


def test_sealed_chain_verifies():
    s = seal(_entries())
    assert s[0]["prev_hash"] == GENESIS
    assert verify(s)["status"] == "ok"


def test_editing_an_entry_is_detected():
    s = seal(_entries())
    s[2]["summary"] = "changed"
    r = verify(s)
    assert r["status"] == "broken" and r["first_bad_seq"] == 3


def test_deleting_inserting_and_reordering_are_detected():
    s = seal(_entries())
    assert verify(s[:2] + s[3:])["status"] == "broken"
    assert verify([s[1], s[0]] + s[2:])["status"] == "broken"
    extra = copy.deepcopy(s[1])
    assert verify(s[:2] + [extra] + s[2:])["status"] == "broken"


def test_truncating_the_tail_is_not_detectable_without_the_head_hash():
    # Documented limitation: the chain proves order and content of what is present, not that nothing was cut off the end.
    s = seal(_entries())
    assert verify(s[:3])["status"] == "ok"


def test_unsealed_file_is_reported_not_passed():
    assert verify(_entries())["status"] == "unsealed"


def test_write_and_read_roundtrip(tmp_path):
    t = AuditTrail()
    t.add("handoff", "orchestrator", 1, "2026-11-02T09:00", "a", nested={"x": [1, 2]})
    t.add("decision", "safety", 1, "2026-11-02T09:00", "b")
    p = tmp_path / "audit.jsonl"
    t.write_jsonl(p)
    assert verify(read_jsonl(p))["status"] == "ok"


def test_truncation_is_caught_when_the_head_hash_is_recorded():
    from backend.agents.audit import head_hash, seal, verify
    sealed = seal([{"seq": i, "x": i} for i in range(1, 6)])
    head = head_hash(sealed)
    assert verify(sealed, expected_head=head)["status"] == "ok"
    assert verify(sealed[:-1], expected_head=head)["status"] == "broken"
