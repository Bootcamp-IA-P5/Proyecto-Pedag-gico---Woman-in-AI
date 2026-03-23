# DigitalOcean: variables recomendadas (perfil anti-429)

Este archivo es una plantilla lista para copiar en App Settings > Environment Variables.

## Perfil recomendado (estable / anti-429)

```env
PORT=8000

SUPABASE_URL=REEMPLAZAR
SUPABASE_KEY=REEMPLAZAR

GROQ_API_KEY=REEMPLAZAR
GEMINI_API_KEY=REEMPLAZAR
MISTRAL_API_KEY=REEMPLAZAR
GITHUB_TOKEN=REEMPLAZAR

SPOTIPY_CLIENT_ID=REEMPLAZAR
SPOTIPY_CLIENT_SECRET=REEMPLAZAR
MUSICBRAINZ_EMAIL=REEMPLAZAR

GROQ_MODEL=llama-3.3-70b-versatile
GEMINI_MODEL=gemini-2.0-flash
MISTRAL_MODEL=mistral-small-latest
GITHUB_MODELS_MODEL=deepseek-r1

LLM_TIMEOUT_SECONDS=25
LLM_MAX_RETRIES=2
LLM_RETRY_BASE=2.0
LLM_CONCURRENCY_LIMIT=1

LLM_RPM_DEFAULT=4
LLM_RPM_MISTRAL=4
LLM_RPM_GITHUB=3
LLM_RPM_GROQ=2
LLM_RPM_GEMINI=2
LLM_RPM_OPENROUTER=2
LLM_RPM_TOGETHER=2

LLM_MIN_INTERVAL_SECONDS=1.0
LLM_MAX_RETRY_AFTER_SECONDS=20
LLM_PROVIDER_ORDER=mistral,github,groq,gemini

ANALYSIS_GUARDIAN_STRICT=false
ANALYSIS_PIPELINE_MODE=simple
ANALYSIS_MIN_COVERAGE_FOR_CONCLUSIVE=0.75
```

## Cuando subir o bajar RPM

- Si aparece 429 frecuente: bajar 1 punto al proveedor afectado.
- Si no hay 429 durante 30-50 canciones: subir 1 punto gradualmente.
- Mantener siempre LLM_CONCURRENCY_LIMIT=1 hasta estabilizar.

## Modo emergencia para batch nocturno

Para el script de backlog:

```bash
cd /workspaces/Vertice/backend
EMERGENCY_MODE=1 MAX_SONGS=60 COOLDOWN_SECONDS=2 ./run_nightly_fill_pending.sh
```

Este modo aplica un perfil conservador para evitar colapsos por tasa.
