"""
Therapist Bot Backend — FastAPI server (API-only mode)
Uses Deepgram (STT/TTS) and Gemini (chat) APIs.
No local ML models required.
"""

import base64
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from asr_engine import create_asr_engine
from chat_engine import ChatEngine, parse_llm_response
from emotion_aligner import WordEmotion, format_tagged_text
from emotion_fusion import EmotionFusion
from mood_context import MoodContextStore
from tts_engine import TTSEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"

load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="Therapist Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global State ──────────────────────────────────────────────────────────────

chat_engine: Optional[ChatEngine] = None
emotion_fusion = EmotionFusion()
asr_engine = None
tts_engine: Optional[TTSEngine] = None
mood_context_store = MoodContextStore()

# Per-session conversation histories: session_id → dict
sessions: dict[str, dict] = {}


def get_or_create_session(session_id: Optional[str] = None) -> str:
    if session_id and session_id in sessions:
        return session_id
    sid = session_id or str(uuid.uuid4())
    sessions[sid] = {
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "emotion_history": [],
    }
    return sid


def get_mood_context(session_id: Optional[str]) -> str:
    if not session_id:
        return ""
    return mood_context_store.summarize_recent(session_id)


def record_mood_context(session_id: Optional[str]) -> None:
    if not session_id:
        return
    mood_context_store.record_snapshot(session_id, emotion_fusion.get_fused_emotion())


# ── Startup / Shutdown ────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    global chat_engine, asr_engine, tts_engine

    try:
        chat_engine = ChatEngine()
        logger.info("Chat engine ready (Gemini API).")
    except Exception as e:
        logger.error("Failed to init chat engine: %s", e)
        chat_engine = None

    try:
        asr_engine = create_asr_engine()
        logger.info("ASR engine ready (Deepgram API).")
    except Exception as e:
        logger.error("Failed to init ASR engine: %s", e)
        asr_engine = None

    try:
        tts_engine = TTSEngine()
        logger.info("TTS engine ready (Deepgram API, loaded=%s).", tts_engine.is_loaded())
    except Exception as e:
        logger.error("Failed to init TTS: %s", e)
        tts_engine = None


@app.on_event("shutdown")
async def shutdown():
    if chat_engine is not None:
        await chat_engine.close()
    if asr_engine is not None and hasattr(asr_engine, "close"):
        asr_engine.close()
    if tts_engine is not None and hasattr(tts_engine, "close"):
        tts_engine.close()


# ── REST Endpoints ────────────────────────────────────────────────────────────


class EmotionUpdate(BaseModel):
    session_id: Optional[str] = None
    video_emotion: str
    confidence: float


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    audio_emotion: Optional[str] = None
    video_emotion: Optional[str] = None


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "gemini_ready": chat_engine is not None,
        "asr_loaded": asr_engine is not None and getattr(asr_engine, "_loaded", False),
        "tts_loaded": tts_engine is not None and tts_engine.is_loaded(),
    }


async def run_voice_pipeline(
    audio_bytes: bytes, filename: str, session_id: str
) -> dict:
    """STT → Chat → TTS pipeline using Deepgram + Gemini APIs."""
    timings = {}

    # 1. Deepgram STT
    t0 = time.time()
    asr_result = asr_engine.transcribe(audio_bytes, filename)
    timings["asr_ms"] = round((time.time() - t0) * 1000)

    audio_emotion = asr_result.detected_emotion or "neutral"
    audio_confidence = float(asr_result.emotion_confidence or 0.6)
    emotion_fusion.update_audio(audio_emotion, audio_confidence)

    if not asr_result.full_text.strip():
        return {
            "response_text": "",
            "emotion_tags": "",
            "target_emotion": "neutral",
            "audio_base64": None,
            "timings": timings,
            "transcription": "",
            "audio_emotion": audio_emotion,
        }

    # Build simple word-level emotion tags from ASR segments
    scores = {audio_emotion: audio_confidence}
    word_emotions = [
        WordEmotion(
            word=segment.word,
            start=segment.start,
            end=segment.end,
            emotion=audio_emotion,
            confidence=audio_confidence,
            scores=scores,
        )
        for segment in asr_result.segments
    ]

    tagged_text = format_tagged_text(word_emotions)

    # 2. Gemini Chat
    t0 = time.time()
    sid = get_or_create_session(session_id)
    sessions[sid]["messages"].append({"role": "user", "content": asr_result.full_text})
    record_mood_context(sid)

    response = await chat_engine.chat(
        messages=sessions[sid]["messages"],
        tagged_text=tagged_text,
        fused_emotion=emotion_fusion.get_fused_emotion(),
        mood_context=get_mood_context(sid),
    )

    target_emotion, clean_response = parse_llm_response(response)
    sessions[sid]["messages"].append({"role": "assistant", "content": clean_response})
    timings["llm_ms"] = round((time.time() - t0) * 1000)

    # 3. Deepgram TTS
    audio_base64 = None
    if tts_engine and tts_engine.is_loaded():
        t0 = time.time()
        audio_wav = tts_engine.generate_speech(clean_response, emotion=target_emotion)
        timings["tts_ms"] = round((time.time() - t0) * 1000)
        if audio_wav:
            audio_base64 = base64.b64encode(audio_wav).decode("utf-8")

    total = sum(v for v in timings.values())
    timings["total_ms"] = total
    logger.info("Voice pipeline complete: %s", timings)

    return {
        "response_text": clean_response,
        "emotion_tags": tagged_text,
        "target_emotion": target_emotion,
        "audio_base64": audio_base64,
        "timings": timings,
        "transcription": asr_result.full_text,
        "session_id": sid,
        "audio_emotion": audio_emotion,
    }


@app.post("/api/analyze-audio")
async def analyze_audio(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
):
    """Upload audio → Deepgram STT → return transcription + basic emotion."""
    if asr_engine is None:
        return {"error": "ASR engine not loaded"}

    audio_bytes = await file.read()
    asr_result = asr_engine.transcribe(audio_bytes, file.filename or "audio.wav")
    sid = get_or_create_session(session_id)

    emotion = asr_result.detected_emotion or "neutral"
    confidence = float(asr_result.emotion_confidence or 0.6)

    sessions[sid]["emotion_history"].append(
        {
            "source": "audio",
            "emotion": emotion,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
    )

    return {
        "transcription": asr_result.full_text,
        "emotion": emotion,
        "confidence": confidence,
        "events": ["speech"] if asr_result.full_text else [],
        "language": asr_result.language,
        "session_id": sid,
    }


@app.post("/api/emotion-update")
async def emotion_update(data: EmotionUpdate):
    """Receive video emotion updates from browser-side face-api.js."""
    sid = get_or_create_session(data.session_id)
    sessions[sid]["emotion_history"].append(
        {
            "source": "video",
            "emotion": data.video_emotion,
            "confidence": data.confidence,
            "timestamp": datetime.now().isoformat(),
        }
    )
    emotion_fusion.update_video(data.video_emotion, data.confidence)
    record_mood_context(sid)
    return {"status": "ok", "session_id": sid}


@app.post("/api/chat")
async def chat(data: ChatRequest):
    """Non-streaming chat endpoint."""
    if chat_engine is None:
        return {"error": "Chat engine not loaded"}

    sid = get_or_create_session(data.session_id)

    if data.audio_emotion:
        emotion_fusion.update_audio(data.audio_emotion, 0.8)
    if data.video_emotion:
        emotion_fusion.update_video(data.video_emotion, 0.8)

    fused = emotion_fusion.get_fused_emotion()
    record_mood_context(sid)

    sessions[sid]["messages"].append({"role": "user", "content": data.message})

    response = await chat_engine.chat(
        messages=sessions[sid]["messages"],
        fused_emotion=fused,
        mood_context=get_mood_context(sid),
    )

    target_emotion, clean_response = parse_llm_response(response)
    sessions[sid]["messages"].append({"role": "assistant", "content": clean_response})

    return {
        "response": clean_response,
        "target_emotion": target_emotion,
        "session_id": sid,
        "detected_emotions": fused,
    }


@app.post("/api/chat/voice")
async def chat_voice(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
):
    if not asr_engine or not chat_engine:
        return {"error": "Pipeline engines not fully loaded"}

    audio_bytes = await file.read()
    result = await run_voice_pipeline(
        audio_bytes, file.filename or "audio.wav", session_id
    )
    return result


# ── WebSocket for Streaming Chat ──────────────────────────────────────────────


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = None

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "message")

            if msg_type == "init":
                session_id = get_or_create_session(data.get("session_id"))
                await websocket.send_json(
                    {
                        "type": "session",
                        "session_id": session_id,
                    }
                )
                continue

            if msg_type == "emotion":
                session_id = get_or_create_session(session_id or data.get("session_id"))
                emotion_fusion.update_video(
                    data.get("emotion", "neutral"),
                    data.get("confidence", 0.5),
                )
                record_mood_context(session_id)
                continue

            if msg_type == "message":
                session_id = get_or_create_session(session_id or data.get("session_id"))

                user_msg = data.get("content", "")
                audio_emo = data.get("audio_emotion")
                video_emo = data.get("video_emotion")

                if audio_emo:
                    emotion_fusion.update_audio(audio_emo, 0.8)
                if video_emo:
                    emotion_fusion.update_video(video_emo, 0.8)

                fused = emotion_fusion.get_fused_emotion()
                record_mood_context(session_id)

                await websocket.send_json(
                    {
                        "type": "emotion_summary",
                        "emotions": fused,
                    }
                )

                sessions[session_id]["messages"].append(
                    {
                        "role": "user",
                        "content": user_msg,
                    }
                )

                # Stream response tokens
                full_response = ""
                if chat_engine is None:
                    await websocket.send_json(
                        {"type": "error", "message": "Chat engine not loaded"}
                    )
                    continue

                async for token in chat_engine.chat_stream(
                    messages=sessions[session_id]["messages"],
                    fused_emotion=fused,
                    mood_context=get_mood_context(session_id),
                ):
                    full_response += token
                    await websocket.send_json(
                        {
                            "type": "response",
                            "content": token,
                            "done": False,
                        }
                    )

                await websocket.send_json(
                    {
                        "type": "response",
                        "content": "",
                        "done": True,
                    }
                )

                sessions[session_id]["messages"].append(
                    {
                        "role": "assistant",
                        "content": full_response,
                    }
                )

            elif msg_type == "voice_message":
                if not asr_engine or not chat_engine:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Pipeline engines not fully loaded",
                        }
                    )
                    continue

                session_id = get_or_create_session(session_id or data.get("session_id"))

                audio_b64 = data.get("audio", "")
                if not audio_b64:
                    await websocket.send_json(
                        {"type": "error", "message": "No audio data"}
                    )
                    continue

                audio_bytes = base64.b64decode(audio_b64)
                result = await run_voice_pipeline(
                    audio_bytes, "ws_audio.wav", session_id
                )

                await websocket.send_json(
                    {
                        "type": "voice_response",
                        "response_text": result["response_text"],
                        "emotion_tags": result["emotion_tags"],
                        "target_emotion": result["target_emotion"],
                        "audio_base64": result.get("audio_base64"),
                        "timings": result["timings"],
                        "transcription": result["transcription"],
                        "done": True,
                    }
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected (session: %s)", session_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_frontend(full_path: str):
    if full_path.startswith("api") or full_path.startswith("ws"):
        raise HTTPException(status_code=404, detail="Not found")

    if not FRONTEND_INDEX_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Frontend build not found. Run `npm run build` in the frontend directory.",
        )

    requested = (FRONTEND_DIST_DIR / full_path).resolve()
    if full_path and requested.is_file() and str(requested).startswith(str(FRONTEND_DIST_DIR)):
        return FileResponse(requested)

    return FileResponse(FRONTEND_INDEX_FILE)


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
