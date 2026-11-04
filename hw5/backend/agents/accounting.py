"""Accounting: watches cash and invoices, checks margins, and prepares payments or
purchase orders. Every one is pending human approval and can never go below zero.

Prompt: backend/prompts/accounting.md · Output: AccountingReport (backend/models.py)
MCP tools: see TOOL_ACCESS["accounting"] in backend/mcp_tools.py · Hand-offs: ask_teammate (full connectivity)
"""

from pydantic_ai import Agent, NativeOutput

from backend.config import build_model, load_prompt, settings_for
from backend.mcp_tools import tools_for
from backend.models import AccountingReport, TeamDeps
from backend.team import ask_teammate

NAME = "accounting"

accounting_agent = Agent(
    build_model(),                       # gpt-6-luna through Portkey (backend/config.py)
    name=NAME,
    description="🧮 Accounting",
    instructions=load_prompt(NAME),      # backend/prompts/accounting.md
    deps_type=TeamDeps,
    output_type=NativeOutput(AccountingReport),
    toolsets=[tools_for(NAME)],          # this role's MCP tools
    tools=[ask_teammate],                # reach any other agent
    model_settings=settings_for(NAME),
    retries=2,
)
