#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Iniciando KUMO VISION - Backend y Frontend${NC}\n"

# Matar procesos previos
echo -e "${YELLOW}Limpiando procesos previos...${NC}"
pkill -f "python.*api.py" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# Terminal 1: Backend
echo -e "${GREEN}✅ Iniciando Backend (Puerto 8000)...${NC}"
cd /workspaces/proyecto12-grupo2
python src/api.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Esperar a que el backend esté listo
sleep 5

# Verificar que el backend responde
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend está corriendo correctamente${NC}\n"
else
    echo -e "${RED}❌ Backend no responde en puerto 8000${NC}"
    echo "Logs del backend:"
    cat /tmp/backend.log
    exit 1
fi

# Terminal 2: Frontend
echo -e "${GREEN}✅ Iniciando Frontend (Puerto 5173)...${NC}"
cd /workspaces/proyecto12-grupo2/frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

sleep 5

echo -e "${GREEN}✅ ¡Todo está listo!${NC}\n"
echo -e "${YELLOW}URLs:${NC}"
echo -e "  Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "  Docs API: ${GREEN}http://localhost:8000/docs${NC}\n"

echo -e "${YELLOW}Presiona CTRL+C para detener${NC}"

# Mantener el script corriendo
wait
