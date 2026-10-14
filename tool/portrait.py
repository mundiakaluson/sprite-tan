"""Procedural face portraits from a players.csv row (skin, hair style/colour, beard, glasses, headband, chain, kit).
Drawn directly on a 21x19 pixel grid (shown 2x on the card), so every pixel is deliberate. One routine, ten hair styles."""
from PIL import Image
import looks

W, H = 21, 19
HEAD = {4: (7, 13), 5: (6, 14), 6: (6, 14), 7: (6, 14), 8: (6, 14), 9: (6, 14), 10: (6, 14), 11: (6, 14), 12: (7, 13), 13: (8, 12)}   # row -> (x0, x1)


def _rgb(h):
    h = (h or '#000000').lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _sh(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def portrait(p, kit='home'):
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
    style = (p.get('hair_style') or 'H01')[:3]
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
    put(8, 8, ink); put(12, 8, ink)                                          # eyes
    row(11, 9, 11, _sh(skin, .62))                                           # mouth

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
        row(11, 9, 11, _sh(skin, .62))
        if bd == 'full': rect(7, 9, 7, 9, hd); put(13, 9, hd)

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
    return im
