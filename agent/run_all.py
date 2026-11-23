"""One command to regenerate every derived artefact from the committed research data.

    python agent/run_all.py              # offline: gate -> score -> analyze -> build page (about 5 seconds)
    python agent/run_all.py --research   # also re-fetch evidence first (needs network; stage 2 LLM extraction is separate)
"""
import subprocess
import sys

from common import ROOT

OFFLINE_STEPS = [
    ["gate.py"],
    ["score.py", "pass2a=data/pass2/pass2a.jsonl", "pass2b=data/pass2/pass2b.jsonl", "pass2b_v3=data/pass2/pass2c.jsonl"],
    ["analyze.py"],
    ["build_site.py"],
]
RESEARCH_STEPS = [["fetch_evidence.py"], ["mcp_probe.py"]]


def run(step):
    print("->", " ".join(step), flush=True)
    done = subprocess.run([sys.executable, str(ROOT / "agent" / step[0]), *step[1:]], cwd=ROOT, capture_output=True, text=True)
    if done.returncode:
        sys.exit(f"step failed: {step[0]}\n{done.stderr[-1500:]}")
    print("   " + (done.stdout.strip().splitlines() or ["ok"])[-1][:140])


if __name__ == "__main__":
    for step in (RESEARCH_STEPS if "--research" in sys.argv else []) + OFFLINE_STEPS:
        run(step)
    print("done: site/index.html, data/final.json, data/scores.json")
