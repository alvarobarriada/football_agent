"""Fully-observed TechShop agent — reference solution for LLMOps Notebook 2.

This module is the **target state** that Notebook 2 guides students toward.
Every pattern here is intentional and documented with a rationale and a
reference to the official Langfuse documentation.

Architecture overview
---------------------
When a query arrives at ``process_query()``, Langfuse sees this trace tree:

::

    Trace: techshop_query
    ├── attributes: user_id, session_id, metadata (via propagate_attributes)
    │
    ├── [observation type=span] tool_search_catalog      ← @observe on impl fn
    │   └── metadata: results_count, query_normalized
    │
    ├── [observation type=span] tool_get_faq_answer      ← @observe on impl fn
    │   └── metadata: matches_found, topic_normalized
    │
    └── [observation type=generation] <strands-llm-call> ← Strands OTEL, auto
        └── model, input_tokens, output_tokens, latency

Why Strands LLM calls appear automatically
-------------------------------------------
When you call ``get_client()``, the Langfuse SDK registers a global
**OpenTelemetry (OTEL) tracer provider**.  Strands Agents is instrumented
with OTEL and emits spans for every LLM call.  Because both share the same
OTEL context, Strands spans automatically become *children* of the active
Langfuse span — with no additional code.

Reference: https://langfuse.com/docs/observability/sdk/overview#opentelemetry-foundation

Environment variables
---------------------
LANGFUSE_PUBLIC_KEY  — pk-lf-...
LANGFUSE_SECRET_KEY  — sk-lf-...
LANGFUSE_BASE_URL    — https://cloud.langfuse.com (EU) or https://us.cloud.langfuse.com (US)
"""

from __future__ import annotations

import json
import logging
import os

from langfuse import Langfuse, get_client, observe, propagate_attributes
from strands import Agent
from strands import tool as strands_tool
from strands.models import BedrockModel

from techshop_agent.config import SYSTEM_PROMPT
from techshop_agent.tools import (
    _check_stock_impl,
    _compare_products_impl,
    _get_faq_answer_impl,
    _get_product_recommendations_impl,
    _search_catalog_impl,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------
# Why singletons?
# - get_client() is already a singleton inside Langfuse, but we cache the
#   reference here to avoid repeated attribute lookups in hot paths.
# - The agent singleton avoids re-loading the BedrockModel on every call,
#   which would add 200-400 ms of cold-start latency per request.
# ---------------------------------------------------------------------------
_langfuse: Langfuse | None = None


def get_langfuse_client() -> Langfuse:
    """Return the shared Langfuse singleton client.

    Reads credentials from environment variables automatically:
    - ``LANGFUSE_PUBLIC_KEY``
    - ``LANGFUSE_SECRET_KEY``
    - ``LANGFUSE_BASE_URL``

    If credentials are absent, Langfuse operates in *disabled* (no-op) mode:
    all tracing calls become no-ops and the agent continues to work normally.
    This makes Langfuse transparent to application correctness.

    Reference: https://langfuse.com/docs/observability/sdk/overview#client-setup

    Returns:
        The Langfuse client singleton.
    """
    global _langfuse  # noqa: PLW0603
    if _langfuse is None:
        _lf_client = get_client()
    return _langfuse


# ---------------------------------------------------------------------------
# Observed tool wrappers
# ---------------------------------------------------------------------------
# Why wrap the implementation functions with @observe here instead of in
# tools.py?
#
# Keeping the base tools.py free of Langfuse dependencies means students can
# study and test the tool logic without needing Langfuse credentials.  This
# solution package provides the observed wrappers as an additive layer.
#
# The @observe decorator automatically captures:
#   - Input arguments (the query / topic string)
#   - Return value (the JSON results string)
#   - Execution duration
#   - Any exceptions raised
#
# Reference: https://langfuse.com/docs/observability/sdk/instrumentation#observe-wrapper
# ---------------------------------------------------------------------------


@observe(name="tool_search_catalog")
def observed_search_catalog(query: str) -> str:
    """Catalog search with Langfuse tracing.

    Wraps ``_search_catalog_impl`` and enriches the span with result metadata
    so you can see in the Langfuse UI how many products matched each query.

    Args:
        query: Customer search string.

    Returns:
        JSON-serialised list of matching products.
    """
    result = _search_catalog_impl(query)

    # update_current_span() adds metadata to the currently-active observation.
    # We call it AFTER we have the result so the metadata reflects reality.
    # Note: metadata values MUST be strings (max 200 chars each).
    # Reference: https://langfuse.com/docs/observability/sdk/instrumentation#update-observations
    try:
        products = json.loads(result)
        n_results = len(products) if isinstance(products, list) else 0
    except Exception:
        n_results = 0

    lf_client = get_langfuse_client()
    lf_client.update_current_span(
        metadata={
            "results_count": str(n_results),
            "query": query[:100],
        }
    )
    return result


@observe(name="tool_get_faq_answer")
def observed_get_faq_answer(topic: str) -> str:
    """FAQ lookup with Langfuse tracing.

    Wraps ``_get_faq_answer_impl`` and records whether the lookup found a
    match.  This metadata lets you detect "FAQ miss" patterns in production,
    which often signal a topic that should be added to the FAQ database.

    Args:
        topic: FAQ topic to look up.

    Returns:
        JSON-serialised list of matching answers, or ``"None"``.
    """
    result = _get_faq_answer_impl(topic)

    lf_client = get_langfuse_client()
    lf_client.update_current_span(
        metadata={
            "matched": str(result != "None"),
            "topic": topic[:100],
        }
    )
    return result


@observe(name="tool_compare_products")
def observed_compare_products(product_a: str, product_b: str) -> str:
    """Product comparison with Langfuse tracing.

    Demonstrates tracing a **multi-input** tool.  The metadata records both
    product names and whether the comparison succeeded or hit an error
    (product not found).  In Langfuse you can filter by ``comparison_valid``
    to find queries where the customer asked for a non-existent product.

    Tracing pattern shown: **multiple input parameters + error flag metadata**.

    Args:
        product_a: Name of the first product.
        product_b: Name of the second product.

    Returns:
        JSON comparison or error object.
    """
    result = _compare_products_impl(product_a, product_b)

    try:
        parsed = json.loads(result)
        is_valid = "error" not in parsed
    except Exception:
        is_valid = False

    lf_client = get_langfuse_client()
    lf_client.update_current_span(
        metadata={
            "product_a": product_a[:100],
            "product_b": product_b[:100],
            "comparison_valid": str(is_valid),
        }
    )
    return result


@observe(name="tool_check_stock")
def observed_check_stock(product_name: str) -> str:
    """Stock availability check with Langfuse tracing.

    Demonstrates tracing a tool where the **business outcome is boolean-like**
    (in stock / out of stock / not found).  The metadata captures the stock
    level so you can correlate in Langfuse: *"which products are users asking
    about when stock is low?"*

    Tracing pattern shown: **categorical outcome + numeric metadata**.

    Args:
        product_name: Exact product name to check.

    Returns:
        JSON with availability and unit count, or error.
    """
    result = _check_stock_impl(product_name)

    try:
        parsed = json.loads(result)
        found = "error" not in parsed
        stock_level = str(parsed.get("unidades_disponibles", "N/A"))
        in_stock = str(parsed.get("en_stock", "N/A"))
    except Exception:
        found = False
        stock_level = "N/A"
        in_stock = "N/A"

    lf_client = get_langfuse_client()
    lf_client.update_current_span(
        metadata={
            "product": product_name[:100],
            "found": str(found),
            "in_stock": in_stock,
            "stock_level": stock_level,
        }
    )
    return result


@observe(name="tool_get_product_recommendations")
def observed_get_product_recommendations(category: str, max_price: float) -> str:
    """Budget-aware product recommendations with Langfuse tracing.

    Demonstrates tracing a tool with **mixed parameter types** (string +
    numeric) and **filter effectiveness metrics**.  The metadata records the
    budget constraint alongside the result count, allowing you to answer in
    Langfuse: *"are customers setting realistic budgets, or are most queries
    returning zero results?"*

    Tracing pattern shown: **numeric filter criteria + result-set statistics**.

    Args:
        category: Product category to filter by.
        max_price: Maximum price in euros.

    Returns:
        JSON list of matching products sorted by price.
    """
    result = _get_product_recommendations_impl(category, max_price)

    try:
        products = json.loads(result)
        n_results = len(products) if isinstance(products, list) else 0
        cheapest = str(products[0]["precio"]) if n_results > 0 else "N/A"
    except Exception:
        n_results = 0
        cheapest = "N/A"

    lf_client = get_langfuse_client()
    lf_client.update_current_span(
        metadata={
            "category": category[:100],
            "max_price": str(max_price),
            "results_count": str(n_results),
            "cheapest_price": cheapest,
        }
    )
    return result


# ---------------------------------------------------------------------------
# Strands tool wrappers (module-level)
# ---------------------------------------------------------------------------
# Why define these at module level instead of inside create_observed_agent?
#
# Strands requires @tool-decorated functions to be stable, named objects so
# it can build the tool schema (from the function signature and docstring)
# once at import time.  Defining them at module level also means Ruff's
# PLC0415 (no imports inside functions) rule is satisfied.
#
# These wrappers simply delegate to the @observe-decorated implementation
# functions above, producing the two-level span hierarchy:
#   [strands tool dispatch] → [observe span] → [implementation]
# ---------------------------------------------------------------------------


@strands_tool
def search_catalog(query: str) -> str:
    """Busca en el catálogo de productos por nombre o categoría.

    Args:
        query: Consulta de búsqueda del cliente.

    Returns:
        Productos encontrados en formato JSON. Lista vacía si no hay coincidencias.
    """
    return observed_search_catalog(query)


@strands_tool
def get_faq_answer(topic: str) -> str:
    """Consulta las preguntas frecuentes de TechShop.

    Args:
        topic: Tema a consultar (ej: devoluciones, envíos, garantías, pagos).

    Returns:
        Respuestas relevantes del FAQ, o None si no hay resultados.
    """
    return observed_get_faq_answer(topic)


@strands_tool
def compare_products(product_a: str, product_b: str) -> str:
    """Compara dos productos del catálogo lado a lado.

    Args:
        product_a: Nombre exacto del primer producto.
        product_b: Nombre exacto del segundo producto.

    Returns:
        Comparación con precios, categorías y diferencia de precio en JSON.
    """
    return observed_compare_products(product_a, product_b)


@strands_tool
def check_stock(product_name: str) -> str:
    """Consulta la disponibilidad y stock de un producto específico.

    Args:
        product_name: Nombre exacto del producto a consultar.

    Returns:
        Disponibilidad y unidades en stock en formato JSON.
    """
    return observed_check_stock(product_name)


@strands_tool
def get_product_recommendations(category: str, max_price: float) -> str:
    """Recomienda productos de una categoría dentro de un presupuesto.

    Args:
        category: Categoría de producto (ej: portatiles, smartphones, audio).
        max_price: Precio máximo en euros.

    Returns:
        Productos que encajan, ordenados por precio ascendente, en JSON.
    """
    return observed_get_product_recommendations(category, max_price)


# ---------------------------------------------------------------------------
# Observed agent factory
# ---------------------------------------------------------------------------


def create_observed_agent(system_prompt: str | None = None) -> Agent:
    """Create a TechShop agent that uses the observed tool wrappers.

    This function creates a fresh Agent instance where the base
    ``search_catalog`` and ``get_faq_answer`` tools are replaced with the
    observed wrappers defined above.  Each tool call will appear as a child
    observation in the Langfuse trace tree.

    Args:
        system_prompt: Optional system prompt override.  If ``None``, falls
            back to the hardcoded ``SYSTEM_PROMPT`` from ``config.py``.

    Returns:
        A Strands Agent with fully-traced tool calls.
    """
    model = BedrockModel(
        model_id=os.getenv("MODEL_ID", "eu.anthropic.claude-haiku-4-5-20251001-v1:0"),
        region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-1")),
    )
    return Agent(
        model=model,
        system_prompt=system_prompt or SYSTEM_PROMPT,
        tools=[
            search_catalog,
            get_faq_answer,
            compare_products,
            check_stock,
            get_product_recommendations,
        ],
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


@observe(name="techshop_query")
def process_query(
    user_query: str,
    *,
    user_id: str = "anonymous",
    session_id: str = "default",
    source: str = "api",
    system_prompt: str | None = None,
) -> str:
    """Process a user query through the observed TechShop agent.

    This is the **reference implementation** for a fully-instrumented agent
    call.  It shows three patterns working together:

    1. ``@observe(name="techshop_query")``
       The decorator creates the root observation (trace) automatically.
       It captures input, output, duration, and any exceptions — with a
       single line of code.
       Reference: https://langfuse.com/docs/observability/sdk/instrumentation#observe-wrapper

    2. ``propagate_attributes(user_id=..., session_id=..., metadata=...)``
       Sets trace-level attributes that are propagated to ALL nested
       observations (tool calls, LLM generations).  This is the v4
       replacement for ``langfuse_context.update_current_trace()``.
       Call it **early** so every child span inherits the attributes.
       Reference: https://langfuse.com/docs/observability/sdk/instrumentation#add-attributes

    3. ``lf_client.update_current_span(metadata={...})``
       Enriches the current observation **after** we have the response,
       adding computed metadata like response length and word count.
       Reference: https://langfuse.com/docs/observability/sdk/instrumentation#update-observations

    Important: metadata values MUST be strings ≤ 200 characters.

    Args:
        user_query: The customer's question or request.
        user_id: Identifier for the end user.  Used for per-user metrics
            and session reconstruction in Langfuse.
        session_id: Conversation session ID.  Group multiple turns of a
            conversation under the same session to reconstruct them in order.
        source: Origin of the query (e.g. ``"notebook"``, ``"api"``,
            ``"streamlit"``).  Stored in metadata for filtering.
        system_prompt: Optional system prompt override.  Typically obtained
            from ``techshop_agent.solution.prompt_provider.get_system_prompt()``.

    Returns:
        The agent's response as a plain string.
    """
    lf_client = get_langfuse_client()

    # Create the agent with observed tool wrappers.
    # If you need to share a single agent instance across calls, cache it
    # outside this function or use a dependency-injection pattern.
    agent = create_observed_agent(system_prompt=system_prompt)

    # propagate_attributes() is a context manager.  Any observation created
    # inside this block (by @observe, or by Strands' OTEL spans) will
    # automatically inherit user_id, session_id, and metadata.
    with propagate_attributes(
        user_id=user_id,
        session_id=session_id,
        metadata={
            "source": source,
            "query_length": str(len(user_query)),
        },
    ):
        try:
            response = agent(user_query)
            response_str = str(response)
        except Exception:
            logger.exception("Agent processing failed for query: %r", user_query)
            raise
        else:
            # Enrich the root span with response metadata.
            # We do this in the else block so it only runs on success.
            lf_client.update_current_span(
                metadata={
                    "response_length": str(len(response_str)),
                    "response_word_count": str(len(response_str.split())),
                }
            )
            return response_str
