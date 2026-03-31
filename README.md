# Serenity — Multimodal AI Therapeutic Companion

A privacy-first multimodal AI therapist that detects your emotions through **voice** and **facial expressions** in real-time, then adapts its therapeutic responses accordingly. Audio emotion analysis runs locally, live STT/TTS run through Deepgram, and therapeutic reasoning is powered through Gemini with a strong system instruction.

![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Node](https://img.shields.io/badge/node-18%2B-green)

## Features

- **Audio Emotion Analysis** — [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) analyzes voice recordings for emotion (happy, sad, angry, fearful, etc.), language detection, and speech-to-text transcription across 50+ languages
- **Video Emotion Analysis** — [face-api.js](https://github.com/vladmandic/face-api) runs entirely in your browser to detect facial expressions from your webcam. No video is ever sent to a server.
- **Emotion Fusion Engine** — Weighted late fusion combines audio (60%) and video (40%) signals with exponential time decay for accurate emotional state tracking
- **Therapeutic Chat** — Gemini API provides empathetic, system-prompted responses tuned for therapeutic active listening, CBT-style reflection, and emotion-aware follow-up
- **Streaming Responses** — WebSocket-based real-time token streaming for natural conversational flow
- **Live Call Mode** — Continuous microphone turn-taking with a dedicated full-screen session UI, live webcam emotion feed, and spoken responses
- **Multilingual** — Supports Hindi, English, Japanese, Korean, Chinese, Cantonese, and more
- **Crisis Safety** — Built-in detection of crisis language with automatic provision of helpline resources
- **Incongruence Detection** — Flags when voice emotion and facial expression disagree (e.g., saying "I'm fine" while looking sad)

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.12 recommended |
| Node.js | 18+ | For the React frontend build |
| Webcam | — | For facial emotion detection |
| Microphone | — | For voice emotion analysis |
| Gemini API key | — | Required for chat generation |
| Deepgram API key | — | Required for live STT and TTS |
| RAM | 8GB+ | 16GB+ recommended for SenseVoice + TTS |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/divyarthjain/therapist-bot.git
cd therapist-bot
```

### 2. Configure Gemini + Deepgram

```bash
cp .env.example .env
```

Then set `GEMINI_API_KEY` and `DEEPGRAM_API_KEY` in `.env`.

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

### 5. Run the unified app

```bash
chmod +x start.sh
./start.sh
```

This builds the React frontend and serves it from FastAPI, so you only need one URL.

Or, if you want to build and run manually:

```bash
cd frontend && npm run build
cd ../backend && source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 6. Open in browser

Navigate to **http://127.0.0.1:8000**

## Usage

| Action | How |
|--------|-----|
| **Chat** | Type a message in the chat panel and press Enter or click Send |
| **Voice Call** | Click the microphone button to start a continuous live call with turn-taking voice input/output |
| **Webcam** | The camera feed stays live and sends continuous facial-expression updates to the fusion engine |
| **View Emotions** | The call screen and chat flow show fused emotion state with voice/face breakdowns |

The therapist adapts its responses based on your detected emotional state. If it detects sadness in your voice but you type "I'm fine", it will gently acknowledge the incongruence.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check — SenseVoice, Gemini, ASR, SER, and TTS status |
| `/api/analyze-audio` | POST | Upload audio file → transcription + emotion |
| `/api/emotion-update` | POST | Send video emotion update from browser |
| `/api/chat` | POST | Non-streaming chat with emotion context |
| `/ws/chat` | WebSocket | Streaming chat with real-time emotion updates |

See the [Architecture Guide](ARCHITECTURE.md) for detailed API contracts.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SENSEVOICE_DEVICE` | `mps` (Apple Silicon) or `cpu` | Device for SenseVoice inference |
| `GEMINI_API_KEY` | — | Gemini API key for therapeutic chat |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `GEMINI_API_BASE` | `https://generativelanguage.googleapis.com/v1beta` | Optional Gemini API base override |
| `DEEPGRAM_API_KEY` | — | Deepgram API key for live STT + TTS |
| `DEEPGRAM_STT_MODEL` | `nova-3` | Deepgram transcription model |
| `DEEPGRAM_TTS_MODEL` | `aura-2-thalia-en` | Deepgram speech model |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite 7 |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Audio Analysis** | FunAudioLLM SenseVoice (via FunASR) |
| **Video Analysis** | face-api.js (@vladmandic/face-api) — runs in-browser |
| **Live Voice I/O** | Deepgram STT (`nova-3`) + Deepgram TTS (`aura-2-thalia-en`) |
| **LLM** | Gemini API with system instructions |
| **Communication** | FastAPI-served SPA + WebSocket (streaming) + REST |
| **Emotion Fusion** | Weighted late fusion with exponential time decay |

## Privacy

- **Audio**: Sent to the local backend for emotion analysis and forwarded to Deepgram for live transcription/speech synthesis.
- **Video**: Processed entirely in the browser via face-api.js. No video frames are ever transmitted.
- **Chat**: Therapeutic chat requests are sent to Gemini.
- **No telemetry**: Zero analytics, tracking, or data collection of any kind.

## License

This project is licensed under the [Apache License 2.0](LICENSE).

## Acknowledgments

- [FunAudioLLM/SenseVoice](https://github.com/FunAudioLLM/SenseVoice) — Audio emotion recognition and multilingual transcription
- [vladmandic/face-api](https://github.com/vladmandic/face-api) — Browser-based facial expression detection
- [Google Gemini API](https://ai.google.dev/) — System-prompted therapeutic chat and response streaming
