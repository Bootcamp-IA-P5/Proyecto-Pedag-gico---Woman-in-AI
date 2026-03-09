"""
backend/app/src/config/groq_config.py
Cliente de Groq para normalización de letras con LLM.
"""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"


def obtener_cliente_groq() -> Groq:
    if not GROQ_API_KEY:
        raise EnvironmentError("❌ Falta GROQ_API_KEY en .env")
    return Groq(api_key=GROQ_API_KEY)
