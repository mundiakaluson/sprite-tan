"""All 25 Titan scenes. Positions are pitch pixels (420x240; goal on the right at x=330, mouth y 90-150). Everything is a function of the frame number i."""
import sys, os, math, random, csv
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import engine as E
from engine import *
import fx

for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'cards.csv'), encoding='utf-8')):
    if r['id'].startswith('TT'): SC_TITLE[r['id']] = r['name'].upper()

GOAL = P(GOAL_X, 120)
HOME, AWAY, KEEP = 'home', 'away', 'keeper'


def stand(c, p, face, skin=HOME, i=None, **kw):
    c.spr('guard', int(((c.i if i is None else i) * 40) / 85) % 12, face, skin, p, **kw)


def runner(c, p, face, skin=HOME, i=None, rate=1.0, **kw):
    c.spr('run', int(((c.i if i is None else i) * 40 * rate) / 57) % 12, face, skin, p, **kw)


# ======================================================================================================== TT01  ZIP ZAP
@scene('TT01', N=150, titan=(30, 112), result='3 DEFENDERS BEATEN')
def tt01(c):
    i = c.i; ZF = [46, 68, 90]; ZT = [P(100, 109), P(116, 132), P(133, 109)]; start = P(50, 120)
    defs = [P(92, 118), P(108, 120), P(124, 118)]
    c.dim(0.5 * c.ta)
    # attacker: runs in, zaps between the defenders (no running), runs out
    if i < 30: pos = start + P(i * 0.84 * 1.0, 0); face = P(1, 0); mode = 'run'
    else:
        pos = P(80, 120); mode = 'stand'
        for zf, T in zip(ZF, ZT):
            if i >= zf + 2: pos = T
        nxt = next((T for zf, T in zip(ZF, ZT) if i < zf + 2), P(160, 120)); face = unit(nxt - pos)
        if i >= 112: pos = pos + P((i - 112) * 0.9, 0); face = P(1, 0); mode = 'run'
        if any(zf <= i <= zf + 1 for zf in ZF): mode = 'hide'
    # defenders turn to follow, then the middle one slides at where he thinks the player is
    for j, d in enumerate(defs):
        if j == 1 and i >= 40:
            k = ak('slide', i, 40, 0.75); tgt = pos if i < 40 else P(100, 118)
            sd = unit(P(96, 120) - d); p = d + ground(sd, root_fwd('slide', k) * 1.0)
            c.spr('slide', k, sd, AWAY, p)
        else:
            stand(c, d, unit(pos - d), AWAY)
    # glow ring + sparks round the attacker while the Titan is on
    if c.ta > 0 and mode != 'hide':
        pulse = 1 + 0.12 * math.sin(i * 0.7); fx.ring(c, pos, 11 * pulse, (255, 214, 80), 230 * c.ta); fx.ring(c, pos, 7 * pulse, (120, 230, 255), 200 * c.ta)
        rng = random.Random(i * 7)
        for _ in range(7): c.od.point((int(pos[0] + rng.uniform(-8, 8)), int(pos[1] - rng.uniform(0, 24))), fill=(255, 230, 120, int(240 * c.ta)))
    for zf, T, prev in zip(ZF, ZT, [P(73, 120), ZT[0], ZT[1]]):
        age = i - zf
        if 0 <= age <= 3: fx.bolt(c, prev + P(0, -10), T + P(0, -10), zf * 31 + age * 7, a=int(255 * (1 - age / 4)))
        if 0 <= age < 12: c.spr('guard', 2, dir_index(*(T - prev)), HOME, prev, tint_rgb=(120, 235, 255), tint_a=int(150 * (1 - age / 12)))
        fx.shock(c, T, i - zf - 2, (255, 235, 140), 6, 20, 2)
    if mode != 'hide':
        if mode == 'run': runner(c, pos, face, i=i); bp = pos + face * 5.5; c.ball(bp, 1.0 + abs(math.sin(i * 0.7)) * 1.2)
        else: stand(c, pos, face); c.ball(pos + face * 5.5, 0.8)
    # camera: wide run-in, hard zoom through the zaps, pull back out
    z = 3 if i < 37 else (4 if i < 43 else (5 if i < 51 else (6 if i < 92 else (5 if i < 98 else (4 if i < 104 else 3)))))
    c.cam(pos[0] + (14 if z <= 4 else 9), 120 + 0.35 * (pos[1] - 120) - 2, z)
    if 30 <= i < 35: pass


# ======================================================================================================== TT06  TIME STOP
@scene('TT06', N=130, titan=(28, 100), color=(190, 235, 255), result='THE WORLD STOPPED')
def tt06(c):
    i = c.i; T0 = 28; frozen = c.in_titan
    # play at the moment of freeze: a cross is flying in, defenders closing in on the runner
    ball_t = i if i < T0 else T0
    bpos = lerp(P(260, 70), P(150, 128), clamp(ball_t / 40)); bz = 28 - 26 * smooth(ball_t / 40) + (0 if frozen else 0)
    run_p = P(60, 120) + P(0.9 * min(i, T0), 0) if i < T0 else None
    me0 = P(60 + 0.9 * T0, 120)
    defs = [P(150 + 0.0, 100 - 0.0), P(165, 136), P(190, 112), P(205, 128)]
    # defenders chase for the first T0 frames; frozen after (then they stay)
    for j, d in enumerate(defs):
        dd = d + P(-0.6 * min(i, T0), (0.3 if j % 2 else -0.3) * min(i, T0)) if True else d
        face = unit(me0 + P(0.9 * min(i, T0), 0) - dd)
        if frozen and i < 88:
            c.spr('run', 3 + j, face, AWAY, dd, tint_rgb=(160, 200, 230), tint_a=255, mix=0.75)
            for q in range(3): fx.glow(c, dd + P(0, -14 + q * 7), 5, (200, 235, 255), 0.35)                  # ice halo
        else: c.spr('run', int(i * 40 / 57) % 12 if not frozen else 3 + j, face, AWAY, dd)
    # time-stop clock hand sweeping over the pitch
    if frozen:
        e = c.ta; c.dim(0.55 * e, (200, 220, 240)); c.after(fx.gray(0.9 * e)); c.after(fx.invert(0.0))
        cx, cy = 240, 135; R = 70 * min(1.0, (i - T0) / 6)
        for k in range(12):
            a = k * math.pi / 6; c.sd.line([(cx + math.cos(a) * R * 0.85, cy + math.sin(a) * R * 0.85), (cx + math.cos(a) * R, cy + math.sin(a) * R)], fill=(220, 240, 255, int(160 * e)), width=2)
        c.sd.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(220, 240, 255, int(170 * e)), width=2)
        sweep = (i - T0) * 0.22; c.sd.line([(cx, cy), (cx + math.sin(sweep) * R * 0.8, cy - math.cos(sweep) * R * 0.8)], fill=(255, 255, 255, int(230 * e)), width=3)
        c.sd.line([(cx, cy), (cx + math.sin(sweep * 0.08) * R * 0.5, cy - math.cos(sweep * 0.08) * R * 0.5)], fill=(255, 255, 255, int(200 * e)), width=4)
        fx.ring(c, me0, 12, (255, 255, 255), 230 * e)
    # the player does not run: the sprite holds one stiff pose and DASHES (Akuma / Dio) in short bursts, leaving afterimages
    WP = [P(60 + 0.9 * T0, 120), P(118, 110), P(152, 127), P(184, 114), P(214, 123)]
    DASH = [(36, 43), (50, 57), (64, 71), (78, 85)]
    def at(f):
        if f < T0: return P(60 + 0.9 * f, 120)
        q = WP[0]
        for n, (a0, a1) in enumerate(DASH):
            if f >= a1: q = WP[n + 1]
            elif f > a0: return lerp(WP[n], WP[n + 1], 1 - (1 - (f - a0) / (a1 - a0)) ** 3)
        return q
    def dashing(f): return any(a0 < f <= a1 for a0, a1 in DASH)
    if i < T0: pos = at(i); runner(c, pos, P(1, 0), i=i)
    elif i < 88:
        pos = at(i); mv = at(i + 1) - at(i - 1)
        seg = next((n for n, (a0, a1) in enumerate(DASH) if a0 < i <= a1 + 6), None)
        face = unit(WP[min(seg + 1, 4)] - WP[seg]) if seg is not None else P(1, 0)
        fdi = dir_index(*face)
        if dashing(i):
            for k in range(1, 8):                                                                                  # afterimages strung out behind
                q = at(i - k)
                if np.linalg.norm(q - pos) > 1.5:
                    c.spr('run', 3, face, HOME, q, tint_rgb=(150, 230, 255) if k % 2 else (255, 255, 255), tint_a=int(190 / k), alpha=int(200 / k))
            pts = [at(i - k) + P(0, -9) for k in range(0, 9)]
            fx.trail(c, pts, (200, 240, 255), a=200, width=3)
            fx.trail(c, [q + P(0, -4) for q in pts], (120, 210, 255), a=150, width=2)
        elif seg is not None and i <= DASH[seg][1] + 3:                                                              # landing puff
            fx.shock(c, pos, i - DASH[seg][1], (230, 245, 255), 4, 16, 2)
        c.spr('run', 3, face, HOME, pos)                                                                           # the frozen pose itself
    else: pos = at(87) + P((i - 88) * 1.0, 0); runner(c, pos, P(1, 0), i=i)
    c.ball(bpos if frozen and i < 88 else (bpos if i < T0 else lerp(bpos, at(87) + P(16, 3), smooth((i - 88) / 12))), bz if i < 88 else max(2, bz * (1 - (i - 88) / 12)), glow=(220, 240, 255) if frozen else None)
    c.cam(pos[0] + 22 if i >= T0 else 130, 122, 3 if i >= T0 else 2.4)
    if i == T0 + 38: c.flash(0.0)
    if 88 <= i < 96:                                                                                         # time resumes: the world shatters back into colour
        c.flash(1 - (i - 88) / 8, (230, 245, 255)); c.shake(4 * (1 - (i - 88) / 8))


# ======================================================================================================== TT02  GRAVITY CANNON
@scene('TT02', N=130, titan=(30, 98), color=(170, 120, 255), result='KEEPER FLATTENED')
def tt02(c):
    i = c.i; me = P(210, 140); T0 = 30
    c.dim(0.55 * c.ta, (30, 12, 60))
    kp = P(GOAL_X - 4, 120)
    k_s = ak('sh07_power_blast', i, 56, 0.9); strike = 56 + int(12 * 70 / 40 / 0.9)
    face = unit(GOAL - me)
    if i < 56:                                                                                                  # winding up while the ball sinks into the turf
        stand(c, me, face, i=i)
        w = smooth((i - T0) / 24) if i >= T0 else 0
        bz = 3 - 3 * w; bsz = 1.0 + 3.0 * w
        c.ball(me + face * 6 + P(0, 4) * 0, bz, r=bsz, col=(60, 40, 110), glow=(150, 90, 255))
        fx.ring(c, me + face * 6, 8 + 20 * w, (170, 120, 255), 180 * w); fx.ring(c, me + face * 6, 4 + 12 * w, (255, 255, 255), 120 * w)
        if w > 0: fx.cracks(c, me + face * 6, i - T0, 11, n=8, length=26 * w + 4)
        c.after(fx.radial_warp(*c.to_screen(me + face * 6) if False else (240, 150), 0.25 * w)) if w > 0 else None
        c.cam(me[0] + 40, 125, 2.6 + 1.6 * w); c.shake(2.5 * w)
    else:
        c.spr('sh07_power_blast', k_s, face, HOME, me)
        age = i - strike
        bs = 6.0                                                                                               # the ball leaves like a cannon shell
        p_ball = lerp(me + face * 8, P(GOAL_X + 6, 118), clamp(age / 9)) if age >= 0 else me + face * 6
        if age >= 0:
            for q in range(1, 7): c.ball(lerp(me + face * 8, P(GOAL_X + 6, 118), clamp((age - q * 0.7) / 9)), 4 + 0, r=3.5 - q * 0.4, col=(60, 40, 110), glow=(150, 90, 255), alpha=int(200 / q))
            c.ball(p_ball, 4, r=3.5, col=(40, 20, 80), glow=(170, 110, 255))
            fx.shock(c, me + face * 8, age, (170, 120, 255), 10, 50, 3)
        else: c.ball(p_ball, 1.0, r=4.0, col=(40, 20, 80), glow=(170, 110, 255))
        c.cam(lerp(me[0] + 40, 300, smooth((age) / 14)), 125, 2.2 if age < 0 else 2.6)
        c.shake(5 if 0 <= age < 5 else 0)
        c.flash(0.7 * clamp(1 - age / 4) if age >= 0 else 0, (200, 170, 255))
    # the keeper: tries to hold it, gets driven back
    age_k = i - (strike + 9)
    if i < strike + 9: c.spr('gk04_punch_clear', ak('gk04_punch_clear', i, strike - 10, 1.0), P(-1, 0), KEEP, kp) if i > strike - 10 else c.spr('guard', int(i * 40 / 85) % 12, P(-1, 0.0), KEEP, kp)
    else:
        kk = kp + P(clamp(age_k / 10) * 22, 0); c.spr('slide', min(21, 10 + age_k // 2), P(1, 0), KEEP, kk, tint_rgb=(170, 120, 255), tint_a=255, mix=min(0.5, 0.05 * age_k))
        fx.burst(c, kp + P(6, 0), age_k, 5, n=20, speed=3.5, col=(190, 150, 255), life=20)
        c.ball(P(GOAL_X + 10, 119), 6, r=3.0 + 0 * age_k, col=(60, 40, 110), glow=(150, 90, 255)) if age_k < 14 else c.ball(P(GOAL_X + 8, 122 + age_k * 0.0), 2, r=2.0, col=(60, 40, 110))



# ======================================================================================================== TT03  EAGLE'S EYE
@scene('TT03', N=130, titan=(26, 104), color=(255, 214, 80), result="OPPONENT'S HAND REVEALED")
def tt03(c):
    i = c.i; me = P(150, 124)
    ds = [P(200, 96), P(214, 132), P(238, 110), P(252, 142)]
    c.dim(0.45 * c.ta, (40, 30, 0))
    # the player is dribbling in, then stops and looks up; an eagle eye opens over the pitch
    if i < 26: pos = P(80 + i * 2.6, 124); runner(c, pos, P(1, 0), i=i); c.ball(pos + P(5.5, 0), 1 + abs(math.sin(i * 0.7)))
    else:
        pos = P(80 + 26 * 2.6 + min(i - 26, 10) * 0.4 * (1 - smooth((i - 26) / 10)), 124); stand(c, pos, P(1, 0.0)); c.ball(pos + P(5.5, 0), 0.8)
        # the head sweeps: three scans
        c.od.rectangle([0, 0, 0, 0], fill=(0, 0, 0, 0))
    for j, d in enumerate(ds):
        stand(c, d, unit(pos - d) if i < 26 else P(-1, 0.1 * (j - 1.5)), AWAY)
    if c.in_titan:
        e = c.ta; sweep = math.sin((i - 26) * 0.13) * 90
        # eagle eye: a big golden eye with a sweeping gaze cone over the screen
        ex, ey = 240, 140; eye_r = 120 * smooth((i - 26) / 8)
        c.sd.polygon([(ex, ey), (ex + 260, ey - 90 + sweep * 0.7), (ex + 260, ey + 90 + sweep * 0.7)], fill=(255, 220, 90, int(30 * e)))
        for q, d in enumerate(ds):
            hit = clamp(1 - abs(((i - 26) * 3.0 + q * 18) % 80 - 40) / 40)
            fx.ring(c, d, 12 + 3 * math.sin(i * 0.5 + q), (255, 214, 80), 230 * e)
            # that defender's hand fanned above his head, revealed
            for h in range(3):
                x = d[0] - 20 + h * 14; y = d[1] - 36 - 4 * math.sin(i * 0.2 + h + q) - abs(h - 1) * 3
                fx.mini_card(c.od, x, y, 12, 18, col=(255, 214, 80) if (q + h) % 2 else (120, 200, 255))
        c.cam(212, 120, 2.0 + 0.8 * smooth((i - 26) / 14))
        # eye shape on screen
        r = eye_r * 0.35
        c.sd.ellipse([ex - r * 1.6, 60 - r * 0.55, ex + r * 1.6, 60 + r * 0.55], outline=(255, 214, 80, int(220 * e)), width=2)
        c.sd.ellipse([ex - r * 0.5, 60 - r * 0.5, ex + r * 0.5, 60 + r * 0.5], fill=(255, 214, 80, int(220 * e)))
        c.sd.ellipse([ex - r * 0.2, 60 - r * 0.2, ex + r * 0.2, 60 + r * 0.2], fill=(10, 8, 30, int(255 * e)))
        # timer arc 6s
        left = clamp(1 - (i - 26) / (104 - 26))
        c.sd.arc([440 - 18, 232 - 18, 440 + 18, 232 + 18], -90, -90 + 360 * left, fill=(255, 214, 80, 255), width=3)
    else:
        c.cam(pos[0] + 40, 124, 2.0)


# ======================================================================================================== TT04  TRIPLE WEAVE
@scene('TT04', N=170, titan=(28, 140), color=(110, 210, 255), result='3 DEFENDERS BEATEN')
def tt04(c):
    i = c.i; T0 = 28
    defs = [P(130, 112), P(172, 132), P(214, 112)]
    # slow motion: the dribble plays at 0.35x while the Titan is on
    sl = 1.0 if i < T0 else 0.35
    if i < T0: t_eff = i
    elif i < 140: t_eff = T0 + (i - T0) * 0.35
    else: t_eff = T0 + (140 - T0) * 0.35 + (i - 140) * 1.0
    c.dim(0.4 * c.ta, (10, 30, 70))
    # the weave: a slalom path between the three defenders
    path = line_track([(0, (50, 122)), (T0, (96, 122)), (T0 + 14, (128, 132)), (T0 + 30, (150, 108)), (T0 + 50, (172, 112)), (T0 + 65, (198, 132)), (T0 + 90, (214, 110)), (T0 + 120, (250, 120)), (T0 + 150, (330, 120))])
    def T(tt): return path(tt)
    pos = T(t_eff); nxt = T(t_eff + 3); face = unit(nxt - pos) if np.linalg.norm(nxt - pos) > 0.01 else P(1, 0)
    mode = 'run' if (i < T0 or i >= 140) else 'skill'
    if mode == 'run': runner(c, pos, face, i=int(t_eff)); c.ball(pos + face * 5.5, 1.0 + abs(math.sin(i * 0.7)))
    else:
        k = ak('dr18_skill_combo', t_eff, T0, 1.0); c.spr('dr18_skill_combo', k, face, HOME, pos); c.ball(pos + face * 6.5, 1.5)
    # ghosts left behind in blue at fixed intervals, sparkle trail
    if c.in_titan:
        for q in range(1, 7):
            tp = T(t_eff - q * 5); fp = unit(T(t_eff - q * 5 + 3) - tp)
            c.spr('guard', int(i * 40 / 85) % 12, fp, HOME, tp, tint_rgb=(110, 210, 255), tint_a=int(170 / q), alpha=int(150 / q), shadow=False)
        fx.ring(c, pos, 11, (110, 210, 255), 220 * c.ta); fx.ring(c, pos, 7, (255, 255, 255), 160 * c.ta)
    # defenders lunge too late: each swings a slide tackle at air once the player has gone past
    for j, d in enumerate(defs):
        trig = T0 + 30 + j * 35
        if c.in_titan and t_eff > trig:
            k = ak('slide', t_eff, trig, 0.6); sd = unit(T(trig + 3) - d) if True else P(1, 0)
            c.spr('slide', k, P(1, (0.4 if j % 2 else -0.4)), AWAY, d + ground(P(1, 0.3), root_fwd('slide', k) * 0.7))
        else: stand(c, d, unit(pos - d), AWAY)
    c.cam(pos[0] + 22, 122, 3.2 if c.in_titan else 2.4)
    for j, d in enumerate(defs):
        trig = T0 + 30 + j * 35 + 22
        if t_eff > trig and i < 150: fx.burst(c, d + P(8, 0), int((t_eff - trig) * 3), j * 17, n=10, speed=2.2, col=(110, 210, 255), life=14)
    if 28 <= i < 33: c.flash(1 - (i - 28) / 5, (160, 230, 255))


def net_ripple(c, age, y=120, col=(255, 255, 255)):
    """goal net bulging after a goal: ripples + a flash at the goal mouth"""
    if not 0 <= age < 24: return
    for q in range(5):
        r = 6 + age * 1.6 - q * 4
        if r > 0: fx.ring(c, P(GOAL_X + 4, y), r, col, int(200 * (1 - age / 24)), 'over', k=1.6)
    fx.burst(c, P(GOAL_X + 4, y), age, 77, n=18, speed=3.0, col=col, life=20)


def keeper_dive(c, i, start, kp, skin=KEEP, anim='gk02_reach_dive', face=P(-1, 0.0), rate=1.0):
    k = ak(anim, i, start, rate); c.spr(anim, k, face, skin, kp + ground(P(0, 1), root_side(anim, k) * 1.0) if False else kp); return k


# ======================================================================================================== TT05  BICYCLE KICK
@scene('TT05', N=120, titan=(28, 84), color=(255, 120, 220), result='WHAT A GOAL')
def tt05(c):
    i = c.i; pos = P(268, 128); face = P(-1, 0.02); START = 40; RATE = 0.55
    c.dim(0.5 * c.ta, (30, 10, 50))
    k = ak('tt05_bicycle_kick', i, START, RATE); STRIKE = START + int(8 * 60 / 40 / RATE)
    # a defender and a teammate who put the cross in
    stand(c, P(236, 108), P(1, 0.4), AWAY); stand(c, P(244, 146), P(1, -0.3), AWAY)
    if i < START: stand(c, pos, face)
    else: c.spr('tt05_bicycle_kick', k, face, HOME, pos)
    # the ball: drops out of the sky in front of him, hit overhead, rockets into the top corner
    if i < STRIKE:
        u = clamp(i / STRIKE); bz = lerp(75, 18, smooth(u) ** 1.2); bp = lerp(pos + P(-18, -2), pos + P(-2, 0), smooth(u))
        c.ball(bp, bz, r=1.3)
    else:
        age = i - STRIKE; u = clamp(age / 12); bp = lerp(pos + P(-2, 0), P(GOAL_X + 4, 112), u); bz = 18 + 30 * math.sin(math.pi * u) - 10 * u
        trail_pts = [lerp(pos + P(-2, 0), P(GOAL_X + 4, 112), clamp((age - q) / 12)) - P(0, 18 + 30 * math.sin(math.pi * clamp((age - q) / 12)) - 10 * clamp((age - q) / 12)) for q in range(6, -1, -1)]
        if age < 14: fx.trail(c, [tuple(t) for t in trail_pts], (255, 120, 220), 230, 3, layer='over')
        if age < 12: c.ball(bp, bz, r=2.0, glow=(255, 150, 230))
        fx.shock(c, pos + P(-2, -10), age, (255, 255, 255), 9, 48, 3); fx.burst(c, pos + P(-2, 0), age, 9, n=14, speed=3, col=(255, 160, 235), life=14)
        if age >= 12: net_ripple(c, age - 12, 112, (255, 150, 230))
        if age >= 12: c.ball(P(GOAL_X + 6, 114), 2, r=2.0)
    # keeper beaten
    if i >= STRIKE: c.spr('gk02_reach_dive', ak('gk02_reach_dive', i, STRIKE + 2, 0.7), P(-1, 0), KEEP, P(GOAL_X - 3, 120))
    else: stand(c, P(GOAL_X - 3, 120), P(-1, 0), KEEP)
    # camera: wide -> slow push in on the jump -> hard pan with the ball
    ph = i - START
    if i < START: c.cam(pos[0] - 10, 124, 2.2 + 0.8 * smooth(i / START))
    elif i < STRIKE: c.cam(pos[0] - 6, 118, 3.0 + 1.5 * smooth(ph / (STRIKE - START)))
    else: c.cam(lerp(pos[0], 300, smooth((i - STRIKE) / 12)), 118, lerp(4.5, 2.4, smooth((i - STRIKE) / 14)))
    if STRIKE <= i < STRIKE + 4: c.flash(0.9 * (1 - (i - STRIKE) / 4), (255, 200, 245)); c.shake(5)
    if i == STRIKE - 1: c.shake(1)


# ======================================================================================================== TT07  ROCKET LEGS
@scene('TT07', N=140, titan=(24, 96), color=(255, 120, 50), result='OUTPACED EVERYONE')
def tt07(c):
    i = c.i; T0 = 24
    defs = [P(120, 100), P(165, 140), P(215, 108), P(262, 138), P(300, 112)]
    # speed: starts jogging, then a launch crouch, then rocket speed
    if i < T0: x = 40 + i * 1.0
    elif i < T0 + 6: x = 40 + T0 + (i - T0) * 0.1
    else: x = 40 + T0 + 0.6 + (i - T0 - 6) * 4.6 * min(1.0, 0.4 + (i - T0 - 6) / 10)
    x = min(x, 372); pos = P(x, 122 + 6 * math.sin(i * 0.15)); face = P(1, 0.03)
    c.dim(0.45 * c.ta, (40, 14, 8))
    if i < T0: runner(c, pos, face, i=i)
    elif i < T0 + 6: c.spr('df11_press_trigger', min(4, ak('df11_press_trigger', i, T0)), face, HOME, pos); fx.ring(c, pos, 6 + (i - T0) * 4, (255, 150, 60), 220, 'under')
    else: runner(c, pos, face, i=i, rate=2.2)
    # flames out of the boots + a long streak
    if i >= T0 + 6:
        for q in range(0, 14):
            bp = pos - P(q * 3.0, -2); fx.flame(c, bp + P(0, 6 - 0 * q), q, i * 3 + q, n=3, spread=1.5 + q * 0.2, dirv=(-1, 0.1), rise=0.6, size=2, layer='under')
        fx.glow(c, pos - P(8, -4), 10, (255, 150, 60), 0.6)
        fx.trail(c, [tuple(pos - P(q * 7, -6)) for q in range(9, -1, -1)], (255, 200, 80), 150, 2)
    # defenders get swept aside as he passes
    for j, d in enumerate(defs):
        near = pos[0] - d[0]
        if near < -6: stand(c, d, unit(pos - d), AWAY)
        else:
            a = clamp(near / 40); fl = d + P(-6 * a, (-1 if j % 2 else 1) * 22 * a); sp = int(near * 0.5)
            c.spr('guard', int(i * 0.8) % 12, (int(i * 3 + j * 5) % 32), AWAY, fl + P(0, 0), alpha=int(255 - 120 * a))
            fx.shock(c, d + P(2, 0), int(near / 3.0), (255, 170, 80), 8, 26, 2)
    c.cam(pos[0] + 36, 120, 2.0 if i >= T0 + 6 else 2.8)
    c.shake(3 if i >= T0 + 6 and c.in_titan else 0)
    for q in range(10):                                                                                  # heat streaks across the screen
        rng = random.Random(i * 11 + q); y = rng.randint(34, 236); xx = (rng.randint(0, 480) - i * 160) % 600 - 60
        c.sd.line([(xx, y), (xx + rng.randint(40, 110), y)], fill=(255, 190, 90, int(150 * c.ta)), width=1)
    if c.in_titan and i > T0 + 6: c.text(240, 214, 'SPEED  ' + str(min(99, 40 + (i - T0 - 6) * 3)) + ' KM/H', (255, 190, 90), 2)


# ======================================================================================================== TT08  IRON WALL
@scene('TT08', N=140, titan=(26, 106), color=(180, 195, 215), result='NOTHING GETS THROUGH')
def tt08(c):
    i = c.i; T0 = 26
    wall = [P(262, 84), P(262, 108), P(262, 132), P(262, 156)]
    c.dim(0.4 * c.ta, (14, 20, 40))
    # attackers: a striker with two runners, three shots hammer the wall
    me = P(176, 124); face = unit(P(262, 120) - me)
    S1, S2, S3 = 44, 70, 94
    shots = [S1, S2, S3]
    k = 0
    for q, st in enumerate(shots):
        if st - 8 <= i < st + 16: k = ak('sh02_instep_drive', i, st - 8, 1.0); c.spr('sh02_instep_drive', k, face, HOME, me); break
    else: stand(c, me, face)
    stand(c, P(190, 90), P(1, 0.4), HOME); stand(c, P(190, 160), P(1, -0.4), HOME)
    # steel plates rise out of the ground in front of each defender
    for j, w in enumerate(wall):
        rise = smooth((i - T0 - j * 2) / 8) if c.in_titan or i >= T0 else 0
        h = 24 * rise
        stand(c, w, P(-1, 0.1), AWAY)
        if h > 0.5:
            x0, x1, y1 = w[0] - 14, w[0] - 6, w[1] + 4
            c.od.rectangle([x0, y1 - h, x1, y1], fill=(150, 165, 185, 255), outline=(60, 70, 90, 255))
            if h > 4: c.od.rectangle([x0 + 1, y1 - h + 1, x0 + 2, y1 - 1], fill=(220, 232, 245, 255))
            for rv in range(2): c.od.point((x1 - 2, int(y1 - h + 3 + rv * (h - 6))), fill=(40, 46, 60, 255))
        shimmer = (i * 0.35 + j) % 3.0
        if rise >= 1 and shimmer < 1.0: c.od.rectangle([w[0] - 14, w[1] + 4 - 24 * (shimmer), w[0] - 6, w[1] + 4 - 24 * (shimmer) + 2], fill=(255, 255, 255, 120))
    if T0 <= i < T0 + 10: fx.shock(c, P(262, 120), i - T0, (190, 205, 225), 10, 70, 2)
    # the three balls: each flies at the wall, clangs and ricochets back
    for q, st in enumerate(shots):
        hit = st + 8; age = i - (st + 4)
        tgt = P(246, 100 + q * 20)
        if st + 4 <= i < hit: u = (i - st - 4) / 4; c.ball(lerp(me + face * 6, tgt, u), 5 - 2 * u, r=1.8, glow=(255, 230, 160))
        elif i >= hit:
            a2 = i - hit; bp = tgt + P(-a2 * 5.0, (q - 1) * a2 * 3.0); c.ball(bp, 2 + max(0, 12 * a2 - 2.2 * a2 * a2) * 0.2, r=1.5) if a2 < 16 else None
            fx.burst(c, tgt, a2, q * 13, n=16, speed=3.2, col=(255, 240, 180), life=10)
            fx.shock(c, tgt, a2, (255, 255, 255), 6, 18, 1)
            if a2 < 3: c.shake(5 - a2); c.flash(0.25 * (1 - a2 / 3), (230, 240, 255))
            if a2 < 14:
                c.text(*([int(250 + q * 0) , 52 + q * 22]) if False else (0, 0), '', (0, 0, 0), 1) if False else None
    # CLANG text near each impact (screen overlay)
    for q, st in enumerate(shots):
        a2 = i - (st + 8)
        if 0 <= a2 < 12: c.text(300 + q * 20, 80 + q * 40, 'CLANG', (255, 240, 170), 3 if a2 < 4 else 2)
    c.cam(220, 122, 2.4 + 0.5 * c.ta)


# ======================================================================================================== TT09  PHANTOM PASS
@scene('TT09', N=130, titan=(26, 96), color=(200, 170, 255), result='UNTOUCHED')
def tt09(c):
    i = c.i; T0 = 26
    me = P(110, 124); mate = P(300, 112); face = unit(mate - me)
    defs = [P(165, 120), P(200, 128), P(236, 114)]
    c.dim(0.45 * c.ta, (30, 20, 60))
    K = 34; STRIKE = K + int(10 * 70 / 40)
    if i < K: stand(c, me, face)
    else: c.spr('ps01_through_ball', ak('ps01_through_ball', i, K, 1.0), face, HOME, me)
    stand(c, mate, P(-1, 0.2), HOME) if i < STRIKE + 20 else runner(c, mate + P((i - STRIKE - 20) * 1.2, 0), P(1, 0), i=i)
    age = i - STRIKE
    def bpos(a): return lerp(me + P(8, 0), mate + P(-6, 0), clamp(a / 20))
    for j, d in enumerate(defs):
        # each defender lunges at the ball as it passes; the lunge goes straight through it
        pa = (d[0] - me[0]) / (mate[0] - me[0]) * 20
        if age >= pa - 8 and c.in_titan:
            k = ak('slide', i, STRIKE + pa - 8, 0.8); c.spr('slide', k, P(1, 0.1), AWAY, d + ground(P(1, 0), root_fwd('slide', k) * 0.4))
            if age >= pa and age < pa + 8: fx.shock(c, d + P(4, 0), age - pa, (200, 170, 255), 8, 24, 2); c.spr('guard', 0, P(1, 0), AWAY, d + P(0, -60), alpha=0) if False else None
        else: stand(c, d, unit(me - d) * -1, AWAY)
    if age >= 0 and age <= 22:
        u = clamp(age / 20); bz = 3 + 7 * math.sin(math.pi * u)
        for q in range(8, 0, -1):                                                                          # ghost echoes along the path
            c.ball(bpos(age - q * 1.2), bz, r=1.7, col=(200, 170, 255), glow=(160, 120, 255), alpha=int(110 / q * 3))
        c.ball(bpos(age), bz, r=2.2, col=(235, 225, 255), glow=(170, 130, 255), alpha=150)
        if c.in_titan: fx.trail(c, [tuple(bpos(age - q) - P(0, bz)) for q in range(10, -1, -1)], (200, 170, 255), 170, 2, layer='over')
    elif age > 22: c.ball(mate + P(-6, 0), 1, r=1.5)
    else: c.ball(me + P(7, 0), 1, r=1.5)
    if 20 <= age < 24: c.flash(0.4 * (1 - (age - 20) / 4), (230, 215, 255))
    c.cam(lerp(150, 235, smooth(age / 24)) if age >= 0 else 150, 120, 2.2 + 0.5 * c.ta)


# ======================================================================================================== TT10  HUNDRED YARD STRIKE
@scene('TT10', N=150, titan=(24, 118), color=(255, 214, 80), result='100 YARDS. GOAL.')
def tt10(c):
    i = c.i; T0 = 24
    me = P(52, 150); face = unit(P(300, 120) - me); K = 30; STRIKE = K + int(12 * 70 / 40)
    defs = [P(130, 120), P(196, 150), P(250, 112), P(292, 138)]
    for d in defs: stand(c, d, P(-1, 0.1), AWAY)
    if i < K: stand(c, me, face)
    else: c.spr('sh22_rocket_long_shot', ak('sh22_rocket_long_shot', i, K), face, HOME, me)
    kp = P(GOAL_X - 4, 120); age = i - STRIKE; FL = 54
    u = clamp(age / FL)
    # a huge curving flight that bends around the defenders and drops into the corner
    def ball_at(a):
        u = clamp(a / FL); x = lerp(me[0] + 8, GOAL_X + 6, u); y = lerp(150, 112, u) + 24 * math.sin(math.pi * u) * (1 if True else 0) * math.cos(u * 3.2)
        return P(x, y), 4 + 62 * math.sin(math.pi * u) ** 0.8
    if age >= 0 and u < 1:
        bp, bz = ball_at(age); pts = [tuple(ball_at(age - q)[0] - P(0, ball_at(age - q)[1])) for q in range(20, -1, -1) if age - q >= 0]
        if len(pts) > 1: fx.trail(c, pts, (255, 214, 80), 230, 3, layer='over'); fx.trail(c, [(p[0], p[1] + 1) for p in pts], (255, 120, 40), 150, 2, layer='over')
        c.ball(bp, bz, r=2.4, col=(255, 250, 220), glow=(255, 200, 80)); c.ball(bp, 0, r=1.0, col=(8, 8, 28), alpha=90)
    elif age < 0: c.ball(me + face * 6, 0.8, r=1.5)
    else: c.ball(P(GOAL_X + 6, 114), 3, r=2.0)
    # keeper reads it late
    if age > FL - 14: c.spr('gk02_reach_dive', ak('gk02_reach_dive', i, STRIKE + FL - 14, 0.9), P(-1, 0), KEEP, kp)
    else: stand(c, kp, P(-1, 0), KEEP)
    net_ripple(c, age - FL, 112, (255, 220, 120))
    # camera: stays on the striker for the strike, follows the ball the whole way, snaps to the goal
    if age < 0: c.cam(me[0] + 30, 140, 2.8)
    else:
        bp, bz = ball_at(age); c.cam(max(bp[0], me[0] + 40), 130, lerp(2.6, 1.8, smooth(age / 20)) if age < FL else 2.4)
    c.dim(0.35 * c.ta, (30, 24, 4))
    if age >= 0 and age < FL:                                                                           # live yard counter
        c.text(240, 214, str(int(100 * u)) + ' YD', (255, 214, 80), 3)
    if STRIKE <= i < STRIKE + 4: c.flash(0.6 * (1 - (i - STRIKE) / 4), (255, 240, 190)); c.shake(5)
    if 0 <= age - FL < 4: c.shake(6)


def airborne(c, anim, k, face, skin, p, z, **kw):
    """sprite lifted off the ground by z px, with its shadow staying on the turf"""
    c.shadow(p, 6, 70); c.spr(anim, k, face, skin, p + P(0, -z), shadow=False, dy=z, **kw)


# ======================================================================================================== TT11  DRAGON HEADER
@scene('TT11', N=130, titan=(26, 98), color=(255, 120, 60), result='SCORCHED THE NET')
def tt11(c):
    i = c.i; pos = P(246, 126); face = P(1, 0.05); K = 36; STRIKE = K + int(12 * 70 / 40)
    c.dim(0.5 * c.ta, (40, 10, 4))
    stand(c, P(236, 104), P(1, 0.3), AWAY); stand(c, P(232, 152), P(1, -0.3), AWAY); stand(c, P(300, 118), P(-1, 0.1), AWAY)
    if i < K: stand(c, pos, face)
    else: c.spr('sh12_power_header', ak('sh12_power_header', i, K), face, HOME, pos)
    head = pos + P(3, 0); HZ = 30
    # the cross floats in over the defenders from the wing
    if i < STRIKE:
        u = clamp(i / STRIKE); c.ball(lerp(P(360, 60), head, smooth(u)), lerp(70, HZ, smooth(u)), r=1.4, glow=(255, 140, 60) if u > 0.7 else None)
    age = i - STRIKE
    if age >= 0:
        u = clamp(age / 10); bp = lerp(head, P(GOAL_X + 4, 116), u); bz = lerp(HZ, 10, u)
        # the dragon: a flaming serpent streaming out of the ball, head at the ball
        if age < 16 and c.in_titan:
            n = 26
            for q in range(n):
                t = q / n; back = clamp(u - t * 0.5 * (1 if u > 0.5 else u * 2)); pq = lerp(head, P(GOAL_X + 4, 116), back); zq = lerp(HZ, 10, back)
                wob = math.sin(i * 0.9 + q * 0.7) * (3 + 6 * t); w = 4.5 * (1 - t) + 1
                fx.glow(c, pq + P(0, -zq + wob), 4 + 7 * (1 - t), (255, 90 + int(100 * (1 - t)), 30), 0.7 * (1 - 0.5 * t), 'over')
            hx, hy = bp[0], bp[1] - bz
            c.od.polygon([(hx - 3, hy - 6), (hx + 12, hy - 1), (hx + 12, hy + 3), (hx - 3, hy + 6)], fill=(255, 110, 30, 255), outline=(120, 20, 0, 255))     # snout
            c.od.polygon([(hx + 12, hy + 1), (hx + 6, hy + 5), (hx + 9, hy + 8)], fill=(255, 230, 150, 255))                                                    # lower jaw
            c.od.polygon([(hx - 2, hy - 6), (hx - 6, hy - 12), (hx + 2, hy - 7)], fill=(255, 200, 60, 255))                                                      # horn
            c.od.rectangle([hx + 3, hy - 3, hx + 5, hy - 2], fill=(255, 255, 255, 255))                                                                          # eye
            fx.flame(c, P(hx + 12, hy + 2), age, 5, n=10, spread=2, dirv=(1, 0), rise=1.2)
        if u < 1: c.ball(bp, bz, r=2.2, col=(255, 240, 200), glow=(255, 120, 40))
        fx.shock(c, head + P(0, -10), age, (255, 190, 90), 10, 44, 3)
        if 0 <= age < 4: c.flash(0.6 * (1 - age / 4), (255, 200, 120)); c.shake(5)
    # keeper burned: tries to claim it, gets engulfed
    kp = P(GOAL_X - 5, 120)
    if age >= 8: kk = ak('gk05_claim_cross', i, STRIKE + 2, 0.8); c.spr('gk05_claim_cross', kk, P(-1, 0), KEEP, kp, tint_rgb=(30, 20, 20) if age > 14 else None, tint_a=255, mix=clamp((age - 12) / 8) * 0.8)
    else: stand(c, kp, P(-1, 0), KEEP)
    if age >= 10:
        for q in range(6): fx.flame(c, P(GOAL_X + 3 + q * 1.3, 108 + q * 4), age + q, q * 9, n=5, spread=2, dirv=(0, -1), rise=1.5, layer='over')
        net_ripple(c, age - 10, 116, (255, 160, 60))
    c.cam(lerp(pos[0], 296, smooth((age) / 14)) if age >= 0 else pos[0] + 10, 118, 3.0 if age < 0 else lerp(3.0, 2.4, smooth(age / 14)))


# ======================================================================================================== TT12  STEEL GOALKEEPER
@scene('TT12', N=150, titan=(24, 124), color=(190, 205, 225), result='THREE SAVES. ZERO GOALS.')
def tt12(c):
    i = c.i; kp = P(GOAL_X - 8, 120); steel = (190, 205, 225)
    c.dim(0.4 * c.ta, (14, 20, 36))
    shooters = [P(200, 90), P(190, 150), P(216, 124)]
    anims = ['gk02_reach_dive', 'gk09_low_dive', 'gk24_fingertip_save']
    shots = [40, 76, 112]
    tgts = [P(GOAL_X - 4, 100), P(GOAL_X - 4, 104), P(GOAL_X - 4, 98)]
    # keeper turns to steel when the Titan starts, with a glint sweeping over him
    metal = clamp((i - 24) / 6) * c.ta
    cur = None
    for q, (st, an) in enumerate(zip(shots, anims)):
        if st - 2 <= i < st + 34: cur = (q, st, an)
    if cur:
        q, st, an = cur; k = ak(an, i, st - 9, 1.0); c.spr(an, k, P(-1, 0), KEEP, kp + P(0, -0.0), tint_rgb=steel, tint_a=255, mix=0.55 * metal)
    else: c.spr('guard', int(i * 40 / 85) % 12, P(-1, 0), KEEP, kp, tint_rgb=steel, tint_a=255, mix=0.55 * metal)
    if metal > 0:
        gl = (i * 3) % 40; fx.glow(c, kp + P(-3, -18 + (gl % 20)), 5, (255, 255, 255), 0.5 * metal, 'over'); fx.ring(c, kp, 10, steel, 160 * metal)
    for q, (sh, st, tg) in enumerate(zip(shooters, shots, tgts)):
        face = unit(kp - sh)
        if st - 10 <= i < st + 10: c.spr('sh02_instep_drive', ak('sh02_instep_drive', i, st - 10), face, HOME, sh)
        else: stand(c, sh, face)
        a = i - st
        if 0 <= a < 8: c.ball(lerp(sh + face * 7, tg, a / 8), 3 + 4 * math.sin(math.pi * a / 8), r=1.8, glow=(255, 240, 180))
        if a >= 8:
            a2 = a - 8; bp = tg + P(-a2 * 4.0, (q - 1) * -a2 * 3.0)
            if a2 < 16: c.ball(bp, 4 + 2 * a2 * 0.4, r=1.6)
            fx.burst(c, tg + P(0, -6), a2, q * 7 + 1, n=16, speed=3, col=(255, 245, 200), life=10); fx.shock(c, tg + P(0, -6), a2, (255, 255, 255), 7, 22, 1)
            if a2 < 3: c.shake(4 - a2); c.flash(0.2 * (1 - a2 / 3), (230, 240, 255))
            if 0 <= a2 < 14: c.text(262, 60 + 36 * q, 'SAVED', (255, 245, 200), 3 if a2 < 4 else 2)
    c.cam(280, 118, 2.6 + 0.2 * c.ta)


# ======================================================================================================== TT13  EARTHQUAKE TACKLE
@scene('TT13', N=130, titan=(24, 96), color=(205, 150, 90), result='THEY ALL WENT DOWN')
def tt13(c):
    i = c.i; me = P(200, 124); K = 36; IMPACT = K + int(8 * 60 / 40)
    c.dim(0.45 * c.ta, (36, 20, 6))
    if i < K: stand(c, me, P(0, 1))
    else: c.spr('tt13_earthquake_tackle', ak('tt13_earthquake_tackle', i, K), P(0, 1), HOME, me)
    foes = [P(166, 112), P(236, 108), P(170, 148), P(232, 146), P(200, 164), P(200, 90)]
    age = i - IMPACT
    for j, d in enumerate(foes):
        dist = float(np.linalg.norm((d - me) * P(1, 2.0))); hit = dist / 3.2
        if age < hit: stand(c, d, unit(me - d), AWAY)
        else:
            a = age - hit; z = max(0.0, 26 * a - 2.1 * a * a); push = unit(d - me) * min(a, 8) * 1.6
            if z > 0.5: airborne(c, 'slide', 14 if a < 8 else 18, unit(me - d), AWAY, d + push * P(1, 0.5), z, tint_rgb=(205, 150, 90), tint_a=255, mix=0.15)
            else: c.spr('slide', min(21, 14 + int((a - 11) / 2)), unit(me - d), AWAY, d + push * P(1, 0.5))
            fx.burst(c, d, int(a), j * 13, n=10, speed=2.2, col=(150, 110, 70), life=16, size=2) if a < 16 else None
    if age >= 0:
        fx.cracks(c, me, age, 3, n=12, length=70); fx.cracks(c, me, age - 2, 9, n=8, length=40, col=(20, 12, 8))
        fx.shock(c, me, age, (230, 180, 120), 14, 110, 4, 'under'); fx.burst(c, me, age, 21, n=26, speed=3.4, col=(160, 120, 80), life=22, size=2)
        fx.glow(c, me, 28 * clamp(1 - age / 20), (205, 150, 90), 0.6)
        c.shake(8 * clamp(1 - age / 22)); 
        if age < 3: c.flash(0.5 * (1 - age / 3), (255, 225, 170))
    c.ball(me + P(14, 6), 1 if age < 0 else 1 + max(0, 26 * age - 2.1 * age * age) * 0.35, r=1.4)
    c.cam(200, 124, 2.0 + 0.8 * smooth((i - 20) / 16) - 0.7 * smooth((age) / 14))


# ======================================================================================================== TT14  WIND WALK
@scene('TT14', N=150, titan=(24, 120), color=(170, 230, 255), result='UNTACKLEABLE')
def tt14(c):
    i = c.i; T0 = 24
    path = line_track([(0, (40, 126)), (T0, (100, 126)), (60, (150, 112)), (90, (200, 134)), (120, (262, 116)), (150, (330, 124))])
    pos = path(i); nx = path(i + 2); face = unit(nx - pos)
    c.dim(0.35 * c.ta, (10, 30, 50))
    k = ak('dr17_drive_through', i, 0, 1.0, loop=True); c.spr('dr17_drive_through', k, face, HOME, pos); c.ball(pos + face * 7, 1.5)
    defs = [P(130, 124), P(190, 112), P(240, 136)]
    for j, d in enumerate(defs):
        lunge = int(30 + 28 * (j + 1.0) * 1.0) + 10 * j
        near = pos[0] - d[0]
        if c.in_titan and near > -20:
            a = i - (i - int(near + 20))   # progress by distance
            t = clamp((near + 20) / 36.0); blown = clamp((near - 6) / 22.0)
            k2 = int(t * 12); push = P(-10 * blown, (-1 if j % 2 == 0 else 1) * 26 * blown)
            c.spr('slide', k2, P(1, 0.3 * (1 if j % 2 else -1)), AWAY, d + push + ground(P(1, 0), root_fwd('slide', k2) * 0.5), alpha=int(255 - 70 * blown))
            if 0.3 < blown < 1.0:
                for q in range(6): fx.trail(c, [tuple(d + P(-4 * q, -4 * q + 10 * (z - 2.5)) + P(0, 4 * math.sin(i * 0.8 + q + z))) for z in range(5)], (200, 240, 255), 160, 1, layer='over')
        else: stand(c, d, unit(pos - d), AWAY)
    if c.in_titan:
        # a cyclone wrapped round the legs: stacked rings spinning, wind streaks and leaves
        for q in range(7):
            r = 5 + q * 1.4; yy = 3 - q * 2.5; ph = i * 0.6 + q
            fx.ring(c, pos + P(0, yy), r, (190, 240, 255), 170 * c.ta, 'over', k=0.35)
            ang = ph; c.od.rectangle([pos[0] + math.cos(ang) * r, pos[1] + yy + math.sin(ang) * r * 0.35, pos[0] + math.cos(ang) * r + 1, pos[1] + yy + math.sin(ang) * r * 0.35 + 1], fill=(255, 255, 255, 255))
        for q in range(10):
            rng = random.Random(i * 5 + q); a = rng.uniform(0, 6.28); r = rng.uniform(8, 24)
            c.od.line([(pos[0] + math.cos(a) * r, pos[1] - 6 + math.sin(a) * r * 0.4), (pos[0] + math.cos(a + 0.8) * r, pos[1] - 6 + math.sin(a + 0.8) * r * 0.4)], fill=(210, 245, 255, 200), width=1)
        fx.glow(c, pos + P(0, -6), 16, (170, 230, 255), 0.35 * c.ta)
    c.cam(pos[0] + 28, 122, 2.6)
    for q in range(8):                                                                                  # gusts across the screen
        rng = random.Random(i * 7 + q); y = rng.randint(34, 236); xx = (rng.randint(0, 480) - i * 90) % 600 - 60
        c.sd.arc([xx, y - 6, xx + 60, y + 6], 180, 360, fill=(220, 245, 255, int(120 * c.ta)), width=1)


# ======================================================================================================== TT15  METEOR SHOT
@scene('TT15', N=140, titan=(26, 100), color=(255, 130, 40), result='BURNED THE KEEPER')
def tt15(c):
    i = c.i; me = P(214, 132); K = 34; STRIKE = K + int(12 * 70 / 40); face = unit(P(GOAL_X, 118) - me)
    c.dim(0.5 * c.ta, (40, 12, 4))
    if i < K: stand(c, me, face)
    else: c.spr('sh19_dipping_drive', ak('sh19_dipping_drive', i, K), face, HOME, me)
    age = i - STRIKE; FL = 20; kp = P(GOAL_X - 6, 120)
    def b_at(a):
        u = clamp(a / FL); x = lerp(me[0] + 8, GOAL_X + 2, u); y = lerp(me[1], 114, u); z = 8 + 78 * math.sin(math.pi * min(u * 1.15, 1.0)) ** 1.0 * (1 - u) ** 0.3 - 8 * u
        return P(x, y), max(1.5, z)
    if age < 0: c.ball(me + face * 6, 1, r=1.5)
    elif age < FL:
        bp, bz = b_at(age)
        for q in range(14, 0, -1):                                                                          # smoke and flame trail
            tp, tz = b_at(age - q * 0.9) if age - q * 0.9 >= 0 else (bp, bz)
            fx.glow(c, tp + P(0, -tz), 5 + q * 0.5, (255, 100 + 6 * (14 - q), 30), 0.5 * (1 - q / 15), 'over')
            fx.glow(c, tp + P(0, -tz - 2), 4 + q * 0.7, (50, 40, 40), 0.25 * (1 - q / 15), 'over')
        fx.flame(c, bp + P(0, -bz), age, 3, n=14, spread=3, dirv=(-1, -0.4), rise=1.2); c.ball(bp, bz, r=2.8, col=(255, 235, 170), glow=(255, 110, 30))
        c.ball(bp, 0, r=1.0, col=(8, 8, 28), alpha=90)
    else:
        a2 = age - FL
        fx.glow(c, P(GOAL_X, 118), 36 * clamp(1 - a2 / 14), (255, 140, 40), 0.9, 'over'); fx.shock(c, P(GOAL_X - 2, 118), a2, (255, 200, 90), 12, 60, 3)
        fx.burst(c, P(GOAL_X, 118), a2, 31, n=34, speed=4.0, col=(255, 160, 50), life=24, size=2)
        for q in range(7): fx.flame(c, P(GOAL_X + 1 + q * 1.1, 104 + q * 5), a2 + q, q * 5, n=5, spread=2, dirv=(0, -1), rise=1.7)
        net_ripple(c, a2, 118, (255, 150, 50))
        if a2 < 4: c.flash(0.8 * (1 - a2 / 4), (255, 220, 160)); c.shake(8 - a2 * 2)
    # keeper hit: knocked flat, scorched
    if age >= FL: a2 = age - FL; c.spr('slide', min(21, 10 + a2 // 2), P(-1, 0), KEEP, kp + P(min(a2, 10) * 1.4, 0), tint_rgb=(25, 18, 18), tint_a=255, mix=clamp(a2 / 10) * 0.8)
    else: c.spr('guard', int(i * 40 / 85) % 12, P(-1, 0), KEEP, kp)
    # camera: on the striker, then tilts up to follow the fireball, then snaps to the goal
    if age < 0: c.cam(me[0] + 24, 122, 3.0)
    elif age < FL: bp, bz = b_at(age); c.cam(lerp(me[0] + 30, 292, smooth(age / FL)), lerp(122, 100, smooth(age / FL)), 2.2)
    else: c.cam(296, 118, 3.0)


# ======================================================================================================== TT16  CHAIN LIGHTNING
@scene('TT16', N=140, titan=(26, 100), color=(255, 226, 60), result='THREE PASSES. ZERO TIME.')
def tt16(c):
    i = c.i; A, B, C_, D = P(96, 126), P(168, 92), P(238, 154), P(296, 108); T0 = 26
    c.dim(0.45 * c.ta, (30, 28, 0))
    nodes = [A, B, C_, D]; Z = [46, 54, 62]                                                         # the three arcs fire a few frames apart
    for d in (P(130, 112), P(200, 128), P(262, 128)): stand(c, d, P(-1, 0), AWAY)
    ball_at = A + P(7, 0); stage = 0
    for q, z in enumerate(Z):
        if i >= z + 1: stage = q + 1
    ball_at = nodes[stage] + unit(nodes[min(stage + 1, 3)] - nodes[stage]) * 7
    # passer winds up, the others wait on their toes; each receiver flashes white as the bolt lands
    if i < 40: stand(c, A, unit(B - A))
    else: c.spr('ps03_driven_pass', ak('ps03_driven_pass', i, 38, 1.0), unit(B - A), HOME, A)
    for q, N_ in enumerate(nodes[1:3], start=1):
        flashing = Z[q - 1] + 1 <= i <= Z[q - 1] + 3
        stand(c, N_, unit(nodes[q + 1] - N_), HOME, tint_rgb=(255, 255, 255) if flashing else None, tint_a=255, mix=0.8)
    # D: receives, then a one-touch finish
    SD = 70; STR = SD + 14
    if i < SD: stand(c, D, unit(GOAL - D), HOME, tint_rgb=(255, 255, 255) if Z[2] + 1 <= i <= Z[2] + 3 else None, tint_a=255, mix=0.8)
    else: c.spr('sh24_one_touch_finish', ak('sh24_one_touch_finish', i, SD), unit(GOAL - D), HOME, D)
    for q, z in enumerate(Z):
        age = i - z
        if 0 <= age <= 3: fx.bolt(c, nodes[q] + P(0, -12), nodes[q + 1] + P(0, -12), z * 31 + age * 7, a=int(255 * (1 - age / 4)), jag=8)
        if 0 <= age <= 3: fx.bolt(c, nodes[q] + P(0, -12), nodes[q + 1] + P(0, -12), z * 17 + age * 5 + 3, col=(255, 230, 90), a=int(200 * (1 - age / 4)), jag=11, w=2)
        fx.shock(c, nodes[q + 1], i - z - 1, (255, 235, 120), 8, 28, 2)
        if 0 <= age < 14: fx.glow(c, nodes[q + 1] + P(0, -10), 22 * (1 - age / 14), (255, 230, 120), 0.8, 'over')
    if stage < 3 or i < STR: c.ball(ball_at, 1.5, r=1.5, glow=(255, 230, 100) if c.in_titan else None)
    age = i - STR
    if age >= 0:
        u = clamp(age / 8); bp = lerp(D + P(8, 0), P(GOAL_X + 4, 108), u); c.ball(bp, 4 + 3 * u, r=2, glow=(255, 230, 100))
        fx.trail(c, [tuple(lerp(D + P(8, 0), P(GOAL_X + 4, 108), clamp((age - q) / 8)) - P(0, 5)) for q in range(6, -1, -1)], (255, 230, 60), 230, 2, layer='over')
        net_ripple(c, age - 8, 108, (255, 230, 120))
    kp = P(GOAL_X - 4, 120)
    if age >= 6: c.spr('gk02_reach_dive', ak('gk02_reach_dive', i, STR + 6, 0.8), P(-1, 0), KEEP, kp)
    else: stand(c, kp, P(-1, 0), KEEP)
    focus = lerp(A[0] + 40, 292, smooth((i - 26) / 50)) if i < 76 else 292
    c.cam(focus, 122, 1.9 if i < 76 else 2.6)


# ======================================================================================================== TT17  BLACK HOLE
@scene('TT17', N=150, titan=(26, 118), color=(160, 110, 255), result='DEFENCE SWALLOWED')
def tt17(c):
    i = c.i; me = P(138, 126); T0 = 26; hole = P(206, 122)
    c.dim(0.5 * c.ta, (14, 4, 36))
    rad = 20 * smooth((i - T0) / 18) * (1 - smooth((i - 100) / 6)) if c.in_titan else 0
    # the attacker raises an arm and the sky tears open
    if i < T0 - 4: stand(c, me, P(1, 0))
    else: c.spr('df09_offside_trap', min(11, ak('df09_offside_trap', i, T0 - 4)), P(1, 0), HOME, me)
    foes = [(P(190, 96), 0.0), (P(232, 100), 1.0), (P(250, 128), 2.1), (P(228, 156), 3.2), (P(186, 150), 4.4)]
    for j, (d, ph) in enumerate(foes):
        dv = d - hole; r0 = float(np.linalg.norm(dv * P(1, 2.0))); a0 = math.atan2(dv[1] * 2, dv[0])
        pull = clamp((i - T0 - 8 - j * 3) / 50) if c.in_titan else 0
        if i >= 100: pull = 1.0 if i < 104 else 1.0
        r = r0 * (1 - 0.92 * pull ** 1.5); a = a0 + pull * 7.0
        pp = hole + P(math.cos(a) * r, math.sin(a) * r / 2.0)
        if pull < 0.97:
            airborne(c, 'run', int(i * 0.6) % 12, int((a * 32 / (2 * math.pi)) + 8) % 32, AWAY, pp, 10 * pull ** 1.4, alpha=int(255 - 200 * pull ** 3), tint_rgb=(160, 110, 255), tint_a=255, mix=0.4 * pull)
        elif i >= 104 + j * 2:                                                                          # spat back out, dazed on the grass
            ee = i - (104 + j * 2); out = d + P(0, 0); c.spr('slide', min(21, 15 + ee // 2), P(-1, 0.2), AWAY, out); fx.stars(c, out, i + j * 5, z=10) if ee > 6 else None
    if rad > 1:
        # the hole itself: dark core, a hot accretion ring tilted on the ground plane, lensing
        for q in range(14):
            a = i * 0.25 + q * 0.45; rr = rad * (1.0 + 0.35 * math.sin(q))
            c.od.line([(hole[0] + math.cos(a) * rr * 1.4, hole[1] - 22 + math.sin(a) * rr * 0.45), (hole[0] + math.cos(a + 0.4) * rr * 1.4, hole[1] - 22 + math.sin(a + 0.4) * rr * 0.45)], fill=(200, 160, 255, 220), width=1)
        fx.ring(c, hole + P(0, -22), rad * 1.5, (170, 120, 255), 220, 'over', k=0.35, width=2)
        c.od.ellipse([hole[0] - rad * 0.6, hole[1] - 22 - rad * 0.6, hole[0] + rad * 0.6, hole[1] - 22 + rad * 0.6], fill=(3, 0, 10, 255))
        fx.glow(c, hole + P(0, -22), rad * 2.0, (120, 70, 220), 0.55)
        sx, sy = (hole[0] - (210 - 480 / 2 / 2.6)) * 2.6, (hole[1] - 22 - (122 - 270 / 2 / 2.6)) * 2.6
        c.after(fx.radial_warp(sx, sy, 0.35 * min(1.0, rad / 20)))
    if 100 <= i < 108: c.flash(0.9 * (1 - (i - 100) / 8), (230, 210, 255)); c.shake(6)
    c.cam(210, 122, 2.6)


# ======================================================================================================== TT18  MIRROR MATCH
@scene('TT18', N=130, titan=(26, 100), color=(170, 220, 255), result='CARD COPIED')
def tt18(c):
    i = c.i; opp = P(150, 126); us = P(272, 126); K = 34
    c.dim(0.5 * c.ta, (10, 26, 50))
    k = ak('dr09_cruyff_turn', i, K, 1.0)
    # the opponent plays their card ...
    if i < K: stand(c, opp, P(1, 0), AWAY)
    else: c.spr('dr09_cruyff_turn', k, P(1, 0.0), AWAY, opp)
    cx0 = 70 + 0 * i; up = smooth((i - (K - 12)) / 10) * (1 - smooth((i - (K + 10)) / 8))
    if up > 0.02: fx.mini_card(c.od, opp[0] - 6, opp[1] - 54 - 18 * up, 16, 22, col=(255, 130, 130), a=int(255 * up))
    # ... a pane of mirror glass slams down between us: it flashes and shatters outward
    mx = 210; pane = smooth((i - (K + 8)) / 6)
    if i >= K + 8:
        h = 78 * pane
        c.od.polygon([(mx - 5, 126 - h), (mx + 5, 126 - h), (mx + 5, 126 + 18), (mx - 5, 126 + 18)], fill=(190, 225, 255, int(150 * clamp(1 - (i - K - 30) / 30))), outline=(255, 255, 255, 255))
        sh = ((i - K) * 3) % 60; c.od.polygon([(mx - 4, 126 - h + sh), (mx + 1, 126 - h + sh), (mx + 4, 126 - h + sh + 14), (mx - 1, 126 - h + sh + 14)], fill=(255, 255, 255, 190))
        fx.shock(c, P(mx, 128), i - K - 8, (200, 235, 255), 10, 36, 2)
    # ... and OUR player does exactly the same, mirrored, with a copy of the card
    ours = i - (K + 14)
    if i < K + 14: stand(c, us, P(-1, 0), HOME)
    else: c.spr('dr09_cruyff_turn', ak('dr09_cruyff_turn', i, K + 14, 1.0), P(-1, 0.0), HOME, us)
    up2 = smooth((i - (K + 6)) / 10) * (1 - smooth((i - (K + 28)) / 8))
    if up2 > 0.02: fx.mini_card(c.od, us[0] - 6, us[1] - 54 - 18 * up2, 16, 22, col=(120, 220, 255), a=int(255 * up2))
    if i > K + 8: fx.glow(c, us + P(0, -14), 20, (170, 220, 255), 0.35, 'under')
    for q in range(10):                                                                               # glass shards drifting off the pane
        if i >= K + 30:
            rng = random.Random(q); a = i - K - 30; x = mx + rng.uniform(-6, 6) + rng.uniform(-1, 1) * a * 1.5; y = 100 + rng.uniform(0, 40) + a * 1.2
            if a < 24: c.od.polygon([(x, y), (x + 3, y + 1), (x + 1, y + 4)], fill=(210, 240, 255, int(220 * (1 - a / 24))))
    c.ball(opp + P(6, 0), 1.0, r=1.4) if i < K + 4 else c.ball(us + P(-6, 0), 1.0, r=1.4)
    c.cam(210, 124, 2.5 + 0.3 * c.ta)


# ======================================================================================================== TT19  SECOND HEART
@scene('TT19', N=140, titan=(26, 102), color=(255, 100, 130), result='FULL STAMINA. WHOLE TEAM.')
def tt19(c):
    i = c.i; T0 = 26
    base = [P(70, 86), P(70, 160), P(120, 70), P(120, 124), P(120, 176), P(180, 96), P(180, 150), P(236, 70), P(236, 124), P(236, 176)]
    beats = [44, 62, 80]
    def fill_at(j):
        f = 0.12 + 0.02 * (j % 3)
        for b in beats:
            f = max(f, min(1.0, f + 0.3 * smooth((i - b) / 8))) if i > b else f
        return min(1.0, 0.12 + 0.02 * (j % 3) + sum(0.3 * smooth((i - b) / 8) for b in beats if i > b))
    drift = i * 0.12
    for j, bpos in enumerate(base):
        f = fill_at(j); pos = bpos + P(drift * (0.5 + f), 0.0)
        if i < 44: runner(c, pos + P(0, 0.0), P(1, 0.0), i=i, rate=0.45 + j * 0.01, tint_rgb=(120, 100, 120), tint_a=255, mix=0.3 * (1 - f / 0.5))             # tired: slow, grey-ish
        else: runner(c, pos, P(1, 0), i=i, rate=0.45 + 1.5 * f, tint_rgb=(255, 120, 150), tint_a=255, mix=0.3 * clamp(1 - (i - 44) / 40) if False else 0.0)
        # stamina bar floating over the head
        bw = 14; bx, by = pos[0] - bw / 2, pos[1] - 34
        c.od.rectangle([bx - 1, by - 1, bx + bw, by + 2], fill=(10, 8, 24, 255)); col = (255, 70, 70) if f < 0.35 else ((255, 214, 80) if f < 0.7 else (110, 240, 120))
        c.od.rectangle([bx, by, bx + max(1, int(bw * f)), by + 1], fill=col + (255,))
    cam_x = 150 + drift * 0.9 * 1.5
    c.cam(cam_x, 122, 2.0)
    # the second heart: three big beats, each sends a pink pulse across the whole pitch
    if c.in_titan:
        for b in beats:
            a = i - b
            if 0 <= a < 14:
                S = 6 + (5 if a < 3 else 0) - a * 0.2
                heart(c, 240, 84, S)
        for b in beats:
            a = i - b
            if 0 <= a < 26:
                r = 6 + a * 22; c.sd.ellipse([240 - r, 135 - r * 0.55, 240 + r, 135 + r * 0.55], outline=(255, 100, 130, int(220 * (1 - a / 26))), width=3)
        c.after(fx.wash((255, 90, 120), 0.18 * max(0, 1 - min(abs(i - b) for b in beats) / 5.0)))
    for b in beats:
        if i == b: c.shake(5)


def heart(c, x, y, S): fx.heart(c, x, y, S)


# ======================================================================================================== TT20  TITAN SLIDE
@scene('TT20', N=140, titan=(26, 100), color=(255, 150, 50), result='BALL WON')
def tt20(c):
    i = c.i; T0 = 26; me0 = P(60, 134); K = 34
    c.dim(0.45 * c.ta, (40, 18, 4))
    # an attacker dribbles away across the pitch
    ap = P(196 + 0.7 * i, 118 + 4 * math.sin(i * 0.1)); AF = P(1, 0.0)
    steal = 74
    if i < steal: runner(c, ap, AF, AWAY, i=i); ball = ap + P(7, 0)
    else: a2 = i - steal; c.spr('slide', min(21, 6 + a2 // 2), AF, AWAY, ap + P(a2 * 0.6, 0)); ball = ap + P(7, 0) + P(0, 0)
    # the defender sprints, then launches into a slide that cannot miss
    if i < K: pos = me0 + P(i * 1.3, 0); runner(c, pos, P(1, 0), i=i, rate=1.5)
    else:
        k = ak('slide', i, K, 0.95); u = clamp(i - K) ; total = 22; pe = P(ap[0] + 0.7 * (steal - i) * 0, ap[1])
        tgt_end = P(190 + 0.7 * steal + 8, 120)
        start = me0 + P(K * 1.3, 0); u2 = smooth((i - K) / (steal - K + 2)) if i < steal + 2 else 1.0
        pos = lerp(start, tgt_end, u2); c.spr('slide', k, P(1, 0.0), HOME, pos)
        if i < steal + 4:
            for q in range(10): fx.flame(c, pos + P(-q * 3.0, 3 + 0.4 * q), q, i * 7 + q, n=4, spread=1 + q * 0.3, dirv=(-1, 0.1), rise=0.7, layer='under', size=2)
            fx.glow(c, pos + P(-6, 0), 14, (255, 140, 40), 0.55)
    # the lock-on reticle on the ball
    if c.in_titan and i < steal + 2:
        lk = clamp((i - T0) / 14); r = 28 - 20 * lk; fx.reticle(c, ball + P(0, -2), r, i * 0.3 * (1 - lk), (255, 70, 70)); c.text(240, 54, 'LOCKED' if lk >= 1 else 'LOCKING...', (255, 100, 90), 2)
    if i < steal + 2: c.ball(ball, 1.3, r=1.5)
    else:
        a = i - steal - 2; c.ball(ball + P(-a * 2.5, 0), 2 + max(0, 16 * a - 1.4 * a * a) * 0.25, r=1.6)
        fx.shock(c, ball, a, (255, 190, 90), 9, 40, 3); fx.burst(c, ball, a, 19, n=20, speed=3.2, col=(255, 160, 50), life=16)
        if a < 3: c.flash(0.5 * (1 - a / 3)); c.shake(5)
    tgt = lerp(P(110, 126), P(240, 122), smooth(i / 76)) if i < steal + 6 else P(250, 122)
    c.cam(tgt[0] + 10, 124, 2.0 if i < K else 2.6)


# ======================================================================================================== TT21  SKYFALL
@scene('TT21', N=140, titan=(24, 104), color=(255, 140, 50), result='DROPPED FROM THE SKY')
def tt21(c):
    i = c.i; me = P(74, 130); tgt = P(292, 126); K = 30; STRIKE = K + int(10 * 70 / 40); IMP = 86
    c.dim(0.5 * c.ta, (40, 14, 6))
    for d in (P(272, 108), P(310, 142), P(262, 152)): stand(c, d, P(-1, 0.1), AWAY) if i < IMP + 6 else None
    if i < K: stand(c, me, P(1, 0.1))
    else: c.spr('ps18_long_ball_forward', ak('ps18_long_ball_forward', i, K), P(1, 0.0), HOME, me)
    # the ball goes straight up and out of the top of the screen; a warning circle blooms on the grass
    age = i - STRIKE
    if age < 0: c.ball(me + P(8, 0), 1, r=1.5)
    elif i < IMP - 22: u = age / (IMP - 22 - STRIKE); c.ball(lerp(me + P(8, 0), P(180, 126), u), 60 + 180 * math.sin(math.pi * min(u, 1) * 0.5), r=1.5)
    if c.in_titan and i > STRIKE + 6 and i < IMP + 2:
        w = clamp((i - STRIKE - 6) / (IMP - STRIKE - 6)); r = 40 * (1 - 0.35 * w)
        fx.ring(c, tgt, r, (255, 80, 60), 230, 'under', width=2); fx.ring(c, tgt, r * 0.6 * w, (255, 200, 90), 200, 'under'); fx.glow(c, tgt, r, (255, 70, 40), 0.25 * w)
        if int(i / 3) % 2 == 0: fx.reticle(c, tgt, r * 0.5, i * 0.1, (255, 90, 60), 230, 'under')
    # the meteor: a fireball streaking down the screen diagonal onto the circle
    if IMP - 22 <= i < IMP:
        u = (i - (IMP - 22)) / 22.0; zz = 220 * (1 - u) ** 1.3; bp = lerp(P(tgt[0] - 60, tgt[1] - 4), tgt, u)
        for q in range(16): tpz = 220 * (1 - max(0, u - q * 0.02)) ** 1.3; tp = lerp(P(tgt[0] - 60, tgt[1] - 4), tgt, max(0, u - q * 0.02)); fx.glow(c, tp + P(0, -tpz * 0.5), 6 + q * 0.8, (255, 110 + q * 5, 30), 0.6 * (1 - q / 17), 'over')
        c.ball(bp, zz * 0.5, r=3.5, col=(255, 240, 190), glow=(255, 110, 30)); fx.flame(c, bp + P(0, -zz * 0.5), i, 4, n=14, spread=3, dirv=(-1, -1), rise=1.2)
    if i >= IMP:
        a = i - IMP
        fx.cracks(c, tgt, a, 4, n=10, length=46); fx.shock(c, tgt, a, (255, 200, 110), 14, 110, 4, 'under'); fx.burst(c, tgt, a, 31, n=30, speed=4.0, col=(255, 150, 50), life=26, size=2)
        fx.glow(c, tgt + P(0, -4), 34 * clamp(1 - a / 16), (255, 150, 60), 0.9, 'over')
        if a < 5: c.flash(0.9 * (1 - a / 5), (255, 225, 170)); c.shake(9 - a)
        c.ball(tgt + P(-2, 0), 2 + max(0, 14 * a - 1.5 * a * a) * 0.3, r=1.6)
        mate = tgt + P(-16, 6); runner(c, mate + P(max(0, a - 12) * 0.8, 0), P(1, 0), i=i)                          # the receiver trots onto it
    else: stand(c, tgt + P(-16, 6), P(1, 0), HOME)
    c.cam(lerp(150, 292, smooth((i - 20) / 56)) if i < 96 else 292, 124, 1.7 if i < 80 else 2.8)


# ======================================================================================================== TT22  LOCK ON
@scene('TT22', N=140, titan=(24, 104), color=(255, 70, 70), result='TARGET HIT')
def tt22(c):
    i = c.i; me = P(228, 128); K = 60; STRIKE = K + int(10 * 70 / 40); tgt = P(GOAL_X - 2, 98); face = unit(P(GOAL_X, 110) - me)
    c.dim(0.45 * c.ta, (30, 6, 10))
    wall = [P(272, 106), P(276, 124), P(280, 142)]
    for w in wall: stand(c, w, P(-1, 0), AWAY)
    if i < K: stand(c, me, face)
    else: c.spr('sh17_far_post_bender', ak('sh17_far_post_bender', i, K), face, HOME, me)
    kp = P(GOAL_X - 5, 124)
    # the reticle drifts across the goal, then locks onto the top corner: it tightens with each lock
    lock = clamp((i - 30) / 26)
    if c.in_titan and i < STRIKE + 16:
        rp = lerp(P(GOAL_X - 2, 130) + P(0, 30 * math.sin(i * 0.4) * (1 - lock)), tgt, smooth(lock)) if i < 56 else tgt
        sz = 34 - 22 * smooth(lock) + 2 * math.sin(i * 0.9)
        fx.reticle(c, rp, sz, i * 0.12 * (1 - lock) + lock * 0.78, (255, 70, 70), 255)
        fx.ring(c, rp, sz * 1.3, (255, 70, 70), 120 + 100 * lock) if lock < 1 else fx.ring(c, rp, sz * 1.5, (255, 255, 255), 230)
        c.text(240, 56, 'LOCK ON' if lock >= 1 else 'ACQUIRING', (255, 90, 90), 2)
        if int(i / 4) % 2 and lock >= 1: c.sd.rectangle([200, 232, 280, 246], outline=(255, 70, 70, 255), width=1)
    age = i - STRIKE
    if age < 0: c.ball(me + face * 7, 1, r=1.5)
    elif age < 16:
        u = clamp(age / 16); base = lerp(me + face * 7, tgt + P(0, 22), u); bend = P(0, -38 * math.sin(math.pi * u) ** 1.2) + P(0, 0)                  # wide arc round the wall
        bp = base + P(0, -bend[1] * 0.0) ; arc = 34 * math.sin(math.pi * u); bz = 4 + 20 * u + 10 * math.sin(math.pi * u)
        c.ball(bp + P(0, arc * 0.0), bz, r=2.0, glow=(255, 90, 90))
        fx.trail(c, [tuple(lerp(me + face * 7, tgt + P(0, 22), clamp((age - q) / 16)) - P(0, 4 + 20 * clamp((age - q) / 16) + 10 * math.sin(math.pi * clamp((age - q) / 16)))) for q in range(8, -1, -1)], (255, 90, 90), 230, 2, layer='over')
    else:
        net_ripple(c, age - 16, 98, (255, 100, 100)); c.ball(P(GOAL_X + 6, 100), 12, r=2.0)
        fx.shock(c, tgt + P(0, 14), age - 16, (255, 255, 255), 8, 30, 2)
    if age >= 8: c.spr('gk02_reach_dive', ak('gk02_reach_dive', i, STRIKE + 8, 0.8), P(-1, 0), KEEP, kp)
    else: stand(c, kp, P(-1, 0), KEEP)
    sl = smooth((i - 24) / 12) * (1 - smooth((i - STRIKE - 14) / 8))
    c.cam(lerp(me[0] + 30, 296, 0.5 + 0.5 * smooth((age) / 10)) if age > 0 else me[0] + 30 + 24 * sl, 120, 2.2 + 0.6 * sl)
    if 0 <= age - 16 < 4: c.flash(0.7 * (1 - (age - 16) / 4), (255, 190, 190)); c.shake(5)


# ======================================================================================================== TT23  DREAM TEAM
@scene('TT23', N=150, titan=(26, 118), color=(255, 214, 80), result='PERFECT SYNC')
def tt23(c):
    i = c.i; T0 = 26
    form = [P(70, 124), P(120, 80), P(120, 124), P(120, 168), P(176, 62), P(176, 100), P(176, 148), P(176, 186), P(232, 90), P(232, 158)]
    rng = random.Random(3); jit = [P(rng.uniform(-12, 12), rng.uniform(-10, 10)) for _ in form]; ph = [rng.uniform(0, 12) for _ in form]
    s = smooth((i - T0) / 10) if c.in_titan else (1.0 if i >= 118 else 0.0)
    if i >= 112: s = 1 - smooth((i - 112) / 10) * 0.0
    drift = i * 0.5
    pts = []
    for j, f in enumerate(form):
        pos = f + P(drift, 0) + jit[j] * (1 - s)
        pts.append(pos)
        # before the Titan everyone is out of step, after it all twelve limbs hit the ground together
        tstep = i * (40 / 57) + (0 if s > 0.95 else ph[j] * (1 - s))
        c.spr('run', int(tstep) % 12, P(1, 0.0), HOME, pos, tint_rgb=(255, 224, 120) if s > 0.5 else None, tint_a=255, mix=0.18 * s)
    # golden links between neighbours, pulsing with the stride
    if s > 0:
        links = [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3), (1, 4), (1, 5), (2, 5), (2, 6), (3, 6), (3, 7), (4, 5), (5, 6), (6, 7), (5, 8), (6, 9), (8, 9), (5, 9), (6, 8)]
        pulse = 0.6 + 0.4 * math.sin(i * 0.5)
        for a, b in links: c.ud.line([tuple(pts[a] + P(0, -2)), tuple(pts[b] + P(0, -2))], fill=(255, 214, 80, int(170 * s * pulse)), width=1)
        for p_ in pts: fx.glow(c, p_ + P(0, -2), 9, (255, 214, 80), 0.4 * s)
    # the ball zips around the triangle in perfect one-twos, then it is finished off
    cyc = [(1, 5), (5, 2), (2, 6), (6, 8)]
    bi = (i - 52) / 8.0
    if c.in_titan and bi >= 0 and bi < len(cyc):
        a, b = cyc[int(bi)]; u = bi - int(bi); c.ball(lerp(pts[a], pts[b], smooth(u)), 3, r=1.6, glow=(255, 230, 120))
        fx.trail(c, [tuple(lerp(pts[a], pts[b], clamp(u - q * 0.12)) - P(0, 3)) for q in range(5, -1, -1)], (255, 214, 80), 220, 2, layer='over')
    elif bi >= len(cyc) and i < 100: sh = pts[8]; c.ball(lerp(sh, P(GOAL_X + 4, 112), smooth(clamp((i - 52 - len(cyc) * 8) / 10))) + P(drift * 0, 0), 4, r=1.8, glow=(255, 230, 120))
    else: c.ball(pts[0] + P(7, 0), 1.0, r=1.5)
    if i >= 100: c.ball(pts[8] + P(8 + (i - 100) * 2, 0), 1, r=1.5) if i < 108 else None
    c.cam(190 + drift * 0.8, 122, 1.45 if c.in_titan else 1.7)
    if c.in_titan: c.text(240, 214, 'SYNC ' + str(int(100 * s)) + '%', (255, 214, 80), 2)


# ======================================================================================================== TT24  REALITY BEND
def _play(c, t, outcome):
    """the little play that gets rewound: a striker shoots, the keeper saves ('saved') or is beaten ('goal'); t = scene time, can run backwards"""
    me = P(236, 128); face = unit(P(GOAL_X, 118) - me); K = 14; ST = K + int(12 * 70 / 40)
    if t < K: stand(c, me, face)
    else: c.spr('sh02_instep_drive', ak('sh02_instep_drive', t, K), face, HOME, me)
    kp = P(GOAL_X - 5, 120)
    for d in (P(196, 112), P(206, 144)): stand(c, d, P(1, 0), AWAY)
    a = t - ST
    tgt = P(GOAL_X - 4, 126) if outcome == 'saved' else P(GOAL_X + 6, 100)
    if a < 0: c.ball(me + face * 7, 1, r=1.5)
    elif a < 9: u = a / 9; c.ball(lerp(me + face * 7, tgt, u), 4, r=1.6, glow=(255, 255, 255) if outcome == 'goal' else None)
    else:
        a2 = a - 9
        if outcome == 'saved': c.ball(tgt + P(-a2 * 3, -a2 * 1.5), 3 + a2, r=1.5)
        else: c.ball(P(GOAL_X + 6, 100), 5, r=1.6); net_ripple(c, a2, 100, (255, 255, 255))
    if outcome == 'saved': c.spr('gk09_low_dive' if a < 9 else 'gk09_low_dive', min(25, ak('gk09_low_dive', t, ST - 2, 1.0)), P(-1, 0), KEEP, kp)
    else:
        if a < 6: stand(c, kp, P(-1, 0), KEEP)
        else: c.spr('gk02_reach_dive', ak('gk02_reach_dive', t, ST + 6, 1.0), P(-1, 0), KEEP, kp)
    c.cam(280, 122, 2.4)


@scene('TT24', N=170, titan=(46, 140), color=(200, 170, 255), result='TRY AGAIN')
def tt24(c):
    i = c.i
    if i < 46: _play(c, i, 'saved'); c.dim(0.0)                                                              # the play that goes wrong: shot saved
    elif i < 78:                                                                                           # rewind: the whole scene runs backwards, VHS-torn
        t = 46 - (i - 46) * 1.5; _play(c, max(0.0, t), 'saved')
        c.after(fx.glitch(i, 1.0, 7)); c.after(fx.chroma(3 + (i % 3))); c.after(fx.scan(0.25)); c.after(fx.wash((140, 100, 220), 0.18)); c.dim(0.4, (20, 10, 50))
        c.sd.polygon([(20, 40), (46, 52), (46, 28)], fill=(255, 255, 255, 230)); c.sd.polygon([(34, 40), (60, 52), (60, 28)], fill=(255, 255, 255, 230))
        c.text(240, 52, 'REWIND', (255, 255, 255), 3) if (i // 4) % 2 == 0 else None
        c.shake(2)
    elif i < 84: _play(c, 0.0, 'goal'); c.flash(1 - (i - 78) / 6, (230, 215, 255)); c.dim(0.3, (20, 10, 50)); c.after(fx.glitch(i, 0.5, 4))
    else:                                                                                                  # the retake: same play, this time it goes in
        _play(c, (i - 84) * 1.0, 'goal'); c.dim(0.3 * c.ta, (20, 10, 50))
        c.after(fx.chroma(2 if i < 96 else 0)) if i < 96 else None
    if i >= 100 and i < 104: c.shake(4)


# ======================================================================================================== TT25  CHAOS CONTROL
@scene('TT25', N=140, titan=(24, 110), color=(255, 62, 198), result='COOLDOWNS SCRAMBLED')
def tt25(c):
    i = c.i; T0 = 24
    c.dim(0.35 * c.ta, (30, 4, 30))
    foes = [P(150, 96), P(186, 128), P(222, 100), P(258, 140)]
    for j, d in enumerate(foes):
        glitchy = c.in_titan and i >= T0 + 4
        jx = random.Random(i * 5 + j).choice((-3, -1, 0, 1, 3)) if glitchy and (i // 2) % 3 != 0 else 0
        fc = P(random.Random(i // 3 * 7 + j).uniform(-1, 1), random.Random(i // 3 * 11 + j).uniform(-0.6, 0.6)) if glitchy else P(-1, 0.1)
        stand(c, d + P(jx, 0), fc, AWAY, tint_rgb=(255, 62, 198) if glitchy and i % 5 < 2 else None, tint_a=255, mix=0.6)
    stand(c, P(96, 124), P(1, 0), HOME)
    c.cam(190, 124, 2.0)
    # the opponent's hand, top of screen: their cooldown pies spin wildly and the cards shuffle places
    base = [60, 130, 200, 270, 340]
    order = list(range(5))
    if c.in_titan and i > T0 + 6:
        rr = random.Random(i // 6); order = list(range(5)); rr.shuffle(order)
    for slot in range(5):
        card_i = order[slot]; x = 150 + slot * 36; y = 40
        col = (255, 62, 198) if c.in_titan and i > T0 + 6 and (i + slot) % 7 < 3 else (120, 130, 160)
        c.sd.rectangle([x, y, x + 28, y + 40], fill=(28, 24, 52, 255), outline=col + (255,), width=2)
        c.sd.rectangle([x + 3, y + 5, x + 25, y + 22], fill=(60 + 30 * card_i, 40, 110, 255))
        if c.in_titan and i > T0 + 4:
            frac = (math.sin(i * 0.55 + card_i * 2.1) * 0.5 + 0.5)
            c.sd.pieslice([x + 2, y + 2, x + 26, y + 38], -90, -90 + 360 * frac, fill=(10, 10, 20, 170))
            if (i + slot) % 9 == 0: c.sd.rectangle([x, y, x + 28, y + 40], fill=(255, 62, 198, 140))
        else:
            c.sd.pieslice([x + 2, y + 2, x + 26, y + 38], -90, -90 + 360 * (0.25 + 0.15 * card_i), fill=(10, 10, 20, 150))
    c.text(240, 24, "OPPONENT'S COOLDOWNS", (255, 140, 220), 1) if c.in_titan else None
    if c.in_titan and i > T0:
        c.after(fx.glitch(i, min(1.0, (i - T0) / 8), 8)); c.after(fx.chroma(2 + i % 3)); c.after(fx.scan(0.18))
        r = 14 + (i - T0) * 9
        c.sd.ellipse([240 - r, 80 - r * 0.4, 240 + r, 80 + r * 0.4], outline=(255, 62, 198, int(230 * clamp(1 - (i - T0) / 24))), width=2)
    for q in range(12):                                                                                  # static bursts
        if c.in_titan:
            rng = random.Random(i * 13 + q); x = rng.randint(0, 460); y = rng.randint(30, 240); c.sd.rectangle([x, y, x + rng.randint(4, 30), y + 1], fill=(255, 62, 198, 160))

# ---------------------------------------------------------------------------------------------------------- runner
def render_all(ids=None, outdir=None):
    import time
    out = {}
    for cid in (ids or sorted(SCENES)):
        t = time.time(); name, frames = render(cid, outdir); sheet_png(frames, f'/tmp/tt_{cid}.png'); out[cid] = name
        print(cid, name, len(frames), f'{time.time() - t:.1f}s', flush=True)
    return out


if __name__ == '__main__':
    render_all(sys.argv[1:] or None)
