"""Append-only audit trail shared by the orchestrator and the agents.

Records decisions, evidence references, rule-check traces and handoffs. It deliberately does NOT
record hidden model reasoning: only what each component received, did and produced.
"""
import hashlib
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
        """Write the trail as JSON lines, sealed as a hash chain (see `seal`)."""
        plain = [json.loads(json.dumps(e, ensure_ascii=False, default=str)) for e in self._entries]
        write_sealed(plain, path)


GENESIS = "0" * 64


def _digest(entry: dict, prev_hash: str) -> str:
    body = {k: v for k, v in entry.items() if k not in ("hash", "prev_hash")}
    canon = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256((prev_hash + canon).encode("utf-8")).hexdigest()


def seal(entries: list[dict], genesis: str = GENESIS) -> list[dict]:
    """Add `prev_hash` and `hash` to every entry. Each hash covers the entry and the previous hash, so
    editing, deleting, reordering or inserting any entry breaks every hash after it. This makes tampering
    DETECTABLE; it does not prevent it (someone who rewrites the whole chain can reseal it).
    `genesis` lets a second chain (e.g. human reviews) start from another chain's head hash."""
    out, prev = [], genesis
    for e in entries:
        body = {k: v for k, v in e.items() if k not in ("hash", "prev_hash")}
        h = _digest(body, prev)
        out.append({**body, "prev_hash": prev, "hash": h})
        prev = h
    return out


def write_sealed(entries: list[dict], path: Path, genesis: str = GENESIS) -> None:
    Path(path).write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in seal(entries, genesis)) + "\n",
                          encoding="utf-8")


def head_hash(entries: list[dict]) -> str:
    return entries[-1]["hash"] if entries and "hash" in entries[-1] else ""


def verify(entries: list[dict], genesis: str = GENESIS, expected_head: str = "") -> dict:
    """Check a trail. Returns {status: ok|broken|unsealed, entries, first_bad_seq, message}.
    If `expected_head` (recorded elsewhere, e.g. in run.json) is given, entries cut off the end are detected too."""
    if not entries:
        return {"status": "unsealed", "entries": 0, "first_bad_seq": None, "message": "empty trail"}
    if not any("hash" in e for e in entries):
        return {"status": "unsealed", "entries": len(entries), "first_bad_seq": None,
                "message": "no hashes present: integrity cannot be checked"}
    prev = genesis
    for i, e in enumerate(entries):
        if e.get("prev_hash") != prev or e.get("hash") != _digest(e, prev):
            return {"status": "broken", "entries": len(entries), "first_bad_seq": e.get("seq", i + 1),
                    "message": f"chain breaks at entry {e.get('seq', i + 1)}: content or order was changed"}
        prev = e["hash"]
    if expected_head and prev != expected_head:
        return {"status": "broken", "entries": len(entries), "first_bad_seq": None,
                "message": "head hash differs from the one recorded in run.json: entries were removed from the end or the log was replaced"}
    return {"status": "ok", "entries": len(entries), "first_bad_seq": None,
            "message": f"{len(entries)} entries, chain intact (head {prev[:12]}...)"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8-sig").splitlines() if l.strip()]


def _recorded_head(audit_path) -> str:
    """Head hash stored in run.json next to the audit file, if any."""
    f = Path(audit_path).with_name("run.json")
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("audit_head_hash", "")
    except (OSError, ValueError):
        return ""


def _store_head(audit_path) -> None:
    f = Path(audit_path).with_name("run.json")
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        d["audit_head_hash"] = head_hash(read_jsonl(audit_path))
        f.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="python -m backend.agents.audit")
    ap.add_argument("command", choices=["verify", "seal"])
    ap.add_argument("file")
    a = ap.parse_args(argv)
    entries = read_jsonl(a.file)
    if a.command == "seal":
        write_sealed(entries, a.file)
        _store_head(a.file)
        print(f"sealed {len(entries)} entries in {a.file}")
        return 0
    r = verify(entries, expected_head=_recorded_head(a.file))
    print(f"{r['status'].upper()}: {r['message']}")
    return 0 if r["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
