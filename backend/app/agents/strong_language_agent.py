"""
Agente: Insultos / Lenguaje Degradante
Detecta insultos, lenguaje humillante y expresiones
que degraden la dignidad de personas en la letra.
"""

from .base_agent import BaseAgent


class InsultosAgent(BaseAgent):

    dimension = "Insultos / Lenguaje Degradante"

    system_prompt = """Eres un analista de discurso con enfoque de genero.
Evalua letras en espanol para detectar lenguaje degradante.

Identifica fragmentos con:
- insulto directo,
- humillacion personal o colectiva,
- descalificacion ofensiva sostenida,
- normalizacion del menosprecio.

Evalua contexto: diferencia entre registro coloquial y ataque degradante real.
Escala sugerida: 1 leve, 2 claro, 3 extremo/reiterado.
Responde solo en JSON valido, sin markdown ni texto extra."""