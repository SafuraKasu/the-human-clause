"""Safety engine tests. Demo-KB records only; none of this is clinical validation."""
import pytest

from backend.safety.engine import Lab, Medication, NO_ISSUE_STATEMENT, Patient, SafetyEngine


@pytest.fixture(scope="module")
def engine():
    return SafetyEngine()


def patient(meds, **kw):
    return Patient(medications=[Medication(*m) if isinstance(m, tuple) else m for m in meds], **kw)


def by_category(a, cat):
    return [f for f in a.findings if f.category == cat]


def test_brand_names_are_normalized(engine):
    assert engine.normalize("Advil") == "ibuprofen"
    assert engine.normalize("COUMADIN") == "warfarin"
    assert engine.normalize("notadrug") is None


def test_pairwise_interaction_with_brand_name_and_provenance(engine):
    a = engine.assess(patient([("Coumadin", "Hospital A"), ("Advil", "OTC")]))
    f = by_category(a, "interaction")[0]
    assert f.severity == "high" and f.certainty == "established"
    assert f.evidence["reference_id"] == "DEMO-INT-001"
    assert f.evidence["kb_version"] == "demo-0.1" and f.evidence["demonstration_data"] is True


def test_patient_factor_escalates_severity(engine):
    meds = [("ramipril", "Hospital A"), ("spironolactone", "Hospital B")]
    base = by_category(engine.assess(patient(meds, labs={"potassium": Lab(4.2)})), "interaction")[0]
    ckd = by_category(engine.assess(patient(meds, conditions=["Chronic kidney disease"],
                                            labs={"potassium": Lab(4.2)})), "interaction")[0]
    assert base.severity == "moderate" and ckd.severity == "high"
    assert any("chronic kidney disease" in p for p in ckd.patient_factors)


def test_duplication_same_ingredient_and_class(engine):
    same = engine.assess(patient([("ibuprofen", "A"), ("Brufen", "B")]))
    assert any(f.finding_id == "DUP-SAME:ibuprofen" for f in same.findings)
    cls = engine.assess(patient([("ibuprofen", "A"), ("naproxen", "B")]))
    assert any(f.finding_id.startswith("DUP-CLASS") for f in cls.findings)


def test_allergy_contraindication_on_proposed_medication(engine):
    p = patient([("warfarin", "A")], allergies=["Penicillin"])
    a = engine.assess(p, proposed=Medication("Amoxil", "Clinician"))
    f = by_category(a, "contraindication")[0]
    assert f.severity == "critical" and "Amoxil" in f.medications


def test_condition_contraindication(engine):
    a = engine.assess(patient([("ibuprofen", "A")], conditions=["Chronic kidney disease stage 3"]))
    assert by_category(a, "contraindication")[0].finding_id.startswith("DEMO-CON-001")


def test_lab_rule_trips_below_threshold(engine):
    a = engine.assess(patient([("metformin", "C")], labs={"egfr": Lab(24, "2026-10-01")}))
    f = by_category(a, "lab-rule")[0]
    assert f.severity == "high" and "24" in f.patient_factors[0]


def test_lab_rule_not_tripped_when_in_range(engine):
    a = engine.assess(patient([("metformin", "C")], labs={"egfr": Lab(70)}))
    assert not a.findings


def test_missing_lab_is_flagged_not_guessed(engine):
    a = engine.assess(patient([("metformin", "C")]))
    f = by_category(a, "missing-data")[0]
    assert f.certainty == "uncertain" and f.missing_info and "egfr" in f.title.lower()
    assert not by_category(a, "lab-rule")


def test_discontinued_and_uncertain_status_handling(engine):
    a = engine.assess(patient([("warfarin", "A"), Medication("ibuprofen", "B", status="discontinued")]))
    assert not by_category(a, "interaction")
    assert a.ignored_medications == ["ibuprofen"]


def test_unknown_medication_is_flagged(engine):
    a = engine.assess(patient([("warfarin", "A"), ("mysterycure", "B")]))
    f = by_category(a, "missing-data")[0]
    assert "mysterycure" in f.medications and f.severity == "informational"


def test_no_findings_never_claims_safety(engine):
    a = engine.assess(patient([("lisinopril", "A"), ("simvastatin", "B")]))
    assert not a.findings and a.summary == NO_ISSUE_STATEMENT
    s = a.summary.lower()
    assert s.startswith("no known issue") and "not proof" in s
    assert "is safe" not in s.replace("not proof that the combination is safe", "")


def test_findings_sorted_by_severity_and_deterministic(engine):
    p = patient([("simvastatin", "A"), ("clarithromycin", "B"), ("warfarin", "A"), ("ibuprofen", "C")])
    a1, a2 = engine.assess(p), engine.assess(p)
    assert [f.finding_id for f in a1.findings] == [f.finding_id for f in a2.findings]
    sev = ["critical", "high", "moderate", "low", "informational"]
    ranks = [sev.index(f.severity) for f in a1.findings]
    assert ranks == sorted(ranks) and a1.findings[0].severity == "critical"


def test_safety_boundaries_in_next_steps(engine):
    p = patient([("simvastatin", "A"), ("clarithromycin", "B"), ("metformin", "C")],
                labs={"egfr": Lab(20)}, allergies=["penicillin"])
    for f in engine.assess(p, proposed=Medication("amoxicillin")).findings:
        step = f.recommended_next_step.lower()
        assert not step.startswith(("stop", "start", "increase", "decrease", "double"))
        assert "doctor" in step or "pharmacist" in step or "care team" in step


def test_every_finding_has_provenance(engine):
    p = patient([("warfarin", "A"), ("ibuprofen", "B"), ("metformin", "C"), ("ramipril", "A"),
                 ("spironolactone", "B")], conditions=["chronic kidney disease"])
    for f in engine.assess(p).findings:
        assert f.evidence["kb_version"] and f.evidence["source"] and f.evidence["demonstration_data"] is True
