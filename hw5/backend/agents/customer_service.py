"""Customer Service: drafts messages for customers and other requesters. Drafts stay on
the board; nothing is ever sent.

Prompt: backend/prompts/customer_service.md · Output: CustomerDraft (backend/models.py)
MCP tools: see TOOL_ACCESS["customer_service"] in backend/mcp_tools.py · Hand-offs: ask_teammate (full connectivity)
"""

from pydantic_ai import Agent, NativeOutput

from backend.config import build_model, load_prompt, settings_for
from backend.mcp_tools import tools_for
from backend.models import CustomerDraft, TeamDeps
from backend.team import ask_teammate

NAME = "customer_service"

customer_service_agent = Agent(
    build_model(),                       # gpt-6-luna through Portkey (backend/config.py)
    name=NAME,
    description="Customer Service",
    instructions=load_prompt(NAME),      # backend/prompts/customer_service.md
    deps_type=TeamDeps,
    output_type=NativeOutput(CustomerDraft),
    toolsets=[tools_for(NAME)],          # this role's MCP tools
    tools=[ask_teammate],                # reach any other agent
    model_settings=settings_for(NAME),
    retries=2,
)
