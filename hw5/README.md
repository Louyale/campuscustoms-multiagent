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

You need Python 3.12 (what we used) and Node.js 20.19+ or 22.12+ (Vite 8 needs one of those). Run these from this `hw5/` folder.

1. Create and activate a virtual environment, then install the packages:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`, and fill in:
   - `PORTKEY_API_KEY`
   - `HUMAN_APPROVAL_CODE`, used only by the dashboard's **Sign & pay** step
   - `DESK_PIN`, for the dashboard's locked drawer

   Never commit `.env`. The board's own `frontend/.env.example` is optional: without it, the board calls http://localhost:8000.

## The two databases

Both are in `data/`:
- **`data/campus_customs.db`** is the original shop database. Nothing ever changes it.
- **`data/campus_customs_new.db`** is the working copy that the MCP server and the backend use. It's committed as our Problem 9 run left it: all three tickets resolved, two human-approved payments, and checking at $160.00.

**For a clean run, copy the original over the working copy.** Any one of these does it:

```powershell
python scripts/reset_db.py
```

- `python scripts/reset_db.py` copies the file and checks that the copy matches the original byte for byte.
- A plain copy works too: `copy data\campus_customs.db data\campus_customs_new.db` (PowerShell or cmd).
- On the board, the **↺ Reset to the original** button does the same thing, through `POST /reset`.

Resetting replaces the committed Problem 9 working copy. To bring that copy back, run `git checkout -- data/campus_customs_new.db`.

## Run it

1. **The MCP server.** The backend starts it for you, over stdio, the moment the backend starts. Every agent's shop data comes through it. To start it on its own (for example, for a vibe coder through `.mcp.json`):

   ```powershell
   python mcp_server/server.py
   ```

   It talks over stdio, so on its own it waits quietly for a client to connect. Press Ctrl+C to stop it. You don't need to start it before the backend.

2. **The FastAPI backend**, at http://localhost:8000. Its API docs are at `/docs`. This is the assignment's command, run from the `backend/` folder:

   ```powershell
   cd backend
   uvicorn main:app --reload --port 8000
   ```

   It works the same from `hw5/` with `uvicorn main:app --app-dir backend --port 8000`.

3. **The React board**, at http://localhost:5173. Use a second terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

4. **A full three-ticket run:**
   1. **Reset the database first:** `python scripts/reset_db.py`, or **↺ Reset to the original** on the board.
   2. In **Terminal 1 · Ticket inbox**, pick a ticket and press **Start the team on #…**, or press **Run the whole board**.
   3. Watch the agents in **Terminal 2 · The team**.
   4. Approve each payment in the **Signature tray** with **Sign & pay**, and watch checking drop in **Terminal 3 · Checking**.

**One ticket from the command line:** `python scripts/run_ticket.py --ticket 102 --reset-before`. The `--reset-before` flag resets the working copy first.

**A human decision that isn't a payment** (like ticket 103's discount call): `python scripts/human_decision.py --ticket 103 --by "Your name" --decision "..."`. It resolves the ticket through the MCP status tool, logs the decision in the audit trail, and never moves money.

**Note for the grader:** every AI call asks for `gpt-6-luna` (`backend/config.py`), through Portkey. In the recorded runs (`output/audit_trail.json`), the model name in each reply is **`gpt-6-luna-global`**. That's Portkey's name for `gpt-6-luna` in its responses, not a different model. No other model is named anywhere in the code.

## Checks

| Command | What it proves | Model calls |
|---|---|---|
| `python scripts/mcp_tool_check.py` | Every MCP tool works over the real MCP protocol (44 of 44 checks, 25 of 25 tools), on a scratch copy of the database | None |
| `python scripts/route_check.py` | Every backend route works on the real app and agents (21 of 21). It resets the working copy at the start and at the end, so afterward the working copy is fresh (`git checkout -- data/campus_customs_new.db` brings back the Problem 9 copy) | Yes, about a cent (`--no-board` for less) |
| `python scripts/check_submission.py` | The repo is complete and safe to share: files, secrets, model name, outputs, cash math (31 of 31). Run it on the committed working copy | None |

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
| 11. Submit to GitHub | https://github.com/Louyale/campuscustoms-multiagent, `output/github_url.txt`, this README (the file layout), both databases in `data/` |

`output/harness.md` starts with **Table 0**, a map of where every part of the system is documented. The HTML pages in `output/` are self-contained: open them by double-clicking.

**The cash, from the Problem 9 run:** $3,400.00 − $840.00 (invoice 501, ticket 101) − $2,400.00 (rent, ticket 102) = **$160.00**, matching `cash_accounts`. Both payments were approved by a human.

## File layout

This is the assignment's expected layout. Every file in it is in this repo:

<!-- tree:start -->
```text
hw5/
├── AI_prompts.md
├── requirements.txt
├── .env.example
├── .gitignore
├── .mcp.json
├── README.md
├── data/
│   ├── campus_customs.db
│   └── campus_customs_new.db
├── mcp_server/
│   ├── server.py
│   └── README.md
├── frontend/
├── backend/
│   ├── main.py
│   ├── models.py
│   └── prompts/
│       ├── boss.md
│       ├── inventory.md
│       ├── accounting.md
│       ├── facilities.md
│       └── customer_service.md
└── output/
    ├── harness.md
    ├── mcp_smoke.json
    ├── desk_tickets.html
    ├── design.md
    ├── resolved_tickets.json
    ├── resolved_board.html
    ├── audit_trail.json
    └── github_url.txt
```
<!-- tree:end -->

**Also in the repo, supporting the above:**
- `backend/agents/` (one file per agent), `backend/team.py`, `backend/audit.py`, `backend/config.py`, `backend/mcp_tools.py`
- `frontend/src/`
- `scripts/`: reset, checks, builders and the human-decision tool
- `assets/agents/`: the agent avatars
- `output/`: the screenshots and the test records
- `EVIDENCE_CHECKLIST.md`
