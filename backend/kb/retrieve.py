"""Inspectable BM25 retrieval over kb/chunks/*.jsonl (standard library only).

    from backend.kb.retrieve import KnowledgeBase
    kb = KnowledgeBase()
    for hit in kb.search("consent for sharing health data", k=5, scope="Dubai"):
        print(hit["citation"], hit["score"])

CLI: python -m backend.kb.retrieve "query" [scope-substring]
"""
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

CHUNKS = Path(__file__).resolve().parents[2] / "kb" / "chunks"
STOP = frozenset("the of and to in a an or for by be is are as on at with that this it its from shall may any "
                 "such which their has have been not no under into other than all".split())


def tokenize(text: str):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 1]


def citation(c: dict) -> str:
    where = c["section"] if c["section"].startswith("p.") else f"{c['section']}, p.{c['page']}"
    return f"{c['document']}, {where} [{c['chunk_id']}]"


class KnowledgeBase:
    def __init__(self, chunks_dir: Path = CHUNKS, k1: float = 1.5, b: float = 0.75):
        self.chunks = [json.loads(line) for f in sorted(chunks_dir.glob("*.jsonl"))
                       for line in open(f, encoding="utf-8")]
        self.by_id = {c["chunk_id"]: c for c in self.chunks}
        self.k1, self.b = k1, b
        self.tf = [Counter(tokenize(c["section"] + " " + c["text"])) for c in self.chunks]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = sum(self.len) / max(len(self.len), 1)
        df = Counter(w for t in self.tf for w in t)
        n = len(self.chunks)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def search(self, query: str, k: int = 5, scope: str | None = None, doc_id: str | None = None):
        """Top-k chunks by BM25. `scope` filters by substring of the scope field (e.g. "Dubai", "EU")."""
        q = tokenize(query)
        hits = []
        for i, c in enumerate(self.chunks):
            if (scope and scope.lower() not in c["scope"].lower()) or (doc_id and c["doc_id"] != doc_id):
                continue
            if c["text"].count("http") >= 4 and "http" not in query.lower():
                continue  # bibliography/reference-list chunk: matches keywords but carries no provisions
            tf, dl, score = self.tf[i], self.len[i], 0.0
            for w in q:
                f = tf.get(w)
                if f:
                    score += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avg))
            if score > 0:
                hits.append({**c, "score": round(score, 3), "citation": citation(c)})
        return sorted(hits, key=lambda h: -h["score"])[:k]

    def get(self, chunk_id: str):
        return self.by_id.get(chunk_id)


if __name__ == "__main__":
    kb = KnowledgeBase()
    for h in kb.search(sys.argv[1], k=5, scope=sys.argv[2] if len(sys.argv) > 2 else None):
        print(f"{h['score']:6.2f}  {h['citation']}\n        {h['text'][:200]}\n")
