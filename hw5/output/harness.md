# Harness: Campus Customs Multi-Agent Operations (HW5)

This file explains how the Campus Customs agent team is built and why. It starts with the database (Problem 2) and grows with each later problem.

**Safety first.** These rules hold everywhere in this project:

- Every agent uses only `gpt-6-luna`, through `PORTKEY_API_KEY`.
- Every payment needs a human approval.
- The pay tool refuses rather than letting a balance go negative.
- Nobody emails a real customer or calls a real vendor; drafts stay on the board.
- The agents work only on `data/campus_customs_new.db`.

## Problem 2: Study the Campus Customs database

### The two database files

**Table 1: Database Files**

| File | Role | Touched by agents? |
|---|---|---|
| `data/campus_customs.db` | The original shop database, from `data.zip` | **Never.** It's the clean copy we reset from |
| `data/campus_customs_new.db` | The working copy the MCP server and backend point at | **Yes.** Tools update it as tickets get resolved |

Both files had the same SHA-256 when this harness was written (`23686a90…f360a`), so the working copy starts as an exact copy. A reset means copying the original over the working copy again. SQLite's `integrity_check` returns `ok`.

### Each table, its fields, and why it matters for the agents

All 9 tables are listed below. The key fields are marked **PK**, links to another table are marked **→**, and required fields are marked "required" (NOT NULL). Every row is in `output/data_overview.md`.

**Table 2: Table Fields and Why Each Table Matters**

| Table | Rows | Fields (type) | Why it matters for the agents |
|---|---|---|---|
| `desk` | 1 | `date_today` (text, required), `notes` (text) | The shop's "today" (**2026-08-31**). Every agent judges overdue and due-soon against it, never the computer clock. |
| `tickets` | 3 | `id` (int, PK), `type` (text, required), `requester` (text, required), `subject` (text, required), `sku` (text), `size` (text), `qty` (int), `lease_id` (int → `leases.id`), `invoice_id` (int → `invoices.id`), `status` (text, required), `notes` (text), `created_at` (text, required) | The work board. Boss reads each ticket and routes it by `type`, and the link fields point the other agents to the rows they need. |
| `inventory` | 10 | `sku` (text, PK part), `name` (text, required), `size` (text, PK part), `qty` (int, required), `location` (text, required) | Inventory checks stock by SKU **and** size here, to spot shortfalls. |
| `pricing` | 4 | `sku` (text, PK), `unit_cost` (real, required), `list_price` (real, required) | Accounting uses unit cost and list price to check margins on discounts and the cost of a restock. |
| `vendors` | 3 | `id` (int, PK), `name` (text, required), `specialty` (text, required), `lead_days` (int, required) | Inventory picks a restock vendor by specialty. Lead times **must** come from `lead_days` (shop rule). |
| `leases` | 1 | `id` (int, PK), `space_name` (text, required), `landlord` (text, required), `monthly_rent` (real, required), `next_due` (text, required), `notes` (text) | Facilities' table: what rent is owed, to whom, and when. A paid rent should move `next_due` forward. |
| `cash_accounts` | 1 | `name` (text, PK), `balance` (real, required), `date` (text, required) | Accounting checks cash here before any payment. The pay tool must refuse if the balance would go below zero. |
| `payments` | 0 | `id` (int, PK), `kind` (text, required), `ref_id` (int), `amount` (real, required), `account` (text, required), `paid_at` (text, required), `approved_by` (text, required) | The record of human-approved payments. It starts empty, and `approved_by` is required, so no payment can be recorded without naming its approver. |
| `invoices` | 1 | `id` (int, PK), `vendor_id` (int, required → `vendors.id`), `amount` (real, required), `due_date` (text, required), `status` (text, required), `description` (text) | Accounting tracks unpaid bills here. A vendor with an `open` invoice won't ship new product (shop rule). |

### How the tables link

Three links are declared in the database:

- `tickets.invoice_id → invoices.id`
- `tickets.lease_id → leases.id`
- `invoices.vendor_id → vendors.id`

The other links are by matching values only, with no database link behind them:

- `tickets.sku` matches `inventory.sku` and `pricing.sku`.
- `payments.ref_id` will point to an invoice or a lease, depending on `payments.kind`.
- `payments.account` matches `cash_accounts.name`.

🚩 SQLite doesn't check declared links unless `PRAGMA foreign_keys = ON` is set; it reports `0` (off) by default. Our tools should turn it on, or check the links themselves.

### The three open tickets and how they link

**Table 3: How Each Open Ticket Links to Other Tables**

| Ticket | Type, from | Asks for | Linked rows | What the linked rows show | Agents likely involved |
|---|---|---|---|---|---|
| **101** | `customer_order`, Tauhid Zaman | 1 Classic Bulldog Tee, size S | `inventory` (CC-TEE-WHITE, S) → `invoices` 501 (via `invoice_id`) → `vendors` 1; `pricing` CC-TEE-WHITE | Stock for size S is **0**. Invoice 501 is $840 to Bulldog Print Co (apparel reprint, 5 lead days), for "Rush reprint CC-TEE-WHITE S". It's `open` and was due 2026-08-28, which is **3 days overdue**. The tee costs $8 and lists at $28. | Boss, Inventory, Accounting, Customer Service |
| **102** | `rent_notice`, Elm City Properties | Rent due in 2 days | `leases` 1 (via `lease_id`); `cash_accounts` checking | The Chapel Street shop rent of $2,400 is due 2026-09-02, 2 days after "today". Checking has $3,400. | Boss, Facilities, Accounting |
| **103** | `price_override`, Yale AI Club | 20 Basic Hoodies, size M, with a bulk discount | `inventory` (CC-HOOD-NAVY, M); `pricing` CC-HOOD-NAVY; `vendors` (restock) | Stock for size M is **8**, so 12 short. The hoodie costs $22 and lists at $58, so the margin at list price is $36 a unit (62%). | Boss, Inventory, Accounting, Customer Service |

Ticket 101 is the chain to watch. The tee is out of stock, the only apparel vendor is owed an overdue bill, and that vendor won't ship until the bill is paid. Solving it means paying invoice 501 first, which needs a human approval and enough cash.

### Kept open for later problems

These points aren't decided here. They're listed so later problems pick them up.

**Table 4: Open Items for Later Problems**

| # | Open item | Why it matters | Likely problem |
|---|---|---|---|
| O1 | 🚩 Cash covers both bills only just: $840 + $2,400 = $3,240 of $3,400, which would leave $160. No money comes in. | Paying for a hoodie restock as well (12 × $22 = $264 at unit cost) wouldn't fit after both bills. The order of payments and the human's choice will matter. | Accounting, payments, approvals |
| O2 | Bulldog Print Co is the only apparel vendor. Its specialty is "apparel reprint", which covers tees and probably hoodies. | Both 101 and 103 depend on it, and invoice 501 blocks it until paid. | Inventory restock |
| O3 | No table links a SKU to its vendor. | Inventory has to match on `vendors.specialty`. The tool should say how it chose. | MCP tools |
| O4 | Pricing has no size, and there's no discount rule or floor price in the database. | Accounting needs a stated margin rule for 103's bulk discount, and a human decides. | Accounting, approvals |
| O5 | `payments.kind` and `ref_id` have no fixed values. | We'll define them (for example `invoice` → invoice id, `rent` → lease id) and use them the same way every time. | Pay tool |
| O6 | What a paid bill updates: `invoices.status` → `paid`, `leases.next_due` → next month, `cash_accounts.balance` goes down, and a row is added to `payments`. | The shop rule says to update the relevant table when a payment is made. | Pay tool |
| O7 | `tickets.status` is `open` for all three. | We'll need the list of status values the agents move a ticket through, and drafts must stay on the board. | Board, dashboard |
| O8 | Every full run must start from a fresh copy of the original. | Shop rule: reset before a full run. A reset script makes this one command. | Every full run |
| O9 | `cash_accounts.date` (2026-08-31) should change when cash moves. | It shows when the balance was last updated. | Pay tool |

## Problem 3: Build the MCP server

The server is in `mcp_server/server.py`, built with FastMCP 4.1.6, and it talks only to `data/campus_customs_new.db`. **Every agent in this homework uses these tools.** Each tool returns database values only (or simple arithmetic on them), and anything missing comes back as `found: false` rather than a guess. As the assignment allows, the server wasn't connected or run in this problem; only a syntax check was done.

### The three MCP tools

#### **`check_stock`**
#### **`get_open_invoices`**
#### **`get_rent_due`**

**Table 5: The Three MCP Tools, Tied to Their Tickets**

| Tool | Table(s) it reads | Ticket it unlocks | What it returns, and why it's the right tool for the ticket | Lou's approval |
|---|---|---|---|---|
| **`check_stock`** | `inventory`, `pricing` | **103** (Yale AI Club, 20 hoodies, size M); also 101 | **Returns:** for `check_stock("CC-HOOD-NAVY", "M", 20)`, the 8 size M hoodies on hand in Aisle A, the shortfall of 12 against the 20 requested, and the hoodie's $22 unit cost and $58 list price.<br><br>**Why it's right for 103:** Ticket 103 needs two decisions at once, whether the shop can fill 20 hoodies and how deep a bulk discount can go. `check_stock` fits because it looks up by SKU **and** size (stock is kept per size, so it returns the exact size M row, not the 32-hoodie total), works out the shortfall from the ticket's own quantity, and returns cost beside list price in the same answer. That lets Inventory size the restock and Accounting test any discount against the $36-a-hoodie margin without a second lookup or a guessed number. | ☐ Approve |
| **`get_open_invoices`** | `invoices`, `vendors`, `desk` | **101** (Tauhid Zaman, 1 tee, size S) | **Returns:** for `get_open_invoices(invoice_id=501)`, invoice 501's $840 amount, its 2026-08-28 due date and 3 days overdue (measured from `desk.date_today`), joined to Bulldog Print Co's "apparel reprint" specialty and 5 lead days, plus `blocked_vendor_ids` = [1].<br><br>**Why it's right for 101:** Ticket 101 can't be filled from stock (size S = 0), so the action it needs is a restock. `get_open_invoices` fits because it follows the ticket's `invoice_id` link to the vendor, flags that vendor as blocked under the shop's rule against shipping while a bill is unpaid, uses the shop's date rather than the computer clock to prove the bill is overdue, and takes lead time from `vendors`. So the agents know the bill must be paid first, exactly how much a human must approve, and how long the tee takes after that. | ☐ Approve |
| **`get_rent_due`** | `leases`, `cash_accounts`, `desk` | **102** (Elm City Properties rent notice) | **Returns:** for `get_rent_due(1)`, the Chapel Street shop's $2,400 rent to Elm City Properties, due 2026-09-02 (2 days after `desk.date_today`, so not yet late), the $3,400 checking balance, and $1,000 left after rent (before invoice 501 is paid).<br><br>**Why it's right for 102:** Ticket 102 needs the rent paid on time without overdrawing cash. `get_rent_due` fits because it follows the ticket's `lease_id` to the exact amount and landlord, counts days from the shop's own date so Facilities knows the rent is due soon but not overdue, and checks cash in the same call, so the shop's no-negative-balance rule is tested before a payment ever reaches a human for approval. The tool itself stays read-only and pays nothing. | ☐ Approve |

### How the tools follow the shop rules

**Table 6: Shop Rules Built Into the Problem 3 Tools**

| Rule | How the tools handle it |
|---|---|
| Never invent data | Values come only from the database; a missing SKU, size, lease or price returns `found: false` with a message |
| "Today" is `desk.date_today` | `get_open_invoices` and `get_rent_due` measure days from `desk.date_today`, never the computer clock |
| Vendor lead times come from `vendors` | `get_open_invoices` returns `vendors.lead_days` |
| A vendor with an open invoice won't ship | `get_open_invoices` returns `blocked_vendor_ids` |
| Human approval for payments, no negative balances | These tools only read and pay nothing. `get_rent_due` reports `cash_after_rent` so a shortfall shows up before any payment step |
| Working copy only; original untouched | `connect()` refuses `campus_customs.db` and opens `campus_customs_new.db` in `mode=rw`, so it can't silently create a blank file |
| Declared links checked | `connect()` turns on `PRAGMA foreign_keys` (harness 🚩 from Problem 2) |
