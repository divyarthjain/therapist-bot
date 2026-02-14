"""
Speech Emotion Recognition (SER) Module
Using Wav2Vec2 for frame-level emotion analysis.
"""

import os
import torch
import logging
import numpy as np
import scipy.io.wavfile
import scipy.signal
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Canonical emotions required by the system
CANONICAL_EMOTIONS = [
    "happy",
    "sad",
    "angry",
    "neutral",
    "fearful",
    "disgusted",
    "surprised",
]

# Mapping from model specific labels to canonical labels
# Model: ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition
# Model labels: 0: angry, 1: calm, 2: disgust, 3: fearful, 4: happy, 5: neutral, 6: sad, 7: surprised
LABEL_MAPPING = {
    "angry": "angry",
    "calm": "neutral",  # Map calm to neutral
    "disgust": "disgusted",  # Map disgust to disgusted
    "fearful": "fearful",
    "happy": "happy",
    "neutral": "neutral",
    "sad": "sad",
    "surprised": "surprised",
}


class SpeechEmotionRecognizer:
    """
    Wav2Vec2-based emotion recognizer.
    Provides frame-level emotion analysis (approx. every 20ms).
    """

    def __init__(self, device: Optional[str] = None):
        if device:
            self.device = device
        elif os.environ.get("SER_DEVICE"):
            self.device = os.environ["SER_DEVICE"]
        else:
            try:
                self.device = "mps" if torch.backends.mps.is_available() else "cpu"
            except Exception:
                self.device = "cpu"

        logger.info(f"Initializing SER on device: {self.device}")

        self.model_name = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
        self._loaded = False
        self.model = None
        self.processor = None

        try:
            self.processor = AutoFeatureExtractor.from_pretrained(self.model_name)
            self.model = AutoModelForAudioClassification.from_pretrained(
                self.model_name
            )
            self.model.to(self.device)
            self.model.eval()
            self._loaded = True
            logger.info(f"SER model {self.model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SER model: {e}")
            self._loaded = False

    def analyze_frames(self, audio_path: str) -> List[Dict[str, float]]:
        """
        Analyze audio file and return emotion probabilities per frame.

        Args:
            audio_path: Path to audio file.

        Returns:
            List of dicts: [{"timestamp": 0.0, "emotion": "neutral", "confidence": 0.9}, ...]
        """
        if not self._loaded:
            logger.warning("SER model not loaded, returning empty analysis")
            return []

        try:
            # Load audio using scipy
            sample_rate, waveform = scipy.io.wavfile.read(audio_path)

            # Convert to float32 normalized to [-1, 1]
            if waveform.dtype == np.int16:
                waveform = waveform.astype(np.float32) / 32768.0
            elif waveform.dtype == np.int32:
                waveform = waveform.astype(np.float32) / 2147483648.0
            elif waveform.dtype == np.uint8:
                waveform = (waveform.astype(np.float32) - 128) / 128.0

            # Convert to mono if stereo
            if len(waveform.shape) > 1:
                waveform = np.mean(waveform, axis=1)

            # Resample to 16kHz
            target_sr = 16000
            if sample_rate != target_sr:
                num_samples = int(len(waveform) * target_sr / sample_rate)
                waveform = scipy.signal.resample(waveform, num_samples)
                sample_rate = target_sr

            # Process with transformers
            inputs = self.processor(
                waveform, sampling_rate=16000, return_tensors="pt", padding=True
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                # Forward pass to get hidden states
                outputs = self.model.wav2vec2(**inputs)
                hidden_states = outputs.last_hidden_state

                # Apply classifier head manually to each frame
                if hasattr(self.model, "projector"):
                    projected = self.model.projector(hidden_states)
                    logits = self.model.classifier(projected)
                else:
                    logits = self.model.classifier(hidden_states)

                probs = torch.softmax(logits, dim=-1)

                # Convert to list of frame results
                results = []
                probs_np = probs.cpu().numpy()[0]  # Batch size 1

                # Get label mapping from model config
                id2label = self.model.config.id2label

                # Wav2Vec2 downsampling factor is 320
                # Frame duration = 320 / 16000 = 0.02s (20ms)
                frame_duration = 0.02

                for i, frame_probs in enumerate(probs_np):
                    # Get top emotion
                    top_idx = np.argmax(frame_probs)
                    top_prob = float(frame_probs[top_idx])
                    raw_label = id2label[top_idx]

                    # Map to canonical label
                    emotion = LABEL_MAPPING.get(raw_label, "neutral")

                    timestamp = i * frame_duration

                    results.append(
                        {
                            "timestamp": round(timestamp, 3),
                            "emotion": emotion,
                            "confidence": round(top_prob, 3),
                            "raw_label": raw_label,
                        }
                    )

                return results

        except Exception as e:
            logger.error(f"Error in SER analysis: {e}")
            return []


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    ser = SpeechEmotionRecognizer()
    if ser._loaded:
        # Create a dummy audio file for testing
        import soundfile as sf

        dummy_audio = np.random.uniform(-1, 1, 16000)  # 1 sec noise
        sf.write("test_audio.wav", dummy_audio, 16000)

        frames = ser.analyze_frames("test_audio.wav")
        print(f"Analyzed {len(frames)} frames")
        if frames:
            print(f"First frame: {frames[0]}")

        os.remove("test_audio.wav")
