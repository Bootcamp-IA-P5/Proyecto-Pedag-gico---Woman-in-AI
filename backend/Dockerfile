FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# UV_SYSTEM_PYTHON=1 → instala en el Python del sistema, no en .venv
# UV_NO_CACHE=1 → no guarda caché dentro de la imagen
# UV_NO_ENV_FILE=1 → no busca ni carga .env (seguridad)
# UV_PROJECT_ENVIRONMENT=/usr/local → fuerza la ruta del entorno al sistema
ENV UV_SYSTEM_PYTHON=1
ENV UV_NO_CACHE=1
ENV UV_NO_ENV_FILE=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY . .

RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Qué hace cada variable
```
UV_SYSTEM_PYTHON=1          → usa /usr/local/bin/python3, nunca crea .venv
UV_NO_CACHE=1               → imagen más limpia, sin caché interna
UV_NO_ENV_FILE=1            → no lee .env dentro del contenedor (las vars vienen de Render/docker-compose)
UV_PROJECT_ENVIRONMENT=/usr/local → doble seguro, apunta explícitamente al sistema