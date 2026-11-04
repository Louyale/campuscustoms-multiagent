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
| 1 | Vibe coder prompts | Finish setting up this log, one section per problem number and title, kept updated | Label the Problem 1 tasks for the grader (Table 3), separate from the earlier setup | `AI_prompts.md`, `EVIDENCE_CHECKLIST.md` |
| 2 | Study the Campus Customs database | Label and log the parts done during setup; study the rest; keep open what later problems need | (none needed) | `output/harness.md`, `output/data_overview.md`, `data/campus_customs_new.db` |

---

## Problem 1: Vibe coder prompts

**Prompt (my own words, with screenshots of Panels A and B):**

> we've already started problem 1, but here it is - pls perform any outstanding set up tasks, and we'll move to problem 2 after you confirm.

**Follow-up prompt:**

> and label the set up tasks that are itemized as problem 1 for the grader, the other set up tasks we did can stay on before problem 1

**What was lacking after the first:** the Problem 1 tasks were done, but they weren't itemized and labeled as Problem 1 for the grader, apart from the earlier setup work.

**Outcome:** each Problem 1 task is done. Table 3 lists them for the grader. The other setup tasks (unzipping the data, the working database copy, the data overview and the repo files) came before Problem 1 and are in the appendix.

**Table 3: Problem 1 Setup Tasks**

| Task | Panel | What was asked | Where it's done |
|---|---|---|---|
| P1-1 | A | Create `AI_prompts.md` at the start of the assignment | This file, created with my first HW5 prompt (appendix, Prompt 2) |
| P1-2 | A | Keep it updated as I work: the log of what I typed | Updated after every prompt, quoted exactly, typos included |
| P1-3 | A | Describe each problem to the vibe coder in my own words | Each problem section quotes my own-words prompt; I don't paste the page or the URL |
| P1-4 | B | One section per problem, with the problem number and title | `## Problem N: <title>` headings, plus Table 1: Problems at a Glance |
| P1-5 | B | At least one prompt I typed, in my own words | The "Prompt (my own words)" line in each section |
| P1-6 | B | One follow-up prompt if needed, plus one sentence on what was lacking after the first | The "Follow-up prompt" line in each section ("none needed" when there wasn't one) |
| P1-7 | (extra) | Proof each problem's evidence exists before grading | `EVIDENCE_CHECKLIST.md` |

**Confirmation:**

> that label is fine, yes.

I approved the Table 3 name as it is.

---

## Problem 2: Study the Campus Customs database

**Prompt (my own words, with screenshots of Panels A and B):**

> here are the instructions for problem 2.  we already did some of this as well, but label them and log them as we did with problem 1.  then study the remainder and keep open what will be needed for subsequent problems.

**Follow-up prompt:** none needed.

**Outcome:** each Problem 2 task is done. Table 4 lists them for the grader and marks which were done during setup.

**Table 4: Problem 2 Tasks**

| Task | Panel | What was asked | When | Where it's done |
|---|---|---|---|---|
| P2-1 | A | Open `data/campus_customs.db` and look through every table and its fields | Setup, then rechecked | `output/data_overview.md` (every row). Rechecked: all 9 tables, field types, required fields, keys and links, and `integrity_check` = ok |
| P2-2 | A | Copy the original to `data/campus_customs_new.db`, the working copy later problems update | Setup | The copy's SHA-256 matches the original (`23686a90…f360a`), rechecked for this problem |
| P2-3 | A | Study the three open tickets and how they link to other tables | Problem 2 | `output/harness.md`, Table 3: How Each Open Ticket Links to Other Tables |
| P2-4 | B | Start `output/harness.md` | Problem 2 | `output/harness.md` |
| P2-5 | B | For each table, list the fields and one short line on why it matters for the agents | Problem 2 | `output/harness.md`, Table 2: Table Fields and Why Each Table Matters |
| P2-6 | B | Keep growing the harness in later problems | Ongoing | Each later problem adds its own section |
| P2-7 | (extra) | Keep open what later problems will need | Problem 2 | `output/harness.md`, Table 4: Open Items for Later Problems (O1–O9) |

**Confirmation:**

> yes as to all titles

I approved all the Problem 2 table names as they are: harness Tables 1–4 and this log's Table 4.

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

## Appendix: Rule reminders (between problems)

**Reminder 1 (after Problem 2, with a screenshot of the shop rule "Do not email customers or call real vendors. Drafts stay on the board"):**

> always remember to follow all rules inc this one

**Outcome:**

- Saved as a standing rule. No agent gets a real email, text or phone tool, and no mail connector is wired in.
- Customer Service and the other agents only write drafts, which stay on the board.
- The full shop rule list gets re-read before each problem and each full run.
