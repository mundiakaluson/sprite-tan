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
    sg = 1 if side == 'R' else -1; o = 'L' if side == 'R' else 'R'
    pos = lambda x, y, fp, z=None: (sg * x, y, fp, z)
    g = dict(R=None, L=None)
    kw = lambda a, b: {side: a, o: b}
    d.at(f0, ball=(sg * 0.2, 8.0), **kw(pos(2.4, 5.2, 30, 6.0), (-sg * 2.2, 1.0, 0, None)), croll=0.1 * sg, cpitch=0.2)
    d.at(f0 + 1, ball=(sg * 0.2, 8.2), **kw(pos(0.2, 9.6, 50, 8.5), (-sg * 2.2, 2.0, 0, None)), croll=-0.12 * sg, cpitch=0.22)
    d.at(f0 + 2, ball=(sg * 0.2, 8.4), **kw(pos(-3.0, 8.4, 0, None), (-sg * 1.4, 3.2, 0, None)), croll=-0.2 * sg, proll=-0.1 * sg)
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
    d = Dr(26); d.carry(0, 5); d.speed(f0=2.0, f8=1.5, f15=2.4)
    d.at(6, R=(0.8, 6.0, -10, None), L=(-2.2, 2.0, 0, None), ball=(0.8, 7.4), cpitch=0.3, pz=23.4)
    d.at(7, R=(0.8, 7.6, -5, None), ball=(0.8, 7.8, 2.6), cpitch=0.24, pz=23.8)                                      # toe scoops under it
    d.at(8, R=(0.8, 9.0, 15, 6.5), ball=(0.8, 9.0, 7.0), cpitch=0.1)
    for f in range(9, 19):
        u = (f - 8) / 9.0; d.m.k(f, bx=0.8 + 0.0, by=9.0 + 1.6 * (f - 8) - 2.0 * (f - 8) * 1.1 * 0 - 0.0, bz=7.0 + 27.0 * 4 * u * (1 - u), bvis=1.0)
    for f in range(9, 19): d.m.k(f, by=9.0 - 1.35 * (f - 8))
    for f in range(8, 17): d.m.k(f, hpitch=-0.6, cpitch=0.05, hyaw=0.0)
    d.at(9, R=(0.8, 9.6, 5, 8.0), cpitch=0.0); d.at(10, R=(0.8, 8.0, 0, None), cpitch=0.1)
    burst(d, 11, 25, 0.25); d.arms(10, (1.0, 1.1, 1.2, 1.0), (1.0, 1.1, 1.2, 1.0))
    for f in range(19, 26):
        saw = (f % 6) / 6.0; d.m.k(f, bx=0.6, by=11.6 - 3.0 * saw, bz=3.0, bvis=1.0)
    d.m.k(18, by=3.2, bz=3.0)
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
    d = Dr(20); d.carry(0, 4); d.speed(f0=2.2, f12=2.6); d.fx = {0: 0.5, 19: 0.6}
    d.at(5, R=(0.8, 6.0, -40, 5.0), L=(-2.2, 2.4, 0, None), ball=(0.8, 7.2, 2.6), cpitch=0.26)
    d.at(6, R=(0.0, 6.4, -45, 4.8), ball=(0.0, 7.0, 2.6), cpitch=0.28)
    d.at(7, R=(-0.9, 6.6, -45, 4.8), ball=(-0.9, 7.2, 2.6), cpitch=0.3)                                                    # sole rolls it across
    d.at(8, L=(-1.2, 7.8, 40, 3.2, 1.0, 0.1), R=(1.6, 3.0, 0, None), ball=(-0.4, 9.6), cpitch=0.34)                      # other foot pushes on
    burst(d, 9, 19, 0.3); settle(d, 9, 19); d.fx.update({9: 0.9, 12: 1.0})
    return d.build()


@move('DR12', 'Shoulder Shield')
def dr12():
    d = Dr(22, speed=1.4); d.carry(0, 21, tight=True, cad=0.7)
    for f in range(0, 22):
        d.m.k(f, pyaw=-0.9, cyaw=-1.0, hyaw=0.7, croll=-0.14, cpitch=0.16, pz=23.6, bx=-1.6 + 0.3 * math.sin(f * 0.6), by=6.4 + 0.5 * math.sin(f * 0.6), bz=3.0)
        d.arms(f, (1.5, 1.35, 1.5, 1.3), (0.5, 0.5, 1.5, 0.3))                                                          # defender side arm out and braced
    d.speed(f0=1.4)
    return d.build()


@move('DR13', 'Hold Up Play')
def dr13():
    d = Dr(24, ms=70, speed=0.0)
    for f in range(24):
        sw = math.sin(f * 0.55)
        d.at(f, R=(3.4, 0.6 + 0.4 * sw, 0, None), L=(-3.4, -1.2, 0, None), ball=(0.2, 4.6, 3.0), pz=22.4, ppitch=-0.2, cpitch=0.36 + 0.05 * sw, croll=0.07 * sw, hpitch=0.25, hyaw=0.0, pyaw=0.04 * sw, root_y=0.0)
        d.arms(f, (0.6 + 0.12 * sw, 1.0, 1.0, 0.7), (0.6 - 0.12 * sw, 1.0, 1.0, 0.7))                                    # arms out feeling the defender
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
    d = Dr(28); d.carry(0, 4); d.speed(f0=2.0, f5=1.2, f14=3.0)
    f = stepover(d, 5, 'R'); f = stepover(d, f, 'L'); f = stepover(d, f, 'R')
    f = push_out(d, f, 'L', dx=-3.0, dy=10.8)
    burst(d, f, 27); d.turn(**{'f14': 0.0, 'f16': 0.4, 'f27': 0.4}); settle(d, f, 27)
    return d.build()


@move('DR16', 'Heel Flick')
def dr16():
    d = Dr(22); d.carry(0, 4); d.speed(f0=2.0, f9=1.4, f12=2.8)
    d.at(5, R=(2.4, 2.0, 20, None), L=(-2.4, 0.0, 0, None), ball=(0.4, 6.0), cpitch=0.2)
    d.at(6, R=(2.0, 6.0, 30, 3.4), L=(-2.4, 3.0, 0, None), ball=(0.4, 6.0), cpitch=0.3)                                    # steps past the ball
    d.at(7, R=(0.6, 3.6, -70, 4.0), ball=(0.4, 5.0), cpitch=0.34, pyaw=0.2)                                                # trailing heel taps it forward
    d.at(8, R=(0.2, 1.8, -70, 6.0), ball=(0.4, 8.8, 4.0), cpitch=0.28)
    d.at(9, R=(0.4, 3.0, -40, 7.0), ball=(0.4, 12.0, 4.8), cpitch=0.22)
    d.at(10, R=(1.0, 6.0, 10, 4.0), ball=(0.4, 13.0, 3.0), cpitch=0.2)
    d.arms(7, (0.8, 1.0, 1.0, 0.8), (0.8, 1.0, 1.0, 0.8))
    burst(d, 11, 21, 0.34); ball_ahead(d, 11, [12.5, 11, 10, 9.5, 9.5, 9.0, 9.4, 9.0, 9.4, 9.0, 9.2], 0.4)
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
    d = Dr(18, speed=1.6); d.carry(0, 17, cad=1.8, tight=True); d.fx = {0: 0.5, 17: 0.6}
    return d.build()


@move('DR21', 'Spin Away')
def dr21():
    d = Dr(22); d.carry(0, 4); d.speed(f0=2.0, f5=0.8, f10=0.3, f14=2.6)
    d.at(5, R=(2.0, 4.0, 20, None), L=(-2.4, 1.0, 0, None), ball=(0.8, 7.0), cpitch=0.3, pz=23.4)
    for f, (bx, by) in zip(range(6, 12), ((0.8, 6.0), (0.6, 4.0), (0.0, 2.0), (-0.8, 2.4), (-1.0, 4.0), (-0.4, 6.0))):
        d.at(f, R=(bx + 0.1, by + 0.4, -45, 4.6), L=(-2.4, 1.4, 0, None), ball=(bx, by, 2.4), cpitch=0.42, pz=22.8, croll=-0.1)
        d.arms(f, (1.3, 1.25, 1.4, 1.2), (1.3, 1.25, 1.4, 1.2))                                                          # arms wide to hold the defender off
    d.at(12, R=(1.2, 9.0, 40, 3.2), ball=(0.8, 10.0), cpitch=0.3)
    d.turn(**{'f6': 0.0, 'f11': PI, 'f21': PI}); burst(d, 13, 21, 0.3); settle(d, 12, 21)
    return d.build()


@move('DR22', 'Trap and Turn')
def dr22():
    d = Dr(24, speed=0.8)
    # the ball arrives from the front, is killed under the sole, and the body spins round it
    for f in range(0, 7): d.at(f, R=(2.2, 1.0, 0, None), L=(-2.2, 1.4, 0, None), ball=(0.6, 14.0 - 1.6 * f, 3.0), hpitch=0.1, cpitch=0.1, pz=24.4, brx=-2.0 * f) if False else None
    for f in range(0, 7):
        d.at(f, R=(2.2, 1.0 + 0.2 * f, 0, None), L=(-2.2, 1.4, 0, None), ball=(0.8, 15.0 - 1.4 * f, 3.0), hpitch=0.2, cpitch=0.1, pz=24.4)
    d.at(5, R=(1.0, 4.0, -30, 5.5), ball=(0.8, 7.4, 3.0), cpitch=0.2)
    d.at(6, R=(0.8, 6.4, -50, 4.9), ball=(0.8, 6.4, 2.4), cpitch=0.3, pz=23.6)                                            # sole kills it
    d.at(7, R=(0.8, 5.2, -50, 4.9), ball=(0.8, 5.2, 2.4), cpitch=0.34)
    d.at(8, R=(0.2, 2.8, -50, 4.9), ball=(0.2, 2.8, 2.4), cpitch=0.34)
    d.at(9, R=(-1.2, 1.4, -45, 4.9), ball=(-1.2, 1.4, 2.4), cpitch=0.3)
    d.at(10, R=(-1.0, 4.0, 40, 3.2, -1.0, 0.1), ball=(-0.4, 6.2), cpitch=0.3)
    d.at(11, L=(-1.6, 8.0, 20, None), R=(1.6, 5.0, 20, None), ball=(0.4, 9.6), cpitch=0.3)
    d.arms(7, (1.2, 1.2, 1.3, 1.1), (1.2, 1.2, 1.3, 1.1))
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
    d.at(8, R=(0.6, 4.0, -30, 7.0), L=(-0.6, 4.6, 40, 3.4), ball=(0.4, 4.2, 7.5), cpitch=0.2, pz=24.4)                      # rolled up the back of the leg
    d.at(9, R=(0.4, 5.0, -10, 11.0), L=(-1.2, 5.0, 40, 8.0), ball=(0.2, 4.8, 12.0), cpitch=0.1, pz=27.0)                    # hop, flick
    d.at(10, R=(0.4, 6.0, 0, 10.0), L=(-1.6, 6.0, 30, 9.0), ball=(0.0, 4.0, 24.0), cpitch=-0.1, pz=28.6, hpitch=-0.5)
    d.at(11, R=(0.6, 5.0, 20, 6.0), L=(-1.6, 4.0, 20, 6.0), ball=(0.0, 4.0, 36.0), cpitch=0.0, pz=27.4, hpitch=-0.6)
    d.at(12, R=(1.6, 4.0, 20, 3.5), L=(-1.8, 3.0, 20, 3.5), ball=(0.0, 7.0, 38.0), cpitch=0.1, pz=25.4, hpitch=-0.6)
    d.at(13, R=(2.0, 3.0, 5, None), L=(-2.0, 4.0, 5, None), ball=(0.0, 10.0, 28.0), cpitch=0.2, pz=24.0, hpitch=-0.4)
    d.at(14, R=(2.0, 4.0, 5, None), L=(-2.0, 5.0, 5, None), ball=(0.2, 11.0, 14.0), cpitch=0.24, pz=23.6)
    d.at(15, R=(1.8, 8.0, 10, None), L=(-2.0, 3.0, 5, None), ball=(0.2, 11.5, 3.0), cpitch=0.28, pz=24.0)
    for f in (9, 10, 11): d.arms(f, (1.2, 1.2, 1.4, 1.1), (1.2, 1.2, 1.4, 1.1))
    burst(d, 16, 25, 0.3); settle(d, 16, 25)
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
    d = Dr(26, ms=66, speed=0.0)
    for f in range(0, 5): d.at(f, R=(2.2, 1.0, 0, None), L=(-2.2, 1.4, 0, None), ball=(0.6, 6.0), pz=24.4, cpitch=0.1)
    d.at(5, R=(1.0, 4.0, 30, 3.4), L=(-2.2, 1.4, 0, None), ball=(0.8, 6.4), cpitch=0.2)
    d.at(6, R=(0.8, 4.6, 30, 6.0), ball=(0.8, 5.6, 9.0), cpitch=0.1, pz=24.6)                                                # ball up onto the foot
    for f in range(7, 18):
        bob = 1.2 * math.sin((f - 7) * 1.4)
        d.at(f, R=(0.8, 4.6, 30, 6.0 + bob), L=(-2.2, 1.4, 0, None), ball=(0.8, 4.8, 9.0 + bob), cpitch=0.1, pz=24.6, hpitch=-0.1)
        d.arms(f, (1.3, 1.25, 1.4, 1.1), (1.3, 1.25, 1.4, 1.1))
    d.at(18, R=(1.4, 5.0, 40, 5.0), ball=(1.0, 6.0, 7.0), cpitch=0.2)
    d.at(19, R=(1.6, 9.0, 60, 3.4), ball=(1.0, 11.0, 3.0), cpitch=0.3)
    d.turn(**{'f6': 0.0, 'f17': 2 * PI, 'f25': 2 * PI}); d.speed(f0=0.0, f19=1.6, f21=2.4); burst(d, 20, 25, 0.28); settle(d, 20, 25)
    d.arms(24, (0.3, 0.4, 0.7, 0.3), (0.3, 0.4, 0.7, 0.3))
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
