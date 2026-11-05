"""Problem 9: build output/resolved_tickets.json from the full run, straight from the records.

Everything comes from two places, read-only:
- the working database (data/campus_customs_new.db): final ticket statuses, payments, the cash balance,
  approval requests and drafts
- the append-only audit trail (output/audit_trail.json): which agents worked, what they handed off,
  which tools they used, what they concluded, and every human approval

The full run is the latest team run on each of tickets 101, 102 and 103, after the database reset that
started it. Nothing here is typed by hand.

Run from hw5/:  python scripts/build_resolved.py
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, OrderedDict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "data" / "campus_customs_new.db"
AUDIT = PROJECT / "output" / "audit_trail.json"
OUT = PROJECT / "output" / "resolved_tickets.json"
PRICE = {"input": 0.10, "cached": 0.01, "output": 0.50}  # gpt-6-luna per 1M tokens (backend/prices.json)
ROLE = {"boss": "Boss (Mr. D'Onofrio)", "inventory": "Inventory", "accounting": "Accounting",
        "facilities": "Facilities", "customer_service": "Customer Service"}
SYMBOL = {"boss": "🕴️", "inventory": "📦", "accounting": "🧮", "facilities": "🧢", "customer_service": "👕"}


def rows(conn, sql):
    return [dict(r) for r in conn.execute(sql)]


def main() -> dict:
    trail = json.loads(AUDIT.read_text(encoding="utf-8"))
    # the latest run per ticket
    latest: dict[int, str] = {}
    for e in trail:
        if e.get("run_id") and e.get("ticket_id") in (101, 102, 103) and e.get("step_kind") == "DecisionCheck":
            latest[e["ticket_id"]] = e["run_id"]
    first = min(i for i, e in enumerate(trail) if e.get("run_id") in latest.values())
    reset_at = max(i for i, e in enumerate(trail[:first]) if e.get("step_kind") == "DatabaseReset")
    window = trail[reset_at:]

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    tickets = {t["id"]: t for t in rows(conn, "SELECT * FROM tickets")}
    reqs = rows(conn, "SELECT * FROM approval_requests ORDER BY id")
    pays = rows(conn, "SELECT * FROM payments ORDER BY id")
    drafts = rows(conn, "SELECT * FROM drafts ORDER BY id")
    checking = rows(conn, "SELECT * FROM cash_accounts WHERE name = 'checking'")[0]

    approvals = [e for e in window if e.get("step_kind") == "HumanApproval" and (e.get("result") or {}).get("paid")]
    start_cash = approvals[0]["result"]["cash_before"] if approvals else checking["balance"]

    out_tickets = []
    for tid in (101, 102, 103):
        rid = latest[tid]
        mine = [e for e in window if e.get("run_id") == rid]
        agents: "OrderedDict[str, dict]" = OrderedDict()
        handoffs, refused = [], []
        tokens = Counter()
        calls = 0
        for e in mine:
            a = e.get("agent")
            if a in ROLE:
                agents.setdefault(a, {"agent": ROLE[a], "symbol": SYMBOL[a], "tools": Counter(), "model_steps": 0, "contributed": None})
            if e.get("step_kind") == "CallToolsNode":
                calls += 1
                agents[a]["model_steps"] += 1
                for k, v in (e.get("tokens") or {}).items():
                    tokens[k] += v or 0
                for c in e.get("tool_calls") or []:
                    agents[a]["tools"][c["tool"]] += 1
                    if c["tool"] == "ask_teammate":
                        args = c.get("arguments") or {}
                        handoffs.append({"from": ROLE[a], "to": ROLE.get(args.get("teammate"), args.get("teammate")),
                                         "priority": args.get("priority"), "due_by": args.get("due_by"), "task": args.get("task")})
            if e.get("step_kind") == "ModelRequestNode":
                for r in e.get("tool_results_sent") or []:
                    if r.get("tool") == "ask_teammate" and str(r.get("result", "")).startswith("REFUSED"):
                        refused.append({"by_agent": ROLE.get(a, a), "reason": r["result"]})
            if e.get("step_kind") == "End" and a in ROLE:
                o = e.get("output") or {}
                agents[a]["contributed"] = (o.get("summary") or o.get("note") or o.get("recommendation")
                                            or (f"Drafted \"{o.get('subject')}\" to {o.get('to')}" if o.get("subject") else None))
        for r in refused:  # mark the hand-off the loop guard turned away (its target is named first in the reason)
            target = r["reason"].split("REFUSED: ", 1)[-1].split(" ", 1)[0]
            for d in reversed(handoffs):
                if d["from"] == r["by_agent"] and d["to"] == ROLE.get(target, target) and not d.get("refused"):
                    d["refused"] = True
                    break
        boss_end = [e for e in mine if e.get("step_kind") == "End" and e.get("agent") == "boss"][-1]["output"]
        sync = [e for e in mine if e.get("step_kind") == "StatusSync"][-1]
        resolved_by = [e for e in window if e.get("step_kind") == "TicketResolved" and e.get("ticket_id") == tid]
        my_reqs = [r for r in reqs if r["ticket_id"] == tid]
        my_pays = []
        for r in my_reqs:
            if r["payment_id"]:
                p = next(p for p in pays if p["id"] == r["payment_id"])
                ap = next(e for e in approvals if e.get("request_id") == r["id"])
                my_pays.append({"request_id": r["id"], "kind": r["kind"], "payee": r["payee"], "amount": r["amount"],
                                "approved_by": p["approved_by"], "approved_at": ap["time"], "paid_on_shop_date": p["paid_at"],
                                "cash_before": ap["result"]["cash_before"], "cash_after": ap["result"]["cash_after"],
                                "requested_by": r["requested_by"], "reason": r["reason"]})
        cost = ((tokens["input"] - tokens["cached_input"]) * PRICE["input"] + tokens["cached_input"] * PRICE["cached"] + tokens["output"] * PRICE["output"]) / 1e6
        out_tickets.append({
            "id": tid,
            "subject": tickets[tid]["subject"],
            "requester": tickets[tid]["requester"],
            "final_status": tickets[tid]["status"],
            "board_state": "resolved" if tickets[tid]["status"] in ("waiting_approval", "blocked", "resolved") else "open",
            "priority": boss_end.get("priority"),
            "outcome": boss_end.get("summary"),
            "boss_reasoning": boss_end.get("reasoning"),
            "still_open_for_a_human": boss_end.get("missing_information"),
            "status_set_by_backend": {"recommended": sync.get("recommended"), "set_to": sync.get("set_to")},
            "fully_resolved_when": resolved_by[-1]["why"] if resolved_by else None,
            "boss_called_first": handoffs[0]["to"] if handoffs else None,
            "agents": [{"agent": v["agent"], "symbol": v["symbol"], "contributed": v["contributed"],
                        "tools": [{"tool": k, "times": n} for k, n in v["tools"].items()], "model_steps": v["model_steps"]}
                       for v in agents.values()],
            "agents_not_called": [ROLE[k] for k in ROLE if k not in agents],
            "delegations": handoffs,
            "refused_hand_offs": refused,
            "human_approvals": my_pays,
            "cash_change": round(-sum(p["amount"] for p in my_pays), 2),
            "drafts_on_board": [{"id": d["id"], "to": d["to_name"], "subject": d["subject"], "body": d["body"], "sent": False}
                                for d in drafts if d["ticket_id"] == tid],
            "run": {"audit_run_id": rid, "model": "gpt-6-luna", "model_calls": calls, "input_tokens": tokens["input"],
                    "cached_input_tokens": tokens["cached_input"], "output_tokens": tokens["output"], "cost_usd": round(cost, 5)},
        })

    end_cash = round(start_cash + sum(t["cash_change"] for t in out_tickets), 2)
    report = {
        "what": "Problem 9: all three tickets resolved in one clean run, after a database reset",
        "shop_date": rows(conn, "SELECT date_today FROM desk")[0]["date_today"],
        "cash": {
            "starting_checking_balance": start_cash,
            "changes": [{"ticket": t["id"], "change": t["cash_change"],
                         "why": "; ".join(f"{p['kind']} ${p['amount']:,.2f} to {p['payee']} (request {p['request_id']}, approved by {p['approved_by']})" for p in t["human_approvals"]) or "no payment or purchase"}
                        for t in out_tickets],
            "ending_checking_balance_by_math": end_cash,
            "ending_checking_balance_in_cash_accounts": checking["balance"],
            "matches_cash_accounts": end_cash == round(checking["balance"], 2),
            "math": f"${start_cash:,.2f} " + " ".join(f"- ${-t['cash_change']:,.2f}" for t in out_tickets if t["cash_change"]) + f" = ${end_cash:,.2f}",
        },
        "payments_table": pays,
        "tickets": out_tickets,
        "audit_trail": {"entries_in_this_run": len(window), "from_index": reset_at},
        "nothing_sent": "No email, call or real payment: drafts stay on the board, and payments only update the practice database.",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT)}: start ${start_cash:,.2f}, end ${end_cash:,.2f}, cash_accounts ${checking['balance']:,.2f}, match {report['cash']['matches_cash_accounts']}")
    return report


if __name__ == "__main__":
    main()
