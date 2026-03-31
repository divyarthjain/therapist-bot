#!/bin/bash
# ─── Therapist Bot Start Script ───────────────────────────────────────────────
# Builds the frontend and serves the whole app from FastAPI.
# Prerequisites:
#   1. GEMINI_API_KEY configured in .env or shell
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

# Check Gemini key
if [ -z "${GEMINI_API_KEY:-}" ] && [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY is not configured.${NC}"
    echo "   Copy .env.example to .env and set GEMINI_API_KEY"
    exit 1
fi
echo -e "${GREEN}✓ Gemini configuration found${NC}"

# Build frontend
echo -e "\n${GREEN}Building frontend bundle...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run build

# Start backend
echo -e "\n${GREEN}Starting unified app (FastAPI on :8000)...${NC}"
cd "$SCRIPT_DIR/backend"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🧠 Therapist Bot is running!${NC}"
echo -e "${GREEN}  App:      http://127.0.0.1:8000${NC}"
echo -e "${GREEN}  API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo "Press Ctrl+C to stop both servers."

# Trap cleanup
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    echo -e "${GREEN}Done.${NC}"
}
trap cleanup EXIT INT TERM

wait
