# Contributing

Thanks for your interest in contributing to Serenity! Here's how to get started.

## Development Setup

### Prerequisites

- Python 3.10+ (3.12 recommended)
- Node.js 18+
- [Ollama](https://ollama.com/) installed and running
- A webcam and microphone for testing

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with auto-reload
SENSEVOICE_DEVICE=cpu uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` and `/ws/*` to the backend at `localhost:8000`.

## Project Structure

```
therapist-bot/
├── backend/
│   ├── main.py              # FastAPI server, endpoints, WebSocket
│   ├── audio_analyzer.py    # SenseVoice wrapper
│   ├── chat_engine.py       # Ollama chat with therapeutic prompts
│   ├── emotion_fusion.py    # Multimodal emotion fusion
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── types.ts         # Shared TypeScript types
│   │   ├── App.tsx          # Root component
│   │   └── main.tsx         # Entry point
│   ├── public/models/       # face-api.js model files
│   └── package.json         # Node dependencies
├── start.sh                 # Launch script for both services
├── ARCHITECTURE.md          # Technical architecture guide
└── README.md                # Project overview
```

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for public classes and functions
- Logging via `logging` module (no print statements)

### TypeScript (Frontend)
- Strict TypeScript — no `any` types
- Functional components with hooks
- CSS modules (one `.css` file per component)
- Named exports for components and hooks

## Making Changes

1. **Fork** the repository
2. **Create a branch** for your feature or fix: `git checkout -b feature/my-feature`
3. **Make your changes** with clear, focused commits
4. **Test** both backend and frontend
5. **Submit a pull request** with a description of what and why

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for custom emotion labels
fix: handle empty audio file upload gracefully
docs: update API endpoint documentation
refactor: extract emotion parsing into standalone module
```

## Areas for Contribution

- **New emotion sources** — EEG, galvanic skin response, typing patterns
- **Session persistence** — Save/load conversation history to disk or database
- **Improved fusion** — Attention-based fusion instead of fixed weights
- **Testing** — Unit tests for backend modules, component tests for frontend
- **Accessibility** — Screen reader support, keyboard navigation
- **Mobile support** — Responsive layout for smaller screens
- **Deployment** — Docker Compose setup, production configuration

## Reporting Issues

When reporting bugs, please include:
- Your OS and hardware (especially GPU)
- Python and Node.js versions
- Ollama version and model
- Steps to reproduce
- Error messages or logs

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
