"""The 30 DRIBBLE skill animations (DR01-DR30). Run:  python moves_dribble.py [id ...]  to (re)write data/animations/drXX_*.json

Authored in the player's own frame (root at the origin, forward = +y). Each move also has a heading (theta, so turns and cuts rotate the whole body, feet and ball
about the player) and a travel speed; build() turns that into world poses with root motion, centred on x as well ('cx'). Plain dribbles carry a speed mist ('fxm')."""
import math, sys
import numpy as np
import gen_actions as A
import moves as M
from moves import Move
from moves_shot import frame

MOVES = {}
PI = math.pi


def move(id_, label):
    def deco(fn):
        MOVES[id_] = (label, fn); return fn
    return deco


def pch(pts, f):
    xs = sorted(pts); return float(A.pchip(xs, [pts[x] for x in xs], f))


class Dr:
    def __init__(s, N, ms=60, speed=2.0):
        s.N = N; s.m = Move({}, N, ms, {'touch': 6}); s.th = {0: 0.0}; s.sp = {0: speed}; s.fx = {0: 0.0}
        for f in range(N): s.m.keys[f] = {}

    def at(s, f, R=None, L=None, ball=None, **body):
        frame(s.m, f, R=R, L=L, **body)
        if ball is not None: s.m.k(f, bx=ball[0], by=ball[1], bz=ball[2] if len(ball) > 2 else 3.0, bvis=1.0)
        return s

    def hide_ball(s, f0, f1):
        for f in range(f0, f1 + 1): s.m.k(f, bvis=0.0)

    def arms(s, f, r=None, l=None):
        if r: s.m.arms(f, 'R', *r)
        if l: s.m.arms(f, 'L', *l)

    def carry(s, f0, f1, lean=0.0, cad=1.0, t0=0.0, tight=False, ball=True):
        for f in range(f0, f1 + 1):
            k = A.run_pose(A.BASE, (f * cad + t0) / 12.0, 0.0)
            k['cpitch'] += lean; k['ppitch'] += lean * 0.4
            s.m.keys[f].update(k)
            if ball:
                saw = ((f * cad) % 6) / 6.0
                s.m.k(f, bx=1.1 * math.sin(f * cad * PI / 6), by=(10.0 if tight else 12.2) - (2.4 if tight else 3.4) * saw, bz=3.0, bvis=1.0, brx=-2.0 * f)

    def turn(s, **pts): s.th.update({int(k[1:]): v for k, v in pts.items()})
    def speed(s, **pts): s.sp.update({int(k[1:]): v for k, v in pts.items()})

    def build(s):
        poses = s.m.poses(); out = {}; rx = ry = 0.0
        for f, p in enumerate(poses):
            T = pch(s.th, f); sp = pch(s.sp, f); c, sn = math.cos(T), math.sin(T)
            rot = lambda x, y: (c * x - sn * y, sn * x + c * y)
            q = dict(p)
            for a, b in (('R_ax', 'R_ay'), ('L_ax', 'L_ay'), ('bx', 'by'), ('R_kx', 'R_ky'), ('L_kx', 'L_ky')):
                x, y = rot(p[a], p[b]); add = (0.0, 0.0) if a.endswith('kx') else (rx, ry)
                q[a], q[b] = x + add[0], y + add[1]
            x, y = rot(p['root_x'], 0.0); q['root_x'], q['root_y'] = rx + x, ry + y
            for k in ('pyaw', 'cyaw', 'hyaw'): q[k] = p[k] + T
            q['brz'] = p.get('brz', 0.0) + T
            q['cx'] = 1.0; q['fxd'] = T; q['fxm'] = max(0.0, pch(s.fx, f)); q['fxp'] = f * 0.9
            out[f] = q
            rx += -sn * sp; ry += c * sp
        s.m.keys = out
        return s.m


# ---------------------------------------------------------------- reusable segments (return the next free frame)
def stepover(d, f0, side='R'):
    """three frames: the foot lifts outside, loops over the front of the ball and lands the far side, while the torso leans AWAY from the working foot"""
    sg = 1 if side == 'R' else -1; o = 'L' if side == 'R' else 'R'
    work = lambda x, y, fp, z=None: {side: (sg * x, y, fp, z)}
    other = {o: (-sg * 2.0, 1.8, 0, None)}
    kw = lambda a, b: {**a, **other} if b is None else {**a, **b}
    d.at(f0, ball=(sg * 0.2, 8.2), **kw(work(3.4, 5.6, 25, 6.5), None), croll=-0.3 * sg, proll=-0.14 * sg, cpitch=0.2, hpitch=0.45, pz=23.8)
    d.at(f0 + 1, ball=(sg * 0.2, 8.3), **kw(work(0.2, 10.4, 45, 8.6), {o: (-sg * 2.2, 2.8, 0, None)}), croll=-0.42 * sg, proll=-0.2 * sg, cpitch=0.24, hpitch=0.5, pz=23.4)
    d.at(f0 + 2, ball=(sg * 0.2, 8.4), **kw(work(-3.0, 8.6, 0, None), {o: (-sg * 1.6, 3.6, 0, None)}), croll=-0.12 * sg, proll=-0.06 * sg, cpitch=0.22, hpitch=0.4, pz=23.8)
    for f in range(f0, f0 + 3): d.arms(f, (-0.2, 0.6, 0.5, 0.4) if side == 'R' else (0.9, 1.0, 1.2, 0.7), (0.9, 1.0, 1.2, 0.7) if side == 'R' else (-0.2, 0.6, 0.5, 0.4))
    return f0 + 3


def push_out(d, f0, side='L', dx=3.0, dy=10.5):
    sg = 1 if side == 'R' else -1
    d.at(f0, ball=(sg * 0.4, 8.6), **{side: (sg * 1.2, 8.6, 60, 3.2, sg * 0.7, sg * 0.3), 'L' if side == 'R' else 'R': (-sg * 2.6, 4.0, 0, None)}, croll=0.3 * sg, cpitch=0.3)
    d.at(f0 + 1, ball=(sg * dx, dy), **{side: (sg * 2.4, 10.4, 50, 3.4, sg * 0.5, sg * 0.2)}, croll=0.1 * sg, cpitch=0.3)
    return f0 + 2


def burst(d, f0, f1, lean=0.38):
    for f in range(f0, f1 + 1):
        k = A.run_pose(A.BASE, (f + 2) / 12.0, 0.0); k['cpitch'] += lean; k['ppitch'] += lean * 0.4; d.m.keys[f].update(k)


def ball_ahead(d, f0, ys, x=0.4, z=3.0):
    for i, y in enumerate(ys):
        if f0 + i < d.N: d.m.k(f0 + i, bx=x + 0.0, by=y, bz=z, bvis=1.0, brx=-3.0 * (f0 + i))


def settle(d, f0, f1):
    """pick the dribble back up: ball glued just ahead with a touch every stride"""
    for f in range(f0, f1 + 1):
        saw = (f % 6) / 6.0
        d.m.k(f, bx=1.0 * math.sin(f * PI / 6), by=11.6 - 3.0 * saw, bz=3.0, bvis=1.0)


# ---------------------------------------------------------------- the moves
@move('DR01', 'Step Over')
def dr01():
    d = Dr(22); d.carry(0, 5)
    f = stepover(d, 6, 'R'); f = push_out(d, f, 'L', dx=-3.0, dy=10.5)           # R over the ball, L takes it away to the left
    burst(d, f, 21); d.turn(**{'f12': 0.0, 'f13': 0.5}); settle(d, f + 1, 21); d.turn(**{'f21': 0.5})
    d.speed(f0=1.8, f9=1.4, f11=3.0)
    return d.build()


@move('DR02', 'Drag Back')
def dr02():
    d = Dr(24); d.carry(0, 5); d.speed(f0=2.0, f6=0.6, f12=2.6)
    d.at(6, R=(1.0, 8.0, -30, 6.0), L=(-2.2, 2.4, 0, None), ball=(0.9, 8.0), cpitch=0.4, pz=23.4)
    d.at(7, R=(0.8, 7.6, -55, 4.9), L=(-2.2, 2.4, 0, None), ball=(0.8, 7.6, 2.4), cpitch=0.5, pz=23.0)             # sole on top of the ball
    d.at(8, R=(0.5, 4.8, -55, 4.9), L=(-2.4, 2.0, 0, None), ball=(0.5, 4.8, 2.4), cpitch=0.5, pz=23.0)
    d.at(9, R=(-0.4, 1.8, -50, 4.9), L=(-2.6, 1.4, 0, None), ball=(-0.4, 1.8, 2.4), cpitch=0.46, pz=23.2)
    d.at(10, R=(-1.6, 0.0, -40, 4.8), L=(-3.0, 1.0, 0, None), ball=(-1.6, 0.0, 2.4), cpitch=0.4, pz=23.4)
    d.at(11, R=(-2.0, 1.6, 40, 3.2, -1.2, 0.1), L=(-3.0, 1.0, 0, None), ball=(-2.8, 2.6), cpitch=0.34)              # inside of the boot rolls it away
    d.turn(**{'f7': 0.0, 'f11': 1.5, 'f14': 1.57}); burst(d, 13, 23, 0.3); settle(d, 14, 23)
    return d.build()


@move('DR03', 'Roulette')
def dr03():
    d = Dr(24); d.carry(0, 4); d.speed(f0=2.0, f5=0.5, f14=2.6)
    for f, (bx, by) in zip(range(5, 15), ((0.8, 7.0), (0.8, 5.4), (0.6, 3.0), (0.0, 0.8), (-0.8, -0.6), (-1.4, 0.4), (-1.0, 2.4), (-0.2, 4.6), (0.6, 6.4), (0.8, 7.6))):
        d.at(f, R=(bx + 0.1, by + 0.4, -50, 4.8), L=(-2.2, 0.8, 0, None), ball=(bx, by, 2.4), cpitch=0.38, pz=23.2, croll=0.12,
             R_s1=0.0)
        d.arms(f, (0.5, 0.9, 0.9, 0.6), (0.5, 0.9, 0.9, 0.6))
    d.at(15, R=(1.6, 10.2, 50, 3.4), ball=(0.6, 10.5), cpitch=0.3)
    d.turn(**{'f5': 0.0, 'f14': 2 * PI * -1}); burst(d, 16, 23, 0.3); settle(d, 15, 23); d.turn(**{'f15': -2 * PI})
    return d.build()


@move('DR04', 'Nutmeg')
def dr04():
    d = Dr(22); d.carry(0, 4); d.speed(f0=2.0, f6=1.6, f8=3.2)
    d.at(5, R=(2.2, 3.0, 20, None), ball=(0.6, 8.2), croll=-0.3, proll=-0.16, hyaw=-0.4, pyaw=-0.2)                  # shoulder dips left
    d.at(6, R=(2.0, 5.6, 60, 4.4), L=(-2.6, 2.0, 0, None), ball=(0.8, 8.4), croll=0.2, cpitch=0.3)
    d.at(7, R=(1.4, 9.0, 80, 3.4), L=(-2.6, 3.0, 0, None), ball=(1.0, 9.6), croll=0.25, cpitch=0.36)                 # toe poke
    ball_ahead(d, 8, [14, 18.5, 21, 22, 21.5, 20, 17, 13.5, 10.5], 1.0)
    burst(d, 8, 21, 0.45); d.at(8, R=(1.4, 10.8, 50, 5.0)); d.arms(8, (1.0, 0.9, 1.1, 0.7), (1.0, 0.9, 1.1, 0.7))
    settle(d, 17, 21)
    return d.build()


@move('DR05', 'Body Feint')
def dr05():
    d = Dr(20); d.carry(0, 4); d.speed(f0=2.0, f6=1.2, f10=2.8)
    d.at(5, L=(-4.6, 2.0, 0, None), R=(2.4, 1.0, 10, None), ball=(0.6, 7.6), croll=-0.3, proll=-0.16, hyaw=-0.5, cpitch=0.2)
    d.at(6, L=(-5.2, 3.2, 0, None), R=(2.0, 0.0, 10, None), ball=(0.6, 7.4), croll=-0.42, proll=-0.22, hyaw=-0.6, hroll=-0.2, cpitch=0.2, pz=23.4)
    d.at(7, L=(-5.2, 3.2, 0, None), R=(1.4, 1.0, 20, None), ball=(0.6, 7.4), croll=-0.42, proll=-0.22, hyaw=-0.4, cpitch=0.2, pz=23.2)
    d.at(8, R=(2.8, 8.8, 70, 3.4, 0.7, 0.4), L=(-4.6, 3.0, 0, None), ball=(1.2, 8.8), croll=0.4, proll=0.2, hyaw=0.3, cpitch=0.3)  # snap the other way
    d.at(9, R=(4.2, 11.6, 50, 4.4), L=(-2.4, 5.0, 20, 4.0), ball=(3.4, 11.4), croll=0.3, proll=0.15, cpitch=0.3)
    d.turn(**{'f7': 0.0, 'f11': -0.6, 'f19': -0.6}); burst(d, 10, 19, 0.36); settle(d, 11, 19)
    d.arms(6, (0.3, 1.1, 0.6, 0.9), (1.0, 1.2, 1.4, 1.1))
    return d.build()


@move('DR06', 'Sombrero Flick')
def dr06():
    d = Dr(26); d.carry(0, 5); d.speed(f0=2.0, f8=1.6, f15=2.4)
    d.at(6, R=(0.8, 6.0, -10, None), L=(-2.2, 2.0, 0, None), ball=(0.8, 7.8), cpitch=0.3, pz=23.4)
    d.at(7, R=(0.8, 7.6, -15, None), ball=(0.8, 8.0, 2.8), cpitch=0.26, pz=23.6, hpitch=0.5)                              # toe slides under the ball
    d.at(8, R=(0.8, 9.4, -20, 6.5), ball=(0.8, 10.0, 9.0), cpitch=0.12, hpitch=0.2)                                         # and lifts it
    arc = ((12.5, 20), (13.8, 29), (14.6, 34), (14.8, 35), (14.2, 33), (12.8, 28), (10.6, 20), (8.2, 11), (6.6, 5), (6.0, 3))
    for i, (y, z) in enumerate(arc): d.m.k(9 + i, bx=0.8, by=y, bz=z, bvis=1.0)
    for f in range(9, 15): d.m.k(f, hpitch=-0.6, cpitch=-0.02)
    d.at(9, R=(0.8, 10.8, 10, 8.0)); d.at(10, R=(0.6, 9.0, 0, None), L=(-2.0, 5.0, 10, None)); d.at(11, R=(1.4, 6.0, 20, 4.0))
    burst(d, 12, 25, 0.25)
    for f in (9, 10, 11, 12): d.arms(f, (0.9, 0.9, 1.2, 0.7), (1.0, 1.0, 1.3, 0.8))
    settle(d, 19, 25)
    return d.build()


@move('DR07', 'La Croqueta')
def dr07():
    d = Dr(18); d.carry(0, 4, tight=True); d.speed(f0=1.8, f5=1.4, f9=2.8)
    d.at(5, R=(1.8, 6.6, 30, 3.4, -1.0, 0.1), L=(-2.0, 2.0, 0, None), ball=(1.2, 7.6), croll=0.15, cpitch=0.2)
    d.at(6, R=(0.2, 7.2, 30, 3.4, -1.1, 0.1), L=(-1.8, 5.0, 20, 3.4), ball=(-1.0, 7.8), croll=-0.12, cpitch=0.2)         # right inside taps it across
    d.at(7, L=(-1.2, 7.6, 30, 3.4, 1.0, 0.1), R=(0.4, 5.0, 10, None), ball=(-0.4, 8.4), croll=0.1, cpitch=0.2)
    d.at(8, L=(-1.0, 8.8, 40, 3.2, 1.0, 0.1), R=(0.6, 6.0, 10, None), ball=(0.8, 9.4), croll=0.0, cpitch=0.26)         # left nudges it on
    d.at(9, L=(-1.8, 8.0, 20, 5.0), R=(1.4, 8.8, 20, None), ball=(0.8, 10.6), cpitch=0.3)
    burst(d, 10, 17, 0.3); settle(d, 10, 17)
    d.arms(6, (0.4, 0.8, 0.8, 0.6), (0.4, 0.8, 0.8, 0.6))
    return d.build()


@move('DR08', 'Elastico')
def dr08():
    d = Dr(20); d.carry(0, 4); d.speed(f0=2.0, f6=1.4, f10=2.8)
    d.at(5, R=(2.4, 6.0, 40, 3.8), L=(-2.4, 2.0, 0, None), ball=(1.0, 8.4), croll=0.2, cpitch=0.26)
    d.at(6, R=(4.2, 8.4, 75, 3.0, 0.9, 0.5), ball=(3.8, 8.8), croll=0.34, proll=0.12, cpitch=0.28)                       # outside of the boot knocks it wide
    d.at(7, R=(2.8, 9.4, 55, 3.2, 0.2, 0.2), ball=(3.6, 9.0), croll=0.34, cpitch=0.28)                                    # and snaps the foot back round
    d.at(8, R=(0.0, 9.2, 45, 3.2, -1.2, 0.1), ball=(-2.6, 9.6), croll=-0.38, proll=-0.16, cpitch=0.3, hyaw=-0.3)           # inside sweeps it the other way
    d.at(9, R=(-1.0, 8.0, 20, 4.4), L=(-3.0, 4.6, 20, 4.0), ball=(-3.6, 11.0), croll=-0.2)
    d.turn(**{'f8': 0.0, 'f11': 0.4, 'f19': 0.4}); burst(d, 10, 19, 0.34); settle(d, 11, 19)
    return d.build()


@move('DR09', 'Cruyff Turn')
def dr09():
    d = Dr(26); d.carry(0, 5); d.speed(f0=2.0, f6=1.0, f9=0.4, f14=2.6)
    d.at(6, R=(2.0, -1.0, 45, 8.0), L=(-2.4, 4.0, 0, None), ball=(0.9, 8.0), cpitch=0.2, pyaw=-0.2)                       # as if to hit it
    d.at(7, R=(1.6, 6.0, 62, 6.0), L=(-2.4, 4.0, 0, None), ball=(0.9, 8.0), cpitch=0.3, pyaw=0.1)
    d.at(8, R=(0.6, 7.6, 40, 3.6, -1.0, 0.1), L=(-2.4, 4.0, 0, None), ball=(0.8, 8.0), cpitch=0.34)                       # foot arrives and hooks the ball
    d.at(9, R=(-1.0, 5.0, 40, 3.2, -1.2, 0.1), ball=(-0.4, 5.6), cpitch=0.34)
    d.at(10, R=(-2.6, 3.0, 40, 3.2, -1.3, 0.1), ball=(-2.2, 3.2), cpitch=0.3)
    d.at(11, R=(-2.6, 3.4, 30, 3.2, -1.1, 0.1), ball=(-2.4, 3.6), cpitch=0.26)
    d.arms(7, (-0.3, 0.8, 0.4, 0.5), (1.1, 1.3, 1.4, 1.0))
    d.turn(**{'f8': 0.0, 'f12': PI, 'f25': PI}); burst(d, 13, 25, 0.3); settle(d, 12, 25)
    return d.build()


@move('DR10', 'Fake Shot Turn')
def dr10():
    d = Dr(28); d.carry(0, 5); d.speed(f0=2.0, f6=0.9, f12=0.3, f17=2.6)
    d.at(6, R=(1.8, -6.0, 50, 10.0), L=(-3.2, 4.0, 0, None), ball=(0.9, 8.4), cpitch=0.2, pyaw=-0.3)
    d.at(7, R=(1.4, -12.0, 56, 16.0), L=(-4.4, 4.6, 0, None), ball=(0.9, 8.4), cpitch=0.3, pyaw=-0.5)                     # big shooting backswing
    d.at(8, R=(1.4, 4.0, 66, 11.0), L=(-4.4, 4.8, 0, None), ball=(0.9, 8.4), cpitch=0.4, pyaw=-0.1)
    d.at(9, R=(1.2, 7.4, 70, 7.4), ball=(0.9, 8.4), cpitch=0.42, pyaw=0.1)                                               # stops dead over the ball
    d.at(10, R=(1.0, 7.8, -45, 4.8), ball=(1.0, 7.6, 2.4), cpitch=0.44, pz=23.4)                                          # sole on it
    d.at(11, R=(1.2, 4.6, -45, 4.8), ball=(1.2, 4.6, 2.4), cpitch=0.4)
    d.at(12, R=(2.0, 1.8, -40, 4.8), ball=(2.0, 1.8, 2.4), cpitch=0.34)
    d.at(13, R=(2.6, 1.4, 30, 3.2, -1.0, 0.1), ball=(2.8, 2.4), cpitch=0.3)
    d.arms(7, (-1.2, 0.5, -0.4, 0.4), (1.2, 1.6, 1.6, 1.5)); d.arms(9, (0.8, 1.0, 1.0, 0.8), (1.0, 1.4, 1.4, 1.1))
    d.turn(**{'f10': 0.0, 'f15': -PI, 'f27': -PI}); burst(d, 16, 27, 0.3); settle(d, 15, 27)
    return d.build()


@move('DR11', 'Ball Roll')
def dr11():
    d = Dr(22); d.carry(0, 4); d.speed(f0=1.8, f11=2.6); d.fx = {0: 0.5, 21: 0.6}
    # sole on top of the ball rolling it across the body, torso and hips leaning AWAY from the rolling foot, head over the ball, arms out for balance
    lean = dict(croll=-0.56, proll=-0.3, cpitch=0.16, hpitch=0.55, pz=23.0, root_x=-1.4)
    d.at(5, R=(2.6, 7.2, -45, 5.8), L=(-2.2, 1.8, 0, None), ball=(1.8, 8.0), **lean)
    d.at(6, R=(1.6, 7.4, -50, 4.9), L=(-2.2, 1.8, 0, None), ball=(1.6, 8.0, 2.4), **lean)
    d.at(7, R=(0.4, 7.2, -50, 4.9), ball=(0.4, 8.0, 2.4), **lean)
    d.at(8, R=(-0.8, 7.0, -50, 4.9), ball=(-0.8, 7.8, 2.4), **dict(lean, croll=-0.62))
    d.at(9, R=(-1.8, 6.8, -45, 4.8), ball=(-1.8, 7.6, 2.4), **dict(lean, croll=-0.66))
    d.at(10, R=(-0.6, 7.0, -50, 4.9), ball=(-0.6, 7.8, 2.4), **dict(lean, croll=-0.52))                                    # rolled back
    d.at(11, L=(-1.4, 8.4, 40, 3.2, 1.0, 0.1), R=(1.8, 3.0, 0, None), ball=(-0.2, 10.8), croll=0.12, proll=0.05, cpitch=0.3, hpitch=0.2)
    d.at(12, L=(-1.8, 10.6, 30, 4.4), R=(1.0, 6.0, 20, 4.0), ball=(0.0, 12.0), croll=0.1, cpitch=0.3)
    for f in range(5, 11): d.arms(f, (-0.2, 0.7, 0.6, 0.5), (1.0, 1.1, 1.3, 0.8))
    burst(d, 13, 21, 0.3); settle(d, 13, 21)
    return d.build()


@move('DR12', 'Shoulder Shield')
def dr12():
    d = Dr(22, speed=1.4); d.carry(0, 21, tight=True, cad=0.7)
    for f in range(0, 22):
        d.m.k(f, pyaw=-0.9, cyaw=-1.0, hyaw=0.7, croll=-0.14, cpitch=0.16, pz=23.6, bx=-1.6 + 0.3 * math.sin(f * 0.6), by=6.4 + 0.5 * math.sin(f * 0.6), bz=3.0)
        d.arms(f, (1.5, 1.35, 1.5, 1.3), (0.5, 0.5, 1.5, 0.3))                                                          # defender side arm out and braced
    d.speed(f0=1.4)
    return d.build()


@move('DR14', 'Chop Cut')
def dr14():
    d = Dr(20); d.carry(0, 5); d.speed(f0=2.0, f6=1.2, f10=2.6)
    d.at(6, R=(3.0, 6.0, 70, 4.0, 0.8, 0.4), L=(-2.4, 2.0, 0, None), ball=(2.2, 7.6), croll=0.2, cpitch=0.3)
    d.at(7, R=(0.8, 5.4, 65, 3.4, 0.9, 0.4), ball=(0.2, 4.8), croll=-0.1, cpitch=0.32)                                    # outside of the boot chops it back across
    d.at(8, R=(-1.8, 3.2, 55, 3.2, 0.9, 0.4), L=(-2.8, 2.4, 0, None), ball=(-2.0, 3.6), croll=-0.3, proll=-0.1, cpitch=0.3)
    d.at(9, R=(-1.4, 5.0, 30, 4.0), ball=(-2.8, 6.0), croll=-0.2, cpitch=0.3)
    d.arms(7, (0.5, 0.9, 1.0, 0.7), (0.9, 1.3, 1.4, 1.0))
    d.turn(**{'f7': 0.0, 'f11': PI / 2, 'f19': PI / 2}); burst(d, 10, 19, 0.3); settle(d, 10, 19)
    return d.build()


@move('DR15', 'Stepover Chain')
def dr15():
    d = Dr(30); d.carry(0, 4); d.speed(f0=1.8, f5=1.1, f17=3.0)
    f = 5
    for side in ('R', 'L', 'R', 'L'): f = stepover(d, f, side)
    f = push_out(d, f, 'R', dx=3.0, dy=11.0)
    burst(d, f, 29); d.turn(**{'f%d' % f: 0.0, 'f%d' % (f + 2): -0.4, 'f29': -0.4}); settle(d, f, 29)
    return d.build()


@move('DR16', 'Heel Flick')
def dr16():
    d = Dr(24); d.carry(0, 4); d.speed(f0=2.0, f9=1.2, f12=2.8)
    d.at(5, R=(2.4, 2.0, 20, None), L=(-2.4, 0.0, 0, None), ball=(0.4, 6.4), cpitch=0.2)
    d.at(6, R=(2.0, 6.0, 30, 3.4), L=(-2.4, 4.0, 0, None), ball=(0.4, 5.6), cpitch=0.3)                                    # steps past the ball
    d.at(7, R=(0.8, 3.4, -70, 5.0), ball=(0.4, 4.4, 3.0), cpitch=0.34, pyaw=0.25, hpitch=0.5)                              # trailing leg sweeps back through
    d.at(8, R=(0.4, 1.2, -75, 6.4), ball=(0.4, 3.0, 4.0), cpitch=0.3, pyaw=0.3)                                            # heel meets it
    for i, (y, z) in enumerate(((6.5, 10), (10.5, 16), (14.0, 18), (16.5, 14), (18.0, 8), (18.6, 3.5))): d.m.k(9 + i, bx=0.4, by=y, bz=z, bvis=1.0)   # up and over, in front
    d.at(9, R=(0.2, 3.0, -50, 9.0), cpitch=0.2, hpitch=0.1); d.at(10, R=(0.6, 5.0, -10, 7.0), cpitch=0.22)
    d.at(11, R=(1.6, 6.0, 10, 4.0)); 
    for f in (7, 8, 9): d.arms(f, (0.8, 0.8, 1.0, 0.6), (1.0, 1.0, 1.2, 0.8))
    burst(d, 11, 23, 0.34); ball_ahead(d, 15, [15.5, 13.5, 12.4, 11.8, 11.8, 11.5, 11.8, 11.4, 11.6], 0.4)
    return d.build()


@move('DR17', 'Drive Through')
def dr17():
    d = Dr(18, speed=2.5); d.carry(0, 17, lean=0.3); d.fx = {0: 0.9, 17: 1.0}
    for f in range(0, 18): d.arms(f, None, None)
    return d.build()


@move('DR18', 'Skill Combo')
def dr18():
    d = Dr(30); d.carry(0, 3); d.speed(f0=2.0, f4=1.2, f20=3.0)
    f = stepover(d, 4, 'R')
    d.at(f, R=(4.2, 8.4, 75, 3.0, 0.9, 0.5), L=(-2.4, 2.0, 0, None), ball=(3.8, 8.8), croll=0.34, cpitch=0.28)           # elastico
    d.at(f + 1, R=(0.0, 9.2, 45, 3.2, -1.2, 0.1), ball=(-2.6, 9.6), croll=-0.38, cpitch=0.3)
    f += 2
    d.at(f, L=(-3.0, 7.0, 30, 3.4, 1.0, 0.1), R=(1.6, 4.0, 0, None), ball=(-2.4, 8.4), croll=-0.1, cpitch=0.3)            # quick double touch
    d.at(f + 1, R=(0.6, 8.0, 30, 3.4, -1.0, 0.1), L=(-1.6, 4.0, 0, None), ball=(-0.2, 9.0), croll=0.1, cpitch=0.3)
    f += 2; f = push_out(d, f, 'R', dx=3.0, dy=11.0)
    burst(d, f, 29); d.turn(**{'f12': 0.0, 'f18': -0.5, 'f29': -0.5}); settle(d, f, 29)
    return d.build()


@move('DR19', 'Fake Pass')
def dr19():
    d = Dr(22); d.carry(0, 5); d.speed(f0=2.0, f6=1.2, f11=2.8)
    d.at(6, R=(2.2, -1.0, 40, 6.0), L=(-2.4, 4.0, 0, None), ball=(0.9, 8.0), cpitch=0.2, hyaw=0.9, hpitch=-0.1)           # looks right at a teammate
    d.at(7, R=(1.6, 5.0, 50, 5.0, -1.2, 0.1), ball=(0.9, 8.0), cpitch=0.26, hyaw=0.9)
    d.at(8, R=(-0.6, 9.2, 50, 4.8, -1.2, 0.1), ball=(0.9, 8.0), cpitch=0.3, hyaw=0.7, pyaw=0.2)                           # inside foot sweeps over, no touch
    d.at(9, R=(-1.8, 8.6, 30, None), ball=(0.9, 8.2), cpitch=0.3, hyaw=0.2)
    d.at(10, L=(-2.0, 9.0, 60, 3.2, 0.8, 0.4), R=(0.8, 5.0, 0, None), ball=(2.0, 10.4), cpitch=0.3, hyaw=-0.2)             # then away with the other
    d.arms(6, (0.5, 0.8, 0.8, 0.6), (1.55, 0.2, 1.55, 0.1)); d.arms(7, (0.5, 0.8, 0.8, 0.6), (1.55, 0.2, 1.55, 0.1))
    d.turn(**{'f9': 0.0, 'f12': -0.5, 'f21': -0.5}); burst(d, 11, 21, 0.3); settle(d, 11, 21)
    return d.build()


@move('DR20', 'Quick Touch')
def dr20():
    d = Dr(20, speed=1.5); d.fx = {0: 0.45, 19: 0.5}
    # tiny alternating taps with the inside of each boot, feet shuffling close together, low and busy, shoulders rocking
    for f in range(20):
        ph = f % 4; rk = 1 if (f // 4) % 2 == 0 else -1
        base = dict(pz=23.2, cpitch=0.2, hpitch=0.5, croll=0.1 * (1 if ph < 2 else -1), proll=0.06 * (1 if ph < 2 else -1))
        if ph == 0: d.at(f, R=(0.8, 6.6, 30, 3.2, -1.0, 0.1), L=(-2.2, 3.0, 0, None), ball=(-0.4, 7.4), **base)
        elif ph == 1: d.at(f, R=(1.0, 4.6, 10, 4.0), L=(-1.0, 5.6, 25, 3.6), ball=(-0.6, 7.8), **base)
        elif ph == 2: d.at(f, L=(-0.8, 6.6, 30, 3.2, 1.0, 0.1), R=(2.2, 3.0, 0, None), ball=(0.4, 7.4), **base)
        else: d.at(f, L=(-1.0, 4.6, 10, 4.0), R=(1.0, 5.6, 25, 3.6), ball=(0.6, 7.8), **base)
        d.arms(f, (0.5, 0.8, 0.9, 0.6), (0.5, 0.8, 0.9, 0.6))
    return d.build()


@move('DR21', 'Spin Away')
def dr21():
    d = Dr(24); d.carry(0, 4); d.speed(f0=2.0, f5=0.8, f10=0.3, f14=2.6)
    d.at(5, R=(2.0, 4.0, 20, None), L=(-2.4, 1.0, 0, None), ball=(0.8, 7.0), cpitch=0.3, pz=23.4)
    arc = ((0.8, 6.0), (0.6, 4.2), (0.0, 2.4), (-0.8, 2.2), (-1.0, 3.8), (-0.4, 5.8))
    for f, (bx, by) in zip(range(6, 12), arc):
        u = (f - 6) / 5.0
        d.at(f, R=(bx + 0.1, by + 0.4, -45, 4.6), L=(-2.4, 1.4, 0, None), ball=(bx, by, 2.4), cpitch=0.42, pz=22.6 + 0.8 * abs(u - 0.5),
             croll=-0.3, proll=-0.16, hyaw=0.7 * (1 - u), cyaw=0.35 * (1 - u), pyaw=-0.3 * (1 - u))                          # head and shoulders lead, hips follow
        d.arms(f, (1.1, 0.9, 1.4, 0.8), (0.3, 0.5, 1.2, 0.3))                                                             # outside arm raised, inside arm tucked
    d.at(12, R=(1.2, 9.0, 40, 3.2), ball=(0.8, 10.0), cpitch=0.3, croll=0.0, proll=0.0)
    d.turn(**{'f6': 0.0, 'f11': PI, 'f23': PI}); burst(d, 13, 23, 0.3); settle(d, 12, 23)
    return d.build()


@move('DR22', 'Trap and Turn')
def dr22():
    d = Dr(24, speed=0.8)
    # the ball arrives from the front, is killed under the sole, and he pivots round it, head leading
    for f in range(0, 6):
        d.at(f, R=(2.2, 1.0 + 0.2 * f, 0, None), L=(-2.2, 1.4, 0, None), ball=(0.8, 15.0 - 1.4 * f, 3.0), hpitch=0.2, cpitch=0.1, pz=24.4)
        d.arms(f, (0.4, 0.6, 0.9, 0.4), (0.6, 0.7, 1.0, 0.5))
    d.at(5, R=(1.0, 4.0, -30, 5.5), ball=(0.8, 7.4, 3.0), cpitch=0.2)
    d.at(6, R=(0.8, 6.4, -50, 4.9), ball=(0.8, 6.4, 2.4), cpitch=0.3, pz=23.6)                                            # sole kills it
    d.at(7, R=(0.8, 5.2, -50, 4.9), ball=(0.8, 5.2, 2.4), cpitch=0.34, hyaw=0.6, cyaw=0.3, pyaw=-0.25, croll=-0.18)
    d.at(8, R=(0.2, 2.8, -50, 4.9), ball=(0.2, 2.8, 2.4), cpitch=0.34, hyaw=0.4, cyaw=0.2, pyaw=-0.2, croll=-0.25, pz=22.8)
    d.at(9, R=(-1.2, 1.4, -45, 4.9), ball=(-1.2, 1.4, 2.4), cpitch=0.3, hyaw=0.2, cyaw=0.1, pyaw=-0.1, croll=-0.2, pz=22.8)
    d.at(10, R=(-1.0, 4.0, 40, 3.2, -1.0, 0.1), ball=(-0.4, 6.2), cpitch=0.3, croll=0.0)
    d.at(11, L=(-1.6, 8.0, 20, None), R=(1.6, 5.0, 20, None), ball=(0.4, 9.6), cpitch=0.3)
    for f in (6, 7, 8, 9): d.arms(f, (0.9, 0.9, 1.3, 0.7), (0.4, 0.6, 1.2, 0.3))
    d.turn(**{'f6': 0.0, 'f10': PI, 'f23': PI}); d.speed(f0=0.0, f10=0.4, f12=2.6); burst(d, 12, 23, 0.3); settle(d, 12, 23)
    return d.build()


@move('DR23', 'Slalom')
def dr23():
    d = Dr(26); d.carry(0, 25, lean=0.14); d.fx = {0: 0.7, 25: 0.8}
    th = {f: 0.6 * math.sin(2 * PI * f / 13.0) for f in range(0, 26, 1)}; d.th = th
    for f in range(26):
        sw = math.sin(2 * PI * f / 13.0)
        d.m.k(f, croll=-0.3 * sw, proll=-0.16 * sw, bx=1.6 * math.sin(2 * PI * (f + 2) / 13.0 + 0.4), by=8.0 - 1.6 * ((f % 6) / 6.0))
    return d.build()


@move('DR24', 'Burst of Pace')
def dr24():
    d = Dr(22, speed=0.0)
    for f in range(0, 4): d.at(f, R=(2.4, -1.5, 0, None), L=(-2.4, 2.0, 0, None), ball=(0.6, 7.0), pz=21.4, cpitch=0.55, ppitch=0.3, hpitch=0.1, root_y=0.0)
    d.arms(0, (-0.4, 0.6, 0.3, 0.5), (0.9, 0.7, 1.4, 0.6)); d.arms(3, (-0.6, 0.6, 0.2, 0.5), (1.0, 0.7, 1.4, 0.6))
    d.at(4, R=(2.4, -4.0, 40, 6.0), L=(-2.4, 4.0, 0, None), ball=(0.6, 7.4), pz=23.4, cpitch=0.6)
    burst(d, 5, 21, 0.5); settle(d, 5, 21)
    d.speed(f0=0.0, f4=0.6, f6=2.0, f10=3.4, f21=3.6); d.fx = {0: 0.0, 5: 0.4, 9: 1.0, 21: 1.2}
    return d.build()


@move('DR25', 'Wall Run')
def dr25():
    d = Dr(22, speed=3.0); d.carry(0, 21, lean=0.2); d.fx = {0: 0.8, 21: 0.9}
    d.turn(**{'f0': 0.12, 'f21': 0.12})
    for f in range(22): d.m.k(f, hpitch=-0.1, bx=0.8 + 0.4 * math.sin(f * 0.5), by=11.5 - 3.0 * ((f % 6) / 6.0))                  # ball pushed well ahead down the line
    return d.build()


@move('DR26', 'Rainbow Flick')
def dr26():
    d = Dr(26); d.carry(0, 4); d.speed(f0=2.0, f5=0.8, f10=1.0, f16=2.4)
    d.at(5, R=(2.2, 2.0, 20, None), L=(-2.2, 4.0, 0, None), ball=(0.6, 6.0), cpitch=0.3, pz=23.6)
    d.at(6, R=(0.6, 3.0, 20, None), L=(-0.6, 4.6, 20, None), ball=(0.0, 5.0), cpitch=0.3, pz=23.2)                         # ball pinned between the boots
    d.at(7, R=(0.4, 4.6, -30, 4.6), L=(0.0, 5.2, -20, 3.0), ball=(0.2, 4.6, 5.0), cpitch=0.28, pz=23.4)
    d.at(8, R=(0.6, 4.0, -30, 7.0), L=(-0.6, 4.6, 40, 3.4), ball=(0.4, 4.2, 8.0), cpitch=0.2, pz=24.4)                      # rolled up the back of the leg
    d.at(9, R=(0.4, 5.0, -10, 11.0), L=(-1.2, 5.0, 40, 8.0), ball=(0.3, 4.4, 15.0), cpitch=0.1, pz=27.0)                    # hop and flick
    arc = ((0.3, 4.0, 28), (0.4, 4.0, 42), (0.6, 5.5, 52), (0.8, 8.0, 56), (1.0, 11.0, 52), (1.0, 14.0, 42), (1.0, 16.0, 28), (1.0, 17.0, 14), (1.0, 16.5, 5))
    for i, (x, y, z) in enumerate(arc): d.m.k(10 + i, bx=x, by=y, bz=z, bvis=1.0)                                            # up over the head and down in front
    d.at(10, R=(0.4, 6.0, 0, 10.0), L=(-1.6, 6.0, 30, 9.0), cpitch=-0.1, pz=28.6, hpitch=-0.5)
    d.at(11, R=(0.6, 5.0, 20, 6.0), L=(-1.6, 4.0, 20, 6.0), cpitch=0.0, pz=27.4, hpitch=-0.7)
    d.at(12, R=(1.6, 4.0, 20, 3.5), L=(-1.8, 3.0, 20, 3.5), cpitch=0.1, pz=25.4, hpitch=-0.7)
    d.at(13, R=(2.0, 3.0, 5, None), L=(-2.0, 4.0, 5, None), cpitch=0.2, pz=24.0, hpitch=-0.5)
    d.at(14, R=(2.0, 4.0, 5, None), L=(-2.0, 5.0, 5, None), cpitch=0.24, pz=23.6, hpitch=-0.2)
    d.at(15, R=(1.8, 8.0, 10, None), L=(-2.0, 3.0, 5, None), cpitch=0.28, pz=24.0)
    for f in (9, 10, 11): d.arms(f, (1.0, 0.8, 1.3, 0.7), (0.8, 0.9, 1.4, 0.7))
    burst(d, 16, 25, 0.3); settle(d, 19, 25)
    return d.build()


@move('DR27', 'Outside Hook')
def dr27():
    d = Dr(20); d.carry(0, 5); d.speed(f0=2.0, f6=1.4, f10=2.6)
    d.at(6, R=(3.2, 5.0, 70, 4.0, 0.8, 0.4), L=(-2.4, 2.0, 0, None), ball=(2.4, 7.6), croll=0.3, proll=0.1, cpitch=0.3)
    d.at(7, R=(3.8, 8.4, 75, 3.4, 0.9, 0.5), ball=(3.4, 9.0), croll=0.34, cpitch=0.3)                                     # reaches round it
    d.at(8, R=(1.4, 9.8, 70, 3.4, 0.9, 0.5), ball=(1.6, 9.2), croll=-0.1, cpitch=0.3)                                       # hooks it in across the body
    d.at(9, R=(-1.0, 8.0, 60, 3.4, 0.9, 0.4), ball=(-1.2, 7.6), croll=-0.3, proll=-0.16, cpitch=0.3)
    d.at(10, R=(-1.4, 7.0, 30, None), L=(-3.0, 4.0, 20, 4.0), ball=(-2.6, 8.8), croll=-0.2, cpitch=0.3)
    d.turn(**{'f7': 0.0, 'f11': 0.9, 'f19': 0.9}); burst(d, 11, 19, 0.3); settle(d, 11, 19)
    return d.build()


@move('DR28', 'Pull Push')
def dr28():
    d = Dr(20); d.carry(0, 5); d.speed(f0=2.0, f6=0.8, f12=2.6)
    d.at(6, R=(1.0, 8.0, -30, 6.0), L=(-2.2, 2.4, 0, None), ball=(0.9, 8.0), cpitch=0.4, pz=23.4)
    d.at(7, R=(0.8, 7.4, -55, 4.9), ball=(0.8, 7.4, 2.4), cpitch=0.5, pz=22.8)
    d.at(8, R=(0.8, 5.0, -55, 4.9), ball=(0.8, 5.0, 2.4), cpitch=0.5, pz=22.8)
    d.at(9, R=(0.8, 3.0, -50, 4.9), ball=(0.8, 3.0, 2.4), cpitch=0.46, pz=23.0)                                            # pulls it back…
    d.at(10, R=(0.8, 1.6, 20, 3.4), ball=(0.8, 3.6), cpitch=0.4, pz=23.4)                                                  # …foot flips over it
    d.at(11, R=(0.8, 8.0, 70, 3.2), ball=(0.8, 9.4), cpitch=0.34)                                                           # …and the laces push it away
    d.at(12, R=(1.2, 10.5, 50, 4.4), ball=(0.8, 12.4), cpitch=0.3)
    burst(d, 13, 19, 0.34); settle(d, 13, 19)
    return d.build()


@move('DR29', 'Dummy Run')
def dr29():
    d = Dr(22, speed=3.0); d.carry(0, 21, lean=0.2, ball=False); d.hide_ball(0, 21); d.fx = {0: 0.8, 21: 1.0}
    d.turn(**{'f0': 0.0, 'f6': 0.45, 'f21': 0.45})
    for f in range(22):
        d.m.k(f, hyaw=-0.9, hpitch=0.0)                                                                                   # looking back at the man on the ball
        d.arms(f, (2.5, 0.35, 2.7, 0.25), (0.3, 0.3, 0.9, 0.2))                                                           # calling for it
    return d.build()


@move('DR30', 'Showboat Spin')
def dr30():
    d = Dr(28, ms=64, speed=0.0)
    for f in range(0, 5): d.at(f, R=(2.2, 1.0, 0, None), L=(-2.2, 1.4, 0, None), ball=(0.6, 6.0), pz=24.4, cpitch=0.1)
    d.at(5, R=(1.0, 4.0, 30, 3.4), L=(-2.2, 1.4, 0, None), ball=(0.8, 6.4), cpitch=0.2)
    d.at(6, R=(0.8, 4.6, 30, 6.0), ball=(0.8, 5.6, 9.0), cpitch=0.1, pz=24.6)                                                # ball up onto the foot
    for f in range(7, 19):
        u = (f - 7) / 11.0; bob = 1.2 * math.sin((f - 7) * 1.4); hop = 1.6 * abs(math.sin(u * PI * 2))
        d.at(f, R=(0.8, 4.6, 30, 6.0 + bob), L=(-2.2, 1.4, 0, None), ball=(0.8, 4.8, 9.0 + bob), cpitch=0.1 - 0.1 * u, pz=24.6 + hop, hpitch=-0.1,
             hyaw=0.6 * (1 - u), croll=0.12, proll=0.06)
        d.arms(f, (2.3, 0.45, 2.6, 0.3), (0.6, 0.6, 1.3, 0.4))                                                            # one arm thrown up, the other at the hip
    d.at(19, R=(1.4, 5.0, 40, 5.0), ball=(1.0, 6.0, 7.0), cpitch=0.2)
    d.at(20, R=(1.6, 9.0, 60, 3.4), ball=(1.0, 11.0, 3.0), cpitch=0.3)
    d.turn(**{'f6': 0.0, 'f18': 2 * PI, 'f27': 2 * PI}); d.speed(f0=0.0, f20=1.6, f22=2.4); burst(d, 21, 27, 0.28); settle(d, 21, 27)
    d.arms(26, (0.3, 0.4, 0.7, 0.3), (0.3, 0.4, 0.7, 0.3))
    return d.build()


def build(ids=None):
    out = []
    for id_, (label, fn) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); name = id_.lower() + '_' + label.lower().replace(' ', '_')
        m.save(name, label, 'auto-generated by sprites/moves_dribble.py'); out.append((id_, name))
    return out


if __name__ == '__main__':
    for id_, name in build(sys.argv[1:] or None): print(id_, name)
