"""Aura preview for SUPPORT cards (data/support_auras.csv). Draws onto a cell-sized RGBA layer; the game will draw the same shapes."""
import csv, math, os
import numpy as np
from PIL import Image

_ROWS = None
PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'support_auras.csv')


TITAN = os.path.join(os.path.dirname(__file__), '..', 'data', 'titan_fx.csv')


def row(cid):
    """aura row for a SUPPORT card (support_auras.csv) or a TITAN card (titan_fx.csv, with a `base` animation it plays over)"""
    global _ROWS
    if _ROWS is None:
        _ROWS = {}
        for p in (PATH, TITAN):
            try: _ROWS.update({r['id']: r for r in csv.DictReader(open(p, encoding='utf-8'))})
            except OSError: pass
    return _ROWS.get(cid)


def _rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _blob(w, h, cx, cy, rx, ry, col, a):
    y, x = np.mgrid[0:h, 0:w]; d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    al = np.clip(1.0 - d, 0, 1) ** 1.4 * a
    im = np.zeros((h, w, 4), np.uint8); im[..., :3] = col; im[..., 3] = (al * 255).astype(np.uint8); return Image.fromarray(im, 'RGBA')


def _ring(w, h, cx, cy, rx, ry, col, a, th=0.22):
    y, x = np.mgrid[0:h, 0:w]; d = np.sqrt(((x - cx) / max(rx, .1)) ** 2 + ((y - cy) / max(ry, .1)) ** 2)
    al = np.clip(1.0 - np.abs(d - 1.0) / th, 0, 1) * a
    im = np.zeros((h, w, 4), np.uint8); im[..., :3] = col; im[..., 3] = (al * 255).astype(np.uint8); return Image.fromarray(im, 'RGBA')


def layers(r, t, w, h):
    """-> (under, over): RGBA layers for tick t (ticks at ~70ms). cx=player centre, feet at y~31."""
    col = _rgb(r['color']); shape = r['shape']; scope = r['scope']
    under = Image.new('RGBA', (w, h), (0, 0, 0, 0)); over = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    s = 0.5 + 0.5 * math.sin(t * 0.35); cyc = (t % 20) / 20.0
    if shape == 'glow':
        under.alpha_composite(_blob(w, h, 20, 20, 15 + 2 * s, 17 + 2 * s, col, 0.55 + 0.25 * s))
    elif shape == 'glow_legs':
        under.alpha_composite(_blob(w, h, 20, 26, 13 + 2 * s, 9 + 1.5 * s, col, 0.65 + 0.2 * s))
        over.alpha_composite(_ring(w, h, 20, 31, 8 + 3 * cyc, 2.5 + 1.2 * cyc, col, 0.8 * (1 - cyc)))
    elif shape == 'ring':
        under.alpha_composite(_ring(w, h, 20, 31, 9 + s, 3.2 + 0.4 * s, col, 0.9))
        over.alpha_composite(_ring(w, h, 20, 31 - 20 * cyc, 8, 2.6, col, 0.6 * (1 - cyc)))     # a second ring rises up the body
    elif shape == 'pulse':
        for k in (0.0, 0.5):
            c = (cyc + k) % 1.0
            under.alpha_composite(_ring(w, h, 20, 24, 6 + 22 * c, 4 + 14 * c, col, 0.85 * (1 - c), 0.28))
        under.alpha_composite(_blob(w, h, 20, 22, 14, 16, col, 0.25 + 0.2 * s))
    elif shape == 'flash':
        e = max(0.0, 1.0 - (t % 28) / 10.0)
        under.alpha_composite(_blob(w, h, 20, 20, 17, 19, col, 0.25 + 0.7 * e)); over.alpha_composite(_ring(w, h, 20, 24, 4 + 16 * (1 - e), 4 + 16 * (1 - e), col, 0.8 * e))
    elif shape in ('bolt', 'crush', 'ghost', 'fire', 'trail', 'wave', 'vortex', 'freeze'):
        _titan(under, over, shape, col, t, w, h, s, cyc)
    return under, over


def _titan(under, over, shape, col, t, w, h, s, cyc):
    from PIL import ImageDraw
    import random
    if shape == 'bolt':                                  # jagged lightning flicking around the body
        rnd = random.Random(t // 2); d = ImageDraw.Draw(over)
        for _ in range(3):
            x, y = rnd.randint(8, 32), 4
            pts = [(x, y)]
            for k in range(5): x += rnd.randint(-5, 5); y += 5; pts.append((x, y))
            d.line(pts, fill=col + (230,), width=1)
        under.alpha_composite(_blob(w, h, 20, 20, 16, 18, col, 0.35 + 0.25 * s))
    elif shape == 'vortex':                              # swirling arms spiralling inward
        d = ImageDraw.Draw(over)
        for k in range(10):
            a = t * 0.3 + k * 0.63; r = 18 - (k + (t % 10)) % 10 * 1.6
            d.point((int(20 + math.cos(a) * r), int(22 + math.sin(a) * r * 0.55)), fill=col + (230,))
        under.alpha_composite(_blob(w, h, 20, 24, 14, 8, col, 0.4 + 0.2 * s))
    elif shape == 'wave':                                # ground shockwave (earthquake / steel shimmer)
        for k in (0.0, 0.4):
            c = (cyc + k) % 1.0; under.alpha_composite(_ring(w, h, 20, 31, 4 + 22 * c, 1.5 + 7 * c, col, 0.9 * (1 - c), 0.3))
    elif shape in ('trail', 'fire'):                     # streaks / flames trailing off to the left of the cell
        d = ImageDraw.Draw(under); rnd = random.Random(t)
        for k in range(9):
            y = 22 + rnd.randint(-9, 9); x1 = 20 - rnd.randint(2, 6); L = rnd.randint(5, 13)
            d.line([(x1, y), (x1 - L, y)], fill=col + (200 if shape == 'trail' else 230,), width=1)
        if shape == 'fire': under.alpha_composite(_blob(w, h, 14, 26, 9, 6, (255, 200, 60), 0.5))
    elif shape == 'freeze':                              # cold white wash
        under.alpha_composite(_blob(w, h, 20, 20, 40, 40, col, 0.28 + 0.1 * s))
    elif shape in ('crush', 'ghost'):
        under.alpha_composite(_blob(w, h, 20, 28, 10, 6, col, 0.5 + 0.3 * s)); over.alpha_composite(_ring(w, h, 20, 31, 6 + 2 * s, 2.2, col, 0.8))


def marker(r, t, w, h, x, y):
    """other-player marker for scope target / two / opponent: a small ghost dot with the same ring"""
    col = _rgb(r['color']); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); s = 0.5 + 0.5 * math.sin(t * 0.35)
    im.alpha_composite(_ring(w, h, x, y, 6 + s, 2.2, col, 0.85)); im.alpha_composite(_blob(w, h, x, y - 5, 4, 6, col, 0.5)); return im
