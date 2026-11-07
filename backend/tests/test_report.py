"""Report content tests: every authored citation must exist in the KB, and the verifier must catch bad ones."""
import pytest

from backend.kb.retrieve import KnowledgeBase
from backend.report import content as C
from backend.report.build import Verifier, adjudicate


@pytest.fixture(scope="module")
def v():
    return Verifier(KnowledgeBase())


def all_citations():
    for comp, _, _, _, cites in C.Y3172_ROWS:
        for cid, ph in cites:
            yield f"y3172:{comp}", cid, ph
    for lens, _, _, _, cites in C.READINESS_ROWS:
        for cid, ph in cites:
            yield f"readiness:{lens}", cid, ph
    for req, provs, _, _ in C.POLICY_ROWS:
        for _, cid, ph in provs:
            yield f"policy:{req}", cid, ph
    for g in C.GAPS:
        for _, cid, ph in g["evidence"] + g["comparison"]:
            yield f"gap:{g['id']}", cid, ph


def test_every_authored_citation_is_verified_in_the_kb(v):
    for where, cid, ph in all_citations():
        v.cite(cid, ph, where)
    assert not v.errors, v.errors


def test_verifier_catches_wrong_phrase_and_missing_chunk(v):
    bad = Verifier(v.kb)
    bad.cite("uae-health-ict-law-2019#0016", "a phrase that is not there", "t")
    bad.cite("no-such-doc#0001", "x", "t")
    assert len(bad.errors) == 2


def test_statuses_use_the_agreed_vocabulary():
    allowed = {"implemented", "partial", "simulated", "not implemented"}
    for row in C.Y3172_ROWS + C.READINESS_ROWS:
        assert row[3] in allowed
    assert all(r[3] in allowed for r in C.POLICY_ROWS)


def test_gap_absence_scans_are_computed_not_typed(v):
    g1 = next(g for g in C.GAPS if g["id"] == "G1")
    docs, pattern, _ = g1["scans"][0]
    assert v.scan(docs, pattern) == 0  # no opt-out wording in the Abu Dhabi policy
    assert v.scan(["dha-consent-access-standard-2025"], pattern) > 0  # control: it exists in the Dubai standard


def test_adjudication_lookup():
    assert "Valid alternative" in adjudicate(5, "cites uae-health-ict-law-2019 ('health and safety of the patient')")
    assert "Unadjudicated" in adjudicate(1, "something nobody reviewed")
