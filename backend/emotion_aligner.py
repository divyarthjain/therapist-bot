from dataclasses import dataclass
from typing import Iterable

EMOTIONS = ["happy", "sad", "angry", "neutral", "fearful", "disgusted", "surprised"]


@dataclass
class WordEmotion:
    word: str
    start: float
    end: float
    emotion: str
    confidence: float
    scores: dict[str, float]


def _get_attr(obj: object, name: str, default=None):
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, dict):
        return obj.get(name, default)
    return default


def _normalize_emotion(emotion: object) -> str:
    if not emotion:
        return "neutral"
    normalized = str(emotion).lower()
    return normalized if normalized in EMOTIONS else "neutral"


def _aggregate_frames(frames: Iterable[object]) -> tuple[str, float, dict[str, float]]:
    frames = list(frames)
    if not frames:
        return "neutral", 0.0, {}

    scores: dict[str, float] = {emotion: 0.0 for emotion in EMOTIONS}
    total_weight = 0.0

    for frame in frames:
        frame_scores = _get_attr(frame, "scores")
        if isinstance(frame_scores, dict) and frame_scores:
            weight = _get_attr(frame, "confidence", 1.0)
            if weight is None:
                weight = 1.0
            weight = float(weight)

            for emotion in EMOTIONS:
                scores[emotion] += float(frame_scores.get(emotion, 0.0)) * weight
            total_weight += weight
            continue

        emotion = _normalize_emotion(_get_attr(frame, "emotion"))
        weight = _get_attr(frame, "confidence", 1.0)
        if weight is None:
            weight = 1.0
        weight = float(weight)
        scores[emotion] += weight
        total_weight += weight

    if total_weight <= 0.0:
        return "neutral", 0.0, {}

    scores = {emotion: value / total_weight for emotion, value in scores.items()}
    max_score = max(scores.values()) if scores else 0.0
    if max_score <= 0.0:
        return "neutral", 0.0, scores

    dominant = max(scores, key=scores.get)
    confidence = scores[dominant]
    return dominant, confidence, scores


def _frame_in_range(frame: object, start: float, end: float) -> bool:
    timestamp = _get_attr(frame, "timestamp")
    if timestamp is None:
        return False
    try:
        ts = float(timestamp)
    except (TypeError, ValueError):
        return False
    return start <= ts < end


def align_emotions(
    word_segments: Iterable[object],
    emotion_frames: Iterable[object],
) -> list[WordEmotion]:
    segments = list(word_segments) if word_segments else []
    if not segments:
        return []

    frames = list(emotion_frames) if emotion_frames else []
    results: list[WordEmotion] = []

    for segment in segments:
        word = _get_attr(segment, "word", "")
        if word is None:
            word = ""

        start = _get_attr(segment, "start", 0.0)
        end = _get_attr(segment, "end", 0.0)

        try:
            start_value = float(start)
        except (TypeError, ValueError):
            start_value = 0.0

        try:
            end_value = float(end)
        except (TypeError, ValueError):
            end_value = start_value

        matched_frames = [
            frame for frame in frames if _frame_in_range(frame, start_value, end_value)
        ]
        emotion, confidence, scores = _aggregate_frames(matched_frames)
        results.append(
            WordEmotion(
                word=str(word),
                start=start_value,
                end=end_value,
                emotion=emotion,
                confidence=confidence,
                scores=scores,
            )
        )

    return results


def format_tagged_text(word_emotions: Iterable[WordEmotion]) -> str:
    word_emotions = list(word_emotions) if word_emotions else []
    if not word_emotions:
        return ""

    segments: list[str] = []
    current_emotion = word_emotions[0].emotion
    current_words = [word_emotions[0].word]

    for word_emotion in word_emotions[1:]:
        if word_emotion.emotion == current_emotion:
            current_words.append(word_emotion.word)
        else:
            segments.append(
                f"<{current_emotion}>{' '.join(current_words)}</{current_emotion}>"
            )
            current_emotion = word_emotion.emotion
            current_words = [word_emotion.word]

    segments.append(f"<{current_emotion}>{' '.join(current_words)}</{current_emotion}>")
    return " ".join(segments)
