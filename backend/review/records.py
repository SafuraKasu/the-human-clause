"""Human review records: a person accepts or overrides what the system escalated or flagged.

The agents never decide these items; they stop at "a human must decide". This module records the
human's decision, who made it, in what stated role and why, so that the oversight itself is auditable
(DHA AI Policy 4.4.2 overridable by designated end users; 4.2.3 appeals). It is RECORD-ONLY:
a recorded decision does not change consent state or any finding, and nothing is released or acted on.

Reviews live beside the run in `reviews.jsonl`, a hash chain that starts from the head hash of the run's
audit trail. So a review is bound to the exact audit it was made against, and changing the audit breaks it.

    python -m backend.review list   --run data/runs/<dir>
    python -m backend.review record --run data/runs/<dir> --item E5:escalation:ED_btg_B_meds \
        --decision override --reviewer "Dr A" --role clinician --reason "..."
    python -m backend.review show   --run data/runs/<dir>

No authority check is made: who is entitled to decide a cross-emirate conflict is itself an open policy gap
(G2/G3), so the role is recorded as stated, not validated.
"""
import argparse
import json
import time
from pathlib import Path

from backend.agents.audit import head_hash, read_jsonl, seal, verify

DECISIONS = {
    "uphold": "agrees with the system's output or block",
    "override": "disagrees; the human's decision replaces the system's output (also how an appeal is recorded)",
    "defer": "cannot decide; passes it to someone else",
}
MIN_REASON = 15
SEVERE = ("critical", "high")


class ReviewError(ValueError):
    pass


def items(run: dict) -> list[dict]:
    """Things a human may review: every escalation and every high or critical finding, per event."""
    out = []
    for ev in run["events"]:
        for esc in ev["escalations"]:
            out.append({"item_id": f"E{ev['seq']}:escalation:{esc['label']}", "event_seq": ev["seq"], "kind": "escalation",
                        "summary": esc["reason"]})
        for f in ev["safety"]["findings"]:
            if f["severity"] in SEVERE:
                out.append({"item_id": f"E{ev['seq']}:finding:{f['finding_id']}", "event_seq": ev["seq"],
                            "kind": "finding", "summary": f"{f['title']} ({f['severity']})"})
    return out


def _load(run_dir: Path) -> tuple[dict, list[dict]]:
    run = json.loads((Path(run_dir) / "run.json").read_text(encoding="utf-8"))
    audit = read_jsonl(Path(run_dir) / "audit.jsonl")
    return run, audit


def read_reviews(run_dir: Path) -> list[dict]:
    p = Path(run_dir) / "reviews.jsonl"
    return read_jsonl(p) if p.exists() else []


def check(run_dir: Path) -> dict:
    """Integrity of the review chain, and that it was made against this run's current audit trail."""
    run_dir = Path(run_dir)
    _, audit = _load(run_dir)
    a = verify(audit)
    if a["status"] != "ok":
        return {"status": "audit_" + a["status"], "message": "the run's audit trail is not intact: " + a["message"], "entries": 0}
    reviews = read_reviews(run_dir)
    if not reviews:
        return {"status": "none", "message": "no human review recorded", "entries": 0}
    r = verify(reviews, genesis=head_hash(audit))
    return {"status": r["status"], "message": r["message"], "entries": r["entries"]}


def record(run_dir: Path, item_id: str, decision: str, reviewer: str, role: str, reason: str) -> dict:
    run_dir = Path(run_dir)
    run, audit = _load(run_dir)
    if verify(audit)["status"] != "ok":
        raise ReviewError("the run's audit trail is not sealed or not intact; refusing to attach a review to it")
    if check(run_dir)["status"] not in ("none", "ok"):
        raise ReviewError("existing reviews.jsonl is broken; refusing to append to it")
    by_id = {i["item_id"]: i for i in items(run)}
    if item_id not in by_id:
        raise ReviewError(f"unknown item {item_id!r}; run `list` to see reviewable items")
    if decision not in DECISIONS:
        raise ReviewError(f"decision must be one of {sorted(DECISIONS)}")
    if not reviewer.strip() or not role.strip():
        raise ReviewError("reviewer and role are required")
    if len(reason.strip()) < MIN_REASON:
        raise ReviewError(f"a reason of at least {MIN_REASON} characters is required")
    existing = read_reviews(run_dir)
    entry = {"seq": len(existing) + 1, "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "item_id": item_id,
             "event_seq": by_id[item_id]["event_seq"], "item_kind": by_id[item_id]["kind"],
             "item_summary": by_id[item_id]["summary"], "decision": decision, "reviewer": reviewer.strip(),
             "role_as_stated": role.strip(), "reason": reason.strip(),
             "supersedes": next((e["seq"] for e in reversed(existing) if e["item_id"] == item_id), None),
             "effect": "record only: does not change consent state or any finding; nothing is released or acted on",
             "run_id": run_dir.name}
    plain = [{k: v for k, v in e.items() if k not in ("hash", "prev_hash")} for e in existing] + [entry]
    sealed = seal(plain, genesis=head_hash(audit))
    (run_dir / "reviews.jsonl").write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in sealed) + "\n",
                                           encoding="utf-8")
    return sealed[-1]


def status_by_item(run: dict, reviews: list[dict]) -> dict:
    """Latest decision per item; items with none are pending."""
    latest = {}
    for r in reviews:
        latest[r["item_id"]] = r
    return {i["item_id"]: latest.get(i["item_id"]) for i in items(run)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m backend.review")
    ap.add_argument("command", choices=["list", "record", "show"])
    ap.add_argument("--run", required=True)
    ap.add_argument("--item")
    ap.add_argument("--decision", choices=sorted(DECISIONS))
    ap.add_argument("--reviewer")
    ap.add_argument("--role")
    ap.add_argument("--reason")
    a = ap.parse_args(argv)
    run, _ = _load(Path(a.run))
    if a.command == "list":
        st = status_by_item(run, read_reviews(Path(a.run)))
        for i in items(run):
            r = st[i["item_id"]]
            print(f"{i['item_id']:55} {('REVIEWED: ' + r['decision'] + ' by ' + r['reviewer']) if r else 'PENDING'}\n    {i['summary']}")
        return 0
    if a.command == "show":
        c = check(Path(a.run))
        print(f"{c['status'].upper()}: {c['message']}")
        for r in read_reviews(Path(a.run)):
            print(f"#{r['seq']} {r['item_id']} -> {r['decision']} by {r['reviewer']} ({r['role_as_stated']}): {r['reason']}")
        return 0 if c["status"] in ("ok", "none") else 1
    missing = [k for k in ("item", "decision", "reviewer", "role", "reason") if not getattr(a, k)]
    if missing:
        ap.error("record needs --" + ", --".join(missing))
    try:
        e = record(Path(a.run), a.item, a.decision, a.reviewer, a.role, a.reason)
    except ReviewError as err:
        print(f"REFUSED: {err}")
        return 2
    print(f"recorded review #{e['seq']} for {e['item_id']}: {e['decision']} (hash {e['hash'][:12]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
