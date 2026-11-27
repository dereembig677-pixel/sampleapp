---
name: edit-video
description: Full professional short-form video editing workflow for this user (YouTube Shorts / Instagram reels, Persian or English). Activates and orchestrates all installed video skills. Use when the user types /edit-video, or asks to edit / ادیت a video, make a Short or reel, add subtitles, B-roll, motion graphics or sound design.
---

# /edit-video — orchestrates every video skill

Arguments (optional): the user's brief, timeline notes, fonts, references.

## 0. Make sure the tools exist
The cloud container is wiped between sessions. If `~/.claude/skills/ffmpeg-skill` is missing, run
`bash scripts/install-video-skills.sh` first (installs all 15 video repos as skills, yt-dlp, Whisper,
faster-whisper, PyTorch). For Persian subtitle alignment also `pip install transformers rembg onnxruntime`.

## 1. Load the skills, in this order
1. **video-references** — ALWAYS first: the user's saved references and standing style preferences
   (white + yellow text only, YouTube safe zone, professional motion, exact subtitle sync).
2. **whisper-transcribe** — speech to text with word timings.
3. **ffmpeg-skill** — probe, cut, loudness, export, checks.
4. Pick the motion / graphics skills that fit the brief:
   - `hyperframes`, `hyperframes-registry` (HTML → video, ready-made blocks),
   - `kinetic-typography`, `caption-animation`, `short-form-video`, `motion-broll`, `explainer-video`,
   - `ghost-editor` (talking-head reels: best takes, pauses, captions, text-behind-subject matte),
   - `shorts` (long video → shorts), `sound-effects`, `soundtrack`, `video-delivery-specs`,
   - `threejs-*` / `3dviz-pro-max` only when 3D is really needed.
5. If the user gives a reference video: follow CLAUDE.md — save it into `video-references` first.

## 2. Workflow (do the edit, don't just plan it)
1. **Watch first**: probe, contact sheets with timestamps, cut/scene detection, audio loudness and pauses.
2. **Transcript**: Whisper large-v3 with a domain-vocabulary `initial_prompt`; correct the text by context.
   Persian: CTC force-align with `jonatasgrosman/wav2vec2-large-xlsr-53-persian` for exact word times;
   split lines by meaning (2–4 words); hide subtitles during pauses; never translate.
   Leave out words that can't be made out and tell the user which ones.
3. **Edit plan** from the actual content, then follow the user's timeline instructions literally
   (check ambiguous words in context, e.g. «بکس» in a garage = socket, not boxing).
4. **B-roll**: free licensed sources (Mixkit works from this container; Pexels/Pixabay block bots).
   Never Gemini / Nano Banana. Credit sources in `CREDITS.txt`.
5. **Build**: graphics in an HTML canvas page with a deterministic `render(t)`, rendered with Playwright to
   transparent PNGs; composite in Python/OpenCV (zooms, B-roll, VFX, matte); render in parallel workers.
6. **Sound**: speech dominant and clean (limit clipping), light ducked music, sparse SFX on real moments;
   loudness -14 LUFS, true peak ≤ -1 dB.
7. **QC before delivering**: full contact sheets, black/freeze detection, subtitle sync, Persian RTL/ZWNJ/
   digits, safe zone, audio balance. Fix and re-render.
8. **Deliver**: 1080×1920 H.264 + AAC, < 100 MB if it goes into git; save the render project in
   `output/<name>-project/` (never commit licensed fonts); commit, push, send the file.
