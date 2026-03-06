Vertice/                          ← Carpeta raíz del proyecto
│
├── 📄 .env                       ← 🔐 CONTRASEÑAS (nunca subir a GitHub)
├── 📄 requirements.txt           ← Lista de programas/librerías que necesita el proyecto
├── 📄 run.sh                     ← Botón de arranque: ejecuta todo el proyecto de una vez
├── 📄 README.md                  ← Descripción del proyecto para quien llega nuevo
│
├── 📁 backend/                   ← TODO EL CEREBRO DEL PROYECTO (Python)
│   ├── 📄 .env                   ← 🔐 Contraseñas para conectarse a Spotify, Genius, etc.
│   ├── 📄 pyproject.toml         ← Configuración técnica del proyecto Python
│   │
│   └── 📁 app/
│       ├── 📄 main.py            ← Puerta de entrada del programa (aún en construcción)
│       │
│       ├── 📁 src/               ← Donde vive todo el código importante
│       │   │
│       │   ├── 📁 config/        ← 🔑 LLAVES Y CONTRASEÑAS
│       │   │   ├── spotify_config.py    ← Conexión con Spotify
│       │   │   ├── deezer_config.py     ← Conexión con Deezer
│       │   │   ├── genius_config.py     ← Conexión con Genius (letras)
│       │   │   └── supabase_client.py   ← Conexión con la base de datos
│       │   │
│       │   ├── 📁 scraper/       ← 🌐 RECOLECTORES (van a buscar datos a internet)
│       │   │   ├── spotify_scraper.py          ← Busca canciones top en Spotify
│       │   │   ├── deezer_scraper.py           ← Busca canciones top en Deezer
│       │   │   ├── lyrics_scraper.py           ← Busca letras de canciones en Genius
│       │   │   ├── scraping_spoti_paraguay.py  ← Ejecuta el proceso completo de Spotify (Paraguay)
│       │   │   ├── scraping_deezer_paraguay.py ← Ejecuta el proceso completo de Deezer (Paraguay)
│       │   │   ├── scraping_deezer_todos.py    ← ⭐ NUEVO: Deezer para TODOS los países a la vez
│       │   │   └── scraping_lyrics.py          ← Busca letras de todas las canciones pendientes
│       │   │
│       │   ├── 📁 processor/     ← 🧹 LIMPIADORES Y GUARDADORES
│       │   │   ├── normalizer.py          ← ⭐ NUEVO: Limpia datos con IA (Groq) antes de guardar
│       │   │   ├── master_tables.py       ← ⭐ NUEVO: Guarda en las tablas maestras (artistas y canciones)
│       │   │   └── upload_to_supabase.py  ← Guarda todos los datos en la base de datos
│       │   │
│       │   └── 📁 evaluation/    ← 🔬 ANÁLISIS (reservado para analizar sesgo de género en letras)
│       │
│       ├── 📁 tests/             ← ✅ PRUEBAS AUTOMÁTICAS
│       │   ├── test_spotify_scraper.py  ← Verifica que Spotify funciona correctamente
│       │   └── test_lyrics_scraper.py   ← Verifica que la búsqueda de letras funciona
│       │
│       ├── 📁 docs/              ← 📖 Documentación (en construcción)
│       └── 📁 notebooks/         ← 📓 Cuadernos de experimentos (en construcción)
│
├── 📁 frontend/                  ← 🖥️ LA PANTALLA (lo que ve el usuario, en construcción)
│   └── 📁 src/
│       ├── App.tsx               ← Pantalla principal (aún vacía)
│       └── main.tsx              ← Punto de arranque de la pantalla
│
└── 📁 data/                      ← 💾 DATOS EN LOCAL
    ├── raw/                      ← Datos tal como llegan de internet (sin tocar)
    ├── processed/                ← Datos después de limpiarlos
    └── final/                    ← Datos listos para analizar