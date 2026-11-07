# Evaluation results

Source run: `20261108-005651-live` (live mode; models: gemini-3.1-flash-lite).

**Totals:** 42 checks pass, 5 fail, 12 need human review, 1 hypothesis not confirmed. `review` items are free-text expectations or gap matches that code cannot judge.

| # | Event | Expected (written beforehand) | Actual (from the run) | Pass / fail / review / differs |
|---|---|---|---|---|
| 1 | Baseline records arrive from Hospitals A and C | findings: MISSING:DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002<br>consent: C_reads_A_meds→GRANTED | findings: MISSING:DEMO-LAB-001:glucophage (informational)<br>consent: C_reads_A_meds→GRANTED | 8 / 0 / 1 / 0 |
| 2 | Hospital B (Dubai) prescribes spironolactone | findings: DEMO-INT-002, MISSING:DEMO-LAB-002:aldactone, MISSING:DEMO-LAB-001:glucophage<br>consent: A_reads_B_meds→GRANTED, B_reads_A_meds→GRANTED<br>gap hypotheses: GAP-CONSENT-REGIME-DIVERGENCE | findings: DEMO-INT-002 (high), MISSING:DEMO-LAB-001:glucophage (informational), MISSING:DEMO-LAB-002:aldactone (informational)<br>consent: A_reads_B_meds→GRANTED, B_reads_A_meds→GRANTED<br>policy agent: 2 searches, 7 requirements, 0 conflicts, gaps: Lack of explicit rules on cross-emirate HIE interoperability | 8 / 2 / 1 / 1 |
| 3 | Overdue lab results arrive three days late | findings: DEMO-LAB-001:glucophage, DEMO-LAB-002:aldactone, DEMO-INT-002<br>absent: MISSING:DEMO-LAB-001:glucophage, MISSING:DEMO-LAB-002:aldactone | findings: DEMO-INT-002 (high), DEMO-LAB-001:glucophage (high), DEMO-LAB-002:aldactone (high) | 7 / 0 / 1 / 0 |
| 4 | Patient withdraws consent for Hospital B's data and opts out of NABIDH | findings: DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002, DEMO-LAB-002:aldactone<br>consent: A_reads_B_meds_direct→REVOKED, A_reads_B_meds_exchange→OPTED_OUT_OF_EXCHANGE<br>gap hypotheses: GAP-CONSENT-REGIME-DIVERGENCE | findings: DEMO-LAB-001:glucophage (high)<br>consent: A_reads_B_meds_direct→REVOKED, A_reads_B_meds_exchange→OPTED_OUT_OF_EXCHANGE<br>policy agent: 2 searches, 4 requirements, 0 conflicts, gaps: Applicability of Opt-Out to Abu Dhabi (Malaffi) | 11 / 0 / 3 / 0 |
| 5 | Emergency: clinician at Hospital A requests Hospital B's medication list | findings: DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002<br>consent: ED_btg_B_meds→EMERGENCY_BLOCKED_BY_OPT_OUT<br>gap hypotheses: GAP-CROSS-EMIRATE-EMERGENCY-ACCESS | findings: DEMO-LAB-001:glucophage (high)<br>consent: ED_btg_B_meds→EMERGENCY_BLOCKED_BY_OPT_OUT<br>escalated to a human<br>policy agent: 3 searches, 3 requirements, 1 conflicts, gaps: Cross-emirate emergency access procedures | 5 / 3 / 3 / 0 |
| 6 | Who owns the follow-up? | findings: DEMO-LAB-001:glucophage<br>absent: DEMO-INT-002<br>gap hypotheses: GAP-CROSS-INSTITUTION-RESPONSIBILITY | findings: DEMO-LAB-001:glucophage (high)<br>policy agent: 7 searches, 0 requirements, 0 conflicts, gaps: Responsibility for cross-emirate clinical coordination; Impact of patient-withheld data on clinical responsibility | 3 / 0 / 3 / 0 |

### Review of checks that were not a pass

Expectations were written before any agent existed and were **not changed** after the run. Failures and non-confirmations were reviewed by the team against the source text:

| Event | Check | Status | Review |
|---|---|---|---|
| 2 | cites uae-health-ict-law-2019 ('confidentiality of health data') | fail | Valid alternative. The agent cited texts that restate the confidentiality rule (DHA 4.7 cites Art. 16 of the ICT Health Law) instead of Art. 4. Our expectation was too narrow. |
| 2 | cites dha-health-info-sharing-2024 ('Consent must be obtained') | fail | Valid alternative. The agent cited another provision of the same DHA policy that makes sharing depend on patient consent (4.6, table of care-purpose sharing). |
| 2 | GAP-CONSENT-REGIME-DIVERGENCE: hypothesis | differs | Confirmed at a different event. At event 2 the agent raised a related interoperability gap (how a consent in one emirate's exchange is recognised in another). It raised the opt-out divergence itself at event 4 ("Applicability of Opt-Out to Abu Dhabi (Malaffi)"), which matches the team's full-text scan. |
| 5 | cites uae-health-ict-law-2019 ('health and safety of the patient') | fail | Valid alternative. The agent cited Executive Regulation Art. 6(3), which expressly covers emergency access to a patient file with reasons: arguably a closer match than Art. 16(3). |
| 5 | cites dha-consent-access-standard-2025 ('emergency condition') | fail | Valid alternative. The agent cited the DHA break-the-glass definition and Abu Dhabi's break-the-seal provision (DoH 6.1.4) instead of DHA 17.2.1; the Abu Dhabi rule was not in our script. |
| 5 | cites dha-consent-access-standard-2025 ('Emirate of Dubai') | fail | Partly met. The agent raised the cross-emirate scope question as a gap but did not cite DHA 2.1; it did cite DHA 9.7 and the federal provision. |
