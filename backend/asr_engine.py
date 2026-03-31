from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Protocol

import httpx

logger = logging.getLogger(__name__)


@dataclass
class WordSegment:
    word: str
    start: float
    end: float


@dataclass
class ASRResult:
    segments: List[WordSegment]
    full_text: str
    language: str
    detected_emotion: str = "neutral"
    emotion_confidence: float = 0.0


class ASREngine(Protocol):
    def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult: ...


class DeepgramASR:
    BASE_URL = "https://api.deepgram.com/v1/listen"

    def __init__(self) -> None:
        self.api_key = os.environ.get("DEEPGRAM_API_KEY", "").strip()
        self.model = os.environ.get("DEEPGRAM_STT_MODEL", "nova-3")
        self.language = os.environ.get("DEEPGRAM_STT_LANGUAGE", "en")
        self.timeout_seconds = float(os.environ.get("DEEPGRAM_STT_TIMEOUT_SECONDS", "60"))
        self._loaded = bool(self.api_key)
        self.client = httpx.Client(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10.0)
        )

        if self._loaded:
            logger.info("Deepgram ASR initialized with model: %s", self.model)
        else:
            logger.warning("DEEPGRAM_API_KEY is missing; ASR will stay unavailable")

    @staticmethod
    def _content_type_for(filename: str, audio_bytes: bytes) -> str:
        lower = (filename or "").lower()
        if lower.endswith(".wav") or (
            len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"
        ):
            return "audio/wav"
        if lower.endswith(".mp3"):
            return "audio/mpeg"
        if lower.endswith(".m4a"):
            return "audio/mp4"
        return "application/octet-stream"

    @staticmethod
    def _extract_segments(words_payload: list[dict], transcript: str) -> List[WordSegment]:
        segments = []
        for item in words_payload:
            word = str(item.get("word", "")).strip()
            if not word:
                continue
            start = float(item.get("start", 0.0) or 0.0)
            end = float(item.get("end", start) or start)
            segments.append(WordSegment(word=word, start=start, end=end))

        if segments:
            return segments

        words = transcript.split()
        if not words:
            return []

        per_word = 0.35
        return [
            WordSegment(word=word, start=index * per_word, end=(index + 1) * per_word)
            for index, word in enumerate(words)
        ]

    def close(self) -> None:
        self.client.close()

    def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult:
        if not self._loaded:
            return ASRResult(segments=[], full_text="", language=self.language)

        try:
            response = self.client.post(
                self.BASE_URL,
                params={
                    "model": self.model,
                    "language": self.language,
                    "smart_format": "true",
                    "punctuate": "true",
                },
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": self._content_type_for(filename, audio_bytes),
                },
                content=audio_bytes,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.error("Deepgram ASR request failed: %s", exc)
            return ASRResult(segments=[], full_text="", language=self.language)

        channel = (
            payload.get("results", {})
            .get("channels", [{}])[0]
        )
        alternative = channel.get("alternatives", [{}])[0]
        transcript = str(alternative.get("transcript", "")).strip()
        words_payload = alternative.get("words", []) or []
        detected_language = str(
            alternative.get("detected_language")
            or channel.get("detected_language")
            or self.language
        )

        return ASRResult(
            segments=self._extract_segments(words_payload, transcript),
            full_text=transcript,
            language=detected_language,
            detected_emotion="neutral",
            emotion_confidence=0.0,
        )


def create_asr_engine(analyzer=None) -> ASREngine:
    del analyzer
    return DeepgramASR()
