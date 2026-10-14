import math, random
import numpy as np
from PIL import Image, ImageDraw

W_, H_ = 56, 38
INK = (14, 12, 26)
WHITE = (244, 244, 250); GREY = (176, 182, 210); DKG = (110, 116, 150)

def new(): return Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
def bez(p0, p1, p2, p3, n=28):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0], u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out

def outline(im, col=INK):
    a = np.array(im); m = a[..., 3] > 0
    p = np.pad(m, 1); nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    edge = nb & ~m
    a[edge] = col + (255,); return Image.fromarray(a, 'RGBA')

def ball(im, cx, cy, r=7, sx=1.0, sy=1.0, rot=0.0, glow=None):
    a = np.array(im); rx, ry = r * sx, r * sy
    L = np.array([-0.5, -0.6, 0.62]); L /= np.linalg.norm(L)
    P = [np.array([math.cos(rot + k * 2.1) * 0.8, math.sin(rot + k * 2.1) * 0.8, 0.35]) for k in range(3)]
    P = [p / np.linalg.norm(p) for p in P]
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            if not (0 <= x < W_ and 0 <= y < H_): continue
            u = (x + 0.5 - cx) / rx; v = (y + 0.5 - cy) / ry; d2 = u * u + v * v
            if d2 > 1: continue
            n = np.array([u, v, math.sqrt(max(0, 1 - d2))]); lam = n @ L
            col = WHITE if lam > 0.35 else (GREY if lam > -0.15 else DKG)
            if any(n @ p > 0.93 for p in P): col = (34, 36, 66) if lam > -0.15 else (20, 22, 44)
            a[y, x] = col + (255,)
    im2 = outline(Image.fromarray(a, 'RGBA'))
    return im2

def disc(d, cx, cy, r, col):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

def trail(im, pts, pal, w0=0.6, w1=3.2, glowcol=None):
    d = ImageDraw.Draw(im); n = len(pts)
    for i, (x, y) in enumerate(pts):
        t = i / (n - 1); r = w0 + (w1 - w0) * t
        c = tuple(int(pal['dark'][k] * (1 - t) + pal['light'][k] * t) for k in range(3)) + (int(70 + 185 * t),)
        disc(d, x, y, r, c)
    for i in range(0, n, 1):
        x, y = pts[i]; t = i / (n - 1)
        if t > 0.35: d.point((int(x), int(y)), (255, 255, 255, int(255 * t)))

def dashed_arc(im, pts, pal, every=2):
    d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate(pts):
        if (i // every) % 2 == 0: disc(d, x, y, 1.0, pal['light'] + (255,))

def speed_lines(im, cx, cy, pal, dirv=(-1, 0), n=5, length=14, spread=9, seed=1):
    d = ImageDraw.Draw(im); rng = random.Random(seed)
    for i in range(n):
        off = (i - (n - 1) / 2) * spread / max(1, n - 1)
        ln = length * rng.uniform(0.6, 1.0); sx_, sy_ = cx - dirv[0] * 6, cy + off * (1 if abs(dirv[0]) > 0 else 0)
        ex, ey = sx_ + dirv[0] * ln * 1.0 * -1, sy_ + dirv[1] * ln * -1
        d.line([(sx_, sy_), (ex, ey)], fill=pal['light'] + (200,), width=1)

def star(im, cx, cy, r1, r2, col, pts=8, rot=0.0, inner=None):
    d = ImageDraw.Draw(im); poly = []
    for i in range(pts * 2):
        rr = r2 if i % 2 == 0 else r1; a = rot + i * math.pi / pts
        poly.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(poly, fill=col)
    if inner:
        poly = []
        for i in range(pts * 2):
            rr = (r2 if i % 2 == 0 else r1) * 0.55; a = rot + i * math.pi / pts
            poly.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(poly, fill=inner)

def sparkle(d, x, y, col, s=2):
    for k in range(-s, s + 1): d.point((x + k, y), col); d.point((x, y + k), col)
    d.point((x, y), (255, 255, 255, 255))

def rings(im, cx, cy, pal, n=3, step=3, flat=0.45):
    d = ImageDraw.Draw(im)
    for i in range(n):
        r = 4 + i * step; a = 220 - i * 60
        d.ellipse([cx - r, cy - r * flat, cx + r, cy + r * flat], outline=pal['light'] + (a,))

def wings(im, cx, cy, pal, span=1.0):
    wing = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(wing)
    for side in (-1, 1):
        for i, (dx, dy, ln) in enumerate(((7, -2, 13), (6, 1, 15), (5, 4, 13), (4, 7, 10))):
            x0, y0 = cx + side * dx, cy + dy
            x1, y1 = cx + side * (dx + ln * span), cy + dy - (5 - i * 1.5)
            d.line([(x0, y0), (x1, y1)], fill=(236, 242, 255, 255), width=3)
            d.line([(x0, y0 + 1), (x1, y1 + 1)], fill=(176, 194, 236, 255), width=1)
    return outline(wing)

def flame(im, x, y, length=16, pal=None, rng=3):
    d = ImageDraw.Draw(im)
    for i in range(length):
        t = i / length; w = 3.2 * (1 - t) + 0.4
        col = (255, int(220 - 140 * t), int(80 - 60 * t), int(255 * (1 - t * 0.6)))
        disc(d, x - i, y + math.sin(i * 0.9) * 1.1, w, col)

def bolt(im, x, y, s=1.0, col=(255, 240, 120)):
    d = ImageDraw.Draw(im)
    pts = [(x + 2 * s, y - 7 * s), (x - 3 * s, y + 0 * s), (x + 0 * s, y + 0 * s), (x - 2 * s, y + 7 * s), (x + 4 * s, y - 2 * s), (x + 1 * s, y - 2 * s)]
    d.polygon(pts, fill=col + (255,), outline=(255, 255, 255, 255))

def goalframe(im, x0, y0, x1, y1, col=(230, 235, 245)):
    d = ImageDraw.Draw(im); d.line([(x0, y1), (x0, y0), (x1, y0), (x1, y1)], fill=col + (255,), width=1)
    for xx in range(x0 + 2, x1, 3): d.line([(xx, y0 + 1), (xx, y1)], fill=col + (70,))
    for yy in range(y0 + 2, y1, 3): d.line([(x0 + 1, yy), (x1 - 1, yy)], fill=col + (70,))

def ground(im, y, pal):
    d = ImageDraw.Draw(im); d.line([(2, y), (W_ - 3, y)], fill=pal['light'] + (90,))

def shadow(im, cx, cy, rx, ry=1.6):
    d = ImageDraw.Draw(im); d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(6, 6, 20, 170))

def flex_arm(cx=26, cy=22):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    SK = (238, 178, 124, 255); SD = (186, 120, 84, 255); SH = (255, 224, 184, 255)
    d.line([(5, 32), (22, 29)], fill=SK, width=9)                       # upper arm
    d.ellipse([14, 13, 31, 29], fill=SK)                                 # bicep
    d.line([(24, 22), (33, 13)], fill=SK, width=8)                       # forearm
    d.ellipse([29, 3, 42, 15], fill=SK)                                  # fist
    d.line([(31, 8), (40, 8)], fill=SD); d.line([(31, 11), (40, 11)], fill=SD)  # knuckles
    d.arc([14, 13, 31, 29], 190, 300, fill=SH, width=2)                   # highlight
    d.ellipse([18, 17, 23, 22], fill=SH)
    d.line([(8, 35), (22, 33)], fill=SD, width=1)                         # underside shade
    d.arc([14, 13, 31, 29], 20, 120, fill=SD, width=2)
    return outline(m)
