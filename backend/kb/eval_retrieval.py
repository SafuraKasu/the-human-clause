"""Retrieval evaluation for the policy KB.

    python -m backend.kb.eval_retrieval [--k 5] [--write docs/report/retrieval-eval.md]

Each case is a realistic question and the document + phrase that a correct answer must be able to cite.
A case HITS if any of the top-k chunks comes from the expected document AND contains the phrase.
Cases are run twice: over the whole KB (no filter) and with the jurisdiction scope the agent would normally
set. Every expected phrase is first checked to exist in the expected document, so a case cannot pass or fail
for a typo. Limits: the questions were written by the team who know the KB (optimistic); 20 cases is a small
sample, not a benchmark; a hit means the passage was retrievable, not that an agent would use it well.
"""
import argparse
import json
from pathlib import Path

from backend import config
from backend.kb.retrieve import KnowledgeBase

# (question, scope used by the agent or None, expected doc id, phrase the cited chunk must contain)
CASES = [
    ("May a hospital send a patient's health data to a cloud server in another country?", "UAE federal", "uae-health-ict-law-2019", "outside State"),
    ("Can a doctor see a patient's record without written consent if the patient's life is at risk?", "UAE federal", "uae-health-ict-law-2019", "health and safety of the patient"),
    ("Who is allowed to access a patient's health file in an emergency under the executive regulation?", "UAE federal", "uae-health-ict-exec-reg-2020", "emergency"),
    ("Does the federal data protection law cover health data that has its own legislation?", "UAE federal", "uae-pdpl-2021", "health"),
    ("What does the UAE national AI strategy say about government use of AI?", "UAE federal", "uae-ai-strategy-2031", "government"),
    ("Can a Dubai patient withdraw from health information sharing?", "Dubai", "dha-consent-access-standard-2025", "right to withdraw"),
    ("Can emergency break-the-glass access override a patient's opt-out in Dubai?", "Dubai", "dha-consent-access-standard-2025", "should not be retrieved using BTG"),
    ("How long does a patient's consent stay valid after their last visit?", "Dubai", "dha-consent-access-standard-2025", "one year"),
    ("What audit trail must be kept of who accessed patient information?", "Dubai", "dha-consent-access-standard-2025", "audit trail"),
    ("When can health information be shared between Dubai health facilities?", "Dubai", "dha-health-info-sharing-2024", "Consent must be obtained"),
    ("Must AI systems in Dubai healthcare be supervised by a human and overridable?", "Dubai", "dha-ai-policy-2021", "supervised/monitored"),
    ("Is patient participation in the Abu Dhabi health information exchange mandatory?", "Abu Dhabi", "doh-hie-policy-2020", "Universal"),
    ("Can Abu Dhabi share patient data when consent is not available?", "Abu Dhabi", "doh-hie-policy-2020", "without"),
    ("How must emergency access to a sealed record be handled in Abu Dhabi?", "Abu Dhabi", "doh-hie-policy-2020", "seal"),
    ("Must log files of the health information exchange be protected from alteration?", "Abu Dhabi", "doh-hie-policy-2020", "cannot be altered"),
    ("Which categories of personal data need extra protection under EU law?", "EU", "eu-gdpr-2016-679", "special categories"),
    ("Does a patient have the right to have their data erased?", "EU", "eu-gdpr-2016-679", "erasure"),
    ("Can EU citizens opt out of the European Health Data Space?", "EU", "eu-ehds-2025-327", "opt"),
    ("What does ITU-T Y.3172 say about a sandbox for testing machine learning?", None, "itu-t-y3172", "sandbox"),
    ("What does the ITU AI readiness framework say about human oversight?", None, "itu-ai-readiness", "human-in-the-loop"),
]


def run(k: int = 5):
    kb = KnowledgeBase()
    rows = []
    for q, scope, doc, phrase in CASES:
        exists = any(c["doc_id"] == doc and phrase.lower() in c["text"].lower() for c in kb.chunks)
        out = {"question": q, "scope": scope or "-", "doc": doc, "phrase": phrase, "phrase_exists": exists}
        for label, sc in (("unscoped", None), ("scoped", scope)):
            hits = kb.search(q, k=k, scope=sc)
            rank = next((i + 1 for i, h in enumerate(hits) if h["doc_id"] == doc and phrase.lower() in h["text"].lower()), None)
            doc_rank = next((i + 1 for i, h in enumerate(hits) if h["doc_id"] == doc), None)
            out[label] = {"rank": rank, "doc_rank": doc_rank}
        rows.append(out)
    return rows


def summarize(rows, k):
    n = len(rows)
    s = {"cases": n, "k": k, "invalid_cases": [r["question"] for r in rows if not r["phrase_exists"]]}
    for label in ("unscoped", "scoped"):
        s[label] = {"passage_recall": sum(1 for r in rows if r[label]["rank"]) / n,
                    "document_recall": sum(1 for r in rows if r[label]["doc_rank"]) / n,
                    "mrr": round(sum(1 / r[label]["rank"] for r in rows if r[label]["rank"]) / n, 3)}
    return s


def markdown(rows, s):
    k = s["k"]
    f = lambda v: f"{v:.0%}"
    out = [f"# Retrieval evaluation (top {k})", "",
           f"{s['cases']} questions. A case is a *hit* when one of the top {k} chunks is from the expected document and contains the expected phrase. "
           "Questions were written by the team, who know the KB, so results are optimistic; this is a small sample, not a benchmark.", "",
           "| | Passage recall | Document recall | MRR |", "|---|---|---|---|"]
    for label, name in (("unscoped", "Whole KB, no filter"), ("scoped", "With jurisdiction scope")):
        out.append(f"| {name} | {f(s[label]['passage_recall'])} | {f(s[label]['document_recall'])} | {s[label]['mrr']} |")
    out += ["", "| Question | Scope | Expected | Rank (no filter) | Rank (scoped) |", "|---|---|---|---|---|"]
    for r in rows:
        rk = lambda x: str(x["rank"]) if x["rank"] else "miss"
        out.append(f"| {r['question']} | {r['scope']} | `{r['doc']}` “{r['phrase']}” | {rk(r['unscoped'])} | {rk(r['scoped'])} |")
    if s["invalid_cases"]:
        out += ["", "Invalid cases (expected phrase not in the expected document): " + "; ".join(s["invalid_cases"])]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--write", default=None)
    a = ap.parse_args()
    rows = run(a.k)
    s = summarize(rows, a.k)
    md = markdown(rows, s)
    print(md)
    if a.write:
        Path(a.write).write_text(md, encoding="utf-8")
        Path(a.write).with_suffix(".json").write_text(json.dumps({"summary": s, "rows": rows}, indent=1), encoding="utf-8")
    return 1 if s["invalid_cases"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
