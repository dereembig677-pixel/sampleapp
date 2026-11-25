# Helper status

Network check (2026-11-25):

| Host | Result |
|---|---|
| https://huggingface.co | blocked — `000` (proxy: CONNECT tunnel failed, response 403) |
| https://dl.fbaipublicfiles.com | blocked — `000` (proxy: CONNECT tunnel failed, response 403) |
| https://pypi.org | reachable (200) |

Because huggingface.co is blocked in this environment too, the faster-whisper `large-v3`
model and the demucs `htdemucs` weights cannot be downloaded. No transcription or stem
separation was run. To unblock, add `huggingface.co` (and `dl.fbaipublicfiles.com` for
demucs) to the environment's network allowlist, or provide the model files another way.
