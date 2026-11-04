# AI Prompts Log: Campus Customs Multi-Agent Operations (HW5)

This is the log of what I typed to my vibe coder (Claude Code) while building Campus Customs Multi-Agent Operations. There is one section per problem. Each section has:

- the problem number and title
- my main prompt, in my own words
- a follow-up prompt where I needed one, plus one sentence on what was lacking after the first
- the outcome

Prompts are quoted exactly as I typed them, typos included. Setup prompts I typed before Problem 1 are in the appendix, so the full conversation is visible.

**Assignment:** Campus Customs Multi-Agent Operations is the agentic team that runs the shop. Open tickets land on a board: customer orders, rent, unpaid bills, discount requests. We build three pieces that talk to each other: an **MCP server**, a **FastAPI backend** with a multi-agent team, and a **React dashboard** where a person can watch the agents work and approve requests. The team has full connectivity, so any agent can delegate to any other:

- **Boss** reads each ticket, decides who works on it, and makes the final calls.
- **Inventory** checks stock by SKU and size, spots shortfalls, and finds which vendor can restock.
- **Accounting** watches cash and invoices, checks margins, and prepares payments or purchase orders for human approval.
- **Facilities** handles the shop space: leases and rent.
- **Customer Service** drafts messages for customers.

Every AI call uses `gpt-6-luna` through `PORTKEY_API_KEY`. Every payment needs a human approval. Nobody really emails a customer or calls a vendor. The tools work on `data/campus_customs_new.db`, and `data/campus_customs.db` stays untouched for resets. The finished project goes in a public GitHub repo, without `.env`.

## At a glance

**Table 1: Problems at a Glance**

| # | Problem | Main prompt was about | Follow-up fixed | Main output |
|---|---|---|---|---|
| | | | | |

---

## Appendix: Setup prompts (before Problem 1)

**Prompt 1:**

> let's start hw 5

**Prompt 2 (with three attachments):**

> yo- here is the into to HW5.  pls read all set up instructions.  open the zip and let me know what is in it.  make sure all tables and files are included.  open a sample file for me in the right panel, here.  pay special attention to the agents that we will create.  always remember all the rules, and only use gpt-6-luna.  let me know if you have any questions

**Attachments sent with Prompt 2:**

**Table 2: Prompt 2 Attachments**

| # | Attachment | What it contains |
|---|---|---|
| 1 | Screenshot: "Homework 5: Campus Customs Multi-Agent Operations", **Scenario** | The shop's agentic team works an open ticket board (customer orders, rent, unpaid bills, discount requests). We build three connected pieces: an MCP server, a FastAPI backend with a multi-agent team, and a React dashboard where a person watches the agents and approves requests. The team has full connectivity. The agents are **Boss** (reads each ticket, decides who works on it, makes final calls), **Inventory** (stock by SKU and size, shortfalls, which vendor can restock), **Accounting** (cash, invoices, margins, payments and purchase orders for human approval), **Facilities** (leases and rent) and **Customer Service** (drafts messages for customers). |
| 2 | Screenshot: **Data** and **Rules of this shop** | **Data:** unzip `data.zip` to get `data/campus_customs.db` (tables `desk`, `tickets`, `inventory`, `pricing`, `vendors`, `leases`, `cash_accounts`, `payments`, `invoices`). Copy it to `data/campus_customs_new.db`, point the MCP server and backend at the copy, and keep the original untouched for resets. **Rules:** `desk.date_today` is "today" and decides what's overdue. Vendor lead times come from `vendors`. A vendor won't ship new product while it has an open unpaid invoice. Human approval is required for any payment (points deducted otherwise), and an approved payment must update the relevant table. If there isn't enough cash, the pay tool must refuse, with no negative balances. Cash only goes out. Reset the database before a full run. Don't email customers or call real vendors; drafts stay on the board. Use `PORTKEY_API_KEY` and **only** `gpt-6-luna` through Portkey for every agent (points deducted for any other model). Work one problem at a time in your own words, and submit a public GitHub repo. |
| 3 | Data file: `data (3).zip` (the course's `data.zip`) | One file, `data/campus_customs.db` (SQLite, 53,248 bytes), with all 9 tables. Every row is in `output/data_overview.md`. |

**Outcome:**

- Unzipped `data.zip` into `hw5/data/`. It holds one file, `campus_customs.db`, with all 9 required tables: `desk`, `tickets`, `inventory`, `pricing`, `vendors`, `leases`, `cash_accounts`, `payments`, `invoices`.
- Made the working copy `data/campus_customs_new.db`. Its SHA-256 matches the original, so it's byte-for-byte identical.
- Wrote `output/data_overview.md`, a readable copy of every table and row, with notes on how the shop rules show up in the data.

**Prompt 3:**

> start the prompt log now and set everything up for a github push to the repo, and we'll do this as we've done the other homework, going for a grade of 100/100.

**Outcome:**

- Started this log.
- Set up the repo the same way as HW6: a git repo at `HW5/` with the project in `hw5/`, plus `.gitignore` (keeps `.env`, `.venv/`, caches and zips out), `.gitattributes` (stores the `.db` files as binary so git can't corrupt them), `.env.example` (variable names only), a root `README.md`, and `EVIDENCE_CHECKLIST.md`.
- Nothing has been pushed yet. The GitHub repo gets created and pushed in the last problem, as in HW6.

**Prompt 4:**

> and include the first prompt with the attachments and the data file in the prompt log.  ty

**Outcome:** added the attachments under Prompt 2 (Table 2): the two instruction screenshots, summarized, and the data file.

**Prompt 5 (answering whether to commit the database files to the public repo):**

> Commit original only

**Outcome:**

- `campus_customs.db` is committed so graders have the original data.
- `campus_customs_new.db` is in `.gitignore`. It changes on every run, and graders make their own copy from the original.
- Made the first local commit. Nothing has been pushed.
