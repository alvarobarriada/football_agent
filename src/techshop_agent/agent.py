"""Football Director AI agent."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

from techshop_agent.config import SYSTEM_PROMPT
from techshop_agent.tools import find_similar_player, search_talent

load_dotenv()


def create_agent(
    *,
    model_id: str | None = None,
    region: str | None = None,
    system_prompt: str | None = None,
) -> Agent:
    """Create and return the Football Director AI agent.

    Args:
        model_id: Bedrock model ID. Defaults to MODEL_ID env var or Claude Haiku 4.5.
        region: AWS region. Defaults to AWS_REGION env var or eu-west-1.
        system_prompt: Override the default system prompt. Defaults to SYSTEM_PROMPT.

    Returns:
        A ready-to-use Strands Agent instance.
    """
    model = BedrockModel(
        model_id=model_id or os.getenv("MODEL_ID", "eu.anthropic.claude-haiku-4-5-20251001-v1:0"),
        region_name=region or os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-1")),
    )
    return Agent(
        model=model,
        system_prompt=system_prompt or SYSTEM_PROMPT,
        tools=[
            search_talent,
            find_similar_player,
        ],
    )
