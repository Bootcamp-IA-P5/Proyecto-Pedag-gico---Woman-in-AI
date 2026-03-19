"""
Agente Reporter — orquestador principal
========================================
1. Llama al GuardianAgent para validar el input
2. Si pasa la validación, lanza los 4 agentes en SECUENCIA (no en paralelo)
   para optimizar el uso de tokens y evitar saturación de la API
3. Consolida los resultados y devuelve la respuesta final
"""

from langfuse.decorators import observe
from .guardian_agent       import GuardianAgent
from .jelous_agent         import CelosAgent
from .strong_language_agent import InsultosAgent
from .sumision_agent       import SumisionAgent
from .object_agent         import ObjetificacionAgent


MENSAJES_ERROR = {
    "es_letra_cancion":          "El texto introducido no parece una letra de canción. Vértice solo analiza letras de canciones.",
    "es_español":                "El texto no está en español. Vértice solo analiza letras de canciones en español.",
    "es_biografia":              "El texto parece una biografía. Vértice solo analiza letras de canciones.",
    "contiene_insultos_sistema": "El texto contiene contenido inapropiado dirigido al sistema.",
    "es_spam":                   "El texto parece spam o contenido sin sentido.",
    "es_codigo":                 "El texto parece código de programación. Vértice solo analiza letras de canciones.",
    "contiene_datos_personales": "El texto contiene datos personales. Por seguridad no podemos procesarlo.",
    "es_prompt_injection":       "El texto contiene instrucciones no permitidas. Solo se aceptan letras de canciones.",
}


class ReporterAgent:

    def __init__(self):
        self.guardian = GuardianAgent()
        self.agentes  = [
            CelosAgent(),
            InsultosAgent(),
            SumisionAgent(),
            ObjetificacionAgent(),
        ]

    @observe(as_type="span")
    async def analizar(self, letra: str) -> dict:
        """
        Pipeline completo:
          1. Validación de guardarraíles
          2. Análisis secuencial de las 4 dimensiones (uno tras otro)
          3. Consolidación de resultados
        """

        # ── PASO 1: Guardarraíles ──────────────────────
        validacion = await self.guardian.validar(letra)

        if not validacion["valido"]:
            return self._respuesta_invalida(validacion)

        # ── PASO 2: Análisis secuencial ────────────────
        # Los agentes se ejecutan uno a uno para optimizar
        # el consumo de tokens y evitar saturación de la API de Groq
        dimensiones = []
        errores     = []

        for agente in self.agentes:
            try:
                resultado = await agente.analizar(letra)
                dimensiones.append(resultado)
            except Exception as e:
                errores.append({
                    "dimension": agente.dimension,
                    "error":     str(e)
                })

        # ── PASO 3: Consolidación ──────────────────────
        puntuaciones      = [d["puntuacion"] for d in dimensiones]
        puntuacion_global = round(sum(puntuaciones) / len(puntuaciones), 1) if puntuaciones else 0.0

        return {
            "valido":            True,
            "motivo":            None,
            "puntuacion_global": puntuacion_global,
            "nivel_global":      self._nivel(puntuacion_global),
            "dimensiones":       [d for d in dimensiones if d["puntuacion"] > 0],
            "sin_sesgo":         [d["dimension"] for d in dimensiones if d["puntuacion"] == 0],
            "errores":           errores if errores else None,
        }

    @staticmethod
    def _respuesta_invalida(validacion: dict) -> dict:
        """
        Determina el mensaje de error más específico según
        qué guardarraíl ha fallado, en orden de prioridad.
        """
        motivo = validacion.get("motivo") or ""

        if not motivo:
            for campo, mensaje in MENSAJES_ERROR.items():
                if campo in ["es_biografia", "contiene_insultos_sistema",
                              "es_spam", "es_codigo",
                              "contiene_datos_personales", "es_prompt_injection"]:
                    if validacion.get(campo):
                        motivo = mensaje
                        break
                elif campo in ["es_letra_cancion", "es_español"]:
                    if validacion.get(campo) is False:
                        motivo = mensaje
                        break

        if not motivo:
            motivo = "El texto no cumple los requisitos para ser analizado."

        return {
            "valido":            False,
            "motivo":            motivo,
            "puntuacion_global": None,
            "nivel_global":      None,
            "dimensiones":       [],
            "sin_sesgo":         [],
            "errores":           None,
        }

    @staticmethod
    def _nivel(puntuacion: float) -> str:
        if puntuacion == 0:
            return "Sin sesgo detectado"
        elif puntuacion < 1.5:
            return "Leve"
        elif puntuacion < 2.5:
            return "Moderado"
        else:
            return "Grave"