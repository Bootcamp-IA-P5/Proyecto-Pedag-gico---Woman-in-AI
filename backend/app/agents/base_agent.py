# backend/app/agents/base_agent.py
import asyncio
import json
import logging
import os
import re
from abc import ABC

import httpx
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

PROVEEDORES = {
    "github": {
        "url": os.getenv(
            "GITHUB_MODELS_URL",
            "https://models.inference.ai.azure.com/chat/completions",
        ),
        "key": os.getenv("GITHUB_MODELS_KEY") or os.getenv("GITHUB_TOKEN"),
        "model": os.getenv("GITHUB_MODELS_MODEL", "deepseek-r1"),
    },
    "openrouter": {
        "url": os.getenv(
            "OPEN_ROUTER_URL",
            "https://openrouter.ai/api/v1/chat/completions",
        ),
        "key": os.getenv("OPEN_ROUTER_KEY"),
        "model": os.getenv("OPEN_ROUTER_MODEL", "openrouter/hunter-alpha"),
    },
}
DEFAULT_PROVIDER_ORDER = [
    p.strip()
    for p in os.getenv("LLM_PROVIDER_ORDER", "github,openrouter").split(",")
    if p.strip()
]
# ── limitador de concurrencia global para llamadas a LLM ──
LLM_CONCURRENCY_LIMIT = int(os.getenv("LLM_CONCURRENCY_LIMIT", 1))
_llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY_LIMIT)


# ── Configuración de reintentos ────────────────────────────────────────────────
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "1"))
RETRY_BASE = float(os.getenv("LLM_RETRY_BASE", "1.5"))
RETRY_ON_CODES = {429, 500, 502, 503, 504}  # códigos que disparan reintento


class BaseAgent(ABC):
    dimension: str = ""
    system_prompt: str = ""

    async def analizar(self, letra: str, proveedor: str | None = None) -> dict:
        user_message = f"""Analiza la siguiente letra de canción en español \
y devuelve ÚNICAMENTE un JSON válido, sin texto adicional ni bloques markdown.

LETRA:
\"\"\"{letra}\"\"\"

El JSON debe seguir exactamente este formato:
{{
  "dimension": "{self.dimension}",
  "puntuacion": <entero entre 0 y 3>,
  "fragmentos": ["fragmento 1 de la letra", "fragmento 2 de la letra"],
  "justificacion": "explicación breve en español"
}}

Recuerda:
- puntuacion 0 = no se detecta nada
- puntuacion 1 = leve, insinuación o lenguaje ambiguo
- puntuacion 2 = moderado, patrón claro pero no explícito
- puntuacion 3 = grave, explícito, reiterativo o normalizador
- fragmentos debe estar vacío ([]) si puntuacion es 0
- Cita los fragmentos exactamente como aparecen en la letra"""

        provider_order = [proveedor] if proveedor else DEFAULT_PROVIDER_ORDER
        resultado, provider_name, model_name = await call_model_json(
            system_prompt=self.system_prompt,
            user_message=user_message,
            provider_order=provider_order,
            temperature=0.1,
            max_tokens=1024,
            context_label=self.dimension,
        )

        validado = self._validar(resultado)
        validado["proveedor"] = provider_name
        validado["modelo"] = model_name
        return validado

    def _validar(self, resultado: dict) -> dict:
        return {
            "dimension": resultado.get("dimension", self.dimension),
            "puntuacion": max(0, min(3, int(resultado.get("puntuacion", 0)))),
            "fragmentos": resultado.get("fragmentos", []),
            "justificacion": resultado.get("justificacion", ""),
        }


def _clean_json_text(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    return raw


def _extract_json_object(raw: str) -> dict:
    cleaned = _clean_json_text(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise
        return json.loads(match.group(0))


def _validate_provider_config(provider_name: str) -> dict:
    config = PROVEEDORES.get(provider_name)
    if not config:
        raise ValueError(f"Proveedor desconocido: {provider_name}")

    missing = [k for k in ("url", "key", "model") if not config.get(k)]
    if missing:
        raise ValueError(
            f"Configuración incompleta para '{provider_name}': "
            f"faltan {', '.join(missing)}"
        )
    return config


async def _call_provider_json(
    provider_name: str,
    config: dict,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_tokens: int,
    context_label: str,
) -> dict:
    ultimo_error = None

    for intento in range(1, MAX_RETRIES + 1):
        try:
            async with _llm_semaphore:
                async with httpx.AsyncClient(timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "8"))) as client:
                    response = await client.post(
                        config["url"],
                        headers={
                            "Authorization": f"Bearer {config['key']}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": config["model"],
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message},
                            ],
                        },
                    )

            if response.status_code == 402:
                raise httpx.HTTPStatusError(
                    f"402 Payment Required en {provider_name}",
                    request=response.request,
                    response=response,
                )

            if response.status_code in RETRY_ON_CODES:
                if intento < MAX_RETRIES:
                    wait = RETRY_BASE**intento
                    log.warning(
                        f"[{provider_name}] {context_label} -> HTTP {response.status_code} "
                        f"(intento {intento}/{MAX_RETRIES}), reintento en {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()

            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]
            return _extract_json_object(raw)

        except (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.HTTPStatusError,
            json.JSONDecodeError,
        ) as e:
            ultimo_error = e
            if isinstance(e, httpx.HTTPStatusError):
                status = e.response.status_code
                # 4xx (except 429) are usually request/config issues; retrying does not help.
                if status == 402 or (400 <= status < 500 and status != 429):
                    detail = (e.response.text or "")[:400]
                    raise RuntimeError(
                        f"[{provider_name}] {context_label} fallo con HTTP {status}. "
                        f"Detalle: {detail}"
                    ) from e
            if intento < MAX_RETRIES:
                wait = RETRY_BASE**intento
                log.warning(
                    f"[{provider_name}] {context_label} -> error {type(e).__name__} "
                    f"(intento {intento}/{MAX_RETRIES}), reintento en {wait:.1f}s"
                )
                await asyncio.sleep(wait)

    raise RuntimeError(
        f"[{provider_name}] {context_label} falló tras {MAX_RETRIES} intentos. "
        f"Último error: {ultimo_error}"
    )


async def call_model_json(
    system_prompt: str,
    user_message: str,
    provider_order: list[str] | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1024,
    context_label: str = "llm-call",
) -> tuple[dict, str, str]:
    providers = provider_order or DEFAULT_PROVIDER_ORDER
    errors: list[str] = []

    for provider_name in providers:
        try:
            config = _validate_provider_config(provider_name)
            payload = await _call_provider_json(
                provider_name=provider_name,
                config=config,
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=temperature,
                max_tokens=max_tokens,
                context_label=context_label,
            )
            return payload, provider_name, config["model"]
        except Exception as e:
            errors.append(f"{provider_name}: {e}")
            log.warning(f"Fallo en proveedor {provider_name} ({context_label}): {e}")

    raise RuntimeError(
        f"Todos los proveedores fallaron para '{context_label}'. "
        f"Detalle: {' | '.join(errors)}"
    )
