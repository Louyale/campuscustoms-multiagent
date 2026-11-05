# Campus Customs Multi-Agent Operations (HW5)

Campus Customs is a Yale campus apparel shop. Its open tickets land on a board: a customer order (101), the rent (102) and a bulk-discount request (103). This project is the agent team that runs the shop. It has three pieces that talk to each other:

- **An MCP server** (`mcp_server/server.py`, FastMCP). It has 25 tools over the shop's SQLite database.
- **A FastAPI backend** (`backend/main.py`). It runs a PydanticAI team of five agents with full connectivity (any agent can delegate to any other):
  - 🕴️ **Boss** reads each ticket, decides who works on it, and makes the final call.
  - 📦 **Inventory** checks stock by SKU and size, and finds which vendor can restock.
  - 🧮 **Accounting** watches cash and invoices, and prepares payments for human approval.
  - 🧢 **Facilities** handles the lease and rent.
  - 👕 **Customer Service** drafts messages to customers.
- **A React dashboard** (`frontend/`, React + Vite + TypeScript). It's modeled on Boss's desk, in Yale blue and white. A person can pick a ticket, watch the agents work, and approve payments.

**Shop rules the system enforces:**
- Every AI call uses `gpt-6-luna` through Portkey (`PORTKEY_API_KEY`).
- Every payment needs a human approval.
- No balance can go negative.
- Nothing is ever really sent or paid: messages stay as drafts on the board, and payments only update the practice database.

## Setup

You need Python 3.12 and Node.js 20 or newer. Run these from this `hw5/` folder.

1. Create and activate a virtual environment, then install the packages:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`, and fill in `PORTKEY_API_KEY`, `HUMAN_APPROVAL_CODE` (used only by the dashboard's approval step) and `DESK_PIN` (the dashboard's locked drawer). Never commit `.env`.

3. Make the working copy of the database. The original, `data/campus_customs.db`, is never changed. Every run works on `data/campus_customs_new.db`, which isn't in the repo:

   ```powershell
   python scripts/reset_db.py
   ```

## Run it

1. **The backend**, at http://localhost:8000. Its API docs are at `/docs`. This is the assignment's command, run from the `backend/` folder:

   ```powershell
   cd backend
   uvicorn main:app --reload --port 8000
   ```

   It works the same from `hw5/` with `uvicorn main:app --app-dir backend --port 8000`.

2. **The dashboard**, at http://localhost:5173. Use a second terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

3. **Pick a ticket** and press **Start the team**, or **Run the whole board**. Watch the agents at Terminal 2, then approve a payment from the in-tray and watch checking drop on Terminal 3.

**One ticket from the command line:** `python scripts/run_ticket.py --ticket 102 --reset-before`

**A human decision that isn't a payment** (like ticket 103's discount call): `python scripts/human_decision.py --ticket 103 --by "Your name" --decision "..."`. It resolves the ticket through the MCP status tool, logs the decision in the audit trail, and never moves money.

**Note for the grader:** every AI call asks for `gpt-6-luna` (`backend/config.py`), through Portkey. In the recorded runs (`output/audit_trail.json`), the model name in each reply is **`gpt-6-luna-global`**. That's Portkey's name for `gpt-6-luna` in its responses, not a different model. No other model is named anywhere in the code.

## Checks

| Command | What it proves | Model calls |
|---|---|---|
| `python scripts/mcp_tool_check.py` | Every MCP tool works over the real MCP protocol (44 of 44 checks, 25 of 25 tools), on a scratch copy of the database | None |
| `python scripts/route_check.py` | Every backend route works on the real app and agents (21 of 21). It resets the database at the start and at the end | Yes, about a cent (`--no-board` for less) |
| `python scripts/check_submission.py` | The repo is complete and safe to share: files, secrets, model name, outputs, cash math | None |

## Where each problem's work is

| Problem | Where |
|---|---|
| 1. Vibe coder prompts | `AI_prompts.md`, `EVIDENCE_CHECKLIST.md` |
| 2. Study the database | `output/harness.md` (Tables 1–4), `output/data_overview.md` |
| 3. Build the MCP server | `mcp_server/server.py`, `mcp_server/README.md`, harness Tables 5–6 |
| 4. Add the MCP server to vibe coder and test each tool | `.mcp.json`, `scripts/mcp_smoke.py`, `output/mcp_smoke.json`, harness Table 7 |
| 5. Build the agent team and grow the MCP tools | `backend/agents/`, `backend/prompts/`, `backend/team.py`, `backend/audit.py`, `scripts/mcp_tool_check.py`, harness Tables 8–21 |
| 6. Plan the three tickets | `output/desk_tickets.html` (each ticket's Expected plan) |
| 7. Backend routes | `backend/main.py`, `scripts/route_check.py`, `output/route_check.json`, harness Tables 22–26 |
| 8. Agent dashboard | `frontend/`, `output/design.md`, `output/dashboard_screens/`, harness Table 27 |
| 9. Resolve the tickets | `output/desk_tickets.html` (Actual sections and Cash tab), `output/resolved_tickets.json`, `output/resolved_board.html`, `output/audit_trail.json`, harness Tables 28–30 |
| 10. Reflection | `output/desk_tickets.html` (Reflection tab) |

`output/harness.md` starts with **Table 0**, a map of where every part of the system is documented. The HTML pages in `output/` are self-contained: open them by double-clicking.

**The cash, from the Problem 9 run:** $3,400.00 − $840.00 (invoice 501, ticket 101) − $2,400.00 (rent, ticket 102) = **$160.00**, matching `cash_accounts`. Both payments were approved by a human.

## Files

<!-- tree:start -->
```text
hw5/
├── assets/
│   └── agents/
│       ├── accounting.svg
│       ├── all_agents.png
│       ├── all_agents.svg
│       ├── boss.svg
│       ├── customer_service.svg
│       ├── facilities.svg
│       ├── intern_engineer.svg
│       ├── intern_lacrosse.svg
│       ├── intern_mba.svg
│       ├── intern_squad.png
│       └── inventory.svg
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── accounting.py
│   │   ├── boss.py
│   │   ├── customer_service.py
│   │   ├── facilities.py
│   │   └── inventory.py
│   ├── prompts/
│   │   ├── accounting.md
│   │   ├── boss.md
│   │   ├── customer_service.md
│   │   ├── facilities.md
│   │   └── inventory.md
│   ├── __init__.py
│   ├── audit.py
│   ├── config.py
│   ├── main.py
│   ├── mcp_tools.py
│   ├── models.py
│   ├── prices.json
│   └── team.py
├── data/
│   └── campus_customs.db
├── frontend/
│   ├── src/
│   │   ├── assets/  (5 images)
│   │   ├── components/
│   │   │   ├── Desk.tsx
│   │   │   └── Office.tsx
│   │   ├── agents.ts
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── office.css
│   │   └── styles.css
│   ├── .env.example
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── mcp_server/
│   ├── README.md
│   └── server.py
├── output/
│   ├── dashboard_screens/  (3 screenshots)
│   ├── desk_tickets_screens/  (5 screenshots)
│   ├── resolved_board_screens/  (3 screenshots)
│   ├── agent_prompts_review.md
│   ├── audit_trail.json
│   ├── data_overview.md
│   ├── design.md
│   ├── desk_tickets.html
│   ├── harness.md
│   ├── mcp_smoke.json
│   ├── mcp_tool_check.json
│   ├── resolved_board.html
│   ├── resolved_tickets.json
│   ├── route_check.json
│   ├── test_run_102.json
│   ├── test_run_102_run1.json
│   ├── test_run_102_run2.json
│   └── test_run_102_run3_regression.json
├── scripts/
│   ├── __init__.py
│   ├── build_desk_tickets.py
│   ├── build_resolved.py
│   ├── build_resolved_board.py
│   ├── check_submission.py
│   ├── cost_report.py
│   ├── human_decision.py
│   ├── make_avatars.py
│   ├── make_tree.py
│   ├── mcp_smoke.py
│   ├── mcp_tool_check.py
│   ├── reflection.py
│   ├── reset_db.py
│   ├── route_check.py
│   └── run_ticket.py
├── .env.example
├── .mcp.json
├── AI_prompts.md
├── EVIDENCE_CHECKLIST.md
├── README.md
└── requirements.txt
```
<!-- tree:end -->
