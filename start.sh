#!/bin/bash
# ─── Therapist Bot Start Script ───────────────────────────────────────────────
# Starts both backend (FastAPI) and frontend (React+Vite) servers.
# Prerequisites:
#   1. Ollama running: ollama serve
#   2. Python venv with dependencies: pip install -r backend/requirements.txt
#   3. Node dependencies: cd frontend && npm install

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🧠 Therapist Bot — Starting...${NC}"
echo ""

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama is not running. Please start it first:${NC}"
    echo "   ollama serve"
    exit 1
fi
echo -e "${GREEN}✓ Ollama is running${NC}"

# Check gemma3 model
if ! ollama list 2>/dev/null | grep -q "gemma3"; then
    echo -e "${YELLOW}⚠ gemma3 model not found. Pulling gemma3:4b...${NC}"
    ollama pull gemma3:4b-it-q8_0
fi
echo -e "${GREEN}✓ Gemma3 model available${NC}"

# Start backend
echo -e "\n${GREEN}Starting backend (FastAPI on :8000)...${NC}"
cd "$SCRIPT_DIR/backend"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
SENSEVOICE_DEVICE=cpu uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo -e "${GREEN}Starting frontend (Vite on :5173)...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🧠 Therapist Bot is running!${NC}"
echo -e "${GREEN}  Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}  Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}  API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo "Press Ctrl+C to stop both servers."

# Trap cleanup
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Done.${NC}"
}
trap cleanup EXIT INT TERM

wait
