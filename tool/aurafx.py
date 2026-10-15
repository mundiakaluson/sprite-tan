"""SUPPORT card effects: one punchy, distinct effect per card (data/support_auras.csv, column `shape` = effect key).
Drawn on a 72x72 canvas around the player (PAD px of margin around the 40x40 sprite cell); feet at (CX, FY). The game draws the same shapes.
Timeline per card: a short CAST burst (age 0-9), the sustained effect for duration_s, a fade-out, then a rest before it loops. 1 tick = 70 ms."""
import math, random
import numpy as np
from PIL import Image, ImageDraw

W = H = 72; PAD = 16; CX = 36; FY = 47; BY = 33; HY = 20
REST = 16


def _rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lighten(c, k=0.5): return tuple(int(v + (255 - v) * k) for v in c)
def darken(c, k=0.5): return tuple(int(v * (1 - k)) for v in c)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))


class Ly:
    def __init__(s): s.im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)

    def glow(s, x, y, rx, ry, col, a):
        if a <= 0.01: return
        yy, xx = np.mgrid[0:H, 0:W]; d = np.sqrt(((xx - x) / max(rx, .5)) ** 2 + ((yy - y) / max(ry, .5)) ** 2)
        al = np.clip(1 - d, 0, 1) ** 1.5 * a; im = np.zeros((H, W, 4), np.uint8); im[..., :3] = col; im[..., 3] = (np.clip(al, 0, 1) * 255).astype(np.uint8)
        s.im.alpha_composite(Image.fromarray(im, 'RGBA'))

    def ring(s, x, y, rx, ry, col, a=1.0, w=1):
        if a <= 0.02 or rx < 0.6: return
        s.d.ellipse([x - rx, y - max(ry, 0.6), x + rx, y + max(ry, 0.6)], outline=col + (int(255 * clamp(a)),), width=w)

    def fill(s, x, y, rx, ry, col, a=1.0):
        if a <= 0.02: return
        s.d.ellipse([x - max(rx, .6), y - max(ry, .6), x + max(rx, .6), y + max(ry, .6)], fill=col + (int(255 * clamp(a)),))

    def px(s, x, y, col, a=1.0, r=0):
        if a <= 0.02: return
        s.d.rectangle([int(round(x)) - r, int(round(y)) - r, int(round(x)) + r, int(round(y)) + r], fill=col + (int(255 * clamp(a)),))

    def line(s, pts, col, a=1.0, w=1):
        if a > 0.02: s.d.line([(float(x), float(y)) for x, y in pts], fill=col + (int(255 * clamp(a)),), width=w)

    def poly(s, pts, col, a=1.0):
        if a > 0.02: s.d.polygon([(float(x), float(y)) for x, y in pts], fill=col + (int(255 * clamp(a)),))

    def spark(s, x, y, r, col, a=1.0):
        r = max(1, int(round(r))); s.line([(x - r, y), (x + r, y)], col, a); s.line([(x, y - r), (x, y + r)], col, a)
        s.px(x, y, (255, 255, 255), a)

    def chev(s, x, y, w, col, a=1.0, up=True):
        k = -1 if up else 1; s.line([(x - w, y - k * w * 0.8), (x, y), (x + w, y - k * w * 0.8)], col, a)

    def note(s, x, y, col, a=1.0):
        s.fill(x, y, 1.6, 1.2, col, a); s.line([(x + 1.5, y), (x + 1.5, y - 5)], col, a); s.line([(x + 1.5, y - 5), (x + 3.5, y - 3.5)], col, a)


class F:
    """per-frame context handed to an effect"""
    def __init__(s, a, e, dur, col, r):
        s.a = a; s.e = e; s.dur = dur; s.p = clamp(a / max(1, dur)); s.col = col; s.lt = lighten(col, .55); s.dk = darken(col, .45); s.row = r
        s.under = Ly(); s.over = Ly(); s.scope = r['scope']

    def rnd(s, *k): return random.Random(hash(k) & 0xffffff)

    def cyc(s, n, life, off=0.0):
        """n looping particles: yields (k, u 0..1 through its life, rng seeded per k and per loop)"""
        for k in range(n):
            x = s.a / life + k / n + off; yield k, x % 1.0, random.Random(k * 977 + int(x) * 31 + 7)

    def cast(s, big=24, a=1.0, col=None):
        c = col or s.col
        if s.a < 10:
            u = s.a / 10.0; s.over.ring(CX, FY, 3 + big * u, (3 + big * u) * 0.4, c, (1 - u) * a, 2); s.under.ring(CX, FY, 2 + big * 0.7 * u, (2 + big * 0.7 * u) * 0.4, s.lt, (1 - u) * a)
        if s.a < 4: s.under.glow(CX, BY, 16, 20, s.lt, (1 - s.a / 4) * 0.9 * a)

    def ghost(s, x, y, a=1.0, col=None):
        """another player's marker (teammate / runner / opponent): a small translucent figure on a ground ring"""
        c = col or s.col; s.under.ring(x, y, 5, 2, c, .9 * a); s.under.glow(x, y - 8, 6, 11, c, .35 * a)
        s.under.fill(x, y - 17, 2.2, 2.2, c, .65 * a); s.under.poly([(x - 2.5, y - 14), (x + 2.5, y - 14), (x + 2, y - 7), (x - 2, y - 7)], c, .65 * a)
        s.under.line([(x - 1, y - 7), (x - 1.5, y - 1)], c, .65 * a); s.under.line([(x + 1, y - 7), (x + 1.5, y - 1)], c, .65 * a)


EFFECTS = {}
def fx(name):
    def deco(f): EFFECTS[name] = f; return f
    return deco


# ---------------------------------------------------------------------------------------------------------------------- self buffs
@fx('tiger')
def _tiger(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, 40, 13, 9, F.col, 0.7 * e)
    for k in range(3):                                                                        # claw-mark stripes flashing across the legs
        if ((a + k * 2) // 3) % 4 < 2:
            x = CX - 8 + k * 5; O.line([(x, 34), (x + 5, 46)], (60, 20, 0), 0.8 * e, 2); O.line([(x + 1, 34), (x + 6, 46)], F.lt, 0.9 * e, 1)
    for k, u, r in F.cyc(8, 9):                                                                  # flames licking up the shins
        x = CX + r.uniform(-8, 8); O.px(x + math.sin(u * 6 + k) * 1.5, 45 - u * 15, F.lt if u < .5 else F.col, (1 - u) * e)
    if a < 8:                                                                                  # roar: three big slashes + shockwave
        u = a / 8.0
        for k in range(3): O.line([(CX - 14 + k * 7, 16 + u * 6), (CX - 2 + k * 7, 44 - (1 - u) * 6)], (255, 255, 230), (1 - u), 2)
    F.cast(26)


@fx('leap')
def _leap(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, FY, 14, 5, F.col, 0.6 * e)
    for k, u, r in F.cyc(7, 10):                                                                 # spring chevrons shoot up
        x = CX + (k - 3) * 3.4; O.chev(x, 46 - u * 24, 3, F.lt if k % 2 else F.col, (1 - u) * e)
    for k, u, r in F.cyc(6, 12):                                                                 # dust kicked out at the feet
        s = -1 if k % 2 else 1; U.fill(CX + s * (4 + u * 12), FY - u * 3, 1.5 + u, 1 + u * .5, (230, 225, 200), (1 - u) * .5 * e)
    if a < 6: O.line([(CX, FY), (CX, FY - 40 * (1 - a / 6))], (255, 255, 220), 1 - a / 6, 3)
    F.cast(28)


@fx('muscle')
def _muscle(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 15, 20, F.col, 0.55 * e)
    for k in range(14):                                                                          # jagged power spikes round the whole body
        ang = k / 14 * 2 * math.pi; L = 4 + 4 * abs(math.sin(a * 0.55 + k * 1.9)); x0, y0 = CX + math.cos(ang) * 13, BY + math.sin(ang) * 19
        O.poly([(x0 - math.sin(ang) * 1.6, y0 + math.cos(ang) * 1.6), (x0 + math.cos(ang) * L, y0 + math.sin(ang) * L), (x0 + math.sin(ang) * 1.6, y0 - math.cos(ang) * 1.6)], F.col if k % 2 else F.lt, .9 * e)
    b = (a % 8) / 8.0                                                                           # a heartbeat pump
    O.ring(CX, BY, 6 + 12 * b, 8 + 16 * b, F.lt, (1 - b) * e, 2)
    for k, u, r in F.cyc(5, 10):
        s = -1 if k % 2 else 1; O.chev(CX + s * (8 + r.uniform(0, 3)), 34 - u * 14, 2, F.lt, (1 - u) * e)
    F.cast(30)


@fx('boots')
def _boots(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, FY - 2, 11, 5, F.col, 0.65 * e)
    sw = (a % 14) / 14.0                                                                         # a glint sweeping across the boots
    O.line([(CX - 10 + sw * 20, 50), (CX - 4 + sw * 20, 42)], (255, 255, 240), e, 2)
    for k in range(4):
        ph = (a * 0.5 + k * 1.7) % 6; r = 1 + abs(3 - ph) * -0.4 + 2
        if ph < 3: O.spark(CX + (-5 if k % 2 else 5) + (k // 2) * 3 - 1, FY - 2 - (k % 2) * 3, 1 + ph * 0.8, F.lt, 1 - ph / 3 * .6)
    if a < 8:
        u = a / 8
        for k in range(8): ang = k * math.pi / 4; O.line([(CX + math.cos(ang) * 3, FY - 1 + math.sin(ang) * 2), (CX + math.cos(ang) * (4 + 20 * u), FY - 1 + math.sin(ang) * (2 + 8 * u))], F.lt, 1 - u)
    F.cast(20)


@fx('radar')
def _radar(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    R = 30; ry = 11
    U.fill(CX, FY, R, ry, darken(F.col, .8), .35 * e)
    for rr in (10, 20, 30): U.ring(CX, FY, rr, rr * ry / R, F.col, .55 * e)
    U.line([(CX - R, FY), (CX + R, FY)], F.col, .35 * e); U.line([(CX, FY - ry), (CX, FY + ry)], F.col, .35 * e)
    th = a * 0.32
    for k in range(10):                                                                           # sweep with a fading wedge
        t2 = th - k * 0.09; U.line([(CX, FY), (CX + math.cos(t2) * R, FY + math.sin(t2) * ry)], F.lt if k == 0 else F.col, (1 - k / 10) * .9 * e, 1)
    for k, (ba, br) in enumerate([(0.6, .5), (2.1, .8), (3.6, .6), (5.0, .9), (1.2, .85)]):         # blips light up as the beam passes
        age = ((th - ba) % (2 * math.pi)) / (2 * math.pi); x = CX + math.cos(ba) * R * br; y = FY + math.sin(ba) * ry * br
        if age < 0.6: O.fill(x, y, 1.6, 1.2, (255, 255, 255), (1 - age / .6) * e); U.ring(x, y, 3 + age * 5, 1.5 + age * 2, F.lt, (1 - age / .6) * .8 * e)
    F.cast(32)


@fx('calm')
def _calm(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, HY, 12, 12, F.lt, .6 * e); U.glow(CX, FY, 14, 5, F.col, .4 * e)
    for k in range(3):                                                                            # ripples spreading from the head
        u = ((a / 14.0) + k / 3) % 1; O.ring(CX, HY - 5, 4 + 14 * u, (4 + 14 * u) * .3, F.lt, (1 - u) * e, 1)
    for k, u, r in F.cyc(7, 18):                                                                  # cool droplets drifting down past the head
        O.px(CX + r.uniform(-12, 12), 8 + u * 36, F.lt, (1 - u) * .9 * e)
    F.cast(22)


@fx('wind')
def _wind(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 14, 20, F.col, .4 * e)
    for strand in (0, 1):                                                                         # a double helix of wind climbing the body
        for k in range(16):
            ang = a * 0.45 + k * 0.5 + strand * math.pi; y = 48 - k * 1.9; x = CX + math.cos(ang) * (11 - k * .25); z = math.sin(ang)
            (O if z > 0 else U).px(x, y, F.lt if k % 3 == 0 else F.col, (1 - k / 18) * e, 1 if z > 0 else 0)
    for k, u, r in F.cyc(5, 12):                                                                  # '+' restore marks rising
        x = CX + r.uniform(-12, 12); y = 46 - u * 30; O.line([(x - 1, y), (x + 1, y)], (255, 255, 255), (1 - u) * e); O.line([(x, y - 1), (x, y + 1)], (255, 255, 255), (1 - u) * e)
    F.cast(26)


@fx('streak')
def _streak(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 14, 20, F.col, .5 * e)
    for k in range(18):                                                                           # flames wrapped round the body
        x = CX - 13 + k * 26 / 17; h = 8 + 8 * abs(math.sin(a * .6 + k * 2.3)); base = 49 - abs(k - 8.5) * 0.4 - 4
        U.poly([(x - 2, base), (x + math.sin(a * .4 + k) * 1.6, base - h), (x + 2, base)], F.col, .85 * e)
        U.poly([(x - 1, base), (x + math.sin(a * .4 + k) * 1.2, base - h * .6), (x + 1, base)], F.lt, .9 * e)
    for k, u, r in F.cyc(8, 10):
        O.px(CX + r.uniform(-13, 13) + math.sin(u * 8) * 2, 44 - u * 30, (255, 230, 120), (1 - u) * e)
    F.cast(30, col=(255, 200, 60))


@fx('clock')
def _clock(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    for k in range(2):                                                                            # waves of time rolling across the pitch
        u = ((a / 16.0) + k * .5) % 1; rx = 4 + 31 * u; U.ring(CX, FY, rx, rx * .38, F.col, (1 - u) * e, 2)
        for t in range(12): ang = t * math.pi / 6; U.px(CX + math.cos(ang) * rx, FY + math.sin(ang) * rx * .38, F.lt, (1 - u) * e)
    for k, ang in enumerate([0.4, 1.5, 2.6, 3.7, 4.9, 5.8]):                                       # teammates flare as the wave reaches them
        x, y = CX + math.cos(ang) * 27, FY + math.sin(ang) * 10; u = ((a / 16.0) % 1) * 31 / 27
        hit = clamp(1 - abs(u - 1) * 4); F.ghost(x, y, .35 + .65 * hit); O.ring(x, y, 4 + 3 * hit, 2 + hit, F.lt, hit)
    cy = HY - 8; O.ring(CX, cy, 6, 6, F.lt, e, 1)                                                  # a clock above the head, hands winding backwards
    for h, sp in ((4.5, -0.5), (3, -0.08)): O.line([(CX, cy), (CX + math.sin(a * sp) * h, cy - math.cos(a * sp) * h)], (255, 255, 255), e)
    F.cast(34)


@fx('reset')
def _reset(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 14, 18, F.col, .4 * e)
    for rr, sg in ((15, 1), (9, -1)):                                                              # two circular arrows chasing each other
        th = a * 0.45 * sg; pts = [(CX + math.cos(th + k * .12 * sg) * rr, BY + math.sin(th + k * .12 * sg) * rr * 1.2) for k in range(0, 36)]
        for k in range(35): O.line([pts[k], pts[k + 1]], F.lt if k > 20 else F.col, (k / 35) * e, 2 if rr > 10 else 1)
        hx, hy = pts[-1]; O.px(hx, hy, (255, 255, 255), e, 1)
    if a < 5: U.glow(CX, BY, 22, 26, (255, 255, 255), (1 - a / 5) * .8)
    F.cast(26)


@fx('overdrive')
def _overdrive(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 16, 21, F.col, .5 * e)
    for k in range(3):                                                                            # electric crackle round the body
        r = random.Random(a // 2 * 7 + k); x, y = CX + r.uniform(-14, 14), 12; pts = [(x, y)]
        for _ in range(6): x += r.uniform(-6, 6); y += 7; pts.append((x, y))
        O.line(pts, F.lt, e, 1)
    for k in range(14):                                                                           # speed lines blasting outward
        ang = k * 2 * math.pi / 14 + .2; u = ((a * .12) + k * .37) % 1; r0 = 8 + u * 22; O.line([(CX + math.cos(ang) * r0, BY + math.sin(ang) * r0), (CX + math.cos(ang) * (r0 + 5), BY + math.sin(ang) * (r0 + 5))], F.col, (1 - u) * e)
    for k in range(2):
        u = ((a / 8.0) + k * .5) % 1; U.ring(CX, FY, 4 + 30 * u, (4 + 30 * u) * .4, F.col, (1 - u) * e, 2)
    for k, ang in enumerate([0.4, 1.5, 2.6, 3.7, 4.9, 5.8]): x, y = CX + math.cos(ang) * 27, FY + math.sin(ang) * 10; F.ghost(x, y, .5); O.line([(x, y - 14), (x + 2, y - 10), (x - 1, y - 8), (x + 1, y - 4)], F.lt, (a % 4 < 2) * e)
    F.cast(34)


@fx('chain')
def _chain(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 14, 18, F.col, .35 * e); n = 8 + min(2, int(a // 4)) if a < 12 else 10                  # a link is added on cast: the chain grows
    for k in range(n):
        ang = a * 0.22 + k * 2 * math.pi / n; x = CX + math.cos(ang) * 14; y = BY + 4 + math.sin(ang) * 5; z = math.sin(ang)
        (O if z > 0 else U).fill(x, y, 2.6, 1.8, F.lt if k % 2 else F.col, e); (O if z > 0 else U).fill(x, y, 1.0, .6, darken(F.col, .6), e * .8)
    for k in range(n):                                                                            # the second chain, tilted
        ang = -a * 0.2 + k * 2 * math.pi / n; x = CX + math.sin(ang) * 6; y = BY - 2 + math.cos(ang) * 15; z = math.cos(ang)
        (O if z < 0 else U).fill(x, y, 1.7, 2.4, F.col, e * .9)
    if a % 6 < 2: O.spark(CX + 14 * math.cos(a * .22), BY + 4 + 5 * math.sin(a * .22), 3, (255, 255, 255), e)
    F.cast(26)


@fx('stamina')
def _stamina(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    beat = 0.5 + 0.5 * math.sin(a * .5); U.glow(CX, BY - 4, 12 + 3 * beat, 14 + 3 * beat, F.col, (.35 + .3 * beat) * e)
    for k, u, r in F.cyc(4, 14):                                                                  # rings climbing from the boots to the head
        O.ring(CX, 49 - u * 32, 11 - u * 3, 3.6 - u, F.lt if k % 2 else F.col, (1 - u) * e, 1)
    for k, u, r in F.cyc(7, 11):
        O.px(CX + r.uniform(-9, 9), 46 - u * 28, (255, 255, 255), (1 - u) * e)
    U.ring(CX, FY, 9 + 3 * beat, 3.5 + beat, F.col, .8 * e, 2)
    F.cast(26)


@fx('hands')
def _hands(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    for s in (-1, 1):
        x, y = CX + s * 9, BY + 5; k = (a % 12) / 12.0
        U.glow(x, y, 7, 7, F.col, .7 * e); O.ring(x, y, 9 - 5 * k, 9 - 5 * k, F.lt, (.4 + .6 * k) * e)
        for q in range(4): ang = q * math.pi / 2 + math.pi / 4; O.px(x + math.cos(ang) * (7 + 3 * (1 - k)), y + math.sin(ang) * (7 + 3 * (1 - k)), (255, 255, 255), e)
    F.cast(22)


@fx('shield')
def _shield(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    pul = .5 + .5 * math.sin(a * .35); U.glow(CX, BY, 15, 21, F.col, .45 * e)
    O.ring(CX, BY, 14 + pul, 20 + pul, F.col, .9 * e, 2)                                          # a bubble the shoulder charge bounces off
    sc = 1 + clamp(1 - a / 6) * 1.2; sh = [(CX - 6 * sc, BY - 8 * sc), (CX + 6 * sc, BY - 8 * sc), (CX + 6 * sc, BY - 1 * sc), (CX, BY + 7 * sc), (CX - 6 * sc, BY - 1 * sc)]
    U.poly(sh, F.col, .35 * e); O.line(sh + [sh[0]], F.lt, .9 * e, 1)
    for k, u, r in F.cyc(5, 9):
        O.spark(CX + r.uniform(-14, 14), BY + r.uniform(-18, 18), 1 + u * 2, (255, 255, 230), (1 - u) * e)
    F.cast(26)


@fx('frost')
def _frost(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    g = clamp(a / 8.0)
    U.glow(CX, FY, 18, 6, F.lt, .5 * e); U.fill(CX, FY, 15 * g, 5 * g, F.lt, .35 * e)
    for k in range(12):                                                                           # ice spikes grow in a ring
        ang = k / 12 * 2 * math.pi; x = CX + math.cos(ang) * 14; y = FY + math.sin(ang) * 5; h = (5 + 4 * ((k * 7) % 3)) * g
        (O if math.sin(ang) > 0 else U).poly([(x - 2, y), (x, y - h), (x + 2, y)], F.lt if k % 2 else (230, 250, 255), .95 * e)
    for k, u, r in F.cyc(6, 16):                                                                  # snowflakes
        x = CX + r.uniform(-14, 14) + math.sin(u * 7 + k) * 2; y = 12 + u * 38; O.spark(x, y, 1, (230, 250, 255), (1 - u * .5) * e)
    F.cast(26)


@fx('rhythm')
def _rhythm(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, FY, 16, 6, F.col, .4 * e); beat = (a % 7) / 7.0; U.ring(CX, FY, 6 + 22 * beat, (6 + 22 * beat) * .38, F.col, (1 - beat) * e, 2)
    for k in range(7):                                                                            # equaliser bars at the player's feet
        h = 2 + 7 * abs(math.sin(a * .6 + k * 1.3)); x = CX - 12 + k * 4; U.d.rectangle([x - 1, FY + 10 - h * .8, x + 1, FY + 10], fill=(F.lt if k % 2 else F.col) + (int(230 * e),))
    for k, u, r in F.cyc(4, 16):                                                                  # music notes float off
        s = -1 if k % 2 else 1; O.note(CX + s * (8 + u * 12) + math.sin(u * 9 + k) * 2, 38 - u * 26, F.lt if k % 2 else (255, 255, 255), (1 - u) * e)
    F.cast(26)


@fx('surge')
def _surge(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 14, 20, F.col, .45 * e)
    for k in range(16):                                                                           # wind tearing past, left to right
        r = random.Random(k * 13); y = 10 + r.uniform(0, 44); L = 9 + r.uniform(0, 12); x = ((a * (4 + r.uniform(0, 3)) + r.uniform(0, 80)) % (W + 2 * L)) - L
        (O if abs(y - BY) > 4 else U).line([(x - L, y), (x, y)], F.lt if k % 3 == 0 else F.col, (.5 + .5 * r.random()) * e)
    for k, u, r in F.cyc(5, 8): U.ring(CX - u * 16, FY, 3 + u * 6, 1.5 + u * 2, F.col, (1 - u) * e)
    F.cast(30)


@fx('fresh')
def _fresh(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, 40, 12, 10, F.col, .5 * e)
    u = (a % 12) / 12.0; y = 48 - u * 20                                                         # a bright band washes up the legs
    O.line([(CX - 9, y), (CX + 9, y)], (240, 255, 245), (1 - u * .5) * e, 2); O.line([(CX - 9, y + 3), (CX + 9, y + 3)], F.lt, (1 - u) * e)
    for k, u2, r in F.cyc(8, 10): O.px(CX + r.uniform(-9, 9), 48 - u2 * 24, F.lt, (1 - u2) * e, 1 if k % 3 == 0 else 0)
    for k, u2, r in F.cyc(3, 12):
        x = CX + r.uniform(-10, 10); y2 = 44 - u2 * 18; O.line([(x - 1, y2), (x + 1, y2)], (255, 255, 255), (1 - u2) * e); O.line([(x, y2 - 1), (x, y2 + 1)], (255, 255, 255), (1 - u2) * e)
    F.cast(24)


@fx('warm')
def _warm(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    for k, (x, y) in enumerate([(CX - 3, 44), (CX + 3, 44), (CX - 3, 39), (CX + 3, 39), (CX - 7, 28), (CX + 7, 28), (CX, 21)]):    # joint after joint heats up
        ph = (a * .3 - k * .6) % 4; g = clamp(1 - ph / 4)
        U.glow(x, y, 6 + 3 * g, 6 + 3 * g, F.col, .8 * g * e); O.px(x, y, F.lt, g * e, 1)
    for k, u, r in F.cyc(5, 14):                                                                  # steam
        x = CX + r.uniform(-9, 9) + math.sin(u * 6 + k) * 2; O.line([(x, 34 - u * 20), (x + math.sin(u * 8) * 1.5, 31 - u * 20)], (255, 235, 200), (1 - u) * .8 * e)
    U.ring(CX, FY, 10 + 2 * math.sin(a * .4), 4, F.col, .8 * e, 1)
    F.cast(22)


@fx('memory')
def _memory(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    N = [(CX, HY - 1), (CX - 7, 27), (CX + 7, 27), (CX - 10, 36), (CX + 10, 36), (CX, 33), (CX - 4, 40), (CX + 4, 40), (CX - 4, 49), (CX + 4, 49)]
    E = [(0, 1), (0, 2), (1, 3), (2, 4), (1, 5), (2, 5), (0, 5), (5, 6), (5, 7), (6, 8), (7, 9)]
    U.glow(CX, BY, 14, 18, F.col, .3 * e)
    for i, j in E: O.line([N[i], N[j]], F.col, .6 * e)
    for n, (x, y) in enumerate(N): O.fill(x, y, 1.6, 1.6, F.lt, .9 * e)
    for k, (i, j) in enumerate(E):                                                                 # signals racing along the web
        u = ((a / 10.0) + k * .17) % 1; O.px(N[i][0] + (N[j][0] - N[i][0]) * u, N[i][1] + (N[j][1] - N[i][1]) * u, (255, 255, 255), e, 1)
    for k in range(2):
        u = ((a / 14.0) + k * .5) % 1; O.ring(CX, BY, 6 + 14 * u, 8 + 18 * u, F.lt, (1 - u) * .7 * e)
    F.cast(26)


@fx('two_touch')
def _twotouch(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    c = a % 10
    for n, t0 in enumerate((0, 5)):                                                                # two taps, two rings, two sparks
        age = c - t0
        if 0 <= age < 5:
            u = age / 5.0; O.ring(CX + (-5 if n == 0 else 5), FY, 3 + 14 * u, (3 + 14 * u) * .4, F.col if n == 0 else F.lt, (1 - u) * e, 2)
            for q in range(6): ang = q * math.pi / 3 + n; O.px(CX + (-5 if n == 0 else 5) + math.cos(ang) * (2 + 9 * u), FY + math.sin(ang) * (1 + 4 * u) - 3 * u, F.lt, (1 - u) * e)
    for n, t0 in enumerate((0, 5)):                                                                # the touch counter above the head
        on = c >= t0; O.fill(CX - 5 + n * 10, HY - 9, 2.6, 2.6, F.col if on else darken(F.col, .75), .95 * e if on else .6 * e); O.ring(CX - 5 + n * 10, HY - 9, 3.2, 3.2, F.lt, e)
    U.glow(CX, FY - 2, 12, 5, F.col, .5 * e)
    F.cast(24)


@fx('battle')
def _battle(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 15, 20, F.col, .45 * e); g = clamp(a / 6.0)
    for k in range(7):                                                                            # cracks spreading out of the turf
        r = random.Random(k * 31); ang = k / 7 * 2 * math.pi + .2; x, y = CX, FY; pts = [(x, y)]
        for q in range(5): ang += r.uniform(-.4, .4); x += math.cos(ang) * 4.2 * g; y += math.sin(ang) * 1.7 * g; pts.append((x, y))
        U.line(pts, (70, 20, 20), .9 * e, 1)
    for s in (-1, 1):                                                                             # shoulder spikes
        for k in range(3): x = CX + s * (6 + k * 2.2); y = 27 - k * 1.5; O.poly([(x - 1.5, y + 3), (x + s * 1.5, y - 5 - k), (x + 1.5, y + 3)], F.lt if k == 1 else F.col, .9 * e)
    for k, u, r in F.cyc(6, 9): O.px(CX + r.uniform(-12, 12), 46 - u * 30, (255, 200, 120), (1 - u) * e)
    O.ring(CX, BY, 15, 21, F.col, (.4 + .5 * (a % 6 < 3)) * e)
    F.cast(28)


@fx('clean')
def _clean(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 14, 19, (255, 255, 255), .4 * e); u = (a % 12) / 12.0; y = 50 - u * 34
    O.line([(CX - 13, y), (CX + 13, y)], (255, 255, 255), e, 2); U.glow(CX, y, 14, 4, (255, 255, 255), .7 * e)
    for k, u2, r in F.cyc(9, 9):                                                                  # grime flicked off to the sides
        s = -1 if k % 2 else 1; O.px(CX + s * (5 + u2 * 15), 40 - u2 * 10 + r.uniform(-8, 8), (90, 80, 70) if k % 3 else (140, 40, 40), (1 - u2) * e)
    for k, u2, r in F.cyc(4, 8): O.spark(CX + r.uniform(-10, 10), 22 + r.uniform(0, 26), 1 + u2 * 2, (255, 255, 255), (1 - u2) * e)
    if a < 8: O.ring(CX, BY, 4 + 30 * a / 8, 6 + 38 * a / 8, (255, 255, 255), 1 - a / 8, 3)
    F.cast(30, col=(255, 255, 255))


@fx('warp')
def _warp(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    for s in (-1, 1):                                                                             # a portal ring at each boot
        x = CX + s * 4; ph = a * .3 + (0 if s < 0 else 1.5); w = abs(math.cos(ph)) * 3 + .8
        U.glow(x, FY, 7, 6, F.col, .7 * e); O.ring(x, FY - 1, w, 6, F.lt, e, 1); O.ring(x, FY - 1, w * .6, 4, (255, 255, 255), e, 1)
    for k in range(12):                                                                           # warp lines falling into the boots
        r = random.Random(k * 17); x = CX + r.uniform(-12, 12); u = ((a * .2) + r.random()) % 1; O.line([(x, 6 + u * 36), (x * .1 + CX * .9, 14 + u * 36)], F.lt if k % 3 == 0 else F.col, (1 - u) * e)
    for s in (-1, 1):                                                                             # electric crackle at the ankles
        r = random.Random(a // 2 * 5 + s); x, y = CX + s * 4, FY - 1; pts = [(x, y)]
        for _ in range(4): x += r.uniform(-3, 3); y -= 3; pts.append((x, y))
        O.line(pts, (255, 255, 255), e)
    if a < 6: O.line([(CX, FY), (CX, FY - 46 * (1 - a / 6))], (255, 255, 255), 1 - a / 6, 4)
    F.cast(32)


# ---------------------------------------------------------------------------------------------------------------------- aimed at others
@fx('beacon')                                      # SP19 Wide Open: calls the runner free
def _beacon(F):
    a, e, U, O = F.a, F.e, F.under, F.over; TX, TY = 55, 47
    U.d.rectangle([TX - 2, TY - 34, TX + 2, TY], fill=F.lt + (int(55 * e),)); F.ghost(TX, TY, e)
    for k in range(10):                                                                           # dashes racing from the caller to the runner
        u = ((a * .08) + k / 10) % 1; x = CX + 6 + (TX - CX - 6) * u; y = BY + 8 + (TY - BY - 8) * u - math.sin(u * math.pi) * 2; O.px(x, y, F.lt, e, 1)
    for k in range(3): u = ((a * .15) + k / 3) % 1; O.chev(TX - 14 + u * 10, TY - 22, 3, F.col, (1 - abs(u - .5) * 2) * e, up=False)
    for k in range(3): u = ((a / 9.0) + k / 3) % 1; O.ring(TX, TY, 3 + 9 * u, (3 + 9 * u) * .4, F.lt, (1 - u) * e)
    F.cast(18)


@fx('orders')                                      # SP21 Captain's Orders: two teammates locked on
def _orders(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    for TX in (13, 59):
        F.ghost(TX, 47, e); k = (a % 12) / 12.0
        for sx in (-1, 1):
            for sy in (-1, 1):
                O.line([(TX + sx * (11 - 4 * k), 40 + sy * (11 - 4 * k)), (TX + sx * (11 - 4 * k) - sx * 3, 40 + sy * (11 - 4 * k)), (TX + sx * (11 - 4 * k), 40 + sy * (11 - 4 * k) - sy * 3)], F.lt, e)
        for q in range(8): u = ((a * .09) + q / 8) % 1; O.px(CX + (TX - CX) * u, BY + 8 + (46 - BY - 8) * u, F.lt, e)
    for k in range(3): O.chev(CX, HY - 10 + k * 3, 5, F.lt if k else (255, 255, 255), e, up=True)  # captain's stripes
    U.glow(CX, BY, 13, 19, F.col, .35 * e)
    F.cast(26)


@fx('sense')                                       # SP24 Sixth Sense: reads the opponent
def _sense(F):
    a, e, U, O = F.a, F.e, F.under, F.over; TX, TY = 56, 47
    F.ghost(TX, TY, e, (255, 90, 90))
    for k in range(3): u = ((a / 12.0) + k / 3) % 1; U.ring(CX, FY, 3 + 30 * u, (3 + 30 * u) * .38, F.col, (1 - u) * e, 1)
    pulse = (a % 8) / 8.0; U.poly([(CX, BY - 6), (TX + 8, TY - 14), (TX + 8, TY + 4)], F.col, .12 * e)
    O.line([(TX - 8, TY - 20 - 2 * pulse), (TX, TY - 28 - 2 * pulse), (TX + 8, TY - 20 - 2 * pulse), (TX, TY - 12 - 2 * pulse), (TX - 8, TY - 20 - 2 * pulse)], F.lt, e)
    O.line([(TX, TY - 26 - 2 * pulse), (TX, TY - 20 - 2 * pulse)], (255, 255, 255), e, 2); O.px(TX, TY - 16 - 2 * pulse, (255, 255, 255), e, 1)
    k = 4 - 3 * pulse
    for sx in (-1, 1):
        for sy in (-1, 1): O.line([(TX + sx * (8 + k), TY - 8 + sy * (9 + k)), (TX + sx * (8 + k) - sx * 3, TY - 8 + sy * (9 + k))], F.lt, e); O.line([(TX + sx * (8 + k), TY - 8 + sy * (9 + k)), (TX + sx * (8 + k), TY - 8 + sy * (9 + k) - sy * 3)], F.lt, e)
    F.cast(22)


@fx('rally')                                       # SP20 Rally the Team
def _rally(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    U.glow(CX, BY, 16, 22, F.col, .45 * e)
    for k in range(2): u = ((a / 12.0) + k * .5) % 1; U.ring(CX, FY, 4 + 31 * u, (4 + 31 * u) * .4, F.col, (1 - u) * e, 3)
    for k in range(10):                                                                           # rays of light fanning from the player
        ang = -math.pi / 2 + (k - 4.5) * .22 + math.sin(a * .1 + k) * .05; O.line([(CX + math.cos(ang) * 8, BY + math.sin(ang) * 8), (CX + math.cos(ang) * 30, BY + math.sin(ang) * 30)], F.lt, .35 * e)
    for k, u, r in F.cyc(10, 12): O.px(CX + r.uniform(-18, 18) * (.4 + u), 40 - u * 34, [(255, 255, 255), F.col, (230, 60, 60)][k % 3], (1 - u) * e, 1)
    for k, ang in enumerate([0.4, 1.5, 2.6, 3.7, 4.9, 5.8]):
        x, y = CX + math.cos(ang) * 27, FY + math.sin(ang) * 10; F.ghost(x, y, .5); U.glow(x, y - 8, 7, 12, F.lt, .5 * (.5 + .5 * math.sin(a * .5 + k))); O.chev(x, y - 20 - (a % 6), 3, F.lt, e)
    F.cast(34)


@fx('decoy')                                       # SP26 Decoy Run
def _decoy(F):
    a, e, U, O = F.a, F.e, F.under, F.over
    for k in range(10): u = ((a * .05) + k / 10) % 1; O.px(CX + 14 + 36 * u, 47 - 18 * u, F.lt, e * .7)
    t = (a % 16) / 16.0
    for g in range(5):                                                                            # a ghost runner and its fading echoes
        u = max(0, t - g * .05); x = CX + 14 + 36 * u; y = 47 - 18 * u; al = (1 - g * .2) * e * (.9 if g == 0 else .5)
        O.fill(x, y - 15, 2.2, 2.2, F.lt, al); O.line([(x, y - 12), (x - 1, y - 5)], F.lt, al, 2); O.line([(x - 1, y - 5), (x - 4 + (a % 4), y)], F.lt, al); O.line([(x - 1, y - 5), (x + 3 - (a % 4), y)], F.lt, al)
    O.chev(CX + 10, 40, 3, F.lt, e, up=False); O.chev(CX + 14, 40, 3, F.col, e, up=False)
    for k in range(3): u = ((a / 10.0) + k / 3) % 1; U.ring(CX + 14, 47, 3 + 10 * u, (3 + 10 * u) * .4, F.col, (1 - u) * e * .7)
    F.cast(18)


# ---------------------------------------------------------------------------------------------------------------------- driver
def _generic(F):
    F.under.glow(CX, BY, 15, 18, F.col, .5 * F.e); F.cast(24)


def timing(r):
    dur = max(8, int(float(r['duration_s']) * 1000 / 70)); return dur, dur + REST


def layers(r, t):
    """-> (under, over) 72x72 RGBA layers for global tick t"""
    dur, cyc = timing(r); a = t % cyc
    e = clamp(a / 2.0 + .35) * clamp((dur - a) / 6.0 + 0.0, 0, 1) if a < dur else 0.0
    f = F(a, e, dur, _rgb(r['color']), r)
    (EFFECTS.get(r['shape']) or _generic)(f)
    return f.under.im, f.over.im
