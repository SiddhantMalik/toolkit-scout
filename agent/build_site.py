"""Render site/index.html (one self-contained file) from site/template.html, style.css and app.js.

Template tokens look like {{name}}; values come from report.build_context(). A token with no value is an error,
so a typo can never ship silently.
"""
import base64
import re

from common import ROOT
from report import build_context

SITE = ROOT / "site"


FONTS = [("Inter", "inter-latin-wght-normal.woff2", "100 900"),
         ("JetBrains Mono", "jetbrains-mono-latin-400-normal.woff2", "400")]


def font_faces():
    """Embed the fonts as data URIs so the page is one file that works offline (Inter and JetBrains Mono, OFL)."""
    faces = []
    for family, file, weight in FONTS:
        data = base64.b64encode((SITE / "fonts" / file).read_bytes()).decode()
        faces.append(f'@font-face{{font-family:"{family}";font-style:normal;font-weight:{weight};font-display:swap;'
                     f'src:url(data:font/woff2;base64,{data}) format("woff2")}}')
    return "\n".join(faces)


def render():
    context = build_context()
    page = (SITE / "template.html").read_text()
    page = page.replace("/*STYLE*/", (SITE / "style.css").read_text().replace("/*FONTS*/", font_faces())).replace("/*SCRIPT*/", (SITE / "app.js").read_text())
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", page)) - set(context))
    if missing:
        raise SystemExit(f"template tokens without a value: {missing}")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: context[m.group(1)], page)


if __name__ == "__main__":
    page = render()
    (SITE / "index.html").write_text(page)
    print(f"built site/index.html ({len(page) // 1024} KB)")
