# Plantilla: despliegue directo desde rama (sin merge de PR)

Esta guia es para desplegar VERTICE directamente desde la rama:

- `feature-set-up-backend-analysis-engine`

## 1. Crear app en DigitalOcean desde GitHub

1. Ir a Apps > Create App.
2. Elegir repo `Bootcamp-IA-P5/Vertice`.
3. Elegir branch `feature-set-up-backend-analysis-engine`.
4. Source Directory: `backend`.
5. Build method: Dockerfile.

## 2. Configuracion del servicio

- HTTP Port: `8000`
- Health Check Path: `/`
- Instance: `basic-xs` (puedes subir luego)
- Auto deploy on push: `ON`

## 3. Variables de entorno (copiar y pegar)

Usar como base:

- `backend/app/docs/digitalocean_env_vars_recomendadas.md`

Asegurate de completar al menos:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `MISTRAL_API_KEY`
- `GITHUB_TOKEN`
- `GROQ_API_KEY` (opcional mientras haya 429 severo)
- `GEMINI_API_KEY` (opcional mientras haya 429 severo)

## 4. Perfil recomendado inicial anti-429

- `LLM_CONCURRENCY_LIMIT=1`
- `LLM_RPM_DEFAULT=4`
- `LLM_RPM_MISTRAL=4`
- `LLM_RPM_GITHUB=3`
- `LLM_RPM_GROQ=2`
- `LLM_RPM_GEMINI=2`
- `LLM_MIN_INTERVAL_SECONDS=1.0`
- `LLM_MAX_RETRY_AFTER_SECONDS=20`
- `LLM_PROVIDER_ORDER=mistral,github,groq,gemini`

## 5. Deploy y verificacion

1. Click en Deploy.
2. Esperar build + release.
3. Validar:
   - `GET /` debe responder estado ok.
   - `GET /docs` debe abrir Swagger.

## 6. Si aparece 429 frecuente

- Bajar 1 punto RPM al proveedor afectado.
- Mantener concurrencia en 1.
- Si hay `retry-after` alto recurrente, priorizar proveedores alternos.

## 7. Batch de backlog en modo emergencia

Cuando el backend ya este arriba:

```bash
cd /workspaces/Vertice/backend
EMERGENCY_MODE=1 MAX_SONGS=60 COOLDOWN_SECONDS=2 ./run_nightly_fill_pending.sh
```

Este comando reduce picos y evita bloqueos largos por rate limit.
