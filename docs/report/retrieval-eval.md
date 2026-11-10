# Retrieval evaluation (top 5)

20 questions. A case is a *hit* when one of the top 5 chunks is from the expected document and contains the expected phrase. Questions were written by the team, who know the KB, so results are optimistic; this is a small sample, not a benchmark.

| | Passage recall | Document recall | MRR |
|---|---|---|---|
| Whole KB, no filter | 70% | 90% | 0.604 |
| With jurisdiction scope | 75% | 100% | 0.654 |

| Question | Scope | Expected | Rank (no filter) | Rank (scoped) |
|---|---|---|---|---|
| May a hospital send a patient's health data to a cloud server in another country? | UAE federal | `uae-health-ict-law-2019` “outside State” | miss | miss |
| Can a doctor see a patient's record without written consent if the patient's life is at risk? | UAE federal | `uae-health-ict-law-2019` “health and safety of the patient” | miss | 1 |
| Who is allowed to access a patient's health file in an emergency under the executive regulation? | UAE federal | `uae-health-ict-exec-reg-2020` “emergency” | 1 | 1 |
| Does the federal data protection law cover health data that has its own legislation? | UAE federal | `uae-pdpl-2021` “health” | 1 | 1 |
| What does the UAE national AI strategy say about government use of AI? | UAE federal | `uae-ai-strategy-2031` “government” | 1 | 1 |
| Can a Dubai patient withdraw from health information sharing? | Dubai | `dha-consent-access-standard-2025` “right to withdraw” | 4 | 4 |
| Can emergency break-the-glass access override a patient's opt-out in Dubai? | Dubai | `dha-consent-access-standard-2025` “should not be retrieved using BTG” | miss | miss |
| How long does a patient's consent stay valid after their last visit? | Dubai | `dha-consent-access-standard-2025` “one year” | 1 | 1 |
| What audit trail must be kept of who accessed patient information? | Dubai | `dha-consent-access-standard-2025` “audit trail” | 1 | 1 |
| When can health information be shared between Dubai health facilities? | Dubai | `dha-health-info-sharing-2024` “Consent must be obtained” | miss | miss |
| Must AI systems in Dubai healthcare be supervised by a human and overridable? | Dubai | `dha-ai-policy-2021` “supervised/monitored” | 1 | 1 |
| Is patient participation in the Abu Dhabi health information exchange mandatory? | Abu Dhabi | `doh-hie-policy-2020` “Universal” | 1 | 1 |
| Can Abu Dhabi share patient data when consent is not available? | Abu Dhabi | `doh-hie-policy-2020` “without” | miss | miss |
| How must emergency access to a sealed record be handled in Abu Dhabi? | Abu Dhabi | `doh-hie-policy-2020` “seal” | 3 | 3 |
| Must log files of the health information exchange be protected from alteration? | Abu Dhabi | `doh-hie-policy-2020` “cannot be altered” | 1 | 1 |
| Which categories of personal data need extra protection under EU law? | EU | `eu-gdpr-2016-679` “special categories” | 1 | 1 |
| Does a patient have the right to have their data erased? | EU | `eu-gdpr-2016-679` “erasure” | 2 | 2 |
| Can EU citizens opt out of the European Health Data Space? | EU | `eu-ehds-2025-327` “opt” | 1 | 1 |
| What does ITU-T Y.3172 say about a sandbox for testing machine learning? | - | `itu-t-y3172` “sandbox” | 1 | 1 |
| What does the ITU AI readiness framework say about human oversight? | - | `itu-ai-readiness` “human-in-the-loop” | miss | miss |
