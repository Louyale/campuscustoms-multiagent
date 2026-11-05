# Evidence Checklist (HW5)

This file lists the evidence each problem needs. Each problem's evidence is added when that problem arrives and checked off once it exists. Before grading, every box should be ticked.

## Every problem
- [ ] A `## Problem N: <title>` section in `AI_prompts.md` with at least one prompt in my own words
- [ ] A follow-up prompt, if one was needed, plus one sentence on what was lacking after the first
- [ ] A row in the "At a glance" table

## Project-wide rules
- [ ] Only `gpt-6-luna` appears in the code and in run logs, for every agent
- [ ] Every AI call goes through `PORTKEY_API_KEY`
- [ ] Every payment needs a human approval in the dashboard, and an approved payment updates the database (`payments`, `cash_accounts`, `invoices` or `leases`)
- [ ] The pay tool refuses when there isn't enough cash, so balances never go negative
- [ ] Cash only goes out; no revenue is modeled
- [ ] No real customer emails or vendor calls: drafts stay on the board
- [ ] The tools and backend use `data/campus_customs_new.db`; `data/campus_customs.db` stays untouched (SHA-256 `23686a90…f360a`)
- [ ] The database is reset to the original before every full run
- [ ] Overdue is judged by `desk.date_today`, and lead times come from `vendors`
- [ ] A vendor with an open unpaid invoice isn't asked to ship new product
- [ ] `.env` is not committed (`.gitignore`), and `.env.example` holds placeholders only
- [ ] Public GitHub repo, with the file tree shown in the last problem
- [ ] `README.md` has the setup and run steps for the grader

## Setup (before Problem 1)
- [x] `data.zip` unzipped: `data/campus_customs.db` with all 9 tables (`output/data_overview.md`)
- [x] Working copy `data/campus_customs_new.db` made (byte-identical)
- [x] `AI_prompts.md` started, with the setup prompts in the appendix
- [x] Repo set up: `git init`, `.gitignore`, `.gitattributes`, `.env.example`, `README.md`
- [x] Only the original `campus_customs.db` is committed; the working copy `campus_customs_new.db` is in `.gitignore` (my choice)

## Problem 1: Vibe coder prompts (5 points)
- [x] `AI_prompts.md` created at the start of the assignment and kept up to date
- [x] One section per problem with its number and title (to be checked again at the end for every problem)
- [x] Each section has my own-words prompt, a follow-up if needed with one sentence on what was lacking, and the outcome

## Problem 2: Study the Campus Customs database (8 points)
- [x] Every table and its fields looked through (`output/data_overview.md`; harness Table 2)
- [x] Original copied to `data/campus_customs_new.db`, the working copy (SHA-256 matches)
- [x] The three open tickets studied, with how they link to other tables (harness Table 3)
- [x] `output/harness.md` started, with each table's fields and one line on why it matters for the agents (harness Table 2)
- [x] Open items kept for later problems (harness Table 4, O1–O9)

## Problem 3: Build the MCP server (12 points)
- [x] MCP server in `mcp_server/` using FastMCP (`server.py`, FastMCP 4.1.6 pinned in `requirements.txt`)
- [x] Talks to `data/campus_customs_new.db` (the original is refused)
- [x] Not connected or run in this problem (syntax check only)
- [x] Three tools the tickets need, with clear names: `check_stock`, `get_open_invoices`, `get_rent_due`
- [x] No invented data: database values only, `found: false` when missing
- [x] `output/harness.md`: each tool's table, ticket (101 / 102 / 103), and a ticket-specific why-sentence (Table 5)
- [x] `mcp_server/README.md`: what the server is for, which database file, the three tools
- [x] My review of the three tool sentences (all three approved in harness Table 5)
- [x] My review of `mcp_server/README.md` (approved)

## Problem 4: Add the MCP server to vibe coder and test each tool (8 points)
- [x] MCP server added to this project for the vibe coder (Claude Code: `campus-customs: connected`, all three tools listed)
- [x] Connection JSON saved in `.mcp.json` at the project root
- [x] Each of the three tools tested with the vibe coder connected
- [x] `output/mcp_smoke.json` has, for every tool, the prompt, the tool name, and the tool output
- [x] Tool output matches `data/campus_customs_new.db` (42 of 42 values, by direct SQL)
- [x] Tool Test Evidence table (harness Table 7)

## Problem 5: Build the agent team and grow the MCP tools (15 points)
### 5a: the agent team (Panel A)
- [x] Five PydanticAI agents: Boss, Inventory, Accounting, Facilities, Customer Service (`backend/agents/`)
- [x] Prompts, models and agent loops, with delegation between all agents (full connectivity: `ask_teammate`)
- [x] Prompts in `backend/prompts/`, one file per agent
- [x] Data types in `backend/models.py` (harness Table 10, including `FinancialStatement`)
- [x] Agent files under `backend/`, with the five roles clear (harness Table 8)
- [x] `PORTKEY_API_KEY` and only `gpt-6-luna` for every agent (`backend/config.py`)
- [x] Each prompt in our own words, with the shop rules that agent needs, and detailed on work and scope
- [x] My approval of each of the five prompts (all five ☑ in `output/agent_prompts_review.md`)

### 5b: grow the MCP tools (Panel B)
- [x] MCP tools added so the agents can work all three open tickets (25 tools; harness Table 12)
- [x] Shop facts only from the MCP server over `campus_customs_new.db`; no second tools layer
- [x] Agents append to `output/audit_trail.json` at every agent-loop step, never wiping it (`backend/audit.py`)
- [x] Harness: each agent and each MCP tool, with the table each tool uses (Tables 11–12), rolled up by agent in Table 13
- [x] Harness: safety section with guardrails for real customers and money, and token limits (Tables 20–21)
- [x] `mcp_server/README.md` tool list matches the server (25 tools)
- [x] Every tool tested on a scratch database copy (43 of 43 checks, 25 of 25 tools; `output/mcp_tool_check.json`)
- [x] My approval of each agent's tool list (all five ☑ in harness Table 11, Boss's after the priority change)
- [x] Boss prioritizes: `rank_open_tickets`, priority on every assignment, top-down follow-up, the $5,000 rule (harness Table 15)
- [x] First audit trail entries from a real agent run (ticket 102: 53 entries, 4 agents, nothing paid; harness Table 16)
- [x] Database reset before and after each test run (`scripts/reset_db.py`)
- [x] Second live run with priorities (harness Table 16, run 2), and token use against the limits (harness Table 17)
- [x] The vibe coder can't reach the human-only pay tools (`CAMPUS_MCP_PROFILE=vibe_coder` in `.mcp.json`)
- [x] Every prompt treats outside text as data, never as instructions
- [x] Dollar cost per ticket and per month, and cost compared with the work done (harness Tables 17–19; `scripts/cost_report.py`)
- [x] Boss's listed approvals are checked against the board by code (`DecisionCheck`; run 4: 1 of 1)
- [x] **Part 5b closed out**

## Problem 6: Plan the three tickets (8 points)
- [x] `output/desk_tickets.html` opens by double-click, with one tab per ticket (101, 102, 103)
- [x] Empty Cash and Reflection tabs, with a "coming later" note
- [x] Each ticket tab has an Expected section, with room for an Actual section
- [x] Expected: who Boss calls first, and why
- [x] Expected: every delegation, in order (not "Boss calls everyone"), with the agents not called and why
- [x] Expected: the MCP tools we expect the run to use
- [x] Not every specialist on every ticket (page Table 1)
- [x] My review and approval of the three plans (all three approved)

## Problem 7: Backend routes (7 points)
- [x] `backend/main.py` uses FastAPI
- [x] Route: the three tickets, each open or resolved (`GET /tickets`)
- [x] Route: run the agent team on a ticket id (`POST /tickets/{id}/run`, `GET /runs/{id}`)
- [x] Route: recent agent events, what each said and which tools it used (`GET /events`)
- [x] Route: human approval pays and changes cash; agents only prepare (`POST /approvals/{id}/approve`)
- [x] Route: the checking balance from `cash_accounts` (`GET /cash`)
- [x] Route: reset the database to the original values (`POST /reset`)
- [x] Starts with `uvicorn main:app --reload --port 8000` from `backend/`
- [x] `output/harness.md` lists each route in one line (Table 22), tied to the assignment bullets and dashboard panels
- [x] Repeatable route test: `scripts/route_check.py`, 21 of 21 steps (harness Tables 24–25; `output/route_check.json`)
- [x] Token savers: re-run guard, `POST /board/run`, `/events?run_id=`, one shared MCP connection (harness Table 23)
- [x] Server stopped after testing, and the database reset to the original
- [x] Board status always matches Boss's decision (status sync; route check step 19)
- [x] Results laid out by the assignment's bullets (harness Table 26): all met

## Problem 8: Agent dashboard (12 points)
- [x] `frontend/` built with React + Vite + TypeScript, calling the Problem 7 routes
- [x] Lists all three tickets
- [x] Pick one ticket and start the agent team on it
- [x] Shows each agent and what it's saying or doing while the ticket runs
- [x] Marks a ticket resolved when the run finishes
- [x] Shows a short summary of what each agent did on the ticket
- [x] A human can approve a pay or purchase
- [x] Shows the checking balance, which drops after an approved pay ($3,400 → $1,000 → $160)
- [x] The front end talks to `http://localhost:8000`; the backend allows `http://localhost:5173`
- [x] Starts with `npm run dev`; `npm run build` compiles cleanly
- [x] `output/design.md`: layout, how agents read differently, resolved tickets and cash, creative choices
- [x] Designed to look good: modeled on my office desk, in Yale blue and white (`output/dashboard_screens/`)
- [x] All 15 improvement options built and tested live (`output/design.md` Table 5)
- [x] The larger office with my touches (door plaque, Yale SOM at night, shades, family and mountain pictures, couch, round table, Keurig, hardwood floor and chair mat, IN box, Yale coasters, "That was Easy" button)
- [x] Full route check rerun after the Problem 8 backend additions: 21 of 21 (`output/route_check.json`)
- [x] **Problem 8 closed out**

## Problem 9: Resolve the tickets

- [x] Working database reset first; starting checking $3,400.00
- [x] All three tickets run on the board and resolved: 101 and 102 after the payment approvals; 103 after Boss's discount decision (`scripts/human_decision.py`, no money moved)
- [x] Both payments approved by the human (Boss, Mr. D'Onofrio): $840 invoice 501, $2,400 rent. No real money or email
- [x] `output/desk_tickets.html`: Actual sections filled in (agents, delegations, MCP tools), Expected kept
- [x] Cash tab itemized: $3,400.00 − $840.00 − $2,400.00 = $160.00, matching `cash_accounts`
- [x] `output/resolved_tickets.json` (`scripts/build_resolved.py`, from the database and the audit trail)
- [x] `output/resolved_board.html`: a board screenshot per ticket (`output/resolved_board_screens/`)
- [x] Real runs appended to `output/audit_trail.json`
- [x] `output/harness.md` finished: Table 0 map, plus Problem 9 Tables 28–30
- [x] Duplicate-draft cause fixed (Boss's title rule; `save_customer_draft` revises in place); tool check 44 of 44; live scratch test: one draft
- [x] Actual sections and Cash tab approved by Boss (Mr. D'Onofrio)
- [x] **Problem 9 closed out**

## Problem 10: Reflection

- [x] Reflection tab in `output/desk_tickets.html`: all 5 bullets as questions, each with an answer
- [x] Every answer tied to this app, the three tickets and the Campus Customs data, with links to the ticket and Cash tabs on the same page
- [x] Cash strip: $3,400.00 − $840.00 − $2,400.00 = $160.00, matching `cash_accounts`
- [x] All five answers (Q1–Q5) approved by Boss (Mr. D'Onofrio)
- [x] The Intern Squad avatars (SOM MBA, engineering undergrad, lacrosse player) in Q5, Table 8 (`assets/agents/intern_*.svg`)
- [x] Receivables: `find_outstanding_receivables` for Sales & Receivables; follow-up drafts added to Customer Service as a related duty (`backend/prompts/customer_service.md`)
- [x] Intern Squad avatars redrawn and approved
- [x] **Problem 10 closed out**

## Problem 11: Submit to GitHub

- [x] `hw5/README.md`: setup, run, checks, where each problem is, the file tree
- [x] `scripts/check_submission.py`: 28 of 28
- [x] Fresh-clone test: reset, 28/28, tool check 44/44, backend health, dashboard build
- [x] Repo name approved: `Louyale/campuscustoms-multiagent`
- [x] Both databases committed under `data/`; the real `.env` is not pushed
- [x] `output/github_url.txt` holds the URL; the README has the expected file layout
- [x] Pushed to https://github.com/Louyale/campuscustoms-multiagent (public); a fresh clone passes 31/31, the tool check 44/44, the backend health check and the dashboard build
- [ ] Lou submits the URL on Canvas
