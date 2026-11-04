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
| 3 | Build the MCP server | FastMCP server on `campus_customs_new.db`, not run; three ticket-specific tools with no invented data; bold tool names and a harness table with the table read, ticket and a why-sentence; a short `mcp_server/README.md`; show me the sentences and README to review | Say what each tool returns; explain why the tool's qualities fit the ticket's actions; an approve box per tool | `mcp_server/server.py`, `mcp_server/README.md`, `requirements.txt`, `output/harness.md` (Tables 5–6) |
| 4 | Add the MCP server to vibe coder and test each tool | Add the server to this project in `.mcp.json`; test all three tools; a Tool Test Evidence table with the prompt, tool name and output; outputs must match the database | Sign in to the command-line copy of Claude Code, then pick up and confirm nothing was lost | `.mcp.json`, `scripts/mcp_smoke.py`, `output/mcp_smoke.json`, `output/harness.md` (Table 7) |

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

## Problem 3: Build the MCP server

**Prompt (my own words, with screenshots of Panels A and B):**

> here are the contents for problem 3.  follow the instructions to build the mcp server using FastMCP so it talks to the campus customs new.db as noted and do not run it in this problem.  all agents use these tools.  now, write 3 tools you know we'll need for the tickets in the data base and do not invent data.  keep the names clear and put them in bold and larger font and list them in harness.  make a table for the 3 tools and include the requested information.  be sure to add the sentence for why it is the right tool for the ticket and show me the 3 sentences here so i can do what i usually do and amend if needed.  tie the tool to the specific ticket and do not use vague descriptions make the description ticket specific.  last add a readme file that explains what the mcp server is for, which database file it uses and the three tools it has - show me that here too so i can also review and amend if needed.

**Follow-up prompt:**

> first for the tools, the first description title should say what it returns and why it is the right tools for the ticket, and you need to do a better job describing why the tools qualities were the right qualities to take the actions that ticket needed, make those revisions and give me an approve box under each of the 3 in the table

**What was lacking after the first:** the why-sentences named what each tool reads but didn't explain which of the tool's qualities (lookup by SKU and size, following the ticket's link, the shop's date, the vendor-blocked flag, the same-call cash check) fit the action each ticket needs. The column also didn't say what each tool returns.

**Outcome of the follow-up:** harness Table 5's column is now "What it returns, and why it's the right tool for the ticket", with a **Returns** line and a deeper **Why** line for each tool. A "Lou's approval" box (☐ Approve) was added for each of the three tools.

**Approval:** I approved all three revised tool entries (`check_stock`, `get_open_invoices`, `get_rent_due`), and each box in Table 5 now reads ☑ Approved by Lou.

**Follow-up prompt 2 (the README):**

> I'll send edits

> please paste the readme here, and before you do, pls do a better job explaining what the server is for and note the database file it uses, and then list the 3 tools as bullets and why we chose them

**What was lacking after the first:** the README said what the server does in one line, but not why the agent team needs a shared MCP server. It also showed the tools as a table, with no reason we chose each one.

**Outcome:** `mcp_server/README.md` was rewritten. It now has:

- a "What this server is for" section: one shared toolbox, one source of truth, no invented data, the shop rules in code, safe by design
- a "Which database it uses" section naming `data/campus_customs_new.db`
- the three tools as bullets, each with why we chose it for its ticket

**Approval:**

> Approve README

I approved the rewritten README. Problem 3 is complete.

**Outcome:** each Problem 3 task is done. Table 5 lists them for the grader.

**Table 5: Problem 3 Tasks**

| Task | Panel | What was asked | Where it's done |
|---|---|---|---|
| P3-1 | A | Write an MCP server in `mcp_server/` using FastMCP | `mcp_server/server.py` (FastMCP 4.1.6, pinned in `requirements.txt`) |
| P3-2 | A | It talks to `data/campus_customs_new.db` | `DB_PATH` in `server.py`; `connect()` refuses the original and won't create a blank file |
| P3-3 | A | Don't connect or run it in this problem | Not run. Only a syntax check (`py_compile`) and an install of FastMCP to confirm its API |
| P3-4 | A | Every agent uses these tools; write three you know the tickets need | `check_stock` (103, also 101), `get_open_invoices` (101), `get_rent_due` (102) |
| P3-5 | A | Keep the names clear; never invent data | Plain verb names; values only from the database, with `found: false` when missing |
| P3-6 | B | In `output/harness.md`, list each tool with the table it reads, the ticket it unlocks, and one sentence on why it's the right tool, tied to the ticket | `output/harness.md`, Table 5: The Three MCP Tools, Tied to Their Tickets (names in bold, larger font) |
| P3-7 | B | Add a short `mcp_server/README.md`: what it's for, which database it uses, the three tools | `mcp_server/README.md` (purpose, database file, three tool bullets with why we chose each; approved by me) |
| P3-8 | (extra) | Show how the tools follow the shop rules | `output/harness.md`, Table 6: Shop Rules Built Into the Problem 3 Tools |

---

## Problem 4: Add the MCP server to vibe coder and test each tool

**Prompt (my own words, with screenshots of Panels A and B):**

> k, now for problem 4, use this vibe coder to add the mcp server to this project, follow all instructions attached and test all three tools.  create a table titled Tool Test Evidence, and for each tool list the requisite three pieces of information, and make sure the tool output matches the values in the data/campus_customs_new.db

**Follow-up prompt (after the sign-in pause):**

> are we now logged back in?

> pls pick up where you left off.  not sure why that happened, but confirm nothing was lost or overlooked?

**What was lacking after the first:** the tool tests couldn't run yet. The command-line copy of Claude Code needed a one-time sign-in, so I signed in and asked to confirm the work picked up without losing anything.

**Outcome:** each Problem 4 task is done. Table 6 lists them for the grader.

**Table 6: Problem 4 Tasks**

| Task | Panel | What was asked | Where it's done |
|---|---|---|---|
| P4-1 | A | Add the MCP server to **this project** in the vibe coder, so it can call the tools | `.mcp.json` at the project root (`hw5/`); Claude Code's startup check reported `campus-customs: connected`, with all three tools listed |
| P4-2 | A | Save the connection JSON in `.mcp.json` at the project root | `hw5/.mcp.json` (shown in `output/harness.md`, Problem 4) |
| P4-3 | B | With the vibe coder connected, test **each** of the three tools | `scripts/mcp_smoke.py`: Claude Code called `check_stock`, `get_open_invoices` and `get_rent_due` over MCP |
| P4-4 | B | Save the evidence in `output/mcp_smoke.json`: the prompt, the tool name, and the tool output for each tool | `output/mcp_smoke.json` (`prompt`, `tool_name`, `tool_output`, plus the arguments and the vibe coder's reply) |
| P4-5 | B | The tool output must match values in `data/campus_customs_new.db` | 42 of 42 values match, field by field, checked by direct SQL (`database_check` in the JSON) |
| P4-6 | (mine) | A table titled **Tool Test Evidence** with the three pieces of information for each tool | `output/harness.md`, Table 7: Tool Test Evidence |
| P4-7 | (extra) | Keep the no-email rule safe while testing | Only `campus-customs` loaded; the parent folder's `outlook-mail` server was excluded; one allowed tool per test |
| P4-8 | (extra) | Prove the tools didn't change the data | The working database's SHA-256 was the same before and after (`database_unchanged: true`) |

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
