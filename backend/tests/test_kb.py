"""KB tests: every chunk is citable, and key provisions are retrievable.

Run: python -m pytest backend/tests -q   (after python backend/kb/ingest.py)
"""
import pytest

from backend.kb.retrieve import KnowledgeBase

REQUIRED_FIELDS = {"chunk_id", "doc_id", "document", "section", "page", "url", "retrieved", "scope", "text"}


@pytest.fixture(scope="module")
def kb():
    return KnowledgeBase()


def test_every_chunk_has_citation_fields(kb):
    assert kb.chunks, "run backend/kb/ingest.py first"
    for c in kb.chunks:
        assert REQUIRED_FIELDS <= c.keys(), c["chunk_id"]
        assert c["url"].startswith("http") and c["text"].strip()


def test_chunk_ids_unique_and_resolvable(kb):
    assert len(kb.by_id) == len(kb.chunks)
    for hit in kb.search("consent health information sharing", k=5):
        assert kb.get(hit["chunk_id"]) is not None


@pytest.mark.parametrize("query,scope,doc_id,needle", [
    ("storing health data outside the state", "UAE federal", "uae-health-ict-law-2019", "outside State"),
    ("universal patient participation mandatory", "Abu Dhabi", "doh-hie-policy-2020", "Universal"),
    ("right to withdraw consent opt-out", "Dubai", "dha-consent-access-standard-2025", "opt-out"),
])
def test_key_provisions_retrievable(kb, query, scope, doc_id, needle):
    hits = kb.search(query, k=5, scope=scope)
    assert any(h["doc_id"] == doc_id and needle.lower() in h["text"].lower() for h in hits)


def test_scope_filter(kb):
    assert all("EU" in h["scope"] for h in kb.search("personal data processing consent", k=5, scope="EU"))
