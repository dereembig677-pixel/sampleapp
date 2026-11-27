# v2 compositor. usage: composite.py <src video> <broll dir> <gfx dir> <out dir> <nframes> [start end]
import sys, os, cv2, numpy as np
SRC, BR, G, O, N = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
F0, F1 = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (0, N)
os.makedirs(O, exist_ok=True)
FPS, W, H = 25, 1080, 1920
clamp = lambda x, a=0, b=1: max(a, min(b, x)); lin = lambda t, a, b: clamp((t - a) / (b - a))
expoOut = lambda p: 1 if p >= 1 else 1 - 2 ** (-10 * p); expoIn = lambda p: 0 if p <= 0 else 2 ** (10 * p - 10)
eIO = lambda p: 4 * p ** 3 if p < .5 else 1 - (-2 * p + 2) ** 3 / 2
sIO = lambda p: p * p * (3 - 2 * p)

class Clip:
    def __init__(s, path): s.cap = cv2.VideoCapture(path); s.fps = s.cap.get(5); s.n = int(s.cap.get(7)); s.pos = -1; s.last = None
    def at(s, t):
        i = int(clamp(round(t * s.fps), 0, s.n - 1))
        if i == s.pos: return s.last
        if i < s.pos or i > s.pos + 30: s.cap.set(1, i); s.pos = i - 1
        while s.pos < i:
            ok, f = s.cap.read(); s.pos += 1
            if ok: s.last = f
        return s.last
src = Clip(SRC); drawer = Clip(BR + '/47082.mp4'); suv = Clip(BR + '/47835.mp4'); fire = Clip(BR + '/52312.mp4')

def upscale(f):
    u = cv2.resize(f, (1081, 1920), interpolation=cv2.INTER_LANCZOS4)[:, :1080]
    b = cv2.GaussianBlur(u, (0, 0), 1.3); return cv2.addWeighted(u, 1.35, b, -0.35, 0)
def cover(f, w=W, h=H, cx=0.5):
    fh, fw = f.shape[:2]; s = max(w / fw, h / fh); r = cv2.resize(f, (int(fw * s + .5), int(fh * s + .5)), interpolation=cv2.INTER_LANCZOS4)
    x = int(clamp((r.shape[1] * cx) - w / 2, 0, r.shape[1] - w)); y = (r.shape[0] - h) // 2; return r[y:y + h, x:x + w]
def transform(img, z, c):
    M = np.float32([[z, 0, c[0] - c[0] * z], [0, z, c[1] - c[1] * z]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def zoomblur(img, amt, c=(540, 960), n=7):
    if amt < 0.004: return img
    acc = np.zeros(img.shape, np.float32)
    for i in range(n): acc += transform(img, 1 + amt * i / (n - 1), c).astype(np.float32)
    return (acc / n).astype(np.uint8)
def vblur(img, k):
    k = int(k) | 1
    if k < 3: return img
    ker = np.zeros((k, k), np.float32); ker[:, k // 2] = 1 / k; return cv2.filter2D(img, -1, ker)

# smooth zoom events: (t0, t1, amount, cx, cy, attack, release) — eased in/out, no shake
Z = [(3.10, 4.00, 0.07, 560, 860, 0.35, 0.45), (7.0, 9.45, 0.08, 560, 900, 2.0, 0.4), (11.24, 12.20, 0.05, 540, 900, 0.3, 0.4),
     (14.43, 15.80, 0.05, 540, 900, 0.35, 0.5), (20.20, 23.90, 0.10, 420, 1050, 0.6, 1.2), (26.80, 29.20, 0.07, 540, 960, 1.4, 0.3),
     (32.2, 35.6, 0.05, 560, 760, 2.4, 0.3), (35.73, 36.70, 0.10, 560, 760, 0.30, 0.45), (37.2, 41.0, 0.05, 540, 1000, 3.0, 0.3),
     (41.14, 42.00, 0.07, 540, 1000, 0.25, 0.5), (43.0, 48.7, 0.11, 540, 1000, 4.5, 0.6), (53.78, 57.40, 0.06, 540, 900, 0.4, 0.6),
     (55.30, 57.40, 0.03, 540, 900, 0.35, 0.6), (56.13, 57.40, 0.03, 540, 900, 0.35, 0.6), (60.57, 61.40, 0.05, 540, 960, 0.3, 0.4),
     (61.35, 64.10, 0.09, 600, 960, 1.5, 0.6), (65.85, 67.0, 0.04, 540, 900, 0.35, 0.5), (67.2, 71.6, 0.06, 540, 1000, 4.0, 0.3),
     (72.4, 80.5, 0.04, 540, 800, 3.0, 0.4)]
def zoom(t):
    z, cx, cy, ws = 1.0, 0.0, 0.0, 0.0
    if t < 1.6: z += 0.10 * (1 - sIO(lin(t, 0, 1.6)))
    for t0, t1, a, x, y, at, rl in Z:
        if t0 <= t <= t1:
            e = min(sIO(lin(t, t0, t0 + at)), 1 - sIO(lin(t, t1 - rl, t1)))
            z += a * e; cx += x * e; cy += y * e; ws += e
    if ws > 1e-3:
        c = (cx / ws, cy / ws); k = min(1, ws); c = (540 + (c[0] - 540) * k, 960 + (c[1] - 960) * k)
    else: c = (540, 960)
    return z, c

# B-roll card (top, reference-inspired): rounded, thin white border, soft shadow
CX0, CW, CH, CY0 = 90, 900, 506, 300
def rounded_mask(w, h, r):
    m = np.zeros((h, w), np.uint8); cv2.rectangle(m, (r, 0), (w - r, h), 255, -1); cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for x, y in [(r, r), (w - r, r), (r, h - r), (w - r, h - r)]: cv2.circle(m, (x, y), r, 255, -1)
    return cv2.GaussianBlur(m, (0, 0), 1.0).astype(np.float32)[..., None] / 255
CMASK = rounded_mask(CW, CH, 40)
BORDER = np.clip(CMASK - cv2.erode(CMASK, np.ones((5, 5), np.uint8))[..., None], 0, 1)
SHADOW = cv2.GaussianBlur(np.pad(CMASK[..., 0], 60), (0, 0), 26)[..., None]
def card_offset(t, a=18.00, b=21.92):
    # returns y offset (0 = in place) and velocity for motion blur, or None
    if t < a or t > b: return None
    pi = expoOut(lin(t, a, a + 0.42)); po = expoIn(lin(t, b - 0.34, b))
    off = -(CY0 + CH + 40) * (1 - pi) - (CY0 + CH + 40) * po
    vel = abs((CY0 + CH + 40) * ((1 - expoOut(lin(t - 0.04, a, a + 0.42))) - (1 - pi))) + abs((CY0 + CH + 40) * (po - expoIn(lin(t - 0.04, b - 0.34, b))))
    return off, vel
def paste(dst, src, x, y):
    # paste src (h,w,c) into dst at (x,y) with clipping; returns region slices
    h, w = src.shape[:2]; X0, Y0 = max(0, x), max(0, y); X1, Y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if X1 <= X0 or Y1 <= Y0: return
    dst[Y0:Y1, X0:X1] = np.maximum(dst[Y0:Y1, X0:X1], src[Y0 - y:Y1 - y, X0 - x:X1 - x]) if src.shape[2] == 1 else src[Y0 - y:Y1 - y, X0 - x:X1 - x]
def put_card(frame, img, t):
    st = card_offset(t)
    if st is None: return frame
    off, vel = st; y0 = int(round(CY0 + off)); out = frame.astype(np.float32)
    k = expoOut(lin(t, 18.0, 18.4)) * (1 - expoIn(lin(t, 21.58, 21.92))); out *= 1 - 0.18 * k
    card = cv2.resize(img, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32)
    card = card * (1 - BORDER) + 255 * BORDER * 0.85
    layer = np.zeros((H, W, 3), np.float32); alpha = np.zeros((H, W, 1), np.float32); shadow = np.zeros((H, W, 1), np.float32)
    paste(shadow, SHADOW * 0.55, CX0 - 60, y0 - 60 + 18)
    paste(layer, card, CX0, y0); paste(alpha, CMASK, CX0, y0)
    if vel > 6:
        k2 = min(61, vel * 0.9); layer = vblur(layer, k2); alpha = vblur(alpha, k2)
        if alpha.ndim == 2: alpha = alpha[..., None]
    out = out * (1 - shadow * (1 - alpha))
    out = out * (1 - alpha) + layer
    return np.clip(out, 0, 255).astype(np.uint8)

def heat(img, t, amt):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return cv2.remap(img, xx + np.sin(yy / 26 + t * 12) * 3.5 * amt, yy + np.cos(xx / 34 + t * 9) * 2.0 * amt, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
FIREMASK = np.clip((np.arange(H, dtype=np.float32) - 760) / 760, 0, 1)[:, None, None] ** 1.4
VIG = None

for n in range(F0, min(F1, N)):
    t = n / FPS
    f = upscale(src.at(min(t, (src.n - 1) / FPS)))
    z, c = zoom(t)
    if t > 80.56: z *= 1 + 0.06 * sIO(lin(t, 80.56, 81.32))
    frame = transform(f, z, c)
    # --- box B-roll: tool drawer card 18.00 -> 21.92 ---
    if 18.0 <= t <= 21.92:
        frame = put_card(frame, drawer.at(1.2 + (t - 18.0) * 0.9), t)
    # --- SUV wheel B-roll, full screen 29.40 -> 31.32, zoom-through transitions ---
    if 29.22 <= t < 29.40: frame = zoomblur(transform(frame, 1 + 0.35 * expoIn(lin(t, 29.22, 29.40)), (540, 960)), 0.30 * lin(t, 29.22, 29.40))
    if 29.40 <= t < 31.32:
        sf = cover(suv.at(1.0 + (t - 29.40)), cx=0.30)
        p = expoOut(lin(t, 29.40, 29.70)); q = expoIn(lin(t, 31.12, 31.32))
        sz = 1.28 - 0.28 * p + 0.06 * lin(t, 29.4, 31.3) + 0.30 * q
        frame = zoomblur(transform(sf, sz, (540, 960)), 0.28 * (1 - p) + 0.30 * q)
        frame = cv2.convertScaleAbs(frame, alpha=1.04, beta=-4)
    if 31.32 <= t < 31.56: frame = zoomblur(transform(frame, 1.25 - 0.25 * expoOut(lin(t, 31.32, 31.56)), (540, 960)), 0.25 * (1 - expoOut(lin(t, 31.32, 31.56))))
    # --- burning hand 61.30 -> 64.0 ---
    fa = min(sIO(lin(t, 61.20, 61.60)), 1 - sIO(lin(t, 63.55, 64.05))) if 61.2 <= t <= 64.05 else 0
    if fa > 0:
        frame = heat(frame, t, fa)
        fl = cover(fire.at(1.0 + (t - 61.2) * 1.1), W, 1100); flames = np.zeros((H, W, 3), np.float32); flames[H - 1100:] = fl
        flames *= FIREMASK * fa
        fr = frame.astype(np.float32); fr = 255 - (255 - fr) * (255 - flames) / 255
        if VIG is None:
            VIG = np.ones((H, W), np.float32); cv2.circle(VIG, (W // 2, H // 2), 720, 0, -1); VIG = cv2.GaussianBlur(VIG, (0, 0), 170)[..., None]
        fr = fr * (1 + (np.array([0.86, 0.95, 1.08], np.float32) - 1) * fa) + VIG * np.array([0, 45, 210], np.float32) * 0.45 * fa * (0.8 + 0.2 * np.sin(t * 6))
        frame = np.clip(fr, 0, 255).astype(np.uint8)
    # graphics overlay
    gp = f'{G}/{n:05d}.png'
    fr = frame.astype(np.float32)
    if os.path.exists(gp):
        gi = cv2.imread(gp, cv2.IMREAD_UNCHANGED); a = gi[..., 3:4].astype(np.float32) / 255
        fr = fr * (1 - a) + gi[..., :3].astype(np.float32) * a
    if t > 80.72: fr *= 1 - sIO(lin(t, 80.72, 81.32))
    cv2.imwrite(f'{O}/{n:05d}.jpg', np.clip(fr, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
print('ok', F0, F1)
