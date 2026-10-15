"""Stadium art generated from data/stadiums.csv: backdrop (pitch with markings + boards + stands + crowd + floodlights), goals, corner flag, thumbnail, layout.json.
Pitch orientation (decided): HORIZONTAL, TV / broadcast side-on view. Own goal on the left, attack to the right. Pitch coords x 0-100 (touchline, 0 = top of the screen = the attacker's left)
and y 0-100 (own goal to opponent goal). Camera: the ground is squashed 2:1 vertically. 12 px per metre: the pitch is 1260 px long and 408 px deep; the match camera scrolls along it.
    python stadiums/stadiumlib.py [out_dir]     writes every stadium + a contact sheet
Nothing here needs Tk. The export step (tool/export_game.py) calls render_all() into godot/assets/pitches/<id>/."""
import os, sys, csv, math, json, random
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data')
S = 12.0                    # pixels per metre across the pitch
SQ = 0.5                    # ground depth squash (screen y per ground metre = S * SQ)
LEN, WID = 105.0, 68.0      # pitch in metres (a = along, 0 = own goal on the left; b = across, 0 = top touchline)
MX_L, MX_R, MX_T, MX_B = 170, 170, 200, 100
PW, PH = int(round(LEN * S)), int(round(WID * S * SQ))
CW, CH = MX_L + PW + MX_R, MX_T + PH + MX_B
APRON = 4.0                 # metres of grass outside the lines before the boards
LINE = (232, 238, 226)


def P(a, b):
    """ground metres (a along from own goal, b across from the left) -> canvas pixels"""
    return (MX_L + a * S, MX_T + b * S * SQ)


def load():
    with open(os.path.join(DATA, 'stadiums.csv'), encoding='utf-8-sig') as f:
        return [dict(r) for r in csv.DictReader(f)]


def hexrgb(h): h = h.strip().lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))
def num(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d


# ------------------------------------------------------------------------------------------------ pitch
def grass_rect():
    x0, x1 = int(MX_L - APRON * S), int(MX_L + PW + APRON * S)
    y0, y1 = int(MX_T - APRON * S * SQ), int(MX_T + PH + APRON * S * SQ)
    return x0, y0, x1, y1


def draw_grass(img, row, rng):
    x0, y0, x1, y1 = grass_rect(); ga, gb = hexrgb(row['grass_a']), hexrgb(row['grass_b'])
    yy, xx = np.mgrid[y0:y1, x0:x1]
    a = (xx - MX_L) / S; b = (yy - MX_T) / (S * SQ); band = 5.25; mow = row['mow']
    if mow == 'checker': k = (np.floor(a / band) + np.floor(b / band)) % 2
    elif mow == 'diagonal': k = np.floor((a + b) / band) % 2
    elif mow == 'rings': k = np.floor(np.hypot(a - LEN / 2, b - WID / 2) / band) % 2
    else: k = np.floor(a / band) % 2
    base = np.where(k[..., None] == 1, np.array(gb), np.array(ga)).astype(np.float32)
    n = rng.random(k.shape)
    base *= np.where(n < 0.07, 0.86, np.where(n > 0.965, 1.07, 1.0))[..., None]          # blades
    bay = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    base += ((bay[yy % 4, xx % 4] - 0.5) * 5)[..., None]                                    # ordered dither
    worn = num(row.get('worn')) / 100.0
    if worn > 0:
        mud = np.array([112, 92, 58], np.float32)
        for (pa, pb, ra, rb) in ((11, 34, 7, 10), (94, 34, 7, 10), (52.5, 34, 6, 6), (3, 34, 5, 14), (102, 34, 5, 14), (16, 34, 8, 12), (89, 34, 8, 12)):
            d = np.hypot((a - pa) / ra, (b - pb) / rb); m = np.clip(1 - d, 0, 1) ** 0.8 * worn
            m = (m > 0.18 + 0.55 * rng.random(m.shape) * (1 - m)).astype(np.float32) * np.clip(m * 1.4, 0, 0.85)
            base = base * (1 - m[..., None]) + mud * m[..., None]
    img[y0:y1, x0:x1, :3] = np.clip(base, 0, 255).astype(np.uint8); img[y0:y1, x0:x1, 3] = 255


def poly(d, pts, width=2, col=LINE):
    d.line([P(*p) for p in pts], fill=col + (255,), width=width, joint='curve')


def arc_pts(ca, cb, r, a0, a1, n=60, keep=None):
    pts = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n); p = (ca + r * math.cos(t), cb + r * math.sin(t))
        if keep is None or keep(p): pts.append(p)
    return pts


def draw_markings(img):
    d = ImageDraw.Draw(img)
    poly(d, [(0, 0), (0, WID), (LEN, WID), (LEN, 0), (0, 0)])                       # touch and goal lines
    poly(d, [(LEN / 2, 0), (LEN / 2, WID)])                                          # halfway line
    poly(d, arc_pts(LEN / 2, WID / 2, 9.15, 0, 360, 90))                             # centre circle
    for end in (0, 1):
        s = 1 if end == 0 else -1; g = 0.0 if end == 0 else LEN                       # own goal at a=0, opponent at a=LEN
        pa = g + s * 16.5; pw0, pw1 = WID / 2 - 20.16, WID / 2 + 20.16
        poly(d, [(g, pw0), (pa, pw0), (pa, pw1), (g, pw1)])                           # penalty area
        poly(d, [(g, WID / 2 - 9.16), (g + s * 5.5, WID / 2 - 9.16), (g + s * 5.5, WID / 2 + 9.16), (g, WID / 2 + 9.16)])   # goal area
        spot = g + s * 11.0
        poly(d, arc_pts(spot, WID / 2, 9.15, -90 if s == 1 else 90, 90 if s == 1 else 270, 60, keep=lambda p, s=s, pa=pa: (p[0] - pa) * s > 0.05))   # penalty arc
        for (cx, cy) in ((spot, WID / 2),):
            x, y = P(cx, cy); d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=LINE + (255,))
    x, y = P(LEN / 2, WID / 2); d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=LINE + (255,))
    for ca, cb, a0 in ((0, 0, 0), (0, WID, 90), (LEN, WID, 180), (LEN, 0, 270)):      # corner arcs
        poly(d, arc_pts(ca, cb, 1.0, a0, a0 + 90, 8), width=2)


def draw_boards(img, row, rng):
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = grass_rect(); bc = hexrgb(row['board']); alt = mix(bc, (20, 20, 30), 0.55); acc = mix(bc, (255, 255, 255), 0.5)
    x = x0
    while x < x1:                                                                         # far end: the faces of the boards
        w = int(rng.integers(26, 56)); col = [bc, alt, acc][int(rng.integers(0, 3))]
        d.rectangle([x, y0 - 12, min(x + w, x1) - 1, y0 - 1], fill=col + (255,)); d.line([(x, y0 - 12), (min(x + w, x1) - 1, y0 - 12)], fill=mix(col, (255, 255, 255), 0.35) + (255,)); x += w
    d.rectangle([x0 - 5, y0 - 12, x0 - 1, y1], fill=alt + (255,)); d.rectangle([x1, y0 - 12, x1 + 4, y1], fill=alt + (255,))          # sides
    d.rectangle([x0 - 5, y1, x1 + 4, y1 + 4], fill=mix(bc, (0, 0, 0), 0.5) + (255,))   # near end: the backs


# ------------------------------------------------------------------------------------------------ stands, crowd, lights
def seat_rows(d, box, axis, rows, row_px, row, rng, crowd_cols, seat, stand, trim, flip=False, start_dark=0.0):
    """fill a stand rectangle with rows of seats and fans. axis 'y': rows stack along y (far/near stands); 'x': along x (side stands)."""
    x0, y0, x1, y1 = box; dens = num(row['crowd']) / 100.0; cell = 6
    n = rows
    for r in range(n):
        t = r / max(1, n - 1)                                  # 0 at the pitch edge, 1 at the back
        shade = mix(seat, stand, 0.35 + 0.5 * t)
        if axis == 'y':
            ya = (y1 - (r + 1) * row_px) if not flip else (y0 + r * row_px); yb = ya + row_px - 1
            d.rectangle([x0, ya, x1, yb], fill=mix(stand, (0, 0, 0), 0.25 + 0.25 * t) + (255,))
            for cx in range(x0 + 1, x1 - cell, cell):
                if ((cx - x0) // cell) % 14 == 0: d.rectangle([cx, ya, cx + 2, yb], fill=mix(stand, (0, 0, 0), 0.5) + (255,)); continue        # gangway
                d.rectangle([cx, yb - 1, cx + cell - 2, yb], fill=shade + (255,))
                if rng.random() < dens * (0.95 - 0.35 * t):
                    body = crowd_cols[int(rng.integers(0, len(crowd_cols)))]; hx = cx + 1; hy = ya + (0 if not flip else 0)
                    d.rectangle([hx, yb - 4, hx + 3, yb - 1], fill=body + (255,)); d.rectangle([hx + 1, yb - 6, hx + 2, yb - 5], fill=(226, 178, 140, 255))
        else:
            xa = (x1 - (r + 1) * row_px) if not flip else (x0 + r * row_px); xb = xa + row_px - 1
            d.rectangle([xa, y0, xb, y1], fill=mix(stand, (0, 0, 0), 0.25 + 0.25 * t) + (255,))
            for cy in range(y0 + 1, y1 - cell, cell):
                if ((cy - y0) // cell) % 14 == 0: d.rectangle([xa, cy, xb, cy + 2], fill=mix(stand, (0, 0, 0), 0.5) + (255,)); continue
                d.rectangle([xb - 1, cy, xb, cy + cell - 2], fill=shade + (255,))
                if rng.random() < dens * (0.95 - 0.35 * t):
                    body = crowd_cols[int(rng.integers(0, len(crowd_cols)))]
                    d.rectangle([xb - 4, cy + 1, xb - 1, cy + 4], fill=body + (255,)); d.rectangle([xb - 6, cy + 2, xb - 5, cy + 3], fill=(226, 178, 140, 255))


def draw_stands(img, row, rng):
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = grass_rect(); stand = hexrgb(row['stand']); trim = hexrgb(row['stand_trim']); seat = hexrgb(row['seat'])
    cols = [hexrgb(c) for c in row['crowd_colors'].split(';') if c.strip()] or [(200, 200, 200)]
    d.rectangle([0, 0, CW, CH], fill=mix(stand, (0, 0, 0), 0.6) + (255,))
    far_h = y0 - 14; near_h = CH - (y1 + 6); side_w_l = x0 - 7; side_w_r = CW - (x1 + 6)
    seat_rows(d, (0, 0, CW - 1, far_h - 1), 'y', far_h // 7, 7, row, rng, cols, seat, stand, trim)                                  # far stand, rows rise away
    seat_rows(d, (0, far_h, side_w_l, y1 + 5), 'x', side_w_l // 7, 7, row, rng, cols, seat, stand, trim)                              # left
    seat_rows(d, (CW - side_w_r, far_h, CW - 1, y1 + 5), 'x', side_w_r // 7, 7, row, rng, cols, seat, stand, trim, flip=True)       # right
    seat_rows(d, (0, y1 + 6, CW - 1, CH - 1), 'y', near_h // 7, 7, row, rng, cols, seat, stand, trim, flip=True)                       # near
    d.rectangle([0, far_h - 3, CW, far_h + 1], fill=trim + (255,)); d.rectangle([0, y1 + 5, CW, y1 + 9], fill=trim + (255,))          # trim lines
    d.rectangle([side_w_l - 2, far_h, side_w_l + 2, y1 + 9], fill=trim + (255,)); d.rectangle([CW - side_w_r - 3, far_h, CW - side_w_r + 1, y1 + 9], fill=trim + (255,))
    if str(row.get('roof', '0')) == '1':                                                                                             # roof overhang on the far stand
        d.rectangle([0, 0, CW, 34], fill=mix(stand, (0, 0, 0), 0.55) + (255,)); d.rectangle([0, 34, CW, 40], fill=trim + (255,))
        for x in range(0, CW, 38): d.rectangle([x, 0, x + 3, 34], fill=mix(trim, (0, 0, 0), 0.4) + (255,))
    else:                                                                                                                             # hedge / sky edge for open grounds
        d.rectangle([0, 0, CW, 10], fill=mix(stand, (255, 255, 255), 0.25) + (255,))


def towers(img, row):
    if str(row.get('towers', '0')) != '1': return []
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = grass_rect(); pts = []
    for (x, y, h) in ((x0 - 30, y0 - 10, 150), (x1 + 30, y0 - 10, 150), (x0 - 30, y1 + 20, 120), (x1 + 30, y1 + 20, 120)):
        d.rectangle([x - 2, y - h, x + 1, y], fill=(58, 62, 72, 255)); d.rectangle([x - 14, y - h - 12, x + 13, y - h], fill=(40, 44, 54, 255))
        for k in range(4):
            for j in range(2): d.rectangle([x - 12 + k * 7, y - h - 10 + j * 5, x - 8 + k * 7, y - h - 7 + j * 5], fill=(255, 248, 214, 255))
        pts.append((x, y - h - 8))
    return pts


def lighting(img, row, lights):
    """time of day: tint and light pools, applied to the whole backdrop"""
    t = row.get('time', 'day'); a = img[..., :3].astype(np.float32); yy, xx = np.mgrid[0:CH, 0:CW]
    if t == 'night':
        f = np.full((CH, CW), 0.68, np.float32); pools = lights or [(CW / 2, MX_T + PH / 2)]
        for (lx, ly) in pools: f += np.clip(1 - np.hypot((xx - lx) / 760.0, (yy - ly) / 520.0), 0, 1) ** 1.3 * 0.42 * max(0.4, num(row.get('light'), 1))
        f += np.clip(1 - np.hypot((xx - CW / 2) / 620.0, (yy - (MX_T + PH / 2)) / 430.0), 0, 1) * 0.12
        a *= np.clip(f, 0.3, 1.05)[..., None] * np.array([0.86, 0.94, 1.08])
        for (lx, ly) in pools:                                                                           # glow at the lamps
            g = np.clip(1 - np.hypot(xx - lx, yy - ly) / 46.0, 0, 1) ** 2 * 190; a += g[..., None] * np.array([1.0, 0.96, 0.8])
    elif t == 'dusk':
        a *= np.array([1.06, 0.88, 0.74]) * 0.94
        g = np.clip(yy / CH, 0, 1)[..., None]; a = a * (0.92 + 0.12 * (1 - g))
        v = np.clip(np.hypot((xx - CW / 2) / (CW * 0.65), (yy - CH / 2) / (CH * 0.65)) - 0.45, 0, 1) * 0.5; a *= (1 - v)[..., None]
    img[..., :3] = np.clip(a, 0, 255).astype(np.uint8)


def render_backdrop(row, seed=1):
    rng = np.random.default_rng(abs(hash(row['id'])) % (2 ** 31) + seed) if False else np.random.default_rng(sum(ord(c) * (i + 3) for i, c in enumerate(row['id'])) + seed)
    img = np.zeros((CH, CW, 4), np.uint8); img[..., 3] = 255; im = Image.fromarray(img, 'RGBA')
    draw_stands(im, row, rng); arr = np.array(im)
    draw_grass(arr, row, rng); im = Image.fromarray(arr, 'RGBA'); draw_markings(im); draw_boards(im, row, rng); lights = towers(im, row)
    arr = np.array(im); lighting(arr, row, lights)
    return Image.fromarray(arr, 'RGBA')


# ------------------------------------------------------------------------------------------------ goals and flag
def _net(d, pts, col=(236, 240, 236), a=70, step=5):
    """a net grid over the quad pts (4 corners, in order)"""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    for k in range(0, step + 1):
        t = k / step
        d.line([(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), (x3 + (x2 - x3) * t, y3 + (y2 - y3) * t)], fill=col + (a,))
        d.line([(x0 + (x3 - x0) * t, y0 + (y3 - y0) * t), (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)], fill=col + (a,))


GW, GH, GOX, GOY = 64, 104, 54, 62         # goal image size and the origin (goal line, centre of the mouth, on the ground)
HALF = 3.66 * S * SQ                       # half the goal mouth in screen y (ground squash)
GHT = 2.44 * S                             # crossbar height
GDEP = 2.0 * S * 0.8                       # net depth along the pitch (goes outside the end line, to the left)


def _goal_pts():
    fb, nb = GOY - HALF, GOY + HALF         # far / near post base y
    gx, bx = GOX, GOX - GDEP
    return fb, nb, gx, bx


def goal_back():
    """the LEFT goal seen from the side, the layer behind the players: shadow, back net, roof, far side net, far post. The right goal is this flipped in Godot."""
    im = Image.new('RGBA', (GW, GH), (0, 0, 0, 0)); d = ImageDraw.Draw(im); fb, nb, gx, bx = _goal_pts(); W = (250, 250, 250, 255)
    d.polygon([(gx + 2, fb + 2), (gx + 2, nb + 3), (bx - 3, nb + 3), (bx - 3, fb + 2)], fill=(0, 0, 0, 38))                          # shadow on the grass
    d.polygon([(bx, fb - GHT), (bx, nb), (bx, nb - GHT), (bx, fb)], fill=(236, 240, 236, 26))
    _net(d, [(bx, fb - GHT), (bx, nb - GHT), (bx, nb), (bx, fb)], a=0)
    for k in range(0, 8):                                                                                                               # back net: a vertical plane seen edge on, drawn as a strip
        y = fb - GHT + (nb - (fb - GHT)) * k / 7; d.line([(bx - 1, y), (bx + 1, y)], fill=(236, 240, 236, 80))
    d.line([(bx, fb - GHT), (bx, nb)], fill=(236, 240, 236, 110))
    _net(d, [(gx, fb - GHT), (gx, nb - GHT), (bx, nb - GHT), (bx, fb - GHT)], a=70)                                                   # roof net
    _net(d, [(gx, fb), (gx, fb - GHT), (bx, fb - GHT), (bx, fb)], a=70)                                                               # far side net
    d.line([(bx, fb), (bx, fb - GHT)], fill=(210, 216, 210, 255)); d.line([(bx, fb - GHT), (gx, fb - GHT)], fill=(210, 216, 210, 255))
    d.rectangle([gx - 1, fb - GHT, gx, fb], fill=W)                                                                                     # far post
    return im, (GOX, GOY)


def goal_front():
    """the layer in front of the players: near side net, near post, crossbar"""
    im = Image.new('RGBA', (GW, GH), (0, 0, 0, 0)); d = ImageDraw.Draw(im); fb, nb, gx, bx = _goal_pts(); W = (250, 250, 250, 255)
    _net(d, [(gx, nb), (gx, nb - GHT), (bx, nb - GHT), (bx, nb)], a=95)
    d.line([(bx, nb), (bx, nb - GHT)], fill=(236, 240, 236, 255)); d.line([(bx, nb - GHT), (gx, nb - GHT)], fill=(236, 240, 236, 255))
    d.line([(gx - 1, fb - GHT), (gx - 1, nb - GHT)], fill=W, width=2)                                                                   # crossbar, far post to near post
    d.rectangle([gx - 1, nb - GHT, gx, nb], fill=W)                                                                                     # near post
    d.rectangle([gx - 2, nb, gx + 1, nb + 1], fill=(0, 0, 0, 70))
    return im, (GOX, GOY)


def corner_flag():
    im = Image.new('RGBA', (10, 22), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([4, 4, 5, 20], fill=(246, 246, 240, 255)); d.polygon([(6, 4), (6, 9), (0, 7)], fill=(236, 70, 50, 255)); d.rectangle([3, 20, 6, 21], fill=(0, 0, 0, 70))
    return im, (5, 21)


# ------------------------------------------------------------------------------------------------ output
def layout(row):
    go = goal_back()[1]; fl = corner_flag()[1]
    return dict(id=row['id'], name=row['name'], time=row['time'], px_per_m=S, squash=SQ, pitch_m=[LEN, WID], canvas=[CW, CH], pitch_origin=[MX_L, MX_T], pitch_size=[PW, PH],
                orientation='horizontal TV view (own goal on the left)', goal_left=dict(pos=list(P(0, WID / 2)), origin=list(go)), goal_right=dict(pos=list(P(LEN, WID / 2)), origin=list(go), flip=True),
                flag=dict(origin=list(fl), corners=[list(P(0, 0)), list(P(0, WID)), list(P(LEN, 0)), list(P(LEN, WID))]), capacity=int(num(row.get('capacity'))))


def render_all(out_dir, log=print, tick=None):
    rows = load(); os.makedirs(out_dir, exist_ok=True)
    for i, row in enumerate(rows):
        d = os.path.join(out_dir, row['id']); os.makedirs(d, exist_ok=True); bd = render_backdrop(row)
        bd.save(os.path.join(d, 'backdrop.png')); bd.resize((CW // 6, CH // 6), Image.NEAREST).save(os.path.join(d, 'thumb.png'))
        goal_back()[0].save(os.path.join(d, 'goal_back.png')); goal_front()[0].save(os.path.join(d, 'goal_front.png')); corner_flag()[0].save(os.path.join(d, 'corner_flag.png'))
        json.dump(layout(row), open(os.path.join(d, 'layout.json'), 'w'), indent=1)
        log(f"  {row['id']} {row['name']}: {CW}x{CH}")
        if tick: tick(i + 1, len(rows))
    json.dump([dict(id=r['id'], name=r['name'], time=r['time'], capacity=int(num(r.get('capacity')))) for r in rows], open(os.path.join(out_dir, 'stadiums.json'), 'w'), indent=1)
    return len(rows)


def check(rows):
    out = []; ids = set()
    for r in rows:
        if r['id'] in ids: out.append(('error', r['id'], 'duplicate id'))
        ids.add(r['id'])
        for c in ('grass_a', 'grass_b', 'stand', 'stand_trim', 'seat', 'board'):
            try: hexrgb(r[c])
            except Exception: out.append(('error', r['id'], f'{c} must be #rrggbb'))
        if r.get('time') not in ('day', 'dusk', 'night'): out.append(('error', r['id'], 'time must be day, dusk or night'))
        if r.get('mow') not in ('stripes', 'checker', 'diagonal', 'rings'): out.append(('error', r['id'], 'mow must be stripes, checker, diagonal or rings'))
    return out


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'export', 'stadiums')
    n = render_all(out); sheet = Image.new('RGB', (CW // 2 * n + 10 * (n + 1), CH // 2 + 20), (20, 20, 28))
    for i, r in enumerate(load()): sheet.paste(Image.open(os.path.join(out, r['id'], 'backdrop.png')).convert('RGB').resize((CW // 2, CH // 2), Image.NEAREST), (10 + i * (CW // 2 + 10), 10))
    sheet.save(os.path.join(out, 'sheet.png')); print('wrote', n, 'stadiums to', out)
