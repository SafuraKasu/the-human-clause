"""Consent module tests."""
from dataclasses import dataclass

import pytest

from backend.consent.registry import ConsentRegistry, Requester

DR_A = Requester("dr_a", "HospitalA", "clinician")
DR_B = Requester("dr_b", "HospitalB", "clinician")
PHARM = Requester("rx1", "HospitalA", "regulator")


@pytest.fixture
def reg():
    r = ConsentRegistry("fatima")
    r.grant("HospitalA", "HospitalB", ["medications", "labs"], "care", "2026-11-01T09:00", "2027-01-01T00:00")
    return r


def check(r, req=DR_A, cat="medications", src="HospitalB", at="2026-11-02T10:00", **kw):
    return r.check(req, cat, src, at, **kw)


def test_active_grant_allows(reg):
    d = check(reg)
    assert d.allowed and d.reason_code == "GRANTED" and d.grant_id == "G001"


def test_no_grant_denied(reg):
    d = check(reg, req=DR_B, src="HospitalA")
    assert not d.allowed and d.reason_code == "NO_GRANT"


def test_custodian_and_patient_always_allowed(reg):
    assert check(reg, req=DR_B, src="HospitalB").reason_code == "OWN_RECORDS"
    assert check(reg, req=Requester("fatima", "", "patient")).reason_code == "PATIENT_SELF"


def test_category_and_purpose_must_match(reg):
    assert check(reg, cat="allergies").reason_code == "CATEGORY_NOT_COVERED"
    assert check(reg, purpose="research").reason_code == "PURPOSE_NOT_COVERED"


def test_grant_expiry_and_not_yet_active(reg):
    assert check(reg, at="2027-01-02T00:00").reason_code == "EXPIRED"
    assert check(reg, at="2026-10-31T00:00").reason_code == "NOT_YET_ACTIVE"


def test_revocation_takes_effect_from_its_timestamp_not_before(reg):
    reg.revoke_grant("G001", "2026-11-07T11:00")
    assert check(reg, at="2026-11-06T12:00").allowed  # earlier access was legitimate
    d = check(reg, at="2026-11-07T11:30")
    assert not d.allowed and d.reason_code == "REVOKED" and "2026-11-07" in d.reason


def test_revoke_where_by_source(reg):
    reg.grant("HospitalC", "HospitalB", ["medications"], "care", "2026-11-01T09:00")
    reg.grant("HospitalC", "HospitalA", ["medications"], "care", "2026-11-01T09:00")
    ids = reg.revoke_where("2026-11-07T11:00", source_org="HospitalB")
    assert len(ids) == 2
    assert reg.revoke_where("2026-11-07T12:00", source_org="HospitalB") == []  # idempotent
    assert check(reg, req=Requester("dr_c", "HospitalC", "clinician"), src="HospitalA", at="2026-11-08T00:00").allowed


def test_exchange_opt_out_blocks_exchange_channel(reg):
    reg.opt_out("NABIDH", "2026-11-07T11:00")
    assert check(reg, exchange="NABIDH", at="2026-11-06T00:00").allowed
    d = check(reg, exchange="NABIDH", at="2026-11-07T12:00")
    assert not d.allowed and d.reason_code == "OPTED_OUT_OF_EXCHANGE"
    assert check(reg, at="2026-11-07T12:00").allowed  # direct grant unaffected


def test_emergency_override_when_no_opt_out_is_flagged(reg):
    reg.revoke_grant("G001", "2026-11-07T11:00")
    d = check(reg, at="2026-11-08T02:30", emergency=True, justification="Unconscious, bleeding, on warfarin")
    assert d.allowed and d.reason_code == "EMERGENCY_OVERRIDE" and d.flagged_for_review and not d.escalate


def test_emergency_needs_clinician_and_justification(reg):
    reg.revoke_grant("G001", "2026-11-07T11:00")
    assert check(reg, req=PHARM, at="2026-11-08T00:00", emergency=True, justification="x"
                 ).reason_code == "EMERGENCY_NOT_PERMITTED"
    assert check(reg, at="2026-11-08T00:00", emergency=True, justification="  "
                 ).reason_code == "EMERGENCY_JUSTIFICATION_REQUIRED"


def test_emergency_blocked_by_opt_out_escalates_and_is_never_silent(reg):
    reg.revoke_grant("G001", "2026-11-07T11:00")
    reg.opt_out("NABIDH", "2026-11-07T11:00")
    d = check(reg, at="2026-11-08T02:30", exchange="NABIDH", emergency=True, justification="Unconscious, bleeding")
    assert not d.allowed and d.reason_code == "EMERGENCY_BLOCKED_BY_OPT_OUT"
    assert d.escalate and d.flagged_for_review and "9.7" in d.rule_basis


def test_opt_out_emergency_block_is_configurable():
    r = ConsentRegistry("f", block_emergency_on_opt_out=False)
    r.opt_out("NABIDH", "2026-11-01T00:00")
    d = r.check(DR_A, "medications", "HospitalB", "2026-11-08T00:00", emergency=True,
                justification="critical", exchange="NABIDH")
    assert d.allowed and d.reason_code == "EMERGENCY_OVERRIDE"


@dataclass
class Rec:
    category: str
    source_org: str
    exchange: "str | None" = None


def test_authorize_records_filters_by_source(reg):
    recs = [Rec("medications", "HospitalA"), Rec("medications", "HospitalB"), Rec("labs", "HospitalC")]
    allowed, decisions = reg.authorize_records(DR_A, recs, "2026-11-02T10:00")
    assert [r.source_org for r in allowed] == ["HospitalA", "HospitalB"]  # own + granted; C has no grant
    assert [d.reason_code for d in decisions] == ["OWN_RECORDS", "GRANTED", "NO_GRANT"]


def test_every_change_and_decision_is_logged_in_order(reg):
    check(reg)
    reg.revoke_grant("G001", "2026-11-07T11:00")
    check(reg, at="2026-11-08T00:00")
    kinds = [e["kind"] for e in reg.log]
    assert kinds == ["grant_created", "access_decision", "grant_revoked", "access_decision"]
    assert [e["seq"] for e in reg.log] == [1, 2, 3, 4]
    assert reg.log[-1]["reason_code"] == "REVOKED" and reg.log[-1]["requester"] == "dr_a"


def test_log_is_read_only_view(reg):
    assert isinstance(reg.log, tuple)
