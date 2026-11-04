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
- Money moves only after a human approves. Agents can *request* a payment
  (request_payment). Only the human approval step can pay (approve_and_pay),
  and it needs HUMAN_APPROVAL_CODE from .env, which no agent is given. Paying
  refuses if the cash would go below zero.
- Customer messages are drafts saved on the board (the drafts table). Nothing
  is ever sent.

Tools added in Problem 5 create two board tables in the working copy if they're
missing: drafts and approval_requests. A reset (copying the original back)
removes them.

Run:  python mcp_server/server.py
"""

from __future__ import annotations

import os
import re
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("CAMPUS_DB", PROJECT_DIR / "data" / "campus_customs_new.db")).resolve()
ORIGINAL_DB = (PROJECT_DIR / "data" / "campus_customs.db").resolve()
load_dotenv(PROJECT_DIR / ".env")  # for HUMAN_APPROVAL_CODE, which is never given to any agent

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True}
WRITES = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False}
HUMAN_ONLY = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False}

TICKET_STATUSES = ("open", "in_progress", "waiting_approval", "blocked", "resolved")
REORDER_POINT = 5  # the shop owner's rule: fewer than 5 units on hand means reorder

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


# ============================================================================ Problem 5: more tools
# ---------------------------------------------------------------- board tables (created on first use)

BOARD_TABLES = """
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    to_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    written_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status = 'draft')
);
CREATE TABLE IF NOT EXISTS approval_requests (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    kind TEXT NOT NULL CHECK (kind IN ('invoice', 'rent', 'purchase_order')),
    ref_id INTEGER,
    vendor_id INTEGER REFERENCES vendors(id),
    sku TEXT, size TEXT, qty INTEGER,
    payee TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    account TEXT NOT NULL,
    reason TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    requested_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'paid', 'rejected', 'refused')),
    decided_by TEXT, decided_at TEXT, decision_note TEXT, payment_id INTEGER
);
CREATE TABLE IF NOT EXISTS building_requests (
    id INTEGER PRIMARY KEY,
    lease_id INTEGER NOT NULL REFERENCES leases(id),
    ticket_id INTEGER REFERENCES tickets(id),
    issue TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low', 'normal', 'urgent')),
    requested_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'waiting_approval', 'done')),
    updated_at TEXT, note TEXT
);
"""


def board(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Make sure the two board tables exist in the working copy."""
    conn.executescript(BOARD_TABLES)
    return conn


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def add_month(d: date) -> date:
    y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    for day in (d.day, 30, 29, 28):
        try:
            return date(y, m, day)
        except ValueError:
            continue
    raise ValueError(d)


def cash_row(conn: sqlite3.Connection, account: str):
    return conn.execute("SELECT name, balance, date FROM cash_accounts WHERE name = ?", (account,)).fetchone()


def pending_total(conn: sqlite3.Connection, account: str) -> float:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM approval_requests WHERE status = 'pending' AND account = ?", (account,)
    ).fetchone()
    return round(row[0], 2)


# ---------------------------------------------------------------- tickets (Boss)

@mcp.tool(annotations=READ_ONLY)
def get_ticket(ticket_id: int) -> dict:
    """One ticket from the board (tickets), with any drafts and payment requests already filed
    for it (drafts, approval_requests). Boss starts every ticket here."""
    with closing(board(connect())) as conn:
        today = shop_today(conn)
        t = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if t is None:
            return {"found": False, "ticket_id": ticket_id, "message": f"No ticket {ticket_id}."}
        drafts = [dict(r) for r in conn.execute("SELECT * FROM drafts WHERE ticket_id = ? ORDER BY id", (ticket_id,))]
        reqs = [dict(r) for r in conn.execute("SELECT * FROM approval_requests WHERE ticket_id = ? ORDER BY id", (ticket_id,))]
    return {"found": True, "today": today.isoformat(), "ticket": dict(t), "drafts": drafts, "payment_requests": reqs}


@mcp.tool(annotations=READ_ONLY)
def list_tickets(status: str | None = None) -> dict:
    """Tickets on the board (tickets), optionally only one status, such as 'open'."""
    with closing(connect()) as conn:
        today = shop_today(conn)
        sql, args = "SELECT * FROM tickets", []
        if status:
            sql += " WHERE status = ?"
            args.append(status)
        rows = [dict(r) for r in conn.execute(sql + " ORDER BY id", args)]
    return {"today": today.isoformat(), "count": len(rows), "tickets": rows}


@mcp.tool(annotations=WRITES)
def update_ticket_status(ticket_id: int, status: str) -> dict:
    """Move a ticket to a new status on the board (tickets.status). Allowed: open, in_progress,
    waiting_approval, blocked, resolved. Changes nothing else."""
    if status not in TICKET_STATUSES:
        return {"updated": False, "message": f"Status must be one of {', '.join(TICKET_STATUSES)}."}
    with closing(connect()) as conn:
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"updated": False, "message": f"No ticket {ticket_id}."}
        with conn:
            conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    return {"updated": True, "ticket_id": ticket_id, "from": row["status"], "to": status}


# ---------------------------------------------------------------- stock and vendors (Inventory)

@mcp.tool(annotations=READ_ONLY)
def list_inventory(low_only: bool = False) -> dict:
    """Every SKU and size on hand (inventory), with unit cost and list price (pricing), value at
    cost, and a reorder flag for anything with fewer than 5 units (the shop's reorder point)."""
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT i.sku, i.name, i.size, i.qty, i.location, p.unit_cost, p.list_price "
            "FROM inventory i LEFT JOIN pricing p ON p.sku = i.sku ORDER BY i.sku, i.size"
        ).fetchall()
    items = []
    for r in rows:
        item = dict(r)
        item["needs_reorder"] = r["qty"] < REORDER_POINT
        item["value_at_cost"] = round(r["qty"] * r["unit_cost"], 2) if r["unit_cost"] is not None else None
        if not low_only or item["needs_reorder"]:
            items.append(item)
    return {
        "reorder_point": REORDER_POINT,
        "items": items,
        "total_value_at_cost": round(sum(i["value_at_cost"] or 0 for i in items), 2),
        "missing_pricing": sorted({i["sku"] for i in items if i["unit_cost"] is None}),
    }


@mcp.tool(annotations=READ_ONLY)
def list_vendors(specialty_contains: str | None = None) -> dict:
    """Vendors (vendors) with specialty and lead days, and whether an open invoice (invoices)
    blocks each one from shipping. Lead times come only from this table."""
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT v.id, v.name, v.specialty, v.lead_days, "
            "COUNT(i.id) AS open_invoices, COALESCE(SUM(i.amount), 0) AS open_amount "
            "FROM vendors v LEFT JOIN invoices i ON i.vendor_id = v.id AND i.status = 'open' "
            "GROUP BY v.id ORDER BY v.id"
        ).fetchall()
    vendors = [{**dict(r), "blocked": r["open_invoices"] > 0} for r in rows]
    if specialty_contains:
        vendors = [v for v in vendors if specialty_contains.lower() in v["specialty"].lower()]
    return {"vendors": vendors}


# ---------------------------------------------------------------- cash and payments (Accounting)

@mcp.tool(annotations=READ_ONLY)
def get_cash_balance() -> dict:
    """Cash on hand in every account (cash_accounts), and how much is already promised to
    pending payment requests (approval_requests), so no money is counted twice."""
    with closing(board(connect())) as conn:
        today = shop_today(conn)
        accounts = [dict(r) for r in conn.execute("SELECT name, balance, date FROM cash_accounts")]
        for a in accounts:
            a["pending_requests"] = pending_total(conn, a["name"])
            a["available_after_pending"] = round(a["balance"] - a["pending_requests"], 2)
    return {"today": today.isoformat(), "accounts": accounts,
            "cash_total": round(sum(a["balance"] for a in accounts), 2)}


@mcp.tool(annotations=READ_ONLY)
def list_payments() -> dict:
    """Payments actually made (payments), each one approved by a human. Used for income statements."""
    with closing(connect()) as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM payments ORDER BY id")]
    return {"payments": rows, "total_paid": round(sum(r["amount"] for r in rows), 2),
            "message": None if rows else "No payments have been recorded."}


@mcp.tool(annotations=READ_ONLY)
def list_payment_requests(status: str | None = None) -> dict:
    """Payment requests waiting for, or already decided by, a human (approval_requests)."""
    with closing(board(connect())) as conn:
        sql, args = "SELECT * FROM approval_requests", []
        if status:
            sql += " WHERE status = ?"
            args.append(status)
        rows = [dict(r) for r in conn.execute(sql + " ORDER BY id", args)]
    return {"requests": rows}


@mcp.tool(annotations=WRITES)
def request_payment(kind: str, ticket_id: int, reason: str, requested_by: str,
                    ref_id: int | None = None, vendor_id: int | None = None,
                    sku: str | None = None, size: str | None = None, qty: int | None = None,
                    account: str = "checking") -> dict:
    """File a payment request for a human to approve (approval_requests). This does NOT pay.

    The amount always comes from the database, never from the agent:
    - kind 'invoice': ref_id is an open invoice id; the amount is that invoice's amount.
    - kind 'rent': ref_id is a lease id; the amount is the lease's monthly_rent.
    - kind 'purchase_order': vendor_id, sku, size and qty; the amount is qty x pricing.unit_cost.
      Refused if that vendor has an open invoice (a blocked vendor won't ship).
    Refused if the account can't cover it after other pending requests (no negative balances),
    or if the same item is already pending.
    """
    with closing(board(connect())) as conn:
        acct = cash_row(conn, account)
        if acct is None:
            return {"filed": False, "message": f"No cash account named {account!r}."}
        if conn.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
            return {"filed": False, "message": f"No ticket {ticket_id}."}

        if kind == "invoice":
            inv = conn.execute(
                "SELECT i.*, v.name AS vendor FROM invoices i JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?", (ref_id,)
            ).fetchone()
            if inv is None or inv["status"] != "open":
                return {"filed": False, "message": f"Invoice {ref_id} is not an open invoice."}
            payee, amount, vendor_id = inv["vendor"], inv["amount"], inv["vendor_id"]
        elif kind == "rent":
            lease = conn.execute("SELECT * FROM leases WHERE id = ?", (ref_id,)).fetchone()
            if lease is None:
                return {"filed": False, "message": f"No lease {ref_id}."}
            payee, amount = lease["landlord"], lease["monthly_rent"]
        elif kind == "purchase_order":
            vendor = conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
            price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
            if vendor is None or price is None or not size or not qty or qty <= 0:
                return {"filed": False, "message": "A purchase order needs a real vendor_id, a priced sku, a size, and qty above 0."}
            if conn.execute("SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)).fetchone() is None:
                return {"filed": False, "message": f"{sku} size {size} is not a stocked item."}
            blocker = conn.execute(
                "SELECT id, amount FROM invoices WHERE vendor_id = ? AND status = 'open'", (vendor_id,)
            ).fetchone()
            if blocker:
                return {"filed": False, "message": f"{vendor['name']} is blocked by open invoice {blocker['id']} "
                                                   f"(${blocker['amount']:.2f}); it won't ship until that is paid."}
            payee, amount, ref_id = vendor["name"], round(qty * price["unit_cost"], 2), None
        else:
            return {"filed": False, "message": "kind must be invoice, rent or purchase_order."}

        dup = conn.execute(
            "SELECT id FROM approval_requests WHERE status = 'pending' AND kind = ? "
            "AND COALESCE(ref_id, -1) = COALESCE(?, -1) AND COALESCE(sku, '') = COALESCE(?, '') "
            "AND COALESCE(size, '') = COALESCE(?, '')",
            (kind, ref_id, sku, size),
        ).fetchone()
        if dup:
            return {"filed": False, "message": f"Already pending as request {dup['id']}."}
        available = round(acct["balance"] - pending_total(conn, account), 2)
        if amount > available:
            return {"filed": False, "message": f"Not enough cash: ${amount:.2f} needed, ${available:.2f} available "
                                               "after pending requests. No negative balances."}

        # File the request under the ticket the bill belongs to: the ticket that links this invoice
        # (tickets.invoice_id) or this lease (tickets.lease_id). That keeps the board accurate even when
        # it's raised while working a different ticket.
        link_col = {"invoice": "invoice_id", "rent": "lease_id"}.get(kind)
        linked = None
        if link_col:
            linked = conn.execute(f"SELECT id FROM tickets WHERE {link_col} = ? ORDER BY id LIMIT 1", (ref_id,)).fetchone()
        filed_under = linked["id"] if linked else ticket_id
        if filed_under != ticket_id:
            reason = f"{reason} (raised while working ticket {ticket_id})"
        with conn:
            cur = conn.execute(
                "INSERT INTO approval_requests (ticket_id, kind, ref_id, vendor_id, sku, size, qty, payee, amount, "
                "account, reason, requested_by, requested_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (filed_under, kind, ref_id, vendor_id, sku, size, qty, payee, amount, account, reason, requested_by, now_utc()),
            )
    note = (f" Filed under ticket {filed_under}, which this {kind} belongs to, not ticket {ticket_id}."
            if filed_under != ticket_id else "")
    return {"filed": True, "request_id": cur.lastrowid, "status": "pending", "kind": kind, "payee": payee,
            "amount": amount, "account": account, "ticket_id": filed_under, "raised_from_ticket": ticket_id,
            "cash_before": acct["balance"], "available_after_this_request": round(available - amount, 2),
            "message": "Waiting for a human to approve on the dashboard. Nothing has been paid." + note}


# ---------------------------------------------------------------- spelling and grammar (Customer Service)

SHOP_WORDS = {
    "hoodie", "hoodies", "tee", "tees", "yale", "bulldog", "bulldogs", "sku", "skus", "restock", "restocking",
    "reprint", "campus", "customs", "chapel", "merch", "xl", "os", "eta", "po",
}
CONFUSIONS = [  # (pattern, problem, suggestion)
    (r"\b(could|should|would|must) of\b", "'{0}' should be 'have', not 'of'", "{1} have"),
    (r"\balot\b", "'alot' is not a word", "a lot"),
    (r"\byour welcome\b", "'your' should be 'you're'", "you're welcome"),
    (r"\bthier\b", "misspelling", "their"),
    (r"\bdefinately\b", "misspelling", "definitely"),
    (r"\bit's own\b", "'it's' means 'it is'", "its own"),
]


def shop_vocabulary() -> set[str]:
    """Words the checker accepts because they are in the shop's own data (names, products, places)."""
    words = set(SHOP_WORDS)
    with closing(connect()) as conn:
        for sql in ("SELECT name FROM inventory", "SELECT requester FROM tickets", "SELECT subject FROM tickets",
                    "SELECT name FROM vendors", "SELECT specialty FROM vendors", "SELECT landlord FROM leases",
                    "SELECT space_name FROM leases", "SELECT sku FROM inventory"):
            for (text,) in conn.execute(sql):
                words.update(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]*", text or ""))
    return words


def text_issues(text: str, label: str, vocab: set[str], spell) -> list[dict]:
    issues = []
    for word in sorted({w for w in re.findall(r"[A-Za-z][A-Za-z']*", text)}):
        core = word.strip("'").lower()
        if len(core) < 2 or core in vocab or core.endswith("'s") and core[:-2] in vocab:
            continue
        if spell.unknown([core]):
            issues.append({"where": label, "type": "spelling", "text": word, "suggestion": spell.correction(core)})
    for m in re.finditer(r"\b(\w+)\s+\1\b", text, re.IGNORECASE):
        issues.append({"where": label, "type": "grammar", "text": m.group(0), "suggestion": m.group(1), "problem": "repeated word"})
    for m in re.finditer(r"\b(a)\s+([aeiou]\w*)", text, re.IGNORECASE):
        if not re.match(r"(?i)(uni|use|usu|one|euro|u[bcdfgklmnprst][aeiou])", m.group(2)):
            issues.append({"where": label, "type": "grammar", "text": m.group(0), "suggestion": f"an {m.group(2)}", "problem": "use 'an' before a vowel sound"})
    for m in re.finditer(r"\b(an)\s+([bcdfgjklmnpqrstvwxyz]\w*)", text, re.IGNORECASE):
        if not re.match(r"(?i)(hour|honest|honor|heir|x)", m.group(2)):
            issues.append({"where": label, "type": "grammar", "text": m.group(0), "suggestion": f"a {m.group(2)}", "problem": "use 'a' before a consonant sound"})
    for pattern, problem, fix in CONFUSIONS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            issues.append({"where": label, "type": "grammar", "text": m.group(0),
                           "suggestion": fix.format(m.group(0), m.group(1) if m.groups() else "") if fix else None,
                           "problem": problem.format(m.group(0))})
    for m in re.finditer(r"\bi\b", text):
        issues.append({"where": label, "type": "grammar", "text": "i", "suggestion": "I", "problem": "capitalize 'I'"})
    for m in re.finditer(r"(^|[.!?]\s+|\n\s*)([a-z])", text):
        issues.append({"where": label, "type": "grammar", "text": m.group(2) + text[m.end():m.end() + 10],
                       "suggestion": m.group(2).upper(), "problem": "start each sentence with a capital letter"})
    if re.search(r" {2,}", text):
        issues.append({"where": label, "type": "style", "text": "double space", "suggestion": "single space", "problem": "double space"})
    for m in re.finditer(r"\s+([,.!?;:])", text):
        issues.append({"where": label, "type": "grammar", "text": m.group(0), "suggestion": m.group(1), "problem": "no space before punctuation"})
    for opener, closer in (("(", ")"), ('"', '"')):
        if (text.count(opener) != text.count(closer)) if opener != closer else text.count(opener) % 2:
            issues.append({"where": label, "type": "grammar", "text": opener, "suggestion": closer, "problem": "unbalanced brackets or quotes"})
    if label == "body":
        last_line = [l for l in text.strip().splitlines() if l.strip()]
        sentences = [l for l in last_line if len(l.split()) > 3]
        for l in sentences:
            if not re.search(r"[.!?:,)\"]$", l.strip()):  # a comma is right after a greeting or sign-off
                issues.append({"where": label, "type": "grammar", "text": l.strip()[-30:], "suggestion": "end with punctuation",
                               "problem": "sentence has no end punctuation"})
    return issues


def check_text(subject: str, body: str) -> dict:
    from spellchecker import SpellChecker  # offline dictionary, no AI call
    vocab, spell = shop_vocabulary(), SpellChecker()
    issues = text_issues(subject, "subject", vocab, spell) + text_issues(body, "body", vocab, spell)
    return {"passed": not issues, "issues": issues, "words_checked": len(re.findall(r"[A-Za-z']+", subject + " " + body))}


@mcp.tool(annotations=READ_ONLY)
def check_spelling_grammar(subject: str, body: str) -> dict:
    """Check a draft's subject and body for spelling and grammar before it's saved. Offline
    dictionary plus grammar rules: repeated words, a/an, capital letters, 'could of', a lone 'i',
    spacing, punctuation and brackets. The shop's own names and products count as correct words
    (inventory, tickets, vendors, leases). Fix every issue, then check again until it passes."""
    return check_text(subject, body)


# ---------------------------------------------------------------- drafts (Customer Service)

@mcp.tool(annotations=WRITES)
def save_customer_draft(ticket_id: int, to_name: str, subject: str, body: str, written_by: str) -> dict:
    """Save a message draft on the board (drafts). It is never sent; there is no send tool.
    Refused unless the subject and body pass check_spelling_grammar."""
    check = check_text(subject, body)
    if not check["passed"]:
        return {"saved": False, "message": "Fix the spelling and grammar issues first, then save again.",
                "issues": check["issues"]}
    with closing(board(connect())) as conn:
        if conn.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
            return {"saved": False, "message": f"No ticket {ticket_id}."}
        with conn:
            cur = conn.execute(
                "INSERT INTO drafts (ticket_id, to_name, subject, body, written_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (ticket_id, to_name, subject, body, written_by, now_utc()),
            )
    return {"saved": True, "draft_id": cur.lastrowid, "status": "draft", "sent": False,
            "message": "Saved on the board for a human to read. Nothing was sent."}


@mcp.tool(annotations=READ_ONLY)
def list_drafts(ticket_id: int | None = None) -> dict:
    """Message drafts on the board (drafts)."""
    with closing(board(connect())) as conn:
        sql, args = "SELECT * FROM drafts", []
        if ticket_id is not None:
            sql += " WHERE ticket_id = ?"
            args.append(ticket_id)
        rows = [dict(r) for r in conn.execute(sql + " ORDER BY id", args)]
    return {"drafts": rows}


# ---------------------------------------------------------------- leases and building requests (Facilities)

@mcp.tool(annotations=READ_ONLY)
def list_leases() -> dict:
    """Every lease (leases) with its rent, landlord, next due date and days until due (desk)."""
    with closing(connect()) as conn:
        today = shop_today(conn)
        rows = [dict(r) for r in conn.execute("SELECT * FROM leases ORDER BY id")]
    for r in rows:
        r["days_until_due"] = (date.fromisoformat(r["next_due"]) - today).days
        r["overdue"] = r["days_until_due"] < 0
    return {"today": today.isoformat(), "leases": rows,
            "total_monthly_rent": round(sum(r["monthly_rent"] for r in rows), 2)}


@mcp.tool(annotations=READ_ONLY)
def get_lease(lease_id: int) -> dict:
    """One lease in full (leases), with its rent payment history (payments, kind 'rent'), any rent
    requests waiting for a human (approval_requests), and its building requests (building_requests)."""
    with closing(board(connect())) as conn:
        today = shop_today(conn)
        lease = conn.execute("SELECT * FROM leases WHERE id = ?", (lease_id,)).fetchone()
        if lease is None:
            return {"found": False, "lease_id": lease_id, "message": f"No lease {lease_id}."}
        paid = [dict(r) for r in conn.execute("SELECT * FROM payments WHERE kind = 'rent' AND ref_id = ? ORDER BY id", (lease_id,))]
        reqs = [dict(r) for r in conn.execute("SELECT * FROM approval_requests WHERE kind = 'rent' AND ref_id = ? ORDER BY id", (lease_id,))]
        building = [dict(r) for r in conn.execute("SELECT * FROM building_requests WHERE lease_id = ? ORDER BY id", (lease_id,))]
    days = (date.fromisoformat(lease["next_due"]) - today).days
    return {"found": True, "lease": dict(lease), "today": today.isoformat(), "days_until_due": days, "overdue": days < 0,
            "rent_payments": paid, "rent_requests": reqs, "building_requests": building,
            "missing_information": ["Lease start and end dates, deposit, and renewal terms aren't in the database."]}


@mcp.tool(annotations=WRITES)
def log_building_request(lease_id: int, issue: str, priority: str, requested_by: str, ticket_id: int | None = None) -> dict:
    """Log a building or maintenance request for a leased space (building_requests). For example, a
    broken lock, a leak, or a landlord notice. It goes on the board for a human; no contractor or
    landlord is contacted. priority: low, normal or urgent."""
    if priority not in ("low", "normal", "urgent"):
        return {"logged": False, "message": "priority must be low, normal or urgent."}
    if not issue.strip():
        return {"logged": False, "message": "Describe the issue."}
    with closing(board(connect())) as conn:
        if conn.execute("SELECT 1 FROM leases WHERE id = ?", (lease_id,)).fetchone() is None:
            return {"logged": False, "message": f"No lease {lease_id}."}
        if ticket_id is not None and conn.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
            return {"logged": False, "message": f"No ticket {ticket_id}."}
        with conn:
            cur = conn.execute(
                "INSERT INTO building_requests (lease_id, ticket_id, issue, priority, requested_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (lease_id, ticket_id, issue.strip(), priority, requested_by, now_utc()),
            )
    return {"logged": True, "request_id": cur.lastrowid, "status": "open",
            "message": "Logged on the board for a human. No one outside the shop was contacted."}


@mcp.tool(annotations=READ_ONLY)
def list_building_requests(status: str | None = None) -> dict:
    """Building and maintenance requests on the board (building_requests), optionally one status."""
    with closing(board(connect())) as conn:
        sql, args = "SELECT * FROM building_requests", []
        if status:
            sql += " WHERE status = ?"
            args.append(status)
        rows = [dict(r) for r in conn.execute(sql + " ORDER BY id", args)]
    return {"requests": rows}


@mcp.tool(annotations=WRITES)
def update_building_request(request_id: int, status: str, note: str = "") -> dict:
    """Move a building request along (building_requests.status): open, in_progress, waiting_approval
    or done. Anything that costs money still needs a payment request and a human's approval."""
    if status not in ("open", "in_progress", "waiting_approval", "done"):
        return {"updated": False, "message": "status must be open, in_progress, waiting_approval or done."}
    with closing(board(connect())) as conn:
        row = conn.execute("SELECT status FROM building_requests WHERE id = ?", (request_id,)).fetchone()
        if row is None:
            return {"updated": False, "message": f"No building request {request_id}."}
        with conn:
            conn.execute("UPDATE building_requests SET status = ?, note = ?, updated_at = ? WHERE id = ?",
                         (status, note, now_utc(), request_id))
    return {"updated": True, "request_id": request_id, "from": row["status"], "to": status}


# ---------------------------------------------------------------- financial statements (Accounting)

# Figures the shop database simply doesn't hold. Every statement lists these as missing, never guessing.
NOT_IN_DATABASE_BALANCE = [
    "Fixed assets (store fixtures, equipment, the point-of-sale system): no table records them.",
    "Accounts receivable: the shop doesn't model revenue, so no customer owes it money in the data.",
    "Owner's equity detail (owner contributions, retained earnings): equity is shown only as assets minus liabilities.",
    "Other liabilities (wages, taxes, utilities, loans, credit cards): no table records them.",
]
NOT_IN_DATABASE_INCOME = [
    "Revenue / sales: the shop doesn't model revenue, so revenue is shown as $0, not estimated.",
    "Cost of goods sold: with no sales recorded, no inventory has been expensed as sold.",
    "Other expenses (wages, utilities, insurance, taxes, depreciation): no table records them.",
]


@mcp.tool(annotations=READ_ONLY)
def build_balance_sheet() -> dict:
    """Balance sheet as of desk.date_today, built only from database figures, with every missing
    figure flagged. Assets: cash (cash_accounts) and inventory at cost (inventory x pricing).
    Liabilities: open invoices (invoices), plus rent once it's overdue (leases). Rent not yet due
    is shown as a note. Equity = assets - liabilities, so the sheet always balances."""
    with closing(board(connect())) as conn:
        today = shop_today(conn)
        cash = [dict(r) for r in conn.execute("SELECT name, balance FROM cash_accounts ORDER BY name")]
        stock = conn.execute(
            "SELECT i.sku, i.size, i.qty, p.unit_cost FROM inventory i LEFT JOIN pricing p ON p.sku = i.sku"
        ).fetchall()
        invoices = [dict(r) for r in conn.execute(
            "SELECT i.id, v.name AS vendor, i.amount, i.due_date FROM invoices i JOIN vendors v ON v.id = i.vendor_id "
            "WHERE i.status = 'open' ORDER BY i.id")]
        leases = [dict(r) for r in conn.execute("SELECT id, space_name, landlord, monthly_rent, next_due FROM leases")]
        pending = [dict(r) for r in conn.execute(
            "SELECT id, kind, payee, amount FROM approval_requests WHERE status = 'pending' ORDER BY id")]

    lines, missing = [], list(NOT_IN_DATABASE_BALANCE)
    for a in cash:
        lines.append({"section": "asset", "label": f"Cash: {a['name']}", "amount": a["balance"], "source": "cash_accounts"})
    unpriced = sorted({r["sku"] for r in stock if r["unit_cost"] is None})
    inv_value = round(sum(r["qty"] * r["unit_cost"] for r in stock if r["unit_cost"] is not None), 2)
    lines.append({"section": "asset", "label": "Inventory at cost (units on hand x unit cost)", "amount": inv_value,
                  "source": "inventory, pricing"})
    if unpriced:
        missing.append(f"Unit cost missing for {', '.join(unpriced)}, so that stock isn't valued.")
    for inv in invoices:
        lines.append({"section": "liability", "label": f"Accounts payable: invoice {inv['id']} ({inv['vendor']}, due {inv['due_date']})",
                      "amount": inv["amount"], "source": "invoices"})
    for lease in leases:
        due = date.fromisoformat(lease["next_due"])
        if due < today:
            lines.append({"section": "liability", "label": f"Overdue rent: {lease['space_name']} ({lease['landlord']})",
                          "amount": lease["monthly_rent"], "source": "leases"})
        else:
            lines.append({"section": "note", "label": f"Rent of ${lease['monthly_rent']:,.2f} for {lease['space_name']} due {lease['next_due']} "
                          f"({(due - today).days} days); not a liability until it's due", "amount": None, "source": "leases"})
    for p in pending:
        lines.append({"section": "note", "label": f"Pending payment request {p['id']} ({p['kind']}, {p['payee']}): awaiting human approval; not yet paid",
                      "amount": p["amount"], "source": "approval_requests"})

    total_assets = round(sum(l["amount"] for l in lines if l["section"] == "asset"), 2)
    total_liabilities = round(sum(l["amount"] for l in lines if l["section"] == "liability"), 2)
    equity = round(total_assets - total_liabilities, 2)
    lines.append({"section": "equity", "label": "Owner's equity (assets minus liabilities)", "amount": equity, "source": "calculated"})
    return {"kind": "balance_sheet", "as_of": today.isoformat(), "lines": lines,
            "total_assets": total_assets, "total_liabilities": total_liabilities, "equity": equity,
            "balances": round(total_assets, 2) == round(total_liabilities + equity, 2),
            "missing_information": missing}


@mcp.tool(annotations=READ_ONLY)
def build_income_statement(period_start: str | None = None, period_end: str | None = None) -> dict:
    """Income statement for a period (dates as YYYY-MM-DD; default: everything up to desk.date_today),
    built only from database figures, with every missing figure flagged. Cash basis: expenses are
    payments actually made (payments), grouped by kind. Pending requests are never counted. Revenue
    is $0 because the shop doesn't model revenue."""
    with closing(connect()) as conn:
        today = shop_today(conn)
        end = period_end or today.isoformat()
        start = period_start or "0001-01-01"
        rows = [dict(r) for r in conn.execute(
            "SELECT kind, amount, paid_at, approved_by FROM payments WHERE paid_at BETWEEN ? AND ? ORDER BY paid_at",
            (start, end))]
    groups: dict[str, float] = {}
    for r in rows:
        groups[r["kind"]] = round(groups.get(r["kind"], 0) + r["amount"], 2)
    labels = {"rent": "Rent", "invoice": "Vendor invoices paid", "purchase_order": "Inventory purchases (purchase orders)"}
    lines = [{"section": "revenue", "label": "Revenue (sales)", "amount": 0.0, "source": "not modeled: no sales table"}]
    lines += [{"section": "expense", "label": labels.get(k, k), "amount": v, "source": "payments"} for k, v in sorted(groups.items())]
    expenses = round(sum(groups.values()), 2)
    missing = list(NOT_IN_DATABASE_INCOME)
    if not rows:
        missing.append("No payments have been recorded in this period, so expenses are $0.")
    if groups.get("invoice") or groups.get("purchase_order"):
        lines.append({"section": "note", "label": "Cash basis: vendor and purchase-order payments for stock are shown as spending. "
                      "On an accrual basis they'd be inventory until sold.", "amount": None, "source": "payments"})
    return {"kind": "income_statement", "as_of": f"{start if period_start else 'start of records'} to {end}",
            "lines": lines, "revenue": 0.0, "expenses": expenses, "net_income": round(0.0 - expenses, 2),
            "payments_counted": len(rows), "missing_information": missing}


# ---------------------------------------------------------------- human approval only (no agent has these)

def human_check(approval_code: str, person: str) -> str | None:
    expected = os.getenv("HUMAN_APPROVAL_CODE")
    if not expected:
        return "HUMAN_APPROVAL_CODE is not set in .env, so no payment can be approved."
    if approval_code != expected:
        return "Approval code is wrong. Only a human on the dashboard can approve payments."
    if not person or not person.strip():
        return "The approver must be named."
    return None


@mcp.tool(annotations=HUMAN_ONLY)
def approve_and_pay(request_id: int, approved_by: str, approval_code: str) -> dict:
    """HUMAN ONLY (dashboard). Pay one pending request after a person approves it.

    Refuses if the code is wrong, the request isn't pending, or the account would go below zero.
    If paid, all of this happens in one transaction:
    - a payments row is added, with approved_by
    - cash_accounts.balance goes down, and its date becomes desk.date_today
    - the invoice is marked paid, or the lease's next_due moves forward one month
    - the request is marked paid
    """
    problem = human_check(approval_code, approved_by)
    if problem:
        return {"paid": False, "message": problem}
    with closing(board(connect())) as conn:
        today = shop_today(conn)
        req = conn.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None or req["status"] != "pending":
            return {"paid": False, "message": f"Request {request_id} is not pending."}
        acct = cash_row(conn, req["account"])
        balance = acct["balance"] if acct else 0.0
        if balance < req["amount"]:
            with conn:
                conn.execute(
                    "UPDATE approval_requests SET status = 'refused', decided_by = ?, decided_at = ?, decision_note = ? WHERE id = ?",
                    (approved_by, now_utc(), "not enough cash; no negative balances", request_id),
                )
            return {"paid": False, "message": f"Refused: ${req['amount']:.2f} is more than the ${balance:.2f} in "
                                              f"{req['account']}. No negative balances."}
        with conn:  # one transaction: all of it happens, or none of it
            new_balance = round(balance - req["amount"], 2)
            ref = req["ref_id"] if req["kind"] in ("invoice", "rent") else req["id"]
            cur = conn.execute(
                "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
                (req["kind"], ref, req["amount"], req["account"], today.isoformat(), approved_by),
            )
            conn.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
                         (new_balance, today.isoformat(), req["account"]))
            if req["kind"] == "invoice":
                conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (req["ref_id"],))
                change = f"invoice {req['ref_id']} marked paid"
            elif req["kind"] == "rent":
                lease = conn.execute("SELECT next_due FROM leases WHERE id = ?", (req["ref_id"],)).fetchone()
                nxt = add_month(date.fromisoformat(lease["next_due"])).isoformat()
                conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (nxt, req["ref_id"]))
                change = f"lease {req['ref_id']} next_due moved to {nxt}"
            else:
                change = f"purchase order for {req['qty']} x {req['sku']} {req['size']} paid to {req['payee']}"
            conn.execute(
                "UPDATE approval_requests SET status = 'paid', decided_by = ?, decided_at = ?, payment_id = ? WHERE id = ?",
                (approved_by, now_utc(), cur.lastrowid, request_id),
            )
    return {"paid": True, "payment_id": cur.lastrowid, "request_id": request_id, "amount": req["amount"],
            "payee": req["payee"], "approved_by": approved_by, "cash_before": balance,
            "cash_after": new_balance, "updated": change}


@mcp.tool(annotations=HUMAN_ONLY)
def reject_payment_request(request_id: int, rejected_by: str, approval_code: str, reason: str = "") -> dict:
    """HUMAN ONLY (dashboard). Reject a pending payment request. No money moves."""
    problem = human_check(approval_code, rejected_by)
    if problem:
        return {"rejected": False, "message": problem}
    with closing(board(connect())) as conn:
        req = conn.execute("SELECT status FROM approval_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None or req["status"] != "pending":
            return {"rejected": False, "message": f"Request {request_id} is not pending."}
        with conn:
            conn.execute(
                "UPDATE approval_requests SET status = 'rejected', decided_by = ?, decided_at = ?, decision_note = ? WHERE id = ?",
                (rejected_by, now_utc(), reason, request_id),
            )
    return {"rejected": True, "request_id": request_id}


if __name__ == "__main__":
    mcp.run()
