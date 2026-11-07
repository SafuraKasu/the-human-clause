"""Orchestrator: plain-Python coordinator (no LLM, no framework).

For each scenario event it applies the deterministic state (consent + safety engine), hands the
situation to the Safety agent and (when the event has a policy question) the Policy agent, collects
their independent assessments, escalates anything needing a human, logs every handoff, and compares
actual with expected outcomes.
"""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from backend.agents.audit import AuditTrail
from backend.agents.evaluate import evaluate_event, summarize
from backend.agents.policy_agent import PolicyAgent, PolicyReport
from backend.agents.safety_agent import SafetyAgent, SafetyReport
from backend.kb.retrieve import KnowledgeBase
from backend.llm.client import LLMClient
from backend.safety.engine import SafetyEngine
from backend.scenario import fatima
from backend.scenario.state import ScenarioState


@dataclass
class EventResult:
    event: fatima.Event
    consent: dict
    safety: SafetyReport
    policy: "PolicyReport | None"
    escalations: list[dict]
    checks: list[dict]
    summary: dict


@dataclass
class RunResult:
    mode: str
    models: list[str]
    results: list[EventResult]
    trail: AuditTrail
    gap_register: list[dict] = field(default_factory=list)

    def totals(self) -> dict:
        out = {"pass": 0, "fail": 0, "review": 0, "differs": 0}
        for r in self.results:
            for k, v in r.summary.items():
                out[k] += v
        return out


class Orchestrator:
    name = "orchestrator"

    def __init__(self, llm: LLMClient, kb: KnowledgeBase | None = None, engine: SafetyEngine | None = None):
        self.llm, self.kb = llm, kb or KnowledgeBase()
        self.engine = engine or SafetyEngine()
        self.safety_agent, self.policy_agent = SafetyAgent(llm), PolicyAgent(llm, self.kb)
        self.trail = AuditTrail()
        self._event: fatima.Event | None = None
        self._models: list[str] = []
        self._calls: list[dict] = []
        self.llm.on_call = self._on_llm_call

    # ---- audit plumbing ------------------------------------------------------------------
    def _log(self, kind, actor, summary, **data):
        e = self._event
        return self.trail.add(kind, actor, e.seq if e else 0, e.at if e else "", summary, **data)

    def _on_llm_call(self, rec: dict) -> None:
        if rec["model"] not in self._models:
            self._models.append(rec["model"])
        self._calls.append(rec)
        self._log("llm_call", rec["agent"] or "llm", f"{rec['agent']} -> {rec['model']} "
                  f"({'cache' if rec['cached'] else 'network'}, {rec['attempts']} attempt(s), {rec['latency_s']}s)",
                  model=rec["model"], mode=rec["mode"], cached=rec["cached"], attempts=rec["attempts"],
                  usage=rec["usage"], request=rec["request"]["messages"][-1]["content"][:2000],
                  response=(rec["response"]["content"] or json.dumps(rec["response"]["tool_calls"]))[:2000])

    # ---- run -----------------------------------------------------------------------------
    def run(self, events=None, progress=print) -> RunResult:
        events = events or fatima.EVENTS
        state = ScenarioState(self.engine)
        seen_log = 0
        results = []
        gap_register = []
        for event in events:
            self._event = event
            self._log("event_arrived", self.name, f"E{event.seq}: {event.title}", kind_of_event=event.kind,
                      actor_of_event=event.actor)
            outputs = state.apply(event)
            for entry in state.registry.log[seen_log:]:
                self._log(f"consent_{entry['kind']}", "consent_module", self._consent_summary(entry), **{
                    k: v for k, v in entry.items() if k not in ("kind", "seq")})
            seen_log = len(state.registry.log)
            assessment = outputs["assessment"]
            self._log("safety_engine_result", "safety_engine",
                      f"{len(assessment.findings)} finding(s) from {len(assessment.pairs_checked)} pair(s)",
                      findings=[{"id": f.finding_id, "severity": f.severity, "certainty": f.certainty,
                                 "evidence": f.evidence["reference_id"], "kb_version": f.evidence["kb_version"]}
                                for f in assessment.findings],
                      pairs_checked=assessment.pairs_checked, limitations=outputs["limitations"],
                      kb_label=assessment.kb_label)

            escalations = []
            for label, d in outputs["consent"].items():
                if d.escalate:
                    escalations.append({"label": label, "reason": d.reason, "basis": d.rule_basis})
                    self._log("escalation_to_human", self.name,
                              f"Human decision required: {d.reason}", label=label, basis=d.rule_basis)

            self._log("handoff", self.name, "orchestrator -> safety_agent", to="safety_agent")
            safety = self.safety_agent.run(assessment, outputs["limitations"])
            self._log("agent_result", "safety_agent",
                      f"explained {len(safety.explanations)} finding(s); sources: "
                      f"{sorted(set(safety.explanation_source.values()))}",
                      explanation_source=safety.explanation_source, issues=safety.issues)

            policy = None
            question = fatima.POLICY_QUESTIONS.get(event.seq)
            if question:
                self._log("handoff", self.name, "orchestrator -> policy_agent", to="policy_agent", question=question)
                policy = self.policy_agent.run(event.seq, question, self._context(event, outputs))
                self._log("agent_result", "policy_agent",
                          f"{len(policy.searches)} search(es); {len(policy.requirements)} requirement(s), "
                          f"{len(policy.conflicts)} conflict(s), {len(policy.gaps)} gap(s)",
                          searches=policy.searches, cited=sorted(policy.cited_chunk_ids()),
                          gaps=[{"title": g["title"], "type": g["type"]} for g in policy.gaps],
                          issues=policy.issues, completed=policy.completed)
                for g in policy.gaps:
                    gap_register.append({"event_seq": event.seq, **g})

            checks = evaluate_event(event, assessment, outputs["consent"], outputs["limitations"], policy,
                                    self.trail.kinds(), self.kb)
            summary = summarize(checks)
            self._log("evaluation", self.name, f"expected vs actual: {summary}", counts=summary)
            results.append(EventResult(event, outputs["consent"], safety, policy, escalations, checks, summary))
            progress(f"E{event.seq} {event.title[:60]:60} {summary}")
        return RunResult(self.llm.mode, list(self._models), results, self.trail, gap_register)

    # ---- helpers -------------------------------------------------------------------------
    @staticmethod
    def _consent_summary(entry: dict) -> str:
        if entry["kind"] == "access_decision":
            return (f"{entry['requester']} -> {entry['source_org']} {entry['category']}: "
                    f"{'ALLOWED' if entry['allowed'] else 'DENIED'} ({entry['reason_code']})")
        return entry["kind"].replace("_", " ")

    @staticmethod
    def _context(event: fatima.Event, outputs: dict) -> str:
        lines = [f"Event {event.seq} ({event.at}): {event.title}", event.narrative, "",
                 "Institutions: " + "; ".join(f"{k} = {v['label']}, {v['emirate']}, exchange {v['exchange']}"
                                              for k, v in fatima.SOURCES.items())]
        if outputs["consent"]:
            lines.append("Consent module decisions:")
            for label, d in outputs["consent"].items():
                lines.append(f"- {label}: {'allowed' if d.allowed else 'denied'} [{d.reason_code}] {d.reason}"
                             + (f" Basis: {d.rule_basis}" if d.rule_basis else "")
                             + (" (escalated to a human)" if d.escalate else ""))
        a = outputs["assessment"]
        lines.append("Safety engine findings now: " + (", ".join(f"{f.finding_id} ({f.severity})" for f in a.findings)
                                                      or "none"))
        for l in outputs["limitations"]:
            lines.append("Limitation: " + l)
        return "\n".join(lines)


# ---- persistence --------------------------------------------------------------------------------
def write_run(run: RunResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    run.trail.write_jsonl(out_dir / "audit.jsonl")
    data = {"mode": run.mode, "models": run.models, "totals": run.totals(), "gap_register": run.gap_register,
            "events": [{
                "seq": r.event.seq, "title": r.event.title, "at": r.event.at, "summary": r.summary,
                "escalations": r.escalations, "checks": r.checks,
                "consent": {k: d.to_dict() for k, d in r.consent.items()},
                "safety": {"summary": r.safety.summary, "explanations": r.safety.explanations,
                           "explanation_source": r.safety.explanation_source, "issues": r.safety.issues,
                           "findings": [asdict(f) for f in r.safety.assessment.findings],
                           "limitations": r.safety.limitations},
                "policy": asdict(r.policy) if r.policy else None} for r in run.results]}
    (out_dir / "run.json").write_text(json.dumps(data, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(run), encoding="utf-8")
    return out_dir


def render_report(run: RunResult) -> str:
    t = run.totals()
    label = ("LIVE run (real LLM; models: " + ", ".join(run.models) + ")" if run.mode == "live"
             else "MOCK run: LLM responses were scripted or replayed; NOT an observed live outcome")
    out = ["# Scenario run report", "", f"**{label}**", "",
           f"Totals: {t['pass']} pass, {t['fail']} fail, {t['review']} need human review, "
           f"{t['differs']} hypotheses not confirmed.", "",
           "Statuses: `pass`/`fail` are objective checks; `review` needs a human; `differs` means the agent did not "
           "confirm one of our written gap hypotheses.", ""]
    for r in run.results:
        out += [f"## Event {r.event.seq}: {r.event.title}", f"*{r.event.at}*", "", r.event.narrative, "",
                "| Area | Check | Expected | Actual | Status |", "|---|---|---|---|---|"]
        for c in r.checks:
            cell = lambda v: str(v).replace("|", "/").replace("\n", " ")[:110]
            out.append(f"| {c['area']} | {cell(c['description'])} | {cell(c['expected'])} | {cell(c['actual'])} | **{c['status']}** |")
        if r.escalations:
            out += ["", "**Escalated to a human:** " + "; ".join(e["reason"] for e in r.escalations)]
        if r.policy:
            p = r.policy
            out += ["", f"**Policy agent** ({len(p.searches)} searches, completed={p.completed})"]
            for key in ("requirements", "conflicts", "comparisons"):
                for item in getattr(p, key):
                    out.append(f"- *{key[:-1]}:* {item.get('statement') or item.get('description')} "
                               f"[{', '.join(item['citations'])}]")
            for g in p.gaps:
                out.append(f"- *gap ({g['type']}):* **{g['title']}**: {g['description']} [{', '.join(g['citations'])}]")
                if g.get("unretrieved_candidates"):
                    out.append("  - ⚠ passages the agent did not retrieve that may bear on this gap (verify before "
                               "accepting it): " + "; ".join(c["citation"] for c in g["unretrieved_candidates"]))
            for issue in p.issues:
                out.append(f"- ⚠ {issue}")
        if r.safety.issues:
            out += ["", "Safety agent issues: " + "; ".join(r.safety.issues)]
        out.append("")
    return "\n".join(out)
