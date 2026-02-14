import copy
import io
import logging
import os
from typing import List, Optional

import torch

logger = logging.getLogger(__name__)


class TTSEngine:
    MODEL_ID = "microsoft/VibeVoice-Realtime-0.5B"
    VOICES_DIR = "/Users/divyarth/Projects/VibeVoice/demo/voices/streaming_model"
    SAMPLE_RATE = 24000

    def __init__(self) -> None:
        try:
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        except Exception:
            self.device = "cpu"

        logger.info("Initializing VibeVoice TTS on device: %s", self.device)

        self._loaded = False
        self.model = None
        self.processor = None

        try:
            from vibevoice.modular.modeling_vibevoice_streaming_inference import (
                VibeVoiceStreamingForConditionalGenerationInference,
            )
            from vibevoice.processor.vibevoice_streaming_processor import (
                VibeVoiceStreamingProcessor,
            )

            self.processor = VibeVoiceStreamingProcessor.from_pretrained(self.MODEL_ID)

            if self.device == "mps":
                load_dtype = torch.float32
                attn_impl = "sdpa"
                self.model = (
                    VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                        self.MODEL_ID,
                        torch_dtype=load_dtype,
                        attn_implementation=attn_impl,
                        device_map=None,
                    )
                )
                self.model.to("mps")
            else:
                load_dtype = torch.float32
                attn_impl = "sdpa"
                self.model = (
                    VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                        self.MODEL_ID,
                        torch_dtype=load_dtype,
                        attn_implementation=attn_impl,
                        device_map="cpu",
                    )
                )

            self.model.eval()
            self.model.set_ddpm_inference_steps(num_steps=5)
            self._loaded = True
            logger.info("VibeVoice TTS model loaded successfully")
        except Exception as e:
            logger.error("Failed to load VibeVoice TTS: %s", e)
            logger.info("TTS engine will use fallback mode (no synthesis)")
            self._loaded = False
            self.model = None
            self.processor = None

    def is_loaded(self) -> bool:
        return self._loaded

    def get_available_voices(self) -> List[str]:
        if not os.path.isdir(self.VOICES_DIR):
            return []
        voice_paths = []
        for root, _, files in os.walk(self.VOICES_DIR):
            for filename in files:
                if filename.lower().endswith(".pt"):
                    voice_paths.append(os.path.join(root, filename))
        voice_names = sorted(
            {os.path.splitext(os.path.basename(p))[0].lower() for p in voice_paths}
        )
        return voice_names

    def get_supported_emotions(self) -> List[str]:
        return [
            "happy",
            "sad",
            "angry",
            "neutral",
            "empathetic",
            "fearful",
        ]

    def _resolve_voice_path(self, voice: str) -> Optional[str]:
        if not os.path.isdir(self.VOICES_DIR):
            return None
        voice = (voice or "").lower()
        voice_paths = []
        for root, _, files in os.walk(self.VOICES_DIR):
            for filename in files:
                if filename.lower().endswith(".pt"):
                    voice_paths.append(os.path.join(root, filename))
        if not voice_paths:
            return None
        voice_map = {
            os.path.splitext(os.path.basename(path))[0].lower(): path
            for path in voice_paths
        }
        if voice in voice_map:
            return voice_map[voice]
        if voice:
            partial_matches = [
                path
                for name, path in voice_map.items()
                if voice in name or name in voice
            ]
            if len(partial_matches) == 1:
                return partial_matches[0]
        return voice_map[sorted(voice_map.keys())[0]]

    def _condition_text(self, text: str, emotion: str) -> str:
        emotion_prefixes = {
            "happy": "[Speaking with warmth and cheerfulness] ",
            "sad": "[Speaking with gentle empathy and softness] ",
            "angry": "[Speaking with calm, measured firmness] ",
            "neutral": "",
            "empathetic": "[Speaking with deep warmth, understanding, and compassion] ",
            "fearful": "[Speaking with reassuring calmness] ",
        }
        prefix = emotion_prefixes.get((emotion or "neutral").lower(), "")
        return f"{prefix}{text}"

    def _audio_tensor_to_wav_bytes(self, audio_tensor: torch.Tensor) -> bytes:
        audio = audio_tensor.detach().float().cpu()
        if audio.dim() > 1:
            audio = audio.squeeze(0)
        audio = audio.clamp(-1.0, 1.0)
        audio_int16 = (audio * 32767.0).to(torch.int16).numpy()
        buffer = io.BytesIO()
        import wave

        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(audio_int16.tobytes())
        return buffer.getvalue()

    def generate_speech(
        self, text: str, emotion: str = "neutral", voice: str = "default"
    ) -> Optional[bytes]:
        if not self._loaded or not self.model or not self.processor:
            return None

        voice_path = self._resolve_voice_path(voice)
        if not voice_path:
            logger.error("No voice presets available; cannot synthesize")
            return None

        try:
            conditioned_text = self._condition_text(text, emotion)
            voice_sample = torch.load(
                voice_path,
                map_location=self.device,
                weights_only=False,
            )

            inputs = self.processor.process_input_with_cached_prompt(
                text=conditioned_text,
                cached_prompt=voice_sample,
                padding=True,
                return_tensors="pt",
                return_attention_mask=True,
            )

            for key, value in inputs.items():
                if torch.is_tensor(value):
                    inputs[key] = value.to(self.device)

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=None,
                cfg_scale=1.5,
                tokenizer=self.processor.tokenizer,
                generation_config={"do_sample": False},
                verbose=False,
                all_prefilled_outputs=copy.deepcopy(voice_sample),
            )

            if not outputs.speech_outputs or outputs.speech_outputs[0] is None:
                return None

            return self._audio_tensor_to_wav_bytes(outputs.speech_outputs[0])
        except Exception as e:
            logger.error("TTS generation failed: %s", e)
            return None
