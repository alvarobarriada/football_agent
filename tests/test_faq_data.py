"""Tests de dataset local de FAQs."""

from __future__ import annotations

import json
from pathlib import Path


def test_faqs_json_has_expected_schema_and_size() -> None:
    """Valida que el dataset FAQ tenga tamaño y campos mínimos del MVP."""
    faqs_path = Path("src/techshop_agent/data/faqs.json")
    assert faqs_path.exists()

    raw_content = faqs_path.read_text(encoding="utf-8")
    data = json.loads(raw_content)

    assert isinstance(data, list)
    assert 10 <= len(data) <= 12

    required_fields = {"pregunta", "respuesta", "tema"}
    for item in data:
        assert required_fields.issubset(item.keys())
        assert isinstance(item["pregunta"], str)
        assert item["pregunta"].strip()
        assert isinstance(item["respuesta"], str)
        assert item["respuesta"].strip()
        assert isinstance(item["tema"], str)
        assert item["tema"].strip()
