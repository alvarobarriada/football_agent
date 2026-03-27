# TechShop Agent — Interfaz Streamlit

Interfaz web para el agente TechShop, con tema **Hiberus Tecnología**.

← [README principal](../README.md) · [Agente](../src/techshop_agent/) · [Notebooks](../notebooks/README.md)

---

## Lanzar Streamlit

Requisito: haber completado los pasos 1–3 del [README principal](../README.md) (`uv sync` + `.env`).

```bash
cd streamlit_app
uv sync
uv run streamlit run app.py --server.port 8501
```

Abre **http://localhost:8501**.

Atajo con Make (desde la raíz):

```bash
make streamlit-install   # solo primera vez
make streamlit           # lanza en :8501
```

---

## Modos del agente

| Modo | Qué hace | Trazas Langfuse |
|------|----------|-----------------|
| **Base** | `create_agent()` directo | Solo span raíz |
| **Instrumentado** | `process_query()` con tracing completo | Árbol: query → tools → LLM |

Cambiar de modo reinicia el historial y crea nueva sesión.

---

## Cuándo reiniciar el servidor

Streamlit recarga `app.py` automáticamente. Pero necesitas `Ctrl+C` + relanzar si modificas:

- `src/techshop_agent/*.py` (agent, config, tools)
- `src/techshop_agent/solution/*.py` (observability)
- `.env`
- `pyproject.toml` (luego `uv sync` antes de relanzar)

---

## Configuración avanzada

```bash
uv run streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MODEL_ID` | `eu.anthropic.claude-haiku-4-5-20251001-v1:0` | Modelo Bedrock |
| `AWS_REGION` | `eu-west-1` | Región AWS |
| `LANGFUSE_PUBLIC_KEY` | — | Activa tracing |
| `LANGFUSE_SECRET_KEY` | — | Par de la pública |
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` | URL Langfuse |

---

## Solución de problemas

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError: techshop_agent` | `uv sync` desde la raíz, luego `cd streamlit_app && uv sync` |
| `NoCredentialsError` | Verificar `.env` tiene `AWS_PROFILE` o `AWS_ACCESS_KEY_ID` |
| Agente no refleja cambios | Reiniciar servidor (`Ctrl+C` + relanzar) |
| Puerto 8501 en uso | `uv run streamlit run app.py --server.port 8502` |
