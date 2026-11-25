#!/usr/bin/env python3
"""Render a timeline.json into a video in the reference ("stickman") style.

Frame-accurate, sub-pixel Ken Burns via cv2.warpAffine (no zoompan jitter),
transitions (dissolve, flash, dip, whip, fade), warm grade, glow and vignette.
Frames are piped as raw RGB into ffmpeg; audio is muxed from --audio.

usage: render.py timeline.json out.mp4 [--preview] [--audio mix.wav]
"""
import argparse, json, math, subprocess, sys
import cv2
import numpy as np

FPS = 30


def ease(p):  # smoothstep-like, for camera moves and transitions
    p = min(max(p, 0.0), 1.0)
    return p * p * (3 - 2 * p)


def ease_io_sine(p):
    p = min(max(p, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * p)


class Source:
    """A still image or a video clip, delivered as float32 RGB 0..1."""

    def __init__(self, path):
        self.path = path
        self.is_video = path.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))
        if self.is_video:
            cap = cv2.VideoCapture(path)
            frames = []
            while True:
                ok, f = cap.read()
                if not ok:
                    break
                frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
            self.frames = frames
        else:
            im = cv2.imread(path, cv2.IMREAD_COLOR)
            if im is None:
                sys.exit(f"cannot read {path}")
            self.frames = [cv2.cvtColor(im, cv2.COLOR_BGR2RGB)]
        self.h, self.w = self.frames[0].shape[:2]

    def get(self, t):
        if not self.is_video:
            return self.frames[0]
        i = min(int(t * FPS), len(self.frames) - 1)  # hold last frame
        return self.frames[i]


def camera(src_img, W, H, scale, cx, cy):
    """Cover-fit src into WxH, zoomed by `scale` (>=1) around normalized focus (cx,cy).
    The focus point is clamped so the frame never shows outside the image."""
    h, w = src_img.shape[:2]
    base = max(W / w, H / h)
    s = base * scale
    # visible window in source pixels
    vw, vh = W / s, H / s
    x0 = min(max(cx * w - vw / 2, 0), w - vw)
    y0 = min(max(cy * h - vh / 2, 0), h - vh)
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC
    out = cv2.warpAffine(src_img, M, (W, H), flags=interp, borderMode=cv2.BORDER_REFLECT)
    return out.astype(np.float32) / 255.0


def shot_frame(shot, src, t_local, W, H):
    """Render a shot at local time t (may be <0 or > duration during transitions)."""
    dur = shot["end"] - shot["start"]
    mv = shot.get("motion", {})
    p = ease_io_sine((t_local + 0.5) / (dur + 1.0))  # span slightly beyond the shot so moves never stop at a cut
    z0, z1 = mv.get("zoom", [1.0, 1.12])
    f0, f1 = mv.get("from", [0.5, 0.5]), mv.get("to", [0.5, 0.5])
    z = z0 + (z1 - z0) * p
    cx = f0[0] + (f1[0] - f0[0]) * p
    cy = f0[1] + (f1[1] - f0[1]) * p
    t_src = shot.get("src_in", 0.0) + max(t_local, 0.0)
    img = camera(src.get(t_src), W, H, z, cx, cy)
    # "rise from darkness" for night / secret shots
    rise = shot.get("rise_from_dark", 0)
    if rise and t_local < rise:
        img = img * (0.15 + 0.85 * ease(max(t_local, 0) / rise))
    return img


def hblur(img, k):
    k = int(k)
    if k < 3:
        return img
    small = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA)
    kk = max(3, k // 2) | 1
    kernel = np.ones((1, kk), np.float32) / kk
    b = cv2.filter2D(small, -1, kernel, borderType=cv2.BORDER_REFLECT)
    return cv2.resize(b, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)


def radial_white(W, H):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.75)) ** 2)
    g = np.clip(1.0 - 0.25 * d ** 2, 0.7, 1.0)
    return np.dstack([g, g, g])


def make_vignette(W, H, strength):
    """strength = darkening at the middle of the long edges (0.35 => 35 % darker)."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (x - W / 2) / (W / 2)
    ny = (y - H / 2) / (H / 2)
    d = np.sqrt(nx ** 2 * 1.0 + ny ** 2 * 0.55)  # elliptical, a bit gentler top/bottom on 9:16
    v = 1.0 - strength * np.clip((d - 0.35) / 0.65, 0, 1.4) ** 1.6
    v = np.clip(v, 0, 1)
    return np.dstack([v, v, v]).astype(np.float32)


def grade(img, vig, glow_amt=0.22, warm=1.0):
    # warm + contrast + saturation
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    img = np.dstack([r * (1 + 0.045 * warm), g * (1 + 0.01 * warm), b * (1 - 0.06 * warm)])
    lum = img.mean(axis=2, keepdims=True)
    img = lum + (img - lum) * 1.10
    img = np.clip(img, 0, 1)
    img = img + 0.12 * (img - 0.5) * (1 - np.abs(2 * img - 1))  # gentle S-curve, keeps blacks/whites
    # glow on highlights
    if glow_amt > 0:
        small = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA)
        hi = np.clip((small - 0.7) / 0.3, 0, 1) * small
        hi = cv2.GaussianBlur(hi, (0, 0), 12)
        hi = cv2.resize(hi, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
        img = 1 - (1 - img) * (1 - glow_amt * hi)  # screen
    img = img * vig
    return np.clip(img, 0, 1)


def build(timeline, W, H):
    shots = timeline["shots"]
    srcs = {}
    for s in shots:
        if s["file"] not in srcs:
            srcs[s["file"]] = Source(s["file"])
    total = timeline.get("duration", shots[-1]["end"])
    nframes = int(round(total * FPS))
    vig = make_vignette(W, H, timeline.get("vignette", 0.35))
    white = radial_white(W, H)
    fade_in = timeline.get("fade_in", 0.6)
    fade_out = timeline.get("fade_out", 1.2)

    def render_at(i, t):
        s = shots[i]
        return shot_frame(s, srcs[s["file"]], t - s["start"], W, H)

    for n in range(nframes):
        t = n / FPS
        # active shot: last one whose start <= t
        i = max(k for k, s in enumerate(shots) if s["start"] <= t + 1e-6) if t >= shots[0]["start"] else 0
        cur = shots[i]
        tr = cur.get("transition_in", {"type": "cut"})
        typ, d = tr.get("type", "cut"), tr.get("dur", 0.0)
        since = t - cur["start"]
        frame = None
        if i > 0 and typ != "cut" and d > 0 and since < d:
            p = since / d
            if typ == "dissolve":
                # centred on the cut: starts d/2 before it
                pass
            elif typ == "flash":
                b = render_at(i, t)
                if since < 1 / FPS:
                    frame = white
                else:
                    q = ease((since - 1 / FPS) / max(d - 1 / FPS, 1e-3))
                    frame = white * (1 - q) + b * q
            elif typ == "dip":
                b = render_at(i, t)
                if since < 1 / FPS:
                    frame = b * 0
                else:
                    frame = b * ease((since - 1 / FPS) / max(d - 1 / FPS, 1e-3))
            elif typ == "whip":
                pass  # handled below (centred)
        # centred transitions (dissolve / whip): window [start - d/2, start + d/2]
        nxt = shots[i + 1] if i + 1 < len(shots) else None
        for (a_idx, b_idx, sh) in ((i - 1, i, cur), (i, i + 1, nxt)):
            if sh is None or a_idx < 0 or b_idx >= len(shots):
                continue
            tr2 = sh.get("transition_in", {})
            if tr2.get("type") not in ("dissolve", "whip"):
                continue
            d2 = tr2.get("dur", 0.3)
            t0 = sh["start"] - d2 / 2
            if t0 <= t < t0 + d2:
                p = (t - t0) / d2
                A = render_at(a_idx, t)
                B = render_at(b_idx, t)
                if tr2["type"] == "dissolve":
                    q = ease(p)
                    frame = A * (1 - q) + B * q
                else:  # whip pan: content slides, heavy horizontal motion blur, direction alternates
                    direction = tr2.get("dir", 1)
                    q = ease_io_sine(p)
                    off = int(q * W)
                    strip = np.concatenate([A, B], axis=1) if direction > 0 else np.concatenate([B, A], axis=1)
                    x = off if direction > 0 else W - off
                    view = strip[:, x:x + W]
                    speed = math.sin(math.pi * p)
                    frame = hblur(view, 3 + speed * W * 0.35)
                break
        if frame is None:
            frame = render_at(i, t)
        frame = grade(frame, vig, timeline.get("glow", 0.22))
        # global fades
        if t < fade_in:
            frame = frame * ease(t / fade_in)
        if t > total - fade_out:
            frame = frame * ease((total - t) / fade_out)
        yield (frame * 255 + 0.5).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("out")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--audio")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--dur", type=float)
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    W, H = tl.get("size", [1080, 1920])
    if a.preview:
        W, H = W * 2 // 3 // 2 * 2, H * 2 // 3 // 2 * 2  # 720x1280
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if a.audio:
        cmd += ["-i", a.audio]
    if a.preview:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                "-profile:v", "high", "-movflags", "+faststart"]
    if a.audio:
        cmd += ["-c:a", "aac", "-b:a", "320k" if not a.preview else "160k", "-ar", "48000", "-shortest"]
    cmd += [a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n0 = int(a.start * FPS)
    n1 = n0 + int(a.dur * FPS) if a.dur else None
    for k, fr in enumerate(build(tl, W, H)):
        if k < n0:
            continue
        if n1 is not None and k >= n1:
            break
        p.stdin.write(fr.tobytes())
        if k % 150 == 0:
            print(f"frame {k}", file=sys.stderr, flush=True)
    p.stdin.close()
    sys.exit(p.wait())


if __name__ == "__main__":
    main()
