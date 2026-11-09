import json

import pytest

from backend.agents.audit import AuditTrail, read_jsonl
from backend.review import records as R

ESC = "E2:escalation:ED_btg_B_meds"
FIND = "E1:finding:DEMO-INT-002"
REASON = "Patient is unconscious and the interaction risk outweighs the opt-out."


@pytest.fixture
def run_dir(tmp_path):
    d = tmp_path / "20260101-000000-live"
    d.mkdir()
    run = {"events": [
        {"seq": 1, "escalations": [], "safety": {"findings": [
            {"finding_id": "DEMO-INT-002", "title": "A + B", "severity": "high"},
            {"finding_id": "MISSING:x", "title": "Missing", "severity": "informational"}]}},
        {"seq": 2, "escalations": [{"label": "ED_btg_B_meds", "reason": "blocked by opt-out", "basis": "9.7"}],
         "safety": {"findings": []}}]}
    (d / "run.json").write_text(json.dumps(run), encoding="utf-8")
    t = AuditTrail()
    t.add("event_arrived", "orchestrator", 1, "t", "E1")
    t.add("escalation_to_human", "orchestrator", 2, "t", "needs human")
    t.write_jsonl(d / "audit.jsonl")
    return d


def rec(d, item=ESC, decision="override", reviewer="Dr A", role="clinician", reason=REASON):
    return R.record(d, item, decision, reviewer, role, reason)


def test_items_are_escalations_and_severe_findings_only(run_dir):
    run = json.loads((run_dir / "run.json").read_text())
    ids = {i["item_id"] for i in R.items(run)}
    assert ids == {ESC, FIND}  # informational finding is not offered


def test_record_and_verify(run_dir):
    e = rec(run_dir)
    assert e["decision"] == "override" and e["supersedes"] is None and "record only" in e["effect"]
    assert R.check(run_dir)["status"] == "ok"


def test_no_reviews_is_pending_not_ok(run_dir):
    assert R.check(run_dir)["status"] == "none"
    run = json.loads((run_dir / "run.json").read_text())
    assert all(v is None for v in R.status_by_item(run, []).values())


@pytest.mark.parametrize("kw", [{"decision": "approve"}, {"item": "E9:nope"}, {"reviewer": " "}, {"role": ""},
                                {"reason": "too short"}])
def test_invalid_input_is_refused(run_dir, kw):
    args = dict(item=ESC, decision="uphold", reviewer="Dr A", role="clinician", reason=REASON)
    args.update(kw)
    with pytest.raises(R.ReviewError):
        rec(run_dir, args["item"], args["decision"], args["reviewer"], args["role"], args["reason"])
    assert not (run_dir / "reviews.jsonl").exists()


def test_later_decision_supersedes_but_history_is_kept(run_dir):
    rec(run_dir, decision="defer")
    e2 = rec(run_dir, decision="override")
    assert e2["supersedes"] == 1
    assert len(read_jsonl(run_dir / "reviews.jsonl")) == 2
    run = json.loads((run_dir / "run.json").read_text())
    assert R.status_by_item(run, R.read_reviews(run_dir))[ESC]["decision"] == "override"
    assert R.check(run_dir)["status"] == "ok"


def test_edited_review_is_detected(run_dir):
    rec(run_dir)
    rec(run_dir, item=FIND, decision="uphold")
    lines = read_jsonl(run_dir / "reviews.jsonl")
    lines[0]["reason"] = "rewritten after the fact"
    (run_dir / "reviews.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n", encoding="utf-8")
    assert R.check(run_dir)["status"] == "broken"
    with pytest.raises(R.ReviewError):
        rec(run_dir, decision="uphold")  # refuses to extend a broken chain


def test_review_is_bound_to_the_audit_it_was_made_against(run_dir):
    rec(run_dir)
    audit = read_jsonl(run_dir / "audit.jsonl")
    audit[0]["summary"] = "edited"
    (run_dir / "audit.jsonl").write_text("\n".join(json.dumps(a) for a in audit) + "\n", encoding="utf-8")
    assert R.check(run_dir)["status"] == "audit_broken"


def test_refuses_unsealed_audit(run_dir):
    audit = read_jsonl(run_dir / "audit.jsonl")
    for a in audit:
        a.pop("hash"); a.pop("prev_hash")
    (run_dir / "audit.jsonl").write_text("\n".join(json.dumps(a) for a in audit) + "\n", encoding="utf-8")
    with pytest.raises(R.ReviewError):
        rec(run_dir)


def test_cli_roundtrip(run_dir, capsys):
    assert R.main(["list", "--run", str(run_dir)]) == 0
    assert "PENDING" in capsys.readouterr().out
    assert R.main(["record", "--run", str(run_dir), "--item", ESC, "--decision", "uphold", "--reviewer", "Dr A",
                   "--role", "clinician", "--reason", REASON]) == 0
    assert R.main(["record", "--run", str(run_dir), "--item", ESC, "--decision", "uphold", "--reviewer", "Dr A",
                   "--role", "clinician", "--reason", "short"]) == 2
    assert R.main(["show", "--run", str(run_dir)]) == 0
    assert "REVIEWED: uphold" in (R.main(["list", "--run", str(run_dir)]) or capsys.readouterr().out)
