# HW5 Data Overview: `data/campus_customs.db`

This overview was read straight from the database, with every row shown. `data.zip` holds a single file, `data/campus_customs.db` (53,248 bytes, SQLite). All 9 tables the assignment names are present, and there are no extra tables.

- **Original:** `data/campus_customs.db`. Keep it untouched so we can reset.
- **Working copy:** `data/campus_customs_new.db`. The MCP server and backend will point here.
- **Byte check:** both files have SHA-256 `23686a90…f360a`, so the copy is identical.

**Table 1: Database Tables and Row Counts**

| Table | Rows | What it holds |
|---|---|---|
| `desk` | 1 | "Today" for the shop: `date_today` = **2026-08-31** |
| `tickets` | 3 | The open board: one order, one rent notice, one discount request |
| `inventory` | 10 | Stock by SKU and size, plus aisle location |
| `pricing` | 4 | Unit cost and list price per SKU |
| `vendors` | 3 | Vendor name, specialty, and lead days |
| `leases` | 1 | The shop space, landlord, rent, and next due date |
| `cash_accounts` | 1 | Cash on hand: checking **$3,400.00** |
| `payments` | 0 | Empty. Rows get added here only when a human-approved payment is made |
| `invoices` | 1 | Unpaid vendor bills |

## Every row

**Table 2: desk**

| date_today | notes |
|---|---|
| 2026-08-31 | (none) |

**Table 3: tickets**

| id | type | requester | subject | sku | size | qty | lease_id | invoice_id | status | notes | created_at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 101 | customer_order | Tauhid Zaman | Bulldog tee | CC-TEE-WHITE | S | 1 | | 501 | open | Needs a tee in size S. | 2026-08-31 09:15 |
| 102 | rent_notice | Elm City Properties | Rent due | | | | 1 | | open | Email: shop rent due in 2 days. | 2026-08-31 11:05 |
| 103 | price_override | Yale AI Club | Bulk hoodie discount | CC-HOOD-NAVY | M | 20 | | | open | Student org wants 20 hoodies, size M, asking for a bulk discount. | 2026-08-31 16:55 |

**Table 4: inventory**

| sku | name | size | qty | location |
|---|---|---|---|---|
| CC-HOOD-NAVY | Basic Hoodie Big Yale | S | 4 | Aisle A |
| CC-HOOD-NAVY | Basic Hoodie Big Yale | M | 8 | Aisle A |
| CC-HOOD-NAVY | Basic Hoodie Big Yale | L | 14 | Aisle A |
| CC-HOOD-NAVY | Basic Hoodie Big Yale | XL | 6 | Aisle A |
| CC-TEE-WHITE | Classic Bulldog Tee | S | **0** | Aisle B |
| CC-TEE-WHITE | Classic Bulldog Tee | M | 5 | Aisle B |
| CC-TEE-WHITE | Classic Bulldog Tee | L | 3 | Aisle B |
| CC-TEE-WHITE | Classic Bulldog Tee | XL | 2 | Aisle B |
| CC-HAT-BLUE | Yale Cap | OS | 40 | Aisle C |
| CC-MUG-CREST | Crest Mug | OS | **0** | Aisle D |

**Table 5: pricing**

| sku | unit_cost | list_price |
|---|---|---|
| CC-HOOD-NAVY | $22.00 | $58.00 |
| CC-TEE-WHITE | $8.00 | $28.00 |
| CC-HAT-BLUE | $6.00 | $22.00 |
| CC-MUG-CREST | $3.50 | $14.00 |

**Table 6: vendors**

| id | name | specialty | lead_days |
|---|---|---|---|
| 1 | Bulldog Print Co | apparel reprint | 5 |
| 2 | Elm City Gifts | mugs and small goods | 3 |
| 3 | QuickShip CT | local courier | 1 |

**Table 7: leases**

| id | space_name | landlord | monthly_rent | next_due | notes |
|---|---|---|---|---|---|
| 1 | Chapel Street shop | Elm City Properties | $2,400.00 | 2026-09-02 | (none) |

**Table 8: cash_accounts**

| name | balance | date |
|---|---|---|
| checking | $3,400.00 | 2026-08-31 |

**Table 9: invoices**

| id | vendor_id | amount | due_date | status | description |
|---|---|---|---|---|---|
| 501 | 1 (Bulldog Print Co) | $840.00 | 2026-08-28 | open | Rush reprint CC-TEE-WHITE S |

**Table 10: payments** has no rows. Its columns are `id, kind, ref_id, amount, account, paid_at, approved_by`. The `approved_by` column is required (NOT NULL), so every payment must name the human who approved it.

## How the shop rules show up in this data

These are observations only, not solutions. We'll solve the tickets when the problems ask.

- 🚩 **Invoice 501 is overdue.** It was due 2026-08-28, three days before "today". It belongs to Bulldog Print Co, the only apparel vendor, so that vendor won't ship new tees until it's paid. Ticket 101 needs a size S tee, which has **0** in stock, and it's linked to invoice 501.
- **Rent is due in 2 days** (2026-09-02, $2,400).
- 🚩 **Cash is tight.** Checking has $3,400, and invoice 501 plus rent comes to $3,240, which would leave $160. Payments need human approval and can never take the balance below zero, and no money comes in.
- **Ticket 103 is short.** It asks for 20 hoodies in size M, but only 8 are in stock. The hoodie costs $22 and lists at $58, so Accounting will have to check margins on the discount request.
- **No vendor clearly makes hoodies.** Bulldog Print Co's specialty is "apparel reprint", which probably covers them. We'll confirm when Inventory looks for a restock vendor.
- The `payments` table is empty and `approved_by` is required, which matches the rule that a payment needs a human approval and must update the table.
