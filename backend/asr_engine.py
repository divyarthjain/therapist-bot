from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Optional, Protocol

from audio_analyzer import AudioAnalyzer, parse_sensevoice_tags

logger = logging.getLogger(__name__)

MEMORY_REPORT_PATH = os.path.join(os.path.dirname(__file__), "MEMORY_REPORT.md")


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


class ASREngine(Protocol):
    def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult: ...


class SenseVoiceASR:
    def __init__(self, device: Optional[str] = None):
        if device:
            self.device = device
        elif os.environ.get("SENSEVOICE_DEVICE"):
            self.device = os.environ["SENSEVOICE_DEVICE"]
        else:
            try:
                import torch

                self.device = "mps" if torch.backends.mps.is_available() else "cpu"
            except Exception:
                self.device = "cpu"

        logger.info(f"Initializing SenseVoice ASR on device: {self.device}")

        try:
            self.analyzer = AudioAnalyzer(device=self.device)
            self._loaded = getattr(self.analyzer, "_loaded", False)
            if self._loaded:
                logger.info("SenseVoice model loaded successfully")
            else:
                logger.info(
                    "Audio analysis will use fallback mode (transcription only)"
                )
        except Exception as e:
            logger.error(f"Failed to load SenseVoice: {e}")
            logger.info("Audio analysis will use fallback mode (transcription only)")
            self._loaded = False
            self.analyzer = None

    def transcribe(self, audio_bytes: bytes, filename: str) -> ASRResult:
        if not self.analyzer:
            return ASRResult(segments=[], full_text="", language="unknown")

        try:
            analysis = self.analyzer.analyze(audio_bytes, filename=filename)
            raw_text = analysis.get("raw_text", "")
            if raw_text:
                parsed = parse_sensevoice_tags(raw_text)
                clean_text = parsed.get("clean_text", "")
                language = parsed.get("language", "unknown")
            else:
                clean_text = analysis.get("transcription", "")
                language = analysis.get("language", "unknown")

            words = clean_text.split()
            total_duration = len(audio_bytes) / (16000 * 2)
            if not words:
                return ASRResult(segments=[], full_text=clean_text, language=language)

            per_word = total_duration / len(words)
            segments = [
                WordSegment(
                    word=word,
                    start=i * per_word,
                    end=(i + 1) * per_word,
                )
                for i, word in enumerate(words)
            ]

            return ASRResult(segments=segments, full_text=clean_text, language=language)

        except Exception as e:
            logger.error(f"SenseVoice inference error: {e}")
            return ASRResult(segments=[], full_text="", language="unknown")


def _confirm_memory_decision() -> None:
    try:
        with open(MEMORY_REPORT_PATH, "r", encoding="utf-8") as handle:
            report = handle.read()
        if "Decision: NO-GO" in report:
            logger.info("Memory report: NO-GO confirmed; using SenseVoice fallback")
        else:
            logger.warning(
                "Memory report missing NO-GO decision; using SenseVoice fallback"
            )
    except Exception as e:
        logger.warning(f"Failed to read MEMORY_REPORT.md: {e}")


def create_asr_engine() -> ASREngine:
    _confirm_memory_decision()
    logger.info("ASR engine selected: SenseVoice")
    return SenseVoiceASR()
