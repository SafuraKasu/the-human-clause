"""Scenario tests: the deterministic parts must meet the expectations written beforehand,
and every policy citation the scenario expects must exist in the ingested KB."""
import re
from datetime import datetime

import pytest

from backend.kb.retrieve import KnowledgeBase
from backend.scenario import fatima
from backend.scenario.state import ScenarioState


@pytest.fixture(scope="module")
def replay():
    """Apply events in order; return {seq: outputs}."""
    state = ScenarioState()
    return state, {e.seq: state.apply(e) for e in fatima.EVENTS}


def norm(s):
    return re.sub(r"\s+", " ", s).lower()


def test_events_are_ordered_and_complete():
    assert [e.seq for e in fatima.EVENTS] == list(range(1, 7))
    times = [datetime.fromisoformat(e.at) for e in fatima.EVENTS]
    assert times == sorted(times)
    for e in fatima.EVENTS:
        assert e.expected and e.narrative and e.title
        assert set(e.expected) >= {"safety", "consent", "policy", "gaps", "audit"}


def test_gap_ids_referenced_by_events_are_defined():
    for e in fatima.EVENTS:
        for g in e.expected["gaps"]:
            assert g in fatima.GAP_HYPOTHESES


@pytest.mark.parametrize("event", fatima.EVENTS, ids=lambda e: f"event{e.seq}")
def test_safety_outcomes_match_expectations(replay, event):
    _, out = replay
    findings = out[event.seq]["assessment"].findings
    ids = {f.finding_id for f in findings}
    exp = event.expected["safety"]
    for fid in exp.get("present", []):
        assert fid in ids, f"event {event.seq}: expected {fid}, got {sorted(ids)}"
    for fid in exp.get("absent", []):
        assert fid not in ids, f"event {event.seq}: {fid} should not be present"
    for fid, sev in exp.get("severity", {}).items():
        assert next(f for f in findings if f.finding_id == fid).severity == sev
    for cat in exp.get("no_category", []):
        assert not [f for f in findings if f.category == cat]


@pytest.mark.parametrize("event", fatima.EVENTS, ids=lambda e: f"event{e.seq}")
def test_consent_outcomes_match_expectations(replay, event):
    _, out = replay
    for label, exp in event.expected["consent"].items():
        d = out[event.seq]["consent"][label]
        assert d.allowed == exp["allowed"] and d.reason_code == exp["reason_code"], (label, d)
        if "escalate" in exp:
            assert d.escalate == exp["escalate"]


def test_limitations_appear_only_after_withdrawal(replay):
    _, out = replay
    for seq in (1, 2, 3):
        assert out[seq]["limitations"] == []
    for seq in (4, 5, 6):
        assert any("HospitalB" in x and "incomplete" in x for x in out[seq]["limitations"])


def test_agents_only_see_data_that_has_arrived(replay):
    _, out = replay
    meds_at = {s: set(out[s]["assessment"].medications_considered) for s in out}
    assert "Aldactone" not in meds_at[1] and "Aldactone" in meds_at[2] and "Aldactone" in meds_at[3]
    assert "Aldactone" not in meds_at[4]  # withdrawn by the patient


def test_uncertainty_then_resolution_is_visible(replay):
    _, out = replay
    uncertain = lambda seq: {f.finding_id for f in out[seq]["assessment"].findings if f.certainty == "uncertain"}
    assert uncertain(2) >= {"MISSING:DEMO-LAB-001:glucophage", "MISSING:DEMO-LAB-002:aldactone"}
    assert not uncertain(3)


def test_audit_kinds_expected_by_events_appear_in_log(replay):
    state, _ = replay
    kinds = {e["kind"] for e in state.registry.log}
    for e in fatima.EVENTS:
        assert set(e.expected["audit"]) <= kinds


def test_emergency_request_is_logged_with_justification_and_blocked(replay):
    state, _ = replay
    entry = [e for e in state.registry.log if e["kind"] == "access_decision" and e["emergency_requested"]][-1]
    assert entry["allowed"] is False and entry["escalate"] and "warfarin" in entry["justification"]


def test_expected_policy_citations_exist_in_kb():
    kb = KnowledgeBase()
    for e in fatima.EVENTS:
        for doc_id, phrase in e.expected["policy"]["must_cite"]:
            hits = [c for c in kb.chunks if c["doc_id"] == doc_id and norm(phrase) in norm(c["text"])]
            assert hits, f"event {e.seq}: phrase {phrase!r} not found in {doc_id}"
