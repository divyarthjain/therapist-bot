"""
Emotion Fusion Engine
Combines emotional signals from multiple modalities:
  - Audio (SenseVoice: voice prosody + content)
  - Video (face-api.js: facial expressions)

Uses weighted late fusion with exponential decay for temporal smoothing.
Audio emotions from voice tone are weighted higher than facial expressions
for therapeutic context, as voice often reveals deeper emotional states.
"""

import time
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)

# Weights for each modality (should sum to 1.0)
MODALITY_WEIGHTS = {
    "audio": 0.6,  # Voice tone is more reliable for deep emotions
    "video": 0.4,  # Facial expressions can be masked/performed
}

# How quickly old emotion readings decay (seconds)
DECAY_HALF_LIFE = 10.0  # After 10s, an emotion reading has half weight

# All supported emotions
EMOTIONS = ["happy", "sad", "angry", "neutral", "fearful", "disgusted", "surprised"]


class EmotionReading:
    """A single emotion reading from any modality."""

    def __init__(self, emotion: str, confidence: float, source: str):
        self.emotion = emotion
        self.confidence = min(max(confidence, 0.0), 1.0)
        self.source = source
        self.timestamp = time.time()

    def decayed_confidence(self, now: Optional[float] = None) -> float:
        """Return confidence with exponential time decay applied."""
        now = now or time.time()
        age = now - self.timestamp
        decay = 0.5 ** (age / DECAY_HALF_LIFE)
        return self.confidence * decay


class EmotionFusion:
    """
    Fuses emotion signals from audio and video into a unified emotional state.

    Maintains a sliding window of recent readings per modality,
    applies temporal decay, and produces a weighted fusion.
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.audio_readings: deque[EmotionReading] = deque(maxlen=window_size)
        self.video_readings: deque[EmotionReading] = deque(maxlen=window_size)

    def update_audio(self, emotion: str, confidence: float):
        """Add a new audio emotion reading."""
        emotion = emotion.lower()
        if emotion not in EMOTIONS:
            emotion = "neutral"
        self.audio_readings.append(EmotionReading(emotion, confidence, "audio"))

    def update_video(self, emotion: str, confidence: float):
        """Add a new video emotion reading."""
        emotion = emotion.lower()
        if emotion not in EMOTIONS:
            emotion = "neutral"
        self.video_readings.append(EmotionReading(emotion, confidence, "video"))

    def _aggregate_modality(self, readings: deque[EmotionReading]) -> dict:
        """
        Aggregate readings from a single modality into emotion scores.
        Returns {"emotion": str, "confidence": float, "scores": dict}.
        """
        if not readings:
            return {"emotion": "neutral", "confidence": 0.0, "scores": {}}

        now = time.time()
        scores: dict[str, float] = {e: 0.0 for e in EMOTIONS}
        total_weight = 0.0

        for reading in readings:
            w = reading.decayed_confidence(now)
            scores[reading.emotion] = scores.get(reading.emotion, 0.0) + w
            total_weight += w

        if total_weight > 0:
            scores = {k: v / total_weight for k, v in scores.items()}

        dominant = max(scores, key=scores.get)
        return {
            "emotion": dominant,
            "confidence": scores[dominant],
            "scores": scores,
        }

    def get_fused_emotion(self) -> dict:
        """
        Get the fused emotional state across all modalities.

        Returns:
            {
                "dominant": "sad",
                "confidence": 0.78,
                "audio": {"emotion": "sad", "confidence": 0.85, "scores": {...}},
                "video": {"emotion": "neutral", "confidence": 0.60, "scores": {...}},
                "fused_scores": {"happy": 0.05, "sad": 0.55, ...},
                "incongruence": False,
            }
        """
        audio_agg = self._aggregate_modality(self.audio_readings)
        video_agg = self._aggregate_modality(self.video_readings)

        # Weighted fusion of emotion scores
        fused_scores: dict[str, float] = {e: 0.0 for e in EMOTIONS}

        audio_weight = MODALITY_WEIGHTS["audio"]
        video_weight = MODALITY_WEIGHTS["video"]

        # If one modality has no data, give full weight to the other
        if not self.audio_readings and not self.video_readings:
            return {
                "dominant": "neutral",
                "confidence": 0.0,
                "audio": audio_agg,
                "video": video_agg,
                "fused_scores": fused_scores,
                "incongruence": False,
            }

        if not self.audio_readings:
            audio_weight = 0.0
            video_weight = 1.0
        elif not self.video_readings:
            audio_weight = 1.0
            video_weight = 0.0

        for emotion in EMOTIONS:
            fused_scores[emotion] = (
                audio_agg["scores"].get(emotion, 0.0) * audio_weight
                + video_agg["scores"].get(emotion, 0.0) * video_weight
            )

        dominant = max(fused_scores, key=fused_scores.get)
        confidence = fused_scores[dominant]

        # Detect incongruence between modalities
        incongruence = (
            audio_agg["emotion"] != "neutral"
            and video_agg["emotion"] != "neutral"
            and audio_agg["emotion"] != video_agg["emotion"]
            and audio_agg["confidence"] > 0.3
            and video_agg["confidence"] > 0.3
        )

        if incongruence:
            logger.info(
                f"Emotional incongruence: voice={audio_agg['emotion']}, "
                f"face={video_agg['emotion']}"
            )

        return {
            "dominant": dominant,
            "confidence": confidence,
            "audio": audio_agg,
            "video": video_agg,
            "fused_scores": fused_scores,
            "incongruence": incongruence,
        }

    def reset(self):
        """Clear all emotion readings."""
        self.audio_readings.clear()
        self.video_readings.clear()
