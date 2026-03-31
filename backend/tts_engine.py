from __future__ import annotations

import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)


class TTSEngine:
    BASE_URL = "https://api.deepgram.com/v1/speak"

    def __init__(self) -> None:
        self.api_key = os.environ.get("DEEPGRAM_API_KEY", "").strip()
        self.default_model = os.environ.get("DEEPGRAM_TTS_MODEL", "aura-2-thalia-en")
        self.encoding = os.environ.get("DEEPGRAM_TTS_ENCODING", "linear16")
        self.container = os.environ.get("DEEPGRAM_TTS_CONTAINER", "wav")
        self.sample_rate = os.environ.get("DEEPGRAM_TTS_SAMPLE_RATE", "24000")
        self.timeout_seconds = float(os.environ.get("DEEPGRAM_TTS_TIMEOUT_SECONDS", "60"))
        self._loaded = bool(self.api_key)
        self.client = httpx.Client(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10.0)
        )

        if self._loaded:
            logger.info(
                "Deepgram TTS initialized with model: %s",
                self.default_model,
            )
        else:
            logger.warning("DEEPGRAM_API_KEY is missing; TTS will stay unavailable")

    def is_loaded(self) -> bool:
        return self._loaded

    def close(self) -> None:
        self.client.close()

    def get_available_voices(self) -> List[str]:
        return [self.default_model]

    def get_supported_emotions(self) -> List[str]:
        return [
            "happy",
            "sad",
            "angry",
            "neutral",
            "empathetic",
            "fearful",
        ]

    def _resolve_model(self, voice: str, emotion: str) -> str:
        if voice and voice.startswith("aura-"):
            return voice

        emotion_models = {
            "happy": os.environ.get("DEEPGRAM_TTS_MODEL_HAPPY", self.default_model),
            "sad": os.environ.get("DEEPGRAM_TTS_MODEL_SAD", self.default_model),
            "angry": os.environ.get("DEEPGRAM_TTS_MODEL_ANGRY", self.default_model),
            "neutral": self.default_model,
            "empathetic": os.environ.get(
                "DEEPGRAM_TTS_MODEL_EMPATHETIC",
                self.default_model,
            ),
            "fearful": os.environ.get("DEEPGRAM_TTS_MODEL_FEARFUL", self.default_model),
        }
        return emotion_models.get((emotion or "neutral").lower(), self.default_model)

    def generate_speech(
        self, text: str, emotion: str = "neutral", voice: str = "default"
    ) -> Optional[bytes]:
        if not self._loaded:
            return None

        text = (text or "").strip()
        if not text:
            return None

        model = self._resolve_model(voice, emotion)

        try:
            response = self.client.post(
                self.BASE_URL,
                params={
                    "model": model,
                    "encoding": self.encoding,
                    "container": self.container,
                    "sample_rate": self.sample_rate,
                },
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"text": text},
            )
            response.raise_for_status()
            return response.content
        except Exception as exc:
            logger.error("Deepgram TTS request failed: %s", exc)
            return None
