# Campus Customs MCP Server

## What this server is for

Campus Customs is run by a team of five AI agents: **Boss**, **Inventory**, **Accounting**, **Facilities** and **Customer Service**. They work the shop's open tickets. To do that, they need real shop facts: what's in stock, what's owed, what rent is due, and how much cash there is. This server is the **one shared toolbox** they all get those facts from.

MCP (Model Context Protocol) is a standard way for an AI agent to call tools. Each tool here is a small, named function. An agent asks it a question, such as "how many size M hoodies do we have?", and gets back an exact answer from the shop database. Putting every agent behind the same server, built with [FastMCP](https://gofastmcp.com) in `server.py`, has four benefits:

- **One source of truth.** Every agent sees the same numbers from the same database, so two agents can't disagree about stock or cash.
- **No invented data.** The agents never write their own database queries and never guess. Each tool returns only database values, or simple arithmetic on them such as a shortfall or days overdue. Anything missing comes back as "not found", never a made-up value.
- **The shop rules live in code.** "Today" is the shop's own date. A vendor with an unpaid invoice is flagged as blocked. Cash is checked before any payment. Each tool enforces these the same way for every agent, so no agent can skip a rule.
- **Safe by design.** The three tools so far only read; none of them changes the database. Tools that change data, such as payments and customer drafts, come in later problems, and every payment will need a human's approval.

## Which database it uses

**`data/campus_customs_new.db`**, the working copy of the shop database.

- The server refuses to open the original **`data/campus_customs.db`**, which stays untouched so the shop can be reset. To reset, copy `campus_customs.db` over `campus_customs_new.db`.
- The working copy must already exist. The server won't quietly create a blank database.
- "Today" for every tool is the database's `desk.date_today` (2026-08-31), never the computer's clock.

## The three tools, and why we chose them

We chose these three because each one gives the agents what one of the three open tickets needs before anything can be decided.

- **`check_stock(sku, size, qty_needed)`**: reads `inventory` and `pricing`. **Chosen for ticket 103** (the Yale AI Club wants 20 size M hoodies at a bulk discount). Stock is kept per size, so it looks up the exact size M row, works out the shortfall (8 on hand, 12 short), and returns the $22 cost beside the $58 list price. Inventory can then size the restock and Accounting can test any discount against the margin. It also shows ticket 101's size S tee is at 0.
- **`get_open_invoices(vendor_id, invoice_id)`**: reads `invoices`, `vendors` and `desk`. **Chosen for ticket 101** (Tauhid Zaman needs a size S tee, which is out of stock). It follows the ticket's link to invoice 501. It shows that Bulldog Print Co is owed $840, 3 days overdue by the shop's date, and is therefore **blocked** from shipping a reprint. It also returns the vendor's 5-day lead time, so the agents know the bill must be paid first, with a human's approval.
- **`get_rent_due(lease_id)`**: reads `leases`, `cash_accounts` and `desk`. **Chosen for ticket 102** (Elm City Properties' rent notice). It follows the ticket's link to lease 1: $2,400 due 2026-09-02, 2 days away. In the same call it checks the $3,400 in checking, so Facilities knows the rent can be paid without overdrawing cash before it asks a human to approve the payment. It reads only and pays nothing.

## Run (in a later problem)

```bash
python mcp_server/server.py
```
