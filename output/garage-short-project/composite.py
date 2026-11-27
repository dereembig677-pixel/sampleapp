# usage: composite.py <src video> <broll dir> <gfx dir> <out dir> <nframes> [start end]
import sys, os, cv2, numpy as np
SRC, BR, G, O, N = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
F0, F1 = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, N)
os.makedirs(O, exist_ok=True)
FPS, W, H = 25, 1080, 1920
clamp = lambda x, a=0, b=1: max(a, min(b, x)); lin = lambda t, a, b: clamp((t - a) / (b - a))
eOut = lambda p: 1 - (1 - p) ** 3; eIn = lambda p: p ** 3
eIO = lambda p: 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2

class Clip:
    def __init__(s, path): s.cap = cv2.VideoCapture(path); s.fps = s.cap.get(5); s.n = int(s.cap.get(7)); s.cache = {}; s.pos = -1; s.last = None
    def at(s, t):
        i = int(clamp(round(t * s.fps), 0, s.n - 1))
        if i == s.pos: return s.last
        if i < s.pos or i > s.pos + 30: s.cap.set(1, i); s.pos = i - 1
        while s.pos < i:
            ok, f = s.cap.read(); s.pos += 1
            if ok: s.last = f
        return s.last
src = Clip(SRC); box = Clip(BR + '/40970.mp4'); car = Clip(BR + '/35577.mp4'); fire = Clip(BR + '/52312.mp4')

def upscale(f):
    u = cv2.resize(f, (1081, 1920), interpolation=cv2.INTER_LANCZOS4)[:, :1080]
    b = cv2.GaussianBlur(u, (0, 0), 1.4); return cv2.addWeighted(u, 1.45, b, -0.45, 0)
def cover(f, w=W, h=H):
    fh, fw = f.shape[:2]; s = max(w / fw, h / fh); r = cv2.resize(f, (int(fw * s + .5), int(fh * s + .5)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2; return r[y:y + h, x:x + w]

# zoom events: (t0, t1, amount, cx, cy, attack, release)
Z = [(0.0, 1.2, 0.0, 540, 960, 0, 0),
     (2.78, 3.90, 0.12, 560, 860, 0.12, 0.35), (7.0, 9.45, 0.10, 560, 900, 2.2, 0.2), (11.40, 12.10, 0.08, 540, 900, 0.1, 0.3), (14.90, 15.70, 0.10, 540, 900, 0.08, 0.3),
     (21.30, 23.60, 0.12, 420, 1050, 0.05, 1.6), (26.90, 29.20, 0.08, 540, 960, 1.2, 0.2),
     (32.5, 35.10, 0.06, 560, 760, 2.4, 0.1), (35.15, 36.50, 0.20, 560, 760, 0.12, 0.35),
     (37.0, 41.0, 0.06, 540, 1000, 3.0, 0.1), (41.04, 41.90, 0.12, 540, 1000, 0.06, 0.35),
     (43.0, 48.3, 0.14, 540, 1000, 4.2, 0.5), (53.60, 57.20, 0.10, 540, 900, 0.1, 0.5), (55.08, 57.20, 0.06, 540, 900, 0.1, 0.5), (55.74, 57.20, 0.06, 540, 900, 0.1, 0.5),
     (60.05, 61.20, 0.07, 540, 960, 0.12, 0.3), (61.30, 64.0, 0.14, 600, 960, 1.6, 0.6), (65.05, 67.0, 0.06, 540, 900, 0.15, 0.5),
     (67.2, 71.6, 0.09, 540, 1000, 4.0, 0.3), (72.6, 80.4, 0.05, 540, 800, 2.0, 0.3)]
SHAKE = [(3.42, 0.35, 14), (14.96, 0.3, 10), (41.06, 0.4, 14), (53.62, 0.3, 8), (55.08, 0.3, 10), (55.74, 0.45, 16), (61.6, 2.0, 4)]
def zoom(t):
    z, cx, cy, wsum = 1.0, 0.0, 0.0, 0.0
    if t < 1.2: z += 0.14 * (1 - eOut(lin(t, 0, 1.2)))  # opening push-out
    for t0, t1, a, x, y, at, rl in Z:
        if t0 <= t <= t1 and a > 0:
            e = min(eOut(lin(t, t0, t0 + at)) if at > 0 else 1, 1 - eIO(lin(t, t1 - rl, t1)) if rl > 0 else 1)
            z += a * e; cx += x * e; cy += y * e; wsum += e
    c = (cx / wsum, cy / wsum) if wsum > 1e-3 else (540, 960)
    if wsum > 1e-3 and wsum < 1: c = (540 + (c[0] - 540) * wsum, 960 + (c[1] - 960) * wsum)
    return z, c
def shake(t):
    dx = dy = 0
    for t0, d, amp in SHAKE:
        if t0 <= t <= t0 + d:
            k = (1 - (t - t0) / d) ** 2 * amp; dx += k * np.sin(t * 97); dy += k * np.cos(t * 83)
    return dx, dy
def transform(img, z, c, sh=(0, 0)):
    M = np.float32([[z, 0, c[0] - c[0] * z + sh[0]], [0, z, c[1] - c[1] * z + sh[1]]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def hblur(img, k):
    k = int(k) | 1
    if k < 3: return img
    ker = np.zeros((k, k), np.float32); ker[k // 2, :] = 1 / k; return cv2.filter2D(img, -1, ker)
def zoomblur(img, amt, c=(540, 960), n=6):
    acc = np.zeros(img.shape, np.float32)
    for i in range(n): acc += transform(img, 1 + amt * i / (n - 1), c).astype(np.float32)
    return (acc / n).astype(np.uint8)
def rounded_mask(w, h, r):
    m = np.zeros((h, w), np.uint8); cv2.rectangle(m, (r, 0), (w - r, h), 255, -1); cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for x, y in [(r, r), (w - r, r), (r, h - r), (w - r, h - r)]: cv2.circle(m, (x, y), r, 255, -1)
    return cv2.GaussianBlur(m, (0, 0), 1.2).astype(np.float32)[..., None] / 255
CW, CH = 1000, 562; CMASK = rounded_mask(CW, CH, 46)

def car_frame(t):
    f = car.at(2.0 + (t - 29.30) * 1.0)
    bg = cv2.GaussianBlur(cover(f), (0, 0), 28); bg = (bg * 0.45).astype(np.uint8)
    p = lin(t, 29.30, 29.58); s = (0.55 + 0.45 * (1 + 2.2 * (p - 1) ** 3 + 1.2 * (p - 1) ** 2)) if p < 1 else 1
    card = cv2.resize(f, (CW, CH), interpolation=cv2.INTER_AREA)
    out = bg.astype(np.float32)
    cw, ch = int(CW * s), int(CH * s)
    if cw > 10:
        cs = cv2.resize(card, (cw, ch)); m = cv2.resize(CMASK, (cw, ch))[..., None]
        x0, y0 = W // 2 - cw // 2, 1000 - ch // 2
        # neon border glow
        glow = np.zeros((H, W), np.float32); cv2.rectangle(glow, (x0 - 6, y0 - 6), (x0 + cw + 6, y0 + ch + 6), 1.0, 8)
        glow = cv2.GaussianBlur(glow, (0, 0), 14) * 2.2 + cv2.GaussianBlur(glow, (0, 0), 2)
        out += glow[..., None] * np.array([255, 230, 47], np.float32) * 0.8
        reg = out[y0:y0 + ch, x0:x0 + cw]; out[y0:y0 + ch, x0:x0 + cw] = reg * (1 - m) + cs.astype(np.float32) * m
    return np.clip(out, 0, 255).astype(np.uint8)

def heat(img, t, amt):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = np.sin(yy / 23 + t * 14) * 5 * amt; dy = np.cos(xx / 31 + t * 11) * 3 * amt
    return cv2.remap(img, xx + dx, yy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
FIREMASK = np.clip((np.arange(H, dtype=np.float32) - 700) / 700, 0, 1)[:, None, None] ** 1.3

last_src = None
for n in range(F0, min(F1, N)):
    t = n / FPS
    st = min(t, (src.n - 1) / FPS)
    f = upscale(src.at(st))
    z, c = zoom(t); sh = shake(t)
    # end: push in and fade
    if t > 80.56: z *= 1 + 0.22 * eIO(lin(t, 80.56, 81.32))
    frame = transform(f, z, c, sh)
    # --- boxing B-roll 18.26 -> 21.30 ---
    if 18.14 <= t < 18.26: frame = hblur(transform(frame, 1, (540, 960), (-140 * lin(t, 18.14, 18.26), 0)), 70 * lin(t, 18.14, 18.26))
    if 18.26 <= t < 21.30:
        bf = box.at(0.15 + (t - 18.26) * 1.0); bf = cover(bf)
        bz = 1.06 + 0.06 * lin(t, 18.26, 21.30); frame = transform(bf, bz, (540, 900), shake(t))
        if t < 18.40: frame = hblur(transform(frame, 1, (540, 960), (160 * (1 - lin(t, 18.26, 18.40)), 0)), 70 * (1 - lin(t, 18.26, 18.40)))
        # punchy contrast
        frame = cv2.convertScaleAbs(frame, alpha=1.08, beta=-6)
    if 21.30 <= t < 21.46:  # flash + rgb split back to real socket
        k = 1 - lin(t, 21.30, 21.46); b, g, r = cv2.split(frame)
        sft = int(18 * k); r = np.roll(r, sft, 1); b = np.roll(b, -sft, 1); frame = cv2.merge([b, g, r])
        frame = cv2.addWeighted(frame, 1 - 0.7 * k, np.full_like(frame, 255), 0.7 * k, 0)
    # --- car B-roll 29.30 -> 31.40 ---
    if 29.16 <= t < 29.30: frame = zoomblur(frame, 0.35 * lin(t, 29.16, 29.30))
    if 29.30 <= t < 31.40:
        frame = car_frame(t)
        if t > 31.26: frame = zoomblur(frame, 0.4 * lin(t, 31.26, 31.40))
    if 31.40 <= t < 31.52: frame = hblur(frame, 60 * (1 - lin(t, 31.40, 31.52)))
    # --- burning hand 61.30 -> 63.90 ---
    fa = min(eOut(lin(t, 61.25, 61.55)), 1 - eIn(lin(t, 63.4, 63.95))) if 61.25 <= t <= 63.95 else 0
    if fa > 0:
        frame = heat(frame, t, fa)
        fl = cover(fire.at(1.0 + (t - 61.25) * 1.2), W, 1100); flames = np.zeros((H, W, 3), np.float32); flames[H - 1100:] = fl
        flames *= FIREMASK * fa * 1.15
        fr = frame.astype(np.float32); fr = 255 - (255 - fr) * (255 - flames) / 255  # screen
        tint = np.array([0.80, 0.93, 1.12], np.float32); fr = fr * (1 + (tint - 1) * fa)
        vg = np.ones((H, W), np.float32); cv2.circle(vg, (W // 2, H // 2), 700, 0, -1); vg = cv2.GaussianBlur(vg, (0, 0), 160)[..., None]
        pulse = 0.6 + 0.4 * np.sin(t * 9)
        fr += vg * np.array([0, 60, 255], np.float32) * 0.55 * fa * pulse
        frame = np.clip(fr, 0, 255).astype(np.uint8)
    # --- end fade ---
    if t > 80.62: frame = cv2.GaussianBlur(frame, (0, 0), 1 + 10 * lin(t, 80.62, 81.32))
    # gfx overlay
    gp = f'{G}/{n:05d}.png'
    if os.path.exists(gp):
        gi = cv2.imread(gp, cv2.IMREAD_UNCHANGED); a = gi[..., 3:4].astype(np.float32) / 255
        frame = (frame.astype(np.float32) * (1 - a) + gi[..., :3].astype(np.float32) * a)
    frame = np.asarray(frame, np.float32)
    if t > 80.80: frame *= 1 - eIn(lin(t, 80.80, 81.32)) ** 0.7
    cv2.imwrite(f'{O}/{n:05d}.jpg', np.clip(frame, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
print('ok', F0, F1)
