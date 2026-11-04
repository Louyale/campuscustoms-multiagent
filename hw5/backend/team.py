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
"""

from __future__ import annotations

from pydantic_ai import RunContext, UsageLimits

from backend.mcp_tools import mcp_toolset
from backend.models import AGENT_NAMES, AgentName, Delegation, TeamDeps, Ticket, TicketDecision

# Limits for one ticket, across every agent it involves.
TICKET_LIMITS = UsageLimits(request_limit=40, total_tokens_limit=400_000)

ROLE_LINES = {
    "boss": "Boss: reads each ticket, routes work, makes the final call",
    "inventory": "Inventory: stock by SKU and size, shortfalls, restock vendor and lead time",
    "accounting": "Accounting: cash, invoices, margins, payment requests for human approval",
    "facilities": "Facilities: leases, rent and the shop space",
    "customer_service": "Customer Service: drafts messages that stay on the board",
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
    deps.chain.append(teammate)
    try:
        result = await registry()[teammate].run(
            f"Request from {who}{ticket}: {task}",
            deps=deps,
            usage=ctx.usage,            # one shared counter for the whole team
            usage_limits=TICKET_LIMITS,
        )
    finally:
        deps.chain.pop()
    record.answer = result.output.model_dump_json()
    deps.delegations.append(record)
    return record.answer


async def run_ticket(ticket: Ticket) -> tuple[TicketDecision, TeamDeps]:
    """Boss works one ticket, handing parts to teammates as needed. Returns the decision and the hand-offs."""
    deps = TeamDeps(ticket_id=ticket.id, chain=["boss"])
    async with mcp_toolset:  # one MCP connection for every agent on this ticket
        result = await registry()["boss"].run(
            f"New ticket from the board:\n{ticket.model_dump_json(indent=2)}",
            deps=deps,
            usage_limits=TICKET_LIMITS,
        )
    return result.output, deps
