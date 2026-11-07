"""Extract and chunk the policy knowledge base.

Reads kb/raw/<id>/source.pdf, writes kb/chunks/<id>.jsonl and kb/MANIFEST.md.
Chunks are split by "Article N" for legislation and by page-aware paragraph windows
for policies/strategies. Every chunk carries document, section, page, URL and retrieval date.

    python backend/kb/ingest.py
"""
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
RAW, OUT = ROOT / "kb" / "raw", ROOT / "kb" / "chunks"
RETRIEVED = "2026-11-07"
MAX_CHARS = 2200

# id -> metadata. `split` is "article" or "window". Sources are the URLs actually downloaded.
DOCS = {
    "uae-health-ict-law-2019": dict(
        title="Federal Law No. (2) of 2019 Concerning the Use of ICT in Health Fields",
        issuer="UAE Federal Government", kind="law", scope="UAE federal", split="article",
        url="https://uaelegislation.gov.ae/en/legislations/1209", file="source.pdf"),
    "uae-health-ict-exec-reg-2020": dict(
        title="Cabinet Resolution No. (32) of 2020, Executive Regulation of Federal Law No. (2) of 2019",
        issuer="UAE Cabinet", kind="regulation", scope="UAE federal", split="article",
        url="https://uaelegislation.gov.ae/en/legislations/1444", file="source.pdf"),
    "uae-pdpl-2021": dict(
        title="Federal Decree-Law No. (45) of 2021 Concerning the Protection of Personal Data",
        issuer="UAE Federal Government", kind="law", scope="UAE federal", split="article",
        url="https://uaelegislation.gov.ae/en/legislations/1972", file="source.pdf"),
    "uae-ai-strategy-2031": dict(
        title="UAE National Strategy for Artificial Intelligence 2031",
        issuer="UAE Government", kind="strategy", scope="UAE federal", split="window",
        url="https://ai.gov.ae/wp-content/uploads/2021/07/UAE-National-Strategy-for-Artificial-Intelligence-2031.pdf",
        file="source.pdf"),
    "dha-health-info-sharing-2024": dict(
        title="Policy for Health Information Sharing (2024)",
        issuer="Dubai Health Authority", kind="policy", scope="Dubai", split="window",
        url="https://dha.gov.ae/uploads/082024/Policy%20for%20Health%20Information%20Sharing_EN202480306.pdf",
        file="source.pdf"),
    "dha-consent-access-standard-2025": dict(
        title="Standards for Health Information Consent and Access Control, Version 1 (2025)",
        issuer="Dubai Health Authority", kind="standard", scope="Dubai", split="window",
        url="https://dha.gov.ae/uploads/012025/Standards%20for%20Consnet%20and%20Access%20Control2025129762.pdf",
        file="source.pdf"),
    "doh-hie-policy-2020": dict(
        title="DoH Policy on the Abu Dhabi Health Information Exchange (April 2020)",
        issuer="Abu Dhabi Department of Health", kind="policy", scope="Abu Dhabi", split="window",
        url="https://doh.gov.ae/-/media/A78104416DF2440E89AC90FB75F11055.ashx", file="source.pdf"),
    "eu-gdpr-2016-679": dict(
        title="Regulation (EU) 2016/679 (GDPR)",
        issuer="European Union", kind="law", scope="EU (comparator)", split="article",
        url="https://eur-lex.europa.eu/eli/reg/2016/679/oj", file="source.pdf"),
    "eu-ehds-2025-327": dict(
        title="Regulation (EU) 2025/327 on the European Health Data Space",
        issuer="European Union", kind="law", scope="EU (comparator)", split="article",
        url="https://eur-lex.europa.eu/eli/reg/2025/327/oj", file="source.pdf"),
    "itu-t-y3172": dict(
        title="ITU-T Y.3172 Architectural framework for machine learning in future networks including IMT-2020 (06/2019)",
        issuer="ITU", kind="standard", scope="ITU (reference)", split="window",
        url="https://www.itu.int/rec/T-REC-Y.3172/en", file="source.pdf"),
    "itu-ai-readiness": dict(
        title="ITU AI Ready: Analysis Towards a Standardized Readiness Framework, Report 2.0 (January 2026)",
        issuer="ITU", kind="framework", scope="ITU (reference)", split="window",
        url="https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf", file="source.pdf"),
    "dha-ai-policy-2021": dict(
        title="DHA Policy: Artificial Intelligence in the Healthcare (DHA/HISHD/PP-09, effective 1 July 2021)",
        issuer="Dubai Health Authority", kind="policy", scope="Dubai", split="window",
        url="https://www.dha.gov.ae/uploads/082022/Artificial%20Intelligence%20Policy20228457.pdf", file="source.pdf"),
    "doh-circular-2026-10-malaffi-onboarding": dict(
        title="DoH Circular 2026/10: Mandatory On-boarding of Minimum Required Dataset with Malaffi",
        issuer="Abu Dhabi Department of Health", kind="circular", scope="Abu Dhabi", split="window",
        url="https://www.doh.gov.ae/-/media/84A213F71AA545D69E01A23A0A99C598.ashx", file="source.bin"),
    "doh-circular-2026-144-malaffi-referrals": dict(
        title="DoH Circular 2026/144: Mandatory Submission of Referral Data to Malaffi",
        issuer="Abu Dhabi Department of Health", kind="circular", scope="Abu Dhabi", split="window",
        url="https://www.doh.gov.ae/-/media/C01533BB56EE4A7D9B75107C89656941.ashx", file="source.bin"),
}

ARTICLE = re.compile(r"^\s*Article\s*\(?\s*(\d+)\s*\)?\s*$|^\s*Article\s*\(?\s*(\d+)\s*\)?\s*[-:.]")
ARABIC = re.compile(r"[؀-ۿ]")


def read_lines(path: Path):
    """Yield (page_number, line) with Arabic-script and empty lines dropped."""
    for n, page in enumerate(PdfReader(str(path)).pages, start=1):
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            if line and not ARABIC.search(line):
                yield n, line


def split_long(section, page, text):
    if len(text) <= MAX_CHARS:
        return [(section, page, text)]
    parts, cur = [], ""
    for para in re.split(r"(?<=[.;:])\s+", text):
        if cur and len(cur) + len(para) > MAX_CHARS:
            parts.append(cur)
            cur = ""
        cur = f"{cur} {para}".strip()
    if cur:
        parts.append(cur)
    return [(f"{section} (part {i})", page, p) for i, p in enumerate(parts, 1)]


def chunk_articles(lines):
    out, section, page, buf = [], "Preamble", 1, []
    for n, line in lines:
        m = ARTICLE.match(line)
        if m:
            if buf:
                out += split_long(section, page, " ".join(buf))
            section, page, buf = f"Article {m.group(1) or m.group(2)}", n, []
        else:
            buf.append(line)
    if buf:
        out += split_long(section, page, " ".join(buf))
    return out


def chunk_windows(lines):
    out, buf, start = [], "", 1
    for n, line in lines:
        if not buf:
            start = n
        buf = f"{buf} {line}".strip()
        if len(buf) >= 1400 and line.endswith((".", ":", ";")):
            out.append((f"p.{start}", start, buf))
            buf = ""
    if buf:
        out.append((f"p.{start}", start, buf))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for doc_id, meta in DOCS.items():
        src = RAW / doc_id / meta["file"]
        lines = list(read_lines(src))
        pieces = chunk_articles(lines) if meta["split"] == "article" else chunk_windows(lines)
        pieces = [p for p in pieces if len(p[2]) > 40]
        with open(OUT / f"{doc_id}.jsonl", "w", encoding="utf-8") as f:
            for i, (section, page, text) in enumerate(pieces, 1):
                f.write(json.dumps({
                    "chunk_id": f"{doc_id}#{i:04d}", "doc_id": doc_id, "document": meta["title"],
                    "section": section, "page": page, "issuer": meta["issuer"], "scope": meta["scope"],
                    "kind": meta["kind"], "url": meta["url"], "retrieved": RETRIEVED,
                    "language": "en", "text": text}, ensure_ascii=False) + "\n")
        rows.append((doc_id, meta, len(PdfReader(str(src)).pages), len(pieces)))
        print(f"{doc_id}: {len(pieces)} chunks")

    md = ["# Policy knowledge base manifest", "",
          f"Generated by `backend/kb/ingest.py`. Retrieved {RETRIEVED}. English text only (Arabic script is dropped; the Arabic original prevails legally).",
          "Raw files: `kb/raw/<id>/`. Chunks: `kb/chunks/<id>.jsonl`.", "",
          "| ID | Document | Issuer | Scope | Type | Pages | Chunks | Source |", "|---|---|---|---|---|---|---|---|"]
    for doc_id, m, pages, n in rows:
        md.append(f"| `{doc_id}` | {m['title']} | {m['issuer']} | {m['scope']} | {m['kind']} | {pages} | {n} | {m['url']} |")
    (ROOT / "kb" / "MANIFEST.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
