"""Build output/desk_tickets.html: one self-contained page (double-click to open, no internet).

Tabs: 101, 102, 103 (each with an Expected plan, and an empty Actual section to fill after the
agents run), plus Cash and Reflection tabs, which say "coming later" for now.

Ticket facts at the top of each tab are read from the ORIGINAL database (read-only), so nothing is
invented. The Expected plans are Lou's expectations, written in plain words in PLANS below; edit
them there and rerun.

Run from hw5/:  python scripts/build_desk_tickets.py
"""

from __future__ import annotations

import html
import re
import sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DB = PROJECT / "data" / "campus_customs.db"
OUT = PROJECT / "output" / "desk_tickets.html"
AVATARS = PROJECT / "assets" / "agents"

AGENTS = {
    "boss": ("🕴️", "Boss (Mr. D'Onofrio)"), "inventory": ("📦", "Inventory"), "accounting": ("🧮", "Accounting"),
    "facilities": ("🧢", "Facilities"), "customer_service": ("👕", "Customer Service"),
}

# ----------------------------------------------------------------------------- Lou's expected plans
PLANS = {
    101: {
        "first": ("inventory",
                  "Ticket 101 is a customer order for one Classic Bulldog Tee in size S, so the first question is whether "
                  "it's on the shelf and, if not, who can restock it. Inventory owns stock by SKU and size, and it's the "
                  "agent that will find that size S is at 0 and that the reprint vendor is blocked."),
        "delegations": [
            ("boss", "inventory", "Check CC-TEE-WHITE size S for 1 unit, find the restock vendor, its lead time, and whether anything blocks it. "
                                  "Expected answer: 0 on hand, 1 short; Bulldog Print Co (apparel reprint, 5 lead days) is blocked by open invoice 501."),
            ("boss", "accounting", "Prepare the payment that unblocks the vendor: file invoice 501 ($840 to Bulldog Print Co, 3 days overdue) "
                                   "for human approval, and confirm cash covers it ($3,400 in checking). The $8 reprint order can only follow "
                                   "once the invoice is paid, so no purchase order yet."),
            ("boss", "customer_service", "Draft a friendly reply to Tauhid Zaman: size S is out of stock, a restock is being arranged, and the shop "
                                         "will confirm timing. No delivery date is promised while the vendor is blocked."),
        ],
        "not_called": [("facilities", "Nothing on this ticket touches the lease, rent or the building.")],
        "tools": {
            "boss": ["get_ticket", "rank_open_tickets", "update_ticket_status", "check_in_on_assignments", "list_payment_requests"],
            "inventory": ["check_stock (CC-TEE-WHITE, S, 1)", "list_vendors", "get_open_invoices (invoice 501)"],
            "accounting": ["get_cash_balance", "get_open_invoices (invoice 501)", "request_payment (invoice 501)"],
            "customer_service": ["check_spelling_grammar", "save_customer_draft"],
        },
        "outcome": [
            "Priority urgent: invoice 501 is 3 days overdue, and a customer is waiting.",
            "One pending payment request: $840 to Bulldog Print Co. Nothing is paid until a human approves.",
            "One draft to Tauhid Zaman on the board, never sent.",
            "Ticket status waiting_approval (the restock is blocked until invoice 501 is paid).",
        ],
    },
    102: {
        "first": ("facilities",
                  "Ticket 102 is the landlord's rent notice for lease 1. Facilities owns the lease, so it confirms the rent, "
                  "the landlord and the due date from the lease record, not from the email, before any money is lined up."),
        "delegations": [
            ("boss", "facilities", "Confirm lease 1 from the record: the Chapel Street shop, Elm City Properties, $2,400, due 2026-09-02 "
                                   "(2 days away). Check that the notice matches the record."),
            ("boss", "accounting", "File the $2,400 rent payment request for human approval, and check cash. If invoice 501's $840 is "
                                   "also pending, $3,400 − $840 − $2,400 leaves $160, still not negative."),
        ],
        "not_called": [
            ("inventory", "No product is involved."),
            ("customer_service", "The landlord needs to be paid, not written to. A human can send thanks after paying, if wanted."),
        ],
        "tools": {
            "boss": ["get_ticket", "rank_open_tickets", "update_ticket_status", "check_in_on_assignments", "list_payment_requests"],
            "facilities": ["get_rent_due (lease 1)", "get_lease (lease 1)"],
            "accounting": ["get_cash_balance", "list_payment_requests", "request_payment (rent, lease 1)"],
        },
        "outcome": [
            "Priority urgent: rent is due within 3 days.",
            "One pending payment request: $2,400 to Elm City Properties. Nothing is paid until a human approves.",
            "When approved, lease 1's next_due moves to 2026-10-02 and checking drops by $2,400.",
            "Ticket status waiting_approval.",
        ],
    },
    103: {
        "first": ("inventory",
                  "Ticket 103 asks for 20 Basic Hoodies in size M at a bulk discount. Before anyone talks price, the shop needs "
                  "to know whether it can fill 20. Inventory checks size M and the restock path."),
        "delegations": [
            ("boss", "inventory", "Check CC-HOOD-NAVY size M for 20 units. Expected answer: 8 on hand, 12 short; restock from Bulldog "
                                  "Print Co (5 lead days), which is blocked by open invoice 501."),
            ("boss", "accounting", "Check margins for a bulk discount: unit cost $22, list price $58, so the margin is $36 a hoodie (62%). "
                                   "Recommend a discount range that stays above cost, and say whether the 12-hoodie restock ($264 at cost) "
                                   "fits in cash. It won't while the vendor is blocked, or if rent and invoice 501 leave only $160."),
            ("boss", "customer_service", "Draft a reply to the Yale AI Club: 8 hoodies are ready now, the rest after a restock, and the discount "
                                         "is being reviewed. No price or date is promised until a human approves."),
        ],
        "not_called": [("facilities", "No lease, rent or building issue.")],
        "tools": {
            "boss": ["get_ticket", "rank_open_tickets", "update_ticket_status", "check_in_on_assignments"],
            "inventory": ["check_stock (CC-HOOD-NAVY, M, 20)", "list_vendors", "get_open_invoices"],
            "accounting": ["check_stock (pricing)", "get_cash_balance", "list_payment_requests"],
            "customer_service": ["check_spelling_grammar", "save_customer_draft"],
        },
        "outcome": [
            "Priority normal: a discount request, ranked below the two urgent bills.",
            "No payment request filed: a restock order would be refused while Bulldog Print Co is blocked, and cash is needed for the urgent bills first.",
            "The discount decision goes to a human, with Accounting's margin numbers.",
            "One draft to the Yale AI Club on the board, never sent. Ticket status blocked or waiting_approval.",
        ],
    },
}


YALE_Y = (
    '<div class="yale" aria-label="Yale"><svg viewBox="0 0 100 100" width="58" height="58" role="img" aria-label="Yale block Y">'
    '<polygon fill="#00356b" points="6,8 44,8 44,20 38,20 50,44 62,20 56,20 56,8 94,8 94,20 84,20 61,60 61,84 74,84 '
    '74,94 26,94 26,84 39,84 39,60 16,20 6,20"/></svg></div>'
)


def desk_art(today: str) -> str:
    """A desk with tickets 101, 102 and 103 on it, drawn in white and light Yale blue for the banner."""
    def card(x, y, rot, num, label):
        return (f'<g transform="translate({x},{y}) rotate({rot})">'
                f'<rect x="-30" y="-20" width="60" height="40" rx="4" fill="#ffffff" stroke="#9cc0ea" stroke-width="1.5"/>'
                f'<rect x="-30" y="-20" width="60" height="9" rx="4" fill="#286dc0"/>'
                f'<text x="0" y="5" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="800" fill="#00356b">{num}</text>'
                f'<text x="0" y="15" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="7" fill="#5b6474">{label}</text></g>')
    return (
        '<svg class="desk" viewBox="0 0 300 110" width="380" height="139" role="img" '
        'aria-label="A desk with tickets 101, 102 and 103 on it">'
        # lamp
        '<path d="M262,28 L250,62" stroke="#cfe0f5" stroke-width="3" stroke-linecap="round"/>'
        '<path d="M244,22 L280,22 L270,34 L254,34 Z" fill="#ffffff"/><circle cx="262" cy="38" r="6" fill="#fff6c9" opacity=".8"/>'
        '<rect x="242" y="60" width="18" height="4" rx="2" fill="#cfe0f5"/>'
        # desk top and legs
        '<rect x="14" y="64" width="272" height="10" rx="3" fill="#ffffff"/>'
        '<rect x="14" y="74" width="272" height="4" fill="#9cc0ea"/>'
        '<rect x="28" y="78" width="10" height="28" fill="#cfe0f5"/><rect x="262" y="78" width="10" height="28" fill="#cfe0f5"/>'
        '<rect x="196" y="78" width="60" height="22" rx="2" fill="#cfe0f5"/><rect x="220" y="86" width="12" height="3" rx="1.5" fill="#00356b"/>'
        # the three tickets
        + card(62, 46, -8, "101", "Tee order") + card(128, 42, 3, "102", "Rent") + card(194, 46, -4, "103", "Bulk discount")
        + f'<text x="150" y="104" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="#d6e2f3">the desk · {today}</text>'
        '</svg>'
    )


def ticket_facts() -> dict[int, dict]:
    with sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        today = c.execute("SELECT date_today FROM desk").fetchone()[0]
        out = {}
        for t in c.execute("SELECT * FROM tickets ORDER BY id"):
            out[t["id"]] = {**dict(t), "today": today}
        return out


def avatar(key: str, size: int = 34) -> str:
    svg = (AVATARS / f"{key}.svg").read_text(encoding="utf-8")
    svg = re.sub(r'id="c"', f'id="c-{key}-{size}"', svg).replace("url(#c)", f"url(#c-{key}-{size})")
    return svg.replace("<svg ", f'<svg width="{size}" height="{size}" class="av" ', 1)


def chip(key: str) -> str:
    e, name = AGENTS[key]
    return f'<span class="chip">{avatar(key, 26)}<span>{html.escape(name)}</span></span>'


def ticket_tab(tid: int, facts: dict) -> str:
    p = PLANS[tid]
    first_key, first_why = p["first"]
    dl = "".join(
        f'<li><span class="flow">{chip(f)} <span class="arrow">→</span> {chip(t)}</span>'
        f'<p>{html.escape(task)}</p></li>' for f, t, task in p["delegations"])
    nc = "".join(f'<li>{chip(k)} <span class="muted">not called: {html.escape(why)}</span></li>' for k, why in p["not_called"])
    tools = "".join(
        f'<li>{chip(k)}<ul class="tools">' + "".join(f"<li><code>{html.escape(x)}</code></li>" for x in v) + "</ul></li>"
        for k, v in p["tools"].items())
    outcome = "".join(f"<li>{html.escape(x)}</li>" for x in p["outcome"])
    used = {first_key} | {t for _, t, _ in p["delegations"]}
    f = facts
    item = f"{f['qty']} × {f['sku']} size {f['size']}" if f["sku"] else (f"lease {f['lease_id']}" if f["lease_id"] else "(none)")
    link = ", ".join(x for x in [f"invoice {f['invoice_id']}" if f["invoice_id"] else "", f"lease {f['lease_id']}" if f["lease_id"] else ""] if x) or "(none)"
    return f"""
<section class="panel" id="t{tid}">
  <div class="ticket-head">
    <div><div class="kicker">Ticket {tid} · {html.escape(f['type'].replace('_', ' '))}</div>
      <h2>{html.escape(f['subject'])}</h2>
      <p class="muted">From <b>{html.escape(f['requester'])}</b> · “{html.escape(f['notes'] or '')}”</p></div>
    <dl class="facts"><div><dt>Item</dt><dd>{html.escape(item)}</dd></div><div><dt>Linked</dt><dd>{html.escape(link)}</dd></div>
      <div><dt>Shop date</dt><dd>{f['today']}</dd></div><div><dt>Agents planned</dt><dd>{len(used)} of 5</dd></div></dl>
  </div>
  <div class="cols">
    <article class="card expected">
      <h3><span class="tag exp">Expected</span> What we expect the team to do</h3>
      <ol class="plan">
        <li><h4>Who Boss calls first, and why</h4>
          <p class="lead">{chip('boss')} <span class="arrow">→</span> {chip(first_key)}</p>
          <p>{html.escape(first_why)}</p></li>
        <li><h4>Every delegation we expect, in order</h4><ol class="deleg">{dl}</ol>
          <ul class="notcalled">{nc}</ul></li>
        <li><h4>MCP tools we expect this run to use</h4><ul class="toolgroups">{tools}</ul></li>
      </ol>
      <div class="outcome"><h4>Expected result</h4><ul>{outcome}</ul></div>
    </article>
    <article class="card actual">
      <h3><span class="tag act">Actual</span> What the team really did</h3>
      <p class="muted">To be filled in after the agents resolve this ticket, so it can be compared line by line with the plan.</p>
      <ol class="plan blank">
        <li><h4>Who Boss called first</h4><div class="slot">(after the run)</div></li>
        <li><h4>Every delegation that happened</h4><div class="slot">(after the run)</div></li>
        <li><h4>MCP tools the run used</h4><div class="slot">(after the run)</div></li>
      </ol>
      <div class="outcome"><h4>Actual result, and how it compares</h4><div class="slot">(after the run)</div></div>
    </article>
  </div>
</section>"""


CSS = """
:root{--yale:#00356b;--yale2:#286dc0;--bg:#f4f7fb;--card:#ffffff;--tint:#eef3fb;--line:#d5deea;--text:#16202e;--muted:#5b6474;--ok:#00356b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 "Segoe UI",system-ui,-apple-system,Arial,sans-serif}
header{padding:20px 36px 18px;display:flex;align-items:center;gap:22px;background:var(--yale);color:#fff;flex-wrap:wrap}header h1{margin:0;font-size:40px;line-height:1.05;letter-spacing:.3px;font-weight:800}.h1sub{font-size:19px;font-weight:600;color:#d6e2f3;margin-top:2px}.yale{background:#fff;border-radius:12px;padding:6px;display:flex;box-shadow:0 1px 4px rgba(0,0,0,.25)}.desk{flex:0 0 auto;margin-left:8px}
header .sub{color:#d6e2f3;margin:2px 0 0}.team{margin-left:auto;display:flex;gap:6px}
input[name=tab]{position:absolute;opacity:0;pointer-events:none}
.tabs{display:flex;gap:6px;padding:14px 36px 0;border-bottom:2px solid var(--yale);flex-wrap:wrap;background:var(--bg)}
.tabs label{padding:10px 18px;border:1px solid var(--line);border-bottom:none;border-radius:10px 10px 0 0;color:var(--yale);cursor:pointer;background:#fff;font-weight:600}
.tabs label:hover{background:var(--tint)}
main{padding:24px 36px 48px}.panel{display:none}
#r101:checked~main #t101,#r102:checked~main #t102,#r103:checked~main #t103,#rcash:checked~main #tcash,#rrefl:checked~main #trefl{display:block}
#r101:checked~.tabs label[for=r101],#r102:checked~.tabs label[for=r102],#r103:checked~.tabs label[for=r103],#rcash:checked~.tabs label[for=rcash],#rrefl:checked~.tabs label[for=rrefl]{color:#fff;background:var(--yale);border-color:var(--yale)}
.ticket-head{display:flex;gap:24px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;margin-bottom:18px}
.kicker{color:var(--yale2);text-transform:uppercase;font-size:12px;letter-spacing:1.4px;font-weight:700}h2{margin:4px 0 6px;font-size:24px;color:var(--yale)}
.facts{display:grid;grid-template-columns:repeat(4,auto);gap:10px 22px;margin:0;background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 18px}
.facts dt{color:var(--muted);font-size:12px}.facts dd{margin:0;font-weight:600;color:var(--yale)}
.cols{display:grid;grid-template-columns:1.25fr 1fr;gap:18px}@media(max-width:1000px){.cols{grid-template-columns:1fr}.facts{grid-template-columns:repeat(2,auto)}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:0 1px 3px rgba(0,53,107,.06)}.card h3{margin:0 0 12px;font-size:17px;display:flex;gap:10px;align-items:center;color:var(--yale)}
.tag{font-size:12px;padding:3px 10px;border-radius:999px;font-weight:700;letter-spacing:.4px}.tag.exp{background:var(--yale);color:#fff}.tag.act{border:1px dashed var(--muted);color:var(--muted)}
.plan{padding-left:20px;margin:0}.plan>li{margin:0 0 18px}.plan>li::marker{color:var(--yale);font-weight:700}h4{margin:0 0 6px;font-size:15px;color:var(--yale)}
.chip{display:inline-flex;align-items:center;gap:6px;background:var(--tint);border:1px solid var(--line);border-radius:999px;padding:2px 10px 2px 3px;font-weight:600;font-size:13.5px;vertical-align:middle;color:var(--yale)}
.av{display:block}.arrow{color:var(--yale2);font-weight:700;margin:0 4px}.lead{margin:2px 0 6px}
.deleg{padding-left:20px}.deleg li{margin:0 0 12px}.deleg li::marker{color:var(--muted)}.deleg p{margin:6px 0 0}.flow{display:inline-flex;align-items:center;flex-wrap:wrap}
.notcalled{list-style:none;padding:0;margin:8px 0 0}.notcalled li{margin:6px 0;opacity:.8}
.toolgroups{list-style:none;padding:0;margin:0}.toolgroups>li{margin:0 0 10px}.tools{margin:6px 0 0 34px;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:6px}.tools li{margin:0}
code{background:var(--tint);border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:13px;color:var(--yale)}
.outcome{border-top:1px solid var(--line);padding-top:12px;margin-top:6px}.outcome ul{margin:0;padding-left:20px}
.slot{border:1px dashed var(--line);border-radius:10px;padding:14px;color:var(--muted);font-style:italic;background:#fafcff}.muted{color:var(--muted)}
.later{max-width:760px;background:#fff;border:1px dashed var(--line);border-radius:14px;padding:28px}.later h2{margin-top:0}
.summary{width:100%;border-collapse:collapse;margin:0 0 22px;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}
.summary th,.summary td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:center}.summary th:first-child,.summary td:first-child{text-align:left}
.summary th{color:#fff;background:var(--yale);font-weight:600;font-size:13px}.yes{color:var(--ok);font-weight:800}.no{color:#a9b3c2}
caption{caption-side:top;text-align:left;font-weight:700;padding:0 0 8px;color:var(--yale)}
#rcash:checked~main .matrix,#rrefl:checked~main .matrix{display:none}
footer{color:var(--muted);font-size:12.5px;padding:0 36px 30px}
"""


def matrix() -> str:
    rows = ""
    for key, (e, name) in AGENTS.items():
        cells = ""
        for tid in (101, 102, 103):
            p = PLANS[tid]
            used = key == "boss" or key == p["first"][0] or any(t == key for _, t, _ in p["delegations"])
            cells += f'<td class="{"yes" if used else "no"}">{"✓" if used else "—"}</td>'
        rows += f"<tr><td>{chip(key)}</td>{cells}</tr>"
    return ('<div class="matrix"><table class="summary"><caption>Table 1: Agents Planned per Ticket (not every specialist on every ticket)</caption>'
            '<tr><th>Agent</th><th>101 Tee order</th><th>102 Rent</th><th>103 Bulk discount</th></tr>' + rows + "</table></div>")


def main() -> None:
    facts = ticket_facts()
    team = "".join(avatar(k, 36) for k in AGENTS)
    tabs = "".join(ticket_tab(t, facts[t]) for t in (101, 102, 103))
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Campus Customs: Desk Tickets (Expected plans)</title><style>{CSS}</style></head>
<body>
<header>{YALE_Y}<div class="titles"><h1>Campus Customs</h1><div class="h1sub">Desk Tickets</div><p class="sub">Problem 6 plan, written before the agents resolve the tickets · shop date {facts[101]['today']}</p></div>
{desk_art(facts[101]['today'])}<div class="team" aria-label="The agent team">{team}</div></header>
<input type="radio" name="tab" id="r101" checked><input type="radio" name="tab" id="r102"><input type="radio" name="tab" id="r103">
<input type="radio" name="tab" id="rcash"><input type="radio" name="tab" id="rrefl">
<nav class="tabs" aria-label="Tickets"><label for="r101">101 · Tee order</label><label for="r102">102 · Rent</label>
<label for="r103">103 · Bulk discount</label><label for="rcash">Cash</label><label for="rrefl">Reflection</label></nav>
<main>
<div class="panel" id="t101" style="display:none"></div>
{matrix()}
{tabs}
<section class="panel" id="tcash"><div class="later"><h2>Cash</h2><p>Coming later: cash before and after each approved payment, once the agents run and a human approves.</p></div></section>
<section class="panel" id="trefl"><div class="later"><h2>Reflection</h2><p>Coming later: how the Actual runs compared with these Expected plans, and what we learned.</p></div></section>
</main>
<footer>One self-contained file: open it by double-clicking, with no internet needed. Ticket facts are read from data/campus_customs.db. Built by scripts/build_desk_tickets.py.</footer>
</body></html>"""
    page = page.replace('<div class="panel" id="t101" style="display:none"></div>\n', "")
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(PROJECT)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
