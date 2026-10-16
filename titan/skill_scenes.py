"""Supernatural skill-card scenes (previews, like the Titan scenes; uses the same engine). A skill card that bends realism: here DF08 DOUBLE TEAM.
The defender who plays it scans for the nearest team mate, who charges up and zaps across the pitch like a lightning streak (afterimages,
a crackling charge left on the grass) to join the challenge:
  DF08_UP    upfield: he lands BEHIND the carrier and nicks it from behind while the first defender holds him up
  DF08_DEEP  near our box: he lands GOAL SIDE to cover, then the two close the carrier down together
Run:  python titan/skill_scenes.py [DF08_UP DF08_DEEP]  -> export/skills/<id>.gif (+ contact sheets in /tmp)
Positions are pitch pixels (420 x 240); our goal is on the right (x = 330), so the attacker (away) runs right."""
import sys, os, math, random
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import engine as E
from engine import *
import fx

HOME, AWAY = 'home', 'away'
YEL, CYAN, WHITE = (255, 236, 110), (90, 210, 255), (255, 255, 255)
SC_TITLE['DF08_UP'] = 'DOUBLE TEAM UPFIELD'
SC_TITLE['DF08_DEEP'] = 'DOUBLE TEAM DEEP'

# ---------------------------------------------------------------- timeline (scene frames, 40 ms)
T_CARD, T_SCAN, T_LOCK, T_CHARGE, T_ZAP, T_ARRIVE = 22, 24, 33, 36, 47, 53
SLOW = 0.12                                   # world speed while the card plays out (the engagement freeze)


def gt(i):
    """world time: normal, then slow motion from the card until he arrives, then normal again"""
    if i <= T_CARD: return float(i)
    if i <= T_ARRIVE: return T_CARD + (i - T_CARD) * SLOW
    return T_CARD + (T_ARRIVE - T_CARD) * SLOW + (i - T_ARRIVE)


def zig(a, b, n, amp, seed):
    """a lightning path from a to b: n kinks, perpendicular jitter `amp` px (pitch is 2:1 squashed, so less jitter in y)"""
    rng = random.Random(seed); a, b = P(*a), P(*b); d = b - a; perp = unit(P(-d[1], d[0] * 2)); perp[1] *= 0.5
    pts = [a]
    for j in range(1, n):
        t = j / n; s = (1 if j % 2 else -1) * amp * rng.uniform(0.6, 1.0)
        pts.append(a + d * t + perp * s)
    pts.append(b); return pts


def along(pts, s):
    """point and direction at fraction s (0..1) of a polyline"""
    seg = [np.linalg.norm(pts[j + 1] - pts[j]) for j in range(len(pts) - 1)]; L = sum(seg); want = clamp(s) * L
    for j, l in enumerate(seg):
        if want <= l or j == len(seg) - 1:
            t = 0 if l < 1e-6 else min(1.0, want / l); return pts[j] + (pts[j + 1] - pts[j]) * t, unit(pts[j + 1] - pts[j])
        want -= l


def chop(pts, step=7.0):
    """the polyline cut into small pieces (for the crackling charge left on the grass)"""
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for j in range(n): out.append((a + (b - a) * j / n, a + (b - a) * (j + 1) / n))
    return out


def ease_zap(t):                              # explodes out of the blocks, brakes hard at the end
    t = clamp(t); return 1 - (1 - t) ** 3 if t > 0.5 else 4 * t ** 3 * 0.5 + t * 0.5


# ---------------------------------------------------------------- the shared supernatural layer
def scan(c, src, mates, lock_i, i):
    """radar from the defender who played it: an expanding ring, rays out to team mates, the nearest one locked"""
    age = i - T_SCAN
    if 0 <= age < 14:
        for j in range(3):
            r = 8 + 150 * smooth((age - j * 2.5) / 12)
            if r > 8: fx.ring(c, src, r, CYAN, 200 * (1 - age / 14), 'under')
    if T_SCAN + 2 <= i < T_ZAP + 2:
        for n, m in enumerate(mates):
            grow = clamp((i - T_SCAN - 2 - n) / 5)
            q = src + (m - src) * grow
            locked = n == lock_i and i >= T_LOCK
            col = YEL if locked else CYAN; a = 220 if locked else int(140 * (1 - clamp((i - T_LOCK) / 6)))
            if a <= 0: continue
            for t in np.linspace(0, 1, 18):                                       # dashed ray
                if int(t * 18 + i * 0.7) % 2: continue
                p = src + (q - src) * t; c.ud.point((int(p[0]), int(p[1])), fill=col + (a,))
            if grow >= 1: fx.ring(c, m, 7 if locked else 6, col, a, 'under')
    if T_LOCK <= i < T_ZAP:                                                       # the lock: a reticle snaps onto him
        m = mates[lock_i]; k = clamp((i - T_LOCK) / 4)
        fx.reticle(c, m + P(0, -12), lerp(22, 9, smooth(k)), (i - T_LOCK) * 0.25, YEL, 255)


def charge(c, p, i):
    """he winds up: arcs crawl over him, a glow under his feet, his body fills with light"""
    age = i - T_CHARGE; k = clamp(age / (T_ZAP - T_CHARGE)); rng = random.Random(i * 17)
    fx.glow(c, p + P(0, 1), 6 + 8 * k, YEL, 0.55 * k + 0.2)
    for _ in range(2 + int(4 * k)):
        a = p + P(rng.uniform(-7, 7), rng.uniform(-22, -2)); b = a + P(rng.uniform(-7, 7), rng.uniform(-6, 6))
        fx.bolt(c, a, b, rng.randint(0, 999), CYAN if rng.random() < 0.5 else YEL, 230, jag=2, w=2)
    if age % 3 == 0: fx.ring(c, p, 4 + 7 * k, YEL, 200, 'under')
    return k


def zap(c, pts, i, anim_face_skin):
    """the dash itself: Celeste-style afterimages along the path, a white-hot head, bolts linking them"""
    t = (i - T_ZAP) / (T_ARRIVE - T_ZAP)
    s_head = ease_zap(t)
    ghosts = []
    for g in range(9):                                                            # afterimages at fixed points of the path
        sg = (g + 0.5) / 9
        if sg <= s_head: ghosts.append(sg)
    for n, sg in enumerate(ghosts):
        q, d = along(pts, sg); passed_at = T_ZAP + (sg / max(s_head, 1e-6)) * (i - T_ZAP)
        age = i - passed_at; a = int(200 * clamp(1 - age / 9))
        if a > 8: c.spr('base_sprint', (n * 3) % 10, d, HOME, q, tint_rgb=CYAN if n % 2 else YEL, tint_a=a, mix=0.85, shadow=False)
    if t <= 1.0:
        q, d = along(pts, s_head)
        fx.glow(c, q + P(0, -10), 14, YEL, 0.8, 'over')
        prev, _ = along(pts, max(0.0, s_head - 0.25))
        fx.bolt(c, prev + P(0, -10), q + P(0, -10), i * 13, YEL, 255, jag=4, w=5)
        fx.bolt(c, prev + P(0, -4), q + P(0, -12), i * 29, CYAN, 220, jag=6, w=3)
        c.spr('base_sprint', i % 10, d, HOME, q, tint_rgb=WHITE, tint_a=255, mix=0.75)
        return q, d
    return None, None


def residue(c, pts, i, life=70):
    """the charge he leaves on the grass: a scorch line, crackling bolts that flicker and die out, sparks hopping off"""
    age = i - T_ARRIVE + 3
    if age < 0: return
    k = clamp(1 - age / life)
    if k <= 0: return
    c.ud.line([tuple(p) for p in pts], fill=(34, 52, 30, int(150 * clamp(1 - age / (life * 1.6)))), width=3)
    rng = random.Random(i * 7 + 3)
    for a, b in chop(pts):
        if rng.random() > 0.35 + 0.5 * k: continue                                # flicker
        fx.bolt(c, a + P(0, -1), b + P(0, -1), rng.randint(0, 9999), YEL if rng.random() < 0.6 else CYAN, int(255 * k), jag=2.5, w=2, layer='under')
    for n in range(3):
        if rng.random() < k:
            a, _ = chop(pts)[rng.randrange(len(chop(pts)))]
            fx.burst(c, a, (i % 6), rng.randint(0, 999), n=4, speed=1.2, col=YEL, life=6, up=1.2)


def card_pop(c, i, cid='DF08'):
    """the card the defender played, shown big while the effect plays"""
    if not T_CARD <= i < T_ARRIVE + 6: return
    a = clamp((i - T_CARD) / 3) * clamp((T_ARRIVE + 6 - i) / 4)
    im = card_face(cid, 1)
    if a < 1: im = fade(im, int(255 * a))
    c.scr.alpha_composite(im, (VW - im.width - 12, 32 - int(6 * (1 - a))))


def stand(c, p, face, skin=HOME, i=None, **kw):
    c.spr('guard', int(((c.i if i is None else i) * 40) / 85) % 12, face, skin, p, **kw)


def runner(c, p, face, skin=HOME, i=None, rate=1.0, **kw):
    c.spr('run', int(((c.i if i is None else i) * 40 * rate) / 57) % 12, face, skin, p, **kw)


def bob(i): return 1.0 + abs(math.sin(i * 0.7)) * 1.0


# ======================================================================================================== DF08_UP
@scene('DF08_UP', N=132, titan=(T_CARD, T_ARRIVE + 4), color=YEL, result='WON IT FROM BEHIND')
def df08_up(c):
    i = c.i; w = gt(i)
    c.dim(0.45 * c.ta, (14, 18, 50))
    # the attacker drives up the pitch at the first defender, who backs off; the nearest team mate is behind him
    car0, d10 = P(110, 124), P(182, 120)
    mates = [P(46, 176), P(200, 66), P(236, 158)]; H0 = mates[0]
    T_POKE = T_ARRIVE + 6; T_LOSE = T_POKE + 6
    car = car0 + P(min(w, gt(T_POKE)) * 1.05, 0)                                  # stops when he is nicked
    d1 = d10 + P(-min(w, gt(T_POKE)) * 0.35, 0)
    land = car0 + P(gt(T_ARRIVE) * 1.05, 0) + P(-10, 5)                           # right behind him
    path = zig(H0, land, 5, 9, 41)
    # ---- the first defender: jockeys, then picks the ball up and breaks the other way
    ball_free = None
    if i < T_LOSE:
        c.spr('df10_jockey', ak('df10_jockey', w, 0, loop=True), P(-1, 0), HOME, d1)
    else:
        a = i - T_LOSE
        if a < 8: ball_free = lerp(car + P(9, 0), d1 + P(-5, 2), smooth(a / 8)); stand(c, d1, unit(car - d1), HOME)
        else:
            d1r = d1 + P(-(a - 8) * 0.9, -0.45 * (a - 8)); runner(c, d1r, P(-1, -0.5), HOME, rate=1.2)
            c.ball(d1r + P(-5, -2), bob(i))
    # ---- the carrier
    if i < T_POKE:
        runner(c, car, P(1, 0), AWAY, i=w); c.ball(car + P(5.5, 0), bob(w))
    else:
        k = ak('base_stumble_fwd_m', i, T_POKE)
        c.spr('base_stumble_fwd_m', k, P(1, 0), AWAY, car + ground(P(1, 0), root_fwd('base_stumble_fwd_m', k)))
        if ball_free is None and i < T_LOSE: c.ball(lerp(car + P(5.5, 0), car + P(9, 0), (i - T_POKE) / 6), 0.6)
        if ball_free is not None: c.ball(ball_free, 0.6)
    # ---- the other team mates watch
    for m in mates[1:]: stand(c, m, unit(car - m), HOME, i=w)
    # ---- the helper
    scan(c, d1, mates, 0, i)
    if i < T_ZAP:
        p = H0 + P(min(w, T_CARD) * 0.25, 0)
        if i < T_CHARGE: runner(c, p, unit(car - p), HOME, i=w, rate=0.6)
        else:
            k = charge(c, p, i)
            c.spr('guard', 3, unit(land - p), HOME, p, tint_rgb=YEL, tint_a=255, mix=0.25 + 0.5 * k)
    elif i < T_ARRIVE:
        zap(c, path, i, None)
    else:
        a = i - T_ARRIVE
        if a == 0: pass
        fx.shock(c, land, a, YEL, 8, 26, 2); fx.burst(c, land + P(0, -6), a, 77, n=16, speed=2.2, col=YEL, life=10)
        if i < T_POKE: c.spr('base_sprint', 4, P(1, -0.2), HOME, land + P(a * 0.6, -a * 0.2), tint_rgb=YEL, tint_a=255, mix=0.5 * clamp(1 - a / 6))
        else:
            k = ak('df03_poke_tackle', i, T_POKE)
            c.spr('df03_poke_tackle', k, P(1, -0.1), HOME, land + P(3.6, -1.2), tint_rgb=YEL, tint_a=255, mix=0.35 * clamp(1 - (i - T_POKE) / 14))
        if T_POKE <= i < T_POKE + 6: fx.shock(c, car + P(6, 0), i - T_POKE, WHITE, 6, 10, 1)
    zap_ghosts_after(c, path, i)
    residue(c, path, i)
    card_pop(c, i)
    # ---- camera: on the duel, widen for the scan and the zap, back in for the steal
    if i < T_ARRIVE: cx, cy, z = (car[0] + d1[0]) / 2 - 18, 132, 2.15
    else: cx, cy, z = lerp((car[0] + d1[0]) / 2 - 18, car[0] + 12, smooth((i - T_ARRIVE) / 12)), lerp(132, 124, smooth((i - T_ARRIVE) / 12)), lerp(2.15, 3.0, smooth((i - T_ARRIVE - 4) / 12))
    c.cam(cx, cy, z)
    if T_ARRIVE <= i < T_ARRIVE + 3: c.shake(2.0)


def step_up(land, car, i, t0, t1):
    """the covering man closes the carrier down from goal side, stopping just short of him"""
    d = car + P(9, 6) - land; k = smooth(clamp((min(i, t1) - t0) / (t1 - t0)))
    return land + d * k


def zap_ghosts_after(c, pts, i):
    """after he lands the afterimages fade where they were"""
    if not T_ARRIVE <= i < T_ARRIVE + 10: return
    for n in range(9):
        sg = (n + 0.5) / 9; q, d = along(pts, sg); age = i - (T_ZAP + sg * (T_ARRIVE - T_ZAP))
        a = int(200 * clamp(1 - age / 9))
        if a > 8: c.spr('base_sprint', (n * 3) % 10, d, HOME, q, tint_rgb=CYAN if n % 2 else YEL, tint_a=a, mix=0.85, shadow=False)


# ======================================================================================================== DF08_DEEP
@scene('DF08_DEEP', N=132, titan=(T_CARD, T_ARRIVE + 4), color=YEL, result='DOUBLED UP AND WON IT')
def df08_deep(c):
    i = c.i; w = gt(i)
    c.dim(0.45 * c.ta, (14, 18, 50))
    # the attacker runs at our box; the first defender stands him up; the nearest team mate is upfield and wide
    car0, d10 = P(214, 126), P(272, 122)
    mates = [P(196, 86), P(300, 172), P(160, 166)]; H0 = mates[0]
    T_SQUEEZE = T_ARRIVE + 4; T_TACKLE = T_ARRIVE + 22; T_WIN = T_TACKLE + 6
    stop = gt(T_TACKLE)
    car = car0 + P(min(w, stop) * 0.85 - max(0.0, min(w, stop) - gt(T_SQUEEZE)) * 0.6, 0)      # brakes once he is doubled
    d1 = d10 + P(-min(w, gt(T_SQUEEZE)) * 0.3 - max(0.0, min(w, stop) - gt(T_SQUEEZE)) * 0.25, 0)
    land = P(d10[0] - gt(T_ARRIVE) * 0.3 + 20, 136)                               # goal side: behind the first defender, covering the way past him
    path = zig(H0, land, 5, 10, 7)
    # ---- the carrier
    if i < T_SQUEEZE:
        runner(c, car, P(1, 0), AWAY, i=w); c.ball(car + P(5.5, 0), bob(w))
    elif i < T_TACKLE:                                                             # boxed in: shields, looks for a way out
        k = ak('dr12_shoulder_shield', i, T_SQUEEZE, 0.8)
        c.spr('dr12_shoulder_shield', k, P(1, 0.25), AWAY, car); c.ball(car + P(4.5, 1), 0.6)
    else:
        k = ak('base_stumble_side_m', i, T_TACKLE)
        c.spr('base_stumble_side_m', k, P(1, -0.3), AWAY, car)
    # ---- the first defender: jockeys, closes, stands in with the tackle
    if i < T_SQUEEZE: c.spr('df10_jockey', ak('df10_jockey', w, 0, loop=True), P(-1, 0), HOME, d1)
    elif i < T_TACKLE: c.spr('df10_jockey', ak('df10_jockey', i, 0, 1.4, loop=True), P(-1, 0), HOME, d1)
    else:
        k = ak('df01_stand_tackle', i, T_TACKLE); c.spr('df01_stand_tackle', k, P(-1, 0.1), HOME, d1)
    # ---- the other team mates
    for m in mates[1:]: stand(c, m, unit(car - m), HOME, i=w)
    # ---- the helper
    scan(c, d1, mates, 0, i)
    if i < T_ZAP:
        p = H0 + P(min(w, T_CARD) * 0.3, 0)
        if i < T_CHARGE: runner(c, p, unit(car - p), HOME, i=w, rate=0.6)
        else:
            k = charge(c, p, i)
            c.spr('guard', 3, unit(land - p), HOME, p, tint_rgb=YEL, tint_a=255, mix=0.25 + 0.5 * k)
    elif i < T_ARRIVE:
        zap(c, path, i, None)
    else:
        a = i - T_ARRIVE; fx.shock(c, land, a, YEL, 8, 26, 2); fx.burst(c, land + P(0, -6), a, 91, n=16, speed=2.2, col=YEL, life=10)
        hp = step_up(land, car, i, T_SQUEEZE, T_TACKLE)
        tm = 0.5 * clamp(1 - a / 6)
        if i < T_SQUEEZE: c.spr('base_sprint', 4, P(-1, -0.3), HOME, land, tint_rgb=YEL, tint_a=255, mix=tm)
        elif i < T_WIN: c.spr('df10_jockey', ak('df10_jockey', i, 0, 1.4, loop=True), unit(car - hp), HOME, hp)
        else:                                                                     # the ball runs to him: he takes it away from goal
            b = i - T_WIN; hr = hp + P(-b * 1.0, b * 0.35)
            if b < 6: c.ball(lerp(car + P(5, 0), hp + P(-3, 2), smooth(b / 6)), 0.6); stand(c, hp, unit(car - hp), HOME)
            else: runner(c, hr, P(-1, 0.35), HOME, rate=1.2); c.ball(hr + P(-5.5, 2), bob(i))
    if T_TACKLE <= i < T_WIN: c.ball(lerp(car + P(4.5, 1), car + P(10, 4), (i - T_TACKLE) / 6), 0.6)
    if T_TACKLE + 3 <= i < T_TACKLE + 9: fx.shock(c, car + P(6, 0), i - T_TACKLE - 3, WHITE, 6, 10, 1)
    if T_SQUEEZE <= i < T_TACKLE:                                                 # the trap: a fading lasso between the two defenders
        hp = step_up(land, car, i, T_SQUEEZE, T_TACKLE); a = int(120 * (0.6 + 0.4 * math.sin(i * 0.8)))
        fx.bolt(c, d1 + P(0, -8), hp + P(0, -8), i * 5, YEL, a, jag=3, w=1, layer='under')
    zap_ghosts_after(c, path, i)
    residue(c, path, i)
    card_pop(c, i)
    if i < T_ARRIVE: cx, cy, z = (car[0] + d1[0]) / 2 + 6, 104, 2.15
    else: cx, cy, z = lerp((car[0] + d1[0]) / 2 + 6, car[0] + 24, smooth((i - T_ARRIVE) / 12)), lerp(104, 128, smooth((i - T_ARRIVE) / 12)), lerp(2.15, 3.0, smooth((i - T_ARRIVE - 4) / 12))
    c.cam(cx, cy, z)
    if T_ARRIVE <= i < T_ARRIVE + 3: c.shake(2.0)


if __name__ == '__main__':
    ids = sys.argv[1:] or ['DF08_UP', 'DF08_DEEP']
    out = os.path.join(ROOT, 'export', 'skills')
    for cid in ids:
        name, frames = render(cid, out)
        sheet_png(frames, f'/tmp/{name}_sheet.png', step=4)
        print(name, len(frames))
