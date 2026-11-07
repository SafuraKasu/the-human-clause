"""Build the report material in docs/report/ from authored content + the KB + the latest run.

    python -m backend.report.build [--run data/runs/<run dir>]

Fails (non-zero exit) if any cited phrase is missing from its KB chunk, so nothing in the report can
drift from the source texts. Evaluation numbers come from the run's run.json, never typed by hand.
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

from backend import config
from backend.kb.retrieve import KnowledgeBase
from backend.report import content as C
from backend.scenario import fatima

OUT = config.ROOT / "docs" / "report"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).lower()


class Verifier:
    def __init__(self, kb: KnowledgeBase):
        self.kb, self.errors, self.count = kb, [], 0

    def cite(self, chunk_id: str, phrase: str, where: str) -> str:
        self.count += 1
        c = self.kb.get(chunk_id)
        if not c:
            self.errors.append(f"{where}: chunk {chunk_id} does not exist")
        elif norm(phrase) not in norm(c["text"]):
            self.errors.append(f"{where}: phrase {phrase!r} not found in {chunk_id}")
        return chunk_id

    def scan(self, doc_ids: list, pattern: str) -> int:
        return sum(len(re.findall(pattern, norm(c["text"]), re.I)) for c in self.kb.chunks if c["doc_id"] in doc_ids)


def short_cite(kb, chunk_id: str) -> str:
    c = kb.get(chunk_id)
    return f"{c['section'] if not c['section'].startswith('p.') else 'p.' + str(c['page'])} [{chunk_id}]"


# ---- table builders --------------------------------------------------------------------------------------
def y3172_md(v: Verifier, full: bool) -> str:
    hdr = "| Y.3172 component | Role in Y.3172 | Human Clause counterpart | Status |" + (" Evidence |" if full else "")
    rows = [hdr, "|---|---|---|---|" + ("---|" if full else "")]
    for comp, role, ours, status, cites in C.Y3172_ROWS:
        ev = "; ".join(f"`{v.cite(cid, ph, 'Y3172 ' + comp)}`" for cid, ph in cites)
        rows.append(f"| {comp} | {role} | {ours} | **{status}** |" + (f" {ev} |" if full else ""))
    return "\n".join(rows) + f"\n\n*{C.Y3172_CAVEAT}*\n"


def readiness_md(v: Verifier, full: bool) -> str:
    hdr = "| Event-page lens | Framework mapping | How addressed | Status |" + (" Evidence |" if full else "")
    rows = [hdr, "|---|---|---|---|" + ("---|" if full else "")]
    for lens, mapping, how, status, cites in C.READINESS_ROWS:
        ev = "; ".join(f"`{v.cite(cid, ph, 'Readiness ' + lens)}`" for cid, ph in cites)
        rows.append(f"| {lens} | {mapping} | {how} | **{status}** |" + (f" {ev} |" if full else ""))
    return "\n".join(rows) + "\n"


def policy_md(v: Verifier, full: bool) -> str:
    rows = ["| Requirement | Provisions (verified in ingested text) | Implementation | Status |", "|---|---|---|---|"]
    for req, provs, impl, status in C.POLICY_ROWS:
        for _, cid, ph in provs:
            v.cite(cid, ph, f"Policy {req}")
        if full:
            p = "<br>".join(f"{label}: \"…{ph}…\" `{cid}`" for label, cid, ph in provs)
        else:
            p = "; ".join(label for label, _, _ in provs)
        rows.append(f"| {req} | {p} | {impl} | **{status}** |")
    return "\n".join(rows) + "\n"


def gaps_md(v: Verifier, full: bool) -> str:
    out = []
    for g in C.GAPS:
        out += [f"### {g['id']}: {g['title']}", "", g["statement"], ""]
        out.append("**Evidence:** " + "; ".join(
            f"{label} `{v.cite(cid, ph, g['id'])}`" if full else label for label, cid, ph in g["evidence"]))
        if g["scans"]:
            res = [f"{n}: **{v.scan(docs, pat)}**" for docs, pat, n in g["scans"]]
            out += ["", "**Full-text scan results (computed at build time):** " + "; ".join(res)]
        if g["comparison"]:
            out += ["", "**International comparison:** " + "; ".join(
                f"{label} `{v.cite(cid, ph, g['id'])}`" if full else label for label, cid, ph in g["comparison"])]
        out += ["", f"**Why it matters here:** {g['relevance']}", "", f"**Recommendation:** {g['recommendation']}", "",
                f"**Origin:** {g['origin']}", "", f"**Caveats:** {g['caveats']}", ""]
    return "\n".join(out)


# ---- evaluation ------------------------------------------------------------------------------------------
def load_run(path: str | None):
    run_dir = Path(path) if path else Path(sorted(glob.glob(str(config.ROOT / "data" / "runs" / "*-live")))[-1])
    return run_dir, json.loads((run_dir / "run.json").read_text(encoding="utf-8"))


def adjudicate(seq: int, description: str) -> str:
    for (s, sub), note in C.ADJUDICATION.items():
        if s == seq and sub in description:
            return note
    return "**Unadjudicated: needs review.**"


def evaluation_md(run_dir: Path, run: dict) -> tuple[str, list]:
    t = run["totals"]
    out = [f"Source run: `{run_dir.name}` ({run['mode']} mode; models: {', '.join(run['models'])}).", "",
           f"**Totals:** {t['pass']} checks pass, {t['fail']} fail, {t['review']} need human review, "
           f"{t['differs']} hypothesis not confirmed. `review` items are free-text expectations or gap matches that code cannot judge.", ""]
    if run["mode"] != "live":
        out.insert(0, "> **WARNING: this run is not a live run; do not present its outcomes as observed.**\n")
    out += ["| # | Event | Expected (written beforehand) | Actual (from the run) | Pass / fail / review / differs |",
            "|---|---|---|---|---|"]
    unadjudicated = []
    for e, ev in zip(fatima.EVENTS, run["events"]):
        exp = e.expected
        exp_bits = []
        if exp["safety"].get("present"):
            exp_bits.append("findings: " + ", ".join(exp["safety"]["present"]))
        if exp["safety"].get("absent"):
            exp_bits.append("absent: " + ", ".join(exp["safety"]["absent"]))
        if exp["consent"]:
            exp_bits.append("consent: " + ", ".join(f"{k}→{v['reason_code']}" for k, v in exp["consent"].items()))
        if exp["gaps"]:
            exp_bits.append("gap hypotheses: " + ", ".join(exp["gaps"]))
        act = ["findings: " + (", ".join(f"{f['finding_id']} ({f['severity']})" for f in ev["safety"]["findings"]) or "none")]
        if ev["consent"]:
            act.append("consent: " + ", ".join(f"{k}→{d['reason_code']}" for k, d in ev["consent"].items()))
        if ev["escalations"]:
            act.append("escalated to a human")
        if ev["policy"]:
            p = ev["policy"]
            act.append(f"policy agent: {len(p['searches'])} searches, {len(p['requirements'])} requirements, "
                       f"{len(p['conflicts'])} conflicts, gaps: " + ("; ".join(g["title"] for g in p["gaps"]) or "none"))
        s = ev["summary"]
        out.append(f"| {e.seq} | {e.title} | {'<br>'.join(exp_bits)} | {'<br>'.join(act)} | "
                   f"{s['pass']} / {s['fail']} / {s['review']} / {s['differs']} |")
    out += ["", "### Review of checks that were not a pass", "",
            "Expectations were written before any agent existed and were **not changed** after the run. "
            "Failures and non-confirmations were reviewed by the team against the source text:", "",
            "| Event | Check | Status | Review |", "|---|---|---|---|"]
    for ev in run["events"]:
        for c in ev["checks"]:
            if c["status"] in ("fail", "differs"):
                note = adjudicate(ev["seq"], c["description"])
                if "Unadjudicated" in note:
                    unadjudicated.append((ev["seq"], c["description"]))
                out.append(f"| {ev['seq']} | {c['description'][:110]} | {c['status']} | {note} |")
    return "\n".join(out) + "\n", unadjudicated


# ---- assemble --------------------------------------------------------------------------------------------
def report_md(v: Verifier, eval_md: str, run: dict, kb: KnowledgeBase) -> str:
    n_docs = len({c["doc_id"] for c in kb.chunks})
    return f"""# The Human Clause: policy-grounded medication-safety agents for the UAE

*DRAFT built from `backend/report/build.py`. Every citation and number below is machine-checked. Trim to the official template (max 5 pages) before submitting.*

## 1. Introduction to the agentic solution

The Human Clause is a prototype in which cooperating AI agents help keep a patient's medications safe across several hospitals **and** check what UAE law, institutional mandates and the patient's consent allow before anything is shown or shared. Where the rules conflict, leave scope unclear or are silent, the system says so, and that becomes a documented policy gap.

It has three agents (Orchestrator, Medication Safety, Policy & Legal Adviser) and two deterministic modules (a safety rule engine and a consent module). The Orchestrator is plain Python. The Safety agent only explains findings that the engine produced. The Policy agent searches a knowledge base of {n_docs} published documents and may cite only passages it actually retrieved. Roles and limits are in `docs/agents.md`. All patient data is synthetic.

## 2. Use case

Healthcare, medication safety. Fatima Hassan, 72 (synthetic), has kidney disease, diabetes, hypertension and atrial fibrillation, a penicillin allergy, and prescriptions from three hospitals: A and C in Abu Dhabi and B in Dubai. No hospital sees the others' prescriptions unless she allows it. The scenario releases six events one at a time (new prescriptions, late lab results, withdrawal of consent, an emergency request, an unclear mandate) so the system must act on incomplete and changing information.

## 3. Requirements

{chr(10).join(f"- **{rid}** {text}" for rid, text in C.REQUIREMENTS)}

## 4. Mapping to ITU-T Y.3172

{y3172_md(v, full=False)}
## 5. Mapping to the ITU AI Readiness Framework 2.0

{readiness_md(v, full=False)}
## 6. Mapping of requirements to local policies

{policy_md(v, full=False)}
## 7. Evaluation scenario (technical and policy)

{eval_md}
## 8. Policy and standards gaps found

{gaps_md(v, full=False)}
## Limitations and honest status

- The medication knowledge base is a **small team-curated demonstration set** (4 interactions, 2 contraindications, 2 lab rules, 13 ingredients), not clinically validated and not reviewed by a clinician.
- No independent validation, authentication, encryption or tamper-proof logging; no real hospital integration; synthetic data only.
- The policy KB holds English text only (Arabic originals prevail legally). Not ingested: Abu Dhabi's AI policy and Responsible AI Standard (download failed), and Ministerial Decision 51 of 2021.
- The language model is a free-tier Gemini model; outputs vary between runs, so results come from a recorded run that is replayable from cache.
- Policy findings are retrieval-based summaries of what the texts say, not legal advice. Absence in the KB is not absence in law.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    args = ap.parse_args()
    kb = KnowledgeBase()
    v = Verifier(kb)
    run_dir, run = load_run(args.run)
    eval_md, unadjudicated = evaluation_md(run_dir, run)

    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "mapping-y3172.md": "# ITU-T Y.3172 mapping (full, with evidence)\n\n" + y3172_md(v, True),
        "mapping-ai-readiness.md": "# ITU AI Readiness Framework 2.0 mapping (full, with evidence)\n\n" + readiness_md(v, True),
        "mapping-policy.md": "# Requirements-to-policy mapping (full, with verified quotes)\n\n" + policy_md(v, True),
        "gap-report.md": "# Policy and standards gap report\n\nEvery quoted phrase is verified against the ingested text at build time.\n\n" + gaps_md(v, True),
        "evaluation.md": "# Evaluation results\n\n" + eval_md,
    }
    files["technical-report-draft.md"] = report_md(v, eval_md, run, kb)
    # Evidence in the draft report is also verified (short form still calls cite()).
    gap_json = [{k: g[k] for k in ("id", "title", "statement", "relevance", "recommendation", "origin", "caveats")}
                | {"evidence": [{"label": l, "chunk_id": c, "phrase": p} for l, c, p in g["evidence"]],
                   "international_comparison": [{"label": l, "chunk_id": c, "phrase": p} for l, c, p in g["comparison"]],
                   "scans": [{"description": n, "count": v.scan(d, pat)} for d, pat, n in g["scans"]]} for g in C.GAPS]
    files["gaps.json"] = json.dumps(gap_json, indent=1, ensure_ascii=False)

    if v.errors:
        print("CITATION CHECK FAILED:")
        print("\n".join("  - " + e for e in v.errors))
        return 1
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8")
    words = len(files["technical-report-draft.md"].split())
    print(f"OK: {v.count} citations verified against the KB; wrote {len(files)} files to {OUT}")
    print(f"Run used: {run_dir.name} ({run['mode']}); totals {run['totals']}")
    print(f"Draft report: {words} words (a 5-page limit with tables is roughly 2,300-2,800 words)")
    if unadjudicated:
        print("UNADJUDICATED checks:", unadjudicated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
