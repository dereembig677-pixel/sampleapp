---
name: video-references
description: The user's saved reference videos for short-form editing style (vertical reels/Shorts), with breakdowns of each one and the user's standing style preferences. Use whenever editing a talking-head reel, YouTube Short, Instagram reel or Persian/Farsi short video for this user, or when they say "like the reference", "use my reference style", or ask for subtitles, motion graphics or B-roll in their style.
---

# Video style references

Reference videos live in `references/` (each with a `.sheet.jpg` contact sheet, 2 frames/s).
Watch the relevant one (contact sheet + a few full-res frames) before designing an edit.
**Take inspiration, don't copy** — the user explicitly asked for this.

## The user's standing preferences (learned from feedback)
- **Text colours: white and yellow only** (yellow `#FFD60A`). No neon, no red/green/cyan text.
- **Respect the YouTube Shorts safe zone** (1080×1920): keep all text inside x 60–900, y 250–1420
  (clear of the header, right-hand action buttons, and the title/description area at the bottom).
- **Motion must look professional, not template-like**: blur-to-sharp reveals, expo ease-out,
  directional motion blur on moving elements. No springy/bouncy overshoot, no camera shake,
  no gimmick widgets (crack lines, X stamps, padlocks, power meters, thermometers, badges).
- **Subtitles must be exactly in sync.** For Persian, Whisper word timestamps are not accurate enough:
  transcribe with Whisper large-v3 (with a domain vocabulary `initial_prompt`), correct the text by
  context, then CTC force-align with `jonatasgrosman/wav2vec2-large-xlsr-53-persian`. Split subtitle
  lines by meaning (2–4 words), hide them during pauses.
- Listen to what the user literally asks for: "بکس/box" in a mechanic context = socket wrench, not boxing.
  Ask or check context before picking a pun-based interpretation. Car names/labels: use what the user says.
- Persian text: correct RTL, ZWNJ (half-space), Persian digits. User-provided fonts: Peyda (ExtraBold) for
  main text, Morabba (UltraLight) for light secondary text — fonts are licensed, never commit them.
- Never use Gemini / Nano Banana for any asset.

## 01-red-kinetic-talking-head.mp4 (9.7 s, 720×1280, English)
Talking head on a light grey seamless studio, one locked-off take; all variety comes from digital
zooms and motion graphics, a new graphic beat roughly every 1.5 s.
- Type hierarchy: small italic kicker line → huge extra-bold italic keyword (red gradient) → small tail word.
- Keyword text sits **behind the speaker's head** (matte), other words in front of the body.
- Motifs repeated as a system: red pixel squares, halftone dot rings, red pill labels, rounded photo
  cards with a red stroke; transitions: glowing light streak, zoom-blur exit, white flash, 1–2 frame
  inverted glitch flash.
- Keyword appears 2–6 frames *before* it is spoken. Music bed with heavy sub-bass, ~-14 LUFS.
- Weak points to avoid: broken first frame, typos, no CTA, abrupt ending.

## 02-persian-pill-subtitles-split-card.mp4 (90 s, 720×1280, Persian)
Persian talking head on a dark red-curtain set — **the user's preferred motion/subtitle feel**.
- Subtitles: short phrase (2–4 words) in a **dark rounded pill**, small white text, placed on the chest
  area mid-frame; blur-in reveal, quick and calm.
- Layout changes: B-roll shown in a **rounded card at the top** with thin light border and a small pill
  label (view count) at its bottom-left; the speaker stays visible below. Cards slide with motion blur.
- Title moments: heavy Persian bold text revealed word by word with blur, layered over photo-cutout
  collages; collage photos fly in with blur/glow and settle with a slow float.
- Overall: clean, restrained, every effect serves the story.
