"""Inventory: checks stock by SKU and size, spots shortfalls, and finds which vendor can
restock, with its lead time and whether an unpaid invoice blocks it.

Prompt: backend/prompts/inventory.md · Output: InventoryReport (backend/models.py)
MCP tools: see TOOL_ACCESS["inventory"] in backend/mcp_tools.py · Hand-offs: ask_teammate (full connectivity)
"""

from pydantic_ai import Agent, NativeOutput

from backend.config import build_model, load_prompt, settings_for
from backend.mcp_tools import tools_for
from backend.models import InventoryReport, TeamDeps
from backend.team import ask_teammate

NAME = "inventory"

inventory_agent = Agent(
    build_model(),                       # gpt-6-luna through Portkey (backend/config.py)
    name=NAME,
    description="Inventory",
    instructions=load_prompt(NAME),      # backend/prompts/inventory.md
    deps_type=TeamDeps,
    output_type=NativeOutput(InventoryReport),
    toolsets=[tools_for(NAME)],          # this role's MCP tools
    tools=[ask_teammate],                # reach any other agent
    model_settings=settings_for(NAME),
    retries=2,
)
