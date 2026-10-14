"""The 25 PASS skill animations (PS01-PS25). Run:  python moves_pass.py [id ...]  to (re)write data/animations/psXX_*.json"""
import math, sys
import numpy as np
import moves as M
from moves import path, kick_base, finesse_base, blank, stand
import moves_shot as S
from moves_shot import frame, arms_out, fly, shift_x, celebrate, run_pose_at, snap_ball

MOVES = {}


def move(id_, label):
    def deco(fn):
        MOVES[id_] = (label, fn); return fn
    return deco


def look(m, f0, f1, hyaw=0.0, hpitch=0.0, hroll=0.0):
    for f in range(f0, f1 + 1): m.k(f, hyaw=hyaw, hpitch=hpitch, hroll=hroll)


def point(m, f0, f1, side='L'):
    for f in range(f0, f1 + 1): m.arms(f, side, 1.55, 0.15, 1.55, 0.1)


def hands_on_hips(m, f0, f1):
    for f in range(f0, f1 + 1): m.arms(f, 'R', 0.5, 0.75, 1.5, 0.2); m.arms(f, 'L', 0.5, 0.75, 1.5, 0.2)


def raise_arm(m, f0, f1, side='R'):
    for f in range(f0, f1 + 1): m.arms(f, side, 2.6, 0.25, 2.9, 0.15)


def fix_contact(m, fc=12, off=(0, 1.6, 0.6), vin=(0, 0, 0), pre=None):
    return M.aim_ball(m, fc, 'boot', 'R', vin=vin, pre=fc if pre is None else pre, off=off)


def rest(m, c, f0, f1):
    for f in range(f0, f1): m.k(f, bx=c[0], by=c[1], bz=c[2], bvis=1.0, brx=0.0, brz=0.0)


def jog(m, f, root_y):
    k = run_pose_at(f, root_y, step=0); return k


@move('PS01', 'Through Ball')
def ps01():
    m = S.sh01(); look(m, 0, 10, 0.0, -0.3)
    # eyes up on the runner, the ball is slid in with the inside of the boot, then the free arm points the way
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (0.7, 5.2, 0.0), 10, g=0.0), spin_x=1.6)
    point(m, 13, m.N - 1, 'L'); look(m, 11, 13, 0.0, -0.1); look(m, 14, m.N - 1, 0.0, -0.3)
    m.ms = 72
    return m


@move('PS02', 'Lofted Through')
def ps02():
    m = S.sh20(); look(m, 0, 11, 0.0, -0.25)
    # the boot gets under the ball and the whole body tips back, eyes tracking the high ball
    for f in (13, 14, 15): m.k(f, hpitch=-0.5, cpitch=-0.2)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (0.4, 4.5, 2.1), 12, g=0.2), spin_x=-2.2)
    celebrate(m, 17, m.N, 'wide')
    return m


@move('PS03', 'Driven Pass')
def ps03():
    m = S.sh02(); S.sprint(m)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (0.0, 10.0, 0.0), 10, g=0.0), spin_x=3.4)
    return m


@move('PS04', 'One Two')
def ps04():
    m = S.sh01(); m.N = 28
    for f in range(22, 28): m.keys[f] = {}
    # pass, then straight into a sprint out to the right; the return arrives at the runner's feet
    for f in range(13, 28):
        m.keys[f] = run_pose_at(f, 6.0 + 3.0 * (f - 13), step=0) if False else m.keys.get(f, {})
    for f in range(13, 28):
        ry = 6.0 + 2.9 * (f - 13)
        k = run_pose_at(f, ry, step=0); k['root_y'] = ry
        for s in 'RL': k[s + '_ay'] += ry - 0.0 if False else 0.0
        m.keys[f] = k
    for f in range(13, 28):
        k = run_pose_at(f, 6.0 + 2.9 * (f - 13), step=0)
        ry = 6.0 + 2.9 * (f - 13)
        # recompute properly with the sprint's own travel
        import gen_actions as A
        k = A.run_pose(A.BASE, (f - 6) / 12.0, ry)
        k.update(cpitch=k['cpitch'] + 0.14, hpitch=-0.2)
        m.keys[f] = k
    shift_x(m, 13, 27, 0.0, 6.0)
    c = fix_contact(m); rest(m, c, 0, 12)
    out = [(c[0] + 0.5 * i, c[1] + 4.6 * i, 3.0) for i in range(1, 6)]
    m.ball(13, out, spin_x=1.6)
    for f in range(18, 24): m.k(f, bx=c[0] + 2.5 - 0.35 * (f - 18) * 0, by=out[-1][1] - 2.4 * (f - 17) - 0.0, bz=3.0, bvis=1.0)
    for f in range(24, 28):
        ry = 6.0 + 2.9 * (f - 13); m.k(f, bx=5.0 + m.keys[f]['root_x'] * 0, by=ry + 8.0 + 1.2 * abs(math.sin(f * 0.8)), bz=3.0, bvis=1.0)
    point(m, 13, 16, 'L'); m.events = {'strike': 12, 'dart': 14}
    return m


@move('PS05', 'Backheel Pass')
def ps05():
    m = S.sh30()
    c = np.array([m.keys[12]['bx'], m.keys[12]['by'], m.keys[12]['bz']])
    m.ball(13, [(1.8, 4.6 - 2.6 * i, 3.0) for i in range(9)], spin_x=-1.6)
    look(m, 0, 12, 0.0, -0.25)
    return m


@move('PS06', 'No Look Pass')
def ps06():
    m = S.sh01(); look(m, 0, m.N - 1, 1.1, -0.1, 0.1)
    # head and shoulders turned hard to the right while the boot sends it left
    for f in range(9, 15): m.k(f, pyaw=m.keys[f].get('pyaw', 0.0) - 0.35, cyaw=0.5)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (-2.6, 4.6, 0.0), 10, g=0.0), spin_x=1.6, spin_z=-0.6)
    return m


@move('PS07', 'Cross')
def ps07():
    m = S.sh05(); S.shift_x(m, 0, 11, 9.0, 0.0)
    # down the wing, head up to find the box, the ball is whipped in high with a long follow-through
    look(m, 0, 11, -0.2, -0.3)
    for f in (13, 14, 15): m.k(f, hpitch=-0.35)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (-1.9, 4.8, 1.8), 13, g=0.2), spin_x=-1.8, spin_z=-1.2)
    return m


@move('PS08', 'Driven Cross')
def ps08():
    m = S.sh02(); S.shift_x(m, 0, 11, 9.0, 0.0); S.sprint(m)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (-3.0, 8.4, 0.1), 10, g=0.0), spin_x=3.0)
    return m


@move('PS09', 'Cutback')
def ps09():
    m = kick_base(); m.N = 24
    for f in range(8, 24): m.keys[f] = {}
    BX, BY = 1.6, 11.0
    for f in range(0, 24): m.k(f, bx=BX, by=BY, bz=3.0, bvis=1.0)
    # to the byline, the sole drags the ball back across, then it is rolled square to the runner
    frame(m, 8, R=(2.2, -1.0, 40, 5.0), L=(-3.0, 5.0, -6), root_y=0.4, pz=24.6, cpitch=0.2)
    frame(m, 9, R=(1.8, 6.0, -20, 5.0), L=(-3.8, 5.6, -6), root_y=1.4, pz=24.2, cpitch=0.3, pyaw=0.1)
    frame(m, 10, R=(1.6, 11.0, -50, 4.2), L=(-4.2, 6.2, -6), root_y=2.2, pz=23.6, cpitch=0.36, pyaw=0.3, proll=-0.1)         # sole on the ball
    frame(m, 11, R=(0.4, 8.0, -50, 4.0), L=(-4.4, 6.4, -6), root_y=2.4, pz=23.4, cpitch=0.38, pyaw=0.5, proll=-0.12)        # drags it back
    frame(m, 12, R=(-1.8, 4.0, -10, 3.0), L=(-4.4, 6.4, -6), root_y=2.4, pz=23.4, cpitch=0.36, pyaw=0.6)
    frame(m, 13, R=(-2.6, 4.4, 40, 3.4, -1.1, 0.0), L=(-4.4, 6.4, -6), root_y=2.4, pz=23.6, cpitch=0.3, pyaw=0.2)
    frame(m, 14, R=(-1.4, 7.0, 50, 3.2, -1.2, 0.1), L=(-4.4, 6.4, -6), root_y=2.6, pz=23.8, cpitch=0.26, pyaw=-0.1)        # side-foot roll
    frame(m, 15, R=(0.0, 9.0, 40, 4.0), L=(-3.8, 6.4, -4), root_y=3.4, pz=24.0, cpitch=0.2, pyaw=-0.2)
    frame(m, 16, R=(1.6, 10.0, 20, 4.0), L=(-3.2, 7.0, 12, 4.0), root_y=5.0, pz=24.4, cpitch=0.14)
    for f in range(17, 24): m.keys[f] = run_pose_at(f, 6.5, step=1.8)
    arms_out(m, 10, (0.2, 0.9, 0.6, 0.6), (0.6, 1.0, 1.0, 0.8)); arms_out(m, 14, (0.2, 0.7, 0.6, 0.4), (0.9, 1.2, 1.5, 0.9))
    for f in range(0, 11): m.k(f, bx=BX, by=BY)
    c0 = (BX, BY, 3.0)
    ball = [(1.6, 9.0, 3.0), (1.0, 6.0, 3.0), (0.2, 4.2, 3.0), (-0.8, 4.4, 3.0)]
    for i, p in enumerate(ball): m.k(11 + i, bx=p[0], by=p[1], bz=p[2])
    m.ball(15, [(-2.4 - 2.8 * i, 4.6 - 0.4 * i, 3.0) for i in range(9)], spin_x=1.6)
    m.events = {'strike': 14}
    return m


@move('PS10', 'Switch Play')
def ps10():
    m = S.sh22(); look(m, 0, 11, 0.0, -0.25)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (-2.4, 5.6, 2.6), 14, g=0.22), spin_x=-1.4, spin_z=-0.8)
    for f in (13, 14, 15): m.k(f, hpitch=-0.4)
    return m


@move('PS11', 'Rabona Cross')
def ps11():
    m = S.sh13()
    c = M.aim_ball(m, 12, 'boot', 'R', vin=(0.0, -0.3, 0.0), pre=12)
    m.ball(13, fly(c, (1.5, 5.6, 2.0), 13, g=0.2), spin_x=-1.6, spin_z=1.0)
    look(m, 0, 11, 0.0, 0.3); look(m, 13, 16, 0.2, -0.3)
    return m


@move('PS12', 'Outside Foot Pass')
def ps12():
    m = S.sh04()
    for f in range(9, 16): m.keys[f]['croll'] = m.keys[f].get('croll', 0) * 0.5
    c = M.aim_ball(m, 12, 'boot', 'R', vin=(0, 0, 0), pre=0, off=(0, 0.6, 0.4)); rest(m, c, 0, 12)
    m.ball(13, path(11, speed=5.2, rise=0.0, curve=-0.9, start=(c[0], c[1] + 3, 3.0)), spin_x=1.2, spin_z=1.4)
    return m


@move('PS13', 'Chipped Pass')
def ps13():
    m = S.sh05(); look(m, 0, 11, 0.0, -0.2)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (0.5, 3.4, 2.4), 12, g=0.28), spin_x=-2.4)
    return m


@move('PS14', 'Pass and Move')
def ps14():
    m = S.sh01(); m.N = 26
    for f in range(17, 26): m.keys[f] = {}
    for f in range(13, 26):
        import gen_actions as A
        ry = 6.0 + 3.0 * (f - 13)
        k = A.run_pose(A.BASE, (f - 6) / 12.0, ry); k.update(cpitch=k['cpitch'] + 0.14, hpitch=-0.15, bvis=1.0)
        m.keys[f] = k
    shift_x(m, 13, 25, 0.0, -7.0)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (0.7, 4.6, 0.0), 13, g=0.0), spin_x=1.6)
    point(m, 13, 15, 'L'); m.events = {'strike': 12, 'dart': 14}
    return m


@move('PS15', 'Killer Ball')
def ps15():
    m = S.sh02(); m.N = 28
    for f in range(16, 28): m.keys[f] = {}
    for f in range(0, 8):
        k = m.keys[f]; k['hyaw'] = 0.7 * math.sin(f * 0.9); k['hpitch'] = -0.25
    frame(m, 12, R=(1.4, 9.0, 74, 3.4), L=(-3.6, 5.4, -6))
    for f in range(16, 28):
        m.keys[f] = run_pose_at(f, 12.2, step=0)
    # threads it, then spreads both arms: "that's the one"
    for f in range(13, 28): m.arms(f, 'R', 1.5, 1.25, 1.6, 1.2); m.arms(f, 'L', 1.5, 1.25, 1.6, 1.2)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (0.0, 9.0, 0.0), 12, g=0.0), spin_x=3.0)
    return m


@move('PS16', 'Square Ball')
def ps16():
    m = S.sh01()
    for f in range(9, 15): m.k(f, pyaw=m.keys[f].get('pyaw', 0.0) - 0.35)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (-3.8, 0.8, 0.0), 10, g=0.0), spin_x=0.4, spin_z=-1.4)
    look(m, 9, 14, 0.2, 0.3)
    m.ms = 78
    return m


@move('PS17', 'Return Pass')
def ps17():
    m = blank(18, 62, ball=(1.4, 22.0, 3.0), events={'strike': 7})
    # the ball comes in, one touch, straight back: a small hop onto the standing foot and the boot just turns it round
    for f in range(0, 18): m.k(f, bvis=1.0)
    frame(m, 0, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0), hpitch=0.3, cpitch=0.1)
    frame(m, 3, R=(2.4, 0.5, 10, 3.0), L=(-2.6, 0.8, -4), root_y=0.2, pz=24.4, hpitch=0.4, cpitch=0.16)
    frame(m, 5, R=(2.6, 2.0, 40, 4.0, -0.6, 0.1), L=(-3.0, 1.6, 6, 3.0), root_y=0.4, pz=25.2, hpitch=0.5, cpitch=0.2)    # hop
    frame(m, 6, R=(2.6, 4.5, 50, 3.6, -1.1, 0.1), L=(-3.4, 2.8, -6), root_y=0.6, pz=24.2, hpitch=0.5, cpitch=0.22)
    frame(m, 7, R=(2.4, 6.0, 52, 3.2, -1.3, 0.1), L=(-3.6, 3.4, -6), root_y=0.8, pz=24.2, hpitch=0.5, cpitch=0.22)
    frame(m, 9, R=(2.2, 7.5, 40, 4.0, -1.0), L=(-3.4, 3.4, -4), root_y=1.2, pz=24.4, hpitch=-0.1, cpitch=0.14)
    frame(m, 13, R=(2.2, 4.0, 6, None), L=(-2.4, 3.0, 6, None), root_y=1.6, pz=24.6, hpitch=-0.2, cpitch=0.1)
    frame(m, 17, R=(2.2, 3.0, 0, None), L=(-2.2, 3.4, 0, None), root_y=1.6, pz=24.6, hpitch=-0.2, cpitch=0.1)
    for f in (0, 3, 5, 7, 9, 13, 17): arms_out(m, f, (0.1, 0.4, 0.5, 0.2), (0.1, 0.4, 0.5, 0.2))
    c = M.aim_ball(m, 7, 'boot', 'R', vin=(0.0, -2.6, 0.0), pre=7, off=(0, 1.6, 0.6))
    m.ball(8, fly(c, (0.0, 6.0, 0.0), 10, g=0.0), spin_x=2.0)
    return m


@move('PS18', 'Long Ball Forward')
def ps18():
    m = S.sh22(); look(m, 0, 11, 0.0, -0.25)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (0.2, 7.0, 2.8), 16, g=0.2), spin_x=-1.6)
    for f in (13, 14, 15): m.k(f, hpitch=-0.45, cpitch=0.0)
    celebrate(m, 18, m.N, 'wide')
    return m


@move('PS19', 'Corner Delivery')
def ps19():
    m = S.sh03(); m.N = 26
    # signals to the box with an arm up, a few measured steps, then the whipped inswinger
    for f in range(0, 8): m.keys[f].update(run_pose_at(f, -12.0 + 1.2 * f, step=0)) if False else None
    raise_arm(m, 0, 5)
    for f in range(0, 7): m.k(f, hyaw=0.5 * math.sin(f * 0.7), hpitch=-0.2)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (-1.6, 3.6, 2.2), 13, g=0.24), spin_x=-1.6, spin_z=-1.8)
    for f in range(14, 26): m.keys[f] = run_pose_at(f, 12.0, step=0)
    for f in range(13, 26): m.k(f, hpitch=-0.35)
    return m


@move('PS20', 'Short Corner')
def ps20():
    m = blank(16, 64, ball=(1.4, 8.0, 3.0), events={'strike': 7})
    raise_arm(m, 0, 3, 'L')
    for f in range(0, 16): m.k(f, bvis=1.0)
    frame(m, 0, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0), hpitch=-0.2, cpitch=0.08)
    frame(m, 3, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0), hpitch=0.35, cpitch=0.12, root_y=0.1)
    frame(m, 5, R=(2.4, -1.5, 40, 4.0), L=(-3.4, 3.0, -4), root_y=0.4, pz=24.4, hpitch=0.5, cpitch=0.2)
    frame(m, 7, R=(2.2, 6.4, 54, 3.4, -1.2, 0.1), L=(-3.6, 4.4, -6), root_y=0.9, pz=24.2, hpitch=0.5, cpitch=0.22)
    frame(m, 9, R=(2.0, 8.5, 40, 4.0), L=(-3.4, 4.6, -4), root_y=1.4, pz=24.4, hpitch=0.1)
    frame(m, 12, R=(2.2, 5.0, 8, None), L=(-2.4, 4.0, 8, None), root_y=1.8, pz=24.6, hpitch=-0.1)
    frame(m, 15, R=(2.2, 3.5, 0, None), L=(-2.2, 3.8, 0, None), root_y=1.8, pz=24.6, hpitch=-0.1)
    for f in (5, 7, 9, 12, 15): arms_out(m, f, (0.1, 0.4, 0.5, 0.2), (0.1, 0.4, 0.5, 0.2))
    arms_out(m, 0, (0.1, 0.4, 0.5, 0.2), (0.1, 0.4, 0.5, 0.2))
    for f in range(0, 4): m.arms(f, 'L', 2.6, 0.25, 2.9, 0.15)
    c = M.aim_ball(m, 7, 'boot', 'R', vin=(0, 0, 0), pre=0); rest(m, c, 0, 7)
    m.ball(8, fly(c, (-2.0, 2.6, 0.0), 8, g=0.0), spin_x=1.0)
    return m


@move('PS21', 'Free Kick Cross')
def ps21():
    m = S.sh05()
    # hands on hips measuring the run-up, then a long curving approach and a floated ball in
    for f in range(0, 4):
        k = stand(ry=-19.8); k.update(bvis=1.0); m.keys[f] = k
    hands_on_hips(m, 0, 3); look(m, 0, 3, 0.4, -0.3)
    S.shift_x(m, 4, 11, 4.0, 0.0)
    c = fix_contact(m); rest(m, c, 0, 12)
    m.ball(13, fly(c, (-1.0, 4.2, 2.0), 13, g=0.2), spin_x=-1.6, spin_z=-1.4)
    return m


@move('PS22', 'Quick Free Kick')
def ps22():
    m = blank(16, 54, ball=(1.4, 8.0, 3.0), events={'strike': 7})
    for f in range(0, 16): m.k(f, bvis=1.0)
    frame(m, 0, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0), hpitch=-0.1, hyaw=0.8, cpitch=0.1)
    frame(m, 2, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0), hpitch=-0.1, hyaw=-0.6, cpitch=0.1, root_y=0.1)     # a quick look round
    frame(m, 4, R=(2.4, -2.0, 44, 4.0), L=(-3.4, 3.0, -4), root_y=0.5, pz=24.2, hpitch=0.3, hyaw=0.0, cpitch=0.2)
    frame(m, 5, R=(2.4, -3.2, 54, 6.0), L=(-3.6, 3.6, -6), root_y=0.7, pz=24.2, hpitch=0.2, cpitch=0.24)
    frame(m, 7, R=(2.2, 6.6, 70, 3.6), L=(-3.6, 4.6, -6), root_y=1.0, pz=24.2, hpitch=-0.1, cpitch=0.26)
    frame(m, 9, R=(2.0, 11.5, 58, 4.4), L=(-3.4, 4.8, -6), root_y=2.0, pz=24.4, hpitch=-0.2, cpitch=0.2)
    frame(m, 11, R=(2.2, 10.0, 30, 5.0), L=(-3.0, 6.0, 12, 4.0), root_y=3.6, pz=24.4, cpitch=0.14, hpitch=-0.2)
    frame(m, 15, R=(2.2, 8.0, 8, None), L=(-2.4, 7.0, 15, 6.0), root_y=6.5, pz=24.4, cpitch=0.1, hpitch=-0.2)
    for f in (0, 2, 4, 5, 7, 9, 11, 15): arms_out(m, f, (0.1, 0.4, 0.5, 0.2), (0.1, 0.4, 0.5, 0.2))
    arms_out(m, 5, (-0.3, 0.5, 0.2, 0.3), (0.6, 0.6, 1.0, 0.5))
    c = M.aim_ball(m, 7, 'boot', 'R', vin=(0, 0, 0), pre=0); rest(m, c, 0, 7)
    m.ball(8, fly(c, (0.6, 7.6, 0.4), 8, g=0.06), spin_x=2.0)
    return m


@move('PS23', 'Lay Off')
def ps23():
    m = blank(18, 66, ball=(1.4, 24.0, 3.0), events={'strike': 8})
    # back to goal: the ball arrives, the boot gives with it and drops it dead back to the shooter, body leaning away
    for f in range(0, 18): m.k(f, bvis=1.0)
    frame(m, 0, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0), hpitch=0.3, cpitch=0.1)
    frame(m, 4, R=(2.4, 1.5, 18, 3.0), L=(-3.0, 0.8, -4), root_y=0.2, pz=24.4, hpitch=0.5, cpitch=0.16, pyaw=0.2)
    frame(m, 7, R=(2.4, 6.5, 30, 3.6, -0.6, 0.0), L=(-3.4, 1.4, -6), root_y=0.2, pz=24.4, hpitch=0.6, cpitch=0.1, pyaw=0.35, ppitch=-0.1)
    frame(m, 8, R=(2.4, 6.0, 40, 3.2, -1.0, 0.1), L=(-3.4, 1.4, -6), root_y=0.0, pz=24.2, hpitch=0.6, cpitch=0.0, pyaw=0.4, ppitch=-0.12)       # pulls the foot back with the ball
    frame(m, 10, R=(2.4, 3.0, 30, 3.4, -1.0), L=(-3.4, 1.4, -6), root_y=-0.6, pz=24.4, hpitch=0.4, cpitch=-0.1, pyaw=0.3)
    frame(m, 13, R=(2.2, 1.5, 8, None), L=(-2.6, 1.8, 6, None), root_y=-0.4, pz=24.6, hpitch=0.1, cpitch=0.05)
    frame(m, 17, R=(2.2, 1.0, 0, None), L=(-2.2, 1.4, 0, None), root_y=-0.4, pz=24.6, hpitch=0.0, cpitch=0.05)
    for f in (0, 4, 7, 8, 10, 13, 17): arms_out(m, f, (0.2, 0.7, 0.9, 0.4), (0.2, 0.7, 0.9, 0.4))
    c = M.aim_ball(m, 8, 'boot', 'R', vin=(0.0, -2.8, 0.0), pre=8, off=(0, 1.6, 0.6))
    m.ball(9, [(c[0] - 0.1 * i, c[1] - 1.8 * i + 0.02 * i * i, 3.0) for i in range(1, 10)], spin_x=-1.0)
    return m


@move('PS24', 'Flick On')
def ps24():
    m = S.sh11()
    # a back-header: the head tips back and glances the ball up and over the shoulder
    for f in range(9, 16): m.k(f, hyaw=0.0, hroll=0.0)
    m.k(11, hpitch=-0.2, cpitch=-0.2); m.k(12, hpitch=-0.5, cpitch=-0.4, ppitch=-0.1); m.k(13, hpitch=-0.3, cpitch=-0.25)
    c = M.aim_ball(m, 12, 'head', vin=(0.0, -3.0, -0.5), pre=12)
    m.ball(13, fly(c, (0.4, -3.2, 1.4), 10, g=0.14), spin_x=-1.6)
    return m


@move('PS25', 'Reverse Pass')
def ps25():
    m = S.sh30()
    # runs one way, sells it, then the boot wraps round and sends it the other way
    shift_x(m, 0, 8, 6.0, 0.0)
    look(m, 0, 9, -0.7, -0.1)
    c = np.array([m.keys[12]['bx'], m.keys[12]['by'], m.keys[12]['bz']])
    m.ball(13, [(1.8 - 3.2 * i, 5.0 - 2.4 * i, 3.0) for i in range(9)], spin_x=-1.4, spin_z=1.0)
    return m


NOSNAP = set(MOVES)       # every pass fixes its own contact (fix_contact / aim_ball)


def build(ids=None):
    out = []
    for id_, (label, fn) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); name = id_.lower() + '_' + label.lower().replace(' ', '_')
        m.save(name, label, 'auto-generated by sprites/moves_pass.py'); out.append((id_, name))
    return out


if __name__ == '__main__':
    for id_, name in build(sys.argv[1:] or None): print(id_, name)
