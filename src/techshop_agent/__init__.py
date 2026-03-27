"""Football Agent — statistics agent for the LLMOps course."""

from __future__ import annotations

from techshop_agent.agent import create_agent
from techshop_agent.config import SYSTEM_PROMPT, load_mock_data

__version__ = "0.1.0"
__all__ = [
    "SYSTEM_PROMPT",
    "create_agent",
    "load_mock_data",
]
