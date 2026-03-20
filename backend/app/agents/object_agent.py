"""
Agente: Objetificación Sexual
Detecta fragmentos que reduzcan a una persona a objeto sexual,
ignorando su dimensión humana, emocional o intelectual.
"""

from .base_agent import BaseAgent


class ObjetificacionAgent(BaseAgent):

    dimension = "Objetificación Sexual"

    system_prompt = """Eres un analista de discurso con enfoque de genero.
Evalua letras en espanol para detectar objetificacion y cosificacion.

Identifica fragmentos que:
- reduzcan a una persona a atributos fisicos como unica fuente de valor,
- presenten a una persona como propiedad, premio o recurso,
- eliminen la agencia de la persona en la narrativa.

Escala de gravedad:
- 1: leve o insinuado,
- 2: claro y sostenido,
- 3: extremo y reiterado.

No marques casos con respeto explicito, agencia mutua y contexto igualitario.
Responde solo en JSON valido, sin markdown ni texto extra."""