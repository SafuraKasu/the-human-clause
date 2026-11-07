# The Human Clause: policy-grounded medication-safety agents for the UAE

*DRAFT built from `backend/report/build.py`. Every citation and number below is machine-checked. Trim to the official template (max 5 pages) before submitting.*

## 1. Introduction to the agentic solution

The Human Clause is a prototype in which cooperating AI agents help keep a patient's medications safe across several hospitals **and** check what UAE law, institutional mandates and the patient's consent allow before anything is shown or shared. Where the rules conflict, leave scope unclear or are silent, the system says so, and that becomes a documented policy gap.

It has three agents (Orchestrator, Medication Safety, Policy & Legal Adviser) and two deterministic modules (a safety rule engine and a consent module). The Orchestrator is plain Python. The Safety agent only explains findings that the engine produced. The Policy agent searches a knowledge base of 14 published documents and may cite only passages it actually retrieved. Roles and limits are in `docs/agents.md`. All patient data is synthetic.

## 2. Use case

Healthcare, medication safety. Fatima Hassan, 72 (synthetic), has kidney disease, diabetes, hypertension and atrial fibrillation, a penicillin allergy, and prescriptions from three hospitals: A and C in Abu Dhabi and B in Dubai. No hospital sees the others' prescriptions unless she allows it. The scenario releases six events one at a time (new prescriptions, late lab results, withdrawal of consent, an emergency request, an unclear mandate) so the system must act on incomplete and changing information.

## 3. Requirements

- **R1** Share a patient's medication data across hospitals only on the patient's authority, per category and purpose, with expiry.
- **R2** Honour withdrawal of consent and opt-out from a health information exchange, and say so when an assessment becomes incomplete.
- **R3** Detect medication-safety issues deterministically (interactions, duplication, contraindications, lab-dependent rules), never guess missing data, never present 'no issue found' as proof of safety.
- **R4** Handle emergency access under explicit rules: allowed only with justification, always flagged, escalated to a human when rules conflict.
- **R5** Ground every policy statement in a retrievable source passage; report conflicts, unclear scope and gaps honestly.
- **R6** Keep an inspectable audit trail of decisions, evidence, rule checks and handoffs (no hidden reasoning).
- **R7** Keep AI supervised: advisory only, overridable by humans, no clinical action taken automatically.
- **R8** Respect data-location limits: no real patient data leaves the State; the prototype uses synthetic data only.

## 4. Mapping to ITU-T Y.3172

| Y.3172 component | Role in Y.3172 | Human Clause counterpart | Status |
|---|---|---|---|
| SRC / C (source, collector) | SRC is the source of pipeline input data; C collects from SRC nodes. | Hospital A/B/C record uploads and late lab results (synthetic) are the sources; `ScenarioState` ingests them. | **simulated** |
| PP (preprocessor) | Cleans or aggregates data into a form the ML model can consume. | Brand-to-ingredient normalization, status filtering, and consent-based exclusion of withdrawn sources before any assessment. | **implemented** |
| M (model) | The ML model usable in the pipeline. | No trained ML model. A deterministic rule engine (demo KB) makes safety findings; an LLM (Gemini free tier) explains findings and reasons over retrieved policy text. | **partial** |
| P (policy) | Applies policies to the model's output before it is acted on. | Consent module and Policy agent decide what outputs may be used or shown; blocked emergency requests are escalated, not overridden. | **implemented** |
| D / SINK (distributor, sink) | D identifies sinks and distributes the output; SINK takes action on it. | Orchestrator routes results to patient-facing wording, clinician review and human escalation. The sink is a human decision; nothing acts automatically. | **implemented** |
| MLFO (orchestrator) | Manages and orchestrates pipeline nodes from ML Intent; selects and reselects the model, e.g. by performance. | Plain-Python Orchestrator sequences nodes and logs handoffs. The LLM client reselects a fallback model on failure; it does not select by measured performance. | **partial** |
| ML Intent | Describes the ML application, its data needs, constraints and characteristics; input to the MLFO. | Scenario definition (events, expected outcomes) plus written agent mandates in `docs/agents.md` play this role informally; there is no formal metalanguage. | **partial** |
| ML sandbox subsystem | Lets operators study ML outputs on simulated underlay networks before deploying live. | Scenario replay with synthetic hospitals, mock and live LLM modes, and expected-versus-actual evaluation. Nothing is deployed live. | **implemented** |
| Management subsystem | Extends network management and orchestration to the ML pipeline nodes. | Append-only audit trail and evaluator record what each node did. No resource or lifecycle management. | **partial** |
| Security considerations | Prevent unauthorized access to, and data leaking from, an ML pipeline. | Consent module and audit log; citation guards against invented sources. Not implemented: authentication, encryption, tamper-proof log storage. Synthetic data only. | **partial** |

*Y.3172 addresses machine learning in future networks (IMT-2020). We apply its pipeline concepts by analogy to a health-data agent system; the mapping explains how our architecture corresponds to it and does not claim network-level conformance.*

## 5. Mapping to the ITU AI Readiness Framework 2.0

| Event-page lens | Framework mapping | How addressed | Status |
|---|---|---|---|
| Open data and open-source management | Factors: Open Data, Open source. Dimension 1 (Data/model Marketplace); Data Governance metrics. | Policy KB built only from published open documents with a manifest of sources and retrieval dates; source code in the repository. Demo medication KB is team-curated and unverified. No bias audit of data (synthetic). | **partial** |
| Generative AI content ecosystem | Dimension 2 (Generated Content Marketplace). | LLM-written explanations are validated against deterministic findings, labelled by origin (llm or template) in the output, and rejected if they give forbidden advice. | **partial** |
| Contextualization and regional development | Dimension 4 (Contextualization and Regional Impact); Dimension 12 (Granular Priorities). | Grounded in UAE federal, Dubai and Abu Dhabi rules, and designed around differences between emirates. English text only; Arabic originals prevail legally. | **partial** |
| Domain-specific and cross-domain AI integration | Dimension 5 (Level of Integration of AI in Workflows); Dimension 3 (Cross-domain correlation analysis). | Joins healthcare medication safety, data-protection law and AI-governance policy in one pipeline across three institutions. Not integrated with real hospital systems. | **partial** |
| Human interaction and supervision | Dimension 6 (Human Interface); Dimension 8 (Collaboration with AI); Dimension 9 (Impacts of Humans in AI Integration). | Plain-language explanations; advisory output only; blocked or conflicting cases escalate to a human; no automatic clinical action. | **implemented** |
| AI policy and implementation opportunities | Dimension 10 (AI & Policies); Dimension 7 (Strategy Alignment); Factors: Standards, Sandbox. | Core of the project: a policy KB, a Policy agent with citation guards, progressive scenarios, and a gap report. The UAE AI Strategy 2031 is ingested but not yet exercised by the scenario. | **implemented** |
| AI for social inclusion | Dimension 11 (AI for Inclusion). | Not addressed beyond plain-language wording. No Arabic interface or content, no accessibility work. | **not implemented** |
| Digital infrastructure and energy considerations | Dimension 13 (Digital Infrastructure). | Runs on a laptop plus a free cloud LLM. Compute, energy and connectivity requirements were not measured. | **not implemented** |

## 6. Mapping of requirements to local policies

| Requirement | Provisions (verified in ingested text) | Implementation | Status |
|---|---|---|---|
| R1 Consent-based sharing | Federal ICT Health Law Art. 16; DHA Health Information Sharing Policy 4.8.5; DoH HIE Policy 4.2.1.2 | Consent module: grants per grantee, source, category and purpose, with expiry; every decision logged. | **implemented** |
| R2 Withdrawal and opt-out | DHA Consent Standard 9.3; DHA Consent Standard 9.4 | Revocation effective from its timestamp; exchange opt-out; withdrawn sources excluded from assessment with a limitation notice. Earlier lawful sharing is not erased. | **implemented** |
| R3 Confidentiality of health data | Federal ICT Health Law Art. 4 | Category-level access control; outputs only to authorised requesters. No encryption in the prototype. | **partial** |
| R3 Minimum necessary sharing | DHA Health Information Sharing Policy 4.5.5 | Grants are limited to data categories (medications, labs, allergies, conditions). No field-level minimisation. | **partial** |
| R4 Emergency access | Executive Regulation Art. 6(3); Federal ICT Health Law Art. 16(3); DHA Consent Standard 17.2.1; DoH HIE Policy 6.1.4; DHA Consent Standard 9.7 (limit) | Break-the-glass needs a clinician and a written justification and is always flagged; blocked and escalated when the patient opted out of the source's exchange. See gap G2. | **implemented** |
| R6 Audit and logging | DHA Consent Standard 17.6; DoH HIE Policy 6.1.3.13 | Append-only consent log and orchestration audit trail, exported as JSON lines. Immutability is by API only; storage is not tamper-proof. | **partial** |
| R7 AI supervised and overridable | DHA AI Policy 4.4.1; DHA AI Policy 4.4.2 | Advisory only; no automatic action; escalation to a human. Override is implicit (nothing is enforced), not a built feature. | **implemented** |
| R7 Accountability and appeals (not met) | DHA AI Policy 4.2.1; DHA AI Policy 4.2.3 | Agent mandates are documented, but there is no accountability agreement and no appeals procedure. | **not implemented** |
| R7 Independent validation (not met) | DHA AI Policy 4.3.3 | No independent validation. Safety rules are a team-curated demonstration KB, not clinically validated. | **not implemented** |
| R8 Data location | Federal ICT Health Law Art. 13; DHA AI Policy 4.6.2 | Synthetic data only. The live LLM runs outside the UAE, so real patient data could not be sent to it without a lawful exception or an in-country model. See gap G4. | **partial** |

## 7. Evaluation scenario (technical and policy)

Source run: `20261108-003623-live` (live mode; models: gemini-3.5-flash, gemini-3.1-flash-lite).

**Totals:** 42 checks pass, 5 fail, 12 need human review, 1 hypothesis not confirmed. `review` items are free-text expectations or gap matches that code cannot judge.

| # | Event | Expected (written beforehand) | Actual (from the run) | Pass / fail / review / differs |
|---|---|---|---|---|
| 1 | Baseline records arrive from Hospitals A and C | findings: MISSING:DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002<br>consent: C_reads_A_meds→GRANTED | findings: MISSING:DEMO-LAB-001:glucophage (informational)<br>consent: C_reads_A_meds→GRANTED | 8 / 0 / 1 / 0 |
| 2 | Hospital B (Dubai) prescribes spironolactone | findings: DEMO-INT-002, MISSING:DEMO-LAB-002:aldactone, MISSING:DEMO-LAB-001:glucophage<br>consent: A_reads_B_meds→GRANTED, B_reads_A_meds→GRANTED<br>gap hypotheses: GAP-CONSENT-REGIME-DIVERGENCE | findings: DEMO-INT-002 (high), MISSING:DEMO-LAB-001:glucophage (informational), MISSING:DEMO-LAB-002:aldactone (informational)<br>consent: A_reads_B_meds→GRANTED, B_reads_A_meds→GRANTED<br>policy agent: 3 searches, 4 requirements, 0 conflicts, gaps: Uniformity of Consent Requirements | 8 / 2 / 2 / 0 |
| 3 | Overdue lab results arrive three days late | findings: DEMO-LAB-001:glucophage, DEMO-LAB-002:aldactone, DEMO-INT-002<br>absent: MISSING:DEMO-LAB-001:glucophage, MISSING:DEMO-LAB-002:aldactone | findings: DEMO-INT-002 (high), DEMO-LAB-001:glucophage (high), DEMO-LAB-002:aldactone (high) | 7 / 0 / 1 / 0 |
| 4 | Patient withdraws consent for Hospital B's data and opts out of NABIDH | findings: DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002, DEMO-LAB-002:aldactone<br>consent: A_reads_B_meds_direct→REVOKED, A_reads_B_meds_exchange→OPTED_OUT_OF_EXCHANGE<br>gap hypotheses: GAP-CONSENT-REGIME-DIVERGENCE | findings: DEMO-LAB-001:glucophage (high)<br>consent: A_reads_B_meds_direct→REVOKED, A_reads_B_meds_exchange→OPTED_OUT_OF_EXCHANGE<br>policy agent: 2 searches, 4 requirements, 0 conflicts, gaps: Specific Opt-out/Withdrawal Procedures for Malaffi (Abu Dhabi) | 11 / 0 / 2 / 1 |
| 5 | Emergency: clinician at Hospital A requests Hospital B's medication list | findings: DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002<br>consent: ED_btg_B_meds→EMERGENCY_BLOCKED_BY_OPT_OUT<br>gap hypotheses: GAP-CROSS-EMIRATE-EMERGENCY-ACCESS | findings: DEMO-LAB-001:glucophage (high)<br>consent: ED_btg_B_meds→EMERGENCY_BLOCKED_BY_OPT_OUT<br>escalated to a human<br>policy agent: 3 searches, 3 requirements, 1 conflicts, gaps: Cross-emirate emergency access procedures | 5 / 3 / 3 / 0 |
| 6 | Who owns the follow-up? | findings: DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002<br>gap hypotheses: GAP-CROSS-INSTITUTION-RESPONSIBILITY | findings: DEMO-LAB-001:glucophage (high)<br>policy agent: 8 searches, 0 requirements, 0 conflicts, gaps: Responsibility for cross-emirate clinical coordination; Impact of patient-withheld data on clinical responsibility | 3 / 0 / 3 / 0 |

### Review of checks that were not a pass

Expectations were written before any agent existed and were **not changed** after the run. Failures and non-confirmations were reviewed by the team against the source text:

| Event | Check | Status | Review |
|---|---|---|---|
| 2 | cites uae-health-ict-law-2019 ('confidentiality of health data') | fail | Valid alternative. The agent cited texts that restate the confidentiality rule (DHA 4.7 cites Art. 16 of the ICT Health Law) instead of Art. 4. Our expectation was too narrow. |
| 2 | cites dha-health-info-sharing-2024 ('Consent must be obtained') | fail | Valid alternative. The agent cited another provision of the same DHA policy that makes sharing depend on patient consent (4.6, table of care-purpose sharing). |
| 4 | GAP-CONSENT-REGIME-DIVERGENCE: hypothesis | differs | Not a miss. The agent raised the divergence at event 2; event 4's question concerned the effect of withdrawal, which it answered with DHA 9.3 and 9.4. |
| 5 | cites uae-health-ict-law-2019 ('health and safety of the patient') | fail | Valid alternative. The agent cited Executive Regulation Art. 6(3), which expressly covers emergency access to a patient file with reasons: arguably a closer match than Art. 16(3). |
| 5 | cites dha-consent-access-standard-2025 ('emergency condition') | fail | Valid alternative. The agent cited the DHA break-the-glass definition and Abu Dhabi's break-the-seal provision (DoH 6.1.4) instead of DHA 17.2.1; the Abu Dhabi rule was not in our script. |
| 5 | cites dha-consent-access-standard-2025 ('Emirate of Dubai') | fail | Partly met. The agent raised the cross-emirate scope question as a gap but did not cite DHA 2.1; it did cite DHA 9.7 and the federal provision. |

## 8. Policy and standards gaps found

### G1: Patients in different emirates get different consent and opt-out rights

Dubai's 2025 standard gives patients a right to withdraw and opt out of the health information exchange. Abu Dhabi's 2020 exchange policy makes participation mandatory, authorizes sharing where consent is unavailable, and contains no opt-out provision (full-text scan: zero hits). The federal data-protection law's general right to withdraw consent cannot be assumed to fill the gap, because it excludes personal health data that has its own regulating legislation.

**Evidence:** DHA Consent Standard 9.3; DoH HIE Policy 4.2 (mandatory participation); DoH HIE Policy 4.2.1.2 (sharing without consent); PDPL Art. 6(2) (general withdrawal right); PDPL Art. 2(2)(e) (health data exclusion)

**Full-text scan results (computed at build time):** occurrences of 'opt-out' in the Abu Dhabi HIE policy: **0**

**International comparison:** EHDS Art. 10(1)

**Why it matters here:** A patient treated in both emirates, as in our scenario, cannot predict whether an opt-out or withdrawal will be honoured.

**Recommendation:** Publish a federal or inter-emirate rule on whether and how an opt-out registered in one emirate binds exchanges in another.

**Origin:** Hypothesis written before the run; the agent raised a closely related gap at event 2 (cross-emirate consent synchronization). Verified by the team in the source text.

**Caveats:** The Abu Dhabi policy is from April 2020 and may have been superseded. English text only.

### G2: Emergency access to an opted-out patient's records across emirates is unresolved

The Dubai standard says an opted-out patient's data should not be retrieved by break-the-glass. The federal Executive Regulation and the ICT Health Law allow access in an emergency or to protect the patient's health and safety, and Abu Dhabi has its own 'break the seal' rule. The Dubai standard's scope is PHI within Dubai. No ingested provision says which rule governs a clinician in one emirate requesting an opted-out patient's data held in another.

**Evidence:** DHA Consent Standard 9.7; DHA Consent Standard 2.1 (scope); Executive Regulation Art. 6(3); Federal ICT Health Law Art. 16(3); DoH HIE Policy 6.1.4

**International comparison:** EHDS Art. 10(2)

**Why it matters here:** Our scenario's event 5: an unconscious, bleeding patient whose opt-out blocks the clinician who needs her full medication list. The system blocked and escalated to a human.

**Recommendation:** State, in federal guidance, whether an opt-out can be overridden for vital interests and which emirate's emergency rule applies to cross-emirate requests. The EU resolves the same question explicitly in EHDS Art. 10.

**Origin:** Hypothesis written before the run. The agent independently found the conflict and the scope question at event 5 and cited Executive Regulation Art. 6(3) and the Abu Dhabi provision, which we had not scripted. Verified by the team.

**Caveats:** Whether the emergency block is the right behavior is a legal question; the consent module's setting is a configuration choice, not a conclusion.

### G3: No ingested provision assigns responsibility for cross-institution follow-up

No ingested UAE text assigns responsibility for coordinating follow-up on high-severity medication findings that span prescribers in different emirates. Full-text scans find no 'medication reconciliation' or 'responsible for coordinating' anywhere. The nearest provisions concern exchange interoperability and referral data, not who acts on a finding.

**Evidence:** DoH HIE Policy (objective: interoperability for coordination of care); DoH Circular 2026/144 (referral data)

**Full-text scan results (computed at build time):** occurrences of 'medication reconciliation' across all ingested UAE texts: **0**; occurrences of 'responsible for coordinating' across all ingested UAE texts: **0**

**International comparison:** EHDS Art. 20 (authority-level coordination only)

**Why it matters here:** Our scenario's event 6: three prescribers in two emirates, two high-severity findings, and no stated owner.

**Recommendation:** Define which institution (for example the most recent prescriber or the patient's primary care provider) owns the response to a cross-institution medication-safety finding.

**Origin:** Hypothesis written before the run; confirmed by the agent after eight searches, with the team's full-text scans as an independent check.

**Caveats:** Absence in the ingested documents is not proof that no rule exists elsewhere. The EU comparator concerns reporting by digital health authorities, not clinical responsibility.

### G4: No ingested provision addresses externally hosted AI processing of health data

The ICT Health Law restricts storing or processing health data outside the State unless a Health Authority resolution allows it. The Dubai AI policy requires AI solutions to comply with that law but never mentions cloud, location or localization (full-text scan: zero hits), and the instrument that lists exceptions (Ministerial Decision 51 of 2021) is not in our KB. Whether an externally hosted LLM can lawfully process real patient data is therefore not answered by the ingested texts.

**Evidence:** Federal ICT Health Law Art. 13; DHA AI Policy 4.6.2

**Full-text scan results (computed at build time):** occurrences of outside/cloud/localization in the Dubai AI policy: **0**

**Why it matters here:** This prototype uses a cloud LLM on synthetic data only. A real deployment would need an in-country model or a lawful exception.

**Recommendation:** Clarify how Art. 13 applies to AI services hosted abroad, and publish the exceptions in one place alongside the AI policies.

**Origin:** Identified in the team's own review, not raised by the agent.

**Caveats:** Ministerial Decision 51 of 2021 and the Abu Dhabi AI policy and Responsible AI Standard are not ingested (the Abu Dhabi files could not be downloaded). This gap is limited to the texts we hold.

## Limitations and honest status

- The medication knowledge base is a **small team-curated demonstration set** (4 interactions, 2 contraindications, 2 lab rules, 13 ingredients), not clinically validated and not reviewed by a clinician.
- No independent validation, authentication, encryption or tamper-proof logging; no real hospital integration; synthetic data only.
- The policy KB holds English text only (Arabic originals prevail legally). Not ingested: Abu Dhabi's AI policy and Responsible AI Standard (download failed), and Ministerial Decision 51 of 2021.
- The language model is a free-tier Gemini model; outputs vary between runs, so results come from a recorded run that is replayable from cache.
- Policy findings are retrieval-based summaries of what the texts say, not legal advice. Absence in the KB is not absence in law.
