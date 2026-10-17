"""CLASH scene preview: what an engagement looks like in PvP instead of a slow-motion freeze.
The match cuts (a quick diagonal wipe) to a small close-up scene: the two players at a much bigger pixel size, shoulder to shoulder, grinding,
with ember flakes spraying off the contact point. Each side picks a card under a short timer (yours from the hand, theirs face down), both flip,
one punchy impact, and the wipe takes you straight back to the match where the result plays out.
Run:  python titan/clash_scene.py  -> export/skills/clash_duel.gif (+ /tmp/clash_sheet.png)"""
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import engine as E
from engine import P, unit, lerp, clamp, smooth, ak, root_fwd, ground, VW, VH

HOME, AWAY = 'home', 'away'
EMBER = [(255, 244, 196), (255, 214, 92), (255, 150, 40), (232, 84, 24), (150, 40, 20)]

# ---------------------------------------------------------------- timeline (40 ms frames)
T_IN = 14            # the match runs, the two meet
T_WIPE = 6           # wipe into the clash
T_GRIND = 46         # choosing (in game: up to the choose timer)
T_PICK = 30          # (inside the grind) you pick your card
T_REVEAL = 10        # both cards flip, impact
T_OUT = 6            # wipe back
T_AFTER = 26         # the result in the match
A0 = T_IN; A1 = A0 + T_WIPE; G1 = A1 + T_GRIND; R1 = G1 + T_REVEAL; O1 = R1 + T_OUT; N = O1 + T_AFTER

HAND = ['DR05', 'DR08', 'DR12', 'DR24']
PICK = 1                                       # Elastico
THEIRS = 'DF01'


# ---------------------------------------------------------------- the match part (engine scene)
def stand(c, p, face, skin, i):
    c.spr('guard', int(i * 40 / 85) % 12, face, skin, p)


def runner(c, p, face, skin, i, rate=1.0):
    c.spr('run', int(i * 40 * rate / 57) % 12, face, skin, p)


@E.scene('CLASH_MATCH', N=80, titan=(999, 1000))
def clash_match(c):
    """i < 15: the run-in; i >= 15: after the clash, the carrier bursts past (the defender bit) and the defender stumbles"""
    i = c.i; c.hud = False
    meet_a, meet_d = P(196, 122), P(212, 121)
    if i < 15:
        a = meet_a + P((i - 14) * 1.1, 0); d = meet_d + P(-(i - 14) * 0.35, 0)
        runner(c, a, P(1, 0), HOME, i); c.ball(a + P(5.5, 0), 1.0 + abs(math.sin(i * 0.7)))
        c.spr('df10_jockey', ak('df10_jockey', i, 0, loop=True), P(-1, 0), AWAY, d)
    else:
        j = i - 15
        k = ak('dr08_elastico', j, 0, 1.4)
        a = meet_a + P(j * 1.25, -min(j, 8) * 0.7)
        if j < 10: c.spr('dr08_elastico', k, P(1, 0), HOME, a)
        else: runner(c, a, P(1, -0.15), HOME, j, 1.3)
        c.ball(a + P(5.5, 0), 0.8)
        ks = ak('base_stumble_side_m', j, 0)
        c.spr('base_stumble_side_m', ks, P(-1, 0.4), AWAY, meet_d + P(1.5, 2.0) + ground(P(-1, 0.4), root_fwd('base_stumble_side_m', ks)))
    for p, f in ((P(150, 150), P(1, -0.3)), (P(250, 90), P(-1, 0.4)), (P(120, 95), P(1, 0.2))):
        stand(c, p, f, HOME if p[0] < 200 else AWAY, i)
    c.cam(208 if i < 15 else 220, 120, 3.0)


def match_frame(i):
    return E.render_frame(E.SCENES['CLASH_MATCH'], i).convert('RGBA')


# ---------------------------------------------------------------- the clash scene
S = 4                                           # sprite scale in the clash (40 px -> 160 px, crisp)
_big = {}


def big(anim, k, d, skin, tint=None):
    key = (anim, k, d, skin, tint)
    if key not in _big:
        im = E.sprite(anim, k, d, skin)
        if tint: im = E.tint(im, tint[0], 255, tint[1])
        _big[key] = im.resize((im.width * S, im.height * S), Image.NEAREST)
    return _big[key]


def backdrop(t, heat):
    """dark field, a low band of blurred pitch green, slow horizontal streaks moving toward the contact point"""
    im = Image.new('RGBA', (VW, VH), (14, 14, 26, 255)); d = ImageDraw.Draw(im)
    for y in range(150, 176):                                                     # the grass they stand on
        g = int(40 + (y - 150) * 1.2)
        d.line([(0, y), (VW, y)], fill=(24, g, 34, 255))
    rng = random.Random(7)
    for n in range(26):                                                           # streaks
        y = rng.randint(20, 145); L = rng.randint(30, 120); sp = rng.uniform(5, 11)
        side = -1 if n % 2 else 1
        x = (rng.randint(0, VW) + side * t * sp) % (VW + L) - L
        a = int(30 + 40 * heat)
        d.line([(x, y), (x + L, y)], fill=(90, 90, 140, a), width=1)
    glow = E.blob(VW, VH, 240, 118, 70 + 25 * heat, 46 + 15 * heat, (255, 140, 40), 0.22 + 0.25 * heat)    # the heat at the contact
    im.alpha_composite(glow)
    return im


class Embers:
    """ember flakes spraying off the contact point: born hot (white-yellow), cool to orange and red, fall with gravity, flicker"""
    def __init__(s): s.p = []; s.rng = random.Random(3)

    def emit(s, x, y, n, power=1.0):
        for _ in range(n):
            a = s.rng.uniform(-math.pi * 0.95, -math.pi * 0.05); v = s.rng.uniform(2.0, 6.5) * power
            s.p.append([x + s.rng.uniform(-4, 4), y + s.rng.uniform(-6, 6), math.cos(a) * v, math.sin(a) * v, 0, s.rng.randint(10, 22), s.rng.choice((2, 2, 3, 4))])

    def step(s):
        for q in s.p:
            q[0] += q[2]; q[1] += q[3]; q[3] += 0.38; q[2] *= 0.96; q[4] += 1
        s.p = [q for q in s.p if q[4] < q[5] and q[1] < 175]

    def draw(s, im):
        d = ImageDraw.Draw(im)
        for x, y, vx, vy, age, life, sz in s.p:
            u = age / life
            col = EMBER[min(len(EMBER) - 1, int(u * len(EMBER)))]
            if s.rng.random() < 0.15: continue                                  # flicker
            if sz >= 3 and u < 0.35: d.line([(x, y), (x - vx * 1.4, y - vy * 1.4)], fill=col + (200,), width=1)   # fresh sparks streak
            d.rectangle([int(x), int(y), int(x) + sz - 1, int(y) + sz - 1], fill=col + (255,))


def card_back(w=64, h=90):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(30, 22, 52, 255), outline=(150, 120, 220, 255))
    for y in range(6, h - 6, 6):
        for x in range(6 + (y // 6 % 2) * 3, w - 6, 6): d.point((x, y), fill=(90, 70, 150, 255))
    d.rectangle([w // 2 - 9, h // 2 - 9, w // 2 + 9, h // 2 + 9], outline=(220, 190, 255, 255))
    return im


def flip(face, back, u):
    """a card turning over: squash the width to 0 and back, back side first"""
    w = max(1, int(64 * abs(math.cos(u * math.pi))))
    src = back if u < 0.5 else face
    return src.resize((w, 90), Image.NEAREST)


def label(im, x, y, txt, col, S2=1, center=True):
    t = E.pix_text(txt, col, S2)
    im.alpha_composite(t, (int(x - t.width / 2) if center else int(x), int(y)))


def clash_frame(f, em):
    """f = frames since the wipe-in started"""
    g = f - T_WIPE                                     # grind time
    reveal = f - (T_WIPE + T_GRIND)                     # >= 0 during reveal
    heat = clamp(g / T_GRIND) if reveal < 0 else 1.0
    im = backdrop(f, heat)
    # the two players: grinding shoulder to shoulder, rocking a pixel or two, pressing harder as time runs
    rock = math.sin(f * 0.9) * (1.0 + heat)
    push = 3 * heat
    ka = 9 + int((f // 3) % 3)                          # held around the shove of the shield clip
    kd = 8 + int((f // 3 + 1) % 3)
    imp = 0
    if reveal >= 0:
        imp = 1 if reveal < 3 else 0
    a = big('dr12_shoulder_shield', ka, 8, HOME)
    dd = big('df13_shoulder_charge', kd, 24, AWAY)
    ax = 240 - 30 - E.OX * S + rock + push + (6 if imp else 0); dx = 240 + 30 - E.OX * S - rock - push - (6 if imp else 0)     # shoulders locked at the middle
    base_y = 166 - E.OY * S                                                     # feet on the grass
    shake = (random.Random(f).randint(-1, 1) * (1 + heat)) if reveal < 0 else (random.Random(f).randint(-4, 4) if reveal < 3 else 0)
    im.alpha_composite(dd, (int(dx), int(base_y + shake)))
    im.alpha_composite(a, (int(ax), int(base_y - shake)))
    # the ball between their feet
    d = ImageDraw.Draw(im)
    bx, by = 240 + rock * 0.5, 168
    d.ellipse([bx - 6, by - 5, bx + 6, by + 5], fill=(10, 10, 20, 120))
    d.ellipse([bx - 6, by - 12, bx + 6, by], fill=(240, 240, 245, 255)); d.rectangle([bx - 1, by - 8, bx + 2, by - 5], fill=(40, 40, 60, 255))
    # embers off the contact point (shoulder height), more as it heats up, a big burst on the reveal
    if reveal < 0: em.emit(240, 104, 2 + int(5 * heat), 0.8 + 0.6 * heat)
    elif reveal == 0: em.emit(240, 104, 70, 2.0)
    em.step(); em.draw(im)
    # names + the stat that matters, small, top
    label(im, 120, 8, 'NEYMARINHO  DRI 88', (255, 220, 220), 1)
    label(im, 360, 8, 'RUEDIGER  DEF 84', (220, 230, 255), 1)
    # the timer: a thin bar that burns down
    if reveal < 0:
        left = 1 - clamp(g / T_GRIND)
        w = int(300 * left)
        d.rectangle([90, 24, 390, 26], fill=(40, 40, 60, 255))
        d.rectangle([240 - w // 2, 24, 240 + w // 2, 26], fill=(255, 200, 80, 255) if left > 0.3 else (255, 90, 60, 255))
    # the hand (yours, bottom left) and their face-down card (right)
    picked = g >= T_PICK
    for n, cid in enumerate(HAND):
        face = E.card_face(cid, 1)
        x = 14 + n * 50; y = 176
        if n == PICK and picked and reveal < 0:
            lift = int(10 * smooth((g - T_PICK) / 4)); y -= lift
            d.rectangle([x - 2, y - 2, x + 65, y + 91], outline=(255, 220, 90, 255), width=2)
        elif picked or reveal >= 0:
            face = E.fade(face, 70)
        if reveal >= 0 and n == PICK: continue
        im.alpha_composite(face, (x, y))
    back = card_back()
    if reveal < 0:
        im.alpha_composite(back, (VW - 80, 176))
    else:                                                                        # both flip in the middle, then hang there
        u = clamp(reveal / 5)
        mine = E.card_face(HAND[PICK], 1)                                       # yours is already face up: it slides to the middle
        theirs = E.card_face(THEIRS, 1) if u >= 1 else flip(E.card_face(THEIRS, 1), back, u)
        im.alpha_composite(mine, (int(170 - mine.width / 2), 176))
        im.alpha_composite(theirs, (int(310 - theirs.width / 2), 176))
        label(im, 240, 205, 'VS', (255, 230, 150), 2)
    # the impact: one white frame + a ring, the moment the cards land
    if reveal in (1, 2):
        ov = Image.new('RGBA', (VW, VH), (255, 245, 220, 150 if reveal == 1 else 60)); im.alpha_composite(ov)
    if 1 <= reveal < 8:
        r = 10 + reveal * 22
        d.ellipse([240 - r, 104 - r * 0.6, 240 + r, 104 + r * 0.6], outline=(255, 220, 120, max(0, 230 - reveal * 30)), width=3)
    if reveal >= 5:
        label(im, 240, 32, 'BEAT HIM', (255, 236, 140), 2)
    # a thin frame so it reads as an insert, not a new screen
    d.rectangle([0, 0, VW - 1, VH - 1], outline=(255, 170, 60, 255), width=2)
    return im


def wipe(a, b, u, angle=0.35):
    """a diagonal slash wipe from a to b (u 0..1), with a hot edge"""
    out = a.copy()
    mask = Image.new('L', (VW, VH), 0); d = ImageDraw.Draw(mask)
    x = lerp(-VW * 0.4, VW * 1.4, smooth(u)); k = VH * angle
    d.polygon([(-10, -10), (x + k, -10), (x - k, VH + 10), (-10, VH + 10)], fill=255)
    out.paste(b, (0, 0), mask)
    e = ImageDraw.Draw(out)
    e.line([(x + k, -10), (x - k, VH + 10)], fill=(255, 210, 90, 255), width=4)
    e.line([(x + k + 5, -10), (x - k + 5, VH + 10)], fill=(255, 120, 40, 160), width=2)
    return out


def render():
    em = Embers(); frames = []
    last_match_in = match_frame(T_IN)
    for i in range(N):
        if i < A0: fr = match_frame(i)
        elif i < A1:                                                             # wipe in
            f = i - A0; fr = wipe(last_match_in, clash_frame(f, em), (f + 1) / T_WIPE)
        elif i < R1: fr = clash_frame(i - A0, em)
        elif i < O1:                                                             # wipe out
            f = i - R1; c = clash_frame(i - A0, em); fr = wipe(c, match_frame(15 + f), (f + 1) / T_OUT, -0.35)
        else: fr = match_frame(15 + T_OUT + (i - O1))
        frames.append(fr.convert('RGB'))
    out = os.path.join(E.ROOT, 'export', 'skills'); os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'clash_duel.gif')
    durs = [40] * N
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0)
    E.sheet_png(frames, '/tmp/clash_sheet.png', step=max(1, N // 24))
    return path, len(frames)


if __name__ == '__main__':
    print(render())
