<p align="center">
  <h1 align="center">🎵 Vértice</h1>
  <p align="center">
    <strong>Pipeline de datos + evaluación con LLMs para medir y analizar sesgos de género en letras de canciones en español</strong>
  </p>
  <p align="center">
    <a href="#-arquitectura">Arquitectura</a> •
    <a href="#-agentes-de-análisis">Agentes</a> •
    <a href="#-pipeline-de-datos">Pipeline</a> •
    <a href="#-instalación">Instalación</a> •
    <a href="#-uso">Uso</a> •
    <a href="#-licencia">Licencia</a>
  </p>
</p>

---

## 📋 Descripción

**Vértice** es un proyecto que combina *web scraping*, procesamiento de datos y **agentes de IA basados en LLMs** para detectar y cuantificar sesgos de género presentes en letras de canciones en español.

El sistema recopila letras de canciones populares de múltiples fuentes (Spotify, Deezer, YouTube, Genius), las normaliza, y las evalúa a través de 4 agentes especializados de IA que analizan distintas dimensiones del sesgo de género. Los resultados se almacenan en **Supabase** y se visualizan a través de un frontend en React.

---

## 🏗️ Arquitectura

```
Vertice/
├── backend/                 # API FastAPI + Agentes IA + Pipeline de datos
│   ├── app/
│   │   ├── agents/          # Agentes LLM de detección de sesgo
│   │   ├── src/
│   │   │   ├── config/      # Configuración de APIs externas
│   │   │   ├── scraper/     # Scrapers multi-fuente
│   │   │   └── processor/   # Normalización y carga a Supabase
│   │   ├── tests/           # Tests unitarios
│   │   └── main.py          # Punto de entrada FastAPI
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                # SPA React + Vite + TypeScript
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── data/                    # Datos del pipeline (raw → processed → final)
├── run.sh                   # Script de arranque rápido
└── requirements.txt
```

---

## 🤖 Agentes de Análisis

El núcleo del proyecto son **4 agentes especializados** que analizan las letras en paralelo usando el modelo **LLaMA 3.3 70B** a través de la API de **Groq**. Cada agente evalúa una dimensión distinta del sesgo de género y devuelve una puntuación de **0 a 3**:

| Agente | Dimensión | Qué detecta |
|--------|-----------|-------------|
| 🔴 `CelosAgent` | **Celos / Control** | Comportamiento posesivo, vigilancia, restricción de libertad, celos justificados como amor |
| 🟠 `InsultosAgent` | **Insultos / Lenguaje Degradante** | Insultos directos, lenguaje humillante, descalificaciones, normalización de trato vejatorio |
| 🟡 `SumisionAgent` | **Sumisión / Roles de Género** | Sumisión femenina, masculinidad tóxica, roles estereotipados, dinámicas de poder asimétricas |
| 🟣 `ObjetificacionAgent` | **Objetificación Sexual** | Cosificación directa e implícita, tratamiento como posesión, eliminación de agencia |

### Escala de puntuación

| Puntuación | Nivel | Significado |
|:-:|:-:|---|
| **0** | Sin sesgo | No se detectan indicadores en esta dimensión |
| **1** | Leve | Insinuación o lenguaje ambiguo |
| **2** | Moderado | Patrón claro pero no explícito |
| **3** | Grave | Explícito, reiterativo o normalizador |

### `ReporterAgent` — Orquestador

El `ReporterAgent` ejecuta los 4 agentes en **paralelo** con `asyncio.gather`, consolida los resultados y calcula una **puntuación global** (media de todas las dimensiones), junto con un nivel global: *Sin sesgo*, *Leve*, *Moderado* o *Grave*.

---

## 🔄 Pipeline de Datos

### 1. Scraping multi-fuente

| Fuente | Módulo | Datos obtenidos |
|--------|--------|-----------------|
| **Spotify** | `spotify_scraper.py` | Rankings, artistas, streams |
| **Deezer** | `deezer_scraper.py`, `scraping_deezer_*.py` | Rankings por país (Paraguay, etc.) |
| **YouTube** | `youtube_scraper.py`, `scraper_youtube*.py` | Rankings de tendencias |
| **Genius / BeautifulSoup** | `scraper_letras.py`, `scraping_BeautifSoup_*.py` | Letras de canciones |
| **LyricsGenius** | `lyrics_fetcher.py` | Letras vía API de Genius |
| **MusicBrainz** | `artist_gender.py` | Género del artista |

### 2. Procesamiento

- **Normalización** de letras (`normalizer.py`, `normalize_lyrics.py`): limpieza de texto, eliminación de artefactos del scraping, detección de idioma con `langdetect`
- **Tabla maestra** (`master_tables.py`): consolidación de datos de canciones con metadatos (país, posición, streams, año, género musical)

### 3. Almacenamiento

Los datos procesados se cargan en **Supabase** (`upload_to_supabase.py`) en tablas estructuradas:
- `songs` — catálogo de canciones con letras
- `top_songs` — posiciones en rankings por país

---

## ⚙️ Stack Tecnológico

### Backend
- **Python 3.11+**
- **FastAPI** + **Uvicorn** — API REST
- **Groq API** (LLaMA 3.3 70B) — Motor de los agentes de IA
- **Supabase** — Base de datos PostgreSQL gestionada
- **httpx** — Cliente HTTP async
- **Pydantic** — Validación de datos
- **BeautifulSoup4** — Web scraping
- **Spotipy** — API de Spotify
- **LyricsGenius** — API de Genius
- **MusicBrainzNGS** — API de MusicBrainz
- **langdetect** — Detección de idioma

### Frontend
- **React 18** + **TypeScript**
- **Vite 5** — Bundler y dev server
- **Tailwind CSS 3** — Estilos
- **React Router 6** — Navegación SPA
- **Vitest** — Tests unitarios

### Infraestructura
- **Docker** — Contenedores para frontend y backend
- **Nginx** — Servidor de estáticos del frontend en producción
- **GitHub Actions** — CI/CD
- **Dependabot** — Actualización automática de dependencias

---

## 🚀 Instalación

### Prerrequisitos

- Python 3.11+
- Node.js 20+
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes Python)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-org/vertice.git
cd vertice
```

### 2. Backend

```bash
cd backend

# Crear entorno virtual e instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves de API
```

### 3. Frontend

```bash
cd frontend

# Instalar dependencias
npm install
```

### 4. Variables de entorno

Crea un archivo `backend/.env` con las siguientes claves:

```env
# Base de datos
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_clave_de_supabase

# APIs de scraping
GENIUS_ACCESS_TOKEN=tu_token_de_genius
MUSICBRAINZ_EMAIL=tu_email

# API de IA
GROQ_API_KEY=tu_clave_de_groq
```

---

## 🎮 Uso

### Desarrollo local

```bash
# Backend (puerto 8000)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (puerto 5173)
cd frontend
npm run dev
```

### Docker

```bash
# Backend
cd backend
docker build -t vertice-backend .
docker run -p 8000:8000 --env-file .env vertice-backend

# Frontend
cd frontend
docker build -t vertice-frontend .
docker run -p 80:80 vertice-frontend
```

### Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Health check — mensaje de bienvenida |
| `GET` | `/docs` | Documentación interactiva (Swagger UI) |

---

## 🧪 Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

---

## 📂 Datos

El directorio `data/` organiza los datos en tres etapas del pipeline:

| Directorio | Descripción |
|------------|-------------|
| `data/raw/` | Datos brutos del scraping |
| `data/processed/` | Datos normalizados y limpiados |
| `data/final/` | Datos listos para análisis y visualización |

---

## 👥 Equipo

Proyecto desarrollado por **Bootcamp IA P5** — Women in AI.

| Nombre | LinkedIn | GitHub |
|--------|----------|--------|
| Mónica Gómez | [LinkedIn](https://www.linkedin.com/in/gomezgomonica/) | [GitHub](https://github.com/monigogo) |
| Jimena Flores Ticona | [LinkedIn](https://www.linkedin.com/in/jimena-flores-ticona/) | [GitHub](https://github.com/JIMENA-ft) |
| Aroa Mateo Gómez | [LinkedIn](https://www.linkedin.com/in/aroamateogomez/) | [GitHub](https://github.com/Arowi95) |
| Kasthlen Rodríguez Blandón | [LinkedIn](https://www.linkedin.com/in/kasthlen-rodriguez-blandon/) | [GitHub](https://github.com/Kasthlen) |

---

## 📄 Licencia

Este proyecto está bajo la [Licencia MIT](LICENSE).
