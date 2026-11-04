"""How the five agents talk to each other: full connectivity through one `ask_teammate` tool.

Any agent can hand a task to any other agent. That's full connectivity: Boss, Inventory,
Accounting, Facilities and Customer Service can all reach each other. Each agent has its own
loop. PydanticAI keeps calling gpt-6-luna and running the agent's tools until the agent returns
its structured report. A hand-off starts the teammate's own loop, and the teammate's report
comes back as the tool result.

Three guards keep the loops from running away (multi-agent chats burn tokens fast):
- no asking yourself
- no asking an agent that is already waiting further up the same chain, which stops ping-pong
- at most `max_depth` hand-offs below the first agent

All agents in a run share one usage counter, so the run's request limit covers the whole team.
Every step of every agent's loop is appended to output/audit_trail.json (backend/audit.py).

Each hand-off is an *assignment* with a deadline (due_by, a shop date measured against desk.date_today).
When the teammate replies, Boss's thanks is recorded automatically (a fixed message, so it costs no
tokens), and Boss can check in on every assignment's status with check_in_on_assignments.
"""

from __future__ import annotations

import json
import uuid

from pydantic_ai import RunContext, UsageLimits

from backend.audit import append_entry, now, run_logged
from backend.mcp_tools import mcp_toolset
from datetime import date

from backend.models import AGENT_NAMES, AGENT_SYMBOLS, AgentName, Assignment, Delegation, TeamDeps, Ticket, TicketDecision

# Limits for one ticket, across every agent it involves.
TICKET_LIMITS = UsageLimits(request_limit=40, total_tokens_limit=400_000)

ROLE_LINES = {
    "boss": "🕴️ Boss: reads each ticket, routes work, makes the final call",
    "inventory": "📦 Inventory: stock by SKU and size, shortfalls, restock vendor and lead time",
    "accounting": "🧮 Accounting: cash, invoices, margins, payment requests for human approval",
    "facilities": "🧢 Facilities: leases, rent and the shop space",
    "customer_service": "👕 Customer Service: drafts messages that stay on the board",
}


def registry() -> dict:
    """name -> Agent. Imported here, at call time, to avoid a circular import."""
    from backend.agents import TEAM
    return TEAM


def title(name: str) -> str:
    return ROLE_LINES[name].split(":")[0]


async def ask_teammate(ctx: RunContext[TeamDeps], teammate: AgentName, task: str, due_by: str | None = None) -> str:
    """Give another agent on the Campus Customs team an assignment and get their report back.

    teammate: one of boss, inventory, accounting, facilities, customer_service.
    task: one clear question with the ids it needs (ticket, SKU and size, invoice, lease).
    due_by: the shop date the answer is needed by (YYYY-MM-DD), measured against desk.date_today.
        Boss must always give one, set from the ticket's urgency. For example, before the rent's due
        date, or today for an overdue bill or a waiting customer.
    """
    deps = ctx.deps
    me = deps.chain[-1] if deps.chain else "boss"
    if teammate not in AGENT_NAMES:
        return f"REFUSED: unknown teammate {teammate!r}; choose one of {', '.join(AGENT_NAMES)}"
    record = Delegation(from_agent=me, to_agent=teammate, task=task, depth=len(deps.chain))

    today = date.fromisoformat(deps.shop_today) if deps.shop_today else None
    deadline = None
    if due_by:
        try:
            deadline = date.fromisoformat(due_by)
        except ValueError:
            record.refused = f"due_by must be a date like 2026-09-01, not {due_by!r}"
    if record.refused:
        pass
    elif teammate == me:
        record.refused = "you cannot ask yourself; use your own tools"
    elif teammate in deps.chain:
        record.refused = (f"{teammate} is already waiting on this request chain ({' -> '.join(deps.chain)}); "
                          "answer with what you have instead of asking back")
    elif len(deps.chain) > deps.max_depth:
        record.refused = f"hand-off limit reached ({deps.max_depth}); answer with what you have"
    elif me == "boss" and deadline is None:
        record.refused = "Boss must give every assignment a due_by date (YYYY-MM-DD)"
    elif deadline and today and deadline < today:
        record.refused = f"due_by {due_by} is before today ({deps.shop_today}, desk.date_today)"
    if record.refused:
        deps.delegations.append(record)
        return f"REFUSED: {record.refused}"

    job = Assignment(id=f"A{len(deps.assignments) + 1}", from_agent=me, to_agent=teammate, task=task,
                     due_by=deadline.isoformat() if deadline else None, assigned_on=deps.shop_today, status="in_progress")
    deps.assignments.append(job)
    ticket = f" (ticket {deps.ticket_id})" if deps.ticket_id is not None else ""
    needed = f", needed by {job.due_by}" if job.due_by else ""
    deps.chain.append(teammate)
    try:
        result = await run_logged(
            registry()[teammate], teammate,
            f"Assignment {job.id} from {title(me)}{ticket}{needed}: {task}",
            deps,
            usage=ctx.usage,            # one shared counter for the whole team
            usage_limits=TICKET_LIMITS,
        )
    except Exception as exc:
        job.status = "failed"
        job.note = f"{type(exc).__name__}: {exc}"[:300]
        raise
    finally:
        deps.chain.pop()

    job.status = "done"
    job.completed_on = deps.shop_today
    job.on_time = job.due_by is None or (job.completed_on or "") <= job.due_by
    job.report = result.output.model_dump_json()
    job.thanks = (f"Thank you, {title(teammate)}, for your work on {job.id}"
                  f"{' - delivered on time' if job.on_time else ' - it came in after the deadline, but it is appreciated'}.")
    append_entry({"time": now(), "run_id": deps.run_id, "ticket_id": deps.ticket_id, "agent": me,
                  "symbol": AGENT_SYMBOLS[me], "chain": list(deps.chain), "step_kind": "AssignmentDone",
                  "assignment": job.model_dump(exclude={"report"}), "thanks_to": teammate})
    record.answer = job.report
    deps.delegations.append(record)
    return json.dumps({"assignment": job.id, "status": job.status, "due_by": job.due_by, "on_time": job.on_time,
                       "thanks_sent": job.thanks, "report": result.output.model_dump()})


async def check_in_on_assignments(ctx: RunContext[TeamDeps]) -> str:
    """Boss only. Check in on every assignment on this ticket: who has it, its deadline, its status
    (in_progress, done, failed), whether it was on time or is overdue against desk.date_today, the
    thanks already sent, and a short summary of each reply. Use it before your final decision to
    confirm every assignment is done, instead of asking a teammate the same question again."""
    deps = ctx.deps
    today = date.fromisoformat(deps.shop_today) if deps.shop_today else None
    rows = []
    for a in deps.assignments:
        due = date.fromisoformat(a.due_by) if a.due_by else None
        rows.append({
            "assignment": a.id, "to": a.to_agent, "task": a.task[:160], "due_by": a.due_by,
            "status": a.status,
            "days_left": (due - today).days if due and today else None,
            "overdue": bool(due and today and a.status != "done" and today > due),
            "on_time": a.on_time, "thanks_sent": a.thanks,
            "reply_summary": (a.report or a.note or "")[:300] or None,
        })
    return json.dumps({"today": deps.shop_today, "assignments": rows,
                       "all_done": bool(rows) and all(r["status"] == "done" for r in rows),
                       "open": [r["assignment"] for r in rows if r["status"] != "done"]})


async def run_ticket(ticket_id: int) -> tuple[TicketDecision, TeamDeps]:
    """Boss works one ticket, handing parts to teammates as needed. Returns the decision and the hand-offs.

    The ticket itself comes from the MCP server (get_ticket), like every other shop fact.
    """
    deps = TeamDeps(ticket_id=ticket_id, chain=["boss"], run_id=uuid.uuid4().hex[:12])
    async with mcp_toolset:  # one MCP connection for every agent on this ticket
        found = await mcp_toolset.direct_call_tool("get_ticket", {"ticket_id": ticket_id})
        found = found if isinstance(found, dict) else json.loads(found)
        if not found.get("found"):
            raise ValueError(found.get("message", f"No ticket {ticket_id}"))
        deps.shop_today = found["today"]
        ticket = Ticket(**found["ticket"])
        result = await run_logged(
            registry()["boss"], "boss",
            f"New ticket from the board (today is {deps.shop_today}):\n{ticket.model_dump_json(indent=2)}",
            deps,
            usage_limits=TICKET_LIMITS,
        )
    return result.output, deps
