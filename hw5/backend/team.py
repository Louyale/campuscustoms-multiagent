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
"""

from __future__ import annotations

import json
import uuid

from pydantic_ai import RunContext, UsageLimits

from backend.audit import run_logged
from backend.mcp_tools import mcp_toolset
from backend.models import AGENT_NAMES, AgentName, Delegation, TeamDeps, Ticket, TicketDecision

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


async def ask_teammate(ctx: RunContext[TeamDeps], teammate: AgentName, task: str) -> str:
    """Hand a task to another agent on the Campus Customs team and get their report back.

    teammate: one of boss, inventory, accounting, facilities, customer_service.
    task: one clear question with the ids it needs (ticket, SKU and size, invoice, lease).
    """
    deps = ctx.deps
    me = deps.chain[-1] if deps.chain else "boss"
    if teammate not in AGENT_NAMES:
        return f"REFUSED: unknown teammate {teammate!r}; choose one of {', '.join(AGENT_NAMES)}"
    record = Delegation(from_agent=me, to_agent=teammate, task=task, depth=len(deps.chain))

    if teammate == me:
        record.refused = "you cannot ask yourself; use your own tools"
    elif teammate in deps.chain:
        record.refused = (f"{teammate} is already waiting on this request chain ({' -> '.join(deps.chain)}); "
                          "answer with what you have instead of asking back")
    elif len(deps.chain) > deps.max_depth:
        record.refused = f"hand-off limit reached ({deps.max_depth}); answer with what you have"
    if record.refused:
        deps.delegations.append(record)
        return f"REFUSED: {record.refused}"

    who = ROLE_LINES[me].split(":")[0]
    ticket = f" (ticket {deps.ticket_id})" if deps.ticket_id is not None else ""
    note = deps.team_notes.pop(teammate, None)
    if note:
        task = f"{task}\n\nA note from 🕴️ Boss: {note}"
    deps.chain.append(teammate)
    try:
        result = await run_logged(
            registry()[teammate], teammate,
            f"Request from {who}{ticket}: {task}",
            deps,
            usage=ctx.usage,            # one shared counter for the whole team
            usage_limits=TICKET_LIMITS,
        )
    finally:
        deps.chain.pop()
    record.answer = result.output.model_dump_json()
    deps.delegations.append(record)
    return record.answer


MAX_NOTE = 200  # characters; short notes keep token use down


async def encourage_teammate(ctx: RunContext[TeamDeps], teammate: AgentName, message: str) -> str:
    """Boss only. Send a short, sincere note of encouragement or thanks to a teammate.

    The note goes along with your next request to that teammate. It's internal team chat, never
    sent to a customer, vendor or landlord. One note per teammate per ticket, up to 200 characters.
    """
    deps = ctx.deps
    if teammate not in AGENT_NAMES or teammate == "boss":
        return "REFUSED: choose a teammate other than yourself."
    if any(n["to"] == teammate for n in deps.notes_sent):
        return f"REFUSED: you already encouraged {teammate} on this ticket."
    message = message.strip()[:MAX_NOTE]
    deps.team_notes[teammate] = message
    deps.notes_sent.append({"from": "boss", "to": teammate, "message": message})
    return f"Noted. Your message goes to {teammate} with your next request."


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
        ticket = Ticket(**found["ticket"])
        result = await run_logged(
            registry()["boss"], "boss",
            f"New ticket from the board:\n{ticket.model_dump_json(indent=2)}",
            deps,
            usage_limits=TICKET_LIMITS,
        )
    return result.output, deps
