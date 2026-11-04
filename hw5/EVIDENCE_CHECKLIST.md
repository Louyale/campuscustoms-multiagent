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
- [x] Harness: each agent and each MCP tool, with the table each tool uses (Tables 11–12), rolled up by agent in Table 18
- [x] Harness: safety section with guardrails for real customers and money, and token limits (Tables 14–15)
- [x] `mcp_server/README.md` tool list matches the server (25 tools)
- [x] Every tool tested on a scratch database copy (43 of 43 checks, 25 of 25 tools; `output/mcp_tool_check.json`)
- [x] My approval of each agent's tool list (all five ☑ in harness Table 11, Boss's after the priority change)
- [x] Boss prioritizes: `rank_open_tickets`, priority on every assignment, top-down follow-up, the $5,000 rule (harness Table 17)
- [x] First audit trail entries from a real agent run (ticket 102: 53 entries, 4 agents, nothing paid; harness Table 16)
- [x] Database reset after the test run (`scripts/reset_db.py`)
