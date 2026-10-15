"""Pack opening scenes. Stateless: frame(scene, i) -> 480x270 image. One pull is rolled from data/pack_odds.csv (guarantee honoured), then:
  float in + tilt shimmer -> charge (rarity glow leaks out) -> tear the top off -> cards burst out and stack -> reveal ONE AT A TIME (tension, flip, rarity burst)
  -> cards collect along the bottom -> summary row.  Epic and legend pulls get longer, bigger reveals.
Run:  python packs/opening.py [Pack Name] [seed] [best]   -> export/packs/open_<pack>.gif (+ contact sheet);  python packs/opening.py tilt -> export/packs/tilt.gif"""
import os, sys, math, random, csv
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
for p in ('packs', 'tool', 'cards', 'sprites', 'titan'):
    sys.path.insert(0, os.path.join(ROOT, p))
import design2 as D
import foil
import engine as E
import playercard as PC
import tables
from playercard import RC

VW, VH = 480, 270
RARS = ['COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGEND']
ACC = {'COMMON': (190, 196, 215), 'UNCOMMON': (90, 220, 130), 'RARE': (90, 200, 255), 'EPIC': (210, 100, 255), 'LEGEND': (255, 210, 90)}
TENS = {'COMMON': 8, 'UNCOMMON': 8, 'RARE': 14, 'EPIC': 24, 'LEGEND': 34}
HOLD = {'COMMON': 8, 'UNCOMMON': 9, 'RARE': 12, 'EPIC': 18, 'LEGEND': 28}
CX, CY = 240, 128


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def out_back(t): t = clamp(t); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


# ---------------------------------------------------------------------------------------------------------------- the pull
def roll(pack, seed=1, best=None):
    od = D.odds()[pack]; rng = random.Random(seed)
    P, C = int(od['player_items']), int(od['card_items']); w = [float(od[k.lower()]) for k in RARS]
    players = tables.table('players').rows; cards = [r for r in tables.table('cards').rows if not r['id'].startswith('TT')] + [r for r in tables.table('cards').rows if r['id'].startswith('TT')]
    for _ in range(200):
        items = [('player', rng.choices(RARS, w)[0]) for _ in range(P)] + [('card', rng.choices(RARS, w)[0]) for _ in range(C)]
        gm = (od.get('guarantee_min') or '').strip().upper()
        if gm and max(RARS.index(r) for _, r in items) < RARS.index(gm): k = rng.randrange(len(items)); items[k] = (items[k][0], gm)
        if best is None or max(RARS.index(r) for _, r in items) >= RARS.index(best): break
        rng = random.Random(rng.random())
    pull = []
    for kind, rar in items:
        pool = [r for r in (players if kind == 'player' else cards) if r['rarity'] == rar] or [r for r in (players if kind == 'player' else cards)]
        pull.append(dict(kind=kind, rarity=rar, row=rng.choice(pool)))
    pull.sort(key=lambda x: RARS.index(x['rarity']))                                            # best card last
    return pull


def face(item, t=1.0):
    r = item['row']
    if item['kind'] == 'player': return PC.card(r, special=True if item['rarity'] in ('RARE', 'EPIC', 'LEGEND') else None, t=t)
    return E.card_face(r['id'], 1)


def card_back(rar):
    c = RC[rar]; im = Image.new('RGBA', (64, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 89], fill=(12, 13, 20, 255)); d.rectangle([1, 1, 62, 88], outline=c['main'] + (255,)); d.rectangle([3, 3, 60, 86], outline=c['dark'] + (255,))
    for y in range(5, 85):
        for x in range(5, 59):
            if (x + y) % 10 == 0 or (x - y) % 10 == 0: d.point((x, y), tuple(int(v * 0.5) for v in c['dark']) + (255,))
    d.polygon([(32, 28), (44, 45), (32, 62), (20, 45)], outline=c['main'] + (255,)); d.polygon([(32, 34), (39, 45), (32, 56), (25, 45)], fill=c['dark'] + (255,))
    for (x, y) in ((5, 5), (58, 5), (5, 84), (58, 84)): d.point((x, y), c['light'] + (255,))
    for (x, y) in ((0, 0), (63, 0), (0, 89), (63, 89)): im.putpixel((x, y), (0, 0, 0, 0))
    return im


# ---------------------------------------------------------------------------------------------------------------- drawing helpers
def coeffs(dst, w, h):
    src = [(0, 0), (w, 0), (w, h), (0, h)]; A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def put(canvas, img, cx, cy, scale=1.0, wf=1.0, k=0.0, alpha=1.0, rot=0.0):
    """draw img centred on (cx, cy): scale, horizontal squash wf (turning), perspective k (+ = right side further away), rotation in radians"""
    if wf < 0.03 or alpha <= 0.01: return
    w, h = img.size; s = img.resize((max(1, int(round(w * scale))), max(1, int(round(h * scale)))), Image.NEAREST); sw, sh = s.size
    hw, hh = sw * wf / 2, sh / 2; q = [(-hw, -hh * (1 + k)), (hw, -hh * (1 - k)), (hw, hh * (1 - k)), (-hw, hh * (1 + k))]; c, sn = math.cos(rot), math.sin(rot)
    dst = [(cx + x * c - y * sn, cy + x * sn + y * c) for x, y in q]
    t = s.transform((VW, VH), Image.PERSPECTIVE, coeffs(dst, sw, sh), Image.NEAREST)
    # keep the screen position: the transform maps output -> source, so the source sits at the origin of its own coordinates; our dst quad is already absolute
    if alpha < 1: a = np.array(t); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); t = Image.fromarray(a, 'RGBA')
    canvas.alpha_composite(t)


def glow(arr, cx, cy, rx, ry, col, a):
    if a <= 0.01: return
    Y, X = np.mgrid[0:VH, 0:VW]; d = np.sqrt(((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2); g = np.clip(1 - d, 0, 1) ** 1.7 * a
    arr += g[..., None] * np.array(col, float)


BG = None


def background(dim=0.0):
    global BG
    if BG is None:
        Y, X = np.mgrid[0:VH, 0:VW]; d = np.hypot((X - VW / 2) / (VW * 0.62), (Y - VH / 2) / (VH * 0.75)); base = np.array([20, 16, 38], float)
        BG = np.clip(1 - d, 0, 1)[..., None] ** 1.3 * base * 1.2 + np.array([6, 5, 12], float)
    return BG.copy() * (1 - dim)


def hsv(h):
    return tuple(int(v) for v in foil.hsv(np.array(h % 1.0), 0.55, 1.0))


def burst(ov, rar, age, cx, cy, seed):
    """the rarity burst: rings, particles, rays"""
    col = ACC[rar]; n = {'COMMON': 6, 'UNCOMMON': 12, 'RARE': 22, 'EPIC': 40, 'LEGEND': 80}[rar]; ring = {'COMMON': 16, 'UNCOMMON': 26, 'RARE': 44, 'EPIC': 80, 'LEGEND': 150}[rar]; d = ImageDraw.Draw(ov)
    if age < 0: return
    u = clamp(age / 14)
    for q in range(2 if rar in ('EPIC', 'LEGEND') else 1):
        uu = clamp((age - q * 4) / 14)
        if 0 < uu < 1: d.ellipse([cx - ring * uu, cy - ring * uu * 0.9, cx + ring * uu, cy + ring * uu * 0.9], outline=col + (int(255 * (1 - uu)),), width=2 if rar != 'COMMON' else 1)
    rng = random.Random(seed)
    for k in range(n):
        ang = rng.uniform(0, 2 * math.pi); sp = rng.uniform(1.5, 5.5) * (1 + RARS.index(rar) * 0.35); life = rng.randint(16, 34)
        if age > life: continue
        x = cx + math.cos(ang) * sp * age; y = cy + math.sin(ang) * sp * age + 0.06 * age * age; a = int(255 * (1 - age / life))
        c = hsv(rng.random()) if rar == 'LEGEND' and k % 2 else (col if k % 3 else (255, 255, 255))
        s = 2 if rng.random() < 0.3 else 1
        d.rectangle([x - s, y - s, x + s, y + s], fill=c + (a,))
    if rar in ('EPIC', 'LEGEND'):                                                           # rotating rays behind the card
        m = 12 if rar == 'EPIC' else 18; L = 130 * clamp(age / 8) * (1 - 0.3 * clamp((age - 20) / 30))
        for r_ in range(m):
            a0 = r_ * 2 * math.pi / m + age * (0.03 if rar == 'EPIC' else 0.045); w = 0.07
            c = hsv(r_ / m + age * 0.01) if rar == 'LEGEND' else col
            d.polygon([(cx, cy), (cx + math.cos(a0 - w) * L * 1.5, cy + math.sin(a0 - w) * L * 1.5), (cx + math.cos(a0 + w) * L * 1.5, cy + math.sin(a0 + w) * L * 1.5)], fill=c + (int(70 * (1 - clamp(age / 90))),))


# ---------------------------------------------------------------------------------------------------------------- the scene
class Scene:
    def __init__(s, pack, seed=1, best=None):
        s.pack = pack; s.od = D.odds()[pack]; s.pull = roll(pack, seed, best); s.n = len(s.pull); s.seed = seed
        s.art = D.foil_bag(pack, s.od); s.top = max(RARS.index(x['rarity']) for x in s.pull); s.topc = ACC[RARS[s.top]]
        s.backs = {r: card_back(r) for r in RARS}; s.fcache = {}
        s.styleCol = ACC[RARS[RARS.index(D.LOOK[pack][0])]] if D.LOOK[pack][0] in RARS else (200, 200, 220)
        # timeline
        s.T_float = 0; s.T_charge = 30; s.T_tear = 64; s.T_out = 76; s.T_rev = 106; t = s.T_rev; s.rev = []
        for it in s.pull:
            r = it['rarity']; dur = TENS[r] + 6 + HOLD[r] + 8; s.rev.append((t, t + TENS[r], t + TENS[r] + 6, t + dur - 8, t + dur)); t += dur
        s.T_sum = t; s.N = t + 40

    def slot(s, k): return CX + (k - (s.n - 1) / 2) * 78, 232

    def fimg(s, k, t):
        key = (k, int(t * 12) if s.pull[k]['kind'] == 'player' and s.pull[k]['rarity'] in ('RARE', 'EPIC', 'LEGEND') else 0)
        if key not in s.fcache: s.fcache[key] = face(s.pull[k], t)
        return s.fcache[key]


def glare(img, pos, strength=70):
    a = np.array(img).astype(float); Yg, Xg = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(float)
    g = np.clip(1 - np.abs(Xg + Yg * 0.6 - pos) / 5.0, 0, 1)[..., None] * strength * (a[..., 3:4] > 0)
    a[..., :3] = np.clip(a[..., :3] + g, 0, 255); return Image.fromarray(a.astype(np.uint8), 'RGBA')


def frame(s, i):
    rng = random.Random(i * 7 + 3); arr = background(); shake = 0.0; flash = 0.0; flash_col = (255, 255, 255)
    ov = Image.new('RGBA', (VW, VH), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); under = Image.new('RGBA', (VW, VH), (0, 0, 0, 0)); ud = ImageDraw.Draw(under)
    # drifting dust
    for k in range(12):
        r = random.Random(k * 31); x = (r.uniform(0, VW) + i * r.uniform(-0.2, 0.2)) % VW; y = (r.uniform(0, VH) - i * r.uniform(0.2, 0.7)) % VH; ud.point((int(x), int(y)), (200, 200, 255, int(r.uniform(30, 90))))
    cv = Image.new('RGBA', (VW, VH), (0, 0, 0, 0))
    acc = s.topc
    # ---------------------------------------------------------------- pack phases
    if i < s.T_out + 16:
        pi = i
        if pi < s.T_charge:                                                                  # float in, tilt shimmer
            u = out_back(pi / 22.0); cy = lerp(VH + 120, CY, u); tilt = 0.45 * math.sin(pi * 0.2) * (1 - 0.3 * smooth((pi - 20) / 10)); sc = 2.0
            pos = (0.5 + 0.5 * math.sin(pi * 0.2 + 0.4)) * 150 - 10; shk = 0
        elif pi < s.T_tear:                                                                  # charge: shake, glow leaks out
            u = (pi - s.T_charge) / (s.T_tear - s.T_charge); cy = CY; tilt = 0.1 * math.sin(pi * 1.1) * u; sc = 2.0 + 0.12 * u; pos = 200; shk = 1 + 5 * u * u
            glow(arr, CX, CY, 150 * (0.5 + u), 150 * (0.5 + u), acc, 0.75 * u)
            for k in range(int(10 * u) + 2):                                                  # light streaming in
                r = random.Random(k * 5 + pi // 2); a_ = r.uniform(0, 6.28); dd = 150 - ((pi * 6 + k * 23) % 140); ud.line([(CX + math.cos(a_) * dd, CY + math.sin(a_) * dd * 0.8), (CX + math.cos(a_) * (dd - 10), CY + math.sin(a_) * (dd - 10) * 0.8)], fill=acc + (int(220 * u),))
        else:
            u = (pi - s.T_tear) / 12.0; cy = CY; tilt = 0; sc = 2.12; pos = 200; shk = 6 * (1 - clamp(u))
        shake = max(shake, shk * 0.8 if pi >= s.T_charge else 0)
        ox = rng.uniform(-1, 1) * (shk if pi >= s.T_charge else 0); oy = rng.uniform(-1, 1) * (shk if pi >= s.T_charge else 0)
        art = glare(s.art, pos)
        top_h = 10                                                                           # rows that tear off (crimp + a bit of body)
        if pi < s.T_tear:
            put(cv, art, CX + ox, cy + oy, sc, wf=math.cos(tilt), k=0.18 * math.sin(tilt), alpha=1.0)
        else:
            u = clamp((pi - s.T_tear) / 12.0); u2 = smooth((pi - s.T_out) / 14.0)
            body = art.crop((0, top_h, 64, 96)); bcy = cy + (top_h * sc) / 2 + 60 * u2
            put(cv, body, CX + ox, bcy + oy, sc, alpha=1 - u2)
            if pi < s.T_out + 16:                                                           # light spilling from the cut + the torn strip flying off
                cut = cy - 96 * sc + top_h * sc
                for q in range(3): ud.polygon([(CX - 56 * sc / 2, cut), (CX + 56 * sc / 2, cut), (CX + 140 * (q + 1) / 2, cut - 220), (CX - 140 * (q + 1) / 2, cut - 220)], fill=acc + (int(40 * (1 - u) * (1 if q == 0 else 0.6)),))
                od.rectangle([CX - 62, cut - 2, CX + 62, cut + 1], fill=(255, 255, 255, int(255 * (1 - u2))))
                strip = art.crop((0, 0, 64, top_h)); put(cv, strip, CX + 20 + 110 * u, cut - 10 - 90 * u + 150 * u * u, sc, rot=-0.15 - 4.5 * u, alpha=1 - u * u)
            if pi < s.T_tear + 6: flash = (1 - (pi - s.T_tear) / 6) * 0.6; flash_col = tuple(int(v * 0.5 + 127) for v in acc)
    # ---------------------------------------------------------------- cards burst out and stack
    if s.T_tear + 4 <= i < s.T_rev + 0 or i >= s.T_rev:
        pass
    k_out = range(s.n)
    for k in reversed(k_out):
        if i < s.T_tear + 4: continue
        t0 = s.T_tear + 4 + k * 3; sr = s.rev[k]
        if i >= sr[4] - 8 or i < t0: continue                                               # already collected / not out yet (collected ones are drawn below)
        u = smooth((i - t0) / 18.0); fly_y = lerp(CY - 60, CY, u) - 70 * math.sin(math.pi * clamp((i - t0) / 18.0)); depth = k
        if i < sr[0]:                                                                        # waiting in the stack, top card = next to reveal
            x = CX + k * 1.2 - (s.n - 1) * 0.6; y = fly_y + k * 1.2 - (s.n - 1) * 0.6 + 0.8 * math.sin(i * 0.2 + k)
            put(cv, s.backs[RARS[RARS.index(D.LOOK[s.pack][0])] if D.LOOK[s.pack][0] in RARS else 'COMMON'], x, y, 2.0 * lerp(0.6, 1.0, u), rot=lerp(0.12 * (k - 1.5), 0.0, u))
    # ---------------------------------------------------------------- reveals
    rev_k = next((k for k, r in enumerate(s.rev) if r[0] <= i < r[4]), None)
    dim = 0.0
    for k, (a0, a1, a2, a3, a4) in enumerate(s.rev):
        it = s.pull[k]; rar = it['rarity']; col = ACC[rar]; big = RARS.index(rar)
        if i < a0: continue
        sx, sy = s.slot(k)
        if i >= a4:                                                                          # collected: sits in the row (moves to the summary layout later)
            ts = clamp((i - s.T_sum) / 18.0)
            fx_, fy_ = lerp(sx, CX + (k - (s.n - 1) / 2) * 104, smooth(ts - k * 0.0)), lerp(sy, 140, smooth(ts)); put(cv, s.fimg(k, 0.95 if ts < 1 else ((i * 0.02) % 1.0)), fx_, fy_, lerp(1.0, 1.5, smooth(ts)))
            continue
        # focus card
        if i < a1:                                                                           # tension: the back shakes and the rarity leaks round its edge
            u = (i - a0) / max(1, a1 - a0); sh = 0.3 + big * 0.8 * u * u; ox = rng.uniform(-1, 1) * sh; oy = rng.uniform(-1, 1) * sh
            glow(arr, CX, CY, 90 + 40 * u * (1 + big * 0.3), 110 + 40 * u, col, 0.18 * u * (0.3 + big * 0.35))
            for q in range(int(2 + 6 * u * (big / 2.0))): r = random.Random(q * 9 + i); a_ = r.uniform(0, 6.28); dd = 60 + r.uniform(0, 40); od.point((int(CX + math.cos(a_) * dd), int(CY + math.sin(a_) * dd * 1.2)), col + (200,))
            enter = smooth((i - a0) / 6.0); put(cv, s.backs[D.LOOK[s.pack][0] if D.LOOK[s.pack][0] in RARS else 'COMMON'], CX + ox, CY + oy + (1 - enter) * 4, 2.0 * (1 + 0.04 * u))
            if rar == 'LEGEND': dim = 0.35 * u
            elif rar == 'EPIC': dim = 0.2 * u
        elif i < a2:                                                                          # flip
            u = (i - a1) / (a2 - a1); wf = abs(math.cos(math.pi * u)); face_up = u >= 0.5
            im = s.fimg(k, 0.9) if face_up else s.backs[D.LOOK[s.pack][0] if D.LOOK[s.pack][0] in RARS else 'COMMON']
            put(cv, im, CX, CY, 2.0 * (1 + 0.12 * math.sin(math.pi * u)), wf=wf, k=0.12 * math.sin(math.pi * u) * (1 if u < 0.5 else -1))
            dim = (0.35 if rar == 'LEGEND' else 0.2 if rar == 'EPIC' else 0.0)
            glow(arr, CX, CY, 150, 150, col, 0.5 * u * (0.4 + big * 0.2))
        elif i < a3:                                                                          # hold: the face, with the burst
            age = i - a2; pop = 1 + (0.18 if rar == 'LEGEND' else 0.1 if rar == 'EPIC' else 0.05) * math.exp(-age / 5.0) * math.cos(age * 0.5)
            dim = (0.35 if rar == 'LEGEND' else 0.2 if rar == 'EPIC' else 0.0) * (1 - 0.4 * smooth(age / 30.0))
            glow(arr, CX, CY, 170, 170, col, (0.35 + 0.15 * big) * (1 - 0.3 * clamp(age / 40)))
            burst(ov, rar, age, CX, CY, 100 + k)
            if age < 3: flash = {'COMMON': 0.0, 'UNCOMMON': 0.12, 'RARE': 0.3, 'EPIC': 0.55, 'LEGEND': 0.95}[rar] * (1 - age / 3); flash_col = tuple(int(v * 0.4 + 150) for v in col)
            shake = max(shake, [0, 0, 1.5, 3.5, 6][big] * math.exp(-age / 6.0))
            put(cv, s.fimg(k, ((i - a2) * 0.03) % 1.0), CX, CY, 2.0 * pop)
        else:                                                                                 # leave: shrink down to its slot in the row
            u = smooth((i - a3) / 8.0); put(cv, s.fimg(k, 0.95), lerp(CX, sx, u), lerp(CY, sy, u), lerp(2.0, 1.0, u))
    # the next card slides up in the stack while a card is being shown is handled by the stack above
    # ---------------------------------------------------------------- summary glow
    if i >= s.T_sum - 6: glow(arr, CX, 140, 260, 170, acc, 0.22 * smooth((i - s.T_sum + 6) / 20.0))
    # ---------------------------------------------------------------- compose
    arr = arr * (1 - dim)[..., None] if isinstance(dim, np.ndarray) else arr * (1 - dim)
    base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    base.alpha_composite(under); base.alpha_composite(cv); base.alpha_composite(ov)
    if flash > 0.01: base.alpha_composite(Image.new('RGBA', (VW, VH), flash_col + (int(255 * clamp(flash)),)))
    if shake > 0.2:
        dx, dy = int(round(rng.uniform(-1, 1) * shake)), int(round(rng.uniform(-1, 1) * shake)); sh = Image.new('RGBA', (VW, VH), (6, 5, 12, 255)); sh.alpha_composite(base, (dx, dy)); base = sh
    return base.convert('RGB')


Scene.frame = frame


def tilt_frames(pack, n=48):
    """the idle pack: the player tilts it, the foil catches the light (in game the tilt follows the mouse / finger)"""
    s = Scene(pack, 3); out = []
    for i in range(n):
        ph = 2 * math.pi * i / n; tilt = 0.5 * math.sin(ph); arr = background(); im = Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA'); cv = Image.new('RGBA', (VW, VH), (0, 0, 0, 0))
        art = glare(s.art, (0.5 + 0.5 * math.sin(ph + 0.3)) * 150 - 10, 80)
        put(cv, art, CX + 12 * math.sin(ph), CY + 3 * math.sin(ph * 2), 2.0, wf=math.cos(tilt), k=0.2 * math.sin(tilt)); im.alpha_composite(cv); out.append(im.convert('RGB'))
    return out


def save_gif(frames, path, ms=40):
    q = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=ms, loop=0, optimize=False)


def sheet(frames, path, cols=10, S=0.3, step=None):
    step = step or max(1, len(frames) // 40); fs = frames[::step][:40]; w, h = int(VW * S), int(VH * S); rows = (len(fs) + cols - 1) // cols
    im = Image.new('RGB', (cols * w, rows * h))
    for n, f in enumerate(fs): im.paste(f.resize((w, h), Image.LANCZOS), ((n % cols) * w, (n // cols) * h))
    im.save(path)


if __name__ == '__main__':
    out = os.path.join(ROOT, 'export', 'packs'); os.makedirs(out, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == 'tilt':
        fr = tilt_frames(sys.argv[2] if len(sys.argv) > 2 else 'Legend Pack'); save_gif(fr, os.path.join(out, 'tilt.gif')); sheet(fr, os.path.join(out, 'tilt_sheet.png'), step=3); print('tilt', len(fr))
    else:
        pack = sys.argv[1] if len(sys.argv) > 1 else 'Legend Pack'; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1; best = sys.argv[3] if len(sys.argv) > 3 else None
        s = Scene(pack, seed, best); print([(x['kind'], x['rarity'], x['row'].get('name')) for x in s.pull], 'frames', s.N)
        fr = [s.frame(i) for i in range(s.N)]; name = 'open_' + pack.lower().replace(' ', '_')
        save_gif(fr, os.path.join(out, name + '.gif')); sheet(fr, os.path.join(out, name + '_sheet.png')); print(name, os.path.getsize(os.path.join(out, name + '.gif')) // 1024, 'KB')
