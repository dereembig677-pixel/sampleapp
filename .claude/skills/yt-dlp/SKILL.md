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
