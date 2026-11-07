"""Policy & Legal Adviser Agent.

Mandate: answer "what do the rules say?" for a situation, using ONLY the ingested policy KB through a
search tool, and report conflicts, unclear scope and gaps. It gives no legal conclusions.

Guards enforced in code (not by trusting the model):
  - every citation must be a chunk_id that this agent actually retrieved in this run;
  - statements that end up with no valid citation are dropped (recorded as issues);
  - "no provision found" gaps are attached to the REAL list of searches performed;
  - absence in the KB is never presented as absence in law.
"""
import json
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from backend.kb.retrieve import KnowledgeBase
from backend.llm.client import LLMClient, LLMError

MAX_ROUNDS = 6
MIN_SEARCHES = 4  # below this, the agent is sent back once before it may conclude
SCOPES = ["UAE federal", "Dubai", "Abu Dhabi", "EU", "ITU"]
GAP_TYPES = {"conflict", "scope_unclear", "no_provision_found", "ambiguity"}

TOOL = {"type": "function", "function": {
    "name": "search_policy",
    "description": "Search the ingested policy knowledge base (UAE federal law, Dubai DHA, Abu Dhabi DoH, EU "
                   "comparators, ITU references). Returns up to 5 passages with chunk_id and citation.",
    "parameters": {"type": "object", "properties": {
        "query": {"type": "string", "description": "Plain-language search query"},
        "scope": {"type": "string", "enum": [""] + SCOPES,
                  "description": "Optional jurisdiction filter; empty searches everything"}},
        "required": ["query"]}}}

SYSTEM = (
    "You are the Policy & Legal Adviser Agent in a health-data safety prototype set in the UAE. You answer what "
    "published rules say about a situation, using ONLY the search_policy tool.\n"
    "Rules:\n"
    "- Search before answering, as many times as needed. Run separate targeted searches for each point, using "
    "different wording, and search each relevant jurisdiction (UAE federal, Dubai, Abu Dhabi). Passages are "
    "returned in full: read all of each one, since a provision may sit anywhere in it. Do not rely on memory.\n"
    "- Cite ONLY chunk_ids returned by your searches. Quote or paraphrase only what the passage says.\n"
    "- Report conflicts between provisions, unclear jurisdictional scope, and ambiguities. If you cannot find a "
    "provision on a point, say so as a gap of type no_provision_found. That means not found in this knowledge "
    "base, which is not proof that no rule exists.\n"
    "- Give no legal conclusions or advice. State what the texts say and where they leave a question open.\n"
    "- Use EU or ITU passages only as clearly labelled comparisons.\n"
    "When finished, reply with ONLY JSON of this shape:\n"
    "{\"requirements\":[{\"statement\":str,\"citations\":[chunk_id]}],"
    "\"conflicts\":[{\"description\":str,\"citations\":[chunk_id]}],"
    "\"gaps\":[{\"title\":str,\"type\":\"conflict|scope_unclear|no_provision_found|ambiguity\","
    "\"description\":str,\"citations\":[chunk_id],\"recommendation\":str}],"
    "\"comparisons\":[{\"statement\":str,\"citations\":[chunk_id]}],\"caveats\":[str]}")


@dataclass
class PolicyReport:
    event_seq: int
    question: str
    requirements: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    gaps: list[dict] = field(default_factory=list)
    comparisons: list[dict] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    searches: list[dict] = field(default_factory=list)  # real tool calls: query, scope, result chunk ids
    issues: list[str] = field(default_factory=list)
    completed: bool = True

    def cited_chunk_ids(self) -> set:
        ids = set()
        for group in (self.requirements, self.conflicts, self.gaps, self.comparisons):
            for item in group:
                ids.update(item.get("citations", []))
        return ids


class PolicyAgent:
    name = "policy_agent"

    def __init__(self, llm: LLMClient, kb: KnowledgeBase):
        self.llm, self.kb = llm, kb

    # ---- tool ----------------------------------------------------------------------------
    def _search(self, query: str, scope: str, report: PolicyReport, retrieved: set) -> str:
        hits = self.kb.search(query, k=5, scope=scope or None)
        retrieved.update(h["chunk_id"] for h in hits)
        report.searches.append({"query": query, "scope": scope, "results": [h["chunk_id"] for h in hits]})
        return json.dumps([{"chunk_id": h["chunk_id"], "citation": h["citation"], "scope": h["scope"],
                            "text": h["text"]} for h in hits], ensure_ascii=False)

    # ---- main ----------------------------------------------------------------------------
    def run(self, event_seq: int, question: str, context: str) -> PolicyReport:
        report = PolicyReport(event_seq, question)
        retrieved: set[str] = set()
        messages = [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": f"Situation:\n{context}\n\nQuestion: {question}"}]
        final, pushed_back = None, False
        try:
            for _ in range(MAX_ROUNDS):
                resp = self.llm.complete(messages, tools=[TOOL], agent=self.name)
                if not resp.tool_calls:
                    if len(report.searches) < MIN_SEARCHES and not pushed_back:
                        pushed_back = True
                        report.issues.append(f"Sent back once: only {len(report.searches)} search(es) before answering")
                        messages.append(resp.as_message())
                        messages.append({"role": "user", "content": (
                            f"You have run only {len(report.searches)} search(es). Before answering, run further "
                            "targeted searches with different wording, covering each relevant jurisdiction (UAE "
                            "federal, Dubai, Abu Dhabi). Do not conclude that a provision is missing until you have "
                            "searched for it from several angles.")})
                        continue
                    final = resp
                    break
                messages.append(resp.as_message())
                for call in resp.tool_calls:
                    args = call["arguments"] if isinstance(call["arguments"], dict) else {}
                    scope = args.get("scope", "") if args.get("scope", "") in SCOPES else ""
                    result = self._search(str(args.get("query", "")), scope, report, retrieved)
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
            parsed = None
            if final is not None:
                parsed = self._try_parse(final.content)
            if parsed is None:  # budget used up, or the model did not return JSON: ask once, no tools
                if final is not None:
                    messages.append(final.as_message())
                messages.append({"role": "user", "content":
                                 "Give your final answer now as ONLY the JSON object described, using what you "
                                 "have retrieved. Do not search again."})
                resp = self.llm.complete(messages, json_mode=True, agent=self.name, validate=self._shape)
                parsed = resp.parsed
        except (LLMError, ValueError) as e:
            report.completed = False
            report.issues.append(f"Policy agent did not complete: {e}")
            return report
        self._ingest(report, parsed, retrieved)
        return report

    # ---- validation ----------------------------------------------------------------------
    def _try_parse(self, text: str):
        from backend.llm.client import _strip_fences
        try:
            return self._shape(json.loads(_strip_fences(text)))
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

    @staticmethod
    def _shape(d):
        if not isinstance(d, dict):
            raise ValueError("expected a JSON object")
        for key in ("requirements", "conflicts", "gaps", "comparisons", "caveats"):
            if not isinstance(d.get(key, []), list):
                raise ValueError(f"'{key}' must be a list")
        return d

    def _clean_citations(self, item: dict, retrieved: set, report: PolicyReport, label: str) -> list[str]:
        good = []
        for cid in item.get("citations", []) or []:
            if cid in retrieved and self.kb.get(cid):
                good.append(cid)
                continue
            # Typo repair: accept only if exactly one RETRIEVED id is a near-identical spelling of it.
            near = [r for r in retrieved if r.split("#")[-1] == str(cid).split("#")[-1]
                    and SequenceMatcher(None, r, str(cid)).ratio() >= 0.9]
            if len(near) == 1:
                good.append(near[0])
                report.issues.append(f"Repaired citation typo {cid!r} -> {near[0]!r} in {label} (retrieved this run)")
            else:
                report.issues.append(f"Removed citation {cid!r} from {label}: not retrieved in this run")
        return good

    def _ingest(self, report: PolicyReport, parsed: dict, retrieved: set) -> None:
        for key, text_key in (("requirements", "statement"), ("conflicts", "description"),
                              ("comparisons", "statement")):
            for item in parsed.get(key, []):
                if not isinstance(item, dict) or not str(item.get(text_key, "")).strip():
                    continue
                cites = self._clean_citations(item, retrieved, report, key)
                if not cites:
                    report.issues.append(f"Dropped uncited {key[:-1]}: {str(item[text_key])[:80]!r}")
                    continue
                getattr(report, key).append({text_key: str(item[text_key]).strip(), "citations": cites})
        for item in parsed.get("gaps", []):
            if not isinstance(item, dict) or not str(item.get("description", "")).strip():
                continue
            gtype = item.get("type") if item.get("type") in GAP_TYPES else "ambiguity"
            cites = self._clean_citations(item, retrieved, report, "gap")
            gap = {"title": str(item.get("title", "")).strip(), "type": gtype,
                   "description": str(item["description"]).strip(), "citations": cites,
                   "recommendation": str(item.get("recommendation", "")).strip()}
            if gtype == "no_provision_found":
                gap["searched_queries"] = [s["query"] for s in report.searches]  # real log, not the model's claim
                gap["note"] = "Not found in the ingested knowledge base; this is not proof that no rule exists."
                # Independent check of the absence claim: passages that may bear on it but the agent never retrieved.
                nearest = self.kb.search(f"{gap['title']} {gap['description']}", k=5)
                gap["unretrieved_candidates"] = [
                    {"chunk_id": h["chunk_id"], "citation": h["citation"]} for h in nearest
                    if h["chunk_id"] not in retrieved][:3]
            elif not cites:
                gap["unsupported"] = True
                report.issues.append(f"Gap {gap['title']!r} of type {gtype} has no valid citation (marked unsupported)")
            report.gaps.append(gap)
        report.caveats = [str(c) for c in parsed.get("caveats", []) if str(c).strip()]
