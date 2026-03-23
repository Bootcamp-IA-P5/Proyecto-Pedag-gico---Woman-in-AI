# 🚀 GUÍA DE DEPLOYMENT: VERTICE API en Digital Ocean

## 📋 Pre-requisitos

- ✅ Acceso a Digital Ocean con proyecto creado
- ✅ Cuenta de GitHub (usuario autenticado)
- ✅ Todas las API keys configuradas (Groq, Gemini, Supabase, etc.)
- ✅ Permisos en la organización de GitHub para conectar repos

---

## 📌 PASO 1: Conectar GitHub a Digital Ocean

### 1.1 En Digital Ocean Console

1. Ve a tu proyecto: https://cloud.digitalocean.com/projects
2. Click en **"Apps"** en el sidebar
3. Click en **"Create Apps"**
4. Selecciona **"GitHub"**
5. Haz click en **"Authorize"** para conectar tu cuenta de GitHub
6. Digital Ocean te pedirá permisos para acceder a tus repos
7. Confirma los permisos

### 1.2 Selecciona el repositorio

1. En el dropdown, busca y selecciona: **`Bootcamp-IA-P5/Vertice`**
2. Selecciona la rama: **`feature-set-up-backend-analysis-engine`**
3. Click en **"Next"**

---

## 🔧 PASO 2: Configurar la Aplicación

### 2.1 Source Code Settings

- **Repository**: `Bootcamp-IA-P5/Vertice`
- **Branch**: `feature-set-up-backend-analysis-engine`
- **Source Directory**: `/backend`

### 2.2 Build Settings

Digital Ocean debería detectar automáticamente el Dockerfile:

```
Build Command: (dejar en blanco, usa Dockerfile)
Dockerfile PATH: Dockerfile
```

---

## 🔑 PASO 3: Configurar Variables de Entorno

### 3.1 En Digital Ocean Console

1. En la pantalla de configuración, busca la sección **"Environment"** o **"Variables"**
2. Haz click en **"Edit"** (si ya existen) o **"Add"**
3. Agrega TODAS las siguientes variables:

```bash
# SUPABASE
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=your_key

# LLM PROVIDERS (mínimo: Groq + 1 fallback)
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile

GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.0-flash

MISTRAL_API_KEY=your_mistral_key
MISTRAL_MODEL=mistral-small-latest

# Fallbacks (agregar al menos uno más)
GITHUB_TOKEN=your_github_token
TOGETHER_API_KEY=your_together_key
OPENROUTER_API_KEY=your_openrouter_key

# SPOTIFY (opcional, para scrapeo)
SPOTIPY_CLIENT_ID=your_spotify_id
SPOTIPY_CLIENT_SECRET=your_spotify_secret

# MUSICBRAINZ
MUSICBRAINZ_EMAIL=your_email@example.com

# ANALYSIS CONFIG
LLM_TIMEOUT_SECONDS=25
LLM_MAX_RETRIES=3
LLM_RETRY_BASE=2.0
ANALYSIS_GUARDIAN_STRICT=false
ANALYSIS_PIPELINE_MODE=simple
ANALYSIS_MIN_COVERAGE_FOR_CONCLUSIVE=0.75

# PORT
PORT=8080
```

⚠️ **NOTA**: Digital Ocean asigna automáticamente el puerto. El Dockerfile expone puerto 8000, pero DO puede mapearlo a otro puerto públicamente.

---

## 📦 PASO 4: Configurar la Aplicación en DO

### 4.1 Resources Settings

```
- Type: Web Service
- Instance Size: Basic ($12/mes) o Professional ($25/mes)
- HTTP Routes: /
```

### 4.2 HTTPS

Digital Ocean crea certificado automáticamente. El backend será accesible en:

```
https://vertice-api-[random-id].ondigitalocean.com
```

---

## ✅ PASO 5: Desplegar

1. Click en **"Deploy"** (o "Create" si es la primera vez)
2. Digital Ocean:
   - Clonará el repo
   - Construirá la Docker image
   - Desplegará en contenedor
   - Expondrá la URL pública

⏳ El despliegue toma **3-5 minutos**

---

## 🧪 PASO 6: Validar el Deployment

### 6.1 Verificar que el servidor está corriendo

```bash
# Obtén la URL pública de tu app (visible en DO console)
# Reemplaza con tu URL real:
curl https://vertice-api-YOUR-ID.ondigitalocean.com/
```

Deberías ver:

```json
{ "status": "ok", "proyecto": "VERTICE" }
```

### 6.2 Acceder a la documentación

```
https://vertice-api-YOUR-ID.ondigitalocean.com/docs
```

Debería abrirse Swagger UI con todos los endpoints

---

## 🔗 PASO 7: Actualizar Frontend para apuntar al backend

Una vez que tengas la URL pública de Digital Ocean, necesitas actualizar el frontend:

### 7.1 Actualizar CORS en backend

En el archivo `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://tu-frontend-url.com",  # ← Agregar URL del frontend
        "https://vertice-ai-[id].ondigitalocean.com",  # Tu URL en DO
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7.2 Actualizar URL en Frontend

En `frontend/src/api/client.ts` (o donde hagas las llamadas HTTP):

```typescript
const API_URL =
  process.env.VITE_API_URL || "https://vertice-api-YOUR-ID.ondigitalocean.com";
```

O en variables de entorno del frontend (`.env`):

```bash
VITE_API_URL=https://vertice-api-YOUR-ID.ondigitalocean.com
```

---

## 🔄 PASO 8: Despliegues Automáticos

Una vez conectado GitHub, cada push a `feature-set-up-backend-analysis-engine` dispara automáticamente:

1. ✅ Build de Docker image
2. ✅ Test de build
3. ✅ Deploy a contenedor
4. ✅ Health check automático

Puedes ver el historial de deploys en Digital Ocean Console → Apps → [Tu App] → Deployments

---

## 📊 Monitoreo

### En Digital Ocean Console:

- **Logs**: Apps → [Tu App] → Logs (ver output del servidor)
- **Metrics**: CPU, Memoria, Requests
- **Build Logs**: Ver logs de compilación Docker

### Health Check

Digital Ocean automáticamente:

- Revisa que el servidor respone a `GET /`
- Reinicia si falla
- Redirige tráfico si hay error

---

## 🆘 Troubleshooting

### ❌ Build falla: "ModuleNotFoundError"

```
Solución: Verificar que pyproject.toml está en backend/
          Digital Ocean debe buildear desde /backend

En app.yaml (si aparece):
root: /backend
```

### ❌ App crashes con error de env vars

```
Solución: Verificar que TODAS las variables están en:
          DO Console → Apps → [Tu App] → Settings → Environment

          Revisar logs: Apps → [Tu App] → Logs
```

### ❌ CORS error en frontend

```
Solución: Actualizar allow_origins en backend/app/main.py
          con la URL exacta del frontend

          Hacer push a GitHub → Auto-redeploy
```

### ❌ Timeout en requests

```
Solución: Ajustar LLM_TIMEOUT_SECONDS a valor mayor
          ej: LLM_TIMEOUT_SECONDS=45

          Aumentar Instance Size en DO (más CPU/RAM)
```

---

## 📝 Checklist Final

- ✅ GitHub conectado a Digital Ocean
- ✅ Variables de entorno configuradas
- ✅ Backend responde a `/` endpoint
- ✅ Swagger UI accesible en `/docs`
- ✅ Frontend apunta a la URL correcta
- ✅ CORS configurado correctamente
- ✅ Logs se ven sin errores

---

## 🎯 Próximos Pasos (Opcional)

1. **Deploy del Frontend**: Usar Vercel, Netlify o Digital Ocean también
2. **Base de Datos**: Supabase ya está configurado
3. **CI/CD adicional**: Agregar tests antes de deploy
4. **Monitoreo**: Integrar con Datadog, New Relic, etc.

---

**¡Tu aplicación estará lista para producción!** 🚀
