"""Compare actual outcomes with the expectations written beforehand in the scenario.

Statuses:
  pass    objective check met
  fail    objective check not met
  review  cannot be judged by code (free-text expectations, gap matching): a human must verify
  differs the agent did not confirm one of our gap hypotheses (a legitimate outcome, not forced to match)
"""
import re

from backend.kb.retrieve import KnowledgeBase
from backend.scenario import fatima


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).lower()


def _check(area, description, expected, actual, status):
    return {"area": area, "description": description, "expected": expected, "actual": actual, "status": status}


def evaluate_event(event, assessment, consent, limitations, policy_report, trail_kinds, kb: KnowledgeBase) -> list[dict]:
    exp, checks = event.expected, []
    findings = {f.finding_id: f for f in assessment.findings}
    ids = sorted(findings)

    s = exp["safety"]
    for fid in s.get("present", []):
        checks.append(_check("safety", f"finding {fid} present", "present", "present" if fid in findings else f"absent (have {ids})",
                             "pass" if fid in findings else "fail"))
    for fid in s.get("absent", []):
        checks.append(_check("safety", f"finding {fid} absent", "absent", "present" if fid in findings else "absent",
                             "fail" if fid in findings else "pass"))
    for fid, sev in s.get("severity", {}).items():
        actual = findings[fid].severity if fid in findings else "missing"
        checks.append(_check("safety", f"severity of {fid}", sev, actual, "pass" if actual == sev else "fail"))
    for cat in s.get("no_category", []):
        got = [f.finding_id for f in assessment.findings if f.category == cat]
        checks.append(_check("safety", f"no '{cat}' findings", "none", got or "none", "fail" if got else "pass"))
    for needle in exp.get("limitations", []):
        ok = any(needle in l for l in limitations)
        checks.append(_check("safety", f"limitation notice mentions {needle}", "present", "present" if ok else "missing",
                             "pass" if ok else "fail"))

    for label, e in exp["consent"].items():
        d = consent.get(label)
        actual = {"allowed": d.allowed, "reason_code": d.reason_code, "escalate": d.escalate} if d else None
        want = {k: e[k] for k in ("allowed", "reason_code", "escalate") if k in e}
        ok = d is not None and all(actual[k] == v for k, v in want.items())
        checks.append(_check("consent", label, want, actual, "pass" if ok else "fail"))

    cited = policy_report.cited_chunk_ids() if policy_report else set()
    for doc_id, phrase in exp["policy"]["must_cite"]:
        hit = [cid for cid in cited if kb.get(cid)["doc_id"] == doc_id and _norm(phrase) in _norm(kb.get(cid)["text"])]
        checks.append(_check("policy", f"cites {doc_id} ({phrase!r})", "cited", hit[:2] or "not cited",
                             "pass" if hit else "fail"))
    for note in exp["policy"]["must_note"]:
        checks.append(_check("policy", "expectation for human review", note,
                             "see agent output (conflicts, caveats, gaps)", "review"))

    raised = policy_report.gaps if policy_report else []
    for gap_id in exp["gaps"]:
        want_docs = fatima.GAP_EVIDENCE_DOCS.get(gap_id, [])
        match = None
        for g in raised:
            docs = {kb.get(c)["doc_id"] for c in g["citations"]}
            if (want_docs and docs & set(want_docs)) or (not want_docs and g["type"] == "no_provision_found"):
                match = g
                break
        if match:
            checks.append(_check("gap", f"{gap_id}: hypothesis", fatima.GAP_HYPOTHESES[gap_id][:140],
                                 f"likely match: {match['title']!r} ({match['type']})", "review"))
        else:
            checks.append(_check("gap", f"{gap_id}: hypothesis", fatima.GAP_HYPOTHESES[gap_id][:140],
                                 "not raised by the agent (hypothesis not confirmed)", "differs"))

    for kind in exp["audit"]:
        ok = kind in trail_kinds or f"consent_{kind}" in trail_kinds
        checks.append(_check("audit", f"audit trail has '{kind}'", "present", "present" if ok else "missing",
                             "pass" if ok else "fail"))
    return checks


def summarize(checks: list[dict]) -> dict:
    out = {"pass": 0, "fail": 0, "review": 0, "differs": 0}
    for c in checks:
        out[c["status"]] += 1
    return out
