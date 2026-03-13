# backend/app/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from app.src.api.routes.analysis import router as analysis

load_dotenv()

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"]
)

app = FastAPI(
    title="VERTICE API",
    description="Análisis de sesgos de género en canciones",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",                   # frontend local
        "https://vertice-frontend.onrender.com",   # frontend en Render
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar routers
app.include_router(analysis)

@app.get("/")
def health_check():
    return {"status": "ok", "proyecto": "VERTICE"}