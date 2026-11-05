"""Record a human's decision on a ticket the team left for a human, and resolve it.

The agents can only recommend. When a ticket waits on a human call that isn't a payment (for example,
ticket 103's bulk-discount decision), a person makes the call. This script records it the same way the
dashboard's approval route records a payment approval:
- the ticket's status changes only through the MCP tool `update_ticket_status` (no direct database writes)
- the decision and the resolution are appended to output/audit_trail.json (`HumanDecision`, `TicketResolved`)
- no money moves: it refuses if the ticket still has a pending payment request, and it never touches cash

Run from hw5/:
  python scripts/human_decision.py --ticket 103 --by "Boss (Mr. D'Onofrio)" --decision "..."
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from backend.audit import append_entry, now  # noqa: E402
from backend.mcp_tools import mcp_toolset  # noqa: E402


async def call(tool: str, **args) -> dict:
    out = await mcp_toolset.direct_call_tool(tool, args)
    return out if isinstance(out, dict) else json.loads(out)


async def decide(ticket_id: int, decided_by: str, decision: str) -> dict:
    async with mcp_toolset:
        found = await call("get_ticket", ticket_id=ticket_id)
        if not found.get("found"):
            return {"resolved": False, "message": f"No ticket {ticket_id}."}
        status = found["ticket"]["status"]
        if status not in ("blocked", "waiting_approval"):
            return {"resolved": False, "message": f"Ticket {ticket_id} is {status}; only a ticket waiting on a human can be decided."}
        pending = [r for r in found["payment_requests"] if r["status"] == "pending"]
        if pending:
            return {"resolved": False, "message": f"Ticket {ticket_id} still has {len(pending)} pending payment request(s). Approve or reject them on the dashboard first."}
        cash_before = (await call("get_cash_balance"))["cash_total"]
        append_entry({"time": now(), "run_id": None, "ticket_id": ticket_id, "agent": "human", "step_kind": "HumanDecision",
                      "decided_by": decided_by, "decision": decision, "status_before": status,
                      "money_moved": False, "cash_before": cash_before})
        result = await call("update_ticket_status", ticket_id=ticket_id, status="resolved")
        cash_after = (await call("get_cash_balance"))["cash_total"]
        append_entry({"time": now(), "run_id": None, "ticket_id": ticket_id, "agent": "human", "step_kind": "TicketResolved",
                      "why": f"{decided_by} made the human decision the team left open: {decision}"})
        return {"resolved": bool(result.get("updated")), "ticket_id": ticket_id, "from": status, "to": "resolved",
                "cash_before": cash_before, "cash_after": cash_after, "money_moved": cash_before != cash_after}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ticket", type=int, required=True)
    ap.add_argument("--by", required=True, help="the human making the call")
    ap.add_argument("--decision", required=True)
    a = ap.parse_args()
    print(json.dumps(asyncio.run(decide(a.ticket, a.by.strip(), a.decision.strip())), indent=2))


if __name__ == "__main__":
    main()
