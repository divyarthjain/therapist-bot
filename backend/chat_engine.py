"""
Ollama Chat Engine — Therapeutic conversation with emotion awareness.
Uses gemma3:4b-it-q8_0 via Ollama for local, private LLM inference.

Features:
- Emotion-aware system prompt that adapts based on detected emotions
- Streaming responses via async generator
- Conversation history management
- Safety boundaries (crisis detection, appropriate referrals)
"""

import logging
from typing import AsyncGenerator, Optional

from ollama import AsyncClient

logger = logging.getLogger(__name__)

OLLAMA_MODEL = "gemma3:4b-it-q8_0"
OLLAMA_HOST = "http://localhost:11434"

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
- Remember and reference earlier parts of the conversation to show you're truly listening."""


def build_emotion_context(fused_emotion: Optional[dict]) -> str:
    """Build an emotion context addendum for the system prompt."""
    if not fused_emotion:
        return ""

    parts = []

    audio_emo = fused_emotion.get("audio", {})
    video_emo = fused_emotion.get("video", {})
    dominant = fused_emotion.get("dominant", "neutral")
    confidence = fused_emotion.get("confidence", 0.0)

    parts.append(f"\n\n## Current Emotional State (Detected)")
    parts.append(f"- **Dominant emotion**: {dominant} (confidence: {confidence:.0%})")

    if audio_emo.get("emotion") and audio_emo["emotion"] != "neutral":
        parts.append(f"- **Voice tone**: {audio_emo['emotion']}")

    if video_emo.get("emotion") and video_emo["emotion"] != "neutral":
        parts.append(f"- **Facial expression**: {video_emo['emotion']}")

    # Detect emotional incongruence (saying one thing, showing another)
    if (
        audio_emo.get("emotion")
        and video_emo.get("emotion")
        and audio_emo["emotion"] != video_emo["emotion"]
        and audio_emo["emotion"] != "neutral"
        and video_emo["emotion"] != "neutral"
    ):
        parts.append(
            f"- ⚠️ **Incongruence detected**: Voice suggests '{audio_emo['emotion']}' "
            f"but facial expression shows '{video_emo['emotion']}'. "
            f"Gently explore this if appropriate."
        )

    # Guidance based on specific emotions
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


class ChatEngine:
    """Async Ollama chat engine with therapeutic persona and emotion awareness."""

    def __init__(self, model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST):
        self.model = model
        self.client = AsyncClient(host=host)
        logger.info(f"Chat engine initialized with model: {model}")

    def _build_messages(
        self,
        messages: list[dict],
        fused_emotion: Optional[dict] = None,
    ) -> list[dict]:
        """Build the full message list with system prompt + emotion context."""
        system_prompt = BASE_SYSTEM_PROMPT + build_emotion_context(fused_emotion)

        full_messages = [{"role": "system", "content": system_prompt}]

        # Include conversation history (keep last 20 messages to fit context)
        history = messages[-20:] if len(messages) > 20 else messages
        full_messages.extend(history)

        return full_messages

    async def chat(
        self,
        messages: list[dict],
        fused_emotion: Optional[dict] = None,
    ) -> str:
        """Non-streaming chat. Returns full response text."""
        full_messages = self._build_messages(messages, fused_emotion)

        try:
            response = await self.client.chat(
                model=self.model,
                messages=full_messages,
                stream=False,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1024,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return f"I'm having trouble connecting to my thinking engine right now. Please make sure Ollama is running (`ollama serve`). Error: {str(e)}"

    async def chat_stream(
        self,
        messages: list[dict],
        fused_emotion: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat. Yields individual tokens."""
        full_messages = self._build_messages(messages, fused_emotion)

        try:
            stream = await self.client.chat(
                model=self.model,
                messages=full_messages,
                stream=True,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1024,
                },
            )
            async for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content

        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"Connection error: {str(e)}. Please ensure Ollama is running."
