"""Animated backgrounds for special player cards. t is 0..1 and every effect loops seamlessly (integer cycles).
rainbow = full-spectrum holo (LEGEND), galaxy = purple/pink nebula + stars + shooting star (EPIC), aurora = teal/green/violet waves (RARE)."""
import math
import numpy as np

W, H = 64, 90
STYLE_BY_RARITY = dict(LEGEND='rainbow', EPIC='galaxy', RARE='aurora')
RAMPS = dict(
    galaxy=[(8, 6, 34), (28, 14, 84), (80, 28, 150), (160, 44, 170), (236, 100, 200), (110, 210, 255)],
    aurora=[(6, 22, 44), (10, 70, 96), (20, 150, 140), (90, 232, 170), (150, 205, 255), (170, 120, 255)],
)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
Y, X = np.mgrid[0:H, 0:W].astype(float)


def hsv(h, s, v):
    h = (h % 1.0) * 6; i = np.floor(h).astype(int) % 6; f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4], [v, q, p, p, t], v)
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4], [t, v, v, q, p], p)
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4], [p, p, t, v, v], q)
    return np.stack([r, g, b], -1) * 255


def ramp(style, n):
    st = np.array(RAMPS[style], float); n = np.clip(n, 0, 1) * (len(st) - 1)
    i = np.minimum(n.astype(int), len(st) - 2); f = (n - i)[..., None]
    return st[i] * (1 - f) + st[i + 1] * f


def edge_colour(style, u):
    """colour of the outer frame at position u (0..1 around the card, already shifted by time)"""
    if style == 'rainbow': return tuple(int(v) for v in hsv(np.array(u), 0.55, 1.0))
    c = ramp(style, np.array(0.5 + 0.5 * math.sin(2 * math.pi * u)))
    return tuple(int(min(255, v * 1.25 + 30)) for v in c)


def background(style, t, cx=32, cy=28):
    a = 2 * math.pi * t
    d = np.hypot(X - cx, Y - cy)
    if style == 'rainbow':
        h = (X * 0.011 + Y * 0.019 - t) % 1.0
        h += 0.06 * np.sin(Y * 0.3 + a * 2)                       # wavy bands
        # posterise the hue to 12 steps so it reads as pixel art
        h = np.round(h * 12) / 12
        col = hsv(h, 0.62 + 0.1 * np.sin(X * 0.2 + a), 0.92)
        w = 0.62 - 0.3 * np.clip((Y - 50) / 24, 0, 1) - 0.12 * np.clip((16 - Y) / 16, 0, 1)
        base = np.array([14, 12, 26], float)
        out = base * (1 - w[..., None]) + col * w[..., None]
        out += (np.clip(1 - d / 26, 0, 1) ** 1.6)[..., None] * 90
    else:
        if style == 'galaxy':
            n = 0.42 + 0.17 * (np.sin(X * 0.13 + Y * 0.08 + a) + np.sin(Y * 0.17 - X * 0.05 - a + 1) + 0.6 * np.sin((X + Y) * 0.09 + 2 * a))
            n += 0.30 * np.clip(1 - d / 30, 0, 1) ** 1.4
        else:
            wave = np.sin(Y * 0.21 + 1.7 * np.sin(X * 0.11 + a) + a)
            n = 0.28 + 0.22 * wave + 0.16 * np.sin(X * 0.07 - a) + 0.30 * np.clip(1 - d / 30, 0, 1) ** 1.4
        n = np.clip(n + (np.tile(BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W] - 0.5) * 0.12, 0, 1)
        n = np.round(n * 11) / 11
        out = ramp(style, n)
        out *= (1 - 0.6 * np.clip((Y - 50) / 30, 0, 1))[..., None]
    # slow glare band sweeping across
    pos = t * (W + H * 0.6 + 36) - 18
    g = np.clip(1 - np.abs(X + Y * 0.6 - pos) / 4.5, 0, 1)
    out = out + g[..., None] * 70
    out = np.clip(out, 0, 255)
    # stars (twinkle) and, for galaxy, a shooting star
    rs = np.random.RandomState(11 if style == 'galaxy' else 5)
    n_st = 30 if style != 'rainbow' else 16
    for k in range(n_st):
        x, y = rs.randint(3, W - 3), rs.randint(3, 66); ph, kk = rs.rand(), 1 + k % 2
        b = 0.5 + 0.5 * math.sin(2 * math.pi * (kk * t + ph))
        if b < 0.25 and style != 'rainbow': continue
        if 10 < y < 17 and x < 22: continue       # keep the rating readable
        col = np.array([255, 255, 255.]) if k % 3 else np.array([255, 240, 160.])
        out[y, x] = out[y, x] * (1 - b) + col * b
        if k % 6 == 0 and b > 0.7:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): out[y + dy, x + dx] = out[y + dy, x + dx] * 0.4 + col * 0.6
    if style == 'galaxy' and 0.05 <= t < 0.35:
        u = (t - 0.05) / 0.30
        hx, hy = -6 + u * 84, 8 + u * 46
        for s in range(10):
            x, y = int(hx - s * 1.6), int(hy - s * 0.9)
            if 1 <= x < W - 1 and 1 <= y < H - 1: out[y, x] = out[y, x] * (1 - 0.9 * (1 - s / 10)) + np.array([255, 255, 255.]) * 0.9 * (1 - s / 10)
    return np.clip(out, 0, 255).astype(np.uint8)
