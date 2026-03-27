# LLMOps para AI Engineering — Curso Hiberus Tecnología

Repositorio del curso práctico de **24 horas (3 días)** donde operacionalizas un agente de IA real con los estándares de la industria en 2026.

> **Hilo conductor:** TechShop Agent — asistente de customer service para una tienda de electrónica, construido sobre **AWS Bedrock + Strands Agents**, con **4 fallos deliberados** que descubrirás y corregirás durante el curso.

---

## Índice del repositorio

### Guías

| Documento | Descripción |
|-----------|-------------|
| [notebooks/README.md](notebooks/README.md) | Índice de notebooks por día |
| [streamlit_app/README.md](streamlit_app/README.md) | Guía para la interfaz web Streamlit |

### Código fuente — `techshop-agent`

Paquete Python instalable (`pip install -e .`) que implementa un agente de customer service para una tienda de electrónica. Usa [Strands Agents](https://github.com/strands-agents/sdk-python) como framework de orquestación y AWS Bedrock (Claude Haiku 4.5) como LLM. Incluye **4 fallos deliberados (F1–F4)** que los estudiantes descubren y corrigen durante el curso.

| Módulo | Descripción |
|--------|-------------|
| [src/techshop_agent/agent.py](src/techshop_agent/agent.py) | Orquestador principal — `create_agent()` |
| [src/techshop_agent/tools.py](src/techshop_agent/tools.py) | Herramientas: `search_catalog`, `get_faq_answer` |
| [src/techshop_agent/config.py](src/techshop_agent/config.py) | Configuración + system prompt |
| [src/techshop_agent/data/](src/techshop_agent/data/) | `catalog.json` + `faqs.json` |
| [src/techshop_agent/solution/](src/techshop_agent/solution/) | Módulos de solución: `observability.py`, `prompt_provider.py` |

### Interfaz Streamlit

| Recurso | Descripción |
|---------|-------------|
| [streamlit_app/README.md](streamlit_app/README.md) | **Guía paso a paso para ejecutar la UI** |
| [streamlit_app/app.py](streamlit_app/app.py) | Aplicación Streamlit con tema Hiberus |
| [streamlit_app/.streamlit/config.toml](streamlit_app/.streamlit/config.toml) | Tema visual (paleta naranja Hiberus) |

### Notebooks del curso

| Recurso | Descripción |
|---------|-------------|
| [notebooks/README.md](notebooks/README.md) | **Índice y guía de ejecución** |
| [notebooks/day_1/01_setup_agent.ipynb](notebooks/day_1/01_setup_agent.ipynb) | Setup + primer agente |
| [notebooks/day_1/02_observability.ipynb](notebooks/day_1/02_observability.ipynb) | Observabilidad con Langfuse |
| [notebooks/day_1/03_prompt_management.ipynb](notebooks/day_1/03_prompt_management.ipynb) | Gestión de prompts en Langfuse |

### Infraestructura

| Recurso | Descripción |
|---------|-------------|
| [infrastructure/terraform/](infrastructure/terraform/) | VPC, EC2, SSM, CloudWatch, Security Groups |
| [infrastructure/docker/](infrastructure/docker/) | Docker Compose para Langfuse local |
| [infrastructure/scripts/](infrastructure/scripts/) | Scripts de deploy, backup y configuración |

### Tests

| Módulo | Descripción |
|--------|-------------|
| [tests/test_agent.py](tests/test_agent.py) | Tests del agente principal |
| [tests/test_guardrails.py](tests/test_guardrails.py) | Tests de guardrails |
| [tests/test_observability.py](tests/test_observability.py) | Tests de instrumentación Langfuse |
| [tests/test_routing.py](tests/test_routing.py) | Tests de routing de herramientas |
| [tests/test_response_contract.py](tests/test_response_contract.py) | Tests del contrato `AgentResponse` |

---

## Quickstart

### Requisitos previos

| Herramienta | Versión mínima | Instalación |
|-------------|---------------|-------------|
| Python | 3.11+ | [python.org](https://python.org) |
| uv | 0.5+ | `pip install uv` o `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| AWS CLI | v2 | [docs.aws.amazon.com](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) |

> **Verificar instalaciones:**
> ```bash
> python --version         # Python 3.11+
> uv --version             # uv 0.5+
> aws --version            # aws-cli/2.x
> aws sts get-caller-identity  # debe devolver tu Account/UserId
> ```

---

### Paso 1 — Clonar el repositorio

```bash
git clone <repo-url>
cd llmops-for-ai-engineering
```

### Paso 2 — Instalar dependencias

```bash
uv sync
uv run python -c "from techshop_agent import create_agent; print('OK')"
```

### Paso 3 — Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env`:

```env
# AWS Bedrock (obligatorio)
AWS_REGION=eu-west-1
AWS_PROFILE=your-profile-name       # o usa AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
MODEL_ID=eu.anthropic.claude-haiku-4-5-20251001-v1:0

# Langfuse (opcional — sin estas vars el agente funciona pero sin trazas)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

### Paso 4 — Ejecutar el ejemplo básico

```bash
uv run python examples/basic_usage.py
```

### Paso 5 — Lanzar Streamlit

```bash
cd streamlit_app
uv sync
uv run streamlit run app.py --server.port 8501
```

Abre **http://localhost:8501**. Ver [streamlit_app/README.md](streamlit_app/README.md) para más detalles.

### Paso 6 — Lanzar JupyterLab (notebooks)

```bash
cd notebooks
uv sync
uv run jupyter lab
```

Abre **http://localhost:8888**. Ver [notebooks/README.md](notebooks/README.md) para más detalles.

---

### Paso 7 — Ejecutar todos los quality gates

```bash
make qa   # lint + format-check + typecheck + test + security
```

---

## Estructura del curso (3 días)

| Día | Pregunta clave | Herramientas | Notebooks |
|-----|---------------|-------------|-----------|
| **Día 1** | ¿Qué está fallando y cómo me entero? | Langfuse Tracing + Prompt Mgmt | [01](notebooks/day_1/01_setup_agent.ipynb) · [02](notebooks/day_1/02_observability.ipynb) · [03](notebooks/day_1/03_prompt_management.ipynb) |

---

## Los 4 fallos deliberados

| ID | Síntoma | Herramienta que lo revela |
|----|---------|--------------------------|
| **F1** | Hallucination silenciosa — inventa productos | Langfuse (trace con `results_count=0`) |
| **F2** | Extrapolación del FAQ — respuestas incorrectas en edge cases | promptfoo + LLM-as-judge |
| **F3** | Scope creep — responde fuera de dominio | LLM Guard + evaluaciones de scope |
| **F4** | Tool selection gap — no llama a herramientas para queries válidas | Langfuse (trace sin spans de herramientas) |

---

## Stack técnico

| Herramienta | Rol |
|-------------|-----|
| [Strands Agents](https://github.com/strands-agents/sdk-python) | Framework del agente |
| AWS Bedrock (Claude Haiku 4.5) | Modelo de lenguaje |
| [Langfuse](https://langfuse.com) | Observabilidad + Prompt Management |
| [LLM Guard](https://llm-guard.com) | Guardrails de seguridad |
| [Streamlit](https://streamlit.io) | Interfaz web del agente |
| [uv](https://docs.astral.sh/uv/) + ruff + pyright | Tooling Python |
| Terraform + Docker Compose | Infraestructura |

---

## Comandos Make

```bash
make dev                # uv sync + pre-commit install
make qa                 # lint + format-check + typecheck + test + security
make lint               # ruff check
make test               # pytest tests/ -v
make example            # uv run python examples/basic_usage.py
make streamlit-install  # cd streamlit_app && uv sync
make streamlit          # arranca en http://localhost:8501
make tf-check           # terraform fmt + validate
```

---

## Licencia

MIT · by **Hiberus Tecnología**

