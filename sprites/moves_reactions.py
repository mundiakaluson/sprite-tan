"""Base reactions: directional stumbles (S/M/L), knocked off the ball, fall, get up, recover step, jump, stun, pain / limp.
Authored in the player's local frame (+y forward, +x right) with the Dr framework. Feet are placed in WORLD terms and converted to local per frame (world - root travel),
so planted feet do not slide while the body staggers. A hit "from the front" pushes the player back, "from behind" pushes forward, "from the side" shoves them left (the
mirrored sheet gives the other side, same as left-footed players)."""
import math
import gen_actions as A
import moves as M
from moves_dribble import Dr, pch
from moves_defend import hidden

MOVES = {}
PI = math.pi
STAND_R = (2.8, 0.8); STAND_L = (-2.8, -0.6)
ARM_REST = (0.12, 0.2, 0.45, -0.08)


def move(id_, label, loop=False):
    def deco(fn):
        MOVES[id_] = (label, fn, loop); return fn
    return deco


def root_at(d, f):
    """root offset (x, y) at frame f: Dr.build adds the travel of frames before f"""
    rx = ry = 0.0
    for g in range(f): rx += pch(d.lt, g); ry += pch(d.sp, g)
    return rx, ry


def lay(d, steps, body, arm=None, N=None, first=None):
    """steps: [(side, f_lift, f_land, (x, y) world target, lift)]; feet start at the stance. body(f) -> dict of body keys; arm(f) -> (R arm tuple, L arm tuple).
    Feet are held in world space except while stepping."""
    N = N or d.N; pos = {'R': first['R'] if first else STAND_R, 'L': first['L'] if first else STAND_L}
    seq = {s: sorted([x for x in steps if x[0] == s], key=lambda q: q[1]) for s in 'RL'}
    for f in range(N):
        rx, ry = root_at(d, f); feet = {}
        for s in 'RL':
            cur = pos[s]; z = None; fp = 0.0; tgt = cur
            for (_, a, b, to, lift) in seq[s]:
                if f > b: cur = to; continue
                if f >= a:
                    u = (f - a) / max(1, b - a); sm = u * u * (3 - 2 * u)
                    tgt = (cur[0] + (to[0] - cur[0]) * sm, cur[1] + (to[1] - cur[1]) * sm); z = lift * math.sin(PI * u) + 0.01 if u < 1.0 else None; fp = 14 * math.sin(PI * u)
                    break
                tgt = cur; break
            else: tgt = cur
            feet[s] = (tgt[0] - rx, tgt[1] - ry, fp if z is not None else 0, z)
        d.at(f, R=feet['R'], L=feet['L'], **body(f))
        ar = arm(f) if arm else (ARM_REST, ARM_REST)
        d.arms(f, ar[0], ar[1])
    hidden(d)


def env(f, a, b, c, d_):
    """0 before a, ramps up to 1 by b, holds to c, ramps down to 0 by d_"""
    if f <= a: return 0.0
    if f < b: return (f - a) / (b - a)
    if f <= c: return 1.0
    if f < d_: return 1.0 - (f - c) / (d_ - c)
    return 0.0


def smooth(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


# ------------------------------------------------------------------------------------------------------------------ stumbles
SIZES = {'s': dict(N=12, k=0.45, n=2, dist=7.0), 'm': dict(N=16, k=0.75, n=3, dist=15.0), 'l': dict(N=20, k=1.0, n=4, dist=26.0)}


def stumble(kind, size):
    P = SIZES[size]; N = P['N']; k = P['k']; n = P['n']; dist = P['dist']
    d = Dr(N, ms=64, speed=0.0); d.m.events = {'hit': 1}
    t_end = N - 5                                              # the stagger is over by here; the rest is the recovery
    sgn = {'back': -1.0, 'fwd': 1.0, 'side': 0.0}[kind]
    # root travel: a quick shove, decaying
    for f in range(N):
        u = (f - 1) / max(1, t_end - 1); v = (max(0.0, 1 - u) ** 1.6) * dist * 0.55 if 1 <= f <= t_end else 0.0
        if kind == 'side': d.sp[f] = 0.0; d.lt[f] = -v
        else: d.sp[f] = sgn * v; d.lt[f] = 0.0
    # steps: alternate feet, landing further along the travel, last one catches the body
    tot = [0.0, 0.0]
    for f in range(t_end): rx, ry = root_at(d, f + 1); tot = [rx, ry]
    steps = []; sides = ['R', 'L'] if kind != 'side' else ['R', 'L']
    f0 = 1
    for i in range(n):
        s = sides[i % 2]; a = f0 + i * max(2, (t_end - 2) // n); b = a + 3
        fx_, fy_ = root_at(d, min(b + 1, N - 1)); sx = STAND_R[0] if s == 'R' else STAND_L[0]; sy = (STAND_R[1] if s == 'R' else STAND_L[1])
        if kind == 'side': steps.append((s, a, b, (sx + fx_ - (1.5 if s == 'R' else -0.5) * (1 if i % 2 == 0 else 0), sy + fy_), 2.5 + 2 * k))       # cross-step then catch
        else: steps.append((s, a, b, (sx, sy + fy_ + sgn * (1.5 + 2 * k)), 2.5 + 2 * k))
    ease = lambda f: smooth(f / 2.0) * (1 - smooth((f - t_end) / 4.0))                  # 0 -> 1 quickly, back to 0 across the recovery
    wob = lambda f: math.sin(f * 1.7)

    def body(f):
        e = ease(f); w = wob(f) * e
        if kind == 'back':
            return dict(pz=22.7 - 1.2 * k * e, cpitch=0.05 - 0.75 * k * e, ppitch=-0.2 * k * e, hpitch=-0.35 * k * e, croll=0.08 * w, proll=0.05 * w)
        if kind == 'fwd':
            return dict(pz=22.7 - 2.2 * k * e, cpitch=0.05 + 1.0 * k * e, ppitch=0.3 * k * e, hpitch=0.25 * k * e, croll=0.08 * w, proll=0.05 * w)
        return dict(pz=22.7 - 1.6 * k * e, cpitch=0.05 + 0.15 * k * e, croll=0.62 * k * e + 0.06 * w, proll=0.4 * k * e, cyaw=-0.25 * k * e, hroll=0.3 * k * e, hyaw=0.2 * k * e)

    def arm(f):
        e = ease(f); w = math.sin(f * 1.5) * e
        if kind == 'back':
            r = (0.12 + (1.9 + 0.5 * w) * k * e, 0.2 + 0.9 * k * e, 0.45 + 1.4 * k * e, -0.08 + 0.6 * k * e); l = (0.12 + (1.9 - 0.5 * w) * k * e, 0.2 + 0.9 * k * e, 0.45 + 1.4 * k * e, -0.08 + 0.6 * k * e)
        elif kind == 'fwd':
            r = (0.12 + 1.5 * k * e, 0.2 + 0.7 * k * e, 0.45 + 1.3 * k * e, -0.08 + 0.3 * k * e); l = (0.12 + 1.5 * k * e, 0.2 + 0.7 * k * e, 0.45 + 1.3 * k * e, -0.08 + 0.3 * k * e)
        else:
            r = (0.12 + 0.4 * e, 0.2 + 1.0 * k * e, 0.45 + 0.4 * e, -0.08), (0.12 + 1.1 * k * e, 0.2 + 0.5 * k * e, 0.45 + 0.9 * k * e, -0.08 + 0.3 * k * e)
            return (r[0], r[1])
        return (r, l)
    lay(d, steps, body, arm)
    return d.m


for _k, _kn in (('back', 'from the front: pushed back'), ('fwd', 'from behind: pushed forward'), ('side', 'from the side: shoved left')):
    for _s, _sn in (('s', 'small'), ('m', 'medium'), ('l', 'big')):
        MOVES[f'base_stumble_{_k}_{_s}'] = (f'Stumble {_k} {_sn}', (lambda k=_k, s=_s: stumble(k, s)), False)


# ------------------------------------------------------------------------------------------------------------------ knocked off the ball
@move('base_knocked_off', 'Knocked Off The Ball')
def knocked_off():
    N = 18; d = Dr(N, ms=60, speed=0.0); d.m.events = {'hit': 1}
    for f in range(N):
        v = max(0.0, 1 - (f - 1) / 9.0) ** 1.4 * 9.0 if 1 <= f <= 10 else 0.0
        d.lt[f] = -v; d.sp[f] = 0.4 * v
    steps = [('R', 1, 4, (STAND_R[0] - 0.5 + root_at(d, 5)[0], STAND_R[1] + root_at(d, 5)[1] + 1.0), 3.0), ('L', 4, 7, (STAND_L[0] + root_at(d, 8)[0], STAND_L[1] + root_at(d, 8)[1] + 1.5), 3.5),
             ('R', 7, 10, (STAND_R[0] + root_at(d, 11)[0], STAND_R[1] + root_at(d, 11)[1]), 2.5)]
    ez = lambda f: smooth(f / 2.0) * (1 - smooth((f - 11) / 5.0))

    def body(f):
        e = ez(f); tw = math.sin(min(f, 9) * 0.5) * e
        return dict(pz=22.7 - 1.3 * e, cpitch=0.05 + 0.25 * e, croll=0.5 * e, proll=0.3 * e, pyaw=0.55 * e, cyaw=0.8 * e, hyaw=-0.5 * e, hpitch=0.1 * e)

    def arm(f):
        e = ez(f)
        return ((0.12 + 0.5 * e, 0.2 + 0.7 * e, 0.45 + 0.5 * e, -0.08), (0.12 + 1.5 * e, 0.2 + 0.9 * e, 0.45 + 1.1 * e, -0.08 + 0.5 * e))
    lay(d, steps, body, arm)
    return d.m


# ------------------------------------------------------------------------------------------------------------------ fall + get up
def lying(d, f, roll=1.45, pz=8.0, **kw):
    d.at(f, R=(3.6, -3.0, 20, 5.0), L=(-0.5, -4.0, 20, 5.0), pz=pz, cpitch=0.0, croll=-roll, proll=-roll + 0.05, hyaw=-0.85, **kw)
    d.arms(f, (2.35, 0.5, 2.8, 0.2), (2.0, 0.6, 2.4, 0.2))


@move('base_fall', 'Fall')
def fall():
    """loses balance to the right, drops, catches himself on one arm, ends lying on his side (held for a beat)"""
    N = 24; d = Dr(N, ms=62, speed=0.0); d.m.events = {'impact': 9}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(0, 4):                                                                         # off balance
        u = f / 3.0
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.7 - 1.0 * u, cpitch=0.05 + 0.2 * u, croll=-0.3 * u, proll=-0.2 * u, hroll=-0.2 * u)
        d.arms(f, (0.12 + 1.3 * u, 0.2 + 0.9 * u, 0.45 + 1.0 * u, -0.08), (0.12 + 1.0 * u, 0.2 + 1.0 * u, 0.45 + 0.8 * u, -0.08))
    for f in range(4, 9):                                                                         # tipping over
        u = (f - 3) / 5.0
        d.at(f, R=(3.0 + 0.6 * u, 0.8 - 2.0 * u, 10 * u, 2.0 * u), L=(-2.8 + 1.8 * u, -0.6 - 2.0 * u, 0, None), pz=22.0 - 13.0 * smooth(u), cpitch=0.25 - 0.25 * u, croll=-0.3 - 1.0 * smooth(u), proll=-0.2 - 0.85 * smooth(u), hyaw=-0.8 * u, hroll=-0.2)
        d.arms(f, (1.4 + 0.9 * u, 1.1 - 0.6 * u, 1.4 + 1.4 * u, 0.2), (1.1 + 0.8 * u, 1.0 - 0.4 * u, 1.3 + 1.1 * u, 0.2))
    for f in range(9, N): lying(d, f, roll=1.45 + 0.04 * math.sin((f - 9) * 0.9) * max(0.0, 1 - (f - 9) / 5.0))
    d.lateral(**{'f2': 0.0, 'f6': 1.5, 'f9': 0.0})
    hidden(d); return d.m


@move('base_get_up', 'Get Up')
def get_up():
    """from lying on the side: roll onto the hands and knees, push up through a crouch, stand"""
    N = 20; d = Dr(N, ms=62, speed=0.0); d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    lying(d, 0); lying(d, 1)
    for f in range(2, N):
        u = (f - 1) / (N - 2.0)
        if u < 0.35:                                                                                # roll up onto hands and knees
            w = smooth(u / 0.35)
            d.at(f, R=(3.4 - 0.6 * w, -3.0 + 2.6 * w, 20 * (1 - w), 5.0 * (1 - w)), L=(-0.5 - 2.0 * w, -4.0 + 3.0 * w, 20 * (1 - w), 5.0 * (1 - w)), pz=8.0 + 4.0 * w, cpitch=0.9 * w, croll=-1.45 * (1 - w) , proll=-1.4 * (1 - w), hyaw=-0.85 * (1 - w), hpitch=0.3 * w)
            d.arms(f, (2.35 - 0.6 * w, 0.5, 2.8 - 1.3 * w, 0.2), (2.0 - 0.3 * w, 0.6, 2.4 - 0.9 * w, 0.2))
        elif u < 0.7:                                                                               # push up, one foot under him
            w = smooth((u - 0.35) / 0.35)
            d.at(f, R=(3.0, 1.0 + 0.4 * w, 0, None), L=(-3.0, -0.6 - 0.8 * (1 - w), 0, None), pz=12.0 + 7.0 * w, cpitch=0.9 - 0.4 * w, croll=0, proll=0, hpitch=0.3 - 0.05 * w)
            d.arms(f, (1.75 - 0.9 * w, 0.5, 1.5 - 0.6 * w, 0.2), (1.7 - 0.9 * w, 0.6, 1.5 - 0.6 * w, 0.2))
        else:                                                                                       # straighten, arms settle
            w = smooth((u - 0.7) / 0.3)
            d.at(f, R=(2.9, 1.0 - 0.2 * w, 0, None), L=(-2.9, -0.6, 0, None), pz=19.0 + 3.7 * w, cpitch=0.5 - 0.45 * w, hpitch=0.25 - 0.2 * w)
            d.arms(f, (0.85 - 0.73 * w, 0.5 - 0.3 * w, 0.9 - 0.45 * w, 0.2 - 0.28 * w), (0.8 - 0.68 * w, 0.6 - 0.4 * w, 0.9 - 0.45 * w, 0.2 - 0.28 * w))
    hidden(d); return d.m


@move('base_recover_step', 'Recover Step')
def recover_step():
    """a half-lost balance caught by one wide step, arms out, then straight again"""
    N = 12; d = Dr(N, ms=62, speed=0.0)
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = (2.4 if 1 <= f <= 5 else 0.0)
    steps = [('R', 1, 5, (STAND_R[0] + 0.8, STAND_R[1] + root_at(d, 6)[1] + 2.5), 3.0)]
    ez = lambda f: smooth(f / 2.0) * (1 - smooth((f - 6) / 5.0))
    body = lambda f: dict(pz=22.7 - 1.4 * ez(f), cpitch=0.05 + 0.3 * ez(f), ppitch=0.1 * ez(f), croll=0.1 * math.sin(f * 1.3) * ez(f))
    arm = lambda f: ((0.12 + 0.6 * ez(f), 0.2 + 1.0 * ez(f), 0.45 + 0.4 * ez(f), -0.08), (0.12 + 0.6 * ez(f), 0.2 + 1.0 * ez(f), 0.45 + 0.4 * ez(f), -0.08))
    lay(d, steps, body, arm)
    return d.m


# ------------------------------------------------------------------------------------------------------------------ jump
@move('base_jump', 'Jump')
def jump():
    """crouch, push off, rise, hang, drop, absorb the landing, stand. The hit (header / challenge) is the airborne frames 9-12"""
    N = 22; d = Dr(N, ms=55, speed=0.0); d.m.events = {'takeoff': 5, 'apex': 10, 'land': 15}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    H = 9.0
    for f in range(N):
        if f <= 2:  w = smooth(f / 2.0); pz = 22.7 - 4.2 * w; air = 0.0; cp = 0.05 + 0.55 * w; ar = (0.12 - 0.9 * w, 0.2, 0.45 - 0.2 * w, -0.08)
        elif f <= 4: w = smooth((f - 2) / 2.0); pz = 18.5 + 5.0 * w; air = 0.0; cp = 0.6 - 0.45 * w; ar = (-0.78 + 3.2 * w, 0.2 + 0.4 * w, 0.25 + 1.8 * w, -0.08)
        elif f <= 15:
            t = (f - 5) / 10.0; hgt = 4 * H * t * (1 - t); pz = 23.7 + hgt; air = max(0.0, hgt * 0.9 + 1.0 if 0 < t < 1 else 0.0); cp = 0.15 - 0.1 * t; ar = (2.4 - 0.5 * t, 0.5, 2.1, -0.08)
        elif f <= 18: w = smooth((f - 15) / 3.0); pz = 23.7 - 5.2 * w; air = 0.0; cp = 0.05 + 0.5 * w; ar = (1.9 - 1.5 * w, 0.5 - 0.1 * w, 1.6 - 0.9 * w, -0.08)
        else: w = smooth((f - 18) / 3.0); pz = 18.5 + 4.2 * w; air = 0.0; cp = 0.55 - 0.5 * w; ar = (0.4 - 0.28 * w, 0.4 - 0.2 * w, 0.7 - 0.25 * w, -0.08)
        tuck = air > 1.5
        d.at(f, R=(2.8, 0.8 - (1.2 if tuck else 0), 0 if not tuck else -20, air if tuck else None), L=(-2.8, -0.6 + (0.5 if tuck else 0), 0 if not tuck else -10, air * 0.85 if tuck else None), pz=pz, cpitch=cp, hpitch=0.1 + 0.25 * (cp > 0.3))
        d.arms(f, ar, ar)
    hidden(d); return d.m


# ------------------------------------------------------------------------------------------------------------------ stun + pain / limp (loops)
@move('base_stun', 'Stun', True)
def stun():
    """dazed: knees soft, weight drifting in a slow circle, head lolling, arms hanging loose. Loops; the game adds the stars"""
    N = 16; d = Dr(N, ms=90, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N):
        ph = 2 * PI * f / N
        d.at(f, R=(2.9 + 0.2 * math.sin(ph), 0.6, 0, None), L=(-2.9, -0.8 + 0.2 * math.cos(ph), 0, None), pz=21.6 + 0.35 * math.sin(2 * ph), cpitch=0.2 + 0.1 * math.sin(ph + 1.0), croll=0.2 * math.sin(ph), proll=-0.12 * math.sin(ph),
             hroll=0.45 * math.sin(ph + 0.6), hyaw=0.35 * math.cos(ph), hpitch=0.35 + 0.12 * math.sin(2 * ph), cyaw=0.1 * math.cos(ph))
        d.arms(f, (0.2 + 0.35 * math.sin(ph + 1.5), 0.3 + 0.1 * math.sin(ph), 0.35 + 0.2 * math.sin(ph + 2.0), -0.05), (0.2 + 0.35 * math.sin(ph + 3.5), 0.3 - 0.1 * math.sin(ph), 0.35 + 0.2 * math.sin(ph + 0.5), -0.05))
    hidden(d); return d.m


@move('base_limp', 'Pain Limp', True)
def limp():
    """a hurt right leg: short weak step, heavy drop on the good side, bent forward, hand pressed to the thigh. Loops (play at walk speed or slower)"""
    P = dict(A.BASE); P.update(stance=0.64, yc=2.6, yo=-3.8, lift=3.0, dip=1.6, flight=0.0, lean=0.2, head_pitch=0.35, arm=0.2, elbow=0.4, twist=0.08, sway=0.9)
    N = 20; m = M.Move({}, N, 85, {}); m.loop = True
    for f in range(N):
        t = f / N; k = A.run_pose(P, t, 0.0); w = 0.5 + 0.5 * math.cos(2 * PI * (t + 0.0))                    # w: 1 while the left (good) foot carries the weight
        k['pz'] -= 0.9 * w; k['croll'] = -0.16 * w + 0.05; k['proll'] = -0.1 * w; k['cpitch'] += 0.12; k['hpitch'] = 0.45; k['hroll'] = -0.12
        k['R_ay'] = k.get('R_ay', 0.0) * 0.55
        k.update(A.arm('R', 0.55, 0.42, 1.75, -0.55)); k.update(A.arm('L', 0.12 + 0.25 * (1 - w), 0.2, 0.7, -0.08))
        k['bvis'] = 0.0; m.keys[f] = k
    return m
