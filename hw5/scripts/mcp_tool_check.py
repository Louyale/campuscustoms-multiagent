"""Problem 5: check every MCP tool over the real MCP protocol, on a scratch copy of the database.

The scratch copy is a fresh copy of the original campus_customs.db in a temp folder. The working
copy (data/campus_customs_new.db) is never touched, and the script proves it with checksums.
Each check calls the tool through a FastMCP client, exactly as an agent would, and compares
the answer with the database.

Run from hw5/:  python scripts/mcp_tool_check.py
Writes output/mcp_tool_check.json.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
ORIGINAL = PROJECT / "data" / "campus_customs.db"
WORKING = PROJECT / "data" / "campus_customs_new.db"
SCRATCH = Path(tempfile.gettempdir()) / "hw5_tool_check" / "campus_customs_scratch.db"
OUT = PROJECT / "output" / "mcp_tool_check.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def q(sql: str, *args):
    with sqlite3.connect(SCRATCH) as c:
        c.row_factory = sqlite3.Row
        return [dict(r) for r in c.execute(sql, args)]


async def main() -> None:
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ORIGINAL, SCRATCH)
    os.environ["CAMPUS_DB"] = str(SCRATCH)  # the server reads this at import
    before_original, before_working = sha(ORIGINAL), sha(WORKING)

    sys.path.insert(0, str(PROJECT))
    from fastmcp import Client
    from mcp_server.server import mcp

    code = os.environ["HUMAN_APPROVAL_CODE"]  # loaded from .env by the server module; never printed
    checks: list[dict] = []

    def check(tool: str, args: dict, got, ok: bool, expected: str):
        shown = {k: ("<HUMAN_APPROVAL_CODE>" if k == "approval_code" else v) for k, v in args.items()}
        checks.append({"tool": tool, "arguments": shown, "expected": expected, "passed": bool(ok), "output": got})
        print(f"{'PASS' if ok else 'FAIL'}  {tool:24} {expected}")

    async with Client(mcp) as client:
        names = sorted(t.name for t in await client.list_tools())

        async def call(tool, **args):
            return (await client.call_tool(tool, args)).data

        r = await call("get_ticket", ticket_id=101)
        check("get_ticket", {"ticket_id": 101}, r, r["ticket"]["sku"] == "CC-TEE-WHITE" and r["ticket"]["invoice_id"] == 501, "ticket 101 is the size S tee, linked to invoice 501")
        r = await call("list_tickets", status="open")
        check("list_tickets", {"status": "open"}, r, [t["id"] for t in r["tickets"]] == [101, 102, 103], "three open tickets: 101, 102, 103")
        r = await call("check_stock", sku="CC-HOOD-NAVY", size="M", qty_needed=20)
        check("check_stock", {"sku": "CC-HOOD-NAVY", "size": "M", "qty_needed": 20}, r, r["qty"] == 8 and r["shortfall"] == 12, "8 on hand, shortfall 12")
        r = await call("list_inventory", low_only=True)
        low = sorted((i["sku"], i["size"]) for i in r["items"])
        exp = sorted((x["sku"], x["size"]) for x in q("SELECT sku, size FROM inventory WHERE qty < 5"))
        check("list_inventory", {"low_only": True}, r, low == exp, f"{len(exp)} items under 5 units, matching the database")
        r = await call("list_inventory")
        val = round(sum(x["qty"] * x["unit_cost"] for x in q("SELECT i.qty, p.unit_cost FROM inventory i JOIN pricing p ON p.sku = i.sku")), 2)
        check("list_inventory", {}, r, r["total_value_at_cost"] == val, f"inventory value at cost ${val:,.2f}")
        r = await call("list_vendors")
        v1 = next(v for v in r["vendors"] if v["id"] == 1)
        check("list_vendors", {}, r, v1["blocked"] and v1["lead_days"] == 5 and len(r["vendors"]) == 3, "3 vendors; Bulldog Print Co blocked, 5 lead days")
        r = await call("get_open_invoices", invoice_id=501)
        check("get_open_invoices", {"invoice_id": 501}, r, r["open_invoices"][0]["days_overdue"] == 3, "invoice 501, 3 days overdue")
        r = await call("get_rent_due", lease_id=1)
        check("get_rent_due", {"lease_id": 1}, r, r["monthly_rent"] == 2400 and r["days_until_due"] == 2, "$2,400 due in 2 days")
        r = await call("get_cash_balance")
        check("get_cash_balance", {}, r, r["cash_total"] == 3400 and r["accounts"][0]["pending_requests"] == 0, "$3,400 in checking, nothing pending")
        r = await call("list_payments")
        check("list_payments", {}, r, r["payments"] == [], "no payments yet")

        # --- financial statements (Accounting), before any payment ---
        r = await call("build_balance_sheet")
        check("build_balance_sheet", {}, r,
              r["total_assets"] == 3400 + val and r["total_liabilities"] == 840 and r["equity"] == 3400 + val - 840
              and r["balances"] and len(r["missing_information"]) >= 4
              and any(l["section"] == "note" and "2,400" in l["label"] for l in r["lines"]),
              f"assets ${3400 + val:,.2f} (cash + inventory at cost), liabilities $840 (invoice 501), balances; rent shown as a note; missing figures flagged")
        r = await call("build_income_statement")
        check("build_income_statement", {}, r, r["revenue"] == 0 and r["expenses"] == 0 and any("Revenue" in m for m in r["missing_information"]),
              "revenue $0 (not modeled, flagged), expenses $0 (no payments yet)")

        # --- leases and building requests (Facilities) ---
        r = await call("list_leases")
        check("list_leases", {}, r, len(r["leases"]) == 1 and r["leases"][0]["days_until_due"] == 2, "1 lease, rent due in 2 days")
        r = await call("get_lease", lease_id=1)
        check("get_lease", {"lease_id": 1}, r, r["found"] and r["lease"]["landlord"] == "Elm City Properties" and r["missing_information"],
              "lease 1, Elm City Properties; lease terms not in the database are flagged")
        r = await call("log_building_request", lease_id=1, issue="Front door lock sticks", priority="normal", requested_by="facilities")
        breq = r.get("request_id")
        check("log_building_request", {"lease_id": 1, "priority": "normal"}, r, r["logged"], "logged on the board; no one contacted")
        r = await call("log_building_request", lease_id=1, issue="x", priority="whenever", requested_by="facilities")
        check("log_building_request", {"priority": "whenever"}, r, r["logged"] is False, "REFUSED: priority must be low, normal or urgent")
        r = await call("update_building_request", request_id=breq, status="in_progress", note="asked Accounting about cost")
        check("update_building_request", {"request_id": breq, "status": "in_progress"}, r, r["updated"] and r["to"] == "in_progress", "open to in_progress")
        r = await call("list_building_requests", status="in_progress")
        check("list_building_requests", {"status": "in_progress"}, r, len(r["requests"]) == 1, "one request in progress")

        # --- money: request, refuse, approve, pay ---
        r = await call("request_payment", kind="purchase_order", ticket_id=103, vendor_id=1, sku="CC-HOOD-NAVY", size="M", qty=12,
                       reason="restock 12 hoodies", requested_by="accounting")
        check("request_payment", {"kind": "purchase_order", "vendor_id": 1, "sku": "CC-HOOD-NAVY", "size": "M", "qty": 12}, r,
              r["filed"] is False and "blocked" in r["message"], "REFUSED: vendor blocked by open invoice 501")
        r = await call("request_payment", kind="invoice", ticket_id=102, ref_id=501, reason="pay overdue invoice", requested_by="accounting")
        inv_req = r.get("request_id")
        check("request_payment", {"kind": "invoice", "ref_id": 501, "ticket_id": 102}, r,
              r["filed"] and r["amount"] == 840 and r["ticket_id"] == 101 and q("SELECT ticket_id FROM approval_requests WHERE id = ?", inv_req)[0]["ticket_id"] == 101,
              "filed: $840 to Bulldog Print Co, pending, amount from the database; raised from ticket 102 but filed under ticket 101, which links invoice 501")
        r = await call("request_payment", kind="invoice", ticket_id=101, ref_id=501, reason="again", requested_by="accounting")
        check("request_payment", {"kind": "invoice", "ref_id": 501, "repeat": True}, r, r["filed"] is False and "Already pending" in r["message"], "REFUSED: duplicate request")
        r = await call("request_payment", kind="rent", ticket_id=102, ref_id=1, reason="September rent", requested_by="accounting")
        rent_req = r.get("request_id")
        check("request_payment", {"kind": "rent", "ref_id": 1}, r, r["filed"] and r["amount"] == 2400 and r["available_after_this_request"] == 160, "filed: $2,400 rent, pending; $160 left after both")
        r = await call("get_cash_balance")
        check("get_cash_balance", {"after": "two requests"}, r, r["accounts"][0]["balance"] == 3400 and r["accounts"][0]["pending_requests"] == 3240, "still $3,400; $3,240 promised to pending requests; nothing paid")

        r = await call("approve_and_pay", request_id=inv_req, approved_by="Lou", approval_code="guess")
        check("approve_and_pay", {"request_id": inv_req, "approved_by": "Lou", "approval_code": "wrong"}, r, r["paid"] is False, "REFUSED: wrong approval code")
        r = await call("approve_and_pay", request_id=inv_req, approved_by="Lou", approval_code=code)
        inv = q("SELECT status FROM invoices WHERE id = 501")[0]["status"]
        cash = q("SELECT balance FROM cash_accounts")[0]["balance"]
        check("approve_and_pay", {"request_id": inv_req, "approved_by": "Lou", "approval_code": code}, r,
              r["paid"] and inv == "paid" and cash == 2560 and q("SELECT approved_by FROM payments")[0]["approved_by"] == "Lou",
              "paid: payments row (approved_by Lou), cash $3,400 to $2,560, invoice 501 paid")
        r = await call("list_vendors")
        check("list_vendors", {"after": "invoice paid"}, r, not next(v for v in r["vendors"] if v["id"] == 1)["blocked"], "Bulldog Print Co no longer blocked")
        r = await call("approve_and_pay", request_id=rent_req, approved_by="Lou", approval_code=code)
        lease = q("SELECT next_due FROM leases WHERE id = 1")[0]["next_due"]
        check("approve_and_pay", {"request_id": rent_req, "approved_by": "Lou", "approval_code": code}, r,
              r["paid"] and r["cash_after"] == 160 and lease == "2026-10-02", "paid: cash $2,560 to $160, lease next_due moved to 2026-10-02")
        r = await call("request_payment", kind="purchase_order", ticket_id=103, vendor_id=1, sku="CC-HOOD-NAVY", size="M", qty=12,
                       reason="restock 12 hoodies", requested_by="accounting")
        check("request_payment", {"kind": "purchase_order", "qty": 12}, r, r["filed"] is False and "Not enough cash" in r["message"], "REFUSED: $264 needed, $160 left (no negative balances)")
        with sqlite3.connect(SCRATCH) as c:  # force a pending request bigger than the cash, to test the pay-time refusal
            c.execute("INSERT INTO approval_requests (ticket_id, kind, vendor_id, sku, size, qty, payee, amount, account, reason, requested_by, requested_at) "
                      "VALUES (103, 'purchase_order', 1, 'CC-HOOD-NAVY', 'M', 12, 'Bulldog Print Co', 264, 'checking', 'test', 'test', 'test')")
            big = c.execute("SELECT max(id) FROM approval_requests").fetchone()[0]
        r = await call("approve_and_pay", request_id=big, approved_by="Lou", approval_code=code)
        check("approve_and_pay", {"request_id": big, "note": "a $264 request with $160 cash"}, r,
              r["paid"] is False and q("SELECT balance FROM cash_accounts")[0]["balance"] == 160, "REFUSED at pay time: cash stays $160, never negative")
        r = await call("reject_payment_request", request_id=big, rejected_by="Lou", approval_code=code, reason="test")
        check("reject_payment_request", {"request_id": big}, r, r["rejected"] is False, "nothing to reject: the refused request is no longer pending")
        r = await call("list_payment_requests")
        check("list_payment_requests", {}, r, [x["status"] for x in r["requests"]] == ["paid", "paid", "refused"], "requests: paid, paid, refused")
        r = await call("list_payments")
        check("list_payments", {"after": "two payments"}, r, r["total_paid"] == 3240, "two payments, $3,240 total, both approved by Lou")
        r = await call("build_income_statement")
        check("build_income_statement", {"after": "two payments"}, r, r["expenses"] == 3240 and r["net_income"] == -3240 and r["payments_counted"] == 2,
              "expenses $3,240 (rent $2,400 + invoice $840), net income -$3,240 (no revenue modeled)")
        r = await call("build_balance_sheet")
        check("build_balance_sheet", {"after": "two payments"}, r, r["total_liabilities"] == 0 and r["balances"],
              "invoice 501 paid, so no liabilities; still balances")

        # --- spelling and grammar (Customer Service) ---
        good_subject, good_body = "Your Classic Bulldog Tee", ("Hi Tauhid,\n\nThanks for your order of a Classic Bulldog Tee in size S. "
                                                              "We're arranging a restock and will confirm timing soon.\n\nCampus Customs")
        bad_body = "Hi Tauhid,\n\nwe recieve alot of orders and i think the the tee could of shipped  soon ."
        r = await call("check_spelling_grammar", subject=good_subject, body=good_body)
        check("check_spelling_grammar", {"draft": "clean"}, r, r["passed"], "clean draft passes (shop names like Bulldog and Tauhid accepted)")
        r = await call("check_spelling_grammar", subject="your tee", body=bad_body)
        found = {i["text"].lower() for i in r["issues"]}
        check("check_spelling_grammar", {"draft": "with mistakes"}, r,
              not r["passed"] and {"recieve", "alot", "the the", "could of", "i"} <= found,
              f"{len(r['issues'])} issues caught: recieve, alot, the the, could of, lowercase i and sentence starts, spacing")
        r = await call("save_customer_draft", ticket_id=101, to_name="Tauhid Zaman", subject="your tee", body=bad_body, written_by="customer_service")
        check("save_customer_draft", {"draft": "with mistakes"}, r, r["saved"] is False and r["issues"], "REFUSED: won't save a draft with spelling or grammar issues")

        # --- board: drafts and ticket status ---
        r = await call("save_customer_draft", ticket_id=101, to_name="Tauhid Zaman", subject=good_subject, body=good_body, written_by="customer_service")
        check("save_customer_draft", {"ticket_id": 101}, r, r["saved"] and r["sent"] is False, "draft saved on the board; sent = false")
        r = await call("list_drafts", ticket_id=101)
        check("list_drafts", {"ticket_id": 101}, r, len(r["drafts"]) == 1 and r["drafts"][0]["status"] == "draft", "one draft, status draft")
        r = await call("update_ticket_status", ticket_id=102, status="resolved")
        check("update_ticket_status", {"ticket_id": 102, "status": "resolved"}, r, r["updated"] and q("SELECT status FROM tickets WHERE id = 102")[0]["status"] == "resolved", "ticket 102: open to resolved")
        r = await call("update_ticket_status", ticket_id=102, status="paid")
        check("update_ticket_status", {"ticket_id": 102, "status": "paid"}, r, r["updated"] is False, "REFUSED: 'paid' isn't a ticket status")

    tested = sorted({c["tool"] for c in checks})
    report = {
        "what": "Every MCP tool called through a FastMCP client against a scratch copy of the original database",
        "tools_on_server": names,
        "tools_tested": tested,
        "all_tools_tested": tested == names,
        "checks_passed": sum(c["passed"] for c in checks),
        "checks_total": len(checks),
        "original_db_unchanged": sha(ORIGINAL) == before_original,
        "working_db_unchanged": sha(WORKING) == before_working,
        "checks": checks,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str).replace(code, "<HUMAN_APPROVAL_CODE>"), encoding="utf-8")
    print(f"\n{report['checks_passed']}/{report['checks_total']} checks passed; {len(tested)}/{len(names)} tools tested; "
          f"original unchanged: {report['original_db_unchanged']}; working copy unchanged: {report['working_db_unchanged']}")


if __name__ == "__main__":
    asyncio.run(main())
