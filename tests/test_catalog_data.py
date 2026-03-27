"""Tests de dataset local de catálogo."""

from __future__ import annotations

import json
from pathlib import Path


def test_catalog_json_has_expected_schema_and_size() -> None:
    """Valida que el catálogo tenga tamaño y campos mínimos del MVP."""
    catalog_path = Path("src/techshop_agent/data/catalog.json")
    assert catalog_path.exists()

    raw_content = catalog_path.read_text(encoding="utf-8")
    data = json.loads(raw_content)

    assert isinstance(data, list)
    assert 15 <= len(data) <= 20

    required_fields = {"nombre", "precio", "stock", "descripcion"}
    for item in data:
        assert required_fields.issubset(item.keys())
        assert isinstance(item["nombre"], str)
        assert item["nombre"].strip()
        assert isinstance(item["precio"], (int, float))
        assert item["precio"] >= 0
        assert isinstance(item["stock"], int)
        assert item["stock"] >= 0
        assert isinstance(item["descripcion"], str)
        assert item["descripcion"].strip()
