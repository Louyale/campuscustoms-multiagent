"""Run one ticket through the agent team (gpt-6-luna via Portkey) and save what happened.

Boss reads the ticket over MCP, gives teammates assignments with deadlines, checks in, and
returns its decision. Every loop step is appended to output/audit_trail.json. Nothing can be
paid: agents can only file requests, and paying needs a human.

Run from hw5/:  python scripts/run_ticket.py --ticket 102 [--reset-before] [--reset-after]
Writes output/test_run_<ticket>.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from backend.audit import AUDIT_TRAIL  # noqa: E402
from backend.team import run_ticket  # noqa: E402
from scripts.reset_db import WORKING, reset  # noqa: E402


def board_snapshot() -> dict:
    with sqlite3.connect(f"file:{WORKING.as_posix()}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        snap = {"cash": [dict(r) for r in c.execute("SELECT * FROM cash_accounts")],
                "payments": [dict(r) for r in c.execute("SELECT * FROM payments")],
                "tickets": [dict(r) for r in c.execute("SELECT id, status FROM tickets")]}
        for t in ("approval_requests", "drafts", "building_requests"):
            snap[t] = [dict(r) for r in c.execute(f"SELECT * FROM {t}")] if t in tables else []
    return snap


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticket", type=int, required=True)
    ap.add_argument("--reset-before", action="store_true")
    ap.add_argument("--reset-after", action="store_true")
    args = ap.parse_args()

    if args.reset_before:
        reset()
        print("Database reset before the run.")
    audit_before = len(json.loads(AUDIT_TRAIL.read_text(encoding="utf-8"))) if AUDIT_TRAIL.exists() else 0

    t0 = time.perf_counter()
    decision, deps = await run_ticket(args.ticket)
    seconds = round(time.perf_counter() - t0, 1)

    entries = json.loads(AUDIT_TRAIL.read_text(encoding="utf-8"))
    new = [e for e in entries if e.get("run_id") == deps.run_id]
    models = sorted({e["model"] for e in new if e.get("model")})
    tokens = {"input": 0, "cached_input": 0, "output": 0}
    for e in new:
        for k in tokens:
            tokens[k] += (e.get("tokens") or {}).get(k) or 0
    board = board_snapshot()
    report = {
        "ticket": args.ticket,
        "run_id": deps.run_id,
        "seconds": seconds,
        "decision": decision.model_dump(),
        "assignments": [a.model_dump(exclude={"report"}) for a in deps.assignments],
        "hand_offs": [d.model_dump(exclude={"answer"}) for d in deps.delegations],
        "audit_entries_added": len(entries) - audit_before,
        "audit_entries_for_this_run": len(new),
        "agents_in_audit": sorted({e["agent"] for e in new}),
        "models_used": models,
        "tokens": tokens,
        "model_calls": sum(1 for e in new if e.get("step_kind") == "CallToolsNode"),
        "tool_calls": [c["tool"] for e in new for c in (e.get("tool_calls") or [])],
        "board_after_run": board,
        "nothing_paid": board["payments"] == [],
    }
    out = PROJECT / "output" / f"test_run_{args.ticket}.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(f"Ticket {args.ticket}: {decision.summary}")
    print(f"  status recommended: {decision.recommended_status}; approvals needed: "
          f"{[(a.kind, a.payee, a.amount) for a in decision.approvals_needed]}")
    print(f"  assignments: {[(a.id, a.to_agent, a.due_by, a.status, a.on_time) for a in deps.assignments]}")
    print(f"  audit entries added: {report['audit_entries_added']} (agents: {report['agents_in_audit']}); models: {models}")
    print(f"  model calls: {report['model_calls']}; tokens: {tokens}; {seconds}s")
    print(f"  board: {len(board['approval_requests'])} payment request(s), {len(board['drafts'])} draft(s); "
          f"payments made: {len(board['payments'])}")
    print(f"  saved {out.relative_to(PROJECT)}")

    if args.reset_after:
        reset()
        print("Database reset after the run.")


if __name__ == "__main__":
    asyncio.run(main())
