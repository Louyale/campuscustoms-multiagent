# Campus Customs MCP Server

**What it's for:** this is the one place the Campus Customs agent team gets its shop data. Every agent uses these tools to look things up, instead of guessing: **Boss**, **Inventory**, **Accounting**, **Facilities** and **Customer Service**. The server is built with [FastMCP](https://gofastmcp.com) in `server.py`. Every answer comes straight from the database, and nothing is invented.

**Which database it uses:** `data/campus_customs_new.db`, the working copy. The server refuses to open the original `data/campus_customs.db`, which stays untouched so the shop can be reset. To reset, copy `campus_customs.db` over `campus_customs_new.db`. "Today" is always the database's `desk.date_today` (2026-08-31), never the computer clock.

## The three tools

**Table 1: MCP Server Tools**

| Tool | What it returns | Tables it reads | Ticket it unlocks |
|---|---|---|---|
| `check_stock(sku, size, qty_needed)` | On-hand quantity and location for one SKU and size, the unit cost and list price, and the shortfall against the quantity needed | `inventory`, `pricing` | **103**: 20 hoodies, size M (also 101: tee, size S) |
| `get_open_invoices(vendor_id, invoice_id)` | Unpaid invoices with the vendor's name, specialty and lead days, days overdue, and which vendors are blocked from shipping | `invoices`, `vendors`, `desk` | **101**: invoice 501 blocks the tee reprint |
| `get_rent_due(lease_id)` | A lease's rent, landlord and next due date, days until due, and whether cash on hand covers it | `leases`, `cash_accounts`, `desk` | **102**: Chapel Street rent |

All three tools only read; none of them changes the database. Tools that write, such as payments and customer drafts, come in later problems, and every payment will need a human's approval.

## Run (in a later problem)

```bash
python mcp_server/server.py
```
