"""Shared settings for every agent: the one allowed model, the Portkey connection, and prompts.

Every agent uses gpt-6-luna through Portkey (PORTKEY_API_KEY). The model name lives only here.
It can be read from OPENAI_MODEL, but anything other than gpt-6-luna is refused, so no other
model can show up in a run.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
PROMPTS_DIR = BACKEND_DIR / "prompts"

load_dotenv(PROJECT_DIR / ".env")

ALLOWED_MODEL = "gpt-6-luna"
MODEL_NAME = os.getenv("OPENAI_MODEL", ALLOWED_MODEL)
if MODEL_NAME != ALLOWED_MODEL:
    raise RuntimeError(f"OPENAI_MODEL must be {ALLOWED_MODEL} for this assignment")

REASONING_EFFORT = os.getenv("REASONING_EFFORT", "low")  # multi-agent chats burn tokens fast


@lru_cache(maxsize=1)
def build_model() -> OpenAIResponsesModel:
    """gpt-6-luna through Portkey, on OpenAI's Responses API. One shared model for all five agents."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing from .env")
    client = AsyncOpenAI(
        base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
        api_key=api_key,
        default_headers={"x-portkey-api-key": api_key},
        timeout=120,
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def settings_for(agent_name: str) -> OpenAIResponsesModelSettings:
    """Low reasoning effort, and a per-agent cache key so each agent's long prompt is cached."""
    return OpenAIResponsesModelSettings(
        openai_reasoning_effort=REASONING_EFFORT,
        parallel_tool_calls=True,  # independent lookups go out in one step, not one call each
        openai_prompt_cache_key=f"campus-customs-{agent_name}",
    )


def load_prompt(agent_name: str) -> str:
    """One prompt file per agent, in backend/prompts/."""
    return (PROMPTS_DIR / f"{agent_name}.md").read_text(encoding="utf-8")
