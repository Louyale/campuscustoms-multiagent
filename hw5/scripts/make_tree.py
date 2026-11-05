"""Write the file tree into README.md, between the <!-- tree:start --> and <!-- tree:end --> markers.

The tree lists the files git will share (tracked, plus new files that aren't ignored), so .env, .venv,
node_modules and the working database never show up. Folders of screenshots are shown as a count.

Run from hw5/:  python scripts/make_tree.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
README = PROJECT / "README.md"
COLLAPSE = {"output/dashboard_screens", "output/desk_tickets_screens", "output/resolved_board_screens", "frontend/src/assets"}


def shared_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "."],
                         cwd=PROJECT, capture_output=True, text=True, check=True).stdout
    return sorted(set(f for f in out.splitlines() if f and "__pycache__" not in f))


def tree(files: list[str]) -> str:
    nested: dict = {}
    for f in files:
        node = nested
        parts = f.split("/")
        for i, part in enumerate(parts):
            if "/".join(parts[:i]) in COLLAPSE:
                node.setdefault("#count", 0)
                node["#count"] += 1
                break
            node = node.setdefault(part, {}) if i < len(parts) - 1 else node.setdefault(part, None) or node
    lines = ["hw5/"]

    def walk(node: dict, prefix: str):
        items = [(k, v) for k, v in node.items() if k != "#count"]
        items.sort(key=lambda kv: (kv[1] is None, kv[0].lower()))
        for i, (name, child) in enumerate(items):
            last = i == len(items) - 1
            branch = "└── " if last else "├── "
            if isinstance(child, dict):
                n = child.get("#count")
                lines.append(f"{prefix}{branch}{name}/" + (f"  ({n} {'images' if name == 'assets' else 'screenshots'})" if n else ""))
                walk(child, prefix + ("    " if last else "│   "))
            else:
                lines.append(f"{prefix}{branch}{name}")

    walk(nested, "")
    return "\n".join(lines)


def main() -> None:
    text = README.read_text(encoding="utf-8")
    start, end = "<!-- tree:start -->", "<!-- tree:end -->"
    a, b = text.index(start) + len(start), text.index(end)
    README.write_text(text[:a] + "\n```text\n" + tree(shared_files()) + "\n```\n" + text[b:], encoding="utf-8", newline="\n")
    print("README tree updated")


if __name__ == "__main__":
    main()
