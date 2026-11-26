---
name: motionclone
description: MotionClone (training-free motion cloning for controllable video generation, text-to-video / image-to-video guided by a reference video's motion). Use when the user asks to transfer/clone motion from a reference video to new generated content.
---
# MotionClone (source: github.com/LPengYang/MotionClone, code at /opt/claude-video-repos/LPengYang_MotionClone)

Research code based on AnimateDiff + Stable Diffusion 1.5. Requirements (see its README / environment.yaml):
an NVIDIA GPU with lots of VRAM, the conda env from environment.yaml, and SD1.5 / AnimateDiff motion-module / SparseCtrl weights from Hugging Face placed under `models/`.
Run: `python t2v_video_sample.py --inference_config configs/t2v_camera.yaml --examples configs/t2v_camera.jsonl` (or `i2v_video_sample.py`).
This container has no GPU, so tell the user it cannot run here. Use it on a GPU machine. For CPU-only motion work, use the code-driven motion skills instead.
