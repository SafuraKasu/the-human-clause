"""The "Fatima Hassan" progressive failure scenario (all data synthetic).

Events are released one at a time; the system only sees what has arrived. Each event carries an
EXPECTED outcome written before any agent exists, so the final report can compare expected with
actual. Expectations about policy and gaps are DRAFT predictions from reading the ingested texts:
the Policy agent must confirm them by real retrieval, and any that it cannot support must be
reported as such rather than forced to match.

Machine-checkable keys in `expected`:
  safety   present / absent finding ids, severity per id, no_category list
  consent  label -> {allowed, reason_code, [escalate]}
  policy   must_cite: [(doc_id, phrase that must occur in the cited chunk)], must_note: [str]
  gaps     gap ids the Policy agent should raise (hypotheses)
  audit    event kinds that must appear in the audit trail
"""
from dataclasses import dataclass, field

PATIENT_ID = "fatima-hassan"
SOURCES = {
    "HospitalA": {"label": "Hospital A (synthetic, cardiology)", "emirate": "Abu Dhabi", "exchange": "Malaffi"},
    "HospitalB": {"label": "Hospital B (synthetic, nephrology)", "emirate": "Dubai", "exchange": "NABIDH"},
    "HospitalC": {"label": "Hospital C (synthetic, endocrinology)", "emirate": "Abu Dhabi", "exchange": "Malaffi"},
}
GRANT_TIME, GRANT_EXPIRY = "2026-11-01T09:00", "2027-01-01T00:00"
GRANT_CATEGORIES = ["medications", "labs", "allergies", "conditions"]

DR_A = {"party_id": "dr_a", "org": "HospitalA", "role": "clinician"}
DR_B = {"party_id": "dr_b", "org": "HospitalB", "role": "clinician"}
DR_C = {"party_id": "dr_c", "org": "HospitalC", "role": "clinician"}
ED_A = {"party_id": "ed_a", "org": "HospitalA", "role": "clinician"}


@dataclass
class Event:
    seq: int
    at: str
    title: str
    actor: str
    kind: str
    narrative: str
    payload: dict = field(default_factory=dict)
    consent_checks: list = field(default_factory=list)
    expected: dict = field(default_factory=dict)


def check(label, requester, source, category="medications", exchange=None, emergency=False, justification=""):
    return {"label": label, "requester": requester, "source_org": source, "category": category,
            "exchange": exchange, "emergency": emergency, "justification": justification}


EVENTS = [
    Event(1, "2026-11-02T09:00", "Baseline records arrive from Hospitals A and C", "HospitalA, HospitalC",
          "records_arrive",
          "Fatima (72) has kidney disease, type 2 diabetes, hypertension and atrial fibrillation, and a recorded "
          "penicillin allergy. Cardiology (A) uploads warfarin and ramipril; endocrinology (C) uploads metformin. "
          "No lab results are on file yet.",
          payload={"age": 72, "uploads": [
              {"source_org": "HospitalA", "medications": ["Coumadin", "Tritace"],
               "conditions": ["chronic kidney disease", "atrial fibrillation", "hypertension"],
               "allergies": ["penicillin"]},
              {"source_org": "HospitalC", "medications": ["Glucophage"], "conditions": ["type 2 diabetes"]}]},
          consent_checks=[check("C_reads_A_meds", DR_C, "HospitalA")],
          expected={
              "safety": {"present": ["MISSING:DEMO-LAB-001:glucophage"], "absent": ["DEMO-INT-002"],
                         "no_category": ["interaction", "contraindication", "lab-rule"]},
              "consent": {"C_reads_A_meds": {"allowed": True, "reason_code": "GRANTED"}},
              "policy": {"must_cite": [], "must_note": ["Metformin cannot be assessed without eGFR: flag as uncertain, do not guess."]},
              "gaps": [], "audit": ["grant_created", "access_decision"]}),

    Event(2, "2026-11-03T10:00", "Hospital B (Dubai) prescribes spironolactone", "HospitalB", "records_arrive",
          "Nephrology at Hospital B, in a different emirate, adds spironolactone. The patient already takes ramipril "
          "and has kidney disease. Neither hospital knows about the other's prescription unless data is shared.",
          payload={"uploads": [{"source_org": "HospitalB", "medications": ["Aldactone"]}]},
          consent_checks=[check("A_reads_B_meds", DR_A, "HospitalB", exchange="NABIDH"),
                          check("B_reads_A_meds", DR_B, "HospitalA", exchange="Malaffi")],
          expected={
              "safety": {"present": ["DEMO-INT-002", "MISSING:DEMO-LAB-002:aldactone",
                                     "MISSING:DEMO-LAB-001:glucophage"],
                         "severity": {"DEMO-INT-002": "high"}},
              "consent": {"A_reads_B_meds": {"allowed": True, "reason_code": "GRANTED"},
                          "B_reads_A_meds": {"allowed": True, "reason_code": "GRANTED"}},
              "policy": {"must_cite": [("uae-health-ict-law-2019", "confidentiality of health data"),
                                       ("dha-health-info-sharing-2024", "Consent must be obtained"),
                                       ("doh-hie-policy-2020", "Universal")],
                         "must_note": ["Two emirate regimes apply (Abu Dhabi DoH and Dubai DHA); sharing here rests on the patient's grants."]},
              "gaps": ["GAP-CONSENT-REGIME-DIVERGENCE"], "audit": ["access_decision"]}),

    Event(3, "2026-11-06T16:00", "Overdue lab results arrive three days late", "HospitalC lab", "lab_arrives",
          "eGFR and potassium were taken on 3 Nov but only reach the system on 6 Nov. Until now the system had to "
          "treat both as unknown.",
          payload={"source_org": "HospitalC",
                   "labs": {"egfr": {"value": 24, "date": "2026-11-03"}, "potassium": {"value": 5.4, "date": "2026-11-03"}}},
          expected={
              "safety": {"present": ["DEMO-LAB-001:glucophage", "DEMO-LAB-002:aldactone", "DEMO-INT-002"],
                         "absent": ["MISSING:DEMO-LAB-001:glucophage", "MISSING:DEMO-LAB-002:aldactone"],
                         "severity": {"DEMO-LAB-001:glucophage": "high", "DEMO-LAB-002:aldactone": "high"}},
              "consent": {}, "policy": {"must_cite": [], "must_note": ["Earlier 'missing lab' uncertainty is resolved by the late result; the log must show both states."]},
              "gaps": [], "audit": []}),

    Event(4, "2026-11-07T11:00", "Patient withdraws consent for Hospital B's data and opts out of NABIDH", "patient",
          "patient_withdraws",
          "Fatima revokes every grant covering Hospital B's records and opts out of the Dubai exchange. From now "
          "on the platform must stop using Hospital B's data. Earlier sharing is already on record.",
          payload={"revoke_source": "HospitalB", "opt_out_exchange": "NABIDH"},
          consent_checks=[check("A_reads_B_meds_direct", DR_A, "HospitalB"),
                          check("A_reads_B_meds_exchange", DR_A, "HospitalB", exchange="NABIDH")],
          expected={
              "safety": {"present": ["DEMO-LAB-001:glucophage"],
                         "absent": ["DEMO-INT-002", "DEMO-LAB-002:aldactone"]},
              "limitations": ["HospitalB"],
              "consent": {"A_reads_B_meds_direct": {"allowed": False, "reason_code": "REVOKED"},
                          "A_reads_B_meds_exchange": {"allowed": False, "reason_code": "OPTED_OUT_OF_EXCHANGE"}},
              "policy": {"must_cite": [("dha-consent-access-standard-2025", "right to withdraw"),
                                       ("dha-consent-access-standard-2025", "retain such information")],
                         "must_note": ["The assessment is now incomplete by the patient's choice and must say so.",
                                       "Information already shared may stay in recipients' records."]},
              "gaps": ["GAP-CONSENT-REGIME-DIVERGENCE"], "audit": ["grant_revoked", "exchange_opt_out", "access_decision"]}),

    Event(5, "2026-11-08T02:30", "Emergency: clinician at Hospital A requests Hospital B's medication list",
          "HospitalA emergency department", "access_request",
          "Fatima arrives unconscious at Hospital A with bleeding. The doctor needs her full medication list, "
          "including Hospital B's, and requests break-the-glass access. She has opted out of NABIDH.",
          payload={"situation": "unconscious patient with bleeding, on an anticoagulant"},
          consent_checks=[check("ED_btg_B_meds", ED_A, "HospitalB", exchange="NABIDH", emergency=True,
                                justification="Unconscious, actively bleeding, on warfarin; need full medication list")],
          expected={
              "safety": {"present": ["DEMO-LAB-001:glucophage"], "absent": ["DEMO-INT-002"]},
              "consent": {"ED_btg_B_meds": {"allowed": False, "reason_code": "EMERGENCY_BLOCKED_BY_OPT_OUT",
                                            "escalate": True}},
              "policy": {"must_cite": [("uae-health-ict-law-2019", "health and safety of the patient"),
                                       ("dha-consent-access-standard-2025", "should not be retrieved using BTG"),
                                       ("dha-consent-access-standard-2025", "emergency condition"),
                                       ("dha-consent-access-standard-2025", "Emirate of Dubai")],
                         "must_note": ["Federal Art. 16(3) health-and-safety exception conflicts with DHA 9.7 opt-out rule.",
                                       "The system must escalate to a human and must not silently override either rule."]},
              "gaps": ["GAP-CROSS-EMIRATE-EMERGENCY-ACCESS"], "audit": ["access_decision"]}),

    Event(6, "2026-11-08T09:00", "Who owns the follow-up?", "HospitalC", "responsibility_query",
          "With eGFR 24 and potassium 5.4 on record, Hospital C asks which institution is responsible for "
          "coordinating the response across three prescribers in two emirates.",
          payload={"question": "Which institution is responsible for coordinating follow-up on high-severity "
                               "medication findings that span prescribers in different emirates?"},
          expected={
              "safety": {"present": ["DEMO-LAB-001:glucophage"], "absent": ["DEMO-INT-002"]},
              "limitations": ["HospitalB"],
              "consent": {},
              "policy": {"must_cite": [],
                         "must_note": ["If no provision assigning cross-institution responsibility is found in the "
                                       "ingested KB, say so and list what was searched. Never invent a provision.",
                                       "Absence in the KB is not proof that no rule exists elsewhere."]},
              "gaps": ["GAP-CROSS-INSTITUTION-RESPONSIBILITY"], "audit": []}),
]

# Gap hypotheses the Policy agent should confirm or reject with retrieved evidence.
GAP_HYPOTHESES = {
    "GAP-CONSENT-REGIME-DIVERGENCE": (
        "Abu Dhabi's HIE policy (DoH 2020, s4.2) makes participation mandatory and authorizes sharing even when "
        "consent is unavailable, while Dubai's 2025 standard (DHA s9.3) gives patients a right to withdraw and opt "
        "out. A patient treated in both emirates faces different consent regimes."),
    "GAP-CROSS-EMIRATE-EMERGENCY-ACCESS": (
        "DHA's break-the-glass rules cover Dubai entities and bar BTG retrieval for opted-out patients (s9.7), "
        "while federal Art. 16(3) allows disclosure to protect a patient's health and safety. No ingested "
        "provision resolves emergency access by a clinician in another emirate."),
    "GAP-CROSS-INSTITUTION-RESPONSIBILITY": (
        "Hypothesis: no ingested provision assigns responsibility for coordinating follow-up on medication "
        "findings that span institutions in different emirates. To be confirmed by searching the KB."),
}


# Neutral questions put to the Policy agent. They deliberately contain no expected answers
# or gap conclusions. Events without a question (1, 3) do not call the Policy agent.
POLICY_QUESTIONS = {
    2: ("Hospital B (Dubai) and Hospitals A and C (Abu Dhabi) now see each other's medication data for the same "
        "patient under the patient's own grants. Which UAE federal, Dubai and Abu Dhabi rules govern this sharing, "
        "and do they treat patient consent the same way?"),
    4: ("The patient has withdrawn consent for one hospital's records and opted out of the Dubai health "
        "information exchange. What do the rules say about the effect of withdrawal, including on information "
        "that was already shared?"),
    5: ("A clinician at an Abu Dhabi hospital requests emergency access to this patient's records held by a Dubai "
        "hospital. The patient has revoked the sharing grants and opted out of the Dubai exchange. What do the "
        "rules say about emergency access here, and are there conflicts or unclear points?"),
    6: ("Which institution is responsible for coordinating follow-up on high-severity medication findings that "
        "involve prescribers at hospitals in different emirates?"),
}

# Documents a correct gap finding should rest on (used only for a heuristic match, then reviewed by a human).
GAP_EVIDENCE_DOCS = {
    "GAP-CONSENT-REGIME-DIVERGENCE": ["doh-hie-policy-2020", "dha-consent-access-standard-2025"],
    "GAP-CROSS-EMIRATE-EMERGENCY-ACCESS": ["uae-health-ict-law-2019", "dha-consent-access-standard-2025"],
    "GAP-CROSS-INSTITUTION-RESPONSIBILITY": [],  # expected type: no provision found
}
