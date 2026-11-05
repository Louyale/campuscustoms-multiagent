"""Write the assignment's expected file layout into README.md, between the <!-- tree:start --> and
<!-- tree:end --> markers, and prove every file in it is really in the repo.

The layout is exactly the one in the Problem 11 instructions. Each listed path is checked against
the files git will share (tracked, plus new files that aren't ignored). If any is missing, the
script stops and says which, so the README never shows a file the grader won't find.

Run from hw5/:  python scripts/make_tree.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
README = PROJECT / "README.md"

# (depth, name); a name ending in "/" is a folder
LAYOUT = [
    (0, "hw5/"),
    (1, "AI_prompts.md"), (1, "requirements.txt"), (1, ".env.example"), (1, ".gitignore"), (1, ".mcp.json"), (1, "README.md"),
    (1, "data/"), (2, "campus_customs.db"), (2, "campus_customs_new.db"),
    (1, "mcp_server/"), (2, "server.py"), (2, "README.md"),
    (1, "frontend/"),
    (1, "backend/"), (2, "main.py"), (2, "models.py"), (2, "prompts/"),
    (3, "boss.md"), (3, "inventory.md"), (3, "accounting.md"), (3, "facilities.md"), (3, "customer_service.md"),
    (1, "output/"), (2, "harness.md"), (2, "mcp_smoke.json"), (2, "desk_tickets.html"), (2, "design.md"),
    (2, "resolved_tickets.json"), (2, "resolved_board.html"), (2, "audit_trail.json"), (2, "github_url.txt"),
]


def shared_files() -> set[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "."],
                         cwd=PROJECT, capture_output=True, text=True, check=True).stdout
    return set(out.splitlines())


def paths() -> list[str]:
    """The full path of each entry, relative to hw5/."""
    stack, out = [], []
    for depth, name in LAYOUT:
        stack = stack[:depth] + [name]
        out.append("".join(stack[1:]))
    return out


def tree() -> str:
    lines = []
    for i, (depth, name) in enumerate(LAYOUT):
        if depth == 0:
            lines.append(name)
            continue
        prefix = ""
        for d in range(1, depth):  # a bar for each open ancestor folder
            ancestor = max(j for j in range(i) if LAYOUT[j][0] == d)
            later = [j for j in range(ancestor + 1, len(LAYOUT)) if LAYOUT[j][0] <= d]
            prefix += "    " if not later or LAYOUT[later[0]][0] < d else "│   "
        later = [j for j in range(i + 1, len(LAYOUT)) if LAYOUT[j][0] <= depth]
        last = not later or LAYOUT[later[0]][0] < depth
        lines.append(prefix + ("└── " if last else "├── ") + name)
    return "\n".join(lines)


def main() -> None:
    files = shared_files()
    missing = []
    for p in paths():
        if not p:
            continue
        found = any(f.startswith(p) for f in files) if p.endswith("/") else p in files
        if not found:
            missing.append(p)
    if missing:
        sys.exit(f"Not in the repo yet: {missing}")
    text = README.read_text(encoding="utf-8")
    start, end = "<!-- tree:start -->", "<!-- tree:end -->"
    a, b = text.index(start) + len(start), text.index(end)
    README.write_text(text[:a] + "\n```text\n" + tree() + "\n```\n" + text[b:], encoding="utf-8", newline="\n")
    print(f"README tree updated: {len(LAYOUT) - 1} entries, all in the repo")


if __name__ == "__main__":
    main()
