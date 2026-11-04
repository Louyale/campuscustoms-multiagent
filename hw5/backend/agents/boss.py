"""Boss: reads each ticket, decides which teammates work on it, combines their answers,
and makes the final call. The only agent that decides what the shop does on a ticket.

Prompt: backend/prompts/boss.md · Output: TicketDecision (backend/models.py)
MCP tools: see TOOL_ACCESS["boss"] in backend/mcp_tools.py · Hand-offs: ask_teammate (full connectivity)
"""

from pydantic_ai import Agent, NativeOutput

from backend.config import build_model, load_prompt, settings_for
from backend.mcp_tools import tools_for
from backend.models import TicketDecision, TeamDeps
from backend.team import ask_teammate

NAME = "boss"

boss_agent = Agent(
    build_model(),                       # gpt-6-luna through Portkey (backend/config.py)
    name=NAME,
    description="🧑‍💼 Boss",
    instructions=load_prompt(NAME),      # backend/prompts/boss.md
    deps_type=TeamDeps,
    output_type=NativeOutput(TicketDecision),
    toolsets=[tools_for(NAME)],          # this role's MCP tools
    tools=[ask_teammate],                # reach any other agent
    model_settings=settings_for(NAME),
    retries=2,
)
