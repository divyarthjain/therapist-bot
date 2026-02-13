"""
Therapist Bot Backend — FastAPI server
Combines SenseVoice (audio emotion), face-api.js results (video emotion),
and Ollama gemma3:4b (therapeutic chat) into a multimodal therapy assistant.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from audio_analyzer import AudioAnalyzer
from chat_engine import ChatEngine
from emotion_fusion import EmotionFusion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Therapist Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global State ──────────────────────────────────────────────────────────────

audio_analyzer: Optional[AudioAnalyzer] = None
chat_engine: Optional[ChatEngine] = None
emotion_fusion = EmotionFusion()

# Per-session conversation histories: session_id → list of messages
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


# ── Startup / Shutdown ────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    global audio_analyzer, chat_engine
    logger.info("Loading SenseVoice model (this may take 30-60s on first run)...")
    audio_analyzer = AudioAnalyzer()
    logger.info("SenseVoice loaded.")
    chat_engine = ChatEngine()
    logger.info("Chat engine ready (Ollama gemma3:4b).")


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
        "sensevoice_loaded": audio_analyzer is not None,
        "ollama_ready": chat_engine is not None,
    }


@app.post("/api/analyze-audio")
async def analyze_audio(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
):
    """
    Upload an audio file → get transcription + emotion + audio events.
    SenseVoice outputs raw_text with embedded tags like <|HAPPY|>, <|Speech|>, etc.
    """
    if audio_analyzer is None:
        return {"error": "Audio analyzer not loaded yet"}

    audio_bytes = await file.read()
    result = audio_analyzer.analyze(audio_bytes, filename=file.filename or "audio.wav")

    # Store emotion in session
    sid = get_or_create_session(session_id)
    sessions[sid]["emotion_history"].append(
        {
            "source": "audio",
            "emotion": result["emotion"],
            "confidence": result["confidence"],
            "timestamp": datetime.now().isoformat(),
        }
    )

    return {**result, "session_id": sid}


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
    return {"status": "ok", "session_id": sid}


@app.post("/api/chat")
async def chat(data: ChatRequest):
    """Non-streaming chat endpoint (use WebSocket for streaming)."""
    if chat_engine is None:
        return {"error": "Chat engine not loaded"}

    sid = get_or_create_session(data.session_id)

    # Fuse emotions from all sources
    if data.audio_emotion:
        emotion_fusion.update_audio(data.audio_emotion, 0.8)
    if data.video_emotion:
        emotion_fusion.update_video(data.video_emotion, 0.8)

    fused = emotion_fusion.get_fused_emotion()

    # Add user message to history
    sessions[sid]["messages"].append({"role": "user", "content": data.message})

    response = await chat_engine.chat(
        messages=sessions[sid]["messages"],
        fused_emotion=fused,
    )

    sessions[sid]["messages"].append({"role": "assistant", "content": response})

    return {
        "response": response,
        "session_id": sid,
        "detected_emotions": fused,
    }


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
                # Video emotion update from face-api.js
                emotion_fusion.update_video(
                    data.get("emotion", "neutral"),
                    data.get("confidence", 0.5),
                )
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

                # Send emotion summary to client
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

    except WebSocketDisconnect:
        logger.info(f"Client disconnected (session: {session_id})")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
