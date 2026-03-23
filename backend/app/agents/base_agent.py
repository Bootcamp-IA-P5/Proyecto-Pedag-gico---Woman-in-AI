# backend/app/agents/base_agent.py
import asyncio
import json
import logging
import os
import re
import time
from abc import ABC

import httpx
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

PROVEEDORES = {
    "groq": {
        "url": os.getenv(
            "GROQ_URL",
            "https://api.groq.com/openai/v1/chat/completions",
        ),
        "key": os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY"),
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    },
    "gemini": {
        "url": os.getenv(
            "GEMINI_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        ),
        "key": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    },
    "mistral": {
        "url": os.getenv(
            "MISTRAL_URL",
            "https://api.mistral.ai/v1/chat/completions",
        ),
        "key": os.getenv("MISTRAL_API_KEY") or os.getenv("MISTRAL_KEY"),
        "model": os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
    },
    "together": {
        "url": os.getenv(
            "TOGETHER_URL",
            "https://api.together.xyz/v1/chat/completions",
        ),
        "key": os.getenv("TOGETHER_API_KEY"),
        "model": os.getenv(
            "TOGETHER_MODEL",
            "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        ),
    },
    "compat": {
        "url": os.getenv("COMPAT_LLM_URL"),
        "key": os.getenv("COMPAT_LLM_KEY"),
        "model": os.getenv("COMPAT_LLM_MODEL"),
    },
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
        "key": os.getenv("OPEN_ROUTER_KEY")
        or os.getenv("OPENROUTER_API_KEY"),
        "model": os.getenv("OPEN_ROUTER_MODEL", "openrouter/auto"),
    },
}
DEFAULT_PROVIDER_ORDER = [
    p.strip()
    for p in os.getenv(
        "LLM_PROVIDER_ORDER",
        "groq,gemini,mistral,github,openrouter,together,compat",
    ).split(",")
    if p.strip()
]


def _parse_concurrency_limit() -> int:
    raw = os.getenv("LLM_CONCURRENCY_LIMIT", "1")
    try:
        parsed = int(raw)
    except ValueError:
        log.warning(
            "LLM_CONCURRENCY_LIMIT invalido '%s'; usando 1 para evitar bloqueo.",
            raw,
        )
        return 1

    if parsed < 1:
        log.warning(
            "LLM_CONCURRENCY_LIMIT=%s no es valido; clamped a 1 para evitar bloqueo.",
            parsed,
        )
        return 1
    return parsed


# ── limitador de concurrencia global para llamadas a LLM ──
LLM_CONCURRENCY_LIMIT = _parse_concurrency_limit()
_llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY_LIMIT)


# ── Configuración de reintentos ────────────────────────────────────────────────
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
RETRY_BASE = float(os.getenv("LLM_RETRY_BASE", "2.0"))
RETRY_ON_CODES = {429, 500, 502, 503, 504}  # códigos que disparan reintento


_provider_rate_locks: dict[str, asyncio.Lock] = {}
_provider_next_allowed_at: dict[str, float] = {}


def _parse_positive_float(raw: str | None) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


def _provider_rpm(provider_name: str) -> float | None:
    specific = _parse_positive_float(os.getenv(f"LLM_RPM_{provider_name.upper()}"))
    if specific is not None:
        return specific
    return _parse_positive_float(os.getenv("LLM_RPM_DEFAULT"))


def _min_interval_seconds(provider_name: str) -> float:
    rpm = _provider_rpm(provider_name)
    interval_from_rpm = (60.0 / rpm) if rpm else 0.0
    floor_interval = _parse_positive_float(os.getenv("LLM_MIN_INTERVAL_SECONDS")) or 0.0
    return max(interval_from_rpm, floor_interval)


def _max_retry_after_seconds() -> float:
    raw = _parse_positive_float(os.getenv("LLM_MAX_RETRY_AFTER_SECONDS"))
    return raw if raw is not None else 45.0


async def throttle_provider_request(provider_name: str, context_label: str) -> None:
    min_interval = _min_interval_seconds(provider_name)
    if min_interval <= 0:
        return

    lock = _provider_rate_locks.setdefault(provider_name, asyncio.Lock())
    async with lock:
        now = time.monotonic()
        next_allowed = _provider_next_allowed_at.get(provider_name, now)
        wait_seconds = max(0.0, next_allowed - now)

        if wait_seconds > 0:
            log.info(
                "Throttle %s (%s): esperando %.2fs para respetar rate limit.",
                provider_name,
                context_label,
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)

        _provider_next_allowed_at[provider_name] = time.monotonic() + min_interval


def _rate_limit_header_snapshot(response: httpx.Response) -> str:
    interesting = [
        "retry-after",
        "x-ratelimit-limit-requests",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-reset-requests",
        "x-ratelimit-limit-tokens",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-tokens",
    ]
    found = []
    for key in interesting:
        value = response.headers.get(key)
        if value:
            found.append(f"{key}={value}")
    return ", ".join(found) if found else "sin cabeceras de rate-limit"


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


def _clean_json_text(raw: str | dict | list | None) -> str:
    if raw is None:
        raise ValueError("Respuesta vacia del modelo (content=None)")
    if not isinstance(raw, str):
        raw = json.dumps(raw, ensure_ascii=False)

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


def _extract_choice_content(response_json: dict) -> str | dict | list | None:
    choices = response_json.get("choices") or []
    if not choices:
        raise ValueError("Respuesta del proveedor sin 'choices'")

    message = choices[0].get("message") or {}
    content = message.get("content")

    # Some providers return content as a list of typed blocks.
    if isinstance(content, list):
        text_blocks: list[str] = []
        for block in content:
            if isinstance(block, dict):
                block_text = block.get("text") or block.get("content")
                if block_text:
                    text_blocks.append(str(block_text))
            elif isinstance(block, str):
                text_blocks.append(block)
        if text_blocks:
            return "\n".join(text_blocks)

    return content


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
            await throttle_provider_request(provider_name, context_label)

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
                    if response.status_code == 429:
                        retry_after_raw = response.headers.get("retry-after")
                        retry_after = _parse_positive_float(retry_after_raw)
                        if retry_after is not None:
                            if retry_after > _max_retry_after_seconds():
                                raise RuntimeError(
                                    f"[{provider_name}] {context_label} rate-limited con retry-after={retry_after:.1f}s; "
                                    "saltando proveedor para evitar bloqueo largo"
                                )
                            wait = max(wait, retry_after)

                        log.warning(
                            "[%s] %s -> HTTP 429. Rate headers: %s",
                            provider_name,
                            context_label,
                            _rate_limit_header_snapshot(response),
                        )
                    log.warning(
                        f"[{provider_name}] {context_label} -> HTTP {response.status_code} "
                        f"(intento {intento}/{MAX_RETRIES}), reintento en {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()

            response.raise_for_status()
            raw = _extract_choice_content(response.json())
            return _extract_json_object(raw)

        except (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.HTTPStatusError,
            json.JSONDecodeError,
            ValueError,
        ) as e:
            ultimo_error = e
            if isinstance(e, httpx.HTTPStatusError):
                status = e.response.status_code
                if status == 429:
                    log.warning(
                        "[%s] %s -> HTTP 429 (sin exito). Rate headers: %s",
                        provider_name,
                        context_label,
                        _rate_limit_header_snapshot(e.response),
                    )
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
    requested = provider_order or DEFAULT_PROVIDER_ORDER
    providers = [p for p in requested if p in PROVEEDORES]
    unknown = [p for p in requested if p not in PROVEEDORES]
    if unknown:
        log.warning("Proveedores ignorados (no implementados): %s", ", ".join(unknown))

    if not providers:
        raise RuntimeError(
            "No hay proveedores validos configurados. "
            "Revisa LLM_PROVIDER_ORDER y las claves disponibles."
        )

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
