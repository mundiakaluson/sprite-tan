"""Player card: same 64x90 frame as the skill cards. Rarity strip on top (with rating and role), the player's face sprite, name plate and
the three stats that matter most for the role. Full stats go in the hover tooltip (popup)."""
import os, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw
import portrait as PT
import looks  # noqa: F401  (adds sprites/ to the path)
import tables
from rules import *

CARDS_DIR = os.path.join(tables.ROOT, 'cards')
if CARDS_DIR not in sys.path:
    sys.path.insert(0, CARDS_DIR)
from cardlib import draw_text, text_w, INK, PANEL  # noqa: E402

CW, CH = 64, 90
RC = dict(COMMON=dict(main=(150, 156, 176), dark=(44, 48, 66), light=(214, 218, 232)), UNCOMMON=dict(main=(76, 184, 106), dark=(22, 64, 44), light=(150, 235, 170)),
          RARE=dict(main=(74, 144, 226), dark=(22, 44, 96), light=(150, 200, 255)), EPIC=dict(main=(168, 95, 216), dark=(52, 24, 84), light=(224, 170, 255)),
          LEGEND=dict(main=(240, 176, 48), dark=(84, 52, 12), light=(255, 236, 150)))
STAT_COL = (110, 214, 140)


def key_stats(p):
    """the three stats that matter most for this player's role"""
    if p.get('role') == 'GK':
        return [(k, to_int(p.get(k), 0)) for k in GK_STATS]
    w = RATING_W.get(p.get('role'), (1,) * 6)
    ks = sorted(range(6), key=lambda i: (-w[i], -to_int(p.get(OUT_STATS[i]), 0)))[:3]
    return [(OUT_STATS[i], to_int(p.get(OUT_STATS[i]), 0)) for i in ks]


PARTICLES = {'van', 'de', 'dos', 'da', 'di', 'del', 'der', 'den', 'al', 'el', 'le', 'la', 'ter', 'von', 'bin'}


def surname(name):
    w = (name or '').split()
    if len(w) < 2: return (name or '').upper()
    return (' '.join(w[-2:]) if w[-2].lower() in PARTICLES else w[-1]).upper()


def face(p, kit=None):
    """head and shoulders, facing the camera, big."""
    return PT.portrait(p, kit or 'home').resize((PT.W * 2, PT.H * 2), Image.NEAREST)


def _text2(im, x, y, s, col, k=2):
    t = Image.new('RGBA', (text_w(s) + 2, 7), (0, 0, 0, 0)); draw_text(t, 0, 0, s, col)
    im.alpha_composite(t.resize((t.width * k, t.height * k), Image.NEAREST), (x, y))


def _mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def card(p, kit=None, state='ready'):
    r = RC.get(p.get('rarity'), RC['COMMON']); legend = p.get('rarity') == 'LEGEND'
    base = (12, 13, 20); im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); px = im.load()
    cx, cy = 32, 28
    for y in range(CH):
        for x in range(CW):
            t = y / (CH - 1); c = _mix(_mix(r['dark'], base, 0.55), base, t)
            dd = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5          # glow behind the head
            if dd < 30: c = _mix(c, r['main'], 0.38 * (1 - dd / 30) ** 1.5)
            if (x - y // 2) % 9 == 0 and 14 < y < 60: c = _mix(c, r['light'], 0.05)   # faint diagonal streaks
            px[x, y] = c + (255,)
    # head and shoulders, fading into the dark at the bottom
    fc = face(p, kit); im.alpha_composite(fc, (4, 12))
    for y in range(46, 61):
        t = (y - 46) / 14
        for x in range(CW):
            c = px[x, y]; px[x, y] = _mix(c[:3], _mix(r['dark'], base, 0.8), min(1, t * t * 1.15)) + (255,)
    d = ImageDraw.Draw(im)
    # chamfered outline in the rarity colour
    edge = r['light'] if legend else r['main']
    for x in range(2, CW - 2): d.point((x, 0), edge + (255,)); d.point((x, CH - 1), edge + (255,))
    for y in range(2, CH - 2): d.point((0, y), edge + (255,)); d.point((CW - 1, y), edge + (255,))
    for (x, y, dx, dy) in ((1, 1, 1, 1), (CW - 2, 1, -1, 1), (1, CH - 2, 1, -1), (CW - 2, CH - 2, -1, -1)): d.point((x, y), edge + (255,))
    for (x, y) in ((0, 0), (CW - 1, 0), (0, CH - 1), (CW - 1, CH - 1)): d.point((x, y), (0, 0, 0, 0))
    # top left: rating (big) and role; top right: rarity
    _text2(im, 5, 5, str(p.get('rating', '')), (255, 255, 255, 255))
    role = p.get('role', ''); draw_text(im, 5, 18, role, r['light'] + (255,))
    d.line([(5, 25), (5 + max(text_w(role), 10), 25)], fill=r['main'] + (255,))
    rn = (p.get('rarity') or '').upper(); draw_text(im, CW - 5 - text_w(rn), 5, rn, r['light'] + (255,))
    # surname
    nm = surname(p.get('name')); ww = text_w(nm)
    draw_text(im, (CW - ww) // 2, 63, nm, (255, 255, 255, 255))
    d.line([(5, 66), (CW // 2 - ww // 2 - 3, 66)], fill=r['dark'] + (255,)); d.line([(CW // 2 + ww // 2 + 3, 66), (CW - 6, 66)], fill=r['dark'] + (255,))
    d.line([(CW // 2 - 6, 70), (CW // 2 + 5, 70)], fill=edge + (255,))
    # three stats: no boxes, thin dividers
    for ci, (kk, v) in enumerate(key_stats(p)):
        x0 = 4 + ci * 19; cxm = x0 + 9
        draw_text(im, cxm - text_w(kk) // 2, 76, kk, (140, 146, 176, 255))
        _text2(im, cxm - text_w(str(v)) + 1, 82, str(v), STAT_COL + (255,), 1) if False else draw_text(im, cxm - text_w(str(v)) // 2, 82, str(v), (255, 255, 255, 255))
        if ci: d.line([(x0 - 1, 76), (x0 - 1, 86)], fill=r['dark'] + (255,))
        d.line([(x0 + 3, 87), (x0 + 3 + int(12 * v / 100), 87)], fill=r['main'] + (255,))
    arr = np.array(im)
    if state == 'unavailable':
        arr[..., :3] = (arr[..., :3] * 0.3).astype(np.uint8); im = Image.fromarray(arr, 'RGBA')
    return im


def popup(p, w=148):
    r = RC.get(p.get('rarity'), RC['COMMON']); gk = p.get('role') == 'GK'; stats = GK_STATS if gk else OUT_STATS
    h = 8 + 7 + 8 + len(stats) * 7 + 4 + 7 + 8
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=INK + (255,)); d.rectangle([1, 1, w - 2, h - 2], fill=r['main'] + (255,)); d.rectangle([2, 2, w - 3, h - 3], fill=PANEL + (255,))
    draw_text(im, 6, 6, (p.get('name') or '').upper(), r['light'] + (255,))
    draw_text(im, 6, 13, f"{p.get('rarity', '')}  {p.get('role', '')}  RATING {p.get('rating', '')}", (150, 156, 190, 255))
    y = 22
    for k in stats:
        v = to_int(p.get(k), 0)
        draw_text(im, 6, y, k, (170, 176, 208, 255)); draw_text(im, 30, y, str(v), STAT_COL + (255,))
        d.rectangle([44, y + 1, w - 8, y + 3], fill=(48, 48, 70, 255)); d.rectangle([44, y + 1, 44 + int((w - 52) * v / 100), y + 3], fill=STAT_COL + (255,)); y += 7
    y += 3; draw_text(im, 6, y, 'PLAYS ' + (p.get('roles') or p.get('role', '')).replace('|', ' '), (235, 238, 250, 255))
    return im
