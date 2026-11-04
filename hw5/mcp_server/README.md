# Campus Customs MCP Server

## What this server is for

Campus Customs is run by a team of five AI agents: **Boss**, **Inventory**, **Accounting**, **Facilities** and **Customer Service**. They work the shop's open tickets. To do that, they need real shop facts: what's in stock, what's owed, what rent is due, and how much cash there is. This server is the **one shared toolbox** they all get those facts from.

MCP (Model Context Protocol) is a standard way for an AI agent to call tools. Each tool here is a small, named function. An agent asks it a question, such as "how many size M hoodies do we have?", and gets back an exact answer from the shop database. Putting every agent behind the same server, built with [FastMCP](https://gofastmcp.com) in `server.py`, has four benefits:

- **One source of truth.** Every agent sees the same numbers from the same database, so two agents can't disagree about stock or cash.
- **No invented data.** The agents never write their own database queries and never guess. Each tool returns only database values, or simple arithmetic on them such as a shortfall or days overdue. Anything missing comes back as "not found", never a made-up value.
- **The shop rules live in code.** "Today" is the shop's own date. A vendor with an unpaid invoice is flagged as blocked. Cash is checked before any payment. Each tool enforces these the same way for every agent, so no agent can skip a rule.
- **Safe by design.** Agents can read, file a payment *request*, save a draft and move a ticket's status, and that's all. Only a human, through the approval tools, can pay, and the pay tool refuses rather than letting a balance go below zero. Nothing is ever sent to a customer.

## Which database it uses

**`data/campus_customs_new.db`**, the working copy of the shop database.

- The server refuses to open the original **`data/campus_customs.db`**, which stays untouched so the shop can be reset. To reset, copy `campus_customs.db` over `campus_customs_new.db`.
- The working copy must already exist. The server won't quietly create a blank database.
- "Today" for every tool is the database's `desk.date_today` (2026-08-31), never the computer's clock.

## The tools (25), and why we have them

### The first three (Problem 3), one for each open ticket

- **`check_stock(sku, size, qty_needed)`**: reads `inventory` and `pricing`. **Chosen for ticket 103** (the Yale AI Club wants 20 size M hoodies at a bulk discount). Stock is kept per size, so it looks up the exact size M row, works out the shortfall (8 on hand, 12 short), and returns the $22 cost beside the $58 list price. Inventory can then size the restock and Accounting can test any discount against the margin. It also shows ticket 101's size S tee is at 0.
- **`get_open_invoices(vendor_id, invoice_id)`**: reads `invoices`, `vendors` and `desk`. **Chosen for ticket 101** (Tauhid Zaman needs a size S tee, which is out of stock). It follows the ticket's link to invoice 501. It shows that Bulldog Print Co is owed $840, 3 days overdue by the shop's date, and is therefore **blocked** from shipping a reprint. It also returns the vendor's 5-day lead time, so the agents know the bill must be paid first, with a human's approval.
- **`get_rent_due(lease_id)`**: reads `leases`, `cash_accounts` and `desk`. **Chosen for ticket 102** (Elm City Properties' rent notice). It follows the ticket's link to lease 1: $2,400 due 2026-09-02, 2 days away. In the same call it checks the $3,400 in checking, so Facilities knows the rent can be paid without overdrawing cash before it asks a human to approve the payment. It reads only and pays nothing.

### Added in Problem 5, so the agents can finish the tickets

**The board**
- **`get_ticket(ticket_id)`**: reads `tickets`, `drafts` and `approval_requests`. Boss starts every ticket here.
- **`list_tickets(status)`**: reads `tickets`. The whole board, or one status.
- **`rank_open_tickets()`**: reads `tickets`, `invoices`, `vendors`, `leases`, `inventory`, `pricing`, `cash_accounts` and `desk`. It ranks every open ticket urgent, high, normal or low from database facts, with reasons, deadlines and dependencies, and says whether cash covers every ticket. Any amount over $5,000.00 is automatically at least high.
- **`update_ticket_status(ticket_id, status)`**: writes `tickets.status` (open, in_progress, waiting_approval, blocked or resolved).

**Stock and vendors**
- **`list_inventory(low_only)`**: reads `inventory` and `pricing`. Every SKU and size, its value at cost, and a reorder flag for anything with fewer than 5 units.
- **`list_vendors(specialty_contains)`**: reads `vendors` and `invoices`. Specialty, lead days, and whether an open invoice blocks the vendor.

**Cash and payments**
- **`get_cash_balance()`**: reads `cash_accounts` and `approval_requests`. Cash on hand, and how much of it is already promised to pending requests.
- **`list_payments()`**: reads `payments`. Payments a human has approved and made.
- **`list_payment_requests(status)`**: reads `approval_requests`. What's waiting for a human.
- **`build_balance_sheet()`**: reads `cash_accounts`, `inventory`, `pricing`, `invoices`, `leases` and `approval_requests`. The balance sheet as of `desk.date_today`: cash and inventory at cost, open invoices, and equity as assets minus liabilities, so it always balances. Rent not yet due and pending requests are shown as notes. Every figure the database can't supply, such as fixed assets, receivables and owner's equity detail, is listed under `missing_information`.
- **`build_income_statement(period_start, period_end)`**: reads `payments`. Revenue is $0 because the shop doesn't model it, and that's flagged, not estimated. Expenses are payments actually made, grouped by kind, and pending requests are never counted. Missing figures are listed.
- **`request_payment(kind, ticket_id, ...)`**: writes a **pending** row to `approval_requests`. It **does not pay**. The amount comes from the database (the invoice amount, the lease rent, or qty × unit cost). It refuses a vendor blocked by an open invoice, a duplicate request, or anything the cash can't cover.

**Leases and building requests**
- **`list_leases()`**: reads `leases` and `desk`. Every lease, its rent and days until due.
- **`get_lease(lease_id)`**: reads `leases`, `payments`, `approval_requests` and `building_requests`. One lease in full, with its rent payment history, pending rent requests and building requests. Lease terms the database doesn't hold are listed as missing.
- **`log_building_request(lease_id, issue, priority, requested_by, ticket_id)`**: writes to `building_requests`. Logs a building or maintenance request (priority low, normal or urgent) on the board. No landlord or contractor is contacted.
- **`list_building_requests(status)`**: reads `building_requests`.
- **`update_building_request(request_id, status, note)`**: writes `building_requests.status` (open, in_progress, waiting_approval or done).

**Drafts**
- **`check_spelling_grammar(subject, body)`**: reads `inventory`, `tickets`, `vendors` and `leases` for the shop's own words. Offline spelling dictionary plus grammar rules: repeated words, a/an, capital letters, a lone "i", "could of", spacing, punctuation and brackets.
- **`save_customer_draft(ticket_id, to_name, subject, body, written_by)`**: writes to `drafts`. The message stays on the board, and nothing is ever sent. It refuses any draft that doesn't pass `check_spelling_grammar`.
- **`list_drafts(ticket_id)`**: reads `drafts`.

**Human approval only** (the dashboard; no agent is given these)
- **`approve_and_pay(request_id, approved_by, approval_code)`**: pays one pending request after a person approves it. It needs `HUMAN_APPROVAL_CODE` from `.env`, and refuses if the cash would go below zero. In one transaction it adds a row to `payments` (with `approved_by`), lowers `cash_accounts`, marks the invoice paid or moves the lease's `next_due` forward a month, and marks the request paid.
- **`reject_payment_request(request_id, rejected_by, approval_code, reason)`**: rejects a pending request. No money moves.

`drafts`, `approval_requests` and `building_requests` are board tables the server creates in the working copy the first time they're needed. A reset removes them.

## Run

```bash
python mcp_server/server.py
```

All 25 tools are checked by `python scripts/mcp_tool_check.py`, which runs them on a scratch copy of the database.
