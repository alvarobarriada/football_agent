"""Tests for compare_products, check_stock, and get_product_recommendations tools."""

import json

from techshop_agent.tools import (
    _check_stock_impl,
    _compare_products_impl,
    _get_product_recommendations_impl,
)

# ---------------------------------------------------------------------------
# compare_products
# ---------------------------------------------------------------------------


def test_compare_products_valid_pair() -> None:
    """Comparing two existing products returns structured comparison."""
    result = json.loads(_compare_products_impl("ProBook X1", "NanoBook Air 13"))
    assert "producto_a" in result
    assert "producto_b" in result
    assert result["producto_a"]["nombre"] == "ProBook X1"
    assert result["producto_b"]["nombre"] == "NanoBook Air 13"
    assert "diferencia_precio" in result
    assert result["misma_categoria"] is True


def test_compare_products_different_categories() -> None:
    """Products from different categories report misma_categoria=False."""
    result = json.loads(_compare_products_impl("ProBook X1", "VoltPhone S"))
    assert result["misma_categoria"] is False


def test_compare_products_first_not_found() -> None:
    """Error when first product does not exist."""
    result = json.loads(_compare_products_impl("NoExiste", "ProBook X1"))
    assert "error" in result
    assert "NoExiste" in result["error"]


def test_compare_products_second_not_found() -> None:
    """Error when second product does not exist."""
    result = json.loads(_compare_products_impl("ProBook X1", "NoExiste"))
    assert "error" in result
    assert "NoExiste" in result["error"]


def test_compare_products_both_not_found() -> None:
    """Error when both products do not exist."""
    result = json.loads(_compare_products_impl("FakeA", "FakeB"))
    assert "error" in result


# ---------------------------------------------------------------------------
# check_stock
# ---------------------------------------------------------------------------


def test_check_stock_existing_product() -> None:
    """Existing product returns stock info."""
    result = json.loads(_check_stock_impl("ProBook X1"))
    assert result["nombre"] == "ProBook X1"
    assert isinstance(result["en_stock"], bool)
    assert isinstance(result["unidades_disponibles"], int)


def test_check_stock_nonexistent_product() -> None:
    """Non-existent product returns error."""
    result = json.loads(_check_stock_impl("ProductoInventado"))
    assert "error" in result


def test_check_stock_case_insensitive() -> None:
    """Stock check is case-insensitive."""
    result = json.loads(_check_stock_impl("probook x1"))
    assert result["nombre"] == "ProBook X1"


# ---------------------------------------------------------------------------
# get_product_recommendations
# ---------------------------------------------------------------------------


def test_recommendations_within_budget() -> None:
    """All returned products are at or below max_price."""
    result = json.loads(_get_product_recommendations_impl("audio", 200.0))
    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(p["precio"] <= 200.0 for p in result)


def test_recommendations_sorted_by_price() -> None:
    """Results are sorted by price ascending."""
    result = json.loads(_get_product_recommendations_impl("audio", 500.0))
    prices = [p["precio"] for p in result]
    assert prices == sorted(prices)


def test_recommendations_empty_for_low_budget() -> None:
    """A budget too low returns empty list."""
    result = json.loads(_get_product_recommendations_impl("portatiles", 10.0))
    assert result == []


def test_recommendations_empty_for_unknown_category() -> None:
    """An unknown category returns empty list."""
    result = json.loads(_get_product_recommendations_impl("drones", 5000.0))
    assert result == []


def test_recommendations_respects_category_filter() -> None:
    """Only products from the requested category appear."""
    result = json.loads(_get_product_recommendations_impl("smartphones", 800.0))
    assert all(p["categoria"] == "smartphones" for p in result)
