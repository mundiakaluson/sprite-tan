"""Player card: same 64x90 frame as the skill cards. Rarity strip on top (with rating and role), the player's face sprite, name plate and
the three stats that matter most for the role. Full stats go in the hover tooltip (popup)."""
import os, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw
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


def face(p, kit=None):
    """close-up of the player's head and shoulders, facing the camera."""
    im = looks.render(p, 'guard', 0, 0, kit, shadow=False)
    return im.crop((11, 8, 29, 23)).resize((54, 45), Image.NEAREST)   # 18x15 -> x3


def card(p, kit=None, state='ready'):
    r = RC.get(p.get('rarity'), RC['COMMON']); legend = p.get('rarity') == 'LEGEND'
    im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, CW - 1, CH - 1], fill=INK + (255,)); d.rectangle([1, 1, CW - 2, CH - 2], fill=r['main'] + (255,)); d.rectangle([2, 2, CW - 3, CH - 3], fill=PANEL + (255,))
    if legend:
        d.rectangle([2, 2, CW - 3, 2], fill=(255, 250, 200, 255)); d.rectangle([2, CH - 3, CW - 3, CH - 3], fill=(255, 250, 200, 255))
        for (x, y) in ((1, 1), (CW - 2, 1), (1, CH - 2), (CW - 2, CH - 2)):
            for k in (-1, 0, 1): d.point((x + k, y), (255, 250, 200, 255)); d.point((x, y + k), (255, 250, 200, 255))
    # rarity strip: rating box, rarity name, role
    d.rectangle([3, 3, 15, 11], fill=INK + (255,)); d.rectangle([4, 4, 14, 10], fill=r['main'] + (255,))
    rt = str(p.get('rating', '')); draw_text(im, 4 + (11 - text_w(rt)) // 2 + 1, 5, rt, INK + (255,))
    rn = (p.get('rarity') or '').upper(); draw_text(im, 18, 5, rn, r['light'] + (255,))
    role = p.get('role', ''); d.rectangle([CW - 4 - text_w(role) - 3, 3, CW - 4, 11], fill=INK + (255,)); draw_text(im, CW - 4 - text_w(role) - 1, 5, role, (255, 255, 255, 255))
    # art window with the face
    ax0, ay0, ax1, ay1 = 4, 13, CW - 5, 58
    for y in range(ay0, ay1 + 1):
        t = (y - ay0) / (ay1 - ay0); base = tuple(int(r['dark'][i] * (1 - 0.5 * t) + 20 * t) for i in range(3)); d.line([(ax0, y), (ax1, y)], fill=base + (255,))
    for x in range(ax0, ax1 + 1, 2):
        for y in range(ay0 + 18, ay0 + 30):
            if (x + y) % 4 == 0: d.point((x, y), tuple(min(255, v + 16) for v in r['dark']) + (255,))
    fc = face(p, kit); im.alpha_composite(fc, (ax0 + 1, ay0 + 1)); d.rectangle([ax0 - 1, ay0 - 1, ax1 + 1, ay1 + 1], outline=INK + (255,))
    # name plate (surname on the plate; long names wrap)
    d.rectangle([4, 60, CW - 5, 73], fill=INK + (255,)); d.rectangle([5, 61, CW - 6, 72], fill=r['main'] + (255,))
    nm = (p.get('name') or '').upper()
    if text_w(nm) <= CW - 12: draw_text(im, (CW - text_w(nm)) // 2, 64, nm, INK + (255,))
    else:
        w = nm.split(' '); l1, l2 = ' '.join(w[:-1]), w[-1]
        if text_w(l1) > CW - 12: l1 = w[0][0] + '. ' + ' '.join(w[1:-1]) if len(w) > 2 else w[0][0] + '.'
        draw_text(im, (CW - text_w(l1)) // 2, 62, l1, INK + (255,)); draw_text(im, (CW - text_w(l2)) // 2, 67, l2, INK + (255,))
    # three key stats
    for ci, (k, v) in enumerate(key_stats(p)):
        x0 = 4 + ci * 19; d.rectangle([x0, 75, x0 + 17, 87], fill=INK + (255,))
        draw_text(im, x0 + 3, 76, k, (170, 176, 208, 255)); draw_text(im, x0 + 3, 82, str(v), STAT_COL + (255,))
        d.rectangle([x0 + 11, 83, x0 + 15, 85], fill=(48, 48, 70, 255)); d.rectangle([x0 + 11, 85 - int(2 * v / 100), x0 + 15, 85], fill=STAT_COL + (255,))
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
