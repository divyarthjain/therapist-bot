# Memory Feasibility Report

**Generated:** 2026-02-14

## Decision: NO-GO

**Total Projected Memory:** ~26GB (exceeds 22GB hard limit)

### Reason

VibeVoice-ASR model loading requires:
- VibeVoice-ASR model: ~14GB  
- Qwen2.5-7B backbone: ~7GB
- Ollama (gemma3:4b): ~4GB
- TTS model (Realtime-0.5B): ~1GB
- **Total: ~26GB > 22GB hard limit**

### Action

**Use SenseVoice fallback in Task 4** - The existing SenseVoice implementation will remain primary for ASR, supplemented with:
- Simple word-level timestamp estimation (split text on word boundaries, distribute time evenly)
- OR integration with WhisperX for word-level timestamps if memory allows

This preserves the core functionality (word-level emotion tagging) while staying within memory constraints.

### Technical Details

- Device: MPS (Apple Silicon)
- VibeVoice package: Installed from /Users/divyarth/Projects/VibeVoice
- Model size: ~14GB for ASR + ~7GB for Qwen backbone
- Alternative: SenseVoice (~1-2GB) + simple timestamp estimation (~0GB)
