# The Human Clause

Policy-grounded medication-safety agents for the **ITU AI for Good Lab Hackathon: United Arab Emirates (2026)**.

When a patient's medications from different hospitals meet, the system does two things. It detects the safety issue. It also checks what UAE law, institutional mandates and patient consent allow before acting. Where policy is silent, conflicting or ambiguous, the system says so, and that becomes the gap report.

> **Demo data only.** All patients, hospitals and prescriptions are synthetic. The medication-safety knowledge base is a team-curated demonstration set and has not been clinically reviewed. This is not a medical device and gives no clinical advice.

## What it does

A progressive failure scenario ("Fatima Hassan") releases six events one at a time, and the agents see only what has arrived:

1. Prescriptions from two hospitals enter the record.
2. The safety agent flags an interaction, and the policy agent says what may be done and by whom.
3. A key lab result (eGFR) is missing, so the system flags uncertainty instead of guessing.
4. The patient revokes consent for one hospital mid-case.
5. An urgent clinician request arrives, and emergency-access rules are weighed against consent.
6. A cross-institution mandate is unclear (who owns the follow-up?), and it is logged as a policy gap.

Each step has an expected outcome written beforehand and an actual outcome captured by an automated runner. The runner compares the two.

## Architecture

| Component | Location | Role |
| --- | --- | --- |
| Orchestrator | `backend/agents/orchestrator.py` | Plain-Python, deterministic (no LLM, no agent framework). Routes events, collects independent assessments, logs every handoff. |
| Medication Safety Agent | `backend/agents/safety_agent.py` | Calls the deterministic engine. The LLM only explains findings and never invents clinical facts. |
| Policy & Legal Adviser Agent | `backend/agents/policy_agent.py` | Searches the policy KB, returns requirements with citations, flags conflicts and unclear mandates. |
| Safety engine | `backend/safety/` | Interactions, duplication, contraindications, eGFR-aware flags. Unit-tested. |
| Consent module | `backend/consent/` | Grants with scope and expiry, revocation, opt-out, break-the-glass. Called as a tool, not an agent. |
| Policy KB + retrieval | `kb/`, `backend/kb/` | Chunked UAE, EU and ITU documents with BM25 retrieval. See [kb/MANIFEST.md](kb/MANIFEST.md). |
| LLM layer | `backend/llm/` | Provider-agnostic, with mock and live modes and an on-disk response cache. |
| Audit trail | `backend/agents/audit.py` | Append-only log of events, inputs, citations, rule checks and decision summaries, sealed as a SHA-256 hash chain so edits are detectable. It records no hidden chain-of-thought. |
| Report generator | `backend/report/` | Builds the gap report and the ITU-T Y.3172 and AI Readiness mappings from the recorded run. |

Agent authority and information boundaries are in [docs/agents.md](docs/agents.md).

## Quick start

Requires Python 3.13. The tests also need `pytest` (`pip install pytest`).

```powershell
pip install -r backend/requirements.txt
copy .env.example .env

# Run the tests (offline, no API key needed)
python -m pytest backend/tests

# Run the scenario with no network (mock mode: replays the cache, otherwise agents fall back)
python -m backend.run_scenario --mode mock
```

Runs are written to `data/runs/<timestamp>-<mode>/` as `audit.jsonl`, `run.json` and `report.md`.

On Windows, if `python` opens the Microsoft Store, use `py -3` instead.

### Audit integrity

Every `audit.jsonl` is written as a hash chain: each entry's hash covers its content and the previous hash. Check a run with:

```powershell
python -m backend.agents.audit verify data/runs/20261108-005651-live/audit.jsonl
```

This detects edited, deleted, inserted or reordered entries. It does not detect entries cut off the end of the log, and someone who rewrites the whole chain can reseal it, so it is tamper-evident, not tamper-proof. `seal` adds hashes to an older unsealed file.

### Offline demo viewer

Open [docs/demo/index.html](docs/demo/index.html) in a browser. It replays the recorded live run and calls no model. It has five pages:

- **Overview:** headline results, who does what, and the six events.
- **Scenario:** step through the events and open each event's findings, consent decisions, policy citations, expected vs actual checks and audit entries.
- **Results:** pass, fail, review and differs counts per event.
- **Gaps:** the policy and standards gap report with evidence.
- **Audit:** the full audit trail with filters, the chain integrity result, and a JSONL export.

Rebuild it with `python -m backend.viewer.build_viewer`.

### Live mode

Edit `.env` and set `LLM_MODE=live`, `LLM_PROVIDER`, `LLM_API_KEY` and `LLM_MODEL` (see `.env.example`). Never commit `.env`.

```powershell
python backend/scripts/llm_smoke_test.py      # check structured output and tool calling
python -m backend.run_scenario --mode live    # real agents; responses are cached
```

To replay the committed recorded run offline, keep `LLM_MODEL=gemini-3.5-flash`. The cache key includes the configured primary model name, so changing it invalidates the cache.

### Rebuild the knowledge base and report

```powershell
python backend/kb/ingest.py                   # raw documents -> kb/chunks/
python -m backend.report.build                # report material -> docs/report/
npm install docx --no-save
python -m backend.report.export_docx          # -> docs/report/The-Human-Clause-technical-report.docx
```

The report build fails if any citation phrase is missing from the ingested KB.

## Recorded results

The final recorded live run is `data/runs/20261108-005651-live`: 42 pass, 5 fail, 12 review, 1 differs. It was served entirely by the fallback model `gemini-3.1-flash-lite`, because the primary model's free-tier quota was exhausted. Every non-pass result is adjudicated in `backend/report/content.py`. Its audit log was sealed with hashes after the run; the entries themselves are unchanged. Mock-mode results are labelled as mock and are not used as evidence.

## Documentation

- [docs/build-prompt.md](docs/build-prompt.md): active spec
- [docs/competition.md](docs/competition.md): competition brief and checklist
- [docs/decisions.md](docs/decisions.md): decision log
- [docs/report/](docs/report/): technical report, mappings, gap report and evaluation

## Limitations (not built)

- No FastAPI service or React UI. The demo is a command-line runner plus a static HTML viewer of a recorded run.
- No federated learning, adherence reminders or real hospital integrations.
- The KB uses English text only, and Arabic prevails legally. Some sources may be superseded (for example the 2020 Abu Dhabi HIE policy). Abu Dhabi's AI policy could not be downloaded and is not ingested.
- The audit log is tamper-evident, not tamper-proof: there is no protected storage, authentication or encryption.
- The medication-safety demo KB is unverified by a clinician or pharmacist.
- Independent validation, appeals and an accountability agreement (DHA AI policy 4.2-4.4) are not met.
