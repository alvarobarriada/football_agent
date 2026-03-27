"""Tests for the search_catalog tool."""

from __future__ import annotations

import json

from techshop_agent.tools import _search_catalog_impl


def test_search_catalog_finds_by_exact_name() -> None:
    """A product name keyword should return matching products."""
    result = _search_catalog_impl("ProBook")
    products = json.loads(result)
    assert isinstance(products, list)
    assert len(products) >= 1
    assert any("ProBook" in p["nombre"] for p in products)


def test_search_catalog_finds_by_category() -> None:
    """A category keyword should return products in that category."""
    result = _search_catalog_impl("portatiles")
    products = json.loads(result)
    assert isinstance(products, list)
    assert len(products) >= 1


def test_search_catalog_returns_empty_for_semantic_query() -> None:
    """A functional/semantic query should NOT match (this is F1)."""
    result = _search_catalog_impl("necesito algo para editar vídeo")
    products = json.loads(result)
    assert products == []


def test_search_catalog_returns_empty_for_nonexistent_product() -> None:
    """A product that doesn't exist returns empty."""
    result = _search_catalog_impl("iPhone")
    products = json.loads(result)
    assert products == []
