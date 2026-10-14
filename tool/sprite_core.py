"""Sprite sheet logic with no GUI: grid detection, colour ramps, recolouring, export. Used by app.py and testable alone."""
import colorsys, json, os
import numpy as np
from PIL import Image

SLOTS = ['(none)', 'skin', 'hair', 'jersey', 'jersey2', 'shorts', 'socks', 'boots', 'gloves', 'ball', 'other']


def load(path):
    return Image.open(path).convert('RGBA')


# ---------------------------------------------------------------- grid
def detect_grid(img, min_cell=8, max_cell=256, tol=0.005):
    """Smallest cell size (w, h) that cuts almost no sprite pixels at its borders. Falls back to the whole image."""
    a = np.array(img)[:, :, 3] > 0
    H, W = a.shape

    def best(n, axis):
        for c in range(min_cell, min(max_cell, n) + 1):
            if n % c:
                continue
            edges = range(c, n, c)
            if axis == 1:   # vertical borders: pixels either side of x are both opaque
                cut = sum(int((a[:, e - 1] & a[:, e]).sum()) for e in edges)
            else:
                cut = sum(int((a[e - 1, :] & a[e, :]).sum()) for e in edges)
            if cut <= tol * max(1, a.sum()):
                return c
        return n
    return best(W, 1), best(H, 0)


def cells(img, cw, ch):
    W, H = img.size
    return [[img.crop((x, y, x + cw, y + ch)) for x in range(0, W - cw + 1, cw)] for y in range(0, H - ch + 1, ch)]


# ---------------------------------------------------------------- colours and ramps
def unique_colours(img, quant_above=256):
    a = np.array(img)
    op = a[:, :, 3] > 0
    rgb = a[:, :, :3][op]
    if len(rgb) == 0:
        return np.zeros((0, 3), np.uint8), np.zeros(0, int)
    cols, counts = np.unique(rgb, axis=0, return_counts=True)
    if len(cols) > quant_above:   # anti-aliased or photo-like: snap to 5 bits per channel
        q = (rgb >> 3) << 3 | 4
        cols, counts = np.unique(q, axis=0, return_counts=True)
    return cols.astype(np.uint8), counts


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def group_ramps(cols, counts, hue_tol=0.06, dark_v=0.16):
    """Group colours into ramps by hue. Returns list of dicts {idx:[colour indices dark->light], name, base}.
    Greys split into 'dark/outline' and 'grey/white'."""
    hsv = [colorsys.rgb_to_hsv(*(c / 255.0)) for c in cols]
    groups = []   # [mean hue, [indices]]
    outline, grey = [], []
    for i, (h, s, v) in enumerate(hsv):
        if v < dark_v:
            outline.append(i)
        elif s < 0.15:
            grey.append(i)
        else:
            for g in groups:
                d = abs(h - g[0]); d = min(d, 1 - d)
                if d <= hue_tol:
                    g[1].append(i)
                    g[0] = float(np.average([hsv[j][0] for j in g[1]], weights=[counts[j] for j in g[1]]))
                    break
            else:
                groups.append([h, [i]])
    out = [g[1] for g in groups]
    if grey: out.append(grey)
    if outline: out.append(outline)
    ramps = []
    for idx in out:
        idx = sorted(idx, key=lambda j: _lum(cols[j]))
        tot = counts[idx].sum()
        base = np.average(cols[idx].astype(float), axis=0, weights=counts[idx])
        ramps.append(dict(idx=idx, pixels=int(tot), base=tuple(int(round(x)) for x in base), slot='(none)', target=None))
    ramps.sort(key=lambda r: -r['pixels'])
    return ramps


def recolour_map(cols, ramp):
    """New colour for each colour in the ramp so the ramp's base colour becomes ramp['target'] and shading is kept."""
    t = ramp['target']
    if t is None:
        return {j: tuple(cols[j]) for j in ramp['idx']}
    bh, bl, bs = colorsys.rgb_to_hls(*(np.array(ramp['base']) / 255.0))
    th, tl, ts = colorsys.rgb_to_hls(*(np.array(t) / 255.0))
    res = {}
    for j in ramp['idx']:
        h, l, s = colorsys.rgb_to_hls(*(cols[j] / 255.0))
        nl = min(1.0, max(0.0, l + (tl - bl)))
        ns = min(1.0, max(0.0, s * (ts / bs) if bs > 1e-3 else ts))
        r, g, b = colorsys.hls_to_rgb(th, nl, ns)
        res[j] = (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
    return res


def colour_index_map(img, cols):
    """Per pixel index into cols (-1 for transparent). Handles quantised palettes the same way as unique_colours."""
    a = np.array(img)
    rgb = a[:, :, :3].astype(np.int32)
    d = ((rgb[:, :, None, :] - cols[None, None, :, :].astype(np.int32)) ** 2).sum(-1) if rgb.size * len(cols) < 3e7 else None
    if d is None:   # big image: do it in row bands
        idx = np.empty(rgb.shape[:2], np.int32)
        for y in range(0, rgb.shape[0], 16):
            band = rgb[y:y + 16]
            idx[y:y + 16] = ((band[:, :, None, :] - cols[None, None].astype(np.int32)) ** 2).sum(-1).argmin(-1)
    else:
        idx = d.argmin(-1)
    idx[a[:, :, 3] == 0] = -1
    return idx


def apply(img, cols, ramps, idxmap=None):
    """Baked recoloured copy of img."""
    if idxmap is None:
        idxmap = colour_index_map(img, cols)
    a = np.array(img).copy()
    for r in ramps:
        if r['target'] is None:
            continue
        for j, c in recolour_map(cols, r).items():
            a[idxmap == j, :3] = c
    return Image.fromarray(a, 'RGBA')


def export_indexed(img, cols, ramps, idxmap, out_png, out_pal_png):
    """Indexed sheet (R = palette index, A kept) + 1-row palette image. A shader looks up palette[R]; swap the palette to recolour."""
    if len(cols) > 256:
        raise ValueError('more than 256 colours, cannot index')
    a = np.array(img)
    o = np.zeros_like(a)
    o[:, :, 0] = np.clip(idxmap, 0, 255)
    o[:, :, 3] = a[:, :, 3]
    Image.fromarray(o, 'RGBA').save(out_png)
    pal = np.zeros((1, len(cols), 4), np.uint8)
    pal[0, :, :3] = cols; pal[0, :, 3] = 255
    for r in ramps:
        if r['target'] is not None:
            for j, c in recolour_map(cols, r).items():
                pal[0, j, :3] = c
    Image.fromarray(pal, 'RGBA').save(out_pal_png)


def save_scheme(path, ramps):
    json.dump([dict(base=r['base'], slot=r['slot'], target=r['target']) for r in ramps], open(path, 'w'), indent=1)
