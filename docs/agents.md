# Agents: mandates, authority and information boundaries

Round 1 has **three agents** plus two deterministic modules. This file states what each may decide, what it can see, and what stops it from overreaching. It describes the code as built (`backend/agents/`, `backend/consent/`, `backend/safety/`).

## Summary

| Component | Type | Decides | Cannot do |
|---|---|---|---|
| Orchestrator | plain Python (no LLM) | order of work, who is asked, escalation to a human | judge medicine or law; alter agent output |
| Medication Safety Agent | LLM, explanation only | how a finding is worded for a lay reader | create, remove or re-grade a finding; advise stopping/starting/changing a medicine |
| Policy & Legal Adviser Agent | LLM + KB search tool | which retrieved provisions are relevant; whether a conflict, scope question or gap exists | cite anything it did not retrieve; give legal conclusions; claim a rule does not exist (only "not found in this KB") |
| Safety engine | deterministic rules + demo KB | which findings exist and their severity | use an LLM; assess unknown drugs (they are flagged) |
| Consent module | deterministic rules | whether a requester may see a category of a source's data now | decide legal questions; override an opt-out silently |

Simulated actors (Hospital A, Hospital B, Hospital C, regulator) are data in the scenario, not agents. Promoting them to agents is a stretch goal, not built.

## Orchestrator (`orchestrator.py`)
- **Mandate:** replay scenario events in order; make each agent see only what has arrived; collect their independent assessments; escalate; log every handoff.
- **Authority:** sequencing and escalation only. It escalates to a human whenever the consent module returns `escalate=True`. It never overrides either rule.
- **Information:** the event, the consent decisions, the engine's findings and limitations. It does **not** pass expected outcomes to any agent.
- **Records:** `event_arrived`, `consent_*`, `safety_engine_result`, `handoff`, `agent_result`, `escalation_to_human`, `llm_call`, `evaluation` in the audit trail.
- **Why not LangGraph/LangChain:** the flow is scripted and sequential; hand-written code makes the audit record exact and keeps the dependency list empty.

## Medication Safety Agent (`safety_agent.py`)
- **Mandate:** restate the engine's findings in calm, plain language, mention missing information, and point the patient to a doctor or pharmacist.
- **Authority:** wording only. Output is validated: unknown finding ids are ignored; text that tells a patient to stop, start, skip, increase or decrease a medicine is rejected (negated safe wording such as "do not stop..." is allowed); rejected or failed explanations fall back to the engine's own template text.
- **Information:** findings, patient factors, missing information, assessment limitations. No tools.
- **If the LLM is down:** the report is still produced from engine text, and the issue is logged.

## Policy & Legal Adviser Agent (`policy_agent.py`)
- **Mandate:** say what published rules say about a situation and where they conflict, leave scope unclear, or are silent.
- **Tool:** `search_policy(query, scope)` over the ingested KB (UAE federal, Dubai, Abu Dhabi, EU comparators, ITU references). Passages are returned in full.
- **Guards in code, not trust:** every citation must be a chunk it actually retrieved in that run (a near-identical typo of a retrieved id is repaired and logged); uncited statements are dropped; "no provision found" gaps carry the **real** search log and an independent list of passages the agent did not retrieve that may bear on the point; the agent is sent back once if it searches fewer than four times before answering.
- **Information:** the situation text, consent decisions (with reason codes and rule basis), engine findings, institutions and their emirates. It is never given expected outcomes or gap hypotheses.
- **Limits:** English text only (Arabic prevails legally); only documents in `kb/MANIFEST.md`; absence in the KB is not absence in law.

## Safety engine (`backend/safety/engine.py`)
Deterministic; findings come only from records in a **demonstration** knowledge base (team-curated, unverified, labelled as such, no external reference ids). "No known issue" is never presented as proof of safety. Missing lab values are reported as uncertain, never guessed.

## Consent module (`backend/consent/registry.py`)
Grants per (grantee, source, category, purpose) with expiry; revocation effective from its timestamp; exchange opt-out; break-the-glass only for clinicians with a written justification, always flagged for review; blocked and escalated when the patient has opted out of the source's exchange (configurable via `block_emergency_on_opt_out`). The block mirrors DHA Standards section 9.7; it is a configuration choice, **not a legal conclusion**. Every change and decision is appended to an immutable-by-API log.

## Human oversight
No component takes a clinical action. Outputs are advisory; blocked emergency requests and every safety finding go to a human. The prototype has no authentication, encryption or clinical validation and uses synthetic data only.
