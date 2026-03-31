"""
Gemini Chat Engine — Therapeutic conversation with emotion awareness.
Uses the Gemini API with a strong system instruction for empathetic responses.
"""

import json
import logging
import os
import re
from typing import Any, AsyncGenerator, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_BASE = os.getenv(
    "GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta"
)

# ── Therapeutic System Prompt ─────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """You are a compassionate, professional AI therapeutic companion. Your role is to provide empathetic, evidence-based emotional support through active listening and gentle guidance.

## Your Approach
- **Active Listening**: Reflect back what the user shares. Use phrases like "It sounds like you're feeling..." or "I hear that..."
- **Socratic Questioning**: Help users explore their thoughts with open-ended questions rather than giving direct advice.
- **Cognitive Behavioral Techniques**: When appropriate, help identify thought patterns, cognitive distortions, and reframing opportunities.
- **Validation**: Always validate emotions before exploring solutions. "It's completely understandable to feel that way."
- **Non-judgmental**: Never criticize, moralize, or dismiss feelings.

## Emotional Intelligence
You have access to real-time emotion data from the user's voice and facial expressions. Use this information subtly:
- If you detect sadness in their voice/face but they say "I'm fine", gently acknowledge: "I notice there might be more beneath the surface. Would you like to talk about it?"
- Match your energy to the user — don't be overly cheerful when they're distressed.
- If emotions shift during conversation, acknowledge the shift naturally.

## Boundaries (CRITICAL)
- You are an AI companion, NOT a licensed therapist. State this if asked directly.
- NEVER diagnose mental health conditions.
- If the user mentions self-harm, suicidal thoughts, or intent to harm others, IMMEDIATELY:
  1. Express care and concern
  2. Provide crisis resources:
     - International: 988 Suicide & Crisis Lifeline (call/text 988)
     - India: iCall (9152987821), Vandrevala Foundation (1860-2662-345)
     - Crisis Text Line: Text HOME to 741741
  3. Encourage them to reach out to a trusted person or professional
- Do NOT roleplay harmful scenarios or provide medical/psychiatric advice.

## Multilingual Support
Respond in the same language the user communicates in. You support Hindi, English, Japanese, Korean, Chinese, and many more languages naturally.

## Conversation Style
- Keep responses concise (2-4 paragraphs max) unless the user wants more depth.
- Use warm, natural language — not clinical jargon.
- Ask one follow-up question at the end of each response to keep dialogue flowing.
- Remember and reference earlier parts of the conversation to show you're truly listening.

## Word-Level Emotion Analysis
When the user's message contains emotion-tagged text in the format `<emotion>words</emotion>`, this represents real-time speech emotion detected at the word level. For example:
- `<neutral>I really thought</neutral> <sad>it would be different this time</sad>`
- This means the words "I really thought" were spoken neutrally, but "it would be different this time" had sadness detected in the voice.

Use these emotion tags to:
1. Understand the emotional journey within a single utterance
2. Identify which specific topics/words trigger emotional shifts
3. Respond with appropriate empathy to the most emotionally charged segments

When responding, start your response with a target emotion tag on its own line:
`[Target Emotion: empathetic]`
This tells the text-to-speech system what emotion to use for your voice response.
Valid target emotions: happy, sad, angry, neutral, empathetic, fearful
Choose the emotion that best matches the therapeutic tone of your response."""


def build_emotion_context(
    fused_emotion: Optional[dict] = None,
    tagged_text: Optional[str] = None,
    mood_context: Optional[str] = None,
) -> str:
    """Build an emotion context addendum for the system prompt."""
    if not fused_emotion and not tagged_text and not mood_context:
        return ""

    parts = []

    if tagged_text:
        parts.append("\n\n## Word-Level Emotion Tags (from user's speech)")
        parts.append(f"The user said: {tagged_text}")

    if mood_context:
        parts.append("\n\n## Recent Mood Timeline (internal therapist context)")
        parts.append(
            "Use this only as quiet context for emotional continuity. Do not mention "
            "an internal log, hidden file, or tracking mechanism unless the user asks directly."
        )
        parts.append(mood_context)

    if fused_emotion:
        audio_emo = fused_emotion.get("audio", {})
        video_emo = fused_emotion.get("video", {})
        dominant = fused_emotion.get("dominant", "neutral")
        confidence = fused_emotion.get("confidence", 0.0)

        parts.append("\n\n## Current Emotional State (Detected)")
        parts.append(
            f"- **Dominant emotion**: {dominant} (confidence: {confidence:.0%})"
        )

        if audio_emo.get("emotion") and audio_emo["emotion"] != "neutral":
            parts.append(f"- **Voice tone**: {audio_emo['emotion']}")

        if video_emo.get("emotion") and video_emo["emotion"] != "neutral":
            parts.append(f"- **Facial expression**: {video_emo['emotion']}")

        if (
            audio_emo.get("emotion")
            and video_emo.get("emotion")
            and audio_emo["emotion"] != video_emo["emotion"]
            and audio_emo["emotion"] != "neutral"
            and video_emo["emotion"] != "neutral"
        ):
            parts.append(
                f"- **Incongruence detected**: Voice suggests '{audio_emo['emotion']}' "
                f"but facial expression shows '{video_emo['emotion']}'. "
                f"Gently explore this if appropriate."
            )

        if dominant in ("sad", "fearful"):
            parts.append(
                "- Approach with extra gentleness and warmth. Prioritize validation."
            )
        elif dominant == "angry":
            parts.append(
                "- Acknowledge the anger without escalating. Help explore what's underneath."
            )
        elif dominant == "happy":
            parts.append("- Share in their positive energy. Explore what's going well.")
        elif dominant == "surprised":
            parts.append(
                "- Help them process what surprised them. Check if it's positive or negative surprise."
            )

    return "\n".join(parts)


def parse_llm_response(response: str) -> tuple[str, str]:
    """Extract target emotion and clean text from LLM response."""
    pattern = r"^\s*\[Target Emotion:\s*([\w-]+)\]\s*"
    match = re.search(pattern, response, re.IGNORECASE)

    if match:
        target_emotion = match.group(1).lower()
        clean_text = response[match.end() :].strip()
        return target_emotion, clean_text

    return "neutral", response.strip()


def extract_text_from_candidate(payload: dict[str, Any]) -> str:
    """Read text from Gemini candidate payload."""
    parts = payload.get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    return "".join(text_parts)


class ChatEngine:
    """Gemini chat engine with therapeutic persona and emotion awareness."""

    def __init__(
        self,
        model: str = GEMINI_MODEL,
        api_key: Optional[str] = GEMINI_API_KEY,
        api_base: str = GEMINI_API_BASE,
    ):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.model = model
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=30.0),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
        )
        logger.info("Chat engine initialized with Gemini model: %s", model)

    def _build_contents(
        self,
        messages: list[dict],
        fused_emotion: Optional[dict] = None,
        tagged_text: Optional[str] = None,
        mood_context: Optional[str] = None,
    ) -> list[dict]:
        history = messages[-20:] if len(messages) > 20 else messages
        contents: list[dict] = []

        for index, message in enumerate(history):
            role = "model" if message["role"] == "assistant" else "user"
            content = message["content"]

            if tagged_text and index == len(history) - 1 and role == "user":
                content = (
                    f"[Transcribed with emotions]: {tagged_text}\n\n"
                    f"{message['content']}"
                )

            contents.append({"role": role, "parts": [{"text": content}]})

        return contents

    def _build_payload(
        self,
        messages: list[dict],
        fused_emotion: Optional[dict] = None,
        tagged_text: Optional[str] = None,
        mood_context: Optional[str] = None,
    ) -> dict[str, Any]:
        system_prompt = BASE_SYSTEM_PROMPT + build_emotion_context(
            fused_emotion, tagged_text, mood_context
        )
        return {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": self._build_contents(messages, fused_emotion, tagged_text),
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "topK": 40,
                "maxOutputTokens": 1024,
                "responseMimeType": "text/plain",
            },
        }

    async def chat(
        self,
        messages: list[dict],
        fused_emotion: Optional[dict] = None,
        tagged_text: Optional[str] = None,
        mood_context: Optional[str] = None,
    ) -> str:
        payload = self._build_payload(messages, fused_emotion, tagged_text, mood_context)
        url = f"{self.api_base}/models/{self.model}:generateContent"

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned no candidates")
            return extract_text_from_candidate(candidates[0])
        except Exception as exc:
            logger.error("Gemini chat error: %s", exc)
            return (
                "I'm having trouble reaching the Gemini therapist engine right now. "
                "Please verify GEMINI_API_KEY and GEMINI_MODEL, then try again."
            )

    async def chat_stream(
        self,
        messages: list[dict],
        fused_emotion: Optional[dict] = None,
        tagged_text: Optional[str] = None,
        mood_context: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        payload = self._build_payload(messages, fused_emotion, tagged_text, mood_context)
        url = f"{self.api_base}/models/{self.model}:streamGenerateContent?alt=sse"
        prefix_buffer = ""
        tag_consumed = False

        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    raw_data = line[6:].strip()
                    if raw_data == "[DONE]":
                        break

                    try:
                        data = json.loads(raw_data)
                    except json.JSONDecodeError:
                        logger.debug("Skipping non-JSON SSE chunk: %s", raw_data)
                        continue

                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    chunk_text = extract_text_from_candidate(candidates[0])
                    if not chunk_text:
                        continue

                    if tag_consumed:
                        yield chunk_text
                        continue

                    prefix_buffer += chunk_text
                    match = re.match(
                        r"^\s*\[Target Emotion:\s*([\w-]+)\]\s*",
                        prefix_buffer,
                        re.IGNORECASE,
                    )

                    if match:
                        tag_consumed = True
                        clean_prefix = prefix_buffer[match.end() :].strip()
                        if clean_prefix:
                            yield clean_prefix
                        prefix_buffer = ""
                        continue

                    if len(prefix_buffer) > 80 or ("\n" in prefix_buffer and "[Target Emotion:" not in prefix_buffer):
                        tag_consumed = True
                        if prefix_buffer:
                            yield prefix_buffer
                        prefix_buffer = ""

            if prefix_buffer:
                yield prefix_buffer

        except Exception as exc:
            logger.error("Gemini stream error: %s", exc)
            yield (
                "I hit a connection issue while speaking. "
                "Please verify the Gemini API configuration and try again."
            )

    async def close(self) -> None:
        await self.client.aclose()
