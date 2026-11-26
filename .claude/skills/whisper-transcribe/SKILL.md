---
name: whisper-transcribe
description: Speech recognition / transcription / translation of audio or video with OpenAI Whisper (CLI `whisper`) or faster-whisper (Python, word timestamps). Use when the user wants a transcript, SRT/VTT subtitles, word-level timings for captions, or language detection.
---
# Whisper (source: github.com/openai/whisper; installed: openai-whisper + faster-whisper, CPU)

- CLI: `whisper input.mp4 --model small --output_format srt --output_dir out/` (add `--language fa`, `--task translate`, `--word_timestamps True`)
- Word timings (faster, CPU): 
  ```python
  from faster_whisper import WhisperModel
  m = WhisperModel("small", compute_type="int8")
  segs, info = m.transcribe("in.mp4", word_timestamps=True)
  ```
Models download on first use (openaipublic.azureedge.net for whisper, huggingface.co for faster-whisper); these hosts must be allowed by the network policy. No GPU here, so prefer tiny/base/small.
