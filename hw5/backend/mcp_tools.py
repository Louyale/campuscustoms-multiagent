"""The connection from the agent team to our MCP server (mcp_server/server.py).

Every agent gets its shop data through these MCP tools, never by reading the database
itself. All five agents share one connection, and each sees only the tools its role
needs (least privilege). For example, Customer Service can check stock but can't see
invoices or cash.
"""

from __future__ import annotations

from pydantic_ai.mcp import MCPToolset

from backend.config import PROJECT_DIR

MCP_SERVER = PROJECT_DIR / "mcp_server" / "server.py"

# One stdio connection to the server, shared by every agent in a run.
mcp_toolset = MCPToolset(MCP_SERVER, init_timeout=60)  # the server can take a few seconds to start on a cold machine

# Which MCP tools each role may call (least privilege). New tools are added here as the server grows.
TOOL_ACCESS: dict[str, set[str]] = {
    "boss": {"get_ticket", "list_tickets", "rank_open_tickets", "update_ticket_status", "check_stock", "get_open_invoices",
             "get_rent_due", "get_cash_balance", "list_payment_requests", "list_drafts"},
    "inventory": {"check_stock", "list_inventory", "list_vendors", "get_open_invoices"},
    "accounting": {"check_stock", "list_inventory", "list_vendors", "get_open_invoices", "get_rent_due",
                   "get_cash_balance", "list_payments", "list_payment_requests", "request_payment",
                   "build_balance_sheet", "build_income_statement"},
    "facilities": {"get_rent_due", "list_leases", "get_lease", "log_building_request", "list_building_requests",
                   "update_building_request", "get_cash_balance", "list_payment_requests"},
    "customer_service": {"get_ticket", "check_stock", "check_spelling_grammar", "save_customer_draft", "list_drafts"},
}

# Only the human approval step (the dashboard) may call these. No agent is ever given them.
HUMAN_ONLY_TOOLS: set[str] = {"approve_and_pay", "reject_payment_request"}
assert not any(HUMAN_ONLY_TOOLS & tools for tools in TOOL_ACCESS.values()), "an agent was given a human-only tool"


def tools_for(agent_name: str):
    """The shared MCP connection, filtered to the tools this agent may use."""
    allowed = TOOL_ACCESS[agent_name]
    return mcp_toolset.filtered(lambda ctx, tool_def: tool_def.name in allowed)
