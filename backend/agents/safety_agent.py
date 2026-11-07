"""Medication Safety Agent.

Mandate: explain the deterministic engine's findings to a non-medical reader. It decides nothing:
which findings exist, their severity and their evidence come only from the engine. The LLM output
is validated, and any explanation that references an unknown finding or gives forbidden advice is
replaced by the engine's own template text. If the LLM is unavailable, the report still stands.
"""
import json
import re
from dataclasses import dataclass, field

from backend.llm.client import LLMClient, LLMError
from backend.safety.engine import Assessment, Finding

FORBIDDEN = re.compile(
    r"\b(stop taking|stop (the|your|this|it)|discontinue|increase (the|your) dose|decrease (the|your) dose|"
    r"double (the|your) dose|extra dose|start taking|you should take|skip (the|your))\b", re.I)

NEGATION = re.compile(r"(do not|don't|never|must not|should not|shouldn't|cannot|can't)\s*(\w+\s+){0,2}$", re.I)


def gives_forbidden_advice(text: str) -> bool:
    """True if the text tells the patient to stop/start/change medicine. Negated safe wording
    ("Do not stop your medicine on your own") is allowed."""
    for m in FORBIDDEN.finditer(text):
        if not NEGATION.search(text[max(0, m.start() - 40):m.start()]):
            return True
    return False


SYSTEM = (
    "You are the Medication Safety Agent in a health-record safety prototype. You receive findings produced by a "
    "deterministic engine. Your only job is to restate them in plain, calm language for a non-medical reader.\n"
    "Rules:\n"
    "- Use ONLY the facts in the findings given. Do not add interactions, doses, risks, numbers or references.\n"
    "- Never tell the patient to stop, start, skip, increase or decrease any medicine. Direct them to a doctor or "
    "pharmacist.\n"
    "- Keep each explanation under 60 words. Mention missing information when a finding lists it.\n"
    "- Reply with ONLY JSON: {\"summary\": str, \"explanations\": [{\"finding_id\": str, \"plain_language\": str}]}")


@dataclass
class SafetyReport:
    assessment: Assessment
    explanations: dict[str, str] = field(default_factory=dict)  # finding_id -> text
    explanation_source: dict[str, str] = field(default_factory=dict)  # finding_id -> "llm" | "template"
    summary: str = ""
    limitations: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)  # validation problems, for the audit trail


def template_text(f: Finding) -> str:
    parts = [f.explanation]
    if f.patient_factors:
        parts.append("Relevant to this patient: " + "; ".join(f.patient_factors) + ".")
    if f.missing_info:
        parts.append("Missing information: " + "; ".join(f.missing_info) + ".")
    parts.append(f.recommended_next_step)
    return " ".join(parts)


class SafetyAgent:
    name = "safety_agent"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, assessment: Assessment, limitations: list[str] | None = None) -> SafetyReport:
        report = SafetyReport(assessment, limitations=list(limitations or []))
        by_id = {f.finding_id: f for f in assessment.findings}
        for f in assessment.findings:  # default: the engine's own words
            report.explanations[f.finding_id] = template_text(f)
            report.explanation_source[f.finding_id] = "template"
        report.summary = assessment.summary
        if not assessment.findings:
            return report

        payload = [{"finding_id": f.finding_id, "category": f.category, "certainty": f.certainty,
                    "severity": f.severity, "medications": f.medications, "what": f.explanation,
                    "patient_factors": f.patient_factors, "missing_info": f.missing_info,
                    "next_step": f.recommended_next_step} for f in assessment.findings]
        messages = [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": "Findings:\n" + json.dumps(payload, indent=1)
                     + ("\nLimitations of this assessment: " + " | ".join(report.limitations) if report.limitations else "")}]
        try:
            resp = self.llm.complete(messages, json_mode=True, agent=self.name, validate=self._shape)
        except LLMError as e:
            report.issues.append(f"LLM unavailable or invalid output; engine text used instead: {e}")
            return report

        for item in resp.parsed["explanations"]:
            fid, text = item["finding_id"], item["plain_language"].strip()
            if fid not in by_id:
                report.issues.append(f"Ignored explanation for unknown finding id {fid!r}")
            elif gives_forbidden_advice(text):
                report.issues.append(f"Rejected explanation for {fid}: contained forbidden medication advice")
            elif not text:
                report.issues.append(f"Empty explanation for {fid}")
            else:
                report.explanations[fid], report.explanation_source[fid] = text, "llm"
        if isinstance(resp.parsed.get("summary"), str) and resp.parsed["summary"].strip() \
                and not gives_forbidden_advice(resp.parsed["summary"]):
            report.summary = resp.parsed["summary"].strip()
        return report

    @staticmethod
    def _shape(d):
        if not isinstance(d, dict) or not isinstance(d.get("explanations"), list):
            raise ValueError("expected an object with an 'explanations' list")
        for e in d["explanations"]:
            if not isinstance(e, dict) or not isinstance(e.get("finding_id"), str) \
                    or not isinstance(e.get("plain_language"), str):
                raise ValueError("each explanation needs string finding_id and plain_language")
        return d
