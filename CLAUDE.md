# Project memory

## Reference videos (standing instruction from the user)
Whenever the user provides a **reference video** (a video given as a style/editing example, as opposed to
raw footage to edit), always save it, without being asked again:

1. Copy it to `.claude/skills/video-references/references/` with a numbered, descriptive name:
   `NN-short-style-description.mp4` (next free number), plus a contact sheet `NN-....sheet.jpg`
   (`ffmpeg -vf "fps=2,scale=150:-1,tile=10x6"`).
2. Watch/analyse it and add a section for it in `.claude/skills/video-references/SKILL.md`
   (format, layout, typography, subtitles, motion, transitions, sound, weak points).
3. Add any new style preference the user states to the "standing preferences" list in that SKILL.md.
4. Copy the skill to `~/.claude/skills/video-references/` so it is active in the current session.
5. Commit and push. Keep each file under 100 MB (GitHub limit); re-encode if needed.

If it is unclear whether an uploaded video is a reference or raw footage, ask.

## Video editing work
The user starts edits with `/edit-video <brief>`. For any video edit, run the `edit-video` skill
(it loads `video-references` first, then the other video skills) even if the user doesn't type the command.
