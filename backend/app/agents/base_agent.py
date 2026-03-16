# backend/app/agents/base_agent.py
import asyncio
import json
import logging
import os
from abc import ABC

import httpx
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

PROVEEDORES = {
    "openrouter": {
        "url":   os.getenv("OPEN_ROUTER_URL"),
        "key":   os.getenv("OPEN_ROUTER_KEY"),
        "model": os.getenv("OPEN_ROUTER_MODEL", "sourceful/riverflow-v2-pro"),
    },
}
# ── limitador de concurrencia global para llamadas a LLM ──
LLM_CONCURRENCY_LIMIT = int(os.getenv("LLM_CONCURRENCY_LIMIT", 1))
_llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY_LIMIT)


# ── Configuración de reintentos ────────────────────────────────────────────────
MAX_RETRIES    = 3       # intentos máximos por llamada
RETRY_BASE     = 2.0     # segundos base (se multiplica exponencialmente)
RETRY_ON_CODES = {429, 500, 502, 503, 504}  # códigos que disparan reintento


class BaseAgent(ABC):

    dimension:     str = ""
    system_prompt: str = ""

    async def analizar(self, letra: str, proveedor: str = "openrouter") -> dict:
        config = PROVEEDORES.get(proveedor)
        if not config:
            raise ValueError(f"Proveedor desconocido: {proveedor}")

        missing = [k for k in ("url", "key", "model") if not config.get(k)]
        if missing:
            raise ValueError(
                f"Configuración incompleta para '{proveedor}': "
                f"faltan {', '.join(missing)}. Revisa las variables de entorno."
            )

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

        ultimo_error = None

        for intento in range(1, MAX_RETRIES + 1):
            try:
                async with _llm_semaphore:
                    async with httpx.AsyncClient(timeout=30) as client:
                     response = await client.post(
                        config["url"],
                        headers={
                            "Authorization": f"Bearer {config['key']}",
                            "Content-Type":  "application/json",
                        },
                        json={
                            "model":       config["model"],
                            "temperature": 0.1,
                            "max_tokens":  1024,
                            "messages": [
                                {"role": "system", "content": self.system_prompt},
                                {"role": "user",   "content": user_message},
                            ],
                        },
                    )

                # 402 = sin crédito → no reintenta, falla inmediato
                if response.status_code == 402:
                    raise httpx.HTTPStatusError(
                        f"402 Payment Required — recarga crédito en {proveedor}",
                        request=response.request,
                        response=response,
                    )

                # 429 / 5xx → reintento con backoff exponencial
                if response.status_code in RETRY_ON_CODES:
                    wait = RETRY_BASE ** intento
                    log.warning(
                        f"[{proveedor}] {self.dimension} → "
                        f"HTTP {response.status_code} "
                        f"(intento {intento}/{MAX_RETRIES}), "
                        f"reintentando en {wait:.1f}s..."
                    )
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()

                raw = response.json()["choices"][0]["message"]["content"].strip()

                try:
                    resultado = json.loads(raw)
                except json.JSONDecodeError:
                    raw_clean = raw.replace("```json", "").replace("```", "").strip()
                    resultado = json.loads(raw_clean)

                validado = self._validar(resultado)
                validado["modelo"] = f"{proveedor}/{config['model']}"
                # evitar saturar APIs
                await asyncio.sleep(2)
                
                return validado

            except httpx.HTTPStatusError as e:
                ultimo_error = e
                # 402 → no reintenta
                if e.response.status_code == 402:
                    raise
                # otros → reintenta si quedan intentos
                if intento < MAX_RETRIES:
                    wait = RETRY_BASE ** intento
                    log.warning(
                        f"[{proveedor}] {self.dimension} → "
                        f"HTTP {e.response.status_code} "
                        f"(intento {intento}/{MAX_RETRIES}), "
                        f"reintentando en {wait:.1f}s..."
                    )
                    await asyncio.sleep(wait)

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                ultimo_error = e
                if intento < MAX_RETRIES:
                    wait = RETRY_BASE ** intento
                    log.warning(
                        f"[{proveedor}] {self.dimension} → "
                        f"Timeout/conexión (intento {intento}/{MAX_RETRIES}), "
                        f"reintentando en {wait:.1f}s..."
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"[{proveedor}] {self.dimension} falló tras {MAX_RETRIES} intentos. "
            f"Último error: {ultimo_error}"
        )

    def _validar(self, resultado: dict) -> dict:
        return {
            "dimension":     resultado.get("dimension",     self.dimension),
            "puntuacion":    max(0, min(3, int(resultado.get("puntuacion", 0)))),
            "fragmentos":    resultado.get("fragmentos",    []),
            "justificacion": resultado.get("justificacion", ""),
        }