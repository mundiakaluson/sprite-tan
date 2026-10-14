"""More emblem pieces on the 56x38 emblem canvas: tiny pixel footballers in poses, arrows and icons.
Used by recipes.py. Everything draws onto an RGBA image `a` and returns nothing unless noted."""
import math
from PIL import Image, ImageDraw
from emblem import *
from emblem import W_, H_

SK = (238, 178, 124, 255); SKD = (186, 120, 84, 255); SHORTS = (34, 38, 82, 255); BOOT_ = (28, 28, 40, 255); GREY_SHIRT = (126, 132, 158); GLOVE = (240, 240, 250, 255)
GOLD = (255, 232, 130, 255)


def lay(a, m):
    """outline a drawing layer and put it on a."""
    a.alpha_composite(outline(m))


def person(a, x, y, shirt, pose='stand', f=1, opp=False, keeper=False, hair=(52, 36, 28)):
    """footballer, feet at (x, y), about 16 px tall. f=+1 faces right, -1 faces left. Colour = shirt (rgb)."""
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    sh = (GREY_SHIRT if opp else tuple(shirt)) + (255,); sho = (60, 64, 100, 255) if opp else SHORTS
    X = lambda dx: x + f * dx
    hand = GLOVE if keeper else SK
    def head(cx, cy):
        d.ellipse([cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5], fill=SK); d.pieslice([cx - 2.5, cy - 2.7, cx + 2.5, cy + 2.3], 180, 360, fill=hair + (255,))
    def leg(hx, hy, fx, fy, w=2):
        d.line([(hx, hy), (fx, fy)], fill=SK, width=w); d.line([(fx, fy), (fx + f * 1.5, fy)], fill=BOOT_, width=2)
    if pose == 'stand':
        leg(X(-1.2), y - 4, X(-1.2), y - 1); leg(X(1.4), y - 4, X(1.4), y - 1)
        d.rectangle([X(-3) if f > 0 else X(3), y - 10, X(3) if f > 0 else X(-3), y - 5], fill=sh); d.rectangle([min(X(-3), X(3)), y - 5, max(X(-3), X(3)), y - 3], fill=sho)
        d.line([(X(-3.5), y - 9), (X(-4), y - 5)], fill=hand, width=2); d.line([(X(3.5), y - 9), (X(4), y - 5)], fill=hand, width=2); head(X(0), y - 13)
    elif pose == 'run':
        leg(X(-1), y - 4, X(-5), y - 1); leg(X(1), y - 4, X(4), y - 2.5)
        d.polygon([(X(-3), y - 9), (X(3), y - 10), (X(4), y - 5), (X(-2), y - 4)], fill=sh); d.polygon([(X(-2), y - 4), (X(4), y - 5), (X(3), y - 3), (X(-2), y - 2)], fill=sho)
        d.line([(X(0), y - 9), (X(-4), y - 7)], fill=hand, width=2); d.line([(X(2), y - 9), (X(5), y - 7)], fill=hand, width=2); head(X(3), y - 12.5)
    elif pose == 'kick':
        leg(X(-1.5), y - 4, X(-2), y - 1); d.line([(X(1), y - 4), (X(8), y - 5)], fill=SK, width=2); d.line([(X(8), y - 5), (X(10), y - 6)], fill=BOOT_, width=2)
        d.polygon([(X(-3), y - 9), (X(2), y - 10), (X(3), y - 5), (X(-3), y - 5)], fill=sh); d.rectangle([min(X(-3), X(3)), y - 5, max(X(-3), X(3)), y - 3], fill=sho)
        d.line([(X(-3), y - 9), (X(-7), y - 8)], fill=hand, width=2); d.line([(X(2), y - 9), (X(6), y - 10)], fill=hand, width=2); head(X(0), y - 13)
    elif pose == 'tackle':   # standing, one leg stretched out low
        leg(X(-2), y - 4, X(-3), y - 1); d.line([(X(0), y - 4), (X(9), y - 2)], fill=SK, width=2); d.line([(X(9), y - 2), (X(11), y - 2)], fill=BOOT_, width=2)
        d.polygon([(X(-4), y - 9), (X(1), y - 10), (X(2), y - 5), (X(-4), y - 5)], fill=sh); d.rectangle([min(X(-4), X(2)), y - 5, max(X(-4), X(2)), y - 3], fill=sho)
        d.line([(X(-4), y - 9), (X(-8), y - 6)], fill=hand, width=2); d.line([(X(1), y - 9), (X(5), y - 7)], fill=hand, width=2); head(X(-1), y - 13)
    elif pose == 'slide':
        d.line([(X(-3), y - 2), (X(10), y - 1)], fill=SK, width=2); d.line([(X(10), y - 1), (X(12), y - 2)], fill=BOOT_, width=2)
        d.line([(X(-7), y - 5), (X(-1), y - 3)], fill=sh, width=4); d.line([(X(-2), y - 3), (X(2), y - 2)], fill=sho, width=3)
        d.line([(X(-5), y - 4), (X(2), y - 7)], fill=hand, width=2); head(X(-9), y - 7)
    elif pose == 'jump':
        leg(X(-1), y - 6, X(-3), y - 3); leg(X(1), y - 6, X(3), y - 3)
        d.rectangle([min(X(-3), X(3)), y - 12, max(X(-3), X(3)), y - 7], fill=sh); d.rectangle([min(X(-3), X(3)), y - 7, max(X(-3), X(3)), y - 5], fill=sho)
        d.line([(X(-3), y - 11), (X(-6), y - 15)], fill=hand, width=2); d.line([(X(3), y - 11), (X(6), y - 15)], fill=hand, width=2); head(X(0), y - 15)
    elif pose == 'header':
        leg(X(-1), y - 6, X(-3), y - 3); leg(X(1), y - 6, X(2), y - 3)
        d.polygon([(X(-3), y - 11), (X(2), y - 12), (X(3), y - 6), (X(-3), y - 6)], fill=sh); d.rectangle([min(X(-3), X(3)), y - 6, max(X(-3), X(3)), y - 4], fill=sho)
        d.line([(X(-3), y - 10), (X(-7), y - 8)], fill=hand, width=2); d.line([(X(3), y - 10), (X(7), y - 9)], fill=hand, width=2); head(X(3), y - 14)
    elif pose == 'dive':     # keeper / diving player, body horizontal, reaching forward
        d.line([(X(-9), y - 6), (X(-3), y - 8)], fill=SK, width=2); d.line([(X(-9), y - 6), (X(-11), y - 6)], fill=BOOT_, width=2)
        d.line([(X(-4), y - 8), (X(2), y - 9)], fill=sh, width=5); d.line([(X(-6), y - 8), (X(-4), y - 8)], fill=sho, width=4)
        d.line([(X(2), y - 10), (X(10), y - 14)], fill=hand, width=2); d.line([(X(1), y - 8), (X(9), y - 10)], fill=hand, width=2); head(X(4), y - 10)
        d.ellipse([X(9) - 1.5, y - 15, X(9) + 1.5, y - 12], fill=GLOVE if keeper else SK)
    elif pose == 'crouch':
        d.line([(X(-1), y - 3), (X(3), y - 4), (X(3), y - 1)], fill=SK, width=2); d.line([(X(-1), y - 3), (X(-4), y - 1)], fill=SK, width=2)
        d.polygon([(X(-4), y - 8), (X(1), y - 9), (X(2), y - 4), (X(-4), y - 4)], fill=sh); d.line([(X(-1), y - 7), (X(4), y - 5)], fill=hand, width=2); head(X(2), y - 11)
    elif pose == 'arms_up':
        leg(X(-1.2), y - 4, X(-1.5), y - 1); leg(X(1.4), y - 4, X(1.6), y - 1)
        d.rectangle([min(X(-3), X(3)), y - 10, max(X(-3), X(3)), y - 5], fill=sh); d.rectangle([min(X(-3), X(3)), y - 5, max(X(-3), X(3)), y - 3], fill=sho)
        d.line([(X(-3), y - 9), (X(-6), y - 15)], fill=hand, width=2); d.line([(X(3), y - 9), (X(6), y - 15)], fill=hand, width=2); head(X(0), y - 13)
    elif pose == 'wide':     # legs apart (for nutmeg / dummy)
        leg(X(-3.5), y - 4, X(-4.5), y - 1); leg(X(3.5), y - 4, X(4.5), y - 1)
        d.rectangle([min(X(-3), X(3)), y - 10, max(X(-3), X(3)), y - 5], fill=sh); d.rectangle([min(X(-4), X(4)), y - 5, max(X(-4), X(4)), y - 3], fill=sho)
        d.line([(X(-3.5), y - 9), (X(-7), y - 6)], fill=hand, width=2); d.line([(X(3.5), y - 9), (X(7), y - 6)], fill=hand, width=2); head(X(0), y - 13)
    elif pose == 'turn':     # back to us, arms out (holding off / shielding)
        leg(X(-1.2), y - 4, X(-1.2), y - 1); leg(X(1.4), y - 4, X(1.4), y - 1)
        d.rectangle([min(X(-3), X(3)), y - 10, max(X(-3), X(3)), y - 5], fill=sh); d.rectangle([min(X(-3), X(3)), y - 5, max(X(-3), X(3)), y - 3], fill=sho)
        d.line([(X(-3), y - 9), (X(-7), y - 8)], fill=hand, width=2); d.line([(X(3), y - 9), (X(7), y - 8)], fill=hand, width=2)
        d.ellipse([X(0) - 2.5, y - 15.5, X(0) + 2.5, y - 10.5], fill=hair + (255,))
    lay(a, m)


def arrow(a, p0, p1, col, w=2, head=4, alpha=255):
    d = ImageDraw.Draw(a); c = tuple(col[:3]) + (alpha,)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) or 1; ux, uy = dx / L, dy / L
    d.line([p0, (p1[0] - ux * head * 0.6, p1[1] - uy * head * 0.6)], fill=c, width=w)
    d.polygon([p1, (p1[0] - ux * head + uy * head * 0.6, p1[1] - uy * head - ux * head * 0.6), (p1[0] - ux * head - uy * head * 0.6, p1[1] - uy * head + ux * head * 0.6)], fill=c)


def carrow(a, pts, col, w=2, head=4, dashed=False):
    d = ImageDraw.Draw(a); c = tuple(col[:3]) + (255,)
    for i in range(len(pts) - 1):
        if dashed and (i // 2) % 2: continue
        d.line([pts[i], pts[i + 1]], fill=c, width=w)
    arrow(a, pts[-4] if len(pts) > 4 else pts[0], pts[-1], col, w=w, head=head)


def dots(a, pts, col, every=2, r=1.0):
    d = ImageDraw.Draw(a)
    for i, (x, y) in enumerate(pts):
        if (i // every) % 2 == 0: disc(d, x, y, r, tuple(col[:3]) + (255,))


def clock(a, x, y, r=7, hand=0.25, col=(255, 255, 255)):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(236, 240, 252, 255)); ang = -math.pi / 2 + hand * 2 * math.pi
    d.line([(x, y), (x + math.cos(ang) * (r - 2), y + math.sin(ang) * (r - 2))], fill=(30, 32, 60, 255), width=1); d.line([(x, y), (x, y - r + 3)], fill=(30, 32, 60, 255))
    for k in range(4):
        t = k * math.pi / 2; d.point((int(x + math.cos(t) * (r - 1)), int(y + math.sin(t) * (r - 1))), (120, 126, 160, 255))
    lay(a, m)


def eye(a, x, y, w=11, col=(120, 210, 255), slash=False):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m); h = w // 3 + 1
    d.polygon([(x - w, y), (x, y - h - 1), (x + w, y), (x, y + h + 1)], fill=(244, 246, 252, 255)); disc(d, x, y, h - 0.5, tuple(col) + (255,)); disc(d, x, y, 1.6, (20, 22, 40, 255)); d.point((x - 1, y - 1), (255, 255, 255, 255))
    lay(a, m)
    if slash: ImageDraw.Draw(a).line([(x - w, y + h + 1), (x + w, y - h - 1)], fill=(236, 84, 76, 255), width=2)


def heart(a, x, y, r=6, col=(236, 84, 100)):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.ellipse([x - r, y - r * 0.9, x, y + r * 0.1], fill=col + (255,)); d.ellipse([x, y - r * 0.9, x + r, y + r * 0.1], fill=col + (255,))
    d.polygon([(x - r, y - r * 0.3), (x + r, y - r * 0.3), (x, y + r)], fill=col + (255,)); d.ellipse([x - r * 0.7, y - r * 0.7, x - r * 0.3, y - r * 0.4], fill=(255, 200, 210, 255))
    lay(a, m)


def battery(a, x, y, level=0.7, col=(96, 220, 120), w=18, h=10):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.rectangle([x - w // 2, y - h // 2, x + w // 2, y + h // 2], fill=(40, 44, 70, 255)); d.rectangle([x + w // 2 + 1, y - 2, x + w // 2 + 3, y + 2], fill=(190, 196, 220, 255))
    d.rectangle([x - w // 2 + 1, y - h // 2 + 1, x - w // 2 + 1 + int((w - 2) * level), y + h // 2 - 1], fill=col + (255,))
    lay(a, m)


def flag(a, x, y, col=(250, 210, 60), h=14):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.line([(x, y), (x, y - h)], fill=(220, 224, 240, 255), width=2); d.polygon([(x, y - h), (x + 8, y - h + 3), (x, y - h + 6)], fill=tuple(col) + (255,))
    lay(a, m)


def boot(a, x, y, f=1, col=(236, 240, 252), accent=(240, 140, 60)):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m); X = lambda dx: x + f * dx
    d.polygon([(X(-6), y - 8), (X(-1), y - 8), (X(0), y - 3), (X(8), y - 2), (X(9), y + 1), (X(-6), y + 1)], fill=tuple(col) + (255,))
    d.rectangle([min(X(-6), X(9)), y + 1, max(X(-6), X(9)), y + 2], fill=(40, 44, 70, 255)); d.line([(X(2), y - 3), (X(5), y - 1)], fill=tuple(accent) + (255,), width=1)
    for k in (-4, 0, 4): d.rectangle([X(k) - 0.5, y + 2, X(k) + 0.5, y + 3], fill=(40, 44, 70, 255))
    lay(a, m)


def cone(a, x, y, col=(255, 140, 60)):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.polygon([(x, y - 7), (x - 4, y), (x + 4, y)], fill=col + (255,)); d.line([(x - 2, y - 3), (x + 2, y - 3)], fill=(255, 255, 255, 255)); lay(a, m)


def card_icon(a, x, y, col=(250, 210, 60)):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m); d.rectangle([x - 3, y - 5, x + 3, y + 4], fill=col + (255,)); lay(a, m)


def check(a, x, y, col=(96, 220, 120), s=1.0):
    d = ImageDraw.Draw(a); d.line([(x - 5 * s, y), (x - 1 * s, y + 4 * s), (x + 6 * s, y - 5 * s)], fill=col + (255,), width=3)


def cross_mark(a, x, y, col=(236, 84, 76), s=1.0):
    d = ImageDraw.Draw(a); d.line([(x - 4 * s, y - 4 * s), (x + 4 * s, y + 4 * s)], fill=col + (255,), width=3); d.line([(x - 4 * s, y + 4 * s), (x + 4 * s, y - 4 * s)], fill=col + (255,), width=3)


def circ_arrows(a, x, y, r, col, parts=2, gap=40):
    d = ImageDraw.Draw(a)
    for k in range(parts):
        s = k * 360 / parts + gap / 2; e = (k + 1) * 360 / parts - gap / 2
        d.arc([x - r, y - r, x + r, y + r], s, e, fill=tuple(col[:3]) + (255,), width=2)
        t = math.radians(e); px, py = x + math.cos(t) * r, y + math.sin(t) * r; tx, ty = -math.sin(t), math.cos(t)
        d.polygon([(px + tx * 4, py + ty * 4), (px - ty * 3, py + tx * 3), (px + ty * 3, py - tx * 3)], fill=tuple(col[:3]) + (255,))


def chevrons(a, x, y, col, n=3, f=1, s=4):
    d = ImageDraw.Draw(a)
    for i in range(n):
        xx = x + f * i * (s + 2); d.line([(xx, y - s), (xx + f * s, y), (xx, y + s)], fill=tuple(col[:3]) + (255 - i * 50,), width=2)


def chain(a, x, y, n=3, col=(220, 226, 245)):
    d = ImageDraw.Draw(a)
    for i in range(n):
        cx = x + i * 7; d.ellipse([cx - 4, y - 3, cx + 3, y + 3], outline=tuple(col) + (255,), width=2)


def note(a, x, y, col=(255, 255, 255)):
    d = ImageDraw.Draw(a); d.ellipse([x - 3, y, x + 1, y + 3], fill=col + (255,)); d.line([(x + 1, y + 1), (x + 1, y - 7)], fill=col + (255,)); d.line([(x + 1, y - 7), (x + 4, y - 5)], fill=col + (255,))


def drop(a, x, y, col=(120, 200, 255)):
    d = ImageDraw.Draw(a); d.polygon([(x, y - 5), (x - 3, y), (x + 3, y)], fill=col + (255,)); d.ellipse([x - 3, y - 2, x + 3, y + 3], fill=col + (255,))


def snow(a, x, y, r=7, col=(190, 230, 255)):
    d = ImageDraw.Draw(a)
    for k in range(3):
        t = k * math.pi / 3; d.line([(x - math.cos(t) * r, y - math.sin(t) * r), (x + math.cos(t) * r, y + math.sin(t) * r)], fill=tuple(col) + (255,), width=1)
    disc(d, x, y, 1.5, (255, 255, 255, 255))


def target(a, x, y, r=8, col=(236, 84, 76)):
    d = ImageDraw.Draw(a)
    for i, rr in enumerate((r, r * 0.66, r * 0.33)): d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(col if i % 2 == 0 else (255, 255, 255)) + (255,), width=2)
    d.line([(x - r - 2, y), (x + r + 2, y)], fill=col + (200,)); d.line([(x, y - r - 2), (x, y + r + 2)], fill=col + (200,))


def sun(a, x, y, r=5, col=(255, 220, 90)):
    d = ImageDraw.Draw(a); disc(d, x, y, r, col + (255,))
    for k in range(8):
        t = k * math.pi / 4; d.line([(x + math.cos(t) * (r + 2), y + math.sin(t) * (r + 2)), (x + math.cos(t) * (r + 5), y + math.sin(t) * (r + 5))], fill=col + (255,))


def hourglass(a, x, y, col=(255, 220, 120)):
    m = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.polygon([(x - 5, y - 8), (x + 5, y - 8), (x, y), (x + 5, y + 8), (x - 5, y + 8), (x, y)], fill=(230, 236, 250, 255)); d.polygon([(x - 3, y + 7), (x + 3, y + 7), (x, y + 3)], fill=col + (255,))
    d.line([(x - 6, y - 8), (x + 6, y - 8)], fill=(120, 126, 160, 255), width=2); d.line([(x - 6, y + 8), (x + 6, y + 8)], fill=(120, 126, 160, 255), width=2); lay(a, m)
