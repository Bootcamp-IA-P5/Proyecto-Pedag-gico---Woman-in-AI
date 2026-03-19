from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.src.api.routes.analysis import router as analysis

load_dotenv()

app = FastAPI(
    title="VERTICE API",
    description="Análisis de sesgos de género en canciones",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://vertice-frontend.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis)

@app.get("/")
def health_check():
    return {"status": "ok", "proyecto": "VERTICE"}