"""Render site/index.html (one self-contained file) from site/template.html, style.css and app.js.

Template tokens look like {{name}}; values come from report.build_context(). A token with no value is an error,
so a typo can never ship silently.
"""
import re

from common import ROOT
from report import build_context

SITE = ROOT / "site"


def render():
    context = build_context()
    page = (SITE / "template.html").read_text()
    page = page.replace("/*STYLE*/", (SITE / "style.css").read_text()).replace("/*SCRIPT*/", (SITE / "app.js").read_text())
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", page)) - set(context))
    if missing:
        raise SystemExit(f"template tokens without a value: {missing}")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: context[m.group(1)], page)


if __name__ == "__main__":
    page = render()
    (SITE / "index.html").write_text(page)
    print(f"built site/index.html ({len(page) // 1024} KB)")
