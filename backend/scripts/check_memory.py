#!/usr/bin/env python3
"""
Memory Feasibility Check for VibeVoice-ASR

This script loads the VibeVoice-ASR model and measures memory usage
to determine if we have enough RAM (24GB total, 20GB threshold) to run
VibeVoice-ASR + Ollama LLM + TTS simultaneously.

Decision:
- GO: Total RSS < 20GB → Use VibeVoice-ASR
- NO-GO: Total RSS >= 20GB → Use SenseVoice fallback
"""

import os
import sys
import time
import logging
import resource
import subprocess
import torch

# Import VibeVoice to register custom model types
try:
    import vibevoice

    VIBEVOICE_AVAILABLE = True
except ImportError:
    VIBEVOICE_AVAILABLE = False

from transformers import AutoModel, AutoProcessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_process_memory_mb():
    """Get current process memory in MB (macOS)."""
    # On macOS, ru_maxrss is in bytes
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / (1024 * 1024)


def get_ollama_memory_mb():
    """Get Ollama process memory usage in MB."""
    try:
        result = subprocess.run(
            ["ps", "-o", "rss=", "-p", "$(pgrep -f ollama)"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            # RSS is in KB on macOS
            rss_kb = int(result.stdout.strip())
            return rss_kb / 1024
        else:
            logger.warning("Ollama process not found - assuming 4GB for gemma3:4b")
            return 4096  # Conservative estimate
    except Exception as e:
        logger.error(f"Error checking Ollama memory: {e}")
        return 4096


def main():
    logger.info("=" * 70)
    logger.info("MEMORY FEASIBILITY CHECK - VibeVoice-ASR")
    logger.info("=" * 70)

    # Check baseline memory
    baseline_memory = get_process_memory_mb()
    logger.info(f"Baseline Python process memory: {baseline_memory:.1f} MB")

    # Check Ollama memory
    ollama_memory = get_ollama_memory_mb()
    logger.info(f"Ollama process memory (gemma3:4b): {ollama_memory:.1f} MB")

    # Determine device
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    logger.info(f"Device: {device}")

    # Load VibeVoice-ASR model
    logger.info("\nLoading VibeVoice-ASR model (microsoft/VibeVoice-ASR)...")
    logger.info(
        "This may take several minutes on first run (downloading ~14GB model)..."
    )

    start_time = time.time()
    try:
        if not VIBEVOICE_AVAILABLE:
            raise ImportError("VibeVoice package not installed")

        from vibevoice import (
            VibeVoiceStreamingForConditionalGenerationInference,
            VibeVoiceStreamingProcessor,
        )

        # Load processor
        processor = VibeVoiceStreamingProcessor.from_pretrained(
            "microsoft/VibeVoice-ASR"
        )
        logger.info("Processor loaded")

        # Load model using VibeVoice's custom class
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            "microsoft/VibeVoice-ASR",
            torch_dtype=torch.float16 if device == "mps" else torch.float32,
            low_cpu_mem_usage=True,
        )
        model.to(device)
        logger.info("Model loaded and moved to device")

        load_time = time.time() - start_time
        logger.info(f"Load time: {load_time:.1f}s")

    except Exception as e:
        logger.error(f"Failed to load VibeVoice-ASR: {e}")
        logger.info("\n❌ DECISION: NO-GO (model load failed)")
        logger.info("→ Use SenseVoice fallback")

        # Write report
        with open("/Users/divyarth/therapist-bot/backend/MEMORY_REPORT.md", "w") as f:
            f.write("# Memory Feasibility Report\n\n")
            f.write("**Decision:** NO-GO\n\n")
            f.write(f"**Reason:** VibeVoice-ASR failed to load: {e}\n\n")
            f.write("**Action:** Use SenseVoice fallback in Task 4\n")

        return 1

    # Measure memory after loading
    asr_memory = get_process_memory_mb()
    asr_delta = asr_memory - baseline_memory

    logger.info(f"\nMemory after loading VibeVoice-ASR: {asr_memory:.1f} MB")
    logger.info(f"ASR model memory delta: {asr_delta:.1f} MB")

    # Estimate TTS memory (VibeVoice-Realtime-0.5B is much smaller)
    tts_estimate = 1024  # ~1GB for 0.5B model

    # Calculate total
    total_memory_mb = ollama_memory + asr_delta + tts_estimate
    total_memory_gb = total_memory_mb / 1024

    logger.info(f"\n{'=' * 70}")
    logger.info("MEMORY PROJECTION")
    logger.info(f"{'=' * 70}")
    logger.info(f"Ollama (gemma3:4b):          {ollama_memory:>8.1f} MB")
    logger.info(f"VibeVoice-ASR (7B):          {asr_delta:>8.1f} MB")
    logger.info(f"VibeVoice-Realtime (0.5B):   {tts_estimate:>8.1f} MB (estimate)")
    logger.info(f"{'-' * 70}")
    logger.info(
        f"Total projected:             {total_memory_mb:>8.1f} MB ({total_memory_gb:.2f} GB)"
    )
    logger.info(f"{'-' * 70}")
    logger.info(f"Threshold:                   {20 * 1024:>8.1f} MB (20.00 GB)")
    logger.info(f"Hard limit:                  {22 * 1024:>8.1f} MB (22.00 GB)")
    logger.info(f"{'=' * 70}")

    # Decision logic
    THRESHOLD_GB = 20.0

    if total_memory_gb < THRESHOLD_GB:
        decision = "GO"
        action = "Use VibeVoice-ASR in Task 4"
        symbol = "✅"
    else:
        decision = "NO-GO"
        action = "Use SenseVoice fallback in Task 4"
        symbol = "❌"

    logger.info(f"\n{symbol} DECISION: {decision}")
    logger.info(f"→ {action}")

    # Write report file
    report_path = "/Users/divyarth/therapist-bot/backend/MEMORY_REPORT.md"
    with open(report_path, "w") as f:
        f.write("# Memory Feasibility Report\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Decision: {decision}\n\n")
        f.write(
            f"**Total Projected Memory:** {total_memory_gb:.2f} GB / 20.00 GB threshold\n\n"
        )
        f.write(f"### Breakdown\n\n")
        f.write(f"- Ollama (gemma3:4b): {ollama_memory:.1f} MB\n")
        f.write(f"- VibeVoice-ASR (7B): {asr_delta:.1f} MB\n")
        f.write(f"- VibeVoice-Realtime (0.5B): {tts_estimate:.1f} MB (estimate)\n")
        f.write(f"- **Total:** {total_memory_mb:.1f} MB ({total_memory_gb:.2f} GB)\n\n")
        f.write(f"### Action\n\n")
        f.write(f"{action}\n\n")
        f.write(f"### Technical Details\n\n")
        f.write(f"- Device: {device}\n")
        f.write(f"- Model load time: {load_time:.1f}s\n")
        f.write(f"- Baseline memory: {baseline_memory:.1f} MB\n")
        f.write(f"- ASR memory after load: {asr_memory:.1f} MB\n")

    logger.info(f"\nReport written to: {report_path}")
    logger.info(f"{'=' * 70}\n")

    # Clean up (unload model)
    del model
    del processor
    if device == "mps":
        torch.mps.empty_cache()

    return 0 if decision == "GO" else 1


if __name__ == "__main__":
    sys.exit(main())
