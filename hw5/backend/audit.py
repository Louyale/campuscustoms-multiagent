"""The audit trail: one entry per agent-loop step, appended to output/audit_trail.json.

Every agent runs through `run_logged`, which walks PydanticAI's loop one step (node) at a time
and appends an entry right after each step. If a run fails halfway, the steps before the failure
are already saved. The file is only ever appended to, never wiped: each write reads the existing
list, adds the new entry, and replaces the file in one move.

Each entry records enough to audit later:
- which run and ticket it belongs to
- which agent, and the hand-off chain that led to it
- the step number and its kind
- every tool call and its arguments
- every tool result, shortened
- the model name and the tokens used
- the agent's final answer
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import (
    RetryPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from backend.config import PROJECT_DIR
from backend.models import AGENT_SYMBOLS, TeamDeps

AUDIT_TRAIL = PROJECT_DIR / "output" / "audit_trail.json"
_lock = threading.Lock()
MAX_TEXT = 800  # long tool results and messages are shortened, so the file stays readable


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def short(value: Any, limit: int = MAX_TEXT) -> Any:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[:limit] + f"... [{len(text) - limit} more characters]"


def append_entry(entry: dict) -> None:
    """Add one entry to the end of the audit trail. Never removes earlier entries."""
    with _lock:
        AUDIT_TRAIL.parent.mkdir(parents=True, exist_ok=True)
        entries = json.loads(AUDIT_TRAIL.read_text(encoding="utf-8")) if AUDIT_TRAIL.exists() else []
        entries.append(entry)
        tmp = AUDIT_TRAIL.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, AUDIT_TRAIL)


def describe(node: Any) -> dict:
    """Turn one loop step into a plain record."""
    kind = type(node).__name__
    rec: dict[str, Any] = {"step_kind": kind}
    if kind == "UserPromptNode":
        rec["prompt"] = short(node.user_prompt)
    elif kind == "ModelRequestNode":
        returns, retries, prompts = [], [], []
        for p in node.request.parts:
            if isinstance(p, ToolReturnPart):
                returns.append({"tool": p.tool_name, "call_id": p.tool_call_id, "result": short(p.content)})
            elif isinstance(p, RetryPromptPart):
                retries.append({"tool": p.tool_name, "retry_reason": short(p.content)})
            elif isinstance(p, UserPromptPart):
                prompts.append(short(p.content))
        rec.update({"what": "send to model", "tool_results_sent": returns, "retries_sent": retries, "user_prompt": prompts})
    elif kind == "CallToolsNode":
        r = node.model_response
        rec.update({
            "what": "model replied",
            "model": r.model_name,
            "tool_calls": [{"tool": p.tool_name, "call_id": p.tool_call_id, "arguments": p.args_as_dict()}
                           for p in r.parts if isinstance(p, ToolCallPart)],
            "text": short(" ".join(p.content for p in r.parts if isinstance(p, TextPart))) or None,
            "reasoning_parts": sum(isinstance(p, ThinkingPart) for p in r.parts),
            "finish_reason": r.finish_reason,
            "tokens": {"input": r.usage.input_tokens, "cached_input": r.usage.cache_read_tokens,
                       "output": r.usage.output_tokens},
        })
    elif kind == "End":
        out = node.data.output
        rec.update({"what": "final answer", "output": out.model_dump() if hasattr(out, "model_dump") else short(out)})
    return rec


async def run_logged(agent: Agent, agent_name: str, prompt: str, deps: TeamDeps, **run_kwargs):
    """Run one agent's loop, appending an audit entry after every step. Returns the final result."""
    step = 0
    async with agent.iter(prompt, deps=deps, **run_kwargs) as run:
        async for node in run:
            step += 1
            append_entry({
                "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "run_id": deps.run_id,
                "ticket_id": deps.ticket_id,
                "agent": agent_name,
                "symbol": AGENT_SYMBOLS[agent_name],
                "chain": list(deps.chain),
                "depth": len(deps.chain) - 1,
                "step": step,
                **describe(node),
            })
        result = run.result
    usage = run.usage
    append_entry({
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": deps.run_id,
        "ticket_id": deps.ticket_id,
        "agent": agent_name,
        "symbol": AGENT_SYMBOLS[agent_name],
        "chain": list(deps.chain),
        "depth": len(deps.chain) - 1,
        "step": step + 1,
        "step_kind": "RunSummary",
        "what": "run finished",
        "team_usage_so_far": {"requests": usage.requests, "input_tokens": usage.input_tokens,
                              "cached_input_tokens": usage.cache_read_tokens, "output_tokens": usage.output_tokens},
    })
    return result
