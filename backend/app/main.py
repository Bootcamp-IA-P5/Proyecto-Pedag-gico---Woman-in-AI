from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from app.src.api.routes.analysis import router as analysis

load_dotenv()

app = FastAPI(
    title="VERTICE API",
    description="Análisis de sesgos de género en canciones",
    version="1.0.0"
)

default_origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "https://vertice-frontend.onrender.com",
]
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", ",".join(default_origins)).split(",")
    if origin.strip()
]
cors_origin_regex = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"https://.*\.ondigitalocean\.app",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis)

@app.get("/")
def health_check():
    return {"status": "ok", "proyecto": "VERTICE"}