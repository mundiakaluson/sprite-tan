"""Procedural face portraits from a players.csv row (skin, hair style/colour, beard, glasses, headband, chain, kit).
Drawn directly on a 21x19 pixel grid (shown 2x on the card), so every pixel is deliberate. One routine, ten hair styles."""
from PIL import Image
import looks

W, H = 21, 21
HEAD = {4: (7, 13), 5: (6, 14), 6: (6, 14), 7: (6, 14), 8: (6, 14), 9: (6, 14), 10: (6, 14), 11: (6, 14), 12: (7, 13), 13: (8, 12)}   # row -> (x0, x1)


FACE_T0, FACE_T1 = 0.36, 0.96      # the face moment sits in this part of the loop (the shimmer is 0..0.3)


def card_style(style):
    """which built-in face shape (H01..H10) a hair style uses on the card; data/hair_card.csv, falls back to its own code or H02"""
    try:
        import tables
        for r in tables.table('hair_card').rows:
            if r['style'] == style and r.get('card_like'): return r['card_like'][:3]
    except Exception:
        pass
    c = (style or 'H02')[:3]
    return c if c in {f'H{n:02d}' for n in range(1, 11)} else 'H02'


def _ss(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def _env(u, a, b, c, d):
    """0 -> 1 between a and b (ease in/out), holds to c, back to 0 by d (a slower ease than the way in)"""
    if u < a: return 0.0
    if u < b: return _ss((u - a) / (b - a))
    if u < c: return 1.0
    if u < d: return 1 - _ss((u - c) / (d - c))
    return 0.0


def face_state(kind, t):
    """expression at loop time t (0..1) for a special player's face animation: wink, lookup or smile. None when idle.
    Everything eases in and out, with a little anticipation first and a slower settle at the end, so it reads as a person and not a switch."""
    if kind not in ('wink', 'lookup', 'smile') or not (FACE_T0 <= t < FACE_T1): return None
    u = (t - FACE_T0) / (FACE_T1 - FACE_T0)
    if kind == 'wink':
        sq = _env(u, 0.06, 0.16, 0.2, 0.3)                       # a small squint before the wink
        w = _env(u, 0.2, 0.3, 0.55, 0.78)
        sm = _env(u, 0.14, 0.38, 0.7, 0.96)
        return dict(squint=sq > 0.5, wink=2 if w > 0.7 else 1 if w > 0.25 else 0, mouth=1 if sm > 0.25 else 0, corner2=sm > 0.65, cheek=sm > 0.7, lean=1 if sm > 0.55 else 0)
    if kind == 'lookup':
        dip = _env(u, 0.03, 0.14, 0.17, 0.27)                    # tiny drop first (anticipation)
        eyes = _env(u, 0.14, 0.26, 0.7, 0.9)
        up = _env(u, 0.24, 0.46, 0.7, 0.97)
        dy = round(dip - 2 * up)
        return dict(eyes_up=eyes > 0.5, dy=dy)
    blink = _env(u, 0.03, 0.07, 0.09, 0.14)                      # a natural blink, then the grin grows
    m = _env(u, 0.12, 0.5, 0.74, 0.98)
    g = None
    if 0.5 < u < 0.74: g = int(_ss((u - 0.5) / 0.24) * 5.99)
    return dict(blink=blink > 0.5, mouth=0 if m < 0.12 else 1 if m < 0.35 else 2 if m < 0.6 else 3 if m < 0.85 else 4, squint=m > 0.8,
                glint=g, spark=2 if 0.7 < u < 0.78 else 1 if 0.64 < u < 0.82 else 0, dy=-1 if m > 0.8 else 0)


def _rgb(h):
    h = (h or '#000000').lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _sh(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def row_(px, x0, x1, y, c):
    for x in range(x0, x1 + 1):
        if 0 <= y < H: px[x, y] = tuple(c) + (255,)


def portrait(p, kit='home', expr=None):
    expr = expr or {}
    pal = looks.palette()
    skin = _rgb(pal['skin'].get(str(p.get('skin') or 3), '#d4a070'))
    hair = _rgb(pal['hair'].get(p.get('hair_color') or 'black', '#14101a'))
    gk = p.get('role') == 'GK'
    kd = looks.kit_dict(kit or 'home'); jersey = tuple(kd.get('jersey', (214, 50, 64))) if not gk else (60, 170, 90)
    trim = tuple(kd.get('trim', (240, 240, 250)))
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); px = im.load()

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H: px[x, y] = tuple(c) + (255,)

    def row(y, x0, x1, c):
        for x in range(x0, x1 + 1): put(x, y, c)

    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1): row(y, x0, x1, c)

    sk, skd = skin, _sh(skin, .8)
    hc, hd = hair, _sh(hair, .62)
    hl = tuple(min(255, int(v * 1.5) + 14) for v in hair)
    style = card_style(p.get('hair_style'))
    ink = (26, 22, 34)

    # shoulders, collar, neck
    for y, (a, b) in zip(range(15, 19), ((5, 15), (3, 17), (2, 18), (1, 19))): row(y, a, b, jersey)
    row(15, 5, 6, _sh(jersey, .8)); row(15, 14, 15, _sh(jersey, .8))
    rect(8, 13, 12, 15, skd)
    for (x, y) in ((8, 15), (9, 16), (10, 16), (11, 16), (12, 15)): put(x, y, trim)
    if p.get('chain') in ('1', 1, True):
        for (x, y) in ((9, 17), (10, 18), (11, 17)): put(x, y, (240, 200, 70))

    # hair behind the head
    if style == 'H08': rect(5, 5, 15, 16, hd)
    if style == 'H06':
        row(0, 7, 13, hd); row(1, 6, 14, hd); row(2, 5, 15, hd); rect(4, 3, 16, 9, hd)
    if style == 'H09':
        for (x, y) in ((15, 5), (16, 6), (16, 7), (16, 8), (16, 9), (15, 10)): put(x, y, hd)
    if style == 'H07': rect(5, 5, 15, 15, hd)

    # head
    for y, (a, b) in HEAD.items(): row(y, a, b, sk)
    for y in range(6, 12): put(14, y, skd)                                   # shaded cheek

    bd = p.get('beard') or 'none'
    if bd == 'stubble':
        for y, (a, b) in HEAD.items():
            if y >= 10:
                for x in range(a, b + 1):
                    if not (y == 11 and 9 <= x <= 11): put(x, y, _sh(skin, .84))
    elif bd in ('short', 'full'):
        for y, (a, b) in HEAD.items():
            if y < 10: continue
            for x in range(a, b + 1):
                edge = x in (a, a + 1, b, b - 1) or y >= 12
                if (bd == 'full' and y >= 9) or edge or y == 10: put(x, y, hd)
        if bd == 'full': rect(7, 9, 7, 9, hd); put(13, 9, hd)

    # eyes and mouth (and the special-card expressions)
    mc = _sh(skin, .62); half = tuple((i + j) // 2 for i, j in zip(ink, skin)); shut = _sh(skin, .5)
    ey = 7 if expr.get('eyes_up') else 8
    def eye(x, how='open'):
        if how == 'shut': row(8, x - 1, x + 1, shut)
        elif how == 'half': put(x, 8, half)
        else: put(x, ey, ink)
    both = 'shut' if expr.get('blink') else 'half' if expr.get('squint') else 'open'
    eye(8, both)
    w = expr.get('wink', 0); eye(12, 'shut' if w == 2 else 'half' if w == 1 else both)
    ms = expr.get('mouth', 0)
    if ms == 0: row(11, 9, 11, mc)
    elif ms == 1 and 'wink' in expr: row(11, 9, 11, mc); put(12, 10, mc)                       # smirk: one corner lifts
    elif ms == 1: row(11, 9, 11, mc); put(8, 10, _sh(skin, .85)); put(12, 10, _sh(skin, .85))     # the start of a smile
    elif ms == 2: row(11, 8, 12, mc); put(7, 10, mc); put(13, 10, mc)
    elif ms == 3: row(11, 8, 12, (226, 230, 240)); put(7, 11, mc); put(13, 11, mc); row(12, 9, 11, mc)
    else:
        row(11, 8, 12, (232, 236, 246)); put(7, 11, mc); put(13, 11, mc); row(12, 9, 11, mc); put(8, 10, mc); put(12, 10, mc); put(7, 10, _sh(skin, .85)); put(13, 10, _sh(skin, .85))
    if expr.get('corner2'): put(13, 10, mc)
    if expr.get('cheek'): put(13, 9, tuple(min(255, int(v * 1.12)) for v in skin))
    g = expr.get('glint')
    if g is not None and ms >= 3: put(8 + g, 11, (255, 255, 255))

    # hair on top (silhouettes differ: buzz, crop, side part, quiff, curly, afro, braids, long, ponytail, bun)
    if style == 'H01':
        row(4, 7, 13, hd); row(5, 6, 14, hd); put(6, 6, hd); put(14, 6, hd)
    elif style == 'H02':
        row(3, 7, 13, hc); row(4, 6, 14, hc); row(5, 6, 14, hc); row(6, 8, 12, hc); put(6, 6, hd); put(14, 6, hd); row(5, 8, 10, hl)
    elif style == 'H03':
        row(3, 7, 13, hc); row(4, 6, 14, hc); row(5, 6, 14, hc); row(6, 6, 10, hc); row(7, 6, 7, hc); put(14, 6, hd); row(3, 8, 10, hl)
        put(10, 3, hd); put(10, 4, hd)
    elif style == 'H04':
        row(1, 9, 13, hc); row(2, 8, 14, hc); row(3, 7, 14, hc); row(4, 6, 14, hc); row(5, 6, 14, hc); put(6, 6, hd); put(14, 6, hd); row(1, 10, 12, hl); row(2, 9, 10, hl)
    elif style == 'H05':
        for (a, b, y) in ((7, 9, 2), (11, 13, 2), (6, 14, 3), (5, 15, 4), (5, 15, 5)): row(y, a, b, hc)
        for (x, y) in ((5, 6), (15, 6), (5, 7), (15, 7), (7, 6), (9, 6), (11, 6), (13, 6)): put(x, y, hc)
        for (x, y) in ((8, 3), (12, 3), (6, 5), (14, 5)): put(x, y, hl)
        for (x, y) in ((9, 5), (13, 5)): put(x, y, hd)
    elif style == 'H06':
        row(1, 7, 13, hc); row(2, 6, 14, hc); rect(5, 3, 15, 6, hc); rect(4, 5, 5, 9, hc); rect(15, 5, 16, 9, hc); row(6, 6, 14, hc); row(7, 6, 7, hc); row(7, 13, 14, hc)
        for (x, y) in ((7, 2), (11, 2), (5, 4), (13, 3)): put(x, y, hl)
        for (x, y) in ((8, 5), (12, 5), (4, 8), (16, 8)): put(x, y, hd)
    elif style == 'H07':
        row(3, 7, 13, hc); row(4, 6, 14, hc); row(5, 6, 14, hc); row(6, 8, 12, hc)
        for x in (5, 7, 13, 15):
            for y in range(6, 16): put(x, y, hc if y % 3 else hd)
    elif style == 'H08':
        row(3, 7, 13, hc); row(4, 6, 14, hc); row(5, 6, 14, hc); row(6, 7, 13, hc); put(6, 6, hc); put(14, 6, hc)
        for x in (5, 6, 14, 15):
            for y in range(6, 16): put(x, y, hc)
        row(3, 8, 10, hl)
    elif style == 'H09':
        row(3, 7, 13, hc); row(4, 6, 14, hc); row(5, 6, 14, hc); row(6, 8, 12, hc); row(3, 8, 10, hl)
    elif style == 'H10':
        row(3, 7, 13, hc); row(4, 6, 14, hc); row(5, 6, 14, hc); row(6, 8, 12, hc)
        rect(9, 0, 11, 2, hc); put(9, 0, (0, 0, 0, 0)[:3] if False else hc); put(10, 0, hl); row(3, 8, 10, hl)

    # extras
    if p.get('headband') in ('1', 1, True): row(5, 6, 14, trim)
    gl = p.get('glasses') or 'none'
    if gl == 'dark': row(8, 7, 13, ink); put(7, 7, ink); put(13, 7, ink)
    elif gl == 'clear':
        for x in (7, 9, 11, 13): put(x, 8, (150, 170, 200))
        row(7, 7, 9, (150, 170, 200)); row(7, 11, 13, (150, 170, 200)); put(8, 8, ink); put(12, 8, ink)
    big = Image.new('RGBA', (W, H), (0, 0, 0, 0)); big.alpha_composite(im, (0, 2)); im = big     # two rows of headroom for the head moves
    sp = expr.get('spark', 0)
    if sp:
        bx, by = 16, 11
        for (x, y) in ((bx, by), (bx - 1, by), (bx + 1, by), (bx, by - 1), (bx, by + 1)): put(x, y, (255, 255, 255))
        if sp == 2:
            for (x, y) in ((bx, by - 2), (bx, by + 2), (bx - 2, by), (bx + 2, by)): put(x, y, (255, 248, 190))
    dy, lean = expr.get('dy', 0), expr.get('lean', 0)
    if dy or lean:                # nod / chin up / head tilt: the head moves, the neck and shoulders stay put
        head = im.crop((0, 0, W, 17)); body = im.crop((0, 17, W, H))
        im2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); im2.alpha_composite(body, (0, 17)); px = im2.load()
        for y in range(17 + min(dy, 0), 18): row_(px, 8, 12, y, skd)
        for y in range(17):
            ln = head.crop((0, y, W, y + 1)); im2.alpha_composite(ln, ((lean if y <= 12 else 0), y + dy))
        im = im2
    return im
