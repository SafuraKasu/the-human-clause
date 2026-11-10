"""Authored content for the technical report: mappings, requirements, gaps, adjudication.

Every (chunk_id, phrase) citation is verified against the ingested KB by backend/report/build.py;
the build fails if a phrase is missing, so no cited provision can drift from the source text.
Status words are deliberately plain: implemented / partial / simulated / not implemented.
"""

# ---- Report FAQ item 3: requirements ---------------------------------------------------------------
REQUIREMENTS = [
    ("R1", "Share a patient's medication data across hospitals only on the patient's authority, per category and purpose, with expiry."),
    ("R2", "Honour withdrawal of consent and opt-out from a health information exchange, and say so when an assessment becomes incomplete."),
    ("R3", "Detect medication-safety issues deterministically (interactions, duplication, contraindications, lab-dependent rules), never guess missing data, never present 'no issue found' as proof of safety."),
    ("R4", "Handle emergency access under explicit rules: allowed only with justification, always flagged, escalated to a human when rules conflict."),
    ("R5", "Ground every policy statement in a retrievable source passage; report conflicts, unclear scope and gaps honestly."),
    ("R6", "Keep an inspectable audit trail of decisions, evidence, rule checks and handoffs (no hidden reasoning)."),
    ("R7", "Keep AI supervised: advisory only, overridable by humans, no clinical action taken automatically."),
    ("R8", "Respect data-location limits: no real patient data leaves the State; the prototype uses synthetic data only."),
]

# ---- ITU-T Y.3172 mapping ----------------------------------------------------------------------------
# (component, Y.3172 role, Human Clause counterpart, status, [(chunk, phrase)])
Y3172_ROWS = [
    ("SRC / C (source, collector)", "SRC is the source of pipeline input data; C collects from SRC nodes.",
     "Hospital A/B/C record uploads and late lab results (synthetic) are the sources; `ScenarioState` ingests them.",
     "simulated", [("itu-t-y3172#0029", "SRC (source)"), ("itu-t-y3172#0029", "C (collector)")]),
    ("PP (preprocessor)", "Cleans or aggregates data into a form the ML model can consume.",
     "Brand-to-ingredient normalization, status filtering, and consent-based exclusion of withdrawn sources before any assessment.",
     "implemented", [("itu-t-y3172#0029", "PP (preprocessor)")]),
    ("M (model)", "The ML model usable in the pipeline.",
     "No trained ML model. A deterministic rule engine (demo KB) makes safety findings; an LLM (Gemini free tier) explains findings and reasons over retrieved policy text.",
     "partial", [("itu-t-y3172#0029", "M (model)")]),
    ("P (policy)", "Applies policies to the model's output before it is acted on.",
     "Consent module and Policy agent decide what outputs may be used or shown; blocked emergency requests are escalated, not overridden.",
     "implemented", [("itu-t-y3172#0030", "P (policy)")]),
    ("D / SINK (distributor, sink)", "D identifies sinks and distributes the output; SINK takes action on it.",
     "Orchestrator routes results to patient-facing wording, clinician review and human escalation. The sink is a human decision; nothing acts automatically.",
     "implemented", [("itu-t-y3172#0030", "D (distributor)"), ("itu-t-y3172#0030", "SINK")]),
    ("MLFO (orchestrator)", "Manages and orchestrates pipeline nodes from ML Intent; selects and reselects the model, e.g. by performance.",
     "Plain-Python Orchestrator sequences nodes and logs handoffs. The LLM client reselects a fallback model on failure; it does not select by measured performance.",
     "partial", [("itu-t-y3172#0030", "MLFO"), ("itu-t-y3172#0030", "selects and reselects the ML model")]),
    ("ML Intent", "Describes the ML application, its data needs, constraints and characteristics; input to the MLFO.",
     "Scenario definition (events, expected outcomes) plus written agent mandates in `docs/agents.md` play this role informally; there is no formal metalanguage.",
     "partial", [("itu-t-y3172#0037", "ML Intent")]),
    ("ML sandbox subsystem", "Lets operators study ML outputs on simulated underlay networks before deploying live.",
     "Scenario replay with synthetic hospitals, mock and live LLM modes, and expected-versus-actual evaluation. Nothing is deployed live.",
     "implemented", [("itu-t-y3172#0036", "ML sandbox subsystem")]),
    ("Management subsystem", "Extends network management and orchestration to the ML pipeline nodes.",
     "Append-only audit trail and evaluator record what each node did. No resource or lifecycle management.",
     "partial", [("itu-t-y3172#0034", "management subsystem")]),
    ("Security considerations", "Prevent unauthorized access to, and data leaking from, an ML pipeline.",
     "Consent module and audit log; citation guards against invented sources. Audit log is tamper-evident (hash chain), not tamper-proof. Not implemented: authentication, encryption, protected log storage. Synthetic data only.",
     "partial", [("itu-t-y3172#0038", "Security considerations")]),
]
Y3172_CAVEAT = ("Y.3172 addresses machine learning in future networks (IMT-2020). We apply its pipeline concepts by analogy to a "
                "health-data agent system; the mapping explains how our architecture corresponds to it and does not claim network-level conformance.")

# ---- AI Readiness Framework mapping (the event page's eight lenses -> Report 2.0 dimensions) -------------
# (lens, framework dimensions/factors, how addressed, status, [(chunk, phrase)])
READINESS_ROWS = [
    ("Open data and open-source management", "Factors: Open Data, Open source. Dimension 1 (Data/model Marketplace); Data Governance metrics.",
     "Policy KB built only from published open documents with a manifest of sources and retrieval dates; source code in the repository. Demo medication KB is team-curated and unverified. No bias audit of data (synthetic).",
     "partial", [("itu-ai-readiness#0004", "Open Data"), ("itu-ai-readiness#0020", "Marketplace")]),
    ("Generative AI content ecosystem", "Dimension 2 (Generated Content Marketplace).",
     "LLM-written explanations are validated against deterministic findings, labelled by origin (llm or template) in the output, and rejected if they give forbidden advice.",
     "partial", [("itu-ai-readiness#0022", "Generated Content Marketplace")]),
    ("Contextualization and regional development", "Dimension 4 (Contextualization and Regional Impact); Dimension 12 (Granular Priorities).",
     "Grounded in UAE federal, Dubai and Abu Dhabi rules, and designed around differences between emirates. English text only; Arabic originals prevail legally.",
     "partial", [("itu-ai-readiness#0025", "Contextualization and Regional Impact"), ("itu-ai-readiness#0043", "Granular Priorities")]),
    ("Domain-specific and cross-domain AI integration", "Dimension 5 (Level of Integration of AI in Workflows); Dimension 3 (Cross-domain correlation analysis).",
     "Joins healthcare medication safety, data-protection law and AI-governance policy in one pipeline across three institutions. Not integrated with real hospital systems.",
     "partial", [("itu-ai-readiness#0027", "Level of Integration of AI in Workflows"), ("itu-ai-readiness#0024", "Cross-domain correlation analysis")]),
    ("Human interaction and supervision", "Dimension 6 (Human Interface); Dimension 8 (Collaboration with AI); Dimension 9 (Impacts of Humans in AI Integration).",
     "Plain-language explanations; advisory output only; blocked or conflicting cases escalate to a human; no automatic clinical action.",
     "implemented", [("itu-ai-readiness#0028", "Human Interface"), ("itu-ai-readiness#0032", "Collaboration with AI"), ("itu-ai-readiness#0033", "Impacts of Humans in AI Integration")]),
    ("AI policy and implementation opportunities", "Dimension 10 (AI & Policies); Dimension 7 (Strategy Alignment); Factors: Standards, Sandbox.",
     "Core of the project: a policy KB, a Policy agent with citation guards, progressive scenarios, and a gap report. The UAE AI Strategy 2031 is ingested but not yet exercised by the scenario.",
     "implemented", [("itu-ai-readiness#0036", "AI & Policies"), ("itu-ai-readiness#0029", "Strategy Alignment"), ("itu-ai-readiness#0004", "Sandbox: Platforms for AI experimentation and validation")]),
    ("AI for social inclusion", "Dimension 11 (AI for Inclusion).",
     "Not addressed beyond plain-language wording. No Arabic interface or content, no accessibility work.",
     "not implemented", [("itu-ai-readiness#0038", "AI for Inclusion")]),
    ("Digital infrastructure and energy considerations", "Dimension 13 (Digital Infrastructure).",
     "Runs on a laptop plus a free cloud LLM. Compute, energy and connectivity requirements were not measured.",
     "not implemented", [("itu-ai-readiness#0044", "Digital Infrastructure")]),
]

# ---- Requirements -> local policies ---------------------------------------------------------------------
# (req, provisions [(label, chunk, phrase)], implementation, status)
POLICY_ROWS = [
    ("R1 Consent-based sharing",
     [("Federal ICT Health Law Art. 16", "uae-health-ict-law-2019#0019", "without written approval from the patient"),
      ("DHA Health Information Sharing Policy 4.8.5", "dha-health-info-sharing-2024#0019", "Consent must be obtained as appropriate"),
      ("DoH HIE Policy 4.2.1.2", "doh-hie-policy-2020#0021", "Require Healthcare Facilities to obtain patient consent")],
     "Consent module: grants per grantee, source, category and purpose, with expiry; every decision logged.", "implemented"),
    ("R2 Withdrawal and opt-out",
     [("DHA Consent Standard 9.3", "dha-consent-access-standard-2025#0018", "right to withdraw and opt-out"),
      ("DHA Consent Standard 9.4", "dha-consent-access-standard-2025#0018", "may retain such information in its records")],
     "Revocation effective from its timestamp; exchange opt-out; withdrawn sources excluded from assessment with a limitation notice. Earlier lawful sharing is not erased.", "implemented"),
    ("R3 Confidentiality of health data",
     [("Federal ICT Health Law Art. 4", "uae-health-ict-law-2019#0007", "confidentiality of health data")],
     "Category-level access control; outputs only to authorised requesters. No encryption in the prototype.", "partial"),
    ("R3 Minimum necessary sharing",
     [("DHA Health Information Sharing Policy 4.5.5", "dha-health-info-sharing-2024#0014", "Only the minimum amount of PHI requested")],
     "Grants are limited to data categories (medications, labs, allergies, conditions). No field-level minimisation.", "partial"),
    ("R4 Emergency access",
     [("Executive Regulation Art. 6(3)", "uae-health-ict-exec-reg-2020#0007", "In case of an emergency and if the"),
      ("Federal ICT Health Law Art. 16(3)", "uae-health-ict-law-2019#0019", "health and safety of the patient"),
      ("DHA Consent Standard 17.2.1", "dha-consent-access-standard-2025#0030", "Treating a Data Subject/Patient with an emergency condition"),
      ("DoH HIE Policy 6.1.4", "doh-hie-policy-2020#0054", "break the seal"),
      ("DHA Consent Standard 9.7 (limit)", "dha-consent-access-standard-2025#0018", "should not be retrieved using BTG access")],
     "Break-the-glass needs a clinician and a written justification and is always flagged; blocked and escalated when the patient opted out of the source's exchange. See gap G2.", "implemented"),
    ("R6 Audit and logging",
     [("DHA Consent Standard 17.6", "dha-consent-access-standard-2025#0030", "detailed audit trail must be documented"),
      ("DoH HIE Policy 6.1.3.13", "doh-hie-policy-2020#0051", "Assure that log files cannot be altered")],
     "Append-only consent log and orchestration audit trail, exported as JSON lines. The audit trail is sealed as a SHA-256 hash chain with its head hash recorded in run.json, so edits, deletions, reordering and truncation are detectable; it is tamper-evident, not tamper-proof, and the recorded run was sealed after it finished.", "partial"),
    ("R7 AI supervised and overridable",
     [("DHA AI Policy 4.4.1", "dha-ai-policy-2021#0008", "safe, secure and supervised/monitored by end users"),
      ("DHA AI Policy 4.4.2", "dha-ai-policy-2021#0008", "overridden or their decisions reversed by designated end users")],
     "Advisory only; no automatic action; escalation to a human. Override is implicit (nothing is enforced), not a built feature.", "implemented"),
    ("R7 Accountability and appeals (not met)",
     [("DHA AI Policy 4.2.1", "dha-ai-policy-2021#0007", "Accountability for the outcomes of an AI solution"),
      ("DHA AI Policy 4.2.3", "dha-ai-policy-2021#0007", "built-in appeals procedures")],
     "Agent mandates are documented, but there is no accountability agreement and no appeals procedure.", "not implemented"),
    ("R7 Independent validation (not met)",
     [("DHA AI Policy 4.3.3", "dha-ai-policy-2021#0008", "independent validation by a competent third party")],
     "No independent validation. Safety rules are a team-curated demonstration KB, not clinically validated.", "not implemented"),
    ("R8 Data location",
     [("Federal ICT Health Law Art. 13", "uae-health-ict-law-2019#0016", "not permissible to store, process, generate or transform the health data and information outside State"),
      ("DHA AI Policy 4.6.2", "dha-ai-policy-2021#0009", "Comply with all Articles detailed within")],
     "Synthetic data only. The live LLM runs outside the UAE, so real patient data could not be sent to it without a lawful exception or an in-country model. See gap G4.", "partial"),
]

# ---- Gaps ---------------------------------------------------------------------------------------------
# Absence scans: ([doc_ids], regex, what we are checking). Counts are recomputed at build time.
UAE_DOCS = ["uae-health-ict-law-2019", "uae-health-ict-exec-reg-2020", "uae-pdpl-2021", "dha-health-info-sharing-2024",
            "dha-consent-access-standard-2025", "dha-ai-policy-2021", "doh-hie-policy-2020",
            "doh-circular-2026-10-malaffi-onboarding", "doh-circular-2026-144-malaffi-referrals"]

GAPS = [
    dict(
        id="G1", title="Patients in different emirates get different consent and opt-out rights",
        statement=("Dubai's 2025 standard gives patients a right to withdraw and opt out of the health information exchange. "
                   "Abu Dhabi's 2020 exchange policy makes participation mandatory, authorizes sharing where consent is unavailable, and "
                   "contains no opt-out provision (full-text scan: zero hits). The federal data-protection law's general right to withdraw "
                   "consent cannot be assumed to fill the gap, because it excludes personal health data that has its own regulating legislation."),
        evidence=[("DHA Consent Standard 9.3", "dha-consent-access-standard-2025#0018", "right to withdraw and opt-out"),
                  ("DoH HIE Policy 4.2 (mandatory participation)", "doh-hie-policy-2020#0021", "making universal patient participation in and sharing of data with the ADHIE Platform mandatory"),
                  ("DoH HIE Policy 4.2.1.2 (sharing without consent)", "doh-hie-policy-2020#0021", "notwithstanding the unavailability of patient consent"),
                  ("PDPL Art. 6(2) (general withdrawal right)", "uae-pdpl-2021#0010", "may, at any time, withdraw their consent"),
                  ("PDPL Art. 2(2)(e) (health data exclusion)", "uae-pdpl-2021#0005", "Personal Health Data that has legislation regulating its protection and processing")],
        scans=[(["doh-hie-policy-2020"], r"opt[- ]?out", "occurrences of 'opt-out' in the Abu Dhabi HIE policy")],
        comparison=[("EHDS Art. 10(1)", "eu-ehds-2025-327#0094", "exercise of that right is reversible")],
        relevance="A patient treated in both emirates, as in our scenario, cannot predict whether an opt-out or withdrawal will be honoured.",
        recommendation="Publish a federal or inter-emirate rule on whether and how an opt-out registered in one emirate binds exchanges in another.",
        origin="Hypothesis written before the run. In the final recorded run the agent independently reported, at event 4, that it found no opt-out provision for Abu Dhabi's exchange equivalent to Dubai's, which matches the team's full-text scan. Verified by the team in the source text.",
        caveats="The Abu Dhabi policy is from April 2020 and may have been superseded. English text only."),
    dict(
        id="G2", title="Emergency access to an opted-out patient's records across emirates is unresolved",
        statement=("The Dubai standard says an opted-out patient's data should not be retrieved by break-the-glass. The federal Executive "
                   "Regulation and the ICT Health Law allow access in an emergency or to protect the patient's health and safety, and Abu Dhabi "
                   "has its own 'break the seal' rule. The Dubai standard's scope is PHI within Dubai. No ingested provision says which rule "
                   "governs a clinician in one emirate requesting an opted-out patient's data held in another."),
        evidence=[("DHA Consent Standard 9.7", "dha-consent-access-standard-2025#0018", "should not be retrieved using BTG access"),
                  ("DHA Consent Standard 2.1 (scope)", "dha-consent-access-standard-2025#0011", "All PHI within the Emirate of Dubai"),
                  ("Executive Regulation Art. 6(3)", "uae-health-ict-exec-reg-2020#0007", "In case of an emergency and if the"),
                  ("Federal ICT Health Law Art. 16(3)", "uae-health-ict-law-2019#0019", "health and safety of the patient"),
                  ("DoH HIE Policy 6.1.4", "doh-hie-policy-2020#0054", "break the seal")],
        scans=[],
        comparison=[("EHDS Art. 10(2)", "eu-ehds-2025-327#0094", "even if the patient has exercised the right to opt out in primary use")],
        relevance="Our scenario's event 5: an unconscious, bleeding patient whose opt-out blocks the clinician who needs her full medication list. The system blocked and escalated to a human.",
        recommendation="State, in federal guidance, whether an opt-out can be overridden for vital interests and which emirate's emergency rule applies to cross-emirate requests. The EU resolves the same question explicitly in EHDS Art. 10.",
        origin="Hypothesis written before the run. The agent independently found the conflict and the scope question at event 5 and cited Executive Regulation Art. 6(3) and the Abu Dhabi provision, which we had not scripted. Verified by the team.",
        caveats="Whether the emergency block is the right behavior is a legal question; the consent module's setting is a configuration choice, not a conclusion."),
    dict(
        id="G3", title="No ingested provision assigns responsibility for cross-institution follow-up",
        statement=("No ingested UAE text assigns responsibility for coordinating follow-up on high-severity medication findings that span "
                   "prescribers in different emirates. Full-text scans find no 'medication reconciliation' or 'responsible for coordinating' "
                   "anywhere. The nearest provisions concern exchange interoperability and referral data, not who acts on a finding."),
        evidence=[("DoH HIE Policy (objective: interoperability for coordination of care)", "doh-hie-policy-2020#0037", "improve the quality and coordination of care"),
                  ("DoH Circular 2026/144 (referral data)", "doh-circular-2026-144-malaffi-referrals#0001", "supporting care coordination, continuity of care, referral tracking")],
        scans=[(UAE_DOCS, r"medication reconciliation", "occurrences of 'medication reconciliation' across all ingested UAE texts"),
               (UAE_DOCS, r"responsible for coordinat", "occurrences of 'responsible for coordinating' across all ingested UAE texts")],
        comparison=[("EHDS Art. 20 (authority-level coordination only)", "eu-ehds-2025-327#0107", "one of them shall be responsible for the drawing up of the report")],
        relevance="Our scenario's event 6: three prescribers in two emirates, two high-severity findings, and no stated owner.",
        recommendation="Define which institution (for example the most recent prescriber or the patient's primary care provider) owns the response to a cross-institution medication-safety finding.",
        origin="Hypothesis written before the run; reported by the agent after a multi-query search (the search log is in the run record), with the team's full-text scans as an independent check.",
        caveats="Absence in the ingested documents is not proof that no rule exists elsewhere. The EU comparator concerns reporting by digital health authorities, not clinical responsibility."),
    dict(
        id="G4", title="No ingested provision addresses externally hosted AI processing of health data",
        statement=("The ICT Health Law restricts storing or processing health data outside the State unless a Health Authority resolution allows it. "
                   "The Dubai AI policy requires AI solutions to comply with that law but never mentions cloud, location or localization (full-text scan: "
                   "zero hits), and the instrument that lists exceptions (Ministerial Decision 51 of 2021) is not in our KB. Whether an externally hosted "
                   "LLM can lawfully process real patient data is therefore not answered by the ingested texts."),
        evidence=[("Federal ICT Health Law Art. 13", "uae-health-ict-law-2019#0016", "not permissible to store, process, generate or transform the health data and information outside State"),
                  ("DHA AI Policy 4.6.2", "dha-ai-policy-2021#0009", "Comply with all Articles detailed within")],
        scans=[(["dha-ai-policy-2021"], r"outside (the )?(UAE|State|Emirate)|cloud|locali[sz]ation", "occurrences of outside/cloud/localization in the Dubai AI policy")],
        comparison=[],
        relevance="This prototype uses a cloud LLM on synthetic data only. A real deployment would need an in-country model or a lawful exception.",
        recommendation="Clarify how Art. 13 applies to AI services hosted abroad, and publish the exceptions in one place alongside the AI policies.",
        origin="Identified in the team's own review, not raised by the agent.",
        caveats="Ministerial Decision 51 of 2021 and the Abu Dhabi AI policy and Responsible AI Standard are not ingested (the Abu Dhabi files could not be downloaded). This gap is limited to the texts we hold."),
]

# ---- Human adjudication of evaluation checks that were not 'pass' --------------------------------------
# (event seq, substring of check description) -> note. Verified against source text by the team.
ADJUDICATION = {
    (2, "confidentiality of health data"): "Valid alternative. The agent cited texts that restate the confidentiality rule (DHA 4.7 cites Art. 16 of the ICT Health Law) instead of Art. 4. Our expectation was too narrow.",
    (2, "Consent must be obtained"): "Valid alternative. The agent cited another provision of the same DHA policy that makes sharing depend on patient consent (4.6, table of care-purpose sharing).",
    (2, "GAP-CONSENT-REGIME-DIVERGENCE"): "Confirmed at a different event. At event 2 the agent raised a related interoperability gap (how a consent in one emirate's exchange is recognised in another). It raised the opt-out divergence itself at event 4 (\"Applicability of Opt-Out to Abu Dhabi (Malaffi)\"), which matches the team's full-text scan.",
    (4, "GAP-CONSENT-REGIME-DIVERGENCE"): "Confirmed at a different event. The agent raised the divergence at event 2 in an earlier run; event 4's question concerned the effect of withdrawal, which it answered with DHA 9.3 and 9.4.",
    (5, "health and safety of the patient"): "Valid alternative. The agent cited Executive Regulation Art. 6(3), which expressly covers emergency access to a patient file with reasons: arguably a closer match than Art. 16(3).",
    (5, "emergency condition"): "Valid alternative. The agent cited the DHA break-the-glass definition and Abu Dhabi's break-the-seal provision (DoH 6.1.4) instead of DHA 17.2.1; the Abu Dhabi rule was not in our script.",
    (5, "Emirate of Dubai"): "Partly met. The agent raised the cross-emirate scope question as a gap but did not cite DHA 2.1; it did cite DHA 9.7 and the federal provision.",
}


# ---- Official-template mapping: one row per pipeline node (template section 4) -------------------------
# (node, Human Clause implementation, Readiness 2.0 text, [(chunk, phrase)] readiness evidence,
#  [(label, chunk, phrase)] policy provisions, status)
PIPELINE_ROWS = [
    ("SRC", "Hospital A/B/C record uploads and lab results (synthetic).",
     "Dim 1 Data/model Marketplace; Data Governance",
     [("itu-ai-readiness#0020", "Marketplace"), ("itu-ai-readiness#0013", "Data Governance")],
     [("ICT Health Law Art. 16", "uae-health-ict-law-2019#0019", "without written approval from the patient"),
      ("DHA Sharing Policy 4.8.5", "dha-health-info-sharing-2024#0019", "Consent must be obtained as appropriate"),
      ("DoH HIE Policy 4.2.1.2", "doh-hie-policy-2020#0021", "Require Healthcare Facilities to obtain patient consent")],
     "simulated"),
    ("C", "Records are ingested as events arrive; the Orchestrator releases one event at a time. Runs locally; the LLM is a free cloud service.",
     "Dim 13 Digital Infrastructure (not assessed)",
     [("itu-ai-readiness#0044", "Digital Infrastructure")],
     [("ICT Health Law Art. 13 (data location)", "uae-health-ict-law-2019#0016", "not permissible to store, process, generate or transform the health data and information outside State")],
     "simulated"),
    ("PP", "Brand-to-ingredient normalization; status filtering; sources the patient withdrew are excluded before any assessment.",
     "Data Interoperability; Dim 4 Contextualization and Regional Impact",
     [("itu-ai-readiness#0013", "Data Interoperability"), ("itu-ai-readiness#0025", "Contextualization and Regional Impact")],
     [("DHA Sharing Policy 4.5.5 (minimum necessary)", "dha-health-info-sharing-2024#0014", "Only the minimum amount of PHI requested"),
      ("DHA Consent Standard 9.4", "dha-consent-access-standard-2025#0018", "may retain such information in its records")],
     "implemented"),
    ("M", "Deterministic safety engine on a demonstration KB (no trained ML model). An LLM explains findings and reasons over retrieved policy text.",
     "Dim 2 Generated Content Marketplace; Factor Standards",
     [("itu-ai-readiness#0022", "Generated Content Marketplace"), ("itu-ai-readiness#0004", "Standards: Ensuring trust, interoperability, and compliance")],
     [("DHA AI Policy 4.3.3 (NOT met)", "dha-ai-policy-2021#0008", "independent validation by a competent third party"),
      ("DHA AI Policy 4.4.1", "dha-ai-policy-2021#0008", "safe, secure and supervised/monitored by end users")],
     "partial"),
    ("P", "Consent module and Policy agent decide what may be used or shown. A blocked emergency request escalates to a human.",
     "Dim 10 AI & Policies; Dim 7 Strategy Alignment",
     [("itu-ai-readiness#0036", "AI & Policies"), ("itu-ai-readiness#0029", "Strategy Alignment")],
     [("Executive Regulation Art. 6(3)", "uae-health-ict-exec-reg-2020#0007", "In case of an emergency and if the"),
      ("ICT Health Law Art. 16(3)", "uae-health-ict-law-2019#0019", "health and safety of the patient"),
      ("DHA Consent Standard 17.2.1 and 9.7", "dha-consent-access-standard-2025#0018", "should not be retrieved using BTG access"),
      ("DoH HIE Policy 6.1.4", "doh-hie-policy-2020#0054", "break the seal")],
     "implemented"),
    ("D", "Orchestrator routes results and records every handoff in an append-only, hash-chained audit trail (tamper-evident, not tamper-proof).",
     "Dim 5 Level of Integration of AI in Workflows; Dim 3 Cross-domain correlation analysis",
     [("itu-ai-readiness#0027", "Level of Integration of AI in Workflows"), ("itu-ai-readiness#0024", "Cross-domain correlation analysis")],
     [("DHA Consent Standard 17.6", "dha-consent-access-standard-2025#0030", "detailed audit trail must be documented"),
      ("DoH HIE Policy 6.1.3.13", "doh-hie-policy-2020#0051", "Assure that log files cannot be altered")],
     "partial"),
    ("SINK", "Human review: output is advisory, nothing acts automatically. No accountability agreement or appeals procedure yet.",
     "Dim 6 Human Interface; Dim 8 Collaboration with AI; Dim 9 Impacts of Humans in AI Integration",
     [("itu-ai-readiness#0028", "Human Interface"), ("itu-ai-readiness#0032", "Collaboration with AI"), ("itu-ai-readiness#0033", "Impacts of Humans in AI Integration")],
     [("DHA AI Policy 4.4.2 (override)", "dha-ai-policy-2021#0008", "overridden or their decisions reversed by designated end users"),
      ("DHA AI Policy 4.2.3 (appeals, NOT met)", "dha-ai-policy-2021#0007", "built-in appeals procedures")],
     "implemented"),
    ("MLFO and ML sandbox", "Plain-Python Orchestrator; scenario replay on synthetic hospitals with expected-versus-actual evaluation. Nothing is deployed live.",
     "Factor Sandbox",
     [("itu-ai-readiness#0004", "Sandbox: Platforms for AI experimentation and validation")],
     [("DHA AI Policy 4.4.1", "dha-ai-policy-2021#0008", "safe, secure and supervised/monitored by end users")],
     "partial"),
]
PIPELINE_NOT_ADDRESSED = ("Not addressed: Dim 11 AI for Inclusion (no Arabic or accessibility work) and energy use; the UAE AI Strategy 2031 is in the "
                          "knowledge base but the scenario does not yet exercise it.")
REQ_NODES = {"R1": "SRC, P", "R2": "PP, P", "R3": "M", "R4": "P, SINK", "R5": "M, P", "R6": "D", "R7": "SINK", "R8": "C"}
