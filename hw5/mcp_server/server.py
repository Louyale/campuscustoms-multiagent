"""Campus Customs MCP server (FastMCP).

Every agent in HW5 (Boss, Inventory, Accounting, Facilities, Customer Service)
gets its shop data through the tools in this server. They all work on the
working copy, data/campus_customs_new.db. The original, data/campus_customs.db,
is never opened here, so it stays clean for resets.

Ground rules for every tool:
- Never invent data. Each value comes straight from the database, or is simple
  arithmetic on database values (shortfall, days overdue, cash left). Anything
  not found comes back as found=False with a message, never a guessed value.
- "Today" is desk.date_today, never the computer clock.
- The three Problem 3 tools only read. Tools that write (payments, drafts) come
  in later problems, behind human approval.

Run later with:  python mcp_server/server.py   (not run in Problem 3)
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from fastmcp import FastMCP

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("CAMPUS_DB", PROJECT_DIR / "data" / "campus_customs_new.db")).resolve()
ORIGINAL_DB = (PROJECT_DIR / "data" / "campus_customs.db").resolve()

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True}

mcp = FastMCP(
    "campus-customs",
    instructions=(
        "Tools for the Campus Customs shop database (working copy campus_customs_new.db). "
        "Use only values these tools return; never invent stock, prices, dates or amounts. "
        "'Today' is desk.date_today."
    ),
)


def connect() -> sqlite3.Connection:
    """Open the working copy. Refuses the original, and never creates a blank file."""
    if DB_PATH == ORIGINAL_DB:
        raise RuntimeError("Refusing to open campus_customs.db; tools use campus_customs_new.db only.")
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Working database not found: {DB_PATH.name}. Copy campus_customs.db to campus_customs_new.db first.")
    # mode=rw: open an existing file only (plain connect would silently create an empty database)
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=rw", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite leaves declared links unchecked unless this is on
    return conn


def shop_today(conn: sqlite3.Connection) -> date:
    """The shop's 'today' from desk.date_today."""
    row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError("desk.date_today is missing; cannot tell what is overdue.")
    return date.fromisoformat(row["date_today"])


@mcp.tool(annotations=READ_ONLY)
def check_stock(sku: str, size: str, qty_needed: int | None = None) -> dict:
    """Stock on hand for one SKU and size (inventory), with that SKU's unit cost and
    list price (pricing). If qty_needed is given, also returns the shortfall.

    Example: check_stock("CC-HOOD-NAVY", "M", 20) for ticket 103.
    """
    with closing(connect()) as conn:
        item = conn.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()
        if item is None:
            sizes = [r["size"] for r in conn.execute("SELECT size FROM inventory WHERE sku = ?", (sku,))]
            return {
                "found": False,
                "sku": sku,
                "size": size,
                "message": f"No inventory row for {sku} size {size}."
                + (f" Sizes on file: {', '.join(sizes)}." if sizes else " SKU not in inventory."),
            }
        price = conn.execute(
            "SELECT unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()

    result = {"found": True, **dict(item), "in_stock": item["qty"] > 0}
    if price is not None:
        result["unit_cost"] = price["unit_cost"]
        result["list_price"] = price["list_price"]
    else:
        result["pricing_message"] = f"No pricing row for {sku}."
    if qty_needed is not None:
        result["qty_needed"] = qty_needed
        result["shortfall"] = max(0, qty_needed - item["qty"])
    return result


@mcp.tool(annotations=READ_ONLY)
def get_open_invoices(vendor_id: int | None = None, invoice_id: int | None = None) -> dict:
    """Unpaid invoices (status 'open') with the vendor's name, specialty and lead days,
    and days overdue measured from desk.date_today. Filter by vendor_id or invoice_id,
    or leave both empty for every open invoice.

    A vendor with an open invoice will not ship new product (shop rule), so this
    tells the agents which vendors are blocked.

    Example: get_open_invoices(invoice_id=501) for ticket 101.
    """
    sql = (
        "SELECT i.id AS invoice_id, i.vendor_id, v.name AS vendor_name, v.specialty, "
        "v.lead_days, i.amount, i.due_date, i.status, i.description "
        "FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE i.status = 'open'"
    )
    args: list = []
    if vendor_id is not None:
        sql += " AND i.vendor_id = ?"
        args.append(vendor_id)
    if invoice_id is not None:
        sql += " AND i.id = ?"
        args.append(invoice_id)

    with closing(connect()) as conn:
        today = shop_today(conn)
        rows = conn.execute(sql + " ORDER BY i.due_date", args).fetchall()

    invoices = []
    for r in rows:
        days = (today - date.fromisoformat(r["due_date"])).days
        invoices.append({**dict(r), "days_overdue": max(0, days), "overdue": days > 0})
    return {
        "today": today.isoformat(),
        "open_invoices": invoices,
        "total_open": round(sum(r["amount"] for r in invoices), 2),
        "blocked_vendor_ids": sorted({r["vendor_id"] for r in invoices}),
        "message": None if invoices else "No open invoices match.",
    }


@mcp.tool(annotations=READ_ONLY)
def get_rent_due(lease_id: int) -> dict:
    """One lease's rent (leases): space, landlord, monthly rent and next due date, with
    days until due from desk.date_today, and whether the cash on hand (cash_accounts)
    covers it without going negative. Read only; it does not pay.

    Example: get_rent_due(1) for ticket 102.
    """
    with closing(connect()) as conn:
        today = shop_today(conn)
        lease = conn.execute(
            "SELECT id AS lease_id, space_name, landlord, monthly_rent, next_due, notes "
            "FROM leases WHERE id = ?",
            (lease_id,),
        ).fetchone()
        accounts = [dict(r) for r in conn.execute("SELECT name, balance, date FROM cash_accounts")]

    if lease is None:
        return {"found": False, "lease_id": lease_id, "message": f"No lease with id {lease_id}."}

    days_until = (date.fromisoformat(lease["next_due"]) - today).days
    cash_total = round(sum(a["balance"] for a in accounts), 2)
    return {
        "found": True,
        **dict(lease),
        "today": today.isoformat(),
        "days_until_due": days_until,
        "overdue": days_until < 0,
        "cash_accounts": accounts,
        "cash_total": cash_total,
        "cash_covers_rent": cash_total >= lease["monthly_rent"],
        "cash_after_rent": round(cash_total - lease["monthly_rent"], 2),
    }


if __name__ == "__main__":
    mcp.run()
