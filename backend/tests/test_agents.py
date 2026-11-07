"""Agent and orchestrator tests with a scripted mock LLM (offline, free)."""
import json

import pytest

from backend.agents.orchestrator import Orchestrator, render_report, write_run
from backend.agents.policy_agent import MAX_ROUNDS, PolicyAgent
from backend.agents.safety_agent import SafetyAgent
from backend.kb.retrieve import KnowledgeBase
from backend.llm.client import LLMClient, MockMiss
from backend.safety.engine import Medication, Patient, SafetyEngine


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase()


def assessment_with_findings():
    p = Patient(conditions=["chronic kidney disease"],
                medications=[Medication("Coumadin", "A"), Medication("Advil", "B")])
    return SafetyEngine().assess(p)


# ---------------------------------------------------------------- safety agent
def test_safety_agent_uses_valid_llm_explanations():
    a = assessment_with_findings()
    fid = a.findings[0].finding_id
    llm = LLMClient(mode="mock", mock_responses=[{"summary": "Two things to review.",
                    "explanations": [{"finding_id": fid, "plain_language": "These two medicines together raise bleeding risk."}]}])
    r = SafetyAgent(llm).run(a)
    assert r.explanation_source[fid] == "llm" and r.summary == "Two things to review."
    others = [f.finding_id for f in a.findings if f.finding_id != fid]
    assert all(r.explanation_source[o] == "template" for o in others)


def test_safety_agent_rejects_unknown_ids_and_forbidden_advice():
    a = assessment_with_findings()
    fid = a.findings[0].finding_id
    llm = LLMClient(mode="mock", mock_responses=[{"summary": "ok", "explanations": [
        {"finding_id": "INVENTED-1", "plain_language": "A made-up interaction."},
        {"finding_id": fid, "plain_language": "You should stop taking warfarin today."}]}])
    r = SafetyAgent(llm).run(a)
    assert r.explanation_source[fid] == "template"
    assert "stop taking" not in r.explanations[fid].lower()
    assert "INVENTED-1" not in r.explanations
    assert len(r.issues) == 2


def test_safety_agent_falls_back_to_engine_text_when_llm_fails():
    a = assessment_with_findings()
    r = SafetyAgent(LLMClient(mode="mock")).run(a)  # no script, no cache -> MockMiss
    assert set(r.explanation_source.values()) == {"template"} and r.issues


def test_safety_agent_makes_no_llm_call_without_findings():
    a = SafetyEngine().assess(Patient(medications=[Medication("lisinopril", "A")]))
    calls = []
    llm = LLMClient(mode="mock", mock_responses=lambda req: calls.append(req))
    SafetyAgent(llm).run(a)
    assert calls == []


# ---------------------------------------------------------------- policy agent
def tool_msg_ids(messages):
    ids = []
    for m in messages:
        if m.get("role") == "tool":
            ids += [h["chunk_id"] for h in json.loads(m["content"])]
    return ids


def test_policy_agent_keeps_only_retrieved_citations_and_real_search_log(kb):
    def script(req):
        if not any(m.get("role") == "tool" for m in req["messages"]):
            return {"tool_calls": [{"id": "t1", "name": "search_policy",
                                    "arguments": {"query": "health data outside the state", "scope": "UAE federal"}}]}
        real = tool_msg_ids(req["messages"])[0]
        return {"requirements": [{"statement": "Storage abroad is restricted.", "citations": [real, "fake#9999"]},
                                 {"statement": "Uncited claim.", "citations": ["fake#1"]}],
                "conflicts": [], "comparisons": [],
                "gaps": [{"title": "No owner", "type": "no_provision_found", "description": "Nothing found.",
                          "citations": [], "recommendation": "Clarify."},
                         {"title": "Shaky", "type": "conflict", "description": "Unsupported.", "citations": ["fake#2"],
                          "recommendation": ""}],
                "caveats": ["KB only"]}
    r = PolicyAgent(LLMClient(mode="mock", mock_responses=script), kb).run(5, "q", "ctx")
    assert r.completed and len(r.searches) == 1 and r.searches[0]["scope"] == "UAE federal"
    assert r.requirements[0]["citations"] == [r.searches[0]["results"][0]]
    assert not any("Uncited" in x["statement"] for x in r.requirements)
    no_prov = next(g for g in r.gaps if g["type"] == "no_provision_found")
    assert no_prov["searched_queries"] == ["health data outside the state"]  # real log, not the model's claim
    assert next(g for g in r.gaps if g["title"] == "Shaky")["unsupported"] is True
    assert any("fake#9999" in i for i in r.issues)


def test_policy_agent_stops_searching_after_budget_and_asks_for_final_answer(kb):
    seen = {"final_without_tools": 0}

    def script(req):
        if req["tools"]:
            return {"tool_calls": [{"id": "t", "name": "search_policy", "arguments": {"query": "consent"}}]}
        seen["final_without_tools"] += 1
        return {"requirements": [], "conflicts": [], "gaps": [], "comparisons": [], "caveats": ["done"]}
    r = PolicyAgent(LLMClient(mode="mock", mock_responses=script), kb).run(2, "q", "ctx")
    assert r.completed and len(r.searches) == MAX_ROUNDS and seen["final_without_tools"] == 1


def test_policy_agent_reports_incomplete_when_llm_unavailable(kb):
    r = PolicyAgent(LLMClient(mode="mock"), kb).run(2, "q", "ctx")
    assert not r.completed and r.issues and not r.requirements


def test_invalid_search_scope_is_ignored(kb):
    def script(req):
        if not any(m.get("role") == "tool" for m in req["messages"]):
            return {"tool_calls": [{"id": "t", "name": "search_policy", "arguments": {"query": "consent", "scope": "Narnia"}}]}
        return {"requirements": [], "conflicts": [], "gaps": [], "comparisons": [], "caveats": []}
    r = PolicyAgent(LLMClient(mode="mock", mock_responses=script), kb).run(2, "q", "ctx")
    assert r.searches[0]["scope"] == "" and r.searches[0]["results"]


# ---------------------------------------------------------------- orchestrator end to end
QUERIES = {  # event -> [(query, scope)] the scripted policy agent searches
    2: [("keep confidentiality of health data circulate cases other than permitted", "UAE federal"),
        ("consent must be obtained before sharing PHI", "Dubai"),
        ("universal patient participation mandatory", "Abu Dhabi")],
    4: [("right to withdraw and opt-out of exchange", "Dubai"),
        ("withdrawal of consent should not affect sharing already carried out may retain information", "Dubai")],
    5: [("health and safety of the patient exception written approval", "UAE federal"),
        ("opted out PHI should not be retrieved using BTG access", "Dubai"),
        ("break the glass emergency condition serious threat", "Dubai"),
        ("scope all PHI within the Emirate of Dubai entities under DHA", "Dubai")],
}


def scripted_llm():
    def script(req):
        system = req["messages"][0]["content"]
        if "Medication Safety Agent" in system:
            items = json.loads(req["messages"][1]["content"].split("Findings:\n")[1].split("\nLimitations")[0])
            return {"summary": "Scripted summary.", "explanations": [
                {"finding_id": i["finding_id"], "plain_language": f"Plain: {i['what']}"} for i in items]}
        event = int(req["messages"][1]["content"].split("Event ")[1].split(" ")[0])
        has_tool = any(m.get("role") == "tool" for m in req["messages"])
        if not has_tool and event in QUERIES:
            return {"tool_calls": [{"id": f"t{i}", "name": "search_policy", "arguments": {"query": q, "scope": s}}
                                   for i, (q, s) in enumerate(QUERIES[event])]}
        ids = sorted(set(tool_msg_ids(req["messages"])))
        gaps = []
        if event == 5:
            gaps = [{"title": "Emergency access across emirates", "type": "conflict", "description": "Provisions pull apart.",
                     "citations": ids[:6], "recommendation": "Clarify"}]
        if event == 4:
            gaps = [{"title": "Different consent regimes", "type": "conflict", "description": "Differ.",
                     "citations": ids[:6], "recommendation": "Align"}]
        if event == 6:
            gaps = [{"title": "No owner for follow-up", "type": "no_provision_found", "description": "None found.",
                     "citations": [], "recommendation": "Assign"}]
        return {"requirements": [{"statement": "See cited passages.", "citations": ids}] if ids else [],
                "conflicts": [], "comparisons": [], "gaps": gaps, "caveats": ["Scripted"]}
    return LLMClient(mode="mock", mock_responses=script)


@pytest.fixture(scope="module")
def run():
    return Orchestrator(scripted_llm()).run(progress=lambda s: None)


def test_objective_safety_consent_and_audit_checks_all_pass(run):
    bad = [(r.event.seq, c) for r in run.results for c in r.checks
           if c["area"] in ("safety", "consent", "audit") and c["status"] != "pass"]
    assert not bad, bad


def test_scripted_policy_citations_satisfy_must_cite(run):
    cites = [c for r in run.results for c in r.checks if c["area"] == "policy" and c["description"].startswith("cites")]
    assert cites and all(c["status"] == "pass" for c in cites), [c for c in cites if c["status"] != "pass"]


def test_human_review_items_are_never_auto_passed(run):
    reviews = [c for r in run.results for c in r.checks if c["area"] in ("policy", "gap") and c["status"] == "review"]
    assert reviews and not any(c["status"] == "pass" for c in run.results[3].checks if c["description"].startswith("expectation"))


def test_event_5_is_escalated_to_a_human_and_logged(run):
    r5 = run.results[4]
    assert r5.escalations and "opted out" in r5.escalations[0]["reason"]
    assert any(e["kind"] == "escalation_to_human" and e["event_seq"] == 5 for e in run.trail.entries)


def test_handoffs_llm_calls_and_evaluations_are_in_the_audit_trail(run):
    kinds = [e["kind"] for e in run.trail.entries]
    assert kinds.count("event_arrived") == 6 and kinds.count("evaluation") == 6
    assert kinds.count("handoff") == 6 + 4  # safety every event, policy on 4 events
    assert kinds.count("llm_call") > 6
    assert [e["seq"] for e in run.trail.entries] == list(range(1, len(kinds) + 1))


def test_policy_agent_only_runs_where_there_is_a_question(run):
    assert [r.policy is not None for r in run.results] == [False, True, False, True, True, True]


def test_gap_register_collects_agent_gaps_with_event_numbers(run):
    assert {g["event_seq"] for g in run.gap_register} >= {4, 5, 6}
    g6 = next(g for g in run.gap_register if g["event_seq"] == 6)
    assert g6["type"] == "no_provision_found" and "not proof" in g6["note"]


def test_mock_run_is_labelled_as_not_a_live_outcome(run):
    assert run.mode == "mock" and "NOT an observed live outcome" in render_report(run)


def test_run_artifacts_are_written(run, tmp_path):
    out = write_run(run, tmp_path / "r")
    assert (out / "report.md").exists() and (out / "audit.jsonl").exists()
    data = json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert data["mode"] == "mock" and len(data["events"]) == 6
    assert len((out / "audit.jsonl").read_text(encoding="utf-8").splitlines()) == len(run.trail.entries)


def test_orchestrator_survives_total_llm_outage():
    r = Orchestrator(LLMClient(mode="mock")).run(progress=lambda s: None)  # every LLM call raises MockMiss
    assert all(not x.policy.completed for x in r.results if x.policy)
    safety_fail = [c for x in r.results for c in x.checks if c["area"] in ("safety", "consent") and c["status"] == "fail"]
    assert not safety_fail  # deterministic parts are unaffected by the LLM being down
    assert r.totals()["fail"] > 0  # but missing policy citations are reported as failures, not hidden


# ---------------------------------------------------------------- regression tests from the first live run
def test_negated_safe_advice_is_allowed_but_real_advice_is_rejected():
    from backend.agents.safety_agent import gives_forbidden_advice as bad
    assert not bad("Please discuss this with your doctor. Do not stop taking your medicine on your own.")
    assert not bad("Do not stop your medicine on your own.") and not bad("Never skip the doctor's advice.")
    assert bad("You should stop taking warfarin today.") and bad("Stop the tablets now.")
    assert bad("Double your dose tomorrow.") and bad("Start taking aspirin.")


def test_policy_agent_is_sent_back_once_when_it_searches_too_little(kb):
    calls = {"n": 0, "pushback_seen": False}

    def script(req):
        calls["n"] += 1
        calls["pushback_seen"] |= any("only 1 search" in str(m.get("content")) for m in req["messages"])
        if calls["n"] == 1:
            return {"tool_calls": [{"id": "t1", "name": "search_policy", "arguments": {"query": "consent"}}]}
        return {"requirements": [], "conflicts": [], "gaps": [], "comparisons": [], "caveats": []}
    r = PolicyAgent(LLMClient(mode="mock", mock_responses=script), kb).run(2, "q", "ctx")
    assert calls["pushback_seen"] and any("Sent back once" in i for i in r.issues)
    assert calls["n"] == 3  # search, premature answer, accepted answer (only one push-back)


def test_search_results_give_the_agent_the_full_passage(kb):
    seen = {}

    def script(req):
        tools = [m for m in req["messages"] if m.get("role") == "tool"]
        if not tools:
            return {"tool_calls": [{"id": "t", "name": "search_policy",
                                    "arguments": {"query": "opted out patient PHI retrieved using BTG access", "scope": "Dubai"}}]}
        seen["text"] = " ".join(h["text"] for h in json.loads(tools[0]["content"]))
        return {"requirements": [], "conflicts": [], "gaps": [], "comparisons": [], "caveats": []}
    PolicyAgent(LLMClient(mode="mock", mock_responses=script), kb).run(5, "q", "ctx")
    assert "should not be retrieved using BTG" in seen["text"]  # section 9.7 sits late in its chunk


def test_absence_claims_get_an_independent_check(kb):
    def script(req):
        if not any(m.get("role") == "tool" for m in req["messages"]):
            return {"tool_calls": [{"id": "t", "name": "search_policy", "arguments": {"query": "unrelated tax rules"}}]}
        return {"requirements": [], "conflicts": [], "comparisons": [], "caveats": [],
                "gaps": [{"title": "Emergency access for opted-out patients",
                          "type": "no_provision_found",
                          "description": "No rule on break the glass access for opted out patients found.",
                          "citations": [], "recommendation": ""}]}
    r = PolicyAgent(LLMClient(mode="mock", mock_responses=script), kb).run(5, "q", "ctx")
    gap = r.gaps[0]
    assert gap["unretrieved_candidates"], "reviewer must be shown passages the agent never retrieved"
    assert all(c["chunk_id"] not in r.searches[0]["results"] for c in gap["unretrieved_candidates"])


def test_reference_list_chunks_are_not_returned_for_ordinary_queries(kb):
    for h in kb.search("break the glass emergency access", k=10):
        assert h["text"].count("http") < 4


def test_citation_typo_is_repaired_only_when_unambiguous_and_retrieved(kb):
    def script(req):
        tools = [m for m in req["messages"] if m.get("role") == "tool"]
        if not tools:
            return {"tool_calls": [{"id": "t", "name": "search_policy",
                                    "arguments": {"query": "break the seal emergency Abu Dhabi", "scope": "Abu Dhabi"}}]}
        real = json.loads(tools[0]["content"])[0]["chunk_id"]
        typo = real.replace("doh-", "dha-", 1) if real.startswith("doh-") else "x" + real
        return {"requirements": [{"statement": "Emergency break-the-seal rule.", "citations": [typo]},
                                 {"statement": "Unrelated.", "citations": ["eu-gdpr-2016-679#9999"]}],
                "conflicts": [], "gaps": [], "comparisons": [], "caveats": []}
    r = PolicyAgent(LLMClient(mode="mock", mock_responses=script), kb).run(5, "q", "ctx")
    assert len(r.requirements) == 1 and r.requirements[0]["citations"][0] in r.searches[0]["results"]
    assert any("Repaired citation typo" in i for i in r.issues)
    assert any("Dropped uncited requirement" in i for i in r.issues)  # the genuinely invented one is still dropped
