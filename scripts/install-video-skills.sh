#!/usr/bin/env bash
# Reinstalls the 15 Claude video-editor repos as skills into ~/.claude/skills.
# Usable as a cloud-environment setup script. Needs github.com, pypi.org, registry.npmjs.org.
set -uo pipefail
R=/opt/claude-video-repos; S="$HOME/.claude/skills"; mkdir -p "$R/iart-packs" "$S"
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
pip install -q -U yt-dlp openai-whisper faster-whisper mediapipe opencv-python-headless numpy pillow google-genai

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
echo "Installed $(ls "$S"/*/SKILL.md | wc -l) skills"
# The 4 wrapper skills (yt-dlp, whisper-transcribe, motionclone, awesome-claude-video-skills) live in this
# repo's .claude/skills and load automatically as project skills.
