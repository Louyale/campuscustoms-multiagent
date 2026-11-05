"""Problem 10: the Reflection tab of output/desk_tickets.html, in Lou's voice.

Five questions from the assignment, each followed by our answer, its evidence (links that jump to the ticket
and Cash tabs on the same page), and Boss's approval box. Run numbers and cash come from
output/resolved_tickets.json; shop facts come from the working database and the Problem 9 run.
Edit the answers here, flip APPROVED when Boss signs off, and rerun scripts/build_desk_tickets.py.
"""

from __future__ import annotations

# Flip to True as Boss (Mr. D'Onofrio) approves each answer.
APPROVED = {1: False, 2: False, 3: False, 4: False, 5: False}
APPROVED_ON = "2026-11-05"

CSS = """
.refl h2{color:var(--yale);margin:0 0 4px}.refl .lede{color:var(--muted);margin:0 0 16px}
.cashstrip{display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:0 0 18px;font-weight:700;color:var(--yale)}
.cashstrip .step{background:var(--tint);border-radius:8px;padding:4px 10px}.cashstrip .ok{color:#1f7a4d}
.qa{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin:0 0 20px;box-shadow:0 4px 12px rgba(0,32,64,.06)}
.qa .q{display:flex;gap:12px;align-items:flex-start}.qa .qn{background:var(--yale);color:#fff;font-weight:900;border-radius:10px;padding:6px 11px;flex:none}
.qa .q h3{margin:2px 0 10px;color:var(--yale);font-size:17px}
.qa .answer{border-left:4px solid var(--yale2,#286dc0);padding:2px 0 2px 14px}.qa .answer>p{margin:6px 0}
.qa ul{margin:6px 0 10px;padding-left:20px}.qa li{margin:4px 0}
.qa table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13.5px}.qa caption{text-align:left;font-weight:800;color:var(--yale);padding:4px 0}
.qa th{background:var(--yale);color:#fff;text-align:left;padding:7px 9px;vertical-align:top}.qa td{border-bottom:1px solid var(--line);padding:7px 9px;vertical-align:top}
.qa td.n{white-space:nowrap;text-align:right}
.grade{display:inline-block;background:var(--yale);color:#fff;font-weight:900;border-radius:8px;padding:2px 9px}
.ev{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0 4px;font-size:13px;color:var(--muted)}
.ev label{cursor:pointer;background:var(--tint);color:var(--yale);border:1px solid #b9cde8;border-radius:999px;padding:3px 11px;font-weight:700}
.ev label:hover{background:var(--yale);color:#fff}
.approve{margin-top:12px;border:2px dashed #9cb4d6;border-radius:10px;padding:8px 12px;color:var(--muted);font-weight:700;display:inline-block}
.approve.yes{border:2px solid var(--yale);color:var(--yale);background:var(--tint)}
"""

TAB = {"101": "r101", "102": "r102", "103": "r103", "Cash": "rcash"}


def evidence(*tabs: str, note: str = "") -> str:
    chips = "".join(f'<label for="{TAB[t]}">{"Tab " + t if t != "Cash" else "Cash tab"}</label>' for t in tabs)
    return f'<div class="ev">Evidence on this page: {chips}{(" · " + note) if note else ""}</div>'


def box(n: int) -> str:
    if APPROVED[n]:
        return f'<div class="approve yes">☑ Approved by Boss (Mr. D\'Onofrio), {APPROVED_ON}</div>'
    return '<div class="approve">☐ Waiting for Boss (Mr. D\'Onofrio) to approve this answer</div>'


def qa(n: int, question: str, body: str) -> str:
    return f"""<div class="qa" id="q{n}"><div class="q"><span class="qn">Q{n}</span><h3>{question}</h3></div>
  <div class="answer">{body}</div>{box(n)}</div>"""


def render(R: dict | None) -> str:
    if not R:
        return '<div class="later"><h2>Reflection</h2><p>Coming later.</p></div>'
    T = {t["id"]: t for t in R["tickets"]}
    c = R["cash"]
    calls = sum(t["run"]["model_calls"] for t in R["tickets"])
    cost = sum(t["run"]["cost_usd"] for t in R["tickets"])
    tin = sum(t["run"]["input_tokens"] for t in R["tickets"])
    tcache = sum(t["run"]["cached_input_tokens"] for t in R["tickets"])
    r = lambda tid: f"{T[tid]['run']['model_calls']} calls · ${T[tid]['run']['cost_usd']:.4f}"
    start, end = c["starting_checking_balance"], c["ending_checking_balance_by_math"]
    shortfall = 2400 - end

    strip = ('<div class="cashstrip">💵 The cash, to the penny:'
             f'<span class="step">Start ${start:,.2f}</span>→'
             + "→".join(f'<span class="step">{x["ticket"]}: {"−$" + format(-x["change"], ",.2f") if x["change"] else "$0.00"}</span>' for x in c["changes"])
             + f'→<span class="step">End ${end:,.2f}</span>'
             + f'<span class="ok">{"✓ matches cash_accounts" if c["matches_cash_accounts"] else "✗ does NOT match cash_accounts"}</span></div>')

    q1 = f"""<p><b>Bottom line:</b> the dream team closed all three tickets for about a penny (<b>${cost:.4f}</b> over {calls} model calls on gpt-6-luna), and the cash never missed by a cent. Not flawless, though, and I grade like a tough-but-fair boss.</p>
<table><caption>Table 4: Agent Scorecard by Ticket</caption>
<tr><th>Ticket</th><th>Grade</th><th>What the dream team nailed</th><th>What cost points</th><th>Cash</th><th>Run</th></tr>
<tr><td><b>101</b> Bulldog tee</td><td><span class="grade">A−</span></td><td>Boss went to Inventory first. Inventory found size S at 0, with Bulldog Print Co blocked by invoice 501. Accounting filed the $840, then got ahead of the curve and filed the $2,400 rent under 102, planning both urgent bills against one checking account.</td><td>Boss sent Customer Service back to drop "Professor," so two drafts went on the board, and this was our priciest run. The root cause was a missing rule in Boss's prompt. It's fixed now, and the draft tool revises instead of duplicating.</td><td class="n">−$840.00</td><td>{r(101)}</td></tr>
<tr><td><b>102</b> Rent due</td><td><span class="grade">A</span></td><td>Boss went to Facilities first. The lease was confirmed from the record, not the landlord's email, which is the scam guard working. The $2,400 waited for my signature, and lease 1 rolled to 2026-10-02. Our cheapest run.</td><td>Facilities' only tool call, <code>get_rent_due</code>, repeated a lookup Boss had already made. A landlord thank-you draft the plan didn't need.</td><td class="n">−$2,400.00</td><td>{r(102)}</td></tr>
<tr><td><b>103</b> Bulk hoodie discount</td><td><span class="grade">B+</span></td><td>The margin math was dead-on: $58 list, $22 cost, a $36 margin (62.07%). No price or date was promised. The ticket was flagged blocked, because the 12-hoodie restock ($264 at cost) doesn't fit the $160 left. The loop guard shut down an Accounting-to-Boss ping-pong.</td><td>Inventory told Accounting "4 short ($88)." The truth is 12 short ($264). Boss didn't lean on it, but a wrong number in the chain is still a wrong number.</td><td class="n">$0.00</td><td>{r(103)}</td></tr>
</table>
<ul>
<li><b>MVPs:</b>
  <ul>
  <li><b>Accounting:</b> filed both bills before anyone asked, and never let checking dip below zero.</li>
  <li><b>Boss:</b> made the right first call, 3 for 3.</li>
  </ul></li>
<li><b>Needs coaching:</b>
  <ul>
  <li><b>Inventory,</b> on its follow-up math in 103.</li>
  <li><b>Customer Service's double draft</b> on 101. In fairness, that was a management problem, not a staff one.</li>
  </ul></li>
<li><b>Why these grades:</b> money and safety count most. All three tickets got the money exactly right, with every payment behind a human signature and no real email sent. That's table stakes, and the team hit it every time. Points came off only for wasted motion and one bad number.</li>
</ul>{evidence("101", "102", "103", "Cash", note="each tab's Actual section lists the delegations, tools and approvals")}"""

    q2 = f"""<p><b>Short version:</b> Boss made the planned first call on all three tickets, the agents I said would sit out sat out, and the cash landed exactly where my Problem 6 plan said it would. My plan for 102 forecast "$3,400 − $840 − $2,400 leaves $160". The Cash tab says <b>${end:,.2f}</b>, matching <code>cash_accounts</code>. No daylight.</p>
<table><caption>Table 5: Expected vs. Actual by Ticket</caption>
<tr><th>Ticket</th><th>First call (Expected → Actual)</th><th>Hand-offs (Expected → Actual)</th><th>Who sat out</th><th>Outcome (Expected → Actual)</th></tr>
<tr><td><b>101</b></td><td>Inventory → Inventory ✓</td><td>3 (Inventory, Accounting, Customer Service) → 4 (Customer Service twice, for the revision)</td><td>Facilities ✓</td><td>$840 pending, waiting_approval → $840 filed, plus the rent filed early under 102. Approved; resolved.</td></tr>
<tr><td><b>102</b></td><td>Facilities → Facilities ✓</td><td>2 (Facilities, Accounting) → 2 (Facilities, Customer Service)</td><td>Inventory ✓</td><td>$2,400 pending → approved; resolved; next due 2026-10-02</td></tr>
<tr><td><b>103</b></td><td>Inventory → Inventory ✓</td><td>3 (Inventory, Accounting, Customer Service) → 4, including Accounting handing off to Inventory itself, plus 1 refused by the loop guard</td><td>Facilities ✓</td><td>blocked or waiting_approval → blocked, on the human discount call</td></tr>
</table>
<ul>
<li><b>101: the dream team beat the plan</b> by planning cash across tickets. My plan had only the $840 for 101; Accounting lined up the rent too, so both urgent bills were ready for one signing session. The miss was the extra Customer Service lap: two drafts where I expected one.</li>
<li><b>102: Accounting was skipped, and that was smart.</b> The rent request was already filed during 101, and the request tool refuses duplicates. My plan said Customer Service could sit this one out; Boss asked for a landlord acknowledgment anyway. It's harmless, and it stayed a draft, but it's not something I asked for.</li>
<li><b>103: the plan and the run agreed on the decision</b> (no promises; a human decides the discount) but took different roads. I expected a straight Boss-to-agents fan-out. Instead we saw real full connectivity: Accounting pulled Inventory in on its own, and the loop guard kept Accounting from bouncing the question back to Boss. The draft asked the club for its proposed price instead of offering the 8 hoodies on hand now, a more conservative play than my plan.</li>
</ul>{evidence("101", "102", "103", "Cash", note="each tab shows Expected and Actual side by side, with a \"Compared with Expected\" list")}"""

    q3 = f"""<p><b>Ticket 102, hands down, then 101.</b> Both are straight-line jobs: look it up, file it, draft it. There's nothing to argue about, so the hand-offs just relay facts from one desk to the next.</p>
<table><caption>Table 6: One Agent or the Dream Team?</caption>
<tr><th>Ticket</th><th>Best fit</th><th>Why</th></tr>
<tr><td><b>102</b> Rent due</td><td>One agent with tools</td><td>Facilities' whole contribution was one <code>get_rent_due</code> call, the same tool Boss had already run himself. One agent with <code>get_rent_due</code>, <code>get_cash_balance</code>, <code>request_payment</code> and <code>save_customer_draft</code> reads the lease, checks the $3,400, files the $2,400 for a human, and is done. Instead the run took {T[102]['run']['model_calls']} model calls. Boss alone used 8, including two hand-offs and two check-ins on work a single agent would just do.</td></tr>
<tr><td><b>101</b> Bulldog tee</td><td>One agent, close call</td><td>Stock → bill → draft is a relay, not a debate. The one real "team" moment was Accounting filing the rent early. A single agent holding the cash tools would see both bills anyway.</td></tr>
<tr><td><b>103</b> Bulk discount</td><td>The dream team</td><td>Money and judgment: margins, a restock that doesn't fit the cash, and a human-only discount call. Accounting cross-checked Inventory, and Boss kept final say. Even with Inventory's misread, the cross-check structure is what keeps a bad number from becoming a bad decision.</td></tr>
</table>
<ul>
<li><b>Why one agent is simpler:</b> every hand-off spins up a fresh model context that re-reads the prompt and the facts. Across the three runs the agents read <b>{tin:,}</b> input tokens, and <b>{tcache / tin:.0%}</b> of them were cached repeats. Caching kept the whole board at ${cost:.4f}, but a single agent wouldn't need the relay at all: fewer calls, fewer places for a number to get garbled (see 103's "4 short"), and one draft instead of two (see 101).</li>
<li><b>Why I'd still keep the dream team for the money stuff:</b> separation of duties and least privilege.
  <ul>
  <li>Only Accounting can file a payment request, and only a human can pay one.</li>
  <li>Customer Service can't see cash or invoices.</li>
  <li>With one all-powerful agent, one prompt injection in a landlord email could reach every tool in the shop.</li>
  </ul></li>
<li><b>My rule of thumb:</b> one agent for lookup-and-file tickets, and the dream team when there's money, judgment, or a number that needs a second set of eyes.</li>
</ul>{evidence("102", "101", "103", note="the tool counts per agent are in each tab's Actual section")}"""

    q4 = f"""<p>We already own the tools for these. When each one lands on the board as a ticket, the way our three did, it's just a matter of pointing the dream team at it. Every one keeps a human on every dollar, and checking in the black.</p>
<table><caption>Table 7: New Problems the Team Can Solve With Today's Tools</caption>
<tr><th>New problem</th><th>Campus Customs facts</th><th>Agents and MCP tools</th><th>Cash</th></tr>
<tr><td><b>1. The low-stock sweep</b>, before the next Crest Mug sellout</td><td>Five items sit below our reorder point of 5: the Crest Mug (0), the white tee in S (0), L (3) and XL (2), and the navy hoodie in S (4). Elm City Gifts does mugs in 3 days. Bulldog Print Co is unblocked now that the $840 is paid.</td><td>📦 Inventory: <code>list_inventory(low_only)</code> and <code>list_vendors</code>. 🧮 Accounting: <code>check_stock</code> (unit cost), <code>get_cash_balance</code> and <code>request_payment</code> (purchase orders). 🕴️ Boss ranks them, and a human approves.</td><td>Example: 10 mugs at $3.50 ($35) plus the one tee at $8 is $43, leaving $117. The pay tool refuses anything that would go negative.</td></tr>
<tr><td><b>2. A shop repair</b>, for example a front door at the Chapel Street shop that sticks</td><td>Lease 1 is the Chapel Street shop, with Elm City Properties as the landlord. The <code>building_requests</code> table is empty and ready.</td><td>🧢 Facilities: <code>get_lease(1)</code>, <code>log_building_request</code>, then <code>update_building_request</code> as the landlord responds. 👕 Customer Service drafts the note to Elm City Properties, which stays on the board. 🕴️ Boss tracks it to done.</td><td>$0.00 unless a human approves a payment</td></tr>
<tr><td><b>3. The October rent early warning</b></td><td>Lease 1's next rent, $2,400, is due 2026-10-02, and checking is ${end:,.2f}. That's a <b>${shortfall:,.2f}</b> gap, spotted a month out.</td><td>🕴️ Boss: <code>get_rent_due</code> and <code>rank_open_tickets</code>. 🧮 Accounting: <code>get_cash_balance</code>, <code>build_balance_sheet</code> and <code>build_income_statement</code>, for an owner-ready picture. The team flags it to the humans now, not on October 1.</td><td>No payment filed: it would break the no-negative-balance rule. We just get the warning early.</td></tr>
</table>
<ul><li><b>The big idea:</b> the same playbook as our three tickets (look it up, plan the cash, file for a human, draft but never send) scales to new problems with zero new code. That's low-hanging fruit.</li></ul>{evidence("Cash", "101", "102", note="the $160 ending balance and lease 1's new due date come from the Problem 9 run")}"""

    q5 = f"""<p>Here's where the dream team hits the wall. By design, our tools can only spend money, read the books, and draft messages.</p>
<table><caption>Table 8: New Problems the Team Can't Solve Yet, and What It Would Take</caption>
<tr><th>New problem</th><th>Why today's team can't</th><th>New tools (and tables)</th><th>New or expanded agent</th></tr>
<tr><td><b>1. Getting cash IN</b> to cover October's rent</td><td>We're ${shortfall:,.2f} short for 2026-10-02, and our rule is "cash only goes out." No tool records a sale, a deposit, or the Yale AI Club paying for hoodies.</td><td><code>record_sale</code>, <code>record_deposit</code> (human-approved), <code>list_receivables</code> and <code>refund_payment</code> (human-only). New <code>sales</code> and <code>receivables</code> tables; the balance sheet and income statement read them.</td><td><b>Sales &amp; Receivables:</b> owns revenue and customer invoices (drafted, never sent). Accounting reconciles every deposit against checking.</td></tr>
<tr><td><b>2. Receiving the restock</b> when Bulldog Print Co delivers</td><td>No tool changes stock, on purpose. So even after the tee arrives, inventory says 0 forever, and nothing tracks an order from placed to delivered.</td><td>A <code>purchase_orders</code> table (ordered → shipped → received), <code>track_delivery</code> (for example with QuickShip CT), and <code>receive_shipment(po_id, qty_counted)</code>, which adds stock only after a human signs off on the count.</td><td><b>Receiving clerk</b> (or Inventory, with new powers): matches each box to its PO and logs every count in the audit trail.</td></tr>
<tr><td><b>3. Making the discount call</b> that left 103 blocked</td><td>There's no pricing policy anywhere in the data, so the team can only recommend, never quote. And the 12-hoodie restock ($264 at cost) doesn't fit the ${end:,.2f} left.</td><td>A <code>discount_policy</code> table (a floor price per SKU that never goes under cost, plus volume tiers set by the owner), <code>create_quote</code>, and <code>approve_quote</code> (human-only above a set discount). Deposits from problem 1 fund the restock.</td><td><b>Pricing &amp; Quotes:</b> writes quotes inside the policy. Customer Service drafts from the approved quote, and Accounting checks the margin.</td></tr>
</table>
<ul><li><b>Same guardrails, bigger playbook:</b> every new tool that moves money or stock gets a human gate and an audit entry, the same as our two approved payments today. Cash accuracy stays 100%, or we don't ship it.</li></ul>{evidence("103", "Cash", "101", note="103's blocked status and the $160 balance are the evidence")}"""

    return f"""<style>{CSS}</style><div class="refl">
<h2>Reflection</h2>
<p class="lede">Five questions, our answers, and the receipts. Every answer ties back to the three tickets the dream team ran on this app and the Campus Customs data. Click an evidence chip to jump to that tab.</p>
{strip}
{qa(1, "How would you evaluate the performance of the agents on each ticket and why?", q1)}
{qa(2, "For each ticket, how did Actual compare to the Expected plan you wrote earlier?", q2)}
{qa(3, "What would have been simpler as one agent with tools — and why?", q3)}
{qa(4, "Describe three new problems Campus Customs might face that this agent team could solve with the tools you built.", q4)}
{qa(5, "Describe three new problems Campus Customs might face that this agent team could not solve with the tools you built, and explain the tools and agents you would need to solve them.", q5)}
</div>"""
