"""Append-only audit trail shared by the orchestrator and the agents.

Records decisions, evidence references, rule-check traces and handoffs. It deliberately does NOT
record hidden model reasoning: only what each component received, did and produced.
"""
import json
import time
from pathlib import Path


class AuditTrail:
    def __init__(self):
        self._entries: list[dict] = []

    @property
    def entries(self) -> tuple:
        return tuple(self._entries)

    def add(self, kind: str, actor: str, event_seq: int, scenario_time: str, summary: str, **data) -> dict:
        entry = {"seq": len(self._entries) + 1, "wallclock": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "scenario_time": scenario_time, "event_seq": event_seq, "kind": kind, "actor": actor,
                 "summary": summary, **data}
        self._entries.append(entry)
        return entry

    def kinds(self) -> set:
        return {e["kind"] for e in self._entries}

    def for_event(self, event_seq: int) -> list[dict]:
        return [e for e in self._entries if e["event_seq"] == event_seq]

    def write_jsonl(self, path: Path) -> None:
        Path(path).write_text("\n".join(json.dumps(e, ensure_ascii=False, default=str) for e in self._entries) + "\n",
                              encoding="utf-8")
