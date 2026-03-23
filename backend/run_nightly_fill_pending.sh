#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/Vertice/backend
mkdir -p pipeline/logs

# Conservative defaults to avoid provider throttling.
export LLM_CONCURRENCY_LIMIT="${LLM_CONCURRENCY_LIMIT:-1}"
export LLM_RPM_DEFAULT="${LLM_RPM_DEFAULT:-8}"
export LLM_RPM_GROQ="${LLM_RPM_GROQ:-8}"
export LLM_RPM_GEMINI="${LLM_RPM_GEMINI:-6}"
export LLM_RPM_MISTRAL="${LLM_RPM_MISTRAL:-6}"
export LLM_RPM_GITHUB="${LLM_RPM_GITHUB:-5}"
export LLM_RPM_OPENROUTER="${LLM_RPM_OPENROUTER:-5}"
export LLM_RPM_TOGETHER="${LLM_RPM_TOGETHER:-4}"
export LLM_MIN_INTERVAL_SECONDS="${LLM_MIN_INTERVAL_SECONDS:-0.5}"
export LLM_PROVIDER_ORDER="${LLM_PROVIDER_ORDER:-groq,gemini,mistral,github}"

# Retry strategy tuned for transient 429/5xx.
export LLM_MAX_RETRIES="${LLM_MAX_RETRIES:-2}"
export LLM_RETRY_BASE="${LLM_RETRY_BASE:-2.0}"

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="pipeline/logs/nightly_fill_${STAMP}.log"

echo "[nightly] starting fill_pending -> log: ${LOG_FILE}"

/usr/local/bin/python app/pipeline/fill_pending_supabase.py \
  --max-songs "${MAX_SONGS:-120}" \
  --page-size "${PAGE_SIZE:-250}" \
  --offset "${OFFSET:-0}" \
  --cooldown-seconds "${COOLDOWN_SECONDS:-1.0}" \
  --max-consecutive-provider-failures "${MAX_CONSECUTIVE_PROVIDER_FAILURES:-4}" \
  --adaptive-rpm \
  --adaptive-provider "${ADAPTIVE_PROVIDER:-groq}" \
  --adaptive-start-rpm "${ADAPTIVE_START_RPM:-8}" \
  --min-rpm "${MIN_RPM:-2}" \
  --rpm-step-down "${RPM_STEP_DOWN:-1}" \
  --extra-wait-on-429-seconds "${EXTRA_WAIT_ON_429_SECONDS:-20}" \
  2>&1 | tee -a "${LOG_FILE}"

echo "[nightly] done"
