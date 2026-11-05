"""Campus Customs backend: the FastAPI routes the React dashboard calls.

Start it from the backend/ folder:
    uvicorn main:app --reload --port 8000
Then it serves http://localhost:8000. Interactive docs, with every response type, are at /docs,
and / lists every route.

Rules this file keeps:
- Shop facts come only from the MCP server, over one MCP connection opened when the app starts and
  reused by every route and every agent run, so no run pays to start the server again. Reset is the
  one exception: it copies the original database file over the working copy.
- Agents only prepare payments. The approve route is the human's click: it is the only thing that
  calls the human-only tool approve_and_pay, using HUMAN_APPROVAL_CODE from .env, which never leaves
  this server. Paying refuses if cash would go below zero.
- Token savers: one run at a time; no re-run of a ticket that's already waiting on a human (unless
  ?force=true); the whole board can run in one call, ranked once; events can be fetched by run.
- Every agent step is appended to output/audit_trail.json, and the events route reads it back.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal, Optional

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:  # so "uvicorn main:app" works when started from backend/
    sys.path.insert(0, str(PROJECT_DIR))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from backend.audit import append_entry, now, read_trail  # noqa: E402
from backend.config import MODEL_NAME  # noqa: E402
from backend.mcp_tools import mcp_toolset  # noqa: E402
from backend.team import run_ticket  # noqa: E402
from scripts.reset_db import reset as reset_database  # noqa: E402


async def mcp(tool: str, **args) -> dict:
    """Call one MCP tool over the shared connection and return its answer as a dict."""
    out = await mcp_toolset.direct_call_tool(tool, args)
    return out if isinstance(out, dict) else json.loads(out)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp_toolset:          # one MCP server connection for the life of the backend
        yield


app = FastAPI(title="Campus Customs Multi-Agent Operations", version="1.1", lifespan=lifespan,
              description="Backend for the Campus Customs dashboard. Agents prepare; a human approves.")
app.add_middleware(  # the React dev server (next problem) runs on another port
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"], allow_headers=["*"],
)

RUNS: dict[str, dict] = {}       # run id -> what happened (kept in memory while the server is up)
RUN_LOCK = asyncio.Lock()        # one run at a time: cash is shared, and it keeps token use in check


# ----------------------------------------------------------------------------- response types (shown in /docs)

class TicketOut(BaseModel):
    id: int
    type: str
    requester: str
    subject: str
    sku: Optional[str] = None
    size: Optional[str] = None
    qty: Optional[int] = None
    lease_id: Optional[int] = None
    invoice_id: Optional[int] = None
    state: Literal["open", "resolved"] = Field(description="What the assignment asks for: open or resolved")
    status: str = Field(description="The board's detailed status: open, in_progress, waiting_approval, blocked, resolved")
    pending_requests: int = Field(description="Payment requests on this ticket waiting for a human")
    notes: Optional[str] = None
    created_at: str


class TicketsOut(BaseModel):
    today: str = Field(description="desk.date_today")
    count: int
    tickets: list[TicketOut]


class RunOut(BaseModel):
    run_id: str
    kind: Literal["ticket", "board"]
    ticket_id: Optional[int] = None
    status: Literal["queued", "running", "done", "failed"]
    model: str
    queued_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    agent_run_ids: list[str] = Field(default=[], description="Audit-trail run ids; use with GET /events?run_id=")
    decision: Optional[dict[str, Any]] = Field(None, description="Boss's TicketDecision (single-ticket runs)")
    assignments: list[dict[str, Any]] = []
    approval_check: list[dict[str, Any]] = Field(default=[], description="Each approval Boss listed, and whether it is filed")
    results: list[dict[str, Any]] = Field(default=[], description="Board runs: one decision per ticket, in priority order")
    skipped: list[dict[str, Any]] = Field(default=[], description="Board runs: tickets skipped, and why")
    status_sync: dict[str, Any] = Field(default={}, description="The board status the backend set from Boss's decision")
    error: Optional[str] = None


class EventOut(BaseModel):
    id: int = Field(description="Position in the audit trail; pass the largest you've seen as ?since=")
    time: Optional[str] = None
    run_id: Optional[str] = None
    ticket_id: Optional[int] = None
    agent: Optional[str] = None
    symbol: Optional[str] = None
    chain: Optional[list[str]] = None
    kind: Optional[str] = None
    said: Optional[str] = Field(None, description="What the agent (or human) said at this step")
    tools_used: list[dict[str, Any]] = Field(default=[], description="MCP and team tools called at this step, with arguments")
    tool_results: list[str] = Field(default=[], description="Tools whose results were fed back to the agent")


class EventsOut(BaseModel):
    next_since: int
    events: list[EventOut]


class CashOut(BaseModel):
    today: str
    account: Literal["checking"]
    balance: float = Field(description="cash_accounts.balance for checking")
    as_of: str = Field(description="cash_accounts.date")
    pending_requests: float = Field(description="Promised to requests waiting for a human")
    available_after_pending: float


class ResetOut(BaseModel):
    reset: bool
    database: str
    matches_original_sha256: str
    checking_balance: float


class Approval(BaseModel):
    approved_by: str = Field(min_length=2, examples=["Boss (Mr. D'Onofrio)"],
                             description="The person clicking approve (recorded in payments.approved_by)")


class Rejection(BaseModel):
    rejected_by: str = Field(min_length=2, examples=["Boss (Mr. D'Onofrio)"])
    reason: str = ""


# ----------------------------------------------------------------------------- 1. tickets

@app.get("/tickets", response_model=TicketsOut, summary="The three tickets, each open or resolved")
async def list_tickets():
    """Every ticket on the board, with **state** (open or resolved), the detailed status, and how many
    payment requests on it are waiting for a human. Dashboard: the ticket board."""
    board = await mcp("list_tickets")
    pending = await mcp("list_payment_requests", status="pending")
    waiting: dict[int, int] = {}
    for r in pending["requests"]:
        waiting[r["ticket_id"]] = waiting.get(r["ticket_id"], 0) + 1
    tickets = [TicketOut(
        id=t["id"], type=t["type"], requester=t["requester"], subject=t["subject"], sku=t["sku"], size=t["size"],
        qty=t["qty"], lease_id=t["lease_id"], invoice_id=t["invoice_id"],
        state="resolved" if t["status"] == "resolved" else "open", status=t["status"],
        pending_requests=waiting.get(t["id"], 0), notes=t["notes"], created_at=t["created_at"],
    ) for t in board["tickets"]]
    return TicketsOut(today=board["today"], count=len(tickets), tickets=tickets)


# ----------------------------------------------------------------------------- 2. run the agent team

def _busy() -> bool:
    return any(r["status"] in ("queued", "running") for r in RUNS.values())


def _new_run(kind: str, ticket_id: int | None = None) -> str:
    run_id = uuid.uuid4().hex[:12]
    RUNS[run_id] = {"run_id": run_id, "kind": kind, "ticket_id": ticket_id, "status": "queued",
                    "queued_at": now(), "model": MODEL_NAME, "agent_run_ids": []}
    return run_id


def _fail(run_id: str, exc: Exception, ticket_id: int | None) -> None:
    RUNS[run_id].update(status="failed", finished_at=now(), error=f"{type(exc).__name__}: {exc}"[:500])
    append_entry({"time": now(), "run_id": None, "ticket_id": ticket_id, "agent": "backend",
                  "step_kind": "RunFailed", "error": RUNS[run_id]["error"]})


async def _run_ticket(run_id: str, ticket_id: int) -> None:
    async with RUN_LOCK:
        RUNS[run_id].update(status="running", started_at=now())
        try:
            decision, deps = await run_ticket(ticket_id)
            RUNS[run_id].update(status="done", finished_at=now(), agent_run_ids=[deps.run_id],
                                decision=decision.model_dump(),
                                assignments=[a.model_dump(exclude={"report"}) for a in deps.assignments],
                                approval_check=deps.approval_check, status_sync=deps.status_sync)
        except Exception as exc:  # a failed run is reported, never hidden
            _fail(run_id, exc, ticket_id)


@app.post("/tickets/{ticket_id}/run", status_code=202, response_model=RunOut, summary="Run the agent team on one ticket")
async def run_agents(ticket_id: int, wait: bool = False, force: bool = False):
    """Boss works the ticket with the teammates it needs. Returns a run id at once (poll `GET /runs/{run_id}`),
    or waits for Boss's decision with `?wait=true`.

    **Token saver:** if the ticket already has payment requests waiting for a human, this answers 409
    ("waiting for your approval") instead of re-running the team. Use `?force=true` to run anyway.
    Dashboard: the "Run agents" button on each ticket."""
    found = await mcp("get_ticket", ticket_id=ticket_id)
    if not found.get("found"):
        raise HTTPException(404, found.get("message", f"No ticket {ticket_id}"))
    if _busy():
        raise HTTPException(409, "The team is already working; wait for that run to finish.")
    waiting = [r for r in found["payment_requests"] if r["status"] == "pending"]
    if waiting and not force:
        raise HTTPException(409, f"Ticket {ticket_id} is waiting for your approval on {len(waiting)} request(s) "
                                 f"({', '.join(f'#{r['id']} ${r['amount']:,.2f} {r['payee']}' for r in waiting)}). "
                                 "Approve or reject first, or pass ?force=true to run the team again.")
    run_id = _new_run("ticket", ticket_id)
    task = asyncio.create_task(_run_ticket(run_id, ticket_id))
    if wait:
        await task
    return RUNS[run_id]


async def _run_board(run_id: str) -> None:
    async with RUN_LOCK:
        RUNS[run_id].update(status="running", started_at=now())
        try:
            ranking = await mcp("rank_open_tickets")
            append_entry({"time": now(), "run_id": None, "ticket_id": None, "agent": "boss", "symbol": "🕴️",
                          "step_kind": "BoardRanking", "ranking": ranking})
            results, skipped = [], []
            for item in ranking["ranked"]:  # most urgent first, so it gets first claim on the shared cash
                tid = item["ticket_id"]
                found = await mcp("get_ticket", ticket_id=tid)
                waiting = [r for r in found["payment_requests"] if r["status"] == "pending"]
                if waiting:
                    skipped.append({"ticket_id": tid, "why": f"waiting for a human on {len(waiting)} request(s)"})
                    continue
                decision, deps = await run_ticket(tid)
                RUNS[run_id]["agent_run_ids"].append(deps.run_id)
                results.append({"rank": item["rank"], "ticket_id": tid, "priority": decision.priority,
                                "summary": decision.summary, "status": decision.recommended_status,
                                "approvals": [{"kind": a.kind, "payee": a.payee, "amount": a.amount} for a in decision.approvals_needed],
                                "approval_check": deps.approval_check, "status_sync": deps.status_sync,
                                "agent_run_id": deps.run_id})
            RUNS[run_id].update(status="done", finished_at=now(), results=results, skipped=skipped)
        except Exception as exc:
            _fail(run_id, exc, None)


@app.post("/board/run", status_code=202, response_model=RunOut, summary="Run the whole board in priority order")
async def run_board(wait: bool = False):
    """Ranks the open tickets once (`rank_open_tickets`), then runs the team on each, **most urgent first**,
    skipping any ticket already waiting for a human. One call for the dashboard's "Run the board" button."""
    if _busy():
        raise HTTPException(409, "The team is already working; wait for that run to finish.")
    run_id = _new_run("board")
    task = asyncio.create_task(_run_board(run_id))
    if wait:
        await task
    return RUNS[run_id]


@app.get("/runs/{run_id}", response_model=RunOut, summary="A run's status and Boss's decision")
async def run_status(run_id: str):
    """queued, running, done (with Boss's decision, the assignments and the approval check) or failed.
    Dashboard: polled while a run is going."""
    if run_id not in RUNS:
        raise HTTPException(404, f"No run {run_id}")
    return RUNS[run_id]


# ----------------------------------------------------------------------------- 3. agent events

def _said(e: dict) -> str | None:
    kind = e.get("step_kind")
    if kind == "UserPromptNode":
        return e.get("prompt")
    if kind == "CallToolsNode":
        return e.get("text")
    if kind == "End":
        out = e.get("output") or {}
        return out.get("summary") or out.get("note") or out.get("recommendation") or out.get("subject")
    if kind == "AssignmentDone":
        return (e.get("assignment") or {}).get("thanks")
    if kind == "DecisionCheck":
        return "Every approval Boss listed is filed on the board." if e.get("passed") else \
               f"Missing from the board: {e.get('approvals_missing_from_board')}"
    if kind == "BoardRanking":
        return "Ranked the open tickets by priority."
    if kind == "HumanApproval":
        r = e.get("result") or {}
        return (f"{e.get('approved_by')} approved request {e.get('request_id')}: paid ${r.get('amount', 0):,.2f} to {r.get('payee')}; "
                f"checking ${r.get('cash_before', 0):,.2f} to ${r.get('cash_after', 0):,.2f}" if r.get("paid")
                else f"{e.get('approved_by')} tried to approve request {e.get('request_id')}: {r.get('message')}")
    if kind == "HumanRejection":
        return f"{e.get('rejected_by')} rejected request {e.get('request_id')}"
    if kind == "DatabaseReset":
        return "Database reset to the original values"
    if kind == "StatusSync":
        return f"Board status set to {e.get('set_to')} (Boss recommended {e.get('recommended')}; it was {e.get('was')})"
    if kind == "RunFailed":
        return f"The run failed: {e.get('error')}"
    return None


@app.get("/events", response_model=EventsOut, summary="Recent agent events: what each agent said and which tools it used")
async def recent_events(since: int = 0, limit: int = 50, ticket_id: int | None = None, run_id: str | None = None):
    """Read from the append-only audit trail, newest last. Filters:
    - `since`: only events after the last id you saw
    - `ticket_id`: one ticket
    - `run_id`: one run (an id from `POST /tickets/{id}/run` or `/board/run`, or an audit-trail run id)

    Dashboard: the live agent feed, polled every few seconds with `since=next_since`."""
    run_ids: set[str] | None = None
    if run_id:
        run_ids = set(RUNS[run_id]["agent_run_ids"]) if run_id in RUNS else {run_id}
    entries = read_trail()  # safe even while the agents are appending
    events = []
    for i, e in enumerate(entries):
        if i < since or (ticket_id is not None and e.get("ticket_id") != ticket_id) or (run_ids is not None and e.get("run_id") not in run_ids):
            continue
        tools = [{"tool": c["tool"], "arguments": c.get("arguments")} for c in (e.get("tool_calls") or [])]
        said = _said(e)
        if not tools and not said and not e.get("tool_results_sent"):
            continue
        events.append(EventOut(
            id=i, time=e.get("time"), run_id=e.get("run_id"), ticket_id=e.get("ticket_id"), agent=e.get("agent"),
            symbol=e.get("symbol"), chain=e.get("chain"), kind=e.get("step_kind"), said=said, tools_used=tools,
            tool_results=[r.get("tool") for r in (e.get("tool_results_sent") or [])]))
    return EventsOut(next_since=len(entries), events=events[-limit:])


# ----------------------------------------------------------------------------- 4. human approval

@app.get("/approvals", summary="Requests waiting for a human")
async def pending_approvals():
    """Payment and purchase requests the agents prepared, waiting for a human (any over $5,000 are marked high).
    Dashboard: the approvals panel."""
    return await mcp("list_payment_requests", status="pending")


@app.post("/approvals/{request_id}/approve", summary="A human approves: pay, and change cash")
async def approve(request_id: int, body: Approval):
    """**The only route that changes cash.** Pays one pending request after a person clicks approve:
    it adds a `payments` row with `approved_by`, lowers `cash_accounts`, and marks the invoice paid or moves
    the lease's `next_due` on. Refuses with 409 if cash would go below zero or the request isn't pending.
    Dashboard: the Approve button."""
    code = os.getenv("HUMAN_APPROVAL_CODE")
    if not code:
        raise HTTPException(500, "HUMAN_APPROVAL_CODE is not set in .env")
    result = await mcp("approve_and_pay", request_id=request_id, approved_by=body.approved_by.strip(), approval_code=code)
    append_entry({"time": now(), "run_id": None, "ticket_id": None, "agent": "human", "step_kind": "HumanApproval",
                  "request_id": request_id, "approved_by": body.approved_by.strip(), "result": result})
    if not result.get("paid"):
        raise HTTPException(409, result.get("message", "Not paid"))
    return result


@app.post("/approvals/{request_id}/reject", summary="A human rejects: no money moves")
async def reject(request_id: int, body: Rejection):
    """Marks a pending request rejected. Dashboard: the Reject button."""
    result = await mcp("reject_payment_request", request_id=request_id, rejected_by=body.rejected_by.strip(),
                       approval_code=os.getenv("HUMAN_APPROVAL_CODE", ""), reason=body.reason)
    append_entry({"time": now(), "run_id": None, "ticket_id": None, "agent": "human", "step_kind": "HumanRejection",
                  "request_id": request_id, "rejected_by": body.rejected_by.strip(), "result": result})
    if not result.get("rejected"):
        raise HTTPException(409, result.get("message", "Not rejected"))
    return result


# ----------------------------------------------------------------------------- 5. cash

@app.get("/cash", response_model=CashOut, summary="The current checking balance from cash_accounts")
async def checking_balance():
    """Checking's balance and as-of date, plus what's promised to pending requests. Dashboard: the cash tile."""
    cash = await mcp("get_cash_balance")
    checking = next((a for a in cash["accounts"] if a["name"] == "checking"), None)
    if checking is None:
        raise HTTPException(404, "No checking account in cash_accounts")
    return CashOut(today=cash["today"], account="checking", balance=checking["balance"], as_of=checking["date"],
                   pending_requests=checking["pending_requests"], available_after_pending=checking["available_after_pending"])


# ----------------------------------------------------------------------------- 6. reset

@app.post("/reset", response_model=ResetOut, summary="Reset the database to the original values")
async def reset():
    """Copies `campus_customs.db` over `campus_customs_new.db` for a fresh run. Refused while a run is
    active. The audit trail is kept (it's append-only), and the reset is logged in it. Dashboard: the Reset button."""
    if _busy():
        raise HTTPException(409, "A run is in progress; reset after it finishes.")
    digest = reset_database()
    append_entry({"time": now(), "run_id": None, "ticket_id": None, "agent": "human", "step_kind": "DatabaseReset",
                  "sha256": digest})
    cash = await mcp("get_cash_balance")
    checking = next(a for a in cash["accounts"] if a["name"] == "checking")
    return ResetOut(reset=True, database="data/campus_customs_new.db", matches_original_sha256=digest,
                    checking_balance=checking["balance"])


# ----------------------------------------------------------------------------- home and health

ROUTES = [
    "GET  /tickets: the three tickets, each open or resolved",
    "POST /tickets/{ticket_id}/run: run the agent team on one ticket (?wait=true waits; ?force=true re-runs a ticket waiting on you)",
    "POST /board/run: run every open ticket, most urgent first",
    "GET  /runs/{run_id}: a run's status and Boss's decision",
    "GET  /events?since=&ticket_id=&run_id=&limit=: recent agent events (what each agent said, tools used)",
    "GET  /approvals: payment and purchase requests waiting for a human",
    "POST /approvals/{request_id}/approve: a human approves; this pays and changes cash",
    "POST /approvals/{request_id}/reject: a human rejects; no money moves",
    "GET  /cash: the current checking balance from cash_accounts",
    "POST /reset: reset the database to the original values",
    "GET  /health: backend up, model, MCP tool count",
]


@app.get("/", summary="Every route, in one line each")
async def home():
    return {"app": "Campus Customs Multi-Agent Operations", "docs": "/docs", "routes": ROUTES}


@app.get("/health", summary="Is the backend up?")
async def health():
    """The backend is up, the model the agents use, and how many MCP tools the shared connection sees."""
    return {"ok": True, "model": MODEL_NAME, "mcp_tools": len(await mcp_toolset.list_tools())}
