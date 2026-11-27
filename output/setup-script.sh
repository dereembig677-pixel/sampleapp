#!/bin/bash
# Self-contained setup script: installs all 15 video repos as Claude Code skills (no repo files needed).
# Usable as a cloud-environment setup script. Needs github.com, pypi.org, registry.npmjs.org.
set -uo pipefail
R="${REPOS_DIR:-/opt/claude-video-repos}"; S="${SKILLS_DIR:-$HOME/.claude/skills}"; mkdir -p "$R/iart-packs" "$S"
clone() { [ -d "$2/.git" ] || git clone -q --depth 1 "https://github.com/$1.git" "$2"; }

for r in kajisho5/ffmpeg-skill howseen-ai/claude-motion-design kurbaitaev/ghost-editor AgriciDaniel/claude-shorts \
  CloudAI-X/threejs-skills artemnovitckii/claude-animation-skills iart-ai/motion-skills Barty-Bart/motion-graphics \
  mattypark/Motion-graphics-skill LPengYang/MotionClone viettranx/3dviz-pro-max heygen-com/hyperframes \
  zhuyansen/awesome-claude-video-skills; do clone "$r" "$R/${r//\//_}"; done
for p in tiktok-video text-message-video youtube-video ecommerce-video ad-video data-animation explainer-video \
  map-animation web-animation motion-design kinetic-typography freelance-motion webgl-animation manim \
  generative-illustration javascript-animation lower-thirds b-roll talking-head; do
  clone "iart-ai/$p-skills" "$R/iart-packs/$p-skills"; done

# yt-dlp + whisper (torch comes from PyPI; download.pytorch.org is usually blocked)
pip install -q -U yt-dlp openai-whisper faster-whisper mediapipe opencv-python-headless numpy pillow google-genai "av<19"  # av 19 breaks faster-whisper (metadata_errors)

cd "$R"
copy() { mkdir -p "$S/$2" && tar -C "$1" --exclude .git --exclude node_modules --exclude ./.claude --exclude ./.agents -cf - . | tar -C "$S/$2" -xf -; }
for d in Barty-Bart_motion-graphics/skills/*/ CloudAI-X_threejs-skills/skills/*/ artemnovitckii_claude-animation-skills/skills/*/ \
  heygen-com_hyperframes/skills/*/ mattypark_Motion-graphics-skill/skills/*/ viettranx_3dviz-pro-max/skills/*/ \
  iart-packs/*/skills/*/ howseen-ai_claude-motion-design/skill/motion-design/ kajisho5_ffmpeg-skill/ kurbaitaev_ghost-editor/; do
  d=${d%/}; n=$(grep -m1 '^name:' "$d/SKILL.md" | sed "s/name:[ ]*//;s/[\"']//g")
  case "$d" in
    iart-packs/tiktok-video-skills/skills/lower-thirds) n=tiktok-lower-thirds ;;
    iart-packs/webgl-animation-skills/skills/threejs-animation) n=webgl-threejs-animation ;;
  esac
  copy "$d" "$n"; sed -i "0,/^name:.*/s//name: $n/" "$S/$n/SKILL.md"
done
# claude-shorts (its install.sh needs rsync, so copy by hand)
mkdir -p "$S/shorts" && cp -r AgriciDaniel_claude-shorts/{SKILL.md,scripts,references} "$S/shorts/"
copy AgriciDaniel_claude-shorts/remotion shorts/remotion && (cd "$S/shorts/remotion" && npm install --no-audit --no-fund -s)
# ghost-editor hardcodes gemini-2.5-flash/-pro, which Google has retired (404). Point them at a live model.
GE_MODEL="${GHOST_GEMINI_MODEL:-gemini-3.5-flash-lite}"
grep -rlE 'gemini-2\.5-(flash|pro)([^-]|$)' --include=*.py --include=*.sh --include=*.mjs "$S/ghost-editor/scripts" 2>/dev/null \
  | xargs -r sed -i -E "s/gemini-2\.5-(flash|pro)([^-a-z]|\$)/$GE_MODEL\2/g"
# ghost-editor reads GEMINI_API_KEY from the environment; set it in the cloud environment's variables, not in the repo.
# Sound effects + music library (needs assets.mixkit.co):
python3 "$S/ghost-editor/scripts/library_restore.py" --sfx-only >/dev/null 2>&1 || true
python3 "$S/ghost-editor/scripts/library_restore.py" --music-only >/dev/null 2>&1 || true
echo "Installed $(ls "$S"/*/SKILL.md | wc -l) skills"
# The 4 wrapper skills (yt-dlp, whisper-transcribe, motionclone, awesome-claude-video-skills) live in this
# repo's .claude/skills and load automatically as project skills.
pip install -q transformers rembg onnxruntime || true

# --- the 4 hand-written wrapper skills ---
mkdir -p "$S/yt-dlp" && cat > "$S/yt-dlp/SKILL.md" <<'SKILLEOF'
---
name: yt-dlp
description: Download video/audio, subtitles, thumbnails and metadata from YouTube and ~1800 other sites with the installed yt-dlp CLI. Use when the user gives a video URL to fetch, wants audio extracted, a clip section, subtitles, or a reference video pulled from a link.
---
# yt-dlp (source: github.com/yt-dlp/yt-dlp, installed via pip)

- Best MP4: `yt-dlp -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b" -o "%(title)s.%(ext)s" URL`
- Audio only: `yt-dlp -x --audio-format mp3 URL`
- Section: `yt-dlp --download-sections "*00:01:00-00:01:30" URL`
- Subtitles: `yt-dlp --write-auto-subs --sub-langs en --skip-download URL`
- Info only: `yt-dlp -J URL` / `--simulate --print title`
Only download content the user has rights to use. Network policy must allow the site's hosts.
SKILLEOF
mkdir -p "$S/whisper-transcribe" && cat > "$S/whisper-transcribe/SKILL.md" <<'SKILLEOF'
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
SKILLEOF
mkdir -p "$S/motionclone" && cat > "$S/motionclone/SKILL.md" <<'SKILLEOF'
---
name: motionclone
description: MotionClone (training-free motion cloning for controllable video generation, text-to-video / image-to-video guided by a reference video's motion). Use when the user asks to transfer/clone motion from a reference video to new generated content.
---
# MotionClone (source: github.com/LPengYang/MotionClone, code at /opt/claude-video-repos/LPengYang_MotionClone)

Research code based on AnimateDiff + Stable Diffusion 1.5. Requirements (see its README / environment.yaml):
an NVIDIA GPU with lots of VRAM, the conda env from environment.yaml, and SD1.5 / AnimateDiff motion-module / SparseCtrl weights from Hugging Face placed under `models/`.
Run: `python t2v_video_sample.py --inference_config configs/t2v_camera.yaml --examples configs/t2v_camera.jsonl` (or `i2v_video_sample.py`).
This container has no GPU, so tell the user it cannot run here. Use it on a GPU machine. For CPU-only motion work, use the code-driven motion skills instead.
SKILLEOF
mkdir -p "$S/awesome-claude-video-skills" && cat > "$S/awesome-claude-video-skills/SKILL.md" <<'SKILLEOF'
---
name: awesome-claude-video-skills
description: Curated index of Claude video/motion skills (from zhuyansen/awesome-claude-video-skills). Use when the user asks which video skill to use, wants to find or install another video/animation skill, or compare options.
---
# Awesome Claude video skills (index)

`skills.json` in this folder is the full catalogue (name, repo, description, stars). Search it, e.g.
`grep -n -i caption <skill-dir>/skills.json` (top-level keys: generated, source, kinds, skills; open it to see the structure).
To install a listed skill: clone its repo and copy the folder that contains SKILL.md into ~/.claude/skills/<name>/.
Full README: /opt/claude-video-repos/zhuyansen_awesome-claude-video-skills/README.md
SKILLEOF
cp "$R/zhuyansen_awesome-claude-video-skills/data/skills.json" "$S/awesome-claude-video-skills/" 2>/dev/null || true
exit 0
