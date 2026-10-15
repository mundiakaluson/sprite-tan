"""Pack wrapper design concepts (64x96 px each, upscaled 4x for viewing). Four directions x six packs:  python packs/concepts.py  -> export/packs/concept_{A,B,C,D}.png + all.png"""
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'titan')); sys.path.insert(0, os.path.join(ROOT, 'sprites')); sys.path.insert(0, os.path.join(ROOT, 'cards'))
import engine as E

W, H = 64, 96
INK = (22, 14, 40); WHITE = (255, 255, 255); GOLD = (255, 205, 60)
# name: (main, dark, light, accent, stars, icon, label)
PACKS = {
    'player': ((52, 120, 220), (24, 54, 130), (130, 190, 255), (255, 205, 60), 1, 'player', 'PLAYER'),
    'card':   ((60, 170, 110), (24, 90, 60), (140, 230, 170), (255, 205, 60), 1, 'cards', 'CARD'),
    'mixed':  ((236, 130, 50), (130, 62, 20), (255, 200, 130), (255, 240, 200), 2, 'ball', 'MIXED'),
    'rare':   ((40, 180, 200), (16, 84, 110), (150, 240, 250), (255, 255, 255), 3, 'gem', 'RARE'),
    'epic':   ((150, 70, 210), (66, 24, 110), (220, 160, 255), (255, 120, 200), 4, 'bolt', 'EPIC'),
    'legend': ((255, 190, 40), (140, 80, 10), (255, 240, 150), (255, 80, 80), 5, 'crown', 'LEGEND'),
}


def text(im, s, cx, y, col, shadow=INK):
    t = E.pix_text(s, col, 1, shadow); im.alpha_composite(t, (cx - t.width // 2, y))


def blank(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def circle(d, cx, cy, r, fill=None, outline=None):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline)


def icon(d, kind, cx, cy, s, col, dark):
    """small pixel icons, s = half size"""
    if kind == 'ball':
        circle(d, cx, cy, s, WHITE, INK); d.polygon([(cx, cy - s // 2), (cx + s // 2, cy - 1), (cx + s // 3, cy + s // 2), (cx - s // 3, cy + s // 2), (cx - s // 2, cy - 1)], fill=INK)
        for a in range(5): ang = a * 2 * math.pi / 5 - math.pi / 2; d.line([(cx + math.cos(ang) * s // 2, cy + math.sin(ang) * s // 2), (cx + math.cos(ang) * s, cy + math.sin(ang) * s)], fill=INK)
    elif kind == 'player':
        circle(d, cx, cy - s // 2, s // 2, WHITE, INK); d.pieslice([cx - s, cy - 1, cx + s, cy + 2 * s], 180, 360, fill=WHITE, outline=INK)
    elif kind == 'cards':
        for i, (dx, dy, c) in enumerate(((-s // 2, 1, dark), (0, 0, col), (s // 2, -1, WHITE))): d.rectangle([cx + dx - s // 2, cy + dy - s, cx + dx + s // 2, cy + dy + s], fill=c, outline=INK)
    elif kind == 'gem':
        d.polygon([(cx - s, cy - s // 3), (cx - s // 2, cy - s), (cx + s // 2, cy - s), (cx + s, cy - s // 3), (cx, cy + s)], fill=WHITE, outline=INK); d.line([(cx - s, cy - s // 3), (cx + s, cy - s // 3)], fill=INK); d.line([(cx, cy - s // 3), (cx, cy + s)], fill=INK)
    elif kind == 'bolt':
        d.polygon([(cx + 1, cy - s), (cx - s // 2, cy + 1), (cx, cy + 1), (cx - 2, cy + s), (cx + s // 2 + 1, cy - 2), (cx + 1, cy - 2)], fill=WHITE, outline=INK)
    elif kind == 'crown':
        d.polygon([(cx - s, cy + s // 2), (cx - s, cy - s // 2), (cx - s // 2, cy), (cx, cy - s), (cx + s // 2, cy), (cx + s, cy - s // 2), (cx + s, cy + s // 2)], fill=WHITE, outline=INK)
        for x in (-s // 2, 0, s // 2): d.point((cx + x, cy + 1), fill=INK)


def stars(d, cx, y, n, col):
    x0 = cx - (n * 7) // 2
    for i in range(n):
        x = x0 + i * 7 + 3; d.polygon([(x, y), (x + 1, y + 2), (x + 3, y + 2), (x + 1, y + 4), (x + 2, y + 6), (x, y + 5), (x - 2, y + 6), (x - 1, y + 4), (x - 3, y + 2), (x - 1, y + 2)], fill=col, outline=INK)


def shade(im, mask_box, main, dark, light, vert=True, dither=True):
    x0, y0, x1, y1 = mask_box; d = ImageDraw.Draw(im)
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        for x in range(x0, x1 + 1):
            u = t * 0.8 + ((x - x0) / max(1, x1 - x0)) * 0.2
            c = main if u < 0.55 else (main if (x + y) % 2 and u < 0.7 else dark)
            d.point((x, y), fill=c)


# ------------------------------------------------------------------------------------------------ A: crimped foil wrapper
def design_a(pk):
    main, dark, light, acc, n, ic, label = PACKS[pk]; im = blank(); d = ImageDraw.Draw(im)
    shade(im, (3, 8, 60, 87), main, dark, light)
    for y in list(range(0, 9)) + list(range(87, 96)):                                              # crimped ends: ridged and toothed
        for x in range(2, 62):
            edge = 0 if y >= 87 or True else 0
            tooth = (x % 4 < 2)
            if y < 9 and (y > 1 or tooth): d.point((x, y), fill=dark if x % 2 else main)
            if y >= 87 and (y < 94 or tooth): d.point((x, y), fill=dark if x % 2 else main)
    d.line([(2, 8), (61, 8)], fill=INK); d.line([(2, 87), (61, 87)], fill=INK)
    d.line([(2, 2), (2, 94)], fill=INK); d.line([(61, 2), (61, 94)], fill=INK)
    for k in range(0, 14):                                                                          # glossy diagonal shine
        x = 8 + k * 3; d.line([(x, 88), (x + 28, 8)], fill=light + (60 if k % 4 else 110,))
    circle(d, 32, 40, 17, dark, INK); circle(d, 32, 40, 14, main, None); d.arc([18, 26, 46, 54], 200, 300, fill=light)
    icon(d, ic, 32, 40, 9, acc, dark)
    d.rectangle([6, 62, 57, 76], fill=INK); d.rectangle([7, 63, 56, 75], fill=dark); d.line([(7, 63), (56, 63)], fill=acc)
    text(im, label, 32, 61, acc if pk != 'legend' else WHITE)
    stars(d, 32, 80, n, acc)
    return im


# ------------------------------------------------------------------------------------------------ B: card-back sleeve
def design_b(pk):
    main, dark, light, acc, n, ic, label = PACKS[pk]; im = blank(); d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, 62, 94], 5, fill=INK); d.rounded_rectangle([3, 3, 60, 92], 4, fill=dark); d.rounded_rectangle([5, 5, 58, 90], 3, outline=acc)
    for y in range(8, 88):                                                                          # diamond lattice
        for x in range(8, 56):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0: d.point((x, y), fill=main)
    circle(d, 32, 38, 19, INK); circle(d, 32, 38, 17, acc); circle(d, 32, 38, 15, main); circle(d, 32, 38, 13, dark)
    icon(d, ic, 32, 38, 10, acc, dark)
    d.polygon([(4, 62), (60, 62), (56, 70), (60, 78), (4, 78), (8, 70)], fill=INK); d.polygon([(6, 63), (58, 63), (55, 70), (58, 77), (6, 77), (9, 70)], fill=acc)
    text(im, label, 32, 63, INK, shadow=light)
    for (x, y) in ((9, 9), (54, 9), (9, 86), (54, 86)): d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=acc)
    stars(d, 32, 82, n, acc)
    return im


# ------------------------------------------------------------------------------------------------ C: sealed envelope
def design_c(pk):
    main, dark, light, acc, n, ic, label = PACKS[pk]; im = blank(); d = ImageDraw.Draw(im)
    d.rectangle([2, 4, 61, 91], fill=INK); d.rectangle([3, 5, 60, 90], fill=main)
    for y in range(6, 90):
        for x in range(4, 60):
            if (x + y) % 2 == 0 and y > 56: d.point((x, y), fill=dark)
    d.polygon([(3, 5), (60, 5), (32, 44)], fill=light, outline=INK); d.line([(3, 90), (32, 60)], fill=INK); d.line([(60, 90), (32, 60)], fill=INK)   # flap + fold lines
    d.polygon([(4, 6), (59, 6), (32, 41)], fill=main); d.line([(8, 8), (32, 36)], fill=light)
    d.rectangle([2, 52, 61, 58], fill=acc, outline=INK); d.line([(2, 55), (61, 55)], fill=dark)       # ribbon band
    circle(d, 32, 44, 9, INK); circle(d, 32, 44, 8, dark); circle(d, 32, 44, 6, acc if pk != 'legend' else (230, 60, 60))   # wax seal
    icon(d, ic, 32, 44, 4, acc, dark)
    d.rectangle([9, 68, 54, 82], fill=(250, 244, 226), outline=INK); text(im, label, 32, 67, INK, shadow=(250, 244, 226))
    stars(d, 32, 84, n, GOLD)
    return im


# ------------------------------------------------------------------------------------------------ D: sticker-bag packet
def design_d(pk):
    main, dark, light, acc, n, ic, label = PACKS[pk]; im = blank(); d = ImageDraw.Draw(im)
    d.rectangle([2, 4, 61, 91], fill=INK)
    for x in range(3, 61):
        c = main if ((x - 3) // 6) % 2 == 0 else dark; d.line([(x, 5), (x, 90)], fill=c)             # pennant stripes
    for x in range(2, 62, 4): d.polygon([(x, 4), (x + 2, 0), (x + 4, 4)], fill=INK); d.polygon([(x + 1, 4), (x + 2, 1), (x + 3, 4)], fill=light)   # tear zigzag
    d.rectangle([3, 40, 60, 66], fill=(60, 150, 80), outline=INK)                                   # pitch band
    for y in (43, 63): d.line([(5, y), (58, y)], fill=WHITE)
    for x in (6, 57): d.line([(x, 43), (x, 63)], fill=WHITE)
    text(im, label, 32, 47, WHITE)
    circle(d, 32, 22, 13, INK); circle(d, 32, 22, 11, acc); icon(d, ic, 32, 22, 7, acc, dark)
    d.polygon([(10, 72), (54, 72), (50, 80), (54, 88), (10, 88), (14, 80)], fill=INK); d.polygon([(11, 73), (53, 73), (49, 80), (53, 87), (11, 87), (15, 80)], fill=light)
    stars(d, 32, 77, n, dark)
    return im


DESIGNS = {'A': ('Foil wrapper', design_a), 'B': ('Card-back sleeve', design_b), 'C': ('Sealed envelope', design_c), 'D': ('Sticker packet', design_d)}


def sheet(fn, S=4):
    im = Image.new('RGB', (len(PACKS) * (W * S + 16) + 16, H * S + 32), (30, 22, 52))
    for i, pk in enumerate(PACKS):
        p = fn(pk).resize((W * S, H * S), Image.NEAREST); im.paste(p, (16 + i * (W * S + 16), 16), p)
    return im


if __name__ == '__main__':
    out = os.path.join(ROOT, 'export', 'packs'); os.makedirs(out, exist_ok=True); sheets = []
    for k, (name, fn) in DESIGNS.items():
        s = sheet(fn); s.save(os.path.join(out, f'concept_{k}.png')); sheets.append(s)
    big = Image.new('RGB', (sheets[0].width, sum(s.height for s in sheets)))
    y = 0
    for s in sheets: big.paste(s, (0, y)); y += s.height
    big.save(os.path.join(out, 'all.png')); print(big.size)
