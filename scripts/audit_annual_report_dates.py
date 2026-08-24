"""Read-only audit of the publication dates of the 10 TERI annual reports.

Answers one question per report: does the document itself state when it was
published? Nothing is written, and no date is inferred from an edition label —
"Annual Report 2024-25" says what period the report covers, not when it came
out, and the two can be a year apart in either direction.

Evidence gathered per report, cheapest first:

* MySQL ``published_at`` (today's value) and ``edition_label``;
* the PDF DocInfo ``CreationDate`` and ``ModDate`` — *authoring* evidence, which
  Phase 0 established is frequently a re-export years after publication and is
  therefore never on its own a verified publication date;
* explicit publication statements in the front matter, quoted verbatim: the
  imprint page, a copyright line, an ISBN block, "first published", "printed",
  a month-and-year on the cover.

A report whose front matter states no publication date is reported as
NO VERIFIED DATE. That is a finding, not a gap to be filled.

PyMuPDF only — Document Intelligence is never called, and this module does not
import the extraction package.

    python -m scripts.audit_annual_report_dates
"""
from __future__ import annotations

import csv
import logging
import os
import re
import sys
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

OUT_DIR = os.path.join("reports", "phase0")
OUT_CSV = os.path.join(OUT_DIR, "annual_report_date_audit.csv")
OUT_MD = os.path.join(OUT_DIR, "annual_report_date_audit.md")
SITE = "https://teriin.org"

# Front matter only: an imprint or copyright statement lives in the first few
# pages. Scanning the whole report would surface every date it mentions.
FRONT_PAGES = 6

_MONTH = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
          r"jul(?:y)?|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|"
          r"dec(?:ember)?)")

# Phrases that would constitute a stated publication date. Each is captured with
# surrounding context so the reviewer sees the sentence, not just a regex hit.
_EVIDENCE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("explicit publication",
     r"[^.\n]{0,80}(?:date\s+of\s+publication|publication\s+date|"
     r"published\s+(?:on|in)|first\s+published|date\s+of\s+issue)"
     r"[^.\n]{0,80}"),
    ("imprint / published by",
     r"[^.\n]{0,60}published\s+by[^.\n]{0,120}"),
    ("copyright line",
     r"[^.\n]{0,40}(?:©|\(c\)|copyright)[^.\n]{0,90}"),
    ("isbn block",
     r"[^.\n]{0,40}isbn[^.\n]{0,80}"),
    ("printed / released",
     r"[^.\n]{0,60}(?:printed\s+(?:in|by|at)|released\s+(?:on|in))[^.\n]{0,80}"),
    ("month and year on the cover",
     r"(?<![a-z])" + _MONTH + r"\s+20\d{2}(?![0-9])"),
)


@dataclass
class Finding:
    document_id: str
    title: str
    edition: str
    current_published_at: str
    filename: str
    url: str
    pdf_created: str = ""
    pdf_modified: str = ""
    quotes: list[tuple[str, str]] = field(default_factory=list)
    fetch: str = ""
    pages: int = 0

    @property
    def has_stated_date(self) -> bool:
        """Only a phrase that names publication AND carries a full date counts."""
        for kind, quote in self.quotes:
            if kind in ("explicit publication", "printed / released") and \
                    re.search(r"\b\d{1,2}\b.*20\d{2}|20\d{2}", quote):
                return True
        return False

    def proposal(self) -> tuple[str, str, str]:
        """(proposed published_at, evidence, confidence)."""
        if self.fetch != "ok":
            return ("NO VERIFIED DATE",
                    f"PDF not readable ({self.fetch})", "none")
        for kind, quote in self.quotes:
            if kind == "explicit publication" and re.search(r"20\d{2}", quote):
                return (self._date_from(quote) or "NO VERIFIED DATE",
                        f"{kind}: {quote.strip()[:120]!r}", "high")
        # Everything else is authoring, imprint or coverage evidence. None of it
        # states when the document was published.
        kinds = ", ".join(sorted({k for k, _ in self.quotes})) or "none found"
        return ("NO VERIFIED DATE",
                f"no publication statement in the first {FRONT_PAGES} pages "
                f"(found: {kinds}; DocInfo created "
                f"{self.pdf_created or 'unreadable'} = authoring evidence only)",
                "none")

    @staticmethod
    def _date_from(quote: str) -> str:
        iso = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", quote)
        if iso:
            return iso.group(0)
        dmy = re.search(r"\b(\d{1,2})\s+(" + _MONTH + r")\.?,?\s+(20\d{2})\b",
                        quote, re.I)
        if dmy:
            return f"{dmy.group(1)} {dmy.group(2).title()} {dmy.group(3)}"
        mdy = re.search(r"\b(" + _MONTH + r")\.?\s+(\d{1,2}),?\s+(20\d{2})\b",
                        quote, re.I)
        if mdy:
            return f"{mdy.group(1).title()} {mdy.group(2)} {mdy.group(3)}"
        month_year = re.search(r"\b(" + _MONTH + r")\s+(20\d{2})\b", quote, re.I)
        if month_year:
            # Month precision only: a day would be invented, so this is not a
            # usable published_at even though it is real evidence.
            return ""
        return ""


def annual_reports() -> list[dict]:
    """The 10 in-body annual-report documents, from the catalog. SELECT only."""
    from app.catalog.db import state_table
    from app.core.clients import mysql_connection

    with mysql_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT document_id, title, source_key, published_at FROM `{state_table()}` "
            "WHERE source_type = 'pdf_attachment' AND document_id LIKE 'inbody:%%' "
            "AND title LIKE 'Annual Report %%' ORDER BY title"
        )
        return list(cur.fetchall())


def editions() -> dict[str, str]:
    """edition_label per document, from the Qdrant payloads."""
    from qdrant_client import models as qm

    from app.config import get_settings
    from app.core.clients import get_qdrant_client

    client = get_qdrant_client()
    points, _ = client.scroll(
        collection_name=get_settings().qdrant_collection,
        scroll_filter=qm.Filter(must=[qm.FieldCondition(
            key="source_type", match=qm.MatchValue(value="pdf_attachment"))]),
        limit=20000, with_payload=["document_id", "edition_label"], with_vectors=False,
    )
    out: dict[str, str] = {}
    for point in points:
        payload = point.payload or {}
        if payload.get("edition_label"):
            out.setdefault(str(payload.get("document_id")),
                           str(payload["edition_label"]))
    return out


def read_front_matter(session: requests.Session, url: str) -> tuple[str, str, str, int, str]:
    """(text, DocInfo created, DocInfo modified, page count, status)."""
    absolute = url if url.startswith("http") else SITE + url
    try:
        response = session.get(absolute, timeout=240)
        if response.status_code != 200:
            return "", "", "", 0, f"http_{response.status_code}"
        import fitz

        from app.ingestion.date_candidates import parse_pdf_date

        with fitz.open(stream=response.content, filetype="pdf") as doc:
            meta = doc.metadata or {}
            pages = doc.page_count
            text = " ".join(
                (doc[i].get_text("text") or "")
                for i in range(min(FRONT_PAGES, pages))
            )
        return (" ".join(text.split()),
                (parse_pdf_date(meta.get("creationDate")) or "")[:10],
                (parse_pdf_date(meta.get("modDate")) or "")[:10],
                pages, "ok")
    except requests.RequestException as exc:
        return "", "", "", 0, type(exc).__name__
    except Exception as exc:  # a corrupt or encrypted PDF
        return "", "", "", 0, f"{type(exc).__name__}"


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    os.makedirs(OUT_DIR, exist_ok=True)

    rows = annual_reports()
    edition_by_doc = editions()
    print(f"auditing {len(rows)} annual-report documents (read-only)\n")

    findings: list[Finding] = []
    with requests.Session() as session:
        for row in rows:
            url = row.get("source_key") or ""
            text, created, modified, pages, status = read_front_matter(session, url)
            finding = Finding(
                document_id=row["document_id"],
                title=str(row.get("title") or ""),
                edition=edition_by_doc.get(row["document_id"], ""),
                current_published_at=str(row.get("published_at") or "")[:19],
                filename=url.split("?")[0].rsplit("/", 1)[-1],
                url=url,
                pdf_created=created, pdf_modified=modified,
                pages=pages, fetch=status,
            )
            lowered = text.lower()
            for kind, pattern in _EVIDENCE_PATTERNS:
                for match in re.finditer(pattern, lowered, re.I):
                    quote = " ".join(text[match.start():match.end()].split())
                    if quote and (kind, quote) not in finding.quotes:
                        finding.quotes.append((kind, quote))
                        break          # one representative quote per kind
            findings.append(finding)
            proposed, evidence, confidence = finding.proposal()
            print(f"  {finding.filename[:34]:<36}{status:<12}"
                  f"{proposed:<20}{confidence}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "document_id", "title", "edition", "current_published_at",
            "proposed_published_at", "evidence", "confidence",
            "pdf_created_authoring_only", "pdf_modified", "pages", "fetch", "url",
        ])
        for finding in findings:
            proposed, evidence, confidence = finding.proposal()
            writer.writerow([
                finding.document_id, finding.title, finding.edition,
                finding.current_published_at, proposed, evidence, confidence,
                finding.pdf_created, finding.pdf_modified, finding.pages,
                finding.fetch, finding.url,
            ])

    lines = ["# Annual report publication dates — read-only audit\n",
             "No date is derived from an edition label. A PDF DocInfo "
             "`CreationDate` is authoring evidence and never on its own a "
             "publication date, so a report whose front matter states none is "
             "reported as **NO VERIFIED DATE**.\n",
             "| document_id | title | edition | current_published_at "
             "| proposed_published_at | evidence | confidence |",
             "|---|---|---|---|---|---|---|"]
    for finding in findings:
        proposed, evidence, confidence = finding.proposal()
        lines.append(
            f"| `{finding.document_id[:24]}…` | {finding.title} | {finding.edition} "
            f"| {finding.current_published_at} | **{proposed}** "
            f"| {evidence.replace('|', '/')[:150]} | {confidence} |")

    lines.append("\n## Evidence found per report\n")
    for finding in findings:
        lines.append(f"\n### {finding.title} — `{finding.filename}`\n")
        lines.append(f"- pages: {finding.pages} · fetch: {finding.fetch}")
        lines.append(f"- DocInfo created: {finding.pdf_created or 'unreadable'} "
                     f"(authoring evidence only) · modified: "
                     f"{finding.pdf_modified or 'unreadable'}")
        if finding.quotes:
            for kind, quote in finding.quotes:
                lines.append(f"- {kind}: `{quote[:160]}`")
        else:
            lines.append("- no imprint, copyright, ISBN or publication phrase "
                         "found in the front matter")

    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {OUT_MD}\nwrote {OUT_CSV}")
    print("\nNothing was written to MySQL or Qdrant.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
