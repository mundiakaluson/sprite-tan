"""Pack wrappers in the player-card language: dark body with a glow, thin chamfered frame in the rarity colour, aurora / galaxy / rainbow foil on the rare tiers,
a hidden-player silhouette, big count top left, tier top right, name plate with thin lines, cost along the bottom (taken from data/pack_odds.csv).
Run:  python packs/design2.py  -> export/packs/design2_foil.png, design2_sleeve.png"""
import os, sys, math, csv
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
for p in ('tool', 'cards', 'sprites'): sys.path.insert(0, os.path.join(ROOT, p))
import foil
from cardlib import draw_text, text_w
from playercard import RC, _mix, _spark, _text2

W, H = 64, 96; BW, BH, BY = 64, 90, 3
BASE = (12, 13, 20)
# pack -> (rarity palette, foil style or None, silhouette kind)
LOOK = {'Player Pack': ('COMMON', None, 'bust'), 'Card Pack': ('UNCOMMON', None, 'cards'), 'Mixed Pack': ('RARE', None, 'both'),
        'Rare Pack': ('RARE', 'aurora', 'bust'), 'Epic Pack': ('EPIC', 'galaxy', 'bust'), 'Legend Pack': ('LEGEND', 'rainbow', 'bust')}
TIER = {'Player Pack': 'COMMON', 'Card Pack': 'COMMON', 'Mixed Pack': 'COMMON', 'Rare Pack': 'RARE', 'Epic Pack': 'EPIC', 'Legend Pack': 'LEGEND'}


def odds():
    return {r['pack']: r for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'pack_odds.csv'), encoding='utf-8'))}


def body(r, style):
    if style:
        im = Image.fromarray(foil.background(style, 0.9), 'RGB').convert('RGBA'); return im
    im = Image.new('RGBA', (BW, BH)); px = im.load(); cx, cy = 32, 30
    for y in range(BH):
        for x in range(BW):
            t = y / (BH - 1); c = _mix(_mix(r['dark'], BASE, 0.55), BASE, t); dd = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dd < 32: c = _mix(c, r['main'], 0.38 * (1 - dd / 32) ** 1.5)
            if (x - y // 2) % 9 == 0 and 8 < y < 62: c = _mix(c, r['light'], 0.05)
            px[x, y] = c + (255,)
    return im


def silhouette(kind, r, style):
    """the unseen player: head and shoulders in near-black with a thin rim light on the upper left"""
    Yg, Xg = np.mgrid[0:BH, 0:BW].astype(float)
    head = ((Xg - 32) / 9.5) ** 2 + ((Yg - 38) / 11.5) ** 2 <= 1
    neck = (abs(Xg - 32) <= 5.5) & (Yg > 44) & (Yg < 56)
    sh = (((Xg - 32) / 27) ** 2 + ((Yg - 77) / 26) ** 2 <= 1) & (Yg > 49)
    m = head | neck | sh
    if kind == 'cards':
        m = np.zeros_like(m)
    fade = np.clip(1 - (Yg - 54) / 10.0, 0, 1) if style else np.clip(1 - (Yg - 50) / 9.0, 0, 1)
    a = (m * (0.84 if style else 0.9) * (0.45 + 0.55 * np.clip(1.0 - (Yg - 58) / 6.0, 0, 1))).astype(float)
    dark = tuple(int(v * 0.32) for v in r['dark'])
    out = np.zeros((BH, BW, 4), np.uint8); out[..., :3] = dark; out[..., 3] = (a * 255).astype(np.uint8)
    rim = m & (~np.roll(m, 1, 0) | ~np.roll(m, 1, 1))                           # lit edge where the shape meets light from the upper left
    out[rim & (Yg < 60)] = tuple(int(v) for v in _mix(r['main'], r['light'], 0.4)) + (220,)
    im = Image.fromarray(out, 'RGBA'); d = ImageDraw.Draw(im)
    if kind in ('cards', 'both'):                                                 # a fan of three card backs
        cx, cy = (32, 38) if kind == 'cards' else (49, 50)
        for i, ang in enumerate((-16, 0, 16)):
            cw, ch = (18, 26) if kind == 'cards' else (11, 16); pts = [(-cw / 2, -ch / 2), (cw / 2, -ch / 2), (cw / 2, ch / 2), (-cw / 2, ch / 2)]; s, c = math.sin(math.radians(ang)), math.cos(math.radians(ang))
            P = [(cx + x * c - y * s + ang * 0.45, cy + x * s + y * c + abs(ang) * 0.3) for x, y in pts]
            d.polygon(P, fill=tuple(int(v * 0.55) for v in r['dark']) + (255,), outline=r['main'] + (255,)); d.line([P[0], P[1]], fill=r['light'] + (255,))
            if i == 1:
                d.rectangle([cx - 4, cy - 5, cx + 4, cy + 5], outline=r['main'] + (255,)); d.point((cx, cy), r['light'] + (255,))
    return im


def foil_bag(pk, od):
    rar, style, kind = LOOK[pk]; r = RC[rar]; legend = rar == 'LEGEND'; edge = r['light'] if legend else r['main']
    b = body(r, style); sil = silhouette(kind, r, style); b.alpha_composite(sil)
    px = b.load()
    for y in range(46, BH):                                                        # darken toward the bottom for the text
        tt = max(0.0, (y - 46) / 14)
        for x in range(BW):
            c = px[x, y]; px[x, y] = _mix(c[:3], tuple(int(v * 0.3) for v in c[:3]) if style else _mix(r['dark'], BASE, 0.8), min(1, tt * tt * 1.15)) + (255,)
    d = ImageDraw.Draw(b)
    # top left: item count (big) and what it is; top right: tier
    n = int(od['player_items']) + int(od['card_items']); what = {'Player Pack': 'PLAYERS', 'Card Pack': 'CARDS'}.get(pk, 'ITEMS')
    _text2(b, 5, 5, str(n), (255, 255, 255, 255)); draw_text(b, 5, 18, what, r['light'] + (255,)); d.line([(5, 25), (5 + max(text_w(what), 10), 25)], fill=r['main'] + (255,))
    tn = TIER[pk]; draw_text(b, BW - 5 - text_w(tn), 5, tn, r['light'] + (255,))
    if style: _spark(d, BW - 5 - text_w(tn) - 4, 7, (255, 255, 255, 255))
    nm = pk.upper().replace(' PACK', ''); ww = text_w(nm)
    draw_text(b, (BW - ww) // 2, 63, nm, (255, 255, 255, 255)); draw_text(b, (BW - text_w('PACK')) // 2, 70, 'PACK', r['light'] + (255,))
    d.line([(5, 66), (BW // 2 - ww // 2 - 3, 66)], fill=r['dark'] + (255,)); d.line([(BW // 2 + ww // 2 + 3, 66), (BW - 6, 66)], fill=r['dark'] + (255,))
    rare = float(od['rare']) + float(od['epic']) + float(od['legend']); cols = [('COST', od['price'])]
    for ci, (kk, v) in enumerate(cols):
        cxm = BW // 2
        draw_text(b, cxm - text_w(kk) // 2, 77, kk, (140, 146, 176, 255)); draw_text(b, cxm - text_w(v) // 2, 83, v, (255, 255, 255, 255))
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); out.alpha_composite(b, (0, BY)); d = ImageDraw.Draw(out)
    metal = _mix(r['dark'], (120, 126, 150), 0.45) if not legend else _mix(r['dark'], (255, 220, 150), 0.5); hi = _mix(metal, (255, 255, 255), 0.35)
    for (y0, y1, top) in ((0, BY - 1, True), (BY + BH, H - 1, False)):             # crimped ends: fine vertical ridges and a serrated cut
        for y in range(y0, y1 + 1):
            for x in range(1, W - 1):
                if (top and y == y0 and x % 3 == 0) or ((not top) and y == y1 and x % 3 == 0): continue
                d.point((x, y), (hi if x % 4 < 1 else metal if x % 4 < 3 else _mix(metal, (0, 0, 0), 0.35)) + (255,))
        yy = BY - 1 if top else BY + BH
        d.line([(1, yy), (W - 2, yy)], fill=_mix(metal, (0, 0, 0), 0.55) + (255,))
    # frame
    ys = range(BY, BY + BH)
    if style:
        per = [(x, BY) for x in range(2, W - 2)] + [(W - 1, y) for y in range(BY + 2, BY + BH - 2)] + [(x, BY + BH - 1) for x in range(W - 3, 1, -1)] + [(0, y) for y in range(BY + BH - 3, BY + 1, -1)]
        for k, (x, y) in enumerate(per): d.point((x, y), foil.edge_colour(style, k / len(per) * 2) + (255,))
        for (x, y) in ((2, BY + 2), (W - 3, BY + 2), (2, BY + BH - 3), (W - 3, BY + BH - 3)): _spark(d, x, y, (255, 255, 255, 255))
    else:
        for y in ys: d.point((0, y), edge + (255,)); d.point((W - 1, y), edge + (255,))
        for x in range(1, W - 1): d.point((x, BY), edge + (255,)); d.point((x, BY + BH - 1), edge + (255,))
    for (x, y) in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)): out.putpixel((x, y), (0, 0, 0, 0))
    return out


def sleeve(pk, od):
    """a rigid sleeve: no crimp, a slim lid, and a diagonal paper band across the foil carrying the name"""
    f = foil_bag(pk, od); rar, style, kind = LOOK[pk]; r = RC[rar]; d = ImageDraw.Draw(f)
    d.rectangle([0, 0, W - 1, 6], fill=_mix(r['dark'], BASE, 0.5) + (255,)); d.line([(0, 7), (W - 1, 7)], fill=r['main'] + (255,)); d.line([(0, 8), (W - 1, 8)], fill=_mix(r['dark'], BASE, 0.8) + (255,))
    d.rectangle([0, H - 7, W - 1, H - 1], fill=_mix(r['dark'], BASE, 0.5) + (255,)); d.line([(0, H - 8), (W - 1, H - 8)], fill=r['main'] + (255,))
    for x in range(4, W - 4, 6): d.point((x, 3), r['main'] + (255,)); d.point((x, H - 4), r['main'] + (255,))
    for (x, y) in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)): f.putpixel((x, y), (0, 0, 0, 0))
    return f


def sheet(fn, S=4):
    od = odds(); im = Image.new('RGB', (len(LOOK) * (W * S + 16) + 16, H * S + 32), (22, 16, 38))
    for i, pk in enumerate(LOOK):
        p = fn(pk, od[pk]).resize((W * S, H * S), Image.NEAREST); im.paste(p, (16 + i * (W * S + 16), 16), p)
    return im


if __name__ == '__main__':
    out = os.path.join(ROOT, 'export', 'packs'); os.makedirs(out, exist_ok=True)
    a = sheet(foil_bag); a.save(os.path.join(out, 'design2.png')); print(a.size)
