# BUILD PROMPT: The Human Clause (policy-grounded medication-safety agents, UAE)

> Derived from `master-prompt.md` (kept as reference) and filtered through `competition.md`. This is the active spec. If they conflict, `competition.md` governs compliance and this file governs what we build.

## 1. Goal
Build a working prototype that wins the ITU AI for Good Lab Hackathon (UAE). Judges score: (1) policy KB quality, (2) agent capability in progressive failure scenarios, (3) policy/standards gap identification, (4) auditability, (5) ITU-T Y.3172 + AI Readiness alignment. Every build decision is checked against these five. A feature that serves none of them is cut.

## 2. Concept
A patient-controlled health-record and medication-safety system made of cooperating AI agents that act **within UAE policy**. When medications from different hospitals meet, agents detect safety issues *and* check what the law, institutional mandates and consent allow before acting. Where policy is silent, conflicting or ambiguous, the system says so, and that becomes the gap report.

Domain: healthcare / medication safety. Country grounding: UAE, with accurate international comparisons.

## 3. Agents (distinct mandates, explicit authority)
Round 1 uses **three agents**:
1. **Orchestrator**: a plain-Python coordinator (no LangGraph/LangChain). Deterministic code, not an LLM. Routes scripted events in order, hands each to the other agents, collects their independent assessments, and records every handoff in the audit log.
2. **Medication Safety Agent**: calls the deterministic engine (interactions, duplication, contraindications, renal/lab-aware checks). The LLM explains findings only; it never invents clinical facts.
3. **Policy & Legal Adviser Agent**: retrieves from the policy KB, returns requirements with citations, flags conflicts and unclear mandates, offers global comparisons only from ingested sources.

Consent and custody (grants with scope, expiry and revocation; per-hospital custody; what may be shared with whom) is a **deterministic module** the agents call as a tool, not a separate agent. Hospital A, Hospital B and the Regulator are simulated actors in the scenario data, each with a stated mandate and limited information.

Stretch, only if time allows: promote Consent & Data-Custodian and the institutions to full agents.

Each agent's authority and information boundary is written down in one place (`docs/agents.md`) and reflected in code.

## 4. Policy knowledge base (core deliverable)
- Collect **published, open UAE** documents: federal health-data/ICT-in-health law, federal personal-data protection law, UAE AI/digital strategies, relevant health-authority policies, relevant standards. The candidate list is verified against official sources before ingestion; **never cite an article, number or clause that was not actually ingested**.
- Add a small set of international comparators (e.g., EU, US) from ingested open texts only.
- Chunk by section/article. Each chunk stores: document, section, official URL, retrieval date, language, text.
- Retrieval: simple, inspectable hybrid (BM25 + optional embeddings). Every answer returns citations to chunks.
- Start from the organizers' reference code (CrashingGuru/ITUAIReadiness) where it saves time.
- Maintain `kb/MANIFEST.md` listing every document, source URL, and what it covers.

## 5. Medication-safety engine (kept, slimmed)
- Deterministic and unit-tested. Rules/data come from a small, clearly labelled **demonstration knowledge base** with provenance for each record (source, id, version, severity rationale). No fabricated references.
- Minimum: drug-drug interactions, therapeutic duplication, allergy/condition contraindications, renal-function-aware flags (eGFR), missing-data handling.
- Output types kept distinct: established / potential / patient-specific / uncertain / "no known issue in available KB" (never "safe").
- Safety boundaries: never tell patients to stop/start/change doses; escalate to clinician/pharmacist; the clinician decides.
- Synthetic data only (demo patient, 2-3 synthetic hospitals' records).

## 6. Progressive failure scenario (core deliverable)
Events are released one at a time; the agents see only what has arrived. Example "Fatima Hassan" case (final script to be refined with the team):
1. Prescriptions from Hospital A and B enter the record.
2. Safety agent flags an interaction; policy agent says what may be done and by whom.
3. A key lab result (eGFR) is late or missing, so the system must flag uncertainty, not guess.
4. Patient revokes consent for Hospital B mid-case; access and processing change; the audit shows it.
5. An urgent clinician request arrives; agents weigh emergency-access rules against consent; the conflict/ambiguity is recorded.
6. A cross-institution mandate is unclear (who owns the follow-up?); logged as a **policy gap** with evidence.

Each step has an **expected outcome** written beforehand and an **actual outcome** captured by an automated runner, producing a comparison table for the report and video.

## 7. Auditability
Append-only decision log: event, agent, inputs, policy chunks cited, rule checks run, decision summary, handoff. No raw hidden chain-of-thought; use auditable decision summaries, evidence references and rule-check traces. Viewable in the UI and exportable.

## 8. Gap report
Structured output (also generated from the run): gap, evidence (citations), domain relevance, international comparison, recommendation. A difference between countries is not automatically a gap.

## 9. ITU alignment (documented, not just named)
- **ITU-T Y.3172:** map components to the architecture (data sources, pipeline stages, model/policy functions, orchestration, sandbox/testing) with a table.
- **AI Readiness Framework:** map relevant dimensions to the design and evaluation.

Both tables feed the 5-page report. Verify against the actual documents before writing.

## 10. Scope
**In:** the 3 agents above (plus the consent module), policy KB + retrieval, safety engine, consent grants (scope/expiry/revoke/audit), document ingestion for a few synthetic documents (extract, then patient confirms), scenario runner, audit view, gap report, minimal clean UI (patient view, clinician view, agent/audit timeline).

**Out for round 1:** federated learning, adherence/reminders, real hospital integrations, user-management extras, 30+ pages, push notifications. Anything not built is stated as not built.

## 11. Stack (kept simple, local, runs in one command)
Python + FastAPI + Pydantic + SQLite (Postgres-ready), lightweight React (Vite) + Tailwind frontend. a provider-agnostic LLM layer targeting a **free provider** (candidates: Gemini free tier, Groq, OpenRouter free models, local Ollama), chosen after an early test of structured output and tool calling. No Claude API key is available. The layer has two modes:
- **mock**: scripted/cached LLM responses; the deterministic engine, retrieval, consent logic and scenario runner are fully testable without a key.
- **live**: real agents; outputs from real runs are cached as the offline demo fallback.

Report/video "actual outcomes" must come from live runs, and mock results must be labelled as mock. API keys via environment variables only, never committed. UI testing by `qa-tester` via Playwright (through Bash) or a browser tool.

## 12. Honesty rules
Never invent clinical facts, citations or metrics. Label demo data. Don't claim validation. Don't present unimplemented features as working. Treat uploaded documents as untrusted input.

## 13. Deliverables for submission (by 10 Nov 2026)
1. Technical report, max 5 pages, on the official template, covering the 8 FAQ items.
2. GitHub repo with README and one-command run instructions.
3. Policy KB with manifest.
4. Optional demo video, max 7 min: setup, main functions, expected vs actual outcomes.
5. The checklist at the end of `competition.md`, ticked honestly.

## 14. Working plan (3 days)
- **Day 1:** pick and smoke-test the free LLM provider, collect + ingest policy KB, safety engine + demo KB + tests, synthetic data, repo skeleton.
- **Day 2:** agents + orchestrator, consent logic, scenario runner, audit log, minimal UI.
- **Day 3:** run scenarios and record actual results, gap report, report writing (mappings), `qa-tester` pass, README, optional video, submit with buffer.

Parallel tracks (subagents/worktrees) only where files don't overlap: KB ingestion, safety engine, UI, report drafting. `qa-tester` runs after each major piece.

## 15. Rules for Claude
Work in small steps, report back after each, run tests after each module, ask when blocked, and never begin a new phase without confirmation.
