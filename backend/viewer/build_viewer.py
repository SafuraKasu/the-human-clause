"""Build the clinician workspace page from a recorded run.

    python -m backend.viewer.build_viewer [--run data/runs/<dir>] [--out docs/demo/index.html]

The page embeds the run, its audit trail, the cited passages and the gap report. Opened as a file it is
read-only; served by `python -m backend.app` it can also record human review decisions.
It shows a RECORDED run; it does not call any model.
"""
import argparse
import glob
import json
import re
from pathlib import Path

from backend import config
from backend.agents.audit import verify as verify_audit
from backend.kb.retrieve import KnowledgeBase
from backend.report import content as C
from backend.report.build import adjudicate
from backend.review import records as review
from backend.scenario import fatima
from backend.scenario.state import ScenarioState


def cited_ids(run: dict) -> set:
    ids = set()
    for ev in run["events"]:
        p = ev["policy"]
        if p:
            for key in ("requirements", "conflicts", "gaps", "comparisons"):
                for item in p[key]:
                    ids.update(item.get("citations", []))
                    ids.update(c["chunk_id"] for c in item.get("unretrieved_candidates", []))
    for g in C.GAPS:
        ids.update(cid for _, cid, _ in g["evidence"] + g["comparison"])
    return ids


def org_name(org: str) -> str:
    return re.sub(r"Hospital(?=[A-C])", "Hospital ", org)


def snapshots() -> list[dict]:
    """The patient's record as of each event, replayed deterministically (medication lists are not in run.json)."""
    st, out = ScenarioState(), []
    for ev in fatima.EVENTS:
        st.apply(ev)
        out.append({"seq": ev.seq, "age": st.age, "conditions": list(st.conditions), "allergies": list(st.allergies),
                    "labs": {k: {"value": v.value, "date": v.date} for k, v in st.labs.items()},
                    "meds": [{"name": m.name, "hospital": m.hospital, "withheld": m.hospital in st.withdrawn} for m in st.meds],
                    "withdrawn": dict(st.withdrawn)})
    return out


def access_text(check: dict) -> str:
    t = f"{org_name(check['requester']['org'])} clinician asks for {org_name(check['source_org'])} {check['category']}"
    if check["emergency"]:
        t += " (emergency access)"
    return t + (f" via {check['exchange']}" if check["exchange"] else "")


def render(run_dir: Path, server: bool = False) -> str:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    audit = [json.loads(line) for line in (run_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    kb = KnowledgeBase()
    chunks = {cid: {"document": kb.get(cid)["document"], "section": kb.get(cid)["section"], "page": kb.get(cid)["page"],
                    "scope": kb.get(cid)["scope"], "url": kb.get(cid)["url"], "text": kb.get(cid)["text"]}
              for cid in cited_ids(run) if kb.get(cid)}
    for ev in run["events"]:  # display wording only: "HospitalB:" -> "Hospital B:" in what the page shows
        ev["safety"]["limitations"] = [re.sub('Hospital([A-C])\\b', 'Hospital \\1', t) for t in ev["safety"]["limitations"]]
        exp = fatima.EVENTS[ev["seq"] - 1].expected
        ev["expected_notes"] = exp["policy"]["must_note"]
        for c in ev["checks"]:
            if c["status"] in ("fail", "differs"):
                c["note"] = adjudicate(ev["seq"], c["description"])
    gaps = [{"id": g["id"], "title": g["title"], "statement": g["statement"], "relevance": g["relevance"],
             "recommendation": g["recommendation"], "origin": g["origin"], "caveats": g["caveats"],
             "evidence": [{"label": l, "chunk_id": c} for l, c, _ in g["evidence"]],
             "comparison": [{"label": l, "chunk_id": c} for l, c, _ in g["comparison"]]} for g in C.GAPS]
    reviews = review.read_reviews(run_dir)
    data = {"run_id": run_dir.name, "run": run, "audit": audit, "audit_integrity": verify_audit(audit, expected_head=run.get("audit_head_hash", "")),
            "reviews": reviews, "review_integrity": review.check(run_dir),
            "review_status": review.status_by_item(run, reviews),
            "chunks": chunks, "gaps": gaps,
            "events_meta": [{"seq": e.seq, "title": e.title, "at": e.at, "narrative": e.narrative, "actor": org_name(e.actor),
                             "access": {c["label"]: access_text(c) for c in e.consent_checks}} for e in fatima.EVENTS],
            "snapshots": snapshots(), "sources": fatima.SOURCES, "server": server}
    blob = json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", blob)


def build(run_dir: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(run_dir), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--out", default=str(config.ROOT / "docs" / "demo" / "index.html"))
    args = ap.parse_args()
    run_dir = Path(args.run) if args.run else Path(sorted(glob.glob(str(config.ROOT / "data" / "runs" / "*-live")))[-1])
    out = build(run_dir, Path(args.out))
    print(f"wrote {out} ({out.stat().st_size // 1024} KB) from {run_dir.name}")
    return 0


TEMPLATE = (Path(__file__).with_name("workspace.html")).read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
