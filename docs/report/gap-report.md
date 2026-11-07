# Policy and standards gap report

Every quoted phrase is verified against the ingested text at build time.

### G1: Patients in different emirates get different consent and opt-out rights

Dubai's 2025 standard gives patients a right to withdraw and opt out of the health information exchange. Abu Dhabi's 2020 exchange policy makes participation mandatory, authorizes sharing where consent is unavailable, and contains no opt-out provision (full-text scan: zero hits). The federal data-protection law's general right to withdraw consent cannot be assumed to fill the gap, because it excludes personal health data that has its own regulating legislation.

**Evidence:** DHA Consent Standard 9.3 `dha-consent-access-standard-2025#0018`; DoH HIE Policy 4.2 (mandatory participation) `doh-hie-policy-2020#0021`; DoH HIE Policy 4.2.1.2 (sharing without consent) `doh-hie-policy-2020#0021`; PDPL Art. 6(2) (general withdrawal right) `uae-pdpl-2021#0010`; PDPL Art. 2(2)(e) (health data exclusion) `uae-pdpl-2021#0005`

**Full-text scan results (computed at build time):** occurrences of 'opt-out' in the Abu Dhabi HIE policy: **0**

**International comparison:** EHDS Art. 10(1) `eu-ehds-2025-327#0094`

**Why it matters here:** A patient treated in both emirates, as in our scenario, cannot predict whether an opt-out or withdrawal will be honoured.

**Recommendation:** Publish a federal or inter-emirate rule on whether and how an opt-out registered in one emirate binds exchanges in another.

**Origin:** Hypothesis written before the run; the agent raised a closely related gap at event 2 (cross-emirate consent synchronization). Verified by the team in the source text.

**Caveats:** The Abu Dhabi policy is from April 2020 and may have been superseded. English text only.

### G2: Emergency access to an opted-out patient's records across emirates is unresolved

The Dubai standard says an opted-out patient's data should not be retrieved by break-the-glass. The federal Executive Regulation and the ICT Health Law allow access in an emergency or to protect the patient's health and safety, and Abu Dhabi has its own 'break the seal' rule. The Dubai standard's scope is PHI within Dubai. No ingested provision says which rule governs a clinician in one emirate requesting an opted-out patient's data held in another.

**Evidence:** DHA Consent Standard 9.7 `dha-consent-access-standard-2025#0018`; DHA Consent Standard 2.1 (scope) `dha-consent-access-standard-2025#0011`; Executive Regulation Art. 6(3) `uae-health-ict-exec-reg-2020#0007`; Federal ICT Health Law Art. 16(3) `uae-health-ict-law-2019#0019`; DoH HIE Policy 6.1.4 `doh-hie-policy-2020#0054`

**International comparison:** EHDS Art. 10(2) `eu-ehds-2025-327#0094`

**Why it matters here:** Our scenario's event 5: an unconscious, bleeding patient whose opt-out blocks the clinician who needs her full medication list. The system blocked and escalated to a human.

**Recommendation:** State, in federal guidance, whether an opt-out can be overridden for vital interests and which emirate's emergency rule applies to cross-emirate requests. The EU resolves the same question explicitly in EHDS Art. 10.

**Origin:** Hypothesis written before the run. The agent independently found the conflict and the scope question at event 5 and cited Executive Regulation Art. 6(3) and the Abu Dhabi provision, which we had not scripted. Verified by the team.

**Caveats:** Whether the emergency block is the right behavior is a legal question; the consent module's setting is a configuration choice, not a conclusion.

### G3: No ingested provision assigns responsibility for cross-institution follow-up

No ingested UAE text assigns responsibility for coordinating follow-up on high-severity medication findings that span prescribers in different emirates. Full-text scans find no 'medication reconciliation' or 'responsible for coordinating' anywhere. The nearest provisions concern exchange interoperability and referral data, not who acts on a finding.

**Evidence:** DoH HIE Policy (objective: interoperability for coordination of care) `doh-hie-policy-2020#0037`; DoH Circular 2026/144 (referral data) `doh-circular-2026-144-malaffi-referrals#0001`

**Full-text scan results (computed at build time):** occurrences of 'medication reconciliation' across all ingested UAE texts: **0**; occurrences of 'responsible for coordinating' across all ingested UAE texts: **0**

**International comparison:** EHDS Art. 20 (authority-level coordination only) `eu-ehds-2025-327#0107`

**Why it matters here:** Our scenario's event 6: three prescribers in two emirates, two high-severity findings, and no stated owner.

**Recommendation:** Define which institution (for example the most recent prescriber or the patient's primary care provider) owns the response to a cross-institution medication-safety finding.

**Origin:** Hypothesis written before the run; confirmed by the agent after eight searches, with the team's full-text scans as an independent check.

**Caveats:** Absence in the ingested documents is not proof that no rule exists elsewhere. The EU comparator concerns reporting by digital health authorities, not clinical responsibility.

### G4: No ingested provision addresses externally hosted AI processing of health data

The ICT Health Law restricts storing or processing health data outside the State unless a Health Authority resolution allows it. The Dubai AI policy requires AI solutions to comply with that law but never mentions cloud, location or localization (full-text scan: zero hits), and the instrument that lists exceptions (Ministerial Decision 51 of 2021) is not in our KB. Whether an externally hosted LLM can lawfully process real patient data is therefore not answered by the ingested texts.

**Evidence:** Federal ICT Health Law Art. 13 `uae-health-ict-law-2019#0016`; DHA AI Policy 4.6.2 `dha-ai-policy-2021#0009`

**Full-text scan results (computed at build time):** occurrences of outside/cloud/localization in the Dubai AI policy: **0**

**Why it matters here:** This prototype uses a cloud LLM on synthetic data only. A real deployment would need an in-country model or a lawful exception.

**Recommendation:** Clarify how Art. 13 applies to AI services hosted abroad, and publish the exceptions in one place alongside the AI policies.

**Origin:** Identified in the team's own review, not raised by the agent.

**Caveats:** Ministerial Decision 51 of 2021 and the Abu Dhabi AI policy and Responsible AI Standard are not ingested (the Abu Dhabi files could not be downloaded). This gap is limited to the texts we hold.
