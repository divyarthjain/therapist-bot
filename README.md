# Serenity — Multimodal AI Therapeutic Companion

A privacy-first, locally-run AI therapist that detects your emotions through **voice** and **facial expressions** in real-time, then adapts its therapeutic responses accordingly. Everything runs on your machine — no data leaves your device.

![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Node](https://img.shields.io/badge/node-18%2B-green)

## Features

- **Audio Emotion Analysis** — [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) analyzes voice recordings for emotion (happy, sad, angry, fearful, etc.), language detection, and speech-to-text transcription across 50+ languages
- **Video Emotion Analysis** — [face-api.js](https://github.com/vladmandic/face-api) runs entirely in your browser to detect facial expressions from your webcam. No video is ever sent to a server.
- **Emotion Fusion Engine** — Weighted late fusion combines audio (60%) and video (40%) signals with exponential time decay for accurate emotional state tracking
- **Therapeutic Chat** — Local LLM via [Ollama](https://ollama.com/) (Gemma 3 4B) provides empathetic, emotion-aware responses using CBT and active listening techniques
- **Streaming Responses** — WebSocket-based real-time token streaming for natural conversational flow
- **Multilingual** — Supports Hindi, English, Japanese, Korean, Chinese, Cantonese, and more
- **Crisis Safety** — Built-in detection of crisis language with automatic provision of helpline resources
- **Incongruence Detection** — Flags when voice emotion and facial expression disagree (e.g., saying "I'm fine" while looking sad)

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.12 recommended |
| Node.js | 18+ | For the React frontend |
| [Ollama](https://ollama.com/) | Latest | Local LLM runtime |
| Webcam | — | For facial emotion detection |
| Microphone | — | For voice emotion analysis |
| RAM | 8GB+ | 16GB+ recommended for SenseVoice + Ollama |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/divyarthjain/therapist-bot.git
cd therapist-bot
```

### 2. Start Ollama and pull the model

```bash
ollama serve                    # Start Ollama (if not already running)
ollama pull gemma3:4b-it-q8_0   # Pull the Gemma 3 4B model (~5GB)
```

### 3. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** First run downloads the SenseVoice model (~900MB) from ModelScope. This is a one-time download.

### 4. Set up the frontend

```bash
cd frontend
npm install
```

### 5. Run everything

```bash
# From the project root
chmod +x start.sh
./start.sh
```

Or start services individually:

```bash
# Terminal 1 — Backend
cd backend && source venv/bin/activate
SENSEVOICE_DEVICE=cpu uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

### 6. Open in browser

Navigate to **http://localhost:5173**

## Usage

| Action | How |
|--------|-----|
| **Chat** | Type a message in the chat panel and press Enter or click Send |
| **Voice** | Click the microphone button to record audio → transcription + emotion analysis |
| **Webcam** | Toggle the camera on in the right panel → real-time facial expression detection |
| **View Emotions** | Left panel shows the fused emotion state with per-modality breakdowns |

The therapist adapts its responses based on your detected emotional state. If it detects sadness in your voice but you type "I'm fine", it will gently acknowledge the incongruence.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check — SenseVoice and Ollama status |
| `/api/analyze-audio` | POST | Upload audio file → transcription + emotion |
| `/api/emotion-update` | POST | Send video emotion update from browser |
| `/api/chat` | POST | Non-streaming chat with emotion context |
| `/ws/chat` | WebSocket | Streaming chat with real-time emotion updates |

See the [Architecture Guide](ARCHITECTURE.md) for detailed API contracts.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SENSEVOICE_DEVICE` | `mps` (Apple Silicon) or `cpu` | Device for SenseVoice inference |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma3:4b-it-q8_0` | LLM model name |

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite 7 |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Audio Analysis** | FunAudioLLM SenseVoice (via FunASR) |
| **Video Analysis** | face-api.js (@vladmandic/face-api) — runs in-browser |
| **LLM** | Ollama + Gemma 3 4B (Q8_0 quantization) |
| **Communication** | WebSocket (streaming), REST (audio upload) |
| **Emotion Fusion** | Weighted late fusion with exponential time decay |

## Privacy

- **Audio**: Sent to the local backend for SenseVoice analysis. Never leaves your machine.
- **Video**: Processed entirely in the browser via face-api.js. No video frames are ever transmitted.
- **Chat**: All LLM inference runs locally via Ollama. No cloud APIs.
- **No telemetry**: Zero analytics, tracking, or data collection of any kind.

## License

This project is licensed under the [Apache License 2.0](LICENSE).

## Acknowledgments

- [FunAudioLLM/SenseVoice](https://github.com/FunAudioLLM/SenseVoice) — Audio emotion recognition and multilingual transcription
- [vladmandic/face-api](https://github.com/vladmandic/face-api) — Browser-based facial expression detection
- [Ollama](https://ollama.com/) — Local LLM inference
- [Google Gemma](https://ai.google.dev/gemma) — Multilingual language model
