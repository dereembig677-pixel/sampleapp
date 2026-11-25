# Inputs
- `reference_stickman.mp4` — style reference (= reference/استیکمن.mp4), 1920x1080, 65.9 s
- `narration_footage.mp4` — raw narration + 28 footage pieces (vertical 1070x1920, 112.9 s).
  Footage: 0–3.9 s animated clip, then a still every 3 s until 84.93 s; black after that (audio only).

Restore the working layout in a new session:
```
mkdir -p reference source && cp inputs/reference_stickman.mp4 reference/استیکمن.mp4 && cp inputs/narration_footage.mp4 source/input.mp4
```
Then re-extract footage/narration as described in output/footage_inventory.md.
