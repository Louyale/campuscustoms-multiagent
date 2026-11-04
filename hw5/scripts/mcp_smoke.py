"""Problem 4: test each MCP tool through the vibe coder (Claude Code) and save the evidence.

For each of the three tools, this script:
1. Asks Claude Code a plain-English prompt in headless mode, connected through .mcp.json.
   Only our campus-customs server is loaded (--strict-mcp-config), so other MCP servers,
   such as a mail connector, can't be used. No built-in tools are allowed, and only the
   one MCP tool under test is permitted.
2. Captures the actual tool call (name and arguments) and the tool's raw output from
   Claude Code's event stream.
3. Reads data/campus_customs_new.db directly with SQL, and checks every value in the
   tool output against it.
4. Saves everything to output/mcp_smoke.json.

The tools only read, and the script checks that the working database is byte-for-byte
unchanged afterwards.

Run from hw5/ with the project venv's python first on PATH, so .mcp.json's "python"
command finds FastMCP:
    python scripts/mcp_smoke.py
Set CLAUDE_BIN if the `claude` command isn't on PATH.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "data" / "campus_customs_new.db"
OUT = PROJECT / "output" / "mcp_smoke.json"
SERVER = "campus-customs"

TESTS = [
    {
        "ticket": 103,
        "tool": "check_stock",
        "prompt": "For ticket 103, use the campus-customs check_stock tool to look up SKU CC-HOOD-NAVY in size M with qty_needed 20, and report exactly what the tool returns.",
    },
    {
        "ticket": 101,
        "tool": "get_open_invoices",
        "prompt": "For ticket 101, use the campus-customs get_open_invoices tool with invoice_id 501, and report exactly what the tool returns.",
    },
    {
        "ticket": 102,
        "tool": "get_rent_due",
        "prompt": "For ticket 102, use the campus-customs get_rent_due tool for lease_id 1, and report exactly what the tool returns.",
    },
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def claude_bin() -> str:
    found = os.getenv("CLAUDE_BIN") or shutil.which("claude")
    if not found:
        sys.exit("Claude Code CLI not found. Put `claude` on PATH or set CLAUDE_BIN.")
    return found


def ask_vibe_coder(test: dict) -> dict:
    """Run one headless Claude Code prompt; return the tool call, raw tool output and reply."""
    full_tool = f"mcp__{SERVER}__{test['tool']}"
    cmd = [
        claude_bin(), "-p", test["prompt"],
        "--mcp-config", str(PROJECT / ".mcp.json"), "--strict-mcp-config",
        "--tools", "", "--allowedTools", full_tool,
        "--no-session-persistence", "--output-format", "stream-json", "--verbose",
    ]
    proc = subprocess.run(cmd, cwd=PROJECT, capture_output=True, text=True,
                          encoding="utf-8", stdin=subprocess.DEVNULL, timeout=300)
    connected, tools_seen, call, output, reply = None, [], None, None, None
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            connected = {s["name"]: s["status"] for s in ev.get("mcp_servers", [])}
            tools_seen = [t for t in ev.get("tools", []) if t.startswith(f"mcp__{SERVER}__")]
        content = ev.get("message", {}).get("content") if ev.get("type") in ("assistant", "user") else None
        for c in content if isinstance(content, list) else []:
            if c.get("type") == "tool_use" and c.get("name") == full_tool and call is None:
                call = {"id": c["id"], "name": c["name"], "arguments": c.get("input", {})}
            if c.get("type") == "tool_result" and call and c.get("tool_use_id") == call["id"]:
                raw = c.get("content")
                text = "".join(x.get("text", "") for x in raw) if isinstance(raw, list) else raw
                output = json.loads(text)
        if ev.get("type") == "result":
            reply = ev.get("result")
    if call is None or output is None:
        sys.exit(f"{test['tool']}: the vibe coder did not call the tool.\n{proc.stdout[-2000:]}\n{proc.stderr[-1000:]}")
    return {"connected": connected, "tools_seen": tools_seen, "call": call, "output": output, "reply": reply}


# ---- independent checks: read the database directly and compare every value ----

def db():
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def today(conn) -> date:
    return date.fromisoformat(conn.execute("SELECT date_today FROM desk").fetchone()[0])


def expect_check_stock(args: dict) -> dict:
    with db() as c:
        inv = dict(c.execute("SELECT sku,name,size,qty,location FROM inventory WHERE sku=? AND size=?",
                             (args["sku"], args["size"])).fetchone())
        pr = c.execute("SELECT unit_cost,list_price FROM pricing WHERE sku=?", (args["sku"],)).fetchone()
    exp = {"found": True, **inv, "in_stock": inv["qty"] > 0, "unit_cost": pr["unit_cost"], "list_price": pr["list_price"]}
    if args.get("qty_needed") is not None:
        exp["qty_needed"] = args["qty_needed"]
        exp["shortfall"] = max(0, args["qty_needed"] - inv["qty"])
    return exp


def expect_get_open_invoices(args: dict) -> dict:
    with db() as c:
        t = today(c)
        sql = ("SELECT i.id AS invoice_id,i.vendor_id,v.name AS vendor_name,v.specialty,v.lead_days,"
               "i.amount,i.due_date,i.status,i.description FROM invoices i JOIN vendors v ON v.id=i.vendor_id "
               "WHERE i.status='open'")
        a = []
        if args.get("vendor_id") is not None:
            sql += " AND i.vendor_id=?"; a.append(args["vendor_id"])
        if args.get("invoice_id") is not None:
            sql += " AND i.id=?"; a.append(args["invoice_id"])
        rows = [dict(r) for r in c.execute(sql + " ORDER BY i.due_date", a)]
    for r in rows:
        d = (t - date.fromisoformat(r["due_date"])).days
        r.update(days_overdue=max(0, d), overdue=d > 0)
    return {"today": t.isoformat(), "open_invoices": rows, "total_open": round(sum(r["amount"] for r in rows), 2),
            "blocked_vendor_ids": sorted({r["vendor_id"] for r in rows}), "message": None if rows else "No open invoices match."}


def expect_get_rent_due(args: dict) -> dict:
    with db() as c:
        t = today(c)
        lease = dict(c.execute("SELECT id AS lease_id,space_name,landlord,monthly_rent,next_due,notes FROM leases WHERE id=?",
                               (args["lease_id"],)).fetchone())
        accts = [dict(r) for r in c.execute("SELECT name,balance,date FROM cash_accounts")]
    days = (date.fromisoformat(lease["next_due"]) - t).days
    cash = round(sum(x["balance"] for x in accts), 2)
    return {"found": True, **lease, "today": t.isoformat(), "days_until_due": days, "overdue": days < 0,
            "cash_accounts": accts, "cash_total": cash, "cash_covers_rent": cash >= lease["monthly_rent"],
            "cash_after_rent": round(cash - lease["monthly_rent"], 2)}


EXPECT = {"check_stock": expect_check_stock, "get_open_invoices": expect_get_open_invoices, "get_rent_due": expect_get_rent_due}


def compare(got, exp, path="") -> list[dict]:
    """Field-by-field comparison; returns one row per leaf value."""
    rows = []
    if isinstance(exp, dict):
        for k in sorted(set(exp) | set(got if isinstance(got, dict) else {})):
            rows += compare((got or {}).get(k, "<missing>"), exp.get(k, "<not expected>"), f"{path}.{k}" if path else k)
    elif isinstance(exp, list):
        for i in range(max(len(exp), len(got) if isinstance(got, list) else 0)):
            g = got[i] if isinstance(got, list) and i < len(got) else "<missing>"
            e = exp[i] if i < len(exp) else "<not expected>"
            rows += compare(g, e, f"{path}[{i}]")
    else:
        rows.append({"field": path, "tool_value": got, "database_value": exp, "match": got == exp})
    return rows


def main() -> None:
    before = sha256(DB)
    results = []
    for t in TESTS:
        print(f"Asking the vibe coder to run {t['tool']} (ticket {t['ticket']}) ...", flush=True)
        run = ask_vibe_coder(t)
        checks = compare(run["output"], EXPECT[t["tool"]](run["call"]["arguments"]))
        ok = all(c["match"] for c in checks)
        print(f"  {run['call']['name']} {run['call']['arguments']} -> {sum(c['match'] for c in checks)}/{len(checks)} values match the database")
        results.append({
            "ticket": t["ticket"],
            "prompt": t["prompt"],
            "tool_name": t["tool"],
            "mcp_tool_called": run["call"]["name"],
            "tool_arguments": run["call"]["arguments"],
            "tool_output": run["output"],
            "vibe_coder_reply": run["reply"],
            "matches_database": ok,
            "values_checked": len(checks),
            "database_check": checks,
            "server_status": run["connected"],
            "tools_listed": run["tools_seen"],
        })
    after = sha256(DB)
    report = {
        "problem": "Problem 4: Add the MCP server to vibe coder and test each tool",
        "vibe_coder": "Claude Code (headless, connected through .mcp.json)",
        "mcp_config": ".mcp.json",
        "database": "data/campus_customs_new.db",
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "all_tools_match_database": all(r["matches_database"] for r in results),
        "database_unchanged": before == after,
        "database_sha256": after,
        "tests": results,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"All match: {report['all_tools_match_database']}; database unchanged: {report['database_unchanged']}; saved {OUT.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
