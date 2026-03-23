# Guia practica: proveedores LLM, cuotas y rate limits

Esta guia resume como evitar errores 429 y 402 en VERTICE, y como operar el pipeline de forma estable.

## 1) Conceptos clave

- RPM: requests por minuto.
- TPM: tokens por minuto.
- RPD/TPD: requests o tokens por dia.
- 429 Too Many Requests: superaste limite de velocidad (RPM/TPM o burst).
- 402 Payment Required: credito insuficiente o saldo agotado.

En la practica, puedes tener credito pero aun asi recibir 429 si envias picos de trafico.

## 2) Por que pasa el 429 en este proyecto

Cada cancion puede disparar varias llamadas LLM:

- 1 llamada del Guardian (validacion)
- 4 llamadas de dimensiones (Celos, Insultos, Sumision, Objetificacion)
- mas reintentos y fallback si falla un proveedor

Si esas llamadas salen seguidas, el proveedor puede bloquear por tasa.

## 3) Estrategia aplicada en VERTICE

Se implemento control de tasa en cliente para evitar picos:

- Concurrencia global limitada (`LLM_CONCURRENCY_LIMIT`)
- Throttle por proveedor con RPM configurables (`LLM_RPM_*`)
- Espera minima entre requests (`LLM_MIN_INTERVAL_SECONDS`)
- Reintentos con backoff exponencial (`LLM_MAX_RETRIES`, `LLM_RETRY_BASE`)
- Uso de `retry-after` cuando el proveedor lo envia
- Logging de headers de rate limit para calibrar limites reales

Archivos clave:

- `backend/app/agents/base_agent.py`
- `backend/app/agents/guardian_agent.py`
- `backend/app/pipeline/fill_pending_supabase.py`
- `backend/run_nightly_fill_pending.sh`

## 4) Variables de entorno recomendadas

Base segura para iniciar:

- `LLM_CONCURRENCY_LIMIT=1`
- `LLM_RPM_DEFAULT=8`
- `LLM_RPM_GROQ=8`
- `LLM_RPM_GEMINI=6`
- `LLM_RPM_MISTRAL=6`
- `LLM_RPM_GITHUB=5`
- `LLM_RPM_OPENROUTER=5`
- `LLM_RPM_TOGETHER=4`
- `LLM_MIN_INTERVAL_SECONDS=0.5`
- `LLM_MAX_RETRIES=2`
- `LLM_RETRY_BASE=2.0`

Orden de fallback sugerido cuando hay providers sin credito:

- `LLM_PROVIDER_ORDER=groq,gemini,mistral,github`

## 5) Como estimar cuantas requests por minuto usar

No hay un numero universal: cambia por proveedor, plan, modelo y carga del momento.

Metodo practico:

1. Empezar en 6 RPM con concurrencia 1.
2. Subir a 8 RPM y observar 10-20 canciones.
3. Subir a 10 RPM si no hay 429.
4. Si aparece 429 sostenido, bajar 1-2 RPM y mantener.

Regla: preferir trafico estable continuo en vez de rafagas.

## 6) Operacion diaria recomendada

### Batch estable (nocturno)

Ejecutar:

```bash
cd /workspaces/Vertice/backend
MAX_SONGS=120 COOLDOWN_SECONDS=1.0 ./run_nightly_fill_pending.sh
```

Este script:

- procesa solo canciones pendientes (sin duplicar evaluaciones)
- aplica throttle
- reduce RPM de forma adaptativa si detecta 429
- registra logs en `backend/pipeline/logs/`

### Revisar progreso

- Ver nuevos `total_ok` en logs.
- Ver inserciones 201 en `llm_evaluations` y `model_comparison`.
- Recalcular backlog con:

```bash
cd /workspaces/Vertice/backend
/usr/local/bin/python app/pipeline/report_analysis_backlog.py --export-pending-csv ../data/final/analysis_pending_queue.csv
```

## 7) Diferencia entre 429 y 402 (importante)

- 429: ajustar ritmo, concurrencia, backoff y esperar reset.
- 402: recargar credito o sacar ese proveedor del fallback temporalmente.

## 8) Buenas practicas para el equipo

- Mantener `LLM_CONCURRENCY_LIMIT=1` hasta conocer limites reales.
- No mezclar muchos proveedores sin credito en fallback.
- Guardar configuracion estable en DigitalOcean como env vars.
- Registrar cambios de RPM y resultados para compartir aprendizaje.
- Evitar subir `max_tokens` innecesariamente altos.

## 9) Checklist rapido antes de correr

- [ ] Variables de entorno cargadas.
- [ ] Provider order revisado.
- [ ] Creditos activos en proveedores usados.
- [ ] RPM conservador configurado.
- [ ] Script de backlog pendiente disponible.
- [ ] Log path verificado.

---

Documento interno VERTICE para operacion y transferencia de conocimiento.
