"""Effect helpers for Titan scenes. All draw on the context's `under` / `over` pitch layers (c.ud / c.od) or the screen layer (c.sd) and take a progress `age` in frames."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from engine import blob, P, lerp, clamp, smooth, unit, PW, PH, VW, VH


def bolt(c, A, B, seed, col=(80, 200, 255), a=255, jag=6, layer='over', w=4):
    d = c.od if layer == 'over' else c.ud; rng = random.Random(seed)
    pts = [tuple(A)]
    for t in np.linspace(0, 1, 8)[1:-1]:
        q = A * (1 - t) + B * t; pts.append((q[0] + rng.uniform(-jag, jag), q[1] + rng.uniform(-jag, jag)))
    pts.append(tuple(B))
    d.line(pts, fill=col + (int(a * 0.6),), width=w); d.line(pts, fill=(200, 245, 255, a), width=max(1, w // 2)); d.line(pts, fill=(255, 255, 255, a), width=1)


def ring(c, p, r, col, a=230, layer='under', k=0.45, width=1):
    d = c.ud if layer == 'under' else c.od
    for w in range(width): d.ellipse([p[0] - r - w, p[1] - r * k - w * k, p[0] + r + w, p[1] + r * k + w * k], outline=col + (int(a),))


def shock(c, p, age, col=(255, 235, 140), life=10, maxr=40, n=2, layer='over'):
    if not 0 <= age < life: return
    for j in range(n):
        r = (4 + maxr * smooth((age - j * 1.5) / life)); a = 230 * (1 - age / life)
        if r > 4: ring(c, p, r, col, a, layer)


def burst(c, p, age, seed, n=14, speed=3.0, col=(255, 220, 120), life=14, g=0.2, layer='over', size=1, up=1.0):
    if not 0 <= age < life: return
    d = c.od if layer == 'over' else c.ud; rng = random.Random(seed)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); sp = rng.uniform(0.4, 1.0) * speed; vz = rng.uniform(0.5, 1.5) * up * speed * 0.7
        x = p[0] + math.cos(a) * sp * age; z = vz * age - g * age * age * 0.5; y = p[1] + math.sin(a) * sp * age * 0.5 - max(z, 0)
        al = int(255 * (1 - age / life)); xi, yi = int(x), int(y); d.rectangle([xi, yi, xi + size - 1, yi + size - 1], fill=col + (al,))


def glow(c, p, r, col, a=0.7, layer='under'):
    lay = c.under if layer == 'under' else c.over
    x0, y0 = int(p[0] - r - 2), int(p[1] - r - 2); s = int(2 * r + 4)
    b = blob(s, s, s / 2, s / 2, r, r, col, a); lay.alpha_composite(b, (x0, y0)) if (x0 >= 0 and y0 >= 0 and x0 + s <= PW and y0 + s <= PH) else _clipped(lay, b, x0, y0)


def _clipped(lay, im, x0, y0):
    big = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); big.alpha_composite(im, (max(x0, 0), max(y0, 0)), (max(-x0, 0), max(-y0, 0), im.width, im.height)) if False else None
    sub = im.crop((max(0, -x0), max(0, -y0), min(im.width, PW - x0), min(im.height, PH - y0)))
    if sub.width > 0 and sub.height > 0: lay.alpha_composite(sub, (max(x0, 0), max(y0, 0)))


def trail(c, pts, col, a=220, width=2, fade=True, layer='under'):
    d = c.ud if layer == 'under' else c.od; n = len(pts)
    for j in range(n - 1):
        al = int(a * ((j + 1) / n if fade else 1)); d.line([tuple(pts[j]), tuple(pts[j + 1])], fill=col + (al,), width=width)


def flame(c, p, age, seed, n=10, col=(255, 130, 40), core=(255, 235, 150), layer='over', spread=3, rise=1.0, dirv=(0, -1), size=2):
    d = c.od if layer == 'over' else c.ud; rng = random.Random(seed + age)
    for _ in range(n):
        t = rng.random(); x = p[0] + dirv[0] * t * 9 * rise + rng.uniform(-spread, spread) * (0.4 + t); y = p[1] + dirv[1] * t * 9 * rise + rng.uniform(-spread, spread) * (0.4 + t)
        cc = core if t < 0.3 else col; xi, yi = int(x), int(y); d.rectangle([xi, yi, xi + size - 1, yi + size - 1], fill=cc + (int(255 * (1 - t * 0.8)),))


def stars(c, p, i, col=(255, 235, 120), n=3, r=7, z=22):
    d = c.od
    for k in range(n):
        a = i * 0.35 + k * 2 * math.pi / n; x = p[0] + math.cos(a) * r; y = p[1] - z + math.sin(a) * r * 0.4
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=col + (255,)); d.point((int(x), int(y) - 2), fill=(255, 255, 255, 255))


def cracks(c, p, age, seed, n=9, length=30, col=(40, 28, 20), life=40):
    if age < 0: return
    rng = random.Random(seed); d = c.ud; grow = clamp(age / 6)
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi); pts = [tuple(p)]; x, y = p
        L = length * grow * rng.uniform(0.5, 1.0); steps = 6
        for s in range(steps):
            a += rng.uniform(-0.5, 0.5); x += math.cos(a) * L / steps; y += math.sin(a) * L / steps * 0.5; pts.append((x, y))
        d.line(pts, fill=col + (230,), width=1)


def reticle(c, p, size, rot, col=(255, 70, 70), a=255, layer='over'):
    d = c.od if layer == 'over' else c.ud
    for k in range(4):
        ang = rot + k * math.pi / 2; ux, uy = math.cos(ang), math.sin(ang) * 0.5
        d.line([(p[0] + ux * size, p[1] + uy * size), (p[0] + ux * (size * 0.55), p[1] + uy * (size * 0.55))], fill=col + (a,), width=1)
    ring(c, p, size * 0.8, col, a, layer)


def heart(c, x, y, S, col=(255, 70, 110)):
    rows = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
    for r_, row in enumerate(rows):
        for q, ch in enumerate(row):
            if ch == '1': c.sd.rectangle([x + (q - 3.5) * S, y + (r_ - 3) * S, x + (q - 2.5) * S - 1, y + (r_ - 2) * S - 1], fill=col + (255,))


def mini_card(d, x, y, w=14, h=20, col=(255, 214, 80), a=255, fill=(28, 24, 52)):
    d.rectangle([x, y, x + w, y + h], fill=fill + (a,), outline=col + (a,)); d.rectangle([x + 2, y + 3, x + w - 2, y + h * 0.55], fill=(60, 50, 110, a)); d.rectangle([x + 2, y + h * 0.7, x + w * 0.6, y + h * 0.78], fill=col + (a,))


# ---- post effects on the cropped 480x270 world (float RGBA arrays)
def gray(amt):
    def f(a): g = a[..., :3].mean(axis=2, keepdims=True); a[..., :3] = a[..., :3] * (1 - amt) + g * amt; return a
    return f


def invert(amt):
    def f(a): a[..., :3] = a[..., :3] * (1 - amt) + (255 - a[..., :3]) * amt; return a
    return f


def wash(rgb, amt):
    def f(a): a[..., :3] = a[..., :3] * (1 - amt) + np.array(rgb, np.float32) * amt; return a
    return f


def chroma(px):
    def f(a): b = a.copy(); b[..., 0] = np.roll(a[..., 0], px, axis=1); b[..., 2] = np.roll(a[..., 2], -px, axis=1); return b
    return f


def scan(amt, step=3):
    def f(a): a[::step, :, :3] *= (1 - amt); return a
    return f


def glitch(seed, amt=1.0, bands=6):
    def f(a):
        rng = random.Random(seed)
        for _ in range(int(bands * amt)):
            y = rng.randint(0, VH - 14); h = rng.randint(3, 14); s = rng.randint(-40, 40); a[y:y + h] = np.roll(a[y:y + h], s, axis=1)
        return a
    return f


def radial_warp(cx, cy, amt):
    """pinch toward (cx, cy) in screen px (gravity lens)"""
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    def f(a):
        dx, dy = xx - cx, yy - cy; r = np.sqrt(dx * dx + dy * dy) + 1e-6; k = 1.0 + amt * np.exp(-r / 90.0)
        sx = np.clip(cx + dx * k, 0, VW - 1).astype(int); sy = np.clip(cy + dy * k, 0, VH - 1).astype(int); return a[sy, sx]
    return f
