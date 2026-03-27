"""TechShop Agent — Reference Solution Package.

This sub-package contains the **fully-instrumented, production-quality**
implementations of the TechShop agent. It is intended as the *target state*
that students are guided toward across the LLMOps notebooks.

Separation rationale
--------------------
``techshop_agent`` (parent)
    Clean base agent used as the student starting point. No Langfuse
    dependency at import time, minimal surface area, easy to modify.

``techshop_agent.solution`` (this package)
    Reference implementations with full Langfuse v4 observability,
    prompt management, and inline documentation explaining *why* each
    pattern exists and linking to official documentation.

Contents
--------
observability.py
    Fully-observed agent wrapper using ``@observe``, ``propagate_attributes``
    and ``lf_client.update_current_span``.  Shows the complete tracing tree:
    trace → observation(span) → tool observations → LLM generation.

prompt_provider.py
    Production-grade prompt resolver that fetches versioned prompts from
    Langfuse with caching, fallback, and trace-linking.  Demonstrates the
    full prompt lifecycle: create → fetch → compile → link → promote.

Usage
-----
::

    from techshop_agent.solution.observability import process_query, get_langfuse_client
    from techshop_agent.solution.prompt_provider import get_system_prompt, FALLBACK_PROMPT

    lf_client = get_langfuse_client()
    agent_response = process_query("¿Qué portátiles tenéis?", user_id="u1")
"""

from __future__ import annotations

from techshop_agent.solution.observability import get_langfuse_client, process_query
from techshop_agent.solution.prompt_provider import (
    FALLBACK_PROMPT,
    create_prompt_version,
    get_system_prompt,
)

__all__ = [
    "FALLBACK_PROMPT",
    "create_prompt_version",
    "get_langfuse_client",
    "get_system_prompt",
    "process_query",
]
