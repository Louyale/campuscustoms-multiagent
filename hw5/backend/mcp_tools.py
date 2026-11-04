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
mcp_toolset = MCPToolset(MCP_SERVER)

# Which MCP tools each role may call. New tools are added here as the server grows.
TOOL_ACCESS: dict[str, set[str]] = {
    "boss": {"check_stock", "get_open_invoices", "get_rent_due"},
    "inventory": {"check_stock", "get_open_invoices"},
    "accounting": {"check_stock", "get_open_invoices", "get_rent_due"},
    "facilities": {"get_rent_due"},
    "customer_service": {"check_stock"},
}


def tools_for(agent_name: str):
    """The shared MCP connection, filtered to the tools this agent may use."""
    allowed = TOOL_ACCESS[agent_name]
    return mcp_toolset.filtered(lambda ctx, tool_def: tool_def.name in allowed)
