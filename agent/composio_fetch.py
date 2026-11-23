"""Stage 3b: re-fetch, through Composio, the pages behind quotes the shell could not check.

Some evidence quotes came through a web-fetch tool (src="web") from sites that block scripts or render with
JavaScript, so stage 3 could only mark them "unchecked_web". This stage asks Composio Connect MCP for a page
fetcher, fetches each cited URL, and saves the text to data/evidence_composio/<app id>_<n>.txt with a
"SOURCE_URL:" first line. check_quotes.py then checks those quotes against the copy of the page they cite.

Usage:
    export COMPOSIO_CONSUMER_KEY=ck_...                 # Composio Connect key, never written to disk
    python agent/composio_fetch.py                      # free keyless fetcher (shared hourly quota)
    python agent/composio_fetch.py --tool TAVILY_EXTRACT   # metered fetcher, renders JavaScript
Writes data/evidence_composio/*.txt and data/composio_run.json (per-URL log).
"""
import argparse
import json
import re
import time

from common import ROOT
from composio_mcp import ComposioMCP

OUT_DIR = ROOT / "data/evidence_composio"
LOG = ROOT / "data/composio_run.json"
BATCH = 2          # the free fetcher also caps requests per second; small batches avoid silent failures
RETRIES = 2


def unchecked_web_urls():
    """{url: app_id} for every quote stage 3 could not check."""
    report = json.load(open(ROOT / "data/pass2/quote_check.json"))
    urls = {}
    for row in report["rows"]:
        for quote in row["quotes"]:
            if quote["status"] == "unchecked_web" and quote.get("url"):
                urls.setdefault(quote["url"], row["id"])
    return urls


def tool_call(tool, url):
    if tool == "KEENABLE_FETCH_URL_PUBLIC":
        return {"tool_slug": tool, "arguments": {"url": url, "keenable_title": "toolkit-scout", "max_chars": 60000}}
    if tool == "TAVILY_EXTRACT":
        return {"tool_slug": tool, "arguments": {"urls": [url], "extract_depth": "advanced"}}
    raise SystemExit(f"unsupported tool {tool}")


def page_text(tool, response):
    data = (response or {}).get("data") or {}
    if tool == "KEENABLE_FETCH_URL_PUBLIC":
        return data.get("content") or ""
    results = data.get("results") or (data.get("response_data") or {}).get("results") or []
    return "\n".join(r.get("raw_content") or "" for r in results)


def fetch_batches(composio, tool, items, log):
    """Fetch (url, app_id) pairs in small batches; save good pages and log every attempt."""
    for start in range(0, len(items), BATCH):
        batch = items[start:start + BATCH]
        results, _ = composio.execute([tool_call(tool, url) for url, _ in batch])
        for (url, app_id), result in zip(batch, results):
            response = result.get("response") or {}
            text = page_text(tool, response) if response.get("successful") else ""
            ok = len(text) >= 200 and text.strip().lower() != "not found"
            error = response.get("error") or result.get("error") or (response.get("data") or {}).get("message")
            entry = {"app_id": app_id, "tool": tool, "ok": ok, "chars": len(text),
                     "error": None if ok else str(error or "empty or 'not found' page")[:160]}
            if ok:
                slug = re.sub(r"\W+", "_", url.split("//", 1)[-1])[:60]
                (OUT_DIR / f"{app_id}_{slug}.txt").write_text(f"SOURCE_URL: {url}\n{text}")
            log["pages"][url] = entry
            print(f"  {'ok ' if ok else 'ERR'} {app_id:>3} {url[:80]} {entry['error'] or entry['chars']}")
        if any("hourly limit" in str(r).lower() for r in results):
            print("  hourly quota used up; re-run later to continue")
            return False
        time.sleep(2)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", default="KEENABLE_FETCH_URL_PUBLIC")
    args = parser.parse_args()

    composio = ComposioMCP()
    found = composio.search_tools("fetch the text of a public web page URL", strategy="tool_search")
    print("Composio session", composio.session_id, "| fetchers offered:",
          [r.get("primary_tool_slugs") for r in (found.get("data") or {}).get("results", [])])

    log = json.load(open(LOG)) if LOG.exists() else {"runs": [], "pages": {}}
    OUT_DIR.mkdir(exist_ok=True)
    targets = unchecked_web_urls()
    for attempt in range(1 + RETRIES):
        items = [(u, i) for u, i in targets.items() if not log["pages"].get(u, {}).get("ok")]
        if not items:
            break
        if attempt:
            print(f"retry pass {attempt}: {len(items)} pages")
            time.sleep(20)
        if not fetch_batches(composio, args.tool, items, log):
            break
    log["runs"].append({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tool": args.tool,
                        "session": composio.session_id, "targets": len(targets)})
    json.dump(log, open(LOG, "w"), indent=1)
    print(f"{sum(p['ok'] for p in log['pages'].values())}/{len(log['pages'])} cited pages saved -> {OUT_DIR}")


if __name__ == "__main__":
    main()
