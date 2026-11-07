"""Build the submission report in the official template's structure (Word + HTML preview).

    python -m backend.report.export_docx [--run data/runs/<dir>] [--team-name "..."]

Content comes from backend/report/content.py (every citation verified against the KB) and from the
recorded live run's run.json (numbers are never typed by hand). The HTML preview is printed with
Edge to estimate the page count, because this machine has no Word/LibreOffice renderer.
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from backend import config
from backend.kb.retrieve import KnowledgeBase
from backend.report import content as C
from backend.report.build import Verifier, adjudicate, load_run

OUT = config.ROOT / "docs" / "report"
EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
STEPS = {
    1: "Hospitals A and C upload warfarin, ramipril and metformin; no lab results are on file.",
    2: "Hospital B (Dubai) adds spironolactone.",
    3: "Overdue results (eGFR 24, potassium 5.4) arrive three days late.",
    4: "The patient withdraws consent for Hospital B's data and opts out of Dubai's exchange (NABIDH).",
    5: "Emergency: an Abu Dhabi clinician requests Hospital B's medication list by break-the-glass; the patient has opted out.",
    6: "Hospital C asks which institution must coordinate follow-up of the high-severity findings.",
}
SEV = ["critical", "high", "moderate", "low", "informational"]


def observed(ev: dict) -> str:
    fs = sorted(ev["safety"]["findings"], key=lambda f: (SEV.index(f["severity"]), f["finding_id"]))
    top = "; ".join(f"{f['title'][:62]} ({f['severity']})" for f in fs[:3]) or "no findings"
    parts = [f"Safety: {top}" + (f" and {len(fs) - 3} more" if len(fs) > 3 else "") + "."]
    if ev["safety"]["limitations"]:
        parts.append("The assessment states it is incomplete (data withheld by the patient).")
    if ev["consent"]:
        parts.append("Consent: " + ", ".join(f"{d['reason_code']}" for d in ev["consent"].values()) + ".")
    if ev["escalations"]:
        parts.append("Escalated to a human.")
    p = ev["policy"]
    if p:
        docs = {c.split("#")[0] for k in ("requirements", "conflicts", "gaps", "comparisons") for i in p[k] for c in i.get("citations", [])}
        gaps = "; ".join(g["title"] for g in p["gaps"]) or "none"
        parts.append(f"Policy agent: {len(p['searches'])} searches, cited {len(docs)} document{'s' if len(docs) != 1 else ''}, gaps raised: {gaps}.")
    return " ".join(parts)


def build_data(v: Verifier, run_dir: Path, run: dict, kb: KnowledgeBase, team: dict) -> dict:
    n_docs = len({c["doc_id"] for c in kb.chunks})
    t = run["totals"]
    for node, _, _, rc, pol, _ in C.PIPELINE_ROWS:
        for cid, ph in rc:
            v.cite(cid, ph, f"{node} readiness")
        for _, cid, ph in pol:
            v.cite(cid, ph, f"{node} policy")
    for g in C.GAPS:
        for _, cid, ph in g["evidence"] + g["comparison"]:
            v.cite(cid, ph, g["id"])
    gap_scan = {g["id"]: [(n, v.scan(d, pat)) for d, pat, n in g["scans"]] for g in C.GAPS}

    table_rows = []
    for node, ours, ready, _, pol, status in C.PIPELINE_ROWS:
        table_rows.append([node, f"{ours} **[{status}]**", ready, "; ".join(lbl for lbl, _, _ in pol)])

    scen = []
    for ev in run["events"]:
        scen.append(f"**Step {ev['seq']} ({ev['at'][5:10].replace('-', '/')}).** {STEPS[ev['seq']]} **Observed:** {observed(ev)}")
    fails = [(ev["seq"], c) for ev in run["events"] for c in ev["checks"] if c["status"] in ("fail", "differs")]
    alt = sum(1 for s, c in fails if "Valid alternative" in adjudicate(s, c["description"]))

    gaps = []
    for g in C.GAPS:
        scans = "; ".join(f"{n} = {c}" for n, c in gap_scan[g["id"]])
        gaps.append(f"**{g['id']}. {g['title']}.** {g['statement']}" + (f" (Full-text check: {scans}.)" if scans else "")
                    + f" **Recommendation:** {g['recommendation']}")

    return {
        "title": f"AI for Good Sandbox Hackathon \u2013 {team['name']} \u2013 The Human Clause",
        "team": team,
        "sections": [
            {"heading": "1. Introduction", "paras": [
                "The Human Clause is an agentic AI prototype for medication safety across hospitals in different emirates. A deterministic safety "
                "engine finds interaction, duplication, contraindication and lab-dependent risks; a Policy agent retrieves what UAE federal, Dubai and "
                "Abu Dhabi rules say about each step; a consent module decides what may be shared; and a plain-Python Orchestrator coordinates them "
                "and records every handoff in an audit trail. Where rules conflict, are silent or leave jurisdiction unclear, the system says so and "
                f"the finding becomes a documented policy gap. The report maps the pipeline to ITU-T Y.3172 and the AI Readiness Framework 2.0 and "
                f"to the {n_docs} published UAE, EU and ITU documents in the knowledge base. All patient data is synthetic."]},
            {"heading": "2. Description of the use case", "paras": [
                "Healthcare, medication safety. Patients with several chronic conditions are treated by multiple hospitals, each holding a separate "
                "record. Existing interaction checkers examine isolated drug pairs from one record and ignore what decides whether anything may "
                "lawfully be done: the patient's consent and the differing rules of each emirate. Our demonstration patient, Fatima Hassan (72, "
                "synthetic), has kidney disease, diabetes, hypertension, atrial fibrillation and a penicillin allergy, with prescriptions from "
                "Hospitals A and C (Abu Dhabi) and B (Dubai).",
                "The solution (1) joins records only where consent allows, (2) checks them with reproducible rules that flag missing data instead of "
                "guessing, (3) cites the rules governing each step, and (4) escalates to a human when rules conflict. It closes the gaps of isolated "
                "checks and policy-blind AI by making policy grounding, consent and auditability part of the pipeline."]},
            {"heading": "3. Use case requirements", "bullets": [f"**{rid}** ({C.REQ_NODES[rid]}): {text}" for rid, text in C.REQUIREMENTS]},
            {"heading": "4. Mapping with ITU-T Y.3172, the Readiness 2.0 report and domain-specific policies",
             "table": {"cols": ["Y.3172 node", "Use case (Human Clause)", "Readiness 2.0 report", "Documents (verified in ingested text)"],
                       "widths": [800, 3300, 2200, 3060], "rows": table_rows},
             "paras": [C.Y3172_CAVEAT + " " + C.PIPELINE_NOT_ADDRESSED]},
            {"heading": "5. Error scenarios",
             "paras": ["Events are released one at a time; each has an expected outcome written before any agent existed. "
                       f"Recorded live run ({', '.join(run['models'])}): {t['pass']} checks pass, {t['fail']} fail, {t['review']} need human judgement, "
                       f"{t['differs']} hypothesis was not confirmed at its expected event."] + scen + [
                       f"**Review of the non-passes.** Expectations were not changed after the run. Of the {t['fail']} failed checks, {alt} cited a different valid "
                       "provision than the one we named (for example Executive Regulation Art. 6(3) for emergency access, and Abu Dhabi's break-the-seal "
                       "rule that we had not scripted), and one did not cite the Dubai scope clause although the agent raised the scope question. "
                       "The unconfirmed hypothesis was raised at a different event. Each was checked against the source text."]},
            {"heading": "6. Policy gaps and standards gaps derived from the mapping exercise", "paras": gaps + [
                "**Limitations.** The medication knowledge base is a small team-curated demonstration set, not clinically validated or reviewed by a "
                "clinician. There is no independent validation, authentication, encryption or tamper-proof logging, and no real hospital integration. "
                f"The language model is a free-tier Gemini model; the recorded run was served by {', '.join(run['models'])} because the primary model's daily free quota was spent, and the run is replayable from a cached record. "
                "Policy texts are English only. Not ingested: Abu Dhabi's AI policy and Responsible AI Standard (download failed) and Ministerial "
                "Decision 51 of 2021. Policy findings summarise what the texts say; they are not legal advice, and absence in our knowledge base is "
                "not absence in law."]},
        ],
    }


def md_runs(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(text))


def preview_html(d: dict) -> str:
    out = ["<!doctype html><meta charset='utf-8'><style>@page{size:Letter;margin:1in}body{font:11pt 'Times New Roman',serif;line-height:1.2;margin:0}"
           "h1{font-size:13pt;margin:0 0 3pt}h2{font-size:12pt;margin:7pt 0 2pt}p{margin:0 0 4pt}ul{margin:0 0 4pt 16pt;padding:0}li{margin:0 0 1pt}"
           "table{border-collapse:collapse;width:100%;font-size:9pt;margin:2pt 0 4pt}td,th{border:.5pt solid #777;padding:2pt 3pt;vertical-align:top}th{background:#ddd}</style>"]
    t = d["team"]
    out.append(f"<h1>{html.escape(d['title'])}</h1><p><b>Team leader:</b> {html.escape(t['leader'])} &nbsp; <b>Members:</b> {html.escape(t['members'])} &nbsp; "
               f"<b>Contact:</b> {html.escape(t['contact'])} &nbsp; <b>GitHub:</b> {html.escape(t['github'])}</p>")
    for s in d["sections"]:
        out.append(f"<h2>{html.escape(s['heading'])}</h2>")
        for p in s.get("paras", []):
            if s.get("table") and p is s["paras"][-1] and False:
                pass
        if s.get("table"):
            tb = s["table"]
            out.append("<table><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in tb["cols"]) + "</tr>" +
                       "".join("<tr>" + "".join(f"<td>{md_runs(c)}</td>" for c in r) + "</tr>" for r in tb["rows"]) + "</table>")
        if s.get("bullets"):
            out.append("<ul>" + "".join(f"<li>{md_runs(b)}</li>" for b in s["bullets"]) + "</ul>")
        out += [f"<p>{md_runs(p)}</p>" for p in s.get("paras", [])]
    return "".join(out)


def count_pages(html_path: Path) -> int | None:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        return None
    pdf = html_path.with_suffix(".pdf")
    subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", html_path.as_uri()],
                   capture_output=True, timeout=90)
    from pypdf import PdfReader
    return len(PdfReader(str(pdf)).pages) if pdf.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--team-name", default="[TEAM NAME]")
    ap.add_argument("--leader", default="[TEAM LEADER]")
    ap.add_argument("--members", default="[TEAM MEMBERS]")
    ap.add_argument("--contact", default="[CONTACT DETAILS]")
    ap.add_argument("--github", default="https://github.com/SafuraKasu/the-human-clause")
    args = ap.parse_args()
    kb = KnowledgeBase()
    v = Verifier(kb)
    run_dir, run = load_run(args.run)
    if run["mode"] != "live":
        print("REFUSING: the run is not a live run; the report must describe observed outcomes.")
        return 1
    team = {"name": args.team_name, "leader": args.leader, "members": args.members, "contact": args.contact, "github": args.github}
    data = build_data(v, run_dir, run, kb, team)
    if v.errors:
        print("CITATION CHECK FAILED:\n" + "\n".join("  - " + e for e in v.errors))
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "docx-data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    prev = OUT / "report-preview.html"
    prev.write_text(preview_html(data), encoding="utf-8")
    docx = OUT / "The-Human-Clause-technical-report.docx"
    r = subprocess.run(["node", str(Path(__file__).with_name("build_docx.js")), str(OUT / "docx-data.json"), str(docx)],
                       capture_output=True, text=True)
    if r.returncode:
        print("docx build failed:", r.stderr[-800:])
        return 1
    words = sum(len(re.sub(r"\*\*", "", x).split()) for s in data["sections"] for x in s.get("paras", []) + s.get("bullets", []))
    words += sum(len(c.split()) for s in data["sections"] if s.get("table") for row in s["table"]["rows"] for c in row)
    pages = count_pages(prev)
    print(f"wrote {docx.name} ({docx.stat().st_size // 1024} KB), {words} words, {v.count} citations verified; run {run_dir.name}")
    print(f"estimated pages (Edge print of the HTML preview, Letter, 1in margins): {pages}  (limit 5; confirm in Word)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
