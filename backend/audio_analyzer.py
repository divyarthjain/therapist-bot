"""
SenseVoice Audio Analyzer
Wraps FunAudioLLM/SenseVoice for:
  - Speech-to-text transcription (50+ languages)
  - Speech emotion recognition (HAPPY, SAD, ANGRY, NEUTRAL, FEARFUL, DISGUSTED, SURPRISED)
  - Audio event detection (Speech, BGM, Laughter, Cry, Applause, etc.)

Model: iic/SenseVoiceSmall (~600MB, non-autoregressive, 70ms for 10s audio on GPU)
On Apple M4 Pro CPU: ~2-3s per audio clip.
"""

import io
import os
import re
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# Emotion tag mapping from SenseVoice output
EMOTION_TAGS = {
    "<|HAPPY|>": "happy",
    "<|SAD|>": "sad",
    "<|ANGRY|>": "angry",
    "<|NEUTRAL|>": "neutral",
    "<|FEARFUL|>": "fearful",
    "<|DISGUSTED|>": "disgusted",
    "<|SURPRISED|>": "surprised",
    "<|EMO_UNKNOWN|>": "unknown",
}

EVENT_TAGS = {
    "<|Speech|>": "speech",
    "<|BGM|>": "bgm",
    "<|Applause|>": "applause",
    "<|Laughter|>": "laughter",
    "<|Cry|>": "cry",
    "<|Sneeze|>": "sneeze",
    "<|Breath|>": "breath",
    "<|Cough|>": "cough",
    "<|Event_UNK|>": "unknown_event",
}

TAG_REGEX = re.compile(r"<\|([^|]+)\|>")


def parse_sensevoice_tags(raw_text: str) -> dict:
    """
    Parse SenseVoice raw output which contains inline tags like:
    '<|en|><|NEUTRAL|><|Speech|><|woitn|>the actual transcription text'

    Returns dict with emotion, events, language, and clean text.
    """
    emotion = "neutral"
    events = []
    language = "unknown"

    # Extract all tags
    tags = TAG_REGEX.findall(raw_text)

    for tag in tags:
        full_tag = f"<|{tag}|>"
        if full_tag in EMOTION_TAGS:
            emotion = EMOTION_TAGS[full_tag]
        elif full_tag in EVENT_TAGS:
            events.append(EVENT_TAGS[full_tag])
        elif tag in ("en", "zh", "ja", "ko", "yue"):
            language = tag
        # withitn/woitn are formatting flags, skip

    # Remove all tags to get clean text
    clean_text = TAG_REGEX.sub("", raw_text).strip()

    return {
        "emotion": emotion,
        "events": events,
        "language": language,
        "clean_text": clean_text,
        "raw_text": raw_text,
    }


class AudioAnalyzer:
    """Wraps SenseVoice model for audio analysis."""

    def __init__(self, device: Optional[str] = None):
        # Determine device: prefer MPS on Apple Silicon, fall back to CPU
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

        logger.info(f"Initializing SenseVoice on device: {self.device}")

        try:
            from funasr import AutoModel

            self.model = AutoModel(
                model="iic/SenseVoiceSmall",
                trust_remote_code=True,
                device=self.device,
                # Disable VAD for short clips (<30s), enable for longer
                vad_model="fsmn-vad",
                vad_kwargs={"max_single_segment_time": 30000},
            )
            self._loaded = True
            logger.info("SenseVoice model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SenseVoice: {e}")
            logger.info("Audio analysis will use fallback mode (transcription only)")
            self._loaded = False
            self.model = None

    def analyze(self, audio_bytes: bytes, filename: str = "audio.wav") -> dict:
        """
        Analyze audio bytes and return transcription + emotion + events.

        Returns:
            {
                "transcription": "Hello, how are you?",
                "emotion": "neutral",
                "confidence": 0.85,
                "events": ["speech"],
                "language": "en",
                "raw_text": "<|en|><|NEUTRAL|><|Speech|>Hello, how are you?"
            }
        """
        if not self._loaded:
            return self._fallback_analyze(audio_bytes, filename)

        # Write to temp file (funasr expects file path or tensor)
        suffix = os.path.splitext(filename)[1] if filename else ".wav"
        if not suffix:
            suffix = ".wav"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            res = self.model.generate(
                input=temp_path,
                cache={},
                language="auto",
                use_itn=True,
                batch_size_s=60,
                merge_vad=True,
                merge_length_s=15,
                ban_emo_unk=True,
            )

            if not res or len(res) == 0:
                return {
                    "transcription": "",
                    "emotion": "neutral",
                    "confidence": 0.0,
                    "events": [],
                    "language": "unknown",
                    "raw_text": "",
                }

            raw_text = (
                res[0].get("text", "") if isinstance(res[0], dict) else str(res[0])
            )
            parsed = parse_sensevoice_tags(raw_text)

            return {
                "transcription": parsed["clean_text"],
                "emotion": parsed["emotion"],
                "confidence": 0.85,  # SenseVoice doesn't expose per-utterance confidence
                "events": parsed["events"],
                "language": parsed["language"],
                "raw_text": parsed["raw_text"],
            }

        except Exception as e:
            logger.error(f"SenseVoice inference error: {e}")
            return {
                "transcription": "",
                "emotion": "neutral",
                "confidence": 0.0,
                "events": [],
                "language": "unknown",
                "raw_text": "",
                "error": str(e),
            }
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def _fallback_analyze(self, audio_bytes: bytes, filename: str) -> dict:
        """Fallback when SenseVoice isn't available — returns empty analysis."""
        logger.warning("Using fallback audio analysis (SenseVoice not loaded)")
        return {
            "transcription": "[Audio analysis unavailable - SenseVoice not loaded]",
            "emotion": "neutral",
            "confidence": 0.0,
            "events": [],
            "language": "unknown",
            "raw_text": "",
        }
