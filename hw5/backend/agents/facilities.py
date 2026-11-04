"""Facilities: handles the shop space (the Chapel Street lease, rent, the landlord, due dates)
and prepares the rent payment for human approval.

Prompt: backend/prompts/facilities.md · Output: FacilitiesReport (backend/models.py)
MCP tools: see TOOL_ACCESS["facilities"] in backend/mcp_tools.py · Hand-offs: ask_teammate (full connectivity)
"""

from pydantic_ai import Agent, NativeOutput

from backend.config import build_model, load_prompt, settings_for
from backend.mcp_tools import tools_for
from backend.models import FacilitiesReport, TeamDeps
from backend.team import ask_teammate

NAME = "facilities"

facilities_agent = Agent(
    build_model(),                       # gpt-6-luna through Portkey (backend/config.py)
    name=NAME,
    description="🧢 Facilities",
    instructions=load_prompt(NAME),      # backend/prompts/facilities.md
    deps_type=TeamDeps,
    output_type=NativeOutput(FacilitiesReport),
    toolsets=[tools_for(NAME)],          # this role's MCP tools
    tools=[ask_teammate],                # reach any other agent
    model_settings=settings_for(NAME),
    retries=2,
)
