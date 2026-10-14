"""Procedural face portraits from a players.csv row (skin, hair style/colour, beard, glasses, headband, chain, kit).
Drawn at 28x24 and meant to be scaled 2x. Cheap: one function, ten hair styles."""
from PIL import Image, ImageDraw
import looks

W, H = 28, 24


def _rgb(h, d=(0, 0, 0)):
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
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    A = lambda c: tuple(c) + (255,)
    sk, skd, skl = A(skin), A(_sh(skin, .78)), A(_sh(skin, 1.12))
    hc, hd, hl = A(hair), A(_sh(hair, .66)), A(_sh(hair, 1.45))
    style = (p.get('hair_style') or 'H01')[:3]
    cx = 14
    # shoulders + collar
    d.polygon([(2, 23), (4, 19), (10, 18), (18, 18), (24, 19), (26, 23)], fill=A(jersey))
    d.line([(10, 18), (12, 20), (15, 20), (17, 18)], fill=A(trim))
    # neck
    d.rectangle([12, 15, 15, 19], fill=skd)
    # back hair for long styles / ponytail / braids / afro
    if style in ('H08', 'H07'):
        d.rectangle([7, 6, 20, 21 if style == 'H08' else 20], fill=hd)
    if style == 'H06':
        d.ellipse([5, 0, 22, 14], fill=hd)
    if style == 'H09': d.rectangle([20, 7, 23, 14], fill=hd); d.rectangle([22, 12, 23, 17], fill=hd)
    # ears
    # head
    d.ellipse([8, 3, 19, 17], fill=sk)
    d.rectangle([8, 11, 8, 12], fill=sk); d.rectangle([19, 11, 19, 12], fill=sk)
    # face
    for ex in (9, 16):
        d.rectangle([ex + 1, 10, ex + 1, 11], fill=A((28, 24, 36)))
    d.line([(12, 15), (15, 15)], fill=A(_sh(skin, .62)))
    # beard
    bd = p.get('beard') or 'none'
    if bd == 'stubble':
        d.rectangle([9, 14, 18, 16], fill=A(_sh(skin, .86)))
    elif bd in ('short', 'full'):
        d.polygon([(8, 12), (9, 15), (11, 17), (16, 17), (18, 15), (19, 12), (18, 12), (17, 14), (10, 14), (9, 12)], fill=hd)
        d.line([(12, 15), (15, 15)], fill=A(_sh(skin, .6)))
        if bd == 'full': d.rectangle([10, 17, 17, 18], fill=hd)
        d.line([(12, 13), (15, 13)], fill=hd)
    # hair on top
    if style == 'H01': d.chord([8, 2, 19, 10], 180, 360, fill=hd); d.line([(9, 6), (18, 6)], fill=hd)
    elif style == 'H02': d.chord([8, 1, 19, 11], 180, 360, fill=hc); d.rectangle([9, 5, 18, 6], fill=hc); d.line([(9, 7), (18, 7)], fill=hd)
    elif style == 'H03':
        d.chord([8, 1, 19, 11], 180, 360, fill=hc); d.rectangle([9, 5, 18, 7], fill=hc); d.polygon([(8, 7), (14, 5), (14, 7)], fill=hc)
    elif style == 'H04':
        d.chord([7, 0, 20, 10], 180, 360, fill=hc); d.rectangle([9, 0, 19, 3], fill=hc); d.rectangle([9, 5, 18, 6], fill=hc)
    elif style == 'H05':
        for (x, y) in ((8, 4), (10, 2), (13, 1), (16, 2), (18, 4), (7, 7), (20, 7)): d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=hc)
        d.rectangle([8, 4, 19, 6], fill=hc)
    elif style == 'H06':
        d.ellipse([5, 0, 22, 9], fill=hc); d.rectangle([7, 4, 20, 5], fill=hc); d.rectangle([6, 5, 7, 10], fill=hc); d.rectangle([20, 5, 21, 10], fill=hc)
    elif style == 'H07':
        d.chord([8, 1, 19, 11], 180, 360, fill=hc); d.rectangle([9, 5, 18, 6], fill=hc)
        for x in (7, 9, 18, 20): d.line([(x, 8), (x, 19)], fill=hc); d.point((x, 12), hd); d.point((x, 16), hd)
    elif style == 'H08':
        d.chord([8, 1, 19, 11], 180, 360, fill=hc); d.rectangle([9, 5, 18, 6], fill=hc)
        d.rectangle([7, 7, 8, 20], fill=hc); d.rectangle([19, 7, 20, 20], fill=hc)
    elif style == 'H09':
        d.chord([8, 1, 19, 11], 180, 360, fill=hc); d.rectangle([9, 5, 18, 6], fill=hc)
    elif style == 'H10':
        d.chord([8, 1, 19, 11], 180, 360, fill=hc); d.rectangle([9, 5, 18, 6], fill=hc); d.ellipse([11, -2, 16, 3], fill=hc)
    # extras
    if p.get('headband') in ('1', 1, True): d.rectangle([9, 5, 18, 6], fill=A(trim))
    gl = p.get('glasses') or 'none'
    if gl != 'none':
        col = A((20, 20, 30)) if gl == 'dark' else A((170, 200, 230))
        for ex in (8, 15): d.rectangle([ex, 9, ex + 4, 11], outline=A((20, 20, 30)), fill=col if gl == 'dark' else None)
        d.line([(13, 10), (14, 10)], fill=A((20, 20, 30)))
    if p.get('chain') in ('1', 1, True): d.line([(11, 21), (13, 22), (14, 22), (16, 21)], fill=A((240, 200, 70)))
    # outline the bust against the background
    return im
