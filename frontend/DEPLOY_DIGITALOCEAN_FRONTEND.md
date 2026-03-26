# Deploy frontend en DigitalOcean (desde rama feature)

## 1) Crear app

1. DigitalOcean -> Apps -> Create App
2. Repo: `Bootcamp-IA-P5/Vertice`
3. Branch: `feature-set-up-backend-analysis-engine`
4. Source Directory: `frontend`
5. Tipo: Dockerfile

## 2) Build y runtime

- Dockerfile: `frontend/Dockerfile`
- HTTP Port: `80`
- Auto deploy on push: ON

## 3) Variables de entorno (IMPORTANTES)

En App Settings -> Environment Variables agrega:

- `VITE_API_BASE_URL` = `https://vertice-x243o.ondigitalocean.app`
- `VITE_SUPABASE_URL` = tu url de supabase
- `VITE_SUPABASE_ANON_KEY` = tu anon key de supabase
- `PORT` = `80`

Nota: las variables `VITE_*` se usan en build de Vite.

## 4) Deploy

- Haz click en Deploy / Create Resources
- Espera build + release
- Copia la URL pública del frontend

## 5) Verificación rápida

- Abre la URL frontend
- Prueba análisis manual con letra demo
- Debe responder sin error de conexión

Si aparece error CORS en navegador:

- agrega la URL del frontend a `CORS_ORIGINS` del backend en DO
- redeploy backend
