"""Stage 3 verifier: does each evidence quote really appear in the page text we saved for that app?

Compares whitespace/case/punctuation-normalised text of each quote with data/evidence/<id>.txt and
data/evidence_extra/<id>_*.txt. This checks the quote against everything saved for the app; it does NOT
check that the text came from the cited URL. Quotes tagged src="web" came through a web-fetch tool with no saved
copy, so they are reported as "unchecked_web" rather than verified, unless stage 3b (composio_fetch.py) saved
a copy of the cited URL in data/evidence_composio/; then the quote is checked against that page alone.

Usage:  python agent/check_quotes.py data/pass2/pass2a.jsonl > data/pass2/quote_check.json
"""
import glob
import json
import re
import sys

from common import ROOT

MIN_QUOTE_CHARS = 12   # shorter "quotes" (package slugs, single words) are trivially findable and are rejected


def norm(text):
    """Lower-case and collapse everything that is not a letter or digit (any script) into single spaces."""
    return re.sub(r"[\W_]+", " ", text.lower()).strip()


def saved_text(app_id):
    """All page text saved for an app, normalised."""
    paths = [ROOT / f"data/evidence/{app_id}.txt", *sorted(glob.glob(str(ROOT / f"data/evidence_extra/{app_id}_*.txt")))]
    chunks = []
    for path in paths:
        try:
            chunks.append(open(path, errors="ignore").read())
        except FileNotFoundError:
            continue
    return norm(" ".join(chunks))


def composio_pages():
    """{cited url: normalised text} for pages re-fetched through Composio (stage 3b)."""
    pages = {}
    for path in glob.glob(str(ROOT / "data/evidence_composio/*.txt")):
        first, _, body = open(path, errors="ignore").read().partition("\n")
        pages[first.removeprefix("SOURCE_URL: ").strip()] = norm(body)
    return pages


COMPOSIO_PAGES = composio_pages()


def quote_status(evidence, corpus):
    quote = norm(evidence.get("quote", ""))
    if len(quote) < MIN_QUOTE_CHARS:
        return "unverified"
    if quote in corpus:
        return "verified"
    if evidence.get("src") == "web":
        cited_copy = COMPOSIO_PAGES.get(evidence.get("url"))
        if cited_copy is None:
            return "unchecked_web"
        return "verified" if quote in cited_copy else "unverified"
    return "unverified"


def check_file(path):
    rows, summary = [], {"verified": 0, "unverified": 0, "unchecked_web": 0}
    with open(path) as handle:
        for line in filter(str.strip, handle):
            record = json.loads(line)
            corpus = saved_text(record["id"])
            results = []
            for evidence in record.get("evidence", []):
                status = quote_status(evidence, corpus)
                summary[status] += 1
                results.append({"field": evidence.get("field"), "url": evidence.get("url"), "status": status})
            rows.append({"id": record["id"], "name": record["name"], "quotes": results})
    return rows, summary


if __name__ == "__main__":
    all_rows, totals = [], {"verified": 0, "unverified": 0, "unchecked_web": 0}
    for file_path in sys.argv[1:]:
        file_rows, file_summary = check_file(file_path)
        all_rows += file_rows
        totals = {k: totals[k] + file_summary[k] for k in totals}
    print(json.dumps({"summary": totals, "rows": all_rows}, indent=1))
