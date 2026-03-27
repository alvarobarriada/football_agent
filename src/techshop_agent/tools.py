"""TechShop agent tools — product search and FAQ lookup."""

from __future__ import annotations

import difflib
import json
import unicodedata

from strands import tool

from techshop_agent.config import load_catalog, load_faqs

_SIMILARITY_THRESHOLD = 0.6


def _normalize(text: str) -> str:
    """Lowercase and strip accents for search matching."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _search_catalog_impl(query: str) -> str:
    """Core search logic — testable without Strands decorator."""
    catalog = load_catalog()
    query_norm = _normalize(query)
    query_words = query_norm.split()
    results = []

    for product in catalog:
        searchable = _normalize(f"{product['nombre']} {product['categoria']}")

        # Direct word overlap
        word_match = any(word in searchable for word in query_words)

        # Fuzzy similarity on the full string
        similarity = difflib.SequenceMatcher(None, query_norm, searchable).ratio()

        if word_match or similarity > _SIMILARITY_THRESHOLD:
            results.append(product)

    return json.dumps(results, ensure_ascii=False)


def _get_faq_answer_impl(topic: str) -> str:
    """Core FAQ logic — testable without Strands decorator."""
    faqs = load_faqs()
    topic_norm = _normalize(topic)
    matches = []

    for faq in faqs:
        tema = _normalize(faq.get("tema", ""))
        if tema in topic_norm or topic_norm in tema:
            matches.append(faq["respuesta"])

    if matches:
        return json.dumps(matches, ensure_ascii=False)
    return "None"


def _compare_products_impl(product_a: str, product_b: str) -> str:
    """Core comparison logic — testable without Strands decorator."""
    catalog = load_catalog()
    index = {_normalize(p["nombre"]): p for p in catalog}

    found_a = index.get(_normalize(product_a))
    found_b = index.get(_normalize(product_b))

    if not found_a and not found_b:
        msg = f"No se encontraron: {product_a}, {product_b}"
        return json.dumps({"error": msg}, ensure_ascii=False)
    if not found_a:
        return json.dumps({"error": f"No se encontró: {product_a}"}, ensure_ascii=False)
    if not found_b:
        return json.dumps({"error": f"No se encontró: {product_b}"}, ensure_ascii=False)

    comparison = {
        "producto_a": found_a,
        "producto_b": found_b,
        "diferencia_precio": round(found_a["precio"] - found_b["precio"], 2),
        "misma_categoria": found_a["categoria"] == found_b["categoria"],
    }
    return json.dumps(comparison, ensure_ascii=False)


def _check_stock_impl(product_name: str) -> str:
    """Core stock check logic — testable without Strands decorator."""
    catalog = load_catalog()
    name_norm = _normalize(product_name)

    for product in catalog:
        if _normalize(product["nombre"]) == name_norm:
            return json.dumps(
                {
                    "nombre": product["nombre"],
                    "en_stock": product["stock"] > 0,
                    "unidades_disponibles": product["stock"],
                },
                ensure_ascii=False,
            )

    return json.dumps({"error": f"Producto no encontrado: {product_name}"}, ensure_ascii=False)


def _get_product_recommendations_impl(category: str, max_price: float) -> str:
    """Core recommendation logic — testable without Strands decorator."""
    catalog = load_catalog()
    cat_norm = _normalize(category)

    matches = [
        p for p in catalog if _normalize(p["categoria"]) == cat_norm and p["precio"] <= max_price
    ]
    matches.sort(key=lambda p: p["precio"])
    return json.dumps(matches, ensure_ascii=False)


@tool
def search_catalog(query: str) -> str:
    """Busca en el catálogo de productos por nombre o categoría.

    Args:
        query: Consulta de búsqueda del cliente.

    Returns:
        Productos encontrados en formato JSON. Lista vacía si no hay coincidencias.
    """
    return _search_catalog_impl(query)


@tool
def get_faq_answer(topic: str) -> str:
    """Consulta las preguntas frecuentes de TechShop.

    Args:
        topic: Tema a consultar (ej: devoluciones, envíos, garantías, pagos).

    Returns:
        Respuestas relevantes del FAQ, o None si no hay resultados.
    """
    return _get_faq_answer_impl(topic)


@tool
def compare_products(product_a: str, product_b: str) -> str:
    """Compara dos productos del catálogo lado a lado.

    Args:
        product_a: Nombre exacto del primer producto.
        product_b: Nombre exacto del segundo producto.

    Returns:
        Comparación con precios, categorías y diferencia de precio en JSON.
    """
    return _compare_products_impl(product_a, product_b)


@tool
def check_stock(product_name: str) -> str:
    """Consulta la disponibilidad y stock de un producto específico.

    Args:
        product_name: Nombre exacto del producto a consultar.

    Returns:
        Disponibilidad y unidades en stock en formato JSON.
    """
    return _check_stock_impl(product_name)


@tool
def get_product_recommendations(category: str, max_price: float) -> str:
    """Recomienda productos de una categoría dentro de un presupuesto.

    Args:
        category: Categoría de producto (ej: portatiles, smartphones, audio).
        max_price: Precio máximo en euros.

    Returns:
        Productos que encajan, ordenados por precio ascendente, en JSON.
    """
    return _get_product_recommendations_impl(category, max_price)
