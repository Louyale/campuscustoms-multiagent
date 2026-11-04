"""Dollar cost of each ticket test run, and what the team got done for it.

Prices are the course's gpt-6-luna prices (backend/prices.json, the same sheet as HW6). Token counts
come straight from the run records (output/test_run_102*.json), which come from the audit trail.
Prints the numbers used in harness Tables 17 and 18.

Run from hw5/:  python scripts/cost_report.py
"""

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PRICES = json.loads((PROJECT / "backend" / "prices.json").read_text(encoding="utf-8"))["gpt-6-luna"]
RUNS = [
    ("Run 1: first team", "test_run_102_run1.json"),
    ("Run 2: with priorities", "test_run_102_run2.json"),
    ("Run 3: efficiency changes (regression)", "test_run_102_run3_regression.json"),
    ("Run 4: final (efficiency + approval guard)", "test_run_102.json"),
]


def dollars(tokens: dict, cached: bool = True) -> float:
    inp, hit, out = tokens["input"], tokens["cached_input"], tokens["output"]
    if not cached:
        hit = 0
    return ((inp - hit) * PRICES["input_per_1m"] + hit * PRICES["cached_input_per_1m"] + out * PRICES["output_per_1m"]) / 1e6


def main() -> list[dict]:
    rows = []
    for label, name in RUNS:
        r = json.loads((PROJECT / "output" / name).read_text(encoding="utf-8"))
        b = r["board_after_run"]
        rows.append({
            "run": label, "calls": r["model_calls"], "tokens": r["tokens"],
            "cost": dollars(r["tokens"]), "cost_no_cache": dollars(r["tokens"], cached=False),
            "assignments": len(r["assignments"]), "requests": len(b["approval_requests"]), "drafts": len(b["drafts"]),
            "tool_calls": len(r["tool_calls"]), "audit": r["audit_entries_for_this_run"], "seconds": r["seconds"],
            "approvals_ok": r.get("approvals_all_filed", len(b["approval_requests"]) >= len(r["decision"]["approvals_needed"])),
        })
    for x in rows:
        print(f"{x['run']:44} calls {x['calls']:2}  ${x['cost']:.5f} (no cache ${x['cost_no_cache']:.5f})  "
              f"assign {x['assignments']} req {x['requests']} drafts {x['drafts']} tools {x['tool_calls']} ok {x['approvals_ok']}")
    return rows


if __name__ == "__main__":
    main()
