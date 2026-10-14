"""The 30 SHOT skill animations (SH01-SH30). Run:  python moves_shot.py [id ...]  to (re)write data/animations/shXX_*.json"""
import math, sys
import moves as M
from moves import D, path, kick_base, finesse_base, blank, stand

MOVES = {}


def move(id_, label):
    def deco(fn):
        MOVES[id_] = (label, fn); return fn
    return deco


def frame(m, f, R=None, L=None, **kw):
    """R/L = (x, y, fp_deg, z|None, fy, fr). kw are body params (root_y, pz, pyaw, cpitch, ...)"""
    if R: m.foot(f, 'R', R[0], R[1], R[2], *(R[4:6] if len(R) > 4 else (0, 0)), z=R[3] if len(R) > 3 else None)
    if L: m.foot(f, 'L', L[0], L[1], L[2], *(L[4:6] if len(L) > 4 else (0, 0)), z=L[3] if len(L) > 3 else None)
    if kw: m.k(f, **kw)
    return m


def arms_out(m, f, r=(-0.4, 0.6, 0.0, 0.4), l=(0.9, 1.2, 1.5, 1.0)):
    m.arms(f, 'R', *r); m.arms(f, 'L', *l)


@move('SH01', 'Side Foot Place')
def sh01():
    m = kick_base()
    # calm: short backswing, inside of the foot, upright, soft follow-through
    frame(m, 9, R=(2.4, -3.0, 40, 6.5), L=(-4.0, 3.5, -6), root_y=1.5, pz=24.8, cpitch=0.12, ppitch=0.05, pyaw=-0.1)
    frame(m, 10, R=(2.6, -6.0, 44, 9.0), L=(-4.6, 5.5, -6), root_y=2.0, pz=24.4, cpitch=0.14, ppitch=0.05, pyaw=-0.16)
    frame(m, 11, R=(2.8, 1.5, 50, 6.2, -1.1, 0.1), L=(-4.6, 6.0, -6), root_y=2.4, pz=24.3, cpitch=0.14, ppitch=0.05, pyaw=0.05)
    frame(m, 12, R=(2.2, 8.0, 52, 3.6, -1.3, 0.1), L=(-4.4, 6.4, -6), root_y=2.8, pz=24.2, cpitch=0.16, ppitch=0.06, pyaw=0.12)
    frame(m, 13, R=(1.4, 13.0, 48, 4.6, -1.0, 0.0), L=(-4.2, 6.4, -6), root_y=4.0, pz=24.4, cpitch=0.14, pyaw=0.18)
    frame(m, 14, R=(0.8, 16.5, 40, 5.5, -0.5, 0.0), L=(-3.8, 6.2, -5), root_y=6.5, pz=24.4, cpitch=0.12, pyaw=0.14)
    frame(m, 15, R=(1.6, 17.5, 25, 3.2, -0.2), L=(-3.0, 8.0, 18, 5.0), root_y=9.5, pz=24.4, cpitch=0.12, pyaw=0.08)
    frame(m, 16, R=(2.0, 19.5, 10, None), L=(-2.4, 10.0, 20, 6.5), root_y=12.2, pz=23.6, cpitch=0.14, pyaw=0.04)
    arms_out(m, 10, (-0.2, 0.6, 0.3, 0.3), (0.7, 1.1, 1.4, 0.8)); arms_out(m, 12, (-0.1, 0.6, 0.4, 0.3), (0.8, 1.1, 1.4, 0.9))
    m.ball(12, path(10, speed=5.5, rise=0.0, start=(1.4, 16.0, 3.0)), spin_x=1.6)
    m.ms = 78
    return m


@move('SH02', 'Instep Drive')
def sh02():
    m = kick_base()
    for f, cp in ((9, 0.2), (10, 0.28), (11, 0.3), (12, 0.32), (13, 0.28)): m.k(f, cpitch=cp, ppitch=cp * 0.5)
    m.k(14, pz=26.4)
    m.ball(12, path(10, speed=8.5, rise=0.2, start=(1.5, 18.5, 4.0)), spin_x=2.6)
    return m


@move('SH03', 'Finesse Curler')
def sh03():
    m = finesse_base()
    return m


@move('SH04', 'Trivela Bender')
def sh04():
    m = finesse_base()
    # outside of the boot: foot rolls the other way, leg swings out-to-in with a wider, more open hip
    for f in (11, 12, 13, 14, 15):
        k = m.keys[f]
        k['R_fy'] = -k.get('R_fy', 0.0) * 0.55 + 0.5; k['R_fr'] = 0.35
        k['R_ax'] = k['R_ax'] + 1.6
    m.k(12, pyaw=-0.2, proll=0.12, cpitch=-0.05)
    m.ball(12, path(12, speed=7.0, rise=0.15, curve=0.9, start=(2.6, 16.0, 3.6)), spin_x=1.0, spin_z=2.0)
    return m


@move('SH05', 'Chip Lob')
def sh05():
    m = kick_base()
    # scoop: short backswing, foot dug under the ball, soft lift
    frame(m, 10, R=(2.2, -7.0, 36, 6.8), L=(-4.4, 5.2, -6), root_y=2.0, pz=24.0, cpitch=0.1, ppitch=0.04, pyaw=-0.12)
    frame(m, 11, R=(2.0, 3.0, 30, 3.2), L=(-4.4, 5.8, -6), root_y=2.4, pz=23.4, cpitch=0.06, ppitch=0.0, pyaw=0.05)
    frame(m, 12, R=(1.6, 8.4, 20, 2.4), L=(-4.2, 6.0, -6), root_y=2.8, pz=23.2, cpitch=-0.02, ppitch=-0.04, pyaw=0.1)
    frame(m, 13, R=(1.2, 12.0, 5, 6.4), L=(-4.0, 6.0, -6), root_y=4.0, pz=23.8, cpitch=-0.04, pyaw=0.14)
    frame(m, 14, R=(1.0, 14.5, -8, 9.0), L=(-3.6, 6.2, -5), root_y=6.0, pz=24.6, cpitch=0.02, pyaw=0.1)
    frame(m, 15, R=(1.4, 16.0, -4, 8.0), L=(-3.0, 7.5, 10, 4.5), root_y=8.4, pz=24.2, cpitch=0.08, pyaw=0.06)
    frame(m, 16, R=(2.0, 18.0, 6, None), L=(-2.4, 9.5, 20, 6.0), root_y=11.5, pz=23.6, cpitch=0.1)
    arms_out(m, 12, (-0.5, 0.9, 0.2, 0.6), (0.6, 1.3, 1.2, 0.9))
    m.ball(12, path(11, speed=4.2, rise=1.6, dip=1.1, start=(1.4, 13.5, 4.5)), spin_x=-2.4)
    m.ms = 76
    return m


@move('SH06', 'Knuckleball')
def sh06():
    m = kick_base()
    # laces straight through the middle, locked ankle, almost no follow-through (foot stops dead)
    frame(m, 12, R=(1.4, 8.2, 80, 4.4), L=(-3.4, 5.4, -6))
    frame(m, 13, R=(1.3, 12.5, 76, 6.0), L=(-3.4, 5.4, -6), root_y=3.6)
    frame(m, 14, R=(1.4, 15.0, 70, 6.5), L=(-3.4, 5.6, -5), root_y=4.8, pz=24.4)
    frame(m, 15, R=(1.8, 16.5, 50, 5.0), L=(-3.0, 7.0, 20, 5.0), root_y=7.5, pz=24.4)
    frame(m, 16, R=(2.0, 19.0, 20, None), L=(-2.4, 9.5, 20, 6.0), root_y=10.8, pz=23.8)
    m.ball(12, path(10, speed=7.5, rise=0.0, wob=0.55, start=(1.4, 18.0, 3.6)), spin_x=0.2)
    return m


@move('SH07', 'Power Blast')
def sh07():
    m = kick_base()
    # bigger everything: deeper lean, full backswing, leap through the ball
    frame(m, 9, R=(2.4, -8.0, 45, 11.0), root_y=1.2, pz=24.8, cpitch=0.3, pyaw=-0.3)
    frame(m, 10, R=(1.2, -18.0, 56, 21.0), L=(-5.2, 4.6, -6), root_y=1.6, pz=24.0, cpitch=0.42, ppitch=0.2, pyaw=-0.45)
    frame(m, 11, R=(1.8, -1.5, 70, 12.5), root_y=2.0, pz=24.2, cpitch=0.48, pyaw=0.05)
    frame(m, 12, R=(1.0, 8.6, 78, 4.8), L=(-3.4, 5.6, -6), root_y=2.6, pz=24.2, cpitch=0.5, pyaw=0.32)
    frame(m, 13, R=(0.2, 17.5, 70, 12.5), L=(-3.4, 5.6, -4), root_y=4.4, pz=26.0, cpitch=0.4, pyaw=0.5)
    frame(m, 14, R=(0.0, 21.5, 58, 21.0), L=(-3.4, 6.0, 10, 9.5), root_y=7.4, pz=29.0, cpitch=0.28, pyaw=0.4)
    arms_out(m, 10, (-1.0, 0.5, -0.4, 0.3), (1.1, 1.6, 1.5, 1.3)); arms_out(m, 13, (0.3, 0.8, 1.2, 0.5), (0.2, 1.4, 1.0, 1.0))
    m.ball(12, path(10, speed=11.0, rise=0.35, start=(1.5, 20.0, 4.4)), spin_x=3.4)
    m.ms = 70
    return m


@move('SH08', 'Volley')
def sh08():
    m = kick_base()
    # ball drops in from the air; planted leg, chest leaning back, other leg whipped up to meet it, then the hop through
    for f in range(0, 13):
        u = f / 12.0
        m.k(f, bx=1.6, by=30.0 - 19.0 * u, bz=34.0 - 25.0 * u + 4.0 * u * u * 0, bvis=1.0)
    frame(m, 9, R=(2.4, -4.0, 40, 9.5), L=(-4.4, 4.6, -6), root_y=1.5, pz=24.8, cpitch=-0.05, ppitch=-0.02, pyaw=-0.15)
    frame(m, 10, R=(2.8, -7.5, 50, 13.0), L=(-5.0, 4.6, -6), root_y=2.0, pz=24.4, cpitch=-0.14, ppitch=-0.05, pyaw=-0.3, proll=0.1)
    frame(m, 11, R=(2.4, 3.0, 62, 10.5), L=(-5.0, 4.6, -6), root_y=2.2, pz=24.4, cpitch=-0.18, ppitch=-0.08, pyaw=-0.02, proll=0.14)
    frame(m, 12, R=(1.6, 9.6, 74, 8.2), L=(-4.6, 5.0, -6), root_y=2.6, pz=24.4, cpitch=-0.2, ppitch=-0.08, pyaw=0.2, proll=0.16)
    frame(m, 13, R=(0.8, 15.5, 66, 11.5), L=(-4.4, 5.0, -4), root_y=3.8, pz=24.8, cpitch=-0.1, pyaw=0.32, proll=0.1)
    frame(m, 14, R=(0.4, 18.5, 55, 15.0), L=(-3.6, 5.6, 14, 6.0), root_y=6.2, pz=26.0, cpitch=0.05, pyaw=0.3, proll=0.04)
    frame(m, 15, R=(0.6, 19.0, 36, 10.5), L=(-3.0, 6.0, 20, 4.0), root_y=8.8, pz=25.0, cpitch=0.12, pyaw=0.2)
    arms_out(m, 10, (-0.9, 0.5, 0.0, 0.4), (1.0, 1.5, 1.5, 1.2)); arms_out(m, 12, (-0.3, 0.6, 0.4, 0.3), (1.0, 1.4, 1.5, 1.1))
    m.ball(13, path(9, speed=9.5, rise=-0.1, start=(1.6, 14.5, 7.0)), spin_x=2.8)
    return m


@move('SH09', 'Half Volley')
def sh09():
    m = kick_base()
    # ball bounces just before contact; stay low over it, foot arrives right after the bounce
    ball = [(1.6, 24.0, 22.0), (1.6, 21.5, 14.0), (1.6, 19.0, 7.0), (1.6, 16.8, 2.2), (1.6, 14.8, 5.2), (1.6, 13.2, 7.2), (1.6, 12.2, 6.2)]
    for i, p in enumerate(ball): m.k(5 + i, bx=p[0], by=p[1], bz=p[2], bvis=1.0)
    for f in range(0, 5): m.k(f, bx=1.6, by=31.0 - 1.5 * f, bz=30.0 - 2.0 * f, bvis=1.0)
    frame(m, 10, R=(1.8, -9.0, 50, 14.0), L=(-4.6, 5.0, -6), root_y=1.8, pz=23.6, cpitch=0.32, ppitch=0.18, pyaw=-0.3)
    frame(m, 11, R=(2.0, 2.0, 62, 8.6), L=(-4.6, 5.2, -6), root_y=2.2, pz=23.4, cpitch=0.36, pyaw=0.0)
    frame(m, 12, R=(1.4, 9.4, 70, 5.4), L=(-4.2, 5.6, -6), root_y=2.6, pz=23.4, cpitch=0.38, pyaw=0.2)
    m.ball(13, path(9, speed=9.0, rise=0.05, start=(1.5, 15.5, 5.0)), spin_x=2.4)
    return m


def prone(m, f, ry, pz, cp, pp, **kw):
    m.k(f, root_y=ry, pz=pz, cpitch=cp, ppitch=pp, **kw)


@move('SH10', 'Diving Header')
def sh10():
    m = blank(22, 70, ball=(1.2, 24.0, 8.0))
    m = kick_base(); m.N = 22
    for f in range(0, 9): m.k(f, bx=1.6, by=34.0 - 2.4 * f, bz=8.0, bvis=1.0)
    # launch from the run-up, torso goes flat, arms reach, legs trail, head meets a low ball, then belly-landing
    frame(m, 9, R=(2.2, -4.5, 30, 6.0), L=(-3.0, 3.0, 10, 8.0), root_y=2.0, pz=25.0, cpitch=0.35, ppitch=0.3, pyaw=0.0)
    frame(m, 10, R=(1.8, -9.0, 30, 9.0), L=(-2.4, -6.0, 20, 11.0), root_y=4.0, pz=22.0, cpitch=0.8, ppitch=0.7)
    frame(m, 11, R=(1.6, -13.5, 26, 13.0), L=(-2.0, -11.0, 26, 15.5), root_y=7.5, pz=18.5, cpitch=1.2, ppitch=1.0, hpitch=-0.2)
    frame(m, 12, R=(1.6, -17.0, 22, 16.0), L=(-2.0, -14.0, 24, 18.0), root_y=11.0, pz=16.0, cpitch=1.4, ppitch=1.2, hpitch=-0.5)
    frame(m, 13, R=(1.6, -17.5, 20, 15.0), L=(-2.0, -14.5, 24, 16.5), root_y=14.5, pz=14.0, cpitch=1.4, ppitch=1.2, hpitch=-0.2)
    frame(m, 14, R=(1.8, -16.5, 22, 12.0), L=(-2.2, -14.0, 22, 13.0), root_y=18.0, pz=11.0, cpitch=1.45, ppitch=1.3, hpitch=0.2)
    frame(m, 15, R=(2.0, -15.0, 20, 8.0), L=(-2.4, -13.0, 20, 9.0), root_y=21.0, pz=8.5, cpitch=1.5, ppitch=1.4, hpitch=0.4)
    for f in range(16, 22): frame(m, f, R=(2.0, -14.0, 20, 5.0), L=(-2.4, -12.5, 20, 5.5), root_y=23.0 + 0.7 * (f - 16), pz=7.0 - 0.2 * (f - 16), cpitch=1.5, ppitch=1.4, hpitch=0.5)
    for f in range(10, 16): arms_out(m, f, (-1.6, 0.4, -1.6, 0.2), (-1.6, 0.4, -1.6, 0.2))
    m.ball(12, path(9, speed=8.5, rise=0.0, start=(1.5, 24.0, 8.0)), spin_x=1.4)
    m.events = {'strike': 12}
    return m


@move('SH11', 'Glancing Header')
def sh11():
    m = kick_base()
    for f in range(0, 12): m.k(f, bx=14.0 - 1.1 * f, by=14.0 + 0.2 * f, bz=34.0 - 0.25 * f, bvis=1.0)
    # standing leap, head turns into the cross and just flicks it on
    frame(m, 9, R=(2.2, -2.0, 30, 6.0), L=(-2.8, 3.0, 20, 4.0), root_y=2.0, pz=25.5, cpitch=0.0, ppitch=0.0, pyaw=0.0)
    frame(m, 10, R=(2.0, -3.0, 28, 8.0), L=(-2.4, 1.0, 26, 9.0), root_y=2.6, pz=28.5, cpitch=-0.1, proll=0.1)
    frame(m, 11, R=(1.8, -4.0, 26, 9.5), L=(-2.2, 0.0, 28, 10.5), root_y=3.0, pz=30.5, cpitch=-0.15, hyaw=0.5, hroll=0.2, proll=0.12)
    frame(m, 12, R=(1.8, -4.5, 24, 9.5), L=(-2.2, -0.5, 28, 10.5), root_y=3.2, pz=31.0, cpitch=-0.12, hyaw=0.9, hroll=0.3, hpitch=0.1, proll=0.1)
    frame(m, 13, R=(2.0, -3.0, 22, 8.0), L=(-2.4, 0.0, 26, 9.0), root_y=3.6, pz=30.0, cpitch=0.0, hyaw=0.6, proll=0.05)
    frame(m, 14, R=(2.2, -1.0, 18, 5.0), L=(-2.6, 1.5, 22, 5.0), root_y=4.2, pz=27.0, cpitch=0.1, hyaw=0.2)
    frame(m, 15, R=(2.2, 0.5, 4, None), L=(-2.6, 2.0, 4, None), root_y=5.0, pz=23.6, cpitch=0.18, hyaw=0.0)
    for f in range(16, 22): m.keys[f] = run_pose_at(f)
    for f in range(9, 15): arms_out(m, f, (0.3, 0.5, 0.6, 0.4), (0.7, 0.7, 0.8, 0.5))
    m.ball(13, [(-2.0 - 2.6 * i, 14.0 + 0.8 * i, 35.0 - 0.4 * i) for i in range(8)], spin_x=0.4, spin_z=1.6)
    return m


def run_pose_at(f, y0=5.0):
    import gen_actions as A
    k = A.run_pose(A.BASE, (f - 6) / 12.0, y0 + 2.4 * (f - 15))
    k.update(dict(bvis=0.0)); return k


@move('SH12', 'Power Header')
def sh12():
    m = kick_base()
    for f in range(0, 12): m.k(f, bx=2.0, by=16.0 + 0.1 * f, bz=36.0 - 0.9 * f, bvis=1.0)
    frame(m, 9, R=(2.4, -3.0, 36, 6.0), L=(-3.6, 3.4, -6), root_y=2.0, pz=24.4, cpitch=0.2, ppitch=0.1)
    frame(m, 10, R=(2.0, -3.4, 30, 8.5), L=(-3.0, 2.0, 24, 7.5), root_y=3.0, pz=27.4, cpitch=-0.38, ppitch=-0.15, hpitch=-0.35, pyaw=0.0)
    frame(m, 11, R=(1.8, -3.0, 26, 9.5), L=(-2.6, 1.0, 26, 10.0), root_y=3.8, pz=31.0, cpitch=-0.55, ppitch=-0.2, hpitch=-0.5)
    frame(m, 12, R=(1.6, -2.0, 24, 9.0), L=(-2.4, 0.5, 26, 10.0), root_y=4.6, pz=31.5, cpitch=0.5, ppitch=0.15, hpitch=0.4)
    frame(m, 13, R=(1.6, -0.5, 24, 8.0), L=(-2.4, 1.0, 24, 9.0), root_y=5.8, pz=30.0, cpitch=0.7, ppitch=0.2, hpitch=0.5)
    frame(m, 14, R=(1.8, 1.5, 16, 5.0), L=(-2.6, 2.0, 18, 5.5), root_y=7.4, pz=27.0, cpitch=0.5, hpitch=0.3)
    frame(m, 15, R=(2.2, 3.0, 4, None), L=(-2.6, 3.4, 4, None), root_y=9.0, pz=23.4, cpitch=0.3, hpitch=0.2)
    for f in range(16, 22): m.keys[f] = run_pose_at(f, 9.0)
    for f in (10, 11): arms_out(m, f, (-1.0, 0.7, -0.3, 0.4), (-1.0, 0.7, -0.3, 0.4))
    arms_out(m, 12, (0.6, 0.6, 1.2, 0.4), (0.6, 0.6, 1.2, 0.4))
    m.ball(13, path(9, speed=10.0, rise=-0.45, start=(2.0, 22.0, 30.0)), spin_x=1.2)
    return m


@move('SH13', 'Rabona Strike')
def sh13():
    m = kick_base()
    # kicking leg wraps BEHIND the planted leg, body twisted over it
    frame(m, 9, R=(0.6, -3.0, 40, 6.5), L=(-3.6, 3.8, -6), root_y=1.6, pz=24.6, cpitch=0.16, pyaw=-0.2)
    frame(m, 10, R=(-4.8, -3.0, 50, 8.5), L=(-3.8, 5.0, -6), root_y=2.2, pz=24.2, cpitch=0.22, pyaw=-0.5, proll=-0.1)
    frame(m, 11, R=(-5.4, 0.5, 60, 7.0), L=(-3.8, 5.2, -6), root_y=2.4, pz=24.0, cpitch=0.26, pyaw=-0.3, proll=-0.14)
    frame(m, 12, R=(-1.0, 8.4, 74, 4.4), L=(-3.8, 5.4, -6), root_y=2.6, pz=24.0, cpitch=0.3, pyaw=0.1, proll=-0.1)
    frame(m, 13, R=(2.4, 14.0, 66, 8.5), L=(-3.8, 5.4, -4), root_y=3.8, pz=24.2, cpitch=0.26, pyaw=0.4)
    frame(m, 14, R=(3.0, 17.5, 50, 12.0), L=(-3.6, 6.0, 14, 5.0), root_y=6.0, pz=25.0, cpitch=0.2, pyaw=0.5)
    frame(m, 15, R=(2.4, 18.5, 30, 8.0), L=(-3.0, 7.0, 20, 5.0), root_y=8.6, pz=24.4, cpitch=0.16, pyaw=0.3)
    frame(m, 16, R=(2.0, 20.0, 12, None), L=(-2.4, 10.0, 20, 7.0), root_y=11.6, pz=23.8, cpitch=0.16, pyaw=0.1)
    arms_out(m, 10, (0.2, 0.9, 0.8, 0.6), (0.6, 1.3, 1.2, 0.9)); arms_out(m, 12, (0.4, 1.0, 1.0, 0.7), (-0.4, 1.0, 0.4, 0.6))
    m.ball(12, path(10, speed=7.0, rise=0.15, curve=-0.5, start=(1.2, 16.0, 3.6)), spin_x=2.0, spin_z=-1.2)
    return m


@move('SH14', 'Toe Poke')
def sh14():
    m = kick_base()
    # no backswing at all: a short stab with the toe at full stretch
    frame(m, 9, R=(2.2, -0.5, 30, 5.0), L=(-3.6, 3.6, -6), root_y=1.8, pz=24.8, cpitch=0.1, pyaw=0.0)
    frame(m, 10, R=(2.0, 2.5, 50, 4.6), L=(-3.8, 4.8, -6), root_y=2.2, pz=24.6, cpitch=0.16)
    frame(m, 11, R=(1.8, 6.0, 82, 3.6), L=(-3.8, 5.4, -6), root_y=2.4, pz=24.4, cpitch=0.22)
    frame(m, 12, R=(1.6, 10.2, 90, 3.0), L=(-3.8, 5.8, -6), root_y=2.6, pz=24.4, cpitch=0.26, pyaw=0.08)
    frame(m, 13, R=(1.6, 13.5, 70, 4.0), L=(-3.6, 6.2, -6), root_y=4.2, pz=24.4, cpitch=0.2)
    frame(m, 14, R=(1.8, 14.5, 40, 3.0), L=(-3.2, 7.5, 14, 4.0), root_y=7.0, pz=24.2, cpitch=0.16)
    frame(m, 15, R=(2.0, 16.5, 12, None), L=(-2.6, 9.0, 20, 6.0), root_y=9.6, pz=24.0, cpitch=0.14)
    frame(m, 16, R=(2.0, 19.0, 6, None), L=(-2.2, 11.0, 20, 7.0), root_y=12.2, pz=23.6, cpitch=0.14)
    arms_out(m, 11, (0.2, 0.7, 0.8, 0.4), (0.6, 1.0, 1.2, 0.6))
    m.ball(12, path(10, speed=8.0, rise=0.0, start=(1.5, 17.0, 3.0)), spin_x=1.0)
    m.ms = 62
    return m


@move('SH15', 'Outside Flick')
def sh15():
    m = kick_base()
    # a quick, small sweep from inside to outside of the boot, hips already turned away
    frame(m, 10, R=(0.4, -2.0, 40, 5.5, 0.4, 0.2), L=(-4.4, 4.8, -6), root_y=2.0, pz=24.2, cpitch=0.1, pyaw=-0.1, proll=0.06)
    frame(m, 11, R=(1.4, 2.5, 55, 4.2, 0.7, 0.3), L=(-4.4, 5.2, -6), root_y=2.4, pz=24.2, cpitch=0.1, pyaw=0.0)
    frame(m, 12, R=(3.2, 8.6, 70, 3.2, 0.9, 0.3), L=(-4.4, 5.4, -6), root_y=2.8, pz=24.2, cpitch=0.1, pyaw=0.16, proll=0.1)
    frame(m, 13, R=(4.4, 12.5, 58, 5.0, 0.6, 0.2), L=(-4.2, 5.6, -6), root_y=4.0, pz=24.4, cpitch=0.1, pyaw=0.3, proll=0.1)
    frame(m, 14, R=(3.0, 15.0, 36, 6.0, 0.2), L=(-3.6, 6.4, 12, 4.0), root_y=6.4, pz=24.2, cpitch=0.1)
    frame(m, 15, R=(2.2, 17.0, 10, None), L=(-2.8, 9.0, 20, 6.0), root_y=9.4, pz=24.0)
    arms_out(m, 12, (0.1, 0.5, 0.8, 0.3), (0.9, 1.2, 1.3, 0.9))
    m.ball(12, path(10, speed=7.0, rise=0.05, curve=0.55, start=(2.4, 16.0, 3.0)), spin_x=1.4, spin_z=1.6)
    return m


@move('SH16', 'Low Skimmer')
def sh16():
    m = kick_base()
    # whole body sinks low and stays over the ball; strike along the grass with a long, low follow-through
    frame(m, 9, R=(2.4, -6.0, 40, 8.0), L=(-4.6, 4.4, -6), root_y=1.6, pz=21.8, cpitch=0.5, ppitch=0.3, pyaw=-0.2)
    frame(m, 10, R=(1.8, -12.0, 48, 11.0), L=(-5.0, 4.8, -6), root_y=2.0, pz=21.0, cpitch=0.6, ppitch=0.34, pyaw=-0.34)
    frame(m, 11, R=(1.8, 0.0, 66, 6.0), L=(-5.0, 5.0, -6), root_y=2.2, pz=20.8, cpitch=0.62, ppitch=0.36, pyaw=0.0)
    frame(m, 12, R=(1.4, 8.6, 74, 3.4), L=(-4.6, 5.4, -6), root_y=2.6, pz=20.8, cpitch=0.64, ppitch=0.38, pyaw=0.2)
    frame(m, 13, R=(0.8, 15.0, 70, 3.8), L=(-4.4, 5.4, -4), root_y=3.8, pz=21.2, cpitch=0.56, pyaw=0.3)
    frame(m, 14, R=(0.6, 19.0, 56, 5.0), L=(-3.8, 6.0, 10, 3.0), root_y=6.0, pz=22.0, cpitch=0.44, pyaw=0.25)
    frame(m, 15, R=(1.0, 20.5, 36, 5.5), L=(-3.0, 7.0, 20, 4.0), root_y=8.4, pz=23.0, cpitch=0.3)
    arms_out(m, 10, (-0.6, 0.8, 0.0, 0.5), (0.9, 1.3, 1.4, 1.0))
    m.ball(12, path(11, speed=9.5, rise=0.0, start=(1.5, 18.5, 2.6)), spin_x=3.0)
    return m


@move('SH17', 'Far Post Bender')
def sh17():
    m = finesse_base()
    # wider arc: bigger lean, hips opened, foot wraps higher around the ball
    for f in (9, 10, 11, 12, 13): m.keys[f]['pyaw'] = m.keys[f].get('pyaw', 0) - 0.15; m.keys[f]['root_x'] = m.keys[f].get('root_x', 0) - 1.2
    m.k(12, proll=0.16, cyaw=0.1)
    for f in (13, 14, 15): m.keys[f]['R_az'] = m.keys[f].get('R_az', 8.0) + 3.0
    m.ball(12, path(12, speed=7.4, rise=0.2, curve=1.1, start=(2.0, 16.0, 3.6)), spin_x=1.0, spin_z=-2.2)
    return m


@move('SH18', 'Near Post Lash')
def sh18():
    m = kick_base()
    # body angled, hard sweep ACROSS the line toward the near post
    frame(m, 10, R=(2.4, -12.0, 52, 15.0), L=(-5.2, 4.6, -6), root_y=2.0, pz=24.2, cpitch=0.3, pyaw=-0.5)
    frame(m, 11, R=(1.6, -0.5, 64, 10.0), L=(-5.2, 4.8, -6), root_y=2.2, pz=24.2, cpitch=0.32, pyaw=-0.1)
    frame(m, 12, R=(0.0, 7.8, 74, 4.2), L=(-4.8, 5.4, -6), root_y=2.6, pz=24.2, cpitch=0.34, pyaw=0.3)
    frame(m, 13, R=(-3.6, 13.5, 66, 8.0), L=(-4.6, 5.4, -4), root_y=3.8, pz=24.6, cpitch=0.3, pyaw=0.6)
    frame(m, 14, R=(-6.4, 16.0, 52, 12.5), L=(-4.0, 6.0, 12, 6.0), root_y=6.0, pz=25.6, cpitch=0.24, pyaw=0.7)
    frame(m, 15, R=(-5.0, 17.5, 34, 9.0), L=(-3.0, 7.0, 20, 5.0), root_y=8.6, pz=24.8, cpitch=0.2, pyaw=0.5)
    m.ball(12, path(10, speed=9.0, rise=0.1, curve=-0.9, start=(0.4, 18.0, 3.6)), spin_x=2.6)
    return m


@move('SH19', 'Dipping Drive')
def sh19():
    m = kick_base()
    # strike over the top of the ball: toe points down, leg keeps going over it
    frame(m, 12, R=(1.2, 8.4, 82, 5.2), L=(-3.6, 5.4, -6), cpitch=0.46, ppitch=0.24)
    frame(m, 13, R=(0.6, 15.5, 80, 9.0), cpitch=0.4)
    frame(m, 14, R=(0.4, 20.0, 78, 15.0), L=(-3.6, 5.6, 8, 7.0), pz=26.6, cpitch=0.3)
    frame(m, 15, R=(0.4, 21.0, 66, 14.0), L=(-3.0, 4.0, 10, 9.0))
    m.ball(12, path(12, speed=8.6, rise=0.9, dip=1.5, start=(1.5, 18.5, 4.4)), spin_x=3.4)
    return m


@move('SH20', 'Rising Drive')
def sh20():
    m = kick_base()
    # scooped through the bottom of the ball, chest a touch back, big lifted follow-through
    frame(m, 12, R=(1.2, 8.2, 66, 3.2), L=(-3.6, 5.4, -6), cpitch=0.24, ppitch=0.06)
    frame(m, 13, R=(0.8, 15.5, 48, 11.0), cpitch=0.16)
    frame(m, 14, R=(0.6, 19.5, 22, 21.0), L=(-3.6, 5.6, 10, 8.0), pz=26.0, cpitch=0.08)
    frame(m, 15, R=(0.6, 20.0, 8, 22.0), L=(-3.0, 4.5, 10, 8.0), cpitch=0.06)
    m.ball(12, path(12, speed=9.0, rise=0.25, dip=-0.4, start=(1.5, 18.5, 3.6)), spin_x=-2.4)
    return m


@move('SH21', 'Lofted Finesse')
def sh21():
    m = finesse_base()
    # lazy arc, softer swing, arms wide and eyes up, ball floated high into the corner
    for f in (11, 12, 13): m.keys[f]['R_az'] = m.keys[f].get('R_az', 5) + 1.5
    m.k(12, hpitch=0.1, cpitch=-0.28)
    m.ball(12, path(12, speed=6.0, rise=1.3, curve=0.9, dip=1.0, start=(2.0, 15.0, 4.6)), spin_x=-1.6, spin_z=-1.6)
    m.ms = 78
    return m


@move('SH22', 'Rocket Long Shot')
def sh22():
    m = kick_base()
    # biggest windup of all: head down, arms thrown wide, leaps off the planted foot
    frame(m, 8, R=(2.0, -3.0, 40, 6.5), L=(-2.4, 1.0, 5, 11.0), root_y=0.5, pz=25.4)
    frame(m, 9, R=(1.8, -10.0, 50, 14.0), L=(-4.8, 3.6, -6), root_y=1.2, pz=24.6, cpitch=0.28, pyaw=-0.4)
    frame(m, 10, R=(0.8, -22.0, 60, 24.0), L=(-5.4, 4.8, -6), root_y=1.6, pz=23.8, cpitch=0.45, ppitch=0.24, pyaw=-0.6)
    frame(m, 11, R=(1.6, -4.0, 70, 15.0), L=(-5.4, 5.0, -6), root_y=2.0, pz=24.0, cpitch=0.5, pyaw=0.0)
    frame(m, 12, R=(1.0, 9.0, 80, 5.0), L=(-3.6, 5.6, -6), root_y=2.6, pz=24.4, cpitch=0.52, pyaw=0.4)
    frame(m, 13, R=(0.0, 19.0, 70, 14.5), L=(-3.4, 5.6, -4), root_y=4.4, pz=26.6, cpitch=0.4, pyaw=0.6)
    frame(m, 14, R=(-0.4, 23.5, 56, 24.0), L=(-3.4, 6.0, 12, 10.0), root_y=7.4, pz=30.0, cpitch=0.28, pyaw=0.45)
    frame(m, 15, R=(-0.2, 22.0, 40, 22.0), L=(-3.0, 4.5, 20, 12.0), root_y=10.0, pz=28.0, cpitch=0.2, pyaw=0.25)
    arms_out(m, 10, (-1.2, 0.4, -0.6, 0.3), (1.3, 1.8, 1.5, 1.5)); arms_out(m, 13, (0.4, 0.8, 1.4, 0.5), (0.4, 1.5, 1.0, 1.1))
    m.ball(12, path(10, speed=12.5, rise=0.3, start=(1.5, 21.0, 4.4)), spin_x=3.6)
    m.ms = 66
    return m


@move('SH23', 'Snap Shot')
def sh23():
    m = blank(16, 56, ball=(1.4, 8.0, 3.0), events={'strike': 6})
    # from standing: a tiny hitch of the hips, the leg flicks through, the body barely moves
    frame(m, 0, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0))
    frame(m, 2, R=(2.4, -3.5, 36, 6.0), L=(-3.6, 3.0, -6), root_y=0.4, pz=24.2, cpitch=0.14, pyaw=-0.2)
    frame(m, 4, R=(2.0, 1.5, 62, 6.0), L=(-3.8, 3.6, -6), root_y=0.8, pz=24.0, cpitch=0.24, pyaw=0.0)
    frame(m, 6, R=(1.6, 6.8, 76, 3.6), L=(-3.8, 4.0, -6), root_y=1.2, pz=24.0, cpitch=0.28, pyaw=0.2)
    frame(m, 8, R=(1.4, 11.0, 62, 6.0), L=(-3.6, 4.2, -6), root_y=2.0, pz=24.2, cpitch=0.24, pyaw=0.26)
    frame(m, 10, R=(1.6, 12.0, 30, 4.0), L=(-3.0, 5.0, 12, 4.0), root_y=3.4, pz=24.2, cpitch=0.18, pyaw=0.12)
    frame(m, 13, R=(2.0, 8.0, 5, None), L=(-2.6, 5.0, 8, None), root_y=4.2, pz=24.6, cpitch=0.12, pyaw=0.0)
    frame(m, 15, R=(2.2, 6.0, 0, None), L=(-2.2, 5.0, 0, None), root_y=4.2, pz=24.6, cpitch=0.1)
    arms_out(m, 4, (-0.2, 0.6, 0.4, 0.3), (0.7, 1.1, 1.3, 0.8)); arms_out(m, 6, (0.0, 0.6, 0.6, 0.3), (0.8, 1.1, 1.3, 0.8))
    m.ball(6, path(9, speed=8.0, start=(1.5, 12.0, 3.2)), spin_x=2.0)
    for f in range(0, 6): m.k(f, bx=1.4, by=8.0, bz=3.0, bvis=1.0)
    return m


@move('SH24', 'One Touch Finish')
def sh24():
    m = kick_base()
    # ball arrives along the ground from the side; no backswing, the boot just meets it and redirects
    for f in range(0, 12): m.k(f, bx=18.0 - 1.35 * f, by=12.0, bz=3.0, brx=-2.0 * f, bvis=1.0)
    frame(m, 9, R=(2.2, 0.0, 30, 4.0), L=(-3.8, 4.0, -6), root_y=2.0, pz=24.6, cpitch=0.14, pyaw=-0.15, proll=0.06)
    frame(m, 10, R=(2.8, 4.5, 50, 3.6, -0.8, 0.1), L=(-4.0, 5.0, -6), root_y=2.4, pz=24.4, cpitch=0.16, pyaw=0.0)
    frame(m, 11, R=(2.4, 8.0, 60, 3.0, -1.1, 0.1), L=(-4.0, 5.4, -6), root_y=2.6, pz=24.4, cpitch=0.18, pyaw=0.12)
    frame(m, 12, R=(1.8, 11.0, 62, 2.9, -1.1, 0.1), L=(-4.0, 5.8, -6), root_y=2.9, pz=24.4, cpitch=0.2, pyaw=0.2)
    frame(m, 13, R=(1.2, 14.0, 50, 4.5, -0.6), L=(-3.8, 6.0, -6), root_y=4.2, pz=24.4, cpitch=0.16, pyaw=0.26)
    frame(m, 14, R=(1.0, 16.0, 30, 5.5), L=(-3.2, 7.0, 14, 4.0), root_y=7.0, pz=24.2, cpitch=0.14)
    frame(m, 15, R=(1.8, 17.5, 10, None), L=(-2.6, 9.0, 20, 6.0), root_y=9.6, pz=24.0)
    m.ball(12, path(10, speed=8.0, rise=0.0, curve=-0.5, start=(5.5, 15.0, 3.0)), spin_x=2.0)
    return m


@move('SH25', 'Cut Inside Shot')
def sh25():
    m = kick_base()
    # drops the shoulder and drags the ball inside on the left foot, then swings the right through it
    for f in (4, 5, 6, 7, 8, 9): m.k(f, root_x=-0.9 * (f - 3), proll=-0.14, croll=-0.1, cpitch=0.2)
    frame(m, 8, L=(-5.0, 1.5, -6), R=(2.0, -2.0, 36, 6.0), root_y=0.5, pz=24.2, pyaw=-0.2)
    frame(m, 9, L=(-6.4, 3.6, -6), R=(1.2, -4.0, 40, 8.5), root_y=1.5, pz=24.0, root_x=-5.6, proll=-0.1, pyaw=-0.3, cpitch=0.2)
    frame(m, 10, L=(-7.0, 4.6, -6), R=(1.0, -9.0, 48, 12.0), root_y=2.0, pz=24.0, root_x=-5.6, proll=-0.06, pyaw=-0.42, cpitch=0.3)
    frame(m, 11, L=(-7.0, 5.0, -6), R=(0.8, 0.0, 64, 8.5), root_y=2.2, root_x=-5.4, pz=24.0, pyaw=-0.1, cpitch=0.34, proll=0.0)
    frame(m, 12, L=(-6.0, 5.4, -6), R=(0.6, 8.0, 74, 4.4), root_y=2.6, root_x=-5.0, pz=24.0, pyaw=0.3, cpitch=0.36)
    for f in (13, 14, 15, 16): m.k(f, root_x=-5.0 + 0.9 * (f - 12))
    m.ball(12, path(10, speed=8.4, rise=0.1, curve=0.3, start=(-3.4, 18.0, 3.8)), spin_x=2.2)
    for f in range(0, 12): m.k(f, bx=1.2 - 0.5 * f if f < 9 else -3.4, by=11.5, bz=3.0, bvis=1.0)
    return m


@move('SH26', 'Shot Fake')
def sh26():
    m = kick_base(); m.N = 26
    # winds up for a shot, stops the foot dead over the ball, rocks back, then really hits it
    for f in range(0, 18): m.k(f, bx=1.2, by=11.5, bz=3.0, bvis=1.0)
    for f in range(18, 26): m.keys[f] = {}
    frame(m, 10, R=(1.6, -14.0, 52, 17.0), L=(-5.0, 4.6, -6), root_y=2.0, pz=24.2, cpitch=0.3, pyaw=-0.3)
    frame(m, 11, R=(1.8, 1.0, 62, 10.0), L=(-5.0, 4.8, -6), root_y=2.2, pz=24.2, cpitch=0.34, pyaw=0.0)
    frame(m, 12, R=(1.8, 4.5, 64, 7.5), L=(-5.0, 4.8, -6), root_y=2.2, pz=24.0, cpitch=0.36, pyaw=0.1)          # stops short of the ball
    frame(m, 13, R=(2.0, 1.0, 50, 6.0), L=(-4.4, 4.0, -6), root_y=1.0, pz=24.4, cpitch=0.2, pyaw=-0.2, proll=0.08)
    frame(m, 14, R=(2.2, -4.0, 40, 6.0), L=(-3.6, 2.0, -6), root_y=0.0, pz=24.8, cpitch=0.1, pyaw=-0.35, proll=-0.1)   # sway back
    frame(m, 15, R=(2.2, -7.0, 44, 8.0), L=(-4.6, 4.0, -6), root_y=1.0, pz=24.4, cpitch=0.2, pyaw=-0.3)
    frame(m, 16, R=(1.6, -11.0, 54, 13.0), L=(-5.0, 4.8, -6), root_y=1.8, pz=24.2, cpitch=0.3, pyaw=-0.36)
    frame(m, 17, R=(1.8, 1.0, 68, 9.0), L=(-5.0, 5.0, -6), root_y=2.2, pz=24.2, cpitch=0.36, pyaw=0.05)
    frame(m, 18, R=(1.2, 8.2, 74, 4.6), L=(-3.6, 5.2, -6), root_y=2.6, pz=24.0, cpitch=0.4, pyaw=0.22)
    frame(m, 19, R=(0.4, 16.0, 66, 11.0), L=(-3.6, 5.2, -4), root_y=3.8, pz=24.4, cpitch=0.34, pyaw=0.38)
    frame(m, 20, R=(0.2, 20.0, 55, 19.0), L=(-3.6, 5.5, 8, 8.0), root_y=6.5, pz=27.0, cpitch=0.22, pyaw=0.25)
    frame(m, 21, R=(0.0, 20.5, 40, 17.0), L=(-3.0, 3.5, 25, 10.0), root_y=8.5, pz=24.8, cpitch=0.16)
    frame(m, 22, R=(0.8, 22.0, 20, 12.0), L=(-2.5, 4.0, 25, 9.0), root_y=11.5, pz=24.5)
    frame(m, 23, R=(1.8, 21.0, -10, None), L=(-2.0, 6.5, 28, 8.5), root_y=14.8, pz=22.6)
    for f in (24, 25): m.keys[f] = run_pose_at(f + 0, 14.8)
    m.keys[25].update(m.keys[25])
    m.ball(18, path(8, speed=9.0, rise=0.2, start=(1.5, 18.5, 4.0)), spin_x=2.4)
    m.events = {'fake': 12, 'strike': 18}
    return m


@move('SH27', 'Cross Shot')
def sh27():
    m = kick_base()
    frame(m, 10, R=(2.0, -12.0, 52, 15.0), L=(-5.2, 4.6, -6), root_y=2.0, pz=24.2, cpitch=0.32, pyaw=-0.45)
    frame(m, 11, R=(1.6, -0.5, 64, 10.0), L=(-5.2, 4.8, -6), root_y=2.2, pz=24.2, cpitch=0.34, pyaw=-0.1)
    frame(m, 12, R=(0.6, 7.8, 74, 4.2), L=(-4.8, 5.4, -6), root_y=2.6, pz=24.2, cpitch=0.38, pyaw=0.26)
    frame(m, 13, R=(-1.8, 14.0, 66, 8.0), L=(-4.6, 5.4, -4), root_y=3.8, pz=24.4, cpitch=0.32, pyaw=0.5)
    frame(m, 14, R=(-3.6, 17.0, 50, 11.0), L=(-3.8, 6.0, 12, 6.0), root_y=6.0, pz=25.2, cpitch=0.26, pyaw=0.55)
    frame(m, 15, R=(-3.0, 18.0, 34, 8.0), L=(-3.0, 7.0, 20, 5.0), root_y=8.6, pz=24.6)
    m.ball(12, path(10, speed=9.4, rise=0.0, curve=-0.55, start=(0.8, 18.5, 3.0)), spin_x=2.6)
    return m


@move('SH28', 'Composure Finish')
def sh28():
    m = kick_base()
    # unhurried: eyes down on the ball, long pause over it, a short controlled pass of the boot, head stays still
    for f in range(8, 14): m.k(f, hpitch=0.75)
    frame(m, 9, R=(2.4, -2.5, 38, 6.0), L=(-3.8, 3.8, -6), root_y=1.6, pz=24.2, cpitch=0.16, pyaw=-0.1)
    frame(m, 10, R=(2.6, -4.5, 42, 7.5), L=(-4.4, 5.0, -6), root_y=2.0, pz=23.8, cpitch=0.2, pyaw=-0.14)
    frame(m, 11, R=(2.8, 1.5, 50, 5.6, -1.1, 0.1), L=(-4.6, 5.6, -6), root_y=2.2, pz=23.8, cpitch=0.22, pyaw=0.0)
    frame(m, 12, R=(2.2, 8.0, 54, 3.4, -1.3, 0.1), L=(-4.4, 6.0, -6), root_y=2.4, pz=23.8, cpitch=0.22, pyaw=0.1)
    frame(m, 13, R=(1.6, 12.0, 48, 4.4, -1.0), L=(-4.2, 6.2, -6), root_y=3.0, pz=24.0, cpitch=0.2, pyaw=0.14)
    frame(m, 14, R=(1.2, 14.5, 36, 4.8), L=(-3.8, 6.4, -6), root_y=4.4, pz=24.2, cpitch=0.16, hpitch=0.5)
    frame(m, 15, R=(1.6, 16.0, 20, 3.0), L=(-3.2, 7.4, 10, 3.5), root_y=7.0, pz=24.4, cpitch=0.1, hpitch=0.25)
    frame(m, 16, R=(2.0, 18.0, 8, None), L=(-2.6, 9.2, 20, 5.0), root_y=10.0, pz=24.0, hpitch=0.2)
    arms_out(m, 11, (0.0, 0.3, 0.4, 0.2), (0.3, 0.5, 0.6, 0.3)); arms_out(m, 12, (0.0, 0.3, 0.4, 0.2), (0.3, 0.5, 0.6, 0.3))
    m.ball(12, path(10, speed=5.8, rise=0.0, start=(1.4, 15.0, 3.0)), spin_x=1.6)
    m.ms = 85
    return m


@move('SH29', 'Lob Volley')
def sh29():
    m = sh08()
    # same dropping ball, but the foot scoops under it in the air and the ball floats high over the keeper
    frame(m, 11, R=(2.2, 3.0, 40, 9.0)); frame(m, 12, R=(1.6, 9.0, 30, 6.2), cpitch=-0.28)
    frame(m, 13, R=(1.2, 14.0, 8, 11.5), cpitch=-0.22); frame(m, 14, R=(1.0, 17.0, -4, 16.0))
    m.ball(13, path(9, speed=5.0, rise=1.8, dip=1.2, start=(1.6, 13.5, 8.5)), spin_x=-2.0)
    return m


@move('SH30', 'Backheel Shot')
def sh30():
    m = kick_base()
    # ball rolls past the planted foot, the heel flicks it backwards with the toe pulled up
    for f in range(0, 12): m.k(f, bx=1.8, by=14.0 - 0.9 * f, bz=3.0, brx=-1.5 * f, bvis=1.0)
    frame(m, 9, R=(2.2, 1.0, 20, 4.0), L=(-3.6, 6.0, -6), root_y=2.0, pz=24.8, cpitch=0.14, pyaw=0.2)
    frame(m, 10, R=(2.6, 5.0, 10, 4.2), L=(-4.0, 8.0, -6), root_y=3.5, pz=24.6, cpitch=0.16, pyaw=0.4)
    frame(m, 11, R=(1.8, 4.0, -30, 4.0), L=(-4.0, 8.6, -6), root_y=5.0, pz=24.4, cpitch=0.2, pyaw=0.6)
    frame(m, 12, R=(1.4, 1.0, -55, 3.6), L=(-4.0, 9.0, -6), root_y=5.8, pz=24.4, cpitch=0.2, pyaw=0.7, hyaw=0.3)
    frame(m, 13, R=(1.4, -3.5, -50, 5.5), L=(-3.8, 9.4, -6), root_y=6.4, pz=24.4, cpitch=0.16, pyaw=0.5)
    frame(m, 14, R=(1.8, -6.0, -20, 8.5), L=(-3.4, 9.6, -4), root_y=7.4, pz=24.6, cpitch=0.1, pyaw=0.3)
    frame(m, 15, R=(2.0, -2.0, 10, 6.0), L=(-3.0, 10.0, 10, 4.0), root_y=9.0, pz=24.4, cpitch=0.1)
    frame(m, 16, R=(2.2, 2.0, 5, None), L=(-2.6, 11.0, 15, 5.0), root_y=11.0, pz=24.0, cpitch=0.1)
    arms_out(m, 11, (0.5, 0.6, 0.9, 0.4), (0.8, 1.2, 1.4, 0.8))
    m.ball(12, [(1.8, 5.0 - 3.0 * i, 3.0 + 0.4 * i if i < 3 else 3.6) for i in range(8)], spin_x=-2.4)
    m.ms = 66
    return m


def build(ids=None):
    out = []
    for id_, (label, fn) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); name = id_.lower() + '_' + label.lower().replace(' ', '_')
        m.save(name, label, 'auto-generated by sprites/moves_shot.py'); out.append((id_, name))
    return out


if __name__ == '__main__':
    for id_, name in build(sys.argv[1:] or None): print(id_, name)
