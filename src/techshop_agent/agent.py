"""TechShop customer service agent."""

from __future__ import annotations

import json
import os
from pathlib import Path

import langfuse
from dotenv import find_dotenv, load_dotenv
from langfuse import get_client
from strands import Agent
from strands.models import BedrockModel

from techshop_agent.config import PROMPT_V1
from techshop_agent.tools import compare_players, get_top_assisters, get_top_scorers, search_player

# Load env
load_dotenv(find_dotenv(usecwd=True))

# Create Langfuse client
langfuse_client = get_client()
langfuse_client.auth_check()
print(f">Conectado a Langfuse - SDK version: {langfuse._langfuse_sdk_version if hasattr(langfuse, '_langfuse_sdk_version') else 'v4'}")

PROMPT_V1_NAME = "Prompt v1"

# Verificar que el prompt existe en Langfuse (la subida se hace via push_prompt.py)
try:
    check = langfuse_client.get_prompt(PROMPT_V1_NAME, label="production", cache_ttl_seconds=0)
    if isinstance(check, str):
        print(f"⚠️  Prompt '{PROMPT_V1_NAME}' no encontrado en Langfuse — usando fallback local")
    else:
        print(f"✅ Prompt '{PROMPT_V1_NAME}' cargado: versión={check.version}, is_fallback={check.is_fallback}")
except Exception as e:
    print(f"⚠️  No se pudo verificar el prompt en Langfuse: {e}")


# Create agent
def create_agent(
    *,
    model_id: str | None = None,
    region: str | None = None,
    system_prompt: str | None = None,
) -> Agent:
    """Create and return the TechShop customer service agent.

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
        system_prompt=system_prompt or PROMPT_V1,
        tools=[search_player, get_top_scorers, get_top_assisters, compare_players],
    )
