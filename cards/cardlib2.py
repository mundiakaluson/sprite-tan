import sys, os, math, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
from emblem import *
from emblem import W_, H_
import emblem as E
from cardlib import G, draw_text, text_w, CAT, INK as INK_, PANEL, icon, glow

CWD, CHD = 64, 90
def fit_lines(txt, width=13, maxl=3):
    lines = textwrap.wrap(txt.upper(), width)
    return lines[:maxl]

def card_old(c, art, state='ready', t=0.0):
    cat = c['cat']; pal = CAT[cat]; titan = cat == 'TITAN'
    im = Image.new('RGBA', (CWD, CHD), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, CWD - 1, CHD - 1], fill=INK_ + (255,)); d.rectangle([1, 1, CWD - 2, CHD - 2], fill=pal['main'] + (255,))
    d.rectangle([2, 2, CWD - 3, CHD - 3], fill=(pal['dark'] if titan else PANEL) + (255,))
    if titan:
        d.rectangle([2, 2, CWD - 3, 2], fill=(255, 120, 220, 255)); d.rectangle([2, CHD - 3, CWD - 3, CHD - 3], fill=(255, 120, 220, 255))
        for (x, y) in ((1, 1), (CWD - 2, 1), (1, CHD - 2), (CWD - 2, CHD - 2)):
            for k in (-1, 0, 1): d.point((x + k, y), (255, 120, 220, 255)); d.point((x, y + k), (255, 120, 220, 255))
    d.rectangle([3, 3, 11, 11], fill=INK_ + (255,)); d.rectangle([4, 4, 10, 10], fill=(70, 80, 120, 255))
    draw_text(im, 6, 5, str(c['slots']), (255, 255, 255, 255))
    draw_text(im, 15, 5, cat, pal['light'] + (255,)); icon(d, CWD - 12, 3, cat, pal['light'] + (255,))
    # art window
    ax0, ay0, ax1, ay1 = 4, 13, CWD - 5, 58
    for y in range(ay0, ay1 + 1):
        t_ = (y - ay0) / (ay1 - ay0)
        base = tuple(int(pal['dark'][i] * (1 - 0.55 * t_) + 18 * t_) for i in range(3)); d.line([(ax0, y), (ax1, y)], fill=base + (255,))
    for x in range(ax0, ax1 + 1, 2):
        for y in range(ay0 + 14, ay0 + 26):
            if (x + y) % 4 == 0: d.point((x, y), tuple(min(255, v + 16) for v in pal['dark']) + (255,))
    im.alpha_composite(art, (ax0, ay0 + 4)); d.rectangle([ax0 - 1, ay0 - 1, ax1 + 1, ay1 + 1], outline=INK_ + (255,))
    # name plate
    d.rectangle([4, 60, CWD - 5, 73], fill=INK_ + (255,)); d.rectangle([5, 61, CWD - 6, 72], fill=pal['main'] + (255,))
    nm = c['name'].upper()
    if text_w(nm) <= CWD - 12: draw_text(im, (CWD - text_w(nm)) // 2, 64, nm, INK_ + (255,))
    else:
        w = nm.split(' '); mid = max(1, len(w) // 2); l1, l2 = ' '.join(w[:mid]), ' '.join(w[mid:])
        draw_text(im, (CWD - text_w(l1)) // 2, 62, l1, INK_ + (255,)); draw_text(im, (CWD - text_w(l2)) // 2, 67, l2, INK_ + (255,))
    cells = [(f"{c['succ']}%", c['succ'], (96, 220, 120)), (f"R{c['risk']}", c['risk'], (236, 84, 76)), (f"{c['cd']}S", min(100, c['cd'] * 100 // 60), (110, 170, 250))]
    for ci, (lab, val, col) in enumerate(cells):
        x0 = 4 + ci * 19
        d.rectangle([x0, 75, x0 + 17, 87], fill=INK_ + (255,)); draw_text(im, x0 + 3, 77, lab, col + (255,))
        d.rectangle([x0 + 3, 84, x0 + 14, 85], fill=(48, 48, 70, 255)); d.rectangle([x0 + 3, 84, x0 + 3 + int(11 * val / 100), 85], fill=col + (255,))
    arr = np.array(im)
    if state == 'cooldown':
        arr[..., :3] = (arr[..., :3] * 0.45).astype(np.uint8); im = Image.fromarray(arr, 'RGBA').copy(); _stopwatch(im, c, t)
    elif state == 'unavailable':
        arr[..., :3] = (arr[..., :3] * 0.3).astype(np.uint8); im = Image.fromarray(arr, 'RGBA')
    return im

RC = dict(COMMON=dict(main=(150, 156, 176), dark=(44, 48, 66), light=(214, 218, 232)), UNCOMMON=dict(main=(76, 184, 106), dark=(22, 64, 44), light=(150, 235, 170)),
          RARE=dict(main=(74, 144, 226), dark=(22, 44, 96), light=(150, 200, 255)), EPIC=dict(main=(168, 95, 216), dark=(52, 24, 84), light=(224, 170, 255)),
          LEGEND=dict(main=(240, 176, 48), dark=(84, 52, 12), light=(255, 236, 150)))


def _mix(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _t2(im, x, y, s, col, k=2):
    t = Image.new('RGBA', (text_w(s) + 2, 7), (0, 0, 0, 0)); draw_text(t, 0, 0, s, col); im.alpha_composite(t.resize((t.width * k, t.height * k), Image.NEAREST), (x, y))


def _foil():
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tool')
    if tool not in sys.path: sys.path.insert(0, tool)
    import foil
    return foil


def card(c, art, state='ready', t=0.0):
    """Skill card in the player-card language: dark field with a glow in the category colour, a thin frame in the RARITY colour, big slot number
    top left with the category under it, rarity top right, plain name, three stats with no boxes. Titan cards get the galaxy foil."""
    cat = c['cat']; pal = CAT[cat]; titan = cat == 'TITAN'; r = RC.get(c.get('rarity'), RC['COMMON']); legend = c.get('rarity') == 'LEGEND'
    base = (12, 13, 20); cx, cy = 32, 36
    if titan:
        foil = _foil(); im = Image.fromarray(foil.background('galaxy', 0.9), 'RGB').convert('RGBA'); px = im.load()
        a_ = np.array(im).astype(float); a_[..., :3] *= 0.8; im = Image.fromarray(a_.astype(np.uint8), 'RGBA').copy(); px = im.load()
    else:
        im = Image.new('RGBA', (CWD, CHD), (0, 0, 0, 255)); px = im.load()
        for y in range(CHD):
            for x in range(CWD):
                k = y / (CHD - 1); col = _mix(_mix(pal['dark'], base, 0.6), base, k); dd = math.hypot((x - cx) * 0.9, y - cy)
                if dd < 30: col = _mix(col, pal['main'], 0.34 * (1 - dd / 30) ** 1.5)
                if (x - y // 2) % 9 == 0 and 14 < y < 60: col = _mix(col, pal['light'], 0.05)
                px[x, y] = col + (255,)
    for y in range(52, 61):                                                                         # settle the bottom into the dark
        k = (y - 52) / 9
        for x in range(CWD): px[x, y] = _mix(px[x, y][:3], tuple(int(v * 0.3) for v in px[x, y][:3]) if titan else _mix(pal['dark'], base, 0.8), min(1, k * k * 1.1)) + (255,)
    for y in range(61, CHD):
        if not titan:
            for x in range(CWD): px[x, y] = _mix(_mix(pal['dark'], base, 0.8), base, (y - 61) / 29) + (255,)
    im.alpha_composite(art, (4, 19)); d = ImageDraw.Draw(im)
    edge = r['light'] if legend else r['main']
    for x in range(2, CWD - 2): d.point((x, 0), edge + (255,)); d.point((x, CHD - 1), edge + (255,))
    for y in range(2, CHD - 2): d.point((0, y), edge + (255,)); d.point((CWD - 1, y), edge + (255,))
    for (x, y) in ((1, 1), (CWD - 2, 1), (1, CHD - 2), (CWD - 2, CHD - 2)): d.point((x, y), edge + (255,))
    for (x, y) in ((0, 0), (CWD - 1, 0), (0, CHD - 1), (CWD - 1, CHD - 1)): d.point((x, y), (0, 0, 0, 0))
    if titan:
        foil = _foil(); per = [(x, 0) for x in range(2, CWD - 2)] + [(CWD - 1, y) for y in range(2, CHD - 2)] + [(x, CHD - 1) for x in range(CWD - 3, 1, -1)] + [(0, y) for y in range(CHD - 3, 1, -1)]
        for n, (x, y) in enumerate(per):
            col = foil.edge_colour('galaxy', n / len(per) * 2); d.point((x, y), col + (255,))
            ix = 2 if x == 0 else CWD - 3 if x == CWD - 1 else x; iy = 2 if y == 0 else CHD - 3 if y == CHD - 1 else y; d.point((ix, iy), tuple(int(v * 0.55) for v in col) + (255,))
        for (x, y) in ((2, 2), (CWD - 3, 2), (2, CHD - 3), (CWD - 3, CHD - 3)):
            for k in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): d.point((x + k[0], y + k[1]), (255, 255, 255, 255))
    _t2(im, 5, 5, str(c['slots']), (255, 255, 255, 255))                                            # slot number big, category under it
    draw_text(im, 5, 18, cat, pal['light'] + (255,)); d.line([(5, 25), (5 + max(text_w(cat), 10), 25)], fill=pal['main'] + (255,))
    rn = (c.get('rarity') or '').upper(); draw_text(im, CWD - 5 - text_w(rn), 5, rn, r['light'] + (255,))
    nm = c['name'].upper()
    if text_w(nm) <= CWD - 14:
        ww = text_w(nm); draw_text(im, (CWD - ww) // 2, 63, nm, (255, 255, 255, 255))
        d.line([(5, 66), (CWD // 2 - ww // 2 - 3, 66)], fill=r['dark'] + (255,)); d.line([(CWD // 2 + ww // 2 + 3, 66), (CWD - 6, 66)], fill=r['dark'] + (255,))
        d.line([(CWD // 2 - 6, 70), (CWD // 2 + 5, 70)], fill=edge + (255,))
    else:
        w = nm.split(' '); mid = max(1, len(w) // 2); l1, l2 = ' '.join(w[:mid]), ' '.join(w[mid:])
        draw_text(im, (CWD - text_w(l1)) // 2, 60, l1, (255, 255, 255, 255)); draw_text(im, (CWD - text_w(l2)) // 2, 66, l2, (255, 255, 255, 255))
        d.line([(CWD // 2 - 6, 72), (CWD // 2 + 5, 72)], fill=edge + (255,))
    cells = [('HIT', f"{c['succ']}%", c['succ'], (110, 214, 140)), ('RISK', str(c['risk']), min(100, c['risk'] * 3), (236, 96, 88)), ('CD', f"{c['cd']}S", min(100, c['cd'] * 100 // 60), (120, 176, 250))]
    for ci, (lab, val, pc, col) in enumerate(cells):
        x0 = 4 + ci * 19; cxm = x0 + 9
        draw_text(im, cxm - text_w(lab) // 2, 76, lab, (140, 146, 176, 255)); draw_text(im, cxm - text_w(val) // 2, 82, val, (255, 255, 255, 255))
        if ci: d.line([(x0 - 1, 76), (x0 - 1, 86)], fill=r['dark'] + (255,))
        d.line([(x0 + 3, 87), (x0 + 3 + int(12 * pc / 100), 87)], fill=col + (255,))
    arr = np.array(im)
    if state == 'cooldown':
        arr[..., :3] = (arr[..., :3] * 0.45).astype(np.uint8); im = Image.fromarray(arr, 'RGBA').copy(); _stopwatch(im, c, t)
    elif state == 'unavailable':
        arr[..., :3] = (arr[..., :3] * 0.3).astype(np.uint8); im = Image.fromarray(arr, 'RGBA')
    return im


def _stopwatch(im, c, t, cx=32, cy=37, R=14):
    """cooldown overlay: a stopwatch in the art window. t = fraction of the cooldown already served (0 just used, 1 ready).
    The lit wedge is the time still to go; the number inside is the seconds left."""
    left = max(0.0, 1.0 - t); secs = int(math.ceil(c['cd'] * left - 1e-9)); px = im.load()
    ring, face, wedge, ink = (226, 232, 250, 255), (12, 14, 30, 255), (44, 92, 168, 255), INK_ + (255,)
    for y in range(cy - R - 2, cy + R + 3):
        for x in range(cx - R - 2, cx + R + 3):
            dx, dy = x - cx + 0.0, y - cy + 0.0; r = math.hypot(dx, dy)
            if r > R + 1.2: continue
            if r > R: px[x, y] = ink
            elif r > R - 2: px[x, y] = ring
            else:
                ang = (math.atan2(dx, -dy)) % (2 * math.pi)
                px[x, y] = wedge if ang <= 2 * math.pi * left else face
    for k in range(4):                                         # ticks at 12, 3, 6, 9
        a = k * math.pi / 2; x, y = cx + round(math.sin(a) * (R - 3)), cy - round(math.cos(a) * (R - 3)); px[x, y] = ring
    if 0 < left < 1:                                           # the hand
        a = 2 * math.pi * left
        for i in range(8, R - 2):
            x, y = cx + round(math.sin(a) * i), cy - round(math.cos(a) * i); px[x, y] = (255, 214, 90, 255)
    d = ImageDraw.Draw(im)
    d.rectangle([cx - 3, cy - R - 5, cx + 3, cy - R - 2], fill=ink); d.rectangle([cx - 2, cy - R - 4, cx + 2, cy - R - 3], fill=ring)       # crown
    d.rectangle([cx - 1, cy - R - 2, cx + 1, cy - R - 1], fill=ring)
    for (x, y) in ((cx + R - 3, cy - R + 3), (cx + R - 2, cy - R + 4)): d.point((x, y), ring)                                               # side button
    s = str(secs); t_ = Image.new('RGBA', (text_w(s) + 1, 6), (0, 0, 0, 0)); draw_text(t_, 0, 0, s, (255, 255, 255, 255)); t2 = t_.resize((t_.width * 2, t_.height * 2), Image.NEAREST)
    im.alpha_composite(t2, (cx - (text_w(s) * 2) // 2, cy - 5))


# ------------------------------------------------------------------ emblem recipes
P_ = CAT
def R_curve(pal, p, rot=0.4, spark=True, bx=None):
    a = new(); trail(a, bez(*p), pal); end = p[3]; a = ball(a, end[0], end[1], 6, rot=rot)
    if spark: d = ImageDraw.Draw(a); sparkle(d, min(53, end[0] + 6), max(3, end[1] - 7), (255, 240, 160, 255)); sparkle(d, 12, 31, (255, 240, 160, 255), 1)
    return a
def R_straight(pal, y=19, n=5, length=20, rot=0.2, r=6, bx=44):
    a = new(); speed_lines(a, bx, y, pal, (1, 0), n=n, length=length, spread=n * 4, seed=2); a = ball(a, bx, y, r, rot=rot); return a
def R_arc(pal, p, bt=0.62, dashed=True, ground_y=34):
    a = new(); pts = bez(*p, n=30); dashed_arc(a, pts, pal); x, y = pts[int(bt * 30)]; shadow(a, x, ground_y, 6); a = ball(a, x, y, 6, rot=0.9); return a
def R_goal_curve(pal, side='right', curve=True):
    a = new(); goalframe(a, 36, 4, 52, 20) if side == 'right' else goalframe(a, 4, 4, 20, 20)
    if side == 'right': p = ((5, 34), (14, 14), (30, 36), (47, 14)) if curve else ((8, 34), (20, 28), (32, 22), (47, 14))
    else: p = ((50, 34), (40, 14), (26, 36), (9, 14)) if curve else ((46, 34), (34, 28), (22, 22), (9, 14))
    trail(a, bez(*p), pal); end = p[3]; a = ball(a, end[0], end[1], 5, rot=0.4); return a
def R_ghost(pal):
    a = new(); d = ImageDraw.Draw(a)
    d.ellipse([12, 10, 28, 26], outline=pal['light'] + (160,)); 
    for k in range(0, 360, 40): d.point((int(20 + 8 * math.cos(math.radians(k))), int(18 + 8 * math.sin(math.radians(k)))), pal['light'] + (230,))
    a = ball(a, 36, 19, 7, rot=0.7); d = ImageDraw.Draw(a)
    d.line([(14, 19), (26, 19)], fill=pal['light'] + (255,)); d.polygon([(27, 19), (23, 16), (23, 22)], fill=pal['light'] + (255,)); return a
def R_wall(pal):
    a = new(); d = ImageDraw.Draw(a)
    for i, x in enumerate((13, 19, 25)):
        d.rectangle([x, 20, x + 4, 32], fill=(150, 158, 190, 255), outline=INK); d.ellipse([x, 17, x + 4, 21], fill=(200, 170, 140, 255), outline=INK)
    goalframe(a, 40, 6, 53, 22); trail(a, bez((4, 34), (8, 4), (34, -4), (46, 14)), pal); a = ball(a, 46, 14, 5, rot=0.5); return a
def R_impact(pal, bx=28, by=22, sz=12, flat=False, boom=True, rot=0.5, trailing=False):
    a = new()
    if boom: star(a, bx, by, sz * 0.55, sz, (255, 232, 130, 255), pts=9, rot=0.3, inner=(255, 140, 70, 255))
    if trailing: speed_lines(a, bx, by, pal, (1, 0), n=4, length=16, spread=16, seed=5)
    a = ball(a, bx, by, 6, rot=rot); return a
def R_gravity(pal):
    a = new(); star(a, 28, 22, 9, 19, (255, 206, 70, 255), pts=10, rot=0.2, inner=(255, 120, 60, 255)); speed_lines(a, 28, 22, pal, (1, 0), n=5, length=22, spread=26, seed=3)
    a = ball(a, 28, 22, 9, sx=1.7, sy=0.75, rot=0.3); rings(a, 28, 32, pal, 3, 4); return a
def R_flame(pal):
    a = new(); flame(a, 40, 19, 28); a = ball(a, 44, 19, 6, rot=0.2); d = ImageDraw.Draw(a); sparkle(d, 10, 8, (255, 240, 160, 255), 1); sparkle(d, 20, 30, (255, 240, 160, 255), 1); return a
def R_knuckle(pal):
    a = new(); d = ImageDraw.Draw(a)
    for i, (x, y) in enumerate(((10, 12), (18, 25), (26, 14), (34, 26))):
        d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=pal['light'] + (60 + i * 40,))
    pts = [(8, 12), (16, 26), (24, 13), (32, 27), (40, 17)]; d.line(pts, fill=pal['light'] + (200,)); a = ball(a, 46, 19, 6, rot=0.9); return a
def R_bounce(pal):
    a = new(); ground(a, 33, pal); rings(a, 22, 33, pal, 3, 3); a = ball(a, 33, 24, 6, rot=1.2); d = ImageDraw.Draw(a)
    star(a, 40, 12, 2, 5, (255, 232, 130, 255), pts=6); return a
def R_kink(pal):
    a = new(); p1 = bez((4, 6), (10, 8), (18, 12), (26, 14), 14); p2 = bez((26, 14), (32, 18), (40, 24), (47, 29), 14); trail(a, p1 + p2, pal); a = ball(a, 47, 29, 5, rot=0.4); return a
def R_cross(pal):
    a = new(); trail(a, bez((4, 8), (20, 8), (32, 28), (46, 30)), pal, 0.6, 2.4); trail(a, bez((4, 30), (20, 30), (32, 10), (46, 8)), pal, 0.6, 2.4); a = ball(a, 46, 8, 6, rot=0.8); return a
def R_two_arrows(pal):
    a = new(); d = ImageDraw.Draw(a); col = pal['light'] + (255,)
    d.line([(2, 19), (14, 19)], fill=col, width=2); d.polygon([(18, 19), (13, 15), (13, 23)], fill=col)
    d.line([(34, 19), (50, 19)], fill=col, width=2); d.polygon([(54, 19), (49, 15), (49, 23)], fill=col)
    a = ball(a, 26, 19, 7, rot=0.5); return a
def R_aura(pal):
    a = new(); d = ImageDraw.Draw(a)
    for i, r in enumerate((16, 12, 8)): d.ellipse([28 - r, 19 - r, 28 + r, 19 + r], outline=pal['light'] + (90 + i * 50,))
    a = ball(a, 28, 19, 7, rot=0.3); return a
def R_loop(pal):
    a = new(); trail(a, bez((6, 10), (50, 4), (8, 36), (44, 24)), pal); a = ball(a, 44, 24, 6, rot=0.2); return a
def R_bolt(pal):
    a = new(); a = ball(a, 24, 21, 7, rot=0.8); bolt(a, 40, 15, 1.4); speed_lines(a, 18, 21, pal, (1, 0), n=3, length=10, spread=10, seed=7); return a
def R_arrow_up(pal):
    a = new(); trail(a, [(28, 36 - i) for i in range(26)], pal, 1.2, 3.6); a = ball(a, 28, 10, 6, rot=0.6); star(a, 28, 4, 1, 4, (255, 232, 130, 255), pts=6); return a
def R_dive(pal):
    a = new(); trail(a, bez((3, 3), (14, 6), (28, 18), (44, 30)), pal, 1.2, 4.0); a = ball(a, 44, 30, 6, rot=0.9); return a
def R_toe(pal):
    a = new(); star(a, 14, 28, 3, 7, (255, 232, 130, 255), pts=7); a = ball(a, 30, 22, 6, rot=0.2); speed_lines(a, 36, 22, pal, (1, 0), n=3, length=8, spread=8, seed=2); return a
def R_low(pal):
    a = new(); ground(a, 33, pal); trail(a, [(6 + i * 1.7, 31 - (i * 0.02)) for i in range(24)], pal, 0.6, 2.2); a = ball(a, 47, 29, 5, rot=0.9); return a

EMB = {
 'SH01': lambda p: R_goal_curve(p, 'right', False), 'SH02': lambda p: R_straight(p), 'SH03': lambda p: R_curve(p, ((5, 33), (12, 4), (32, 2), (44, 13))),
 'SH04': lambda p: R_curve(p, ((6, 8), (22, 36), (34, 0), (48, 22)), rot=0.2), 'SH05': lambda p: R_arc(p, ((6, 30), (14, 0), (40, 0), (50, 30)), 0.6),
 'SH06': R_knuckle, 'SH07': lambda p: R_gravity_lite(p) if False else R_impact(p, 30, 20, 14, trailing=True), 'SH08': lambda p: R_impact(p, 28, 20, 13),
 'SH09': R_bounce, 'SH10': R_dive, 'SH11': R_kink, 'SH12': R_arrow_up, 'SH13': R_cross, 'SH14': R_toe, 'SH15': lambda p: R_curve(p, ((6, 30), (30, 38), (42, 22), (47, 9)), rot=0.5),
 'SH16': R_low, 'SH17': lambda p: R_goal_curve(p, 'right', True), 'SH18': lambda p: R_goal_curve(p, 'left', False), 'SH19': lambda p: R_arc(p, ((5, 30), (16, -4), (34, -6), (47, 32)), 0.7),
 'SH20': R_wall, 'SH21': lambda p: R_arc(p, ((8, 30), (20, 12), (34, 12), (46, 30)), 0.55), 'SH22': R_flame, 'SH23': R_bolt, 'SH24': R_two_arrows,
 'SH25': lambda p: R_curve(p, ((6, 6), (14, 34), (30, 34), (48, 12)), rot=0.3), 'SH26': R_ghost, 'SH27': lambda p: R_goal_curve(p, 'left', True),
 'SH28': R_aura, 'SH29': lambda p: R_arc(p, ((6, 28), (18, -2), (38, -2), (48, 28)), 0.5), 'SH30': R_loop,
}

def R_wings(pal):
    a = new(); a.alpha_composite(wings(a, 28, 21, pal)); a = ball(a, 28, 21, 7, rot=1.0); d = ImageDraw.Draw(a); sparkle(d, 8, 6, (255, 240, 160, 255), 1); sparkle(d, 49, 30, (255, 240, 160, 255), 1); return a
def R_flex(pal):
    a = flex_arm(); d = ImageDraw.Draw(a)
    for x, y in ((10, 10), (47, 14), (46, 29)): sparkle(d, x, y, (255, 240, 160, 255), 1)
    for k in range(4): d.line([(44 + k * 2, 3), (52, 1 + k * 3)], fill=(255, 230, 120, 255))
    return a
def R_shield(pal):
    a = new(); m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.polygon([(18, 4), (38, 4), (38, 20), (28, 34), (18, 20)], fill=pal['main'] + (255,))
    d.polygon([(21, 7), (35, 7), (35, 19), (28, 29), (21, 19)], fill=pal['dark'] + (255,)); d.line([(28, 7), (28, 28)], fill=pal['light'] + (255,)); d.line([(21, 15), (35, 15)], fill=pal['light'] + (255,))
    a.alpha_composite(outline(m)); a = ball(a, 46, 12, 5, rot=0.4); d = ImageDraw.Draw(a); star(a, 40, 14, 2, 5, (255, 232, 130, 255), pts=6); return a
def R_glove(pal):
    a = new(); m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m); WH = (240, 240, 250, 255); GR = (150, 232, 120, 255)
    d.rectangle([16, 18, 38, 34], fill=WH); d.rectangle([16, 28, 38, 31], fill=GR)
    for i, x in enumerate((16, 21, 26, 31)): d.rectangle([x, 6 - (i in (1, 2)) * 2, x + 3, 19], fill=WH)
    d.polygon([(38, 22), (46, 14), (49, 17), (40, 28)], fill=WH)
    return outline(m)
EXTRA = {'wings': R_wings, 'flex': R_flex, 'shield': R_shield, 'glove': R_glove, 'gravity': R_gravity}


def popup(c, w=148):
    """tooltip shown on hover/hold: description + numbers, with a pointer tail at the bottom centre"""
    pal = CAT[c['cat']]; lines = textwrap.wrap(c['desc'].upper(), (w - 12) // 4)[:4]
    h = 8 + 7 + 8 + 3 * 8 + 4 + len(lines) * 7 + 8
    im = Image.new('RGBA', (w, h + 6), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=INK_ + (255,)); d.rectangle([1, 1, w - 2, h - 2], fill=pal['main'] + (255,)); d.rectangle([2, 2, w - 3, h - 3], fill=PANEL + (255,))
    d.polygon([(w // 2 - 4, h - 1), (w // 2 + 4, h - 1), (w // 2, h + 5)], fill=pal['main'] + (255,))
    draw_text(im, 6, 6, c['name'].upper(), pal['light'] + (255,))
    draw_text(im, 6, 13, c['cat'] + '  ' + str(c['slots']) + (' SLOTS' if c['slots'] > 1 else ' SLOT'), (150, 156, 190, 255))
    y = 22
    for lab, v, col, pct in (('SUCCESS', f"{c['succ']}%", (96, 220, 120), c['succ']), ('RISK', f"{c['risk']}%", (236, 84, 76), c['risk']), ('COOLDOWN', f"{c['cd']}S", (110, 170, 250), min(100, c['cd'] * 100 // 60))):
        draw_text(im, 6, y, lab, (170, 176, 208, 255)); draw_text(im, 50, y, v, col + (255,))
        d.rectangle([72, y + 1, w - 8, y + 3], fill=(48, 48, 70, 255)); d.rectangle([72, y + 1, 72 + int((w - 80) * pct / 100), y + 3], fill=col + (255,)); y += 8
    y += 3
    for ln in lines: draw_text(im, 6, y, ln, (235, 238, 250, 255)); y += 7
    return im
