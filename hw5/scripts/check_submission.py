"""Pre-push check: is the repo complete, and safe to share publicly?

No model calls and no database writes. It checks the files git will share (tracked, plus new files that
aren't ignored): required files, ignore rules, secrets, the model name, outputs, the cash math, the
prompt log, the harness tables and the Reflection approvals.

Run from hw5/:  python scripts/check_submission.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
ROOT = PROJECT.parent
results: list[tuple[bool, str]] = []


def check(ok: bool, what: str) -> None:
    results.append((bool(ok), what))


def shared() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f]


def text(rel: str) -> str:
    return (PROJECT / rel).read_text(encoding="utf-8")


def main() -> int:
    files = shared()
    in_hw5 = [f[len("hw5/"):] for f in files if f.startswith("hw5/")]

    required = ["README.md", "requirements.txt", ".env.example", ".gitignore", ".mcp.json", "output/github_url.txt", "data/campus_customs_new.db", "AI_prompts.md", "EVIDENCE_CHECKLIST.md",
                "mcp_server/server.py", "mcp_server/README.md", "backend/main.py", "backend/team.py", "backend/audit.py",
                "backend/config.py", "backend/models.py", "backend/mcp_tools.py", "frontend/package.json", "frontend/src/App.tsx",
                "data/campus_customs.db", "output/harness.md", "output/design.md", "output/desk_tickets.html",
                "output/resolved_tickets.json", "output/resolved_board.html", "output/audit_trail.json",
                "output/route_check.json", "output/mcp_tool_check.json", "scripts/reset_db.py"]
    missing = [r for r in required if r not in in_hw5]
    check(not missing, f"required files are shared ({len(required) - len(missing)} of {len(required)})" + (f": missing {missing}" if missing else ""))
    for a in ["boss", "inventory", "accounting", "facilities", "customer_service"]:
        check(f"backend/prompts/{a}.md" in in_hw5 and f"backend/agents/{a}.py" in in_hw5, f"agent {a}: prompt and code shared")

    # ignore rules and secrets
    check(not [f for f in files if Path(f).name == ".env"], "no .env file is shared")
    check("hw5/data/campus_customs.db" in files and "hw5/data/campus_customs_new.db" in files, "both databases are shared under data/ (the original and the working copy)")
    url = text("output/github_url.txt").strip()
    check(re.fullmatch(r"https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9._-]+", url) is not None, f"output/github_url.txt holds the repo URL ({url})")
    check(not [f for f in files if "/.venv/" in f or f.startswith(".venv/") or "node_modules/" in f], "no .venv or node_modules is shared")
    secrets = {}
    env = PROJECT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if k.strip() in ("PORTKEY_API_KEY", "OPENAI_API_KEY", "HUMAN_APPROVAL_CODE", "DESK_PIN") and len(v) >= 4:
                    secrets[k.strip()] = v
    leaks, keyish, models = [], [], set()
    for f in files:
        try:
            t = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        leaks += [f"{k} in {f}" for k, v in secrets.items() if v in t]
        if re.search(r"\b(sk|pk)-[A-Za-z0-9_\-]{16,}", t):
            keyish.append(f)
        models |= {m.rstrip(".") for m in re.findall(r"\bgpt-[0-9][\w.\-]*", t)}
    if env.exists():
        check(secrets and not leaks, f"no secret value from .env appears in any shared file ({len(secrets)} secrets checked)" + (f": {leaks}" if leaks else ""))
    else:
        check(True, "no .env in this copy, so there are no secret values to leak")
    check(not keyish, "no key-looking strings in shared files" + (f": {keyish}" if keyish else ""))
    other = models - {"gpt-6-luna", "gpt-6-luna-global"}  # gpt-6-luna-global is Portkey's reply name for gpt-6-luna
    check(not other, f"only gpt-6-luna is named anywhere (found {sorted(models)})")
    check('"gpt-6-luna"' in text("backend/config.py"), "backend/config.py locks the model to gpt-6-luna")
    req = text("requirements.txt")
    check("pydantic-ai-slim" in req and not re.search(r"^pydantic-ai[=\[]", req, re.M), "requirements use pydantic-ai-slim, not the full pydantic-ai")
    check(all(re.search(r"==", line) for line in req.splitlines() if line.strip() and not line.startswith("#")), "requirements are pinned")

    # the original database is byte-identical to the committed one
    committed = subprocess.run(["git", "show", "HEAD:hw5/data/campus_customs.db"], cwd=ROOT, capture_output=True).stdout
    check(committed and committed == (PROJECT / "data/campus_customs.db").read_bytes(), "data/campus_customs.db matches the committed original")

    # outputs
    for page in ["output/desk_tickets.html", "output/resolved_board.html"]:
        h = text(page)
        ext = re.findall(r'(?:src|href)\s*=\s*["\']https?://', h) + re.findall(r"<link[^>]+stylesheet|<script[^>]+src=", h)
        check(not ext, f"{page} is self-contained (no external files)")
    R = json.loads(text("output/resolved_tickets.json"))
    c = R["cash"]
    math_ok = round(c["starting_checking_balance"] + sum(x["change"] for x in c["changes"]), 2) == c["ending_checking_balance_by_math"]
    check(math_ok and c["matches_cash_accounts"] and c["ending_checking_balance_by_math"] == c["ending_checking_balance_in_cash_accounts"],
          f"cash math: {c['math']}, matching cash_accounts")
    check([t["id"] for t in R["tickets"]] == [101, 102, 103] and all(t["agents"] and t["outcome"] for t in R["tickets"]),
          "resolved_tickets.json has 101, 102 and 103, each with agents and an outcome")
    d = text("output/desk_tickets.html")
    check("To be filled in after the agents resolve" not in d and d.count("Compared with Expected") >= 3, "desk tickets: all three Actual sections are filled in")
    check(d.count('class="qa"') == 5 and d.count("☑ Approved by Boss") >= 9, "desk tickets: 5 Reflection answers, each approved")
    trail = json.loads(text("output/audit_trail.json"))
    check(isinstance(trail, list) and len(trail) > 1000, f"audit trail is a JSON list ({len(trail):,} entries)")
    rc = json.loads(text("output/route_check.json"))
    check(rc["steps_passed"] == rc["steps_total"], f"route check: {rc['steps_passed']} of {rc['steps_total']}")
    tc = json.loads(text("output/mcp_tool_check.json"))
    passed = [x.get("passed") for x in tc.get("checks", [])] if isinstance(tc, dict) else []
    check(passed and all(passed), f"MCP tool check: {sum(passed)} of {len(passed)}")

    # docs
    log = text("AI_prompts.md")
    probs = [n for n in range(1, 12) if re.search(rf"^## Problem {n}: ", log, re.M)]
    check(probs == list(range(1, 12)), f"AI_prompts.md has a section for Problems 1–11 (found {probs})")
    nums = sorted({int(n) for n in re.findall(r"^\*\*Table (\d+):", text("output/harness.md"), re.M)})
    check(nums == list(range(0, 31)), f"harness tables are numbered 0–30 with no gaps (found {len(nums)})")
    readme = text("README.md")
    check("<!-- tree:start -->\n```text\nhw5/" in readme and "github_url.txt" in readme, "README has the setup steps and the expected file layout")
    check(all(k in readme for k in ["scripts/reset_db.py", "mcp_server/server.py", "uvicorn main:app", "npm run dev", "Reset the database first"]),
          "README explains: copy the original DB for a clean run, start the MCP server, the backend and the board, and reset before a full run")
    import sqlite3
    w = sqlite3.connect(f"file:{(PROJECT / 'data/campus_customs_new.db').as_posix()}?mode=ro", uri=True)
    bal = w.execute("SELECT balance FROM cash_accounts WHERE name = 'checking'").fetchone()[0]
    w.close()
    check(round(bal, 2) == c["ending_checking_balance_in_cash_accounts"], f"the committed working database's checking (${bal:,.2f}) matches resolved_tickets.json")

    for ok, what in results:
        print(("PASS  " if ok else "FAIL  ") + what)
    n = sum(ok for ok, _ in results)
    print(f"\n{n}/{len(results)} checks passed")
    return 0 if n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
