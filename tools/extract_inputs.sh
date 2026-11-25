#!/bin/sh
# Restore working layout from inputs/ and extract footage + narration.
set -e
cd "$(dirname "$0")/.."
mkdir -p reference source footage narration output
cp inputs/reference_stickman.mp4 "reference/استیکمن.mp4"
cp inputs/narration_footage.mp4 source/input.mp4
ffmpeg -loglevel error -y -ss 0 -t 3.9 -i source/input.mp4 -an -c:v libx264 -crf 14 -pix_fmt yuv420p footage/f01_clip.mp4
python3 - <<'PY'
import subprocess
cuts=[3.9+3*i for i in range(27)]+[84.9333]
for i in range(len(cuts)-1):
    t=(cuts[i]+cuts[i+1])/2
    subprocess.run(["ffmpeg","-loglevel","error","-y","-ss",str(t),"-i","source/input.mp4","-frames:v","1",f"footage/f{i+2:02d}.png"],check=True)
PY
ffmpeg -loglevel error -y -i source/input.mp4 -vn -ac 1 -ar 48000 -c:a pcm_s24le narration/narration_raw.wav
echo "done: $(ls footage | wc -l) footage files"
