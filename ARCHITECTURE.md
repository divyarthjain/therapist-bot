# Architecture Guide

## System Overview

Serenity is a three-layer system: a React frontend that handles video emotion detection and user interaction, a FastAPI backend that runs audio emotion analysis and LLM orchestration, and Ollama which serves the local language model.

```
┌──────────────────────────────────────────────────────────────────┐
│                        Browser (localhost:5173)                   │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐│
│  │  WebcamPanel │  │  Chat Panel  │  │   Emotion Display Panel  ││
│  │  (face-api)  │  │  + AudioRec  │  │   (fused emotion bars)   ││
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────────┘│
│         │                 │                                      │
│    face-api.js       WebSocket                                   │
│    (in-browser)      + REST API                                  │
└─────────┼─────────────────┼──────────────────────────────────────┘
          │                 │
          │  ┌──────────────┼─────────────────────────────────────┐
          │  │           Backend (localhost:8000)                   │
          │  │                                                     │
          │  │  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
          └──┼─►│ EmotionFusion│  │AudioAnalyzer│  │ ChatEngine │  │
             │  │ (weighted    │  │(SenseVoice) │  │  (Ollama)  │  │
             │  │  late fusion)│  └──────┬──────┘  └─────┬──────┘  │
             │  └──────────────┘         │               │         │
             └───────────────────────────┼───────────────┼─────────┘
                                         │               │
                                    ┌────┘               └────┐
                                    ▼                         ▼
                            SenseVoice Model          Ollama (gemma3:4b)
                         (~900MB, ModelScope)         (localhost:11434)
```

## Data Flow

### 1. Chat Message Flow (WebSocket)

```
User types message
    → Frontend sends {type: "message", content, audio_emotion?, video_emotion?}
    → Backend updates EmotionFusion with any attached emotions
    → Backend sends {type: "emotion_summary", emotions: {...}} back
    → Backend calls ChatEngine.chat_stream() with fused emotion context
    → Backend streams {type: "response", content: token, done: false} per token
    → Backend sends {type: "response", content: "", done: true} when complete
    → Frontend renders markdown in real-time
```

### 2. Audio Recording Flow (REST)

```
User clicks record → stops recording
    → Browser creates audio blob (webm/opus)
    → POST /api/analyze-audio (multipart file upload)
    → Backend writes temp file → SenseVoice.generate()
    → SenseVoice returns: "<|en|><|SAD|><|Speech|>I feel terrible today"
    → Backend parses tags → {transcription, emotion, events, language}
    → Frontend receives result, injects transcription into chat input
    → Frontend stores audio_emotion for next message send
```

### 3. Video Emotion Flow (In-Browser)

```
face-api.js detection loop (every 500ms):
    → Detect face in webcam frame (TinyFaceDetector)
    → Classify expression (FaceExpressionNet)
    → Returns: {happy: 0.02, sad: 0.85, neutral: 0.10, ...}
    → Pick dominant emotion → send via WebSocket {type: "emotion", emotion, confidence}
    → Backend updates EmotionFusion video readings
    → Display emotion overlay on webcam feed
```

## Module Details

### Backend Modules

#### `main.py` — FastAPI Application Server

The central orchestrator. Handles:
- CORS configuration for the Vite dev server
- Session management (in-memory dict keyed by UUID)
- REST endpoints for audio analysis, emotion updates, and chat
- WebSocket endpoint for streaming chat with real-time emotion updates
- Startup lifecycle (loads SenseVoice and initializes ChatEngine)

#### `audio_analyzer.py` — SenseVoice Wrapper

Wraps the FunASR `AutoModel` for SenseVoice inference:
- Accepts raw audio bytes, writes to temp file (FunASR requires file path)
- Configures VAD (Voice Activity Detection) for handling long audio
- Parses SenseVoice's tag-embedded output format: `<|lang|><|EMOTION|><|Event|>text`
- Supports fallback mode if SenseVoice fails to load
- Device selection: MPS (Apple Silicon) > CPU, configurable via `SENSEVOICE_DEVICE`

**SenseVoice Output Format:**
```
Raw:  "<|en|><|SAD|><|Speech|><|woitn|>I've been feeling really down lately"
Parsed: {emotion: "sad", events: ["speech"], language: "en", clean_text: "I've been feeling really down lately"}
```

#### `chat_engine.py` — Ollama Chat Engine

Manages therapeutic conversation with emotion awareness:
- Constructs a detailed therapeutic system prompt with CBT and active listening guidelines
- Dynamically appends emotion context to the system prompt based on fused emotion state
- Detects emotional incongruence between modalities and instructs the LLM to explore it
- Supports both streaming (`chat_stream`) and non-streaming (`chat`) modes
- Keeps conversation history (last 20 messages) within context window

#### `emotion_fusion.py` — Multimodal Emotion Fusion

Combines audio and video emotion signals:
- **Weighted late fusion**: Audio 60%, Video 40% (voice reveals deeper emotional states)
- **Exponential time decay**: Half-life of 10 seconds (older readings matter less)
- **Sliding window**: Keeps last 10 readings per modality
- **Incongruence detection**: Flags when voice and face disagree with sufficient confidence
- **Graceful degradation**: Works with only one modality available

### Frontend Modules

#### Hooks

| Hook | Purpose |
|------|---------|
| `useWebSocket` | WebSocket connection with auto-reconnect (exponential backoff), message/emotion dispatch, streaming state management |
| `useAudioRecorder` | MediaRecorder API wrapper — records audio, uploads to `/api/analyze-audio`, returns transcription + emotion |
| `useFaceDetection` | face-api.js lifecycle — loads models from `/models/`, runs detection loop on webcam feed every 500ms |

#### Components

| Component | Purpose |
|-----------|---------|
| `App` | Root layout — 3-column: emotion display, chat, webcam. Wires hooks together |
| `ChatPanel` | Message list + input form. Supports pending transcription injection from audio recorder |
| `MessageBubble` | Individual message with markdown rendering (react-markdown + remark-gfm) and emotion emoji |
| `AudioRecorder` | Record button with visual states (idle/recording/analyzing). Sends audio to backend |
| `WebcamEmotion` | Webcam feed with face-api.js overlay. Toggle on/off. Shows detected emotion label |
| `EmotionDisplay` | Horizontal bar chart of fused emotion scores with per-modality breakdown |

## WebSocket Protocol

### Client → Server

```typescript
// Initialize session
{type: "init", session_id?: string}

// Send chat message with optional emotion context
{type: "message", content: string, audio_emotion?: string, video_emotion?: string}

// Send real-time video emotion update
{type: "emotion", emotion: string, confidence: number}
```

### Server → Client

```typescript
// Session established
{type: "session", session_id: string}

// Fused emotion state after processing
{type: "emotion_summary", emotions: EmotionState}

// Streaming response token
{type: "response", content: string, done: boolean}

// Error
{type: "error", message: string}
```

## Emotion Labels

Both audio (SenseVoice) and video (face-api.js) use the same 7 emotion labels:

| Emotion | Audio Source | Video Source | Fusion Weight |
|---------|-------------|-------------|---------------|
| `happy` | Voice prosody | Smile detection | Audio: 0.6, Video: 0.4 |
| `sad` | Voice prosody | Frown/drooped features | Audio: 0.6, Video: 0.4 |
| `angry` | Voice prosody | Furrowed brow/tension | Audio: 0.6, Video: 0.4 |
| `neutral` | Flat prosody | Relaxed face | Audio: 0.6, Video: 0.4 |
| `fearful` | Voice tremor | Wide eyes/tension | Audio: 0.6, Video: 0.4 |
| `disgusted` | Voice quality | Nose wrinkle/lip curl | Audio: 0.6, Video: 0.4 |
| `surprised` | Voice pitch | Raised eyebrows/open mouth | Audio: 0.6, Video: 0.4 |

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| SenseVoice inference | ~2-3s | CPU (Apple M4 Pro). ~70ms on GPU for 10s audio |
| face-api.js detection | ~50ms | Per frame, TinyFaceDetector + expressions |
| Ollama first token | ~500ms | Gemma 3 4B Q8_0 on Apple Silicon |
| Ollama streaming | ~30 tok/s | Varies by hardware |
| Emotion fusion | <1ms | Pure arithmetic |

## Security Considerations

- All services bind to localhost only in development
- No authentication is implemented (single-user local app)
- SenseVoice model is downloaded from ModelScope (Chinese ML hub) — verify checksums if concerned
- Ollama model weights come from the official Ollama registry
- face-api.js models ship with the npm package — no external download at runtime
- Crisis detection is best-effort via LLM prompt engineering, not a guaranteed safety system
