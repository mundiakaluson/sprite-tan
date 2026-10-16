"""The 30 SHOT skill animations (SH01-SH30). Run:  python moves_shot.py [id ...]  to (re)write data/animations/shXX_*.json"""
import math, sys
import gen_actions as A
import moves as M
import numpy as np
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


FINESSE_ENV = {8: 0.25, 9: 0.55, 10: 0.8, 11: 0.95, 12: 1.0, 13: 0.95, 14: 0.9, 15: 0.75, 16: 0.5, 17: 0.25, 18: 0.08}


def retime(m, tmap, ms=None, strike=None):
    """a new Move whose frame j shows the source move at (fractional) source time tmap[j]: slow a wind-up down, hold the top of the backswing,
    whip the strike through in a frame or two and let the follow-through hang. Interpolates the source's dense poses with PCHIP."""
    src = m.poses(); n = len(src); xs = list(range(n))
    out = M.Move({}, len(tmap), ms or m.ms, dict(m.events))
    keys = sorted(src[0].keys())
    for j, t in enumerate(tmap):
        out.keys[j] = {k: float(A.pchip(xs, [src[i][k] for i in xs], t)) for k in keys}
    if strike is not None: out.events['strike'] = strike
    return out


def finesse_windup(m):
    """a big, readable backswing: the hips open and the kicking leg is drawn right back and up behind him (heel towards the backside, toe pointed),
    shoulders coiled the other way and the plant-side arm already rising; this is what tells you the ball is going to be bent"""
    from gen_actions import foot as gfoot, pole as gpole
    for f, ft, coil in ((8, (3.0, -8.0, 11.0, 60), 0.4), (9, (3.8, -13.0, 16.5, 72), 0.8), (10, (4.2, -15.5, 19.5, 80), 1.0)):
        k = m.keys[f]
        k.update(gfoot('R', ft[0], ft[1], ft[2], ft[3])); k.update(gpole('R', 1.0, 1.0, -0.4))
        k['pyaw'] = k.get('pyaw', 0.0) - 0.25 * coil                    # hips open to the kicking side
        k['cyaw'] = k.get('cyaw', 0.0) + 0.3 * coil                     # shoulders stay square: the coil
        k['L_a1'] = k.get('L_a1', 0.0) + (2.0 - k.get('L_a1', 0.0)) * coil
    return m


# new frame -> source frame: short run-in, slow wind-up with a hold at the top, a two-frame whip into contact (new frame 12),
# a long follow-through that keeps the lean, then the recovery steps
# (the tail stops at the follow-through landing, then settle_to_stand eases him upright watching the ball: no running steps in the clip)
FINESSE_TIME = [4.0, 5.3, 6.6, 7.6, 8.2, 8.7, 9.2, 9.6, 9.9, 10.05, 10.15, 11.0, 12.0, 12.5, 13.0, 13.5, 14.0, 14.6, 15.2, 15.8, 16.4,
                17.0, 17.4, 17.7]


def settle_to_stand(m, frames=6, watch=0.15):
    """append `frames` frames easing from the last pose to a balanced stand (feet under him, arms down, head up following the ball):
    after a shot he stops and watches it instead of stepping straight back into a run"""
    last = dict(m.keys[m.N - 1]); goal = dict(last); goal.update(stand(0, last.get('root_y', 0.0)))
    goal['hpitch'] = watch; goal['bvis'] = last.get('bvis', 0.0)
    for k in ('bx', 'by', 'bz', 'brx', 'brz'): goal.pop(k, None)
    for i in range(1, frames + 1):
        u = i / frames; u = u * u * (3 - 2 * u)
        m.keys[m.N - 1 + i] = {k: (last[k] + (goal[k] - last[k]) * u if k in goal and isinstance(last[k], float) else last[k]) for k in last}
    m.N += frames
    return m


def finesse_bend(m, amt=1.0, roll=1.0, tilt=0.35, back=0.5, hips=-0.2, head=0.45, drift=2.2):
    """the curler shape from the references (Locatelli v Juve, the low-camera academy goal): the WHOLE body tips over the planted foot (pelvis roll `tilt`)
    and the chest bends further (`roll`) so head and shoulders hang out over the plant side, shoulders back / hips through (`back`, `hips`) so the C
    reads side-on too, head counter-tilted with the eyes on the ball, the plant-side arm flung out wide and up, the kicking-side arm swept back.
    Exaggerated on purpose: at 40 px a real 25 degree bend reads as upright. Strongest at the contact frame (12)."""
    L_ARM = (0.2, 2.35, 0.5, 0.9)                                         # wide and high: balance
    R_ARM = (-0.7, 0.7, 0.6, 0.4)                                         # back and down, across the turn
    for f, b in FINESSE_ENV.items():
        k = m.keys[f]; b *= amt
        k['croll'] = k.get('croll', 0.0) + (roll - k.get('croll', 0.0)) * b
        k['proll'] = k.get('proll', 0.0) + (tilt - k.get('proll', 0.0)) * b
        k['cpitch'] = k.get('cpitch', 0.0) - back * b                      # shoulders back ...
        k['ppitch'] = k.get('ppitch', 0.0) + hips * b                      # ... hips through: the C reads in the side view too
        k['hroll'] = k.get('hroll', 0.0) + (-0.55 - k.get('hroll', 0.0)) * b
        k['hpitch'] = k.get('hpitch', 0.0) + head * b                      # eyes down on the ball
        k['root_x'] = k.get('root_x', 0.0) - drift * b                     # the body hangs out over the plant foot
        k['pz'] = k.get('pz', 23.0) - 1.0 * b
        for side, tgt in (('L', L_ARM), ('R', R_ARM)):
            for key, v in zip(('s1', 'a1', 's2', 'a2'), tgt):
                kk = f'{side}_{key}'; k[kk] = k.get(kk, 0.0) + (v - k.get(kk, 0.0)) * b
    return m


@move('SH03', 'Finesse Curler')
def sh03():
    return settle_to_stand(retime(finesse_bend(finesse_windup(finesse_base())), FINESSE_TIME, ms=55, strike=12))


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


def run_pose_at(f, y0=5.0, step=2.4):
    import gen_actions as A
    k = A.run_pose(A.BASE, (f - 6) / 12.0, y0 + step * (f - 15))
    k.update(dict(bvis=0.0)); return k


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


def fly(c, v, n, g=0.22, spin=2.0):
    """ball after contact from c with velocity v per frame; gravity g; bounces off the turf"""
    x, y, z = c; vx, vy, vz = v; o = []
    for i in range(n):
        x += vx; y += vy; z += vz; vz -= g
        if z < 1.8: z = 1.8; vz = abs(vz) * 0.45
        o.append((x, y, z))
    return o


def shift_x(m, f0, f1, dx0, dx1):
    """slide the body sideways across frames f0..f1 (feet and ball-free keys follow), for angled run-ups"""
    for f in range(f0, f1 + 1):
        dx = dx0 + (dx1 - dx0) * (f - f0) / max(1, f1 - f0)
        k = m.keys.get(f, {})
        for key in ('root_x', 'R_ax', 'L_ax', 'R_kx', 'L_kx'):
            if key in k: k[key] += dx
    return m


def sprint(m, f1=8):
    """lean into the run-up: more forward lean, bigger arm pump (frames 0..f1)"""
    for f in range(f1):
        k = m.keys[f]; k['cpitch'] = k.get('cpitch', 0.1) + 0.12; k['ppitch'] = k.get('ppitch', 0.0) + 0.05
    return m


def celebrate(m, f0, f1, kind='fist'):
    for f in range(f0, f1):
        if kind == 'fist': m.arms(f, 'R', 2.7, 0.25, 3.0, 0.15)
        elif kind == 'wide': m.arms(f, 'R', 1.5, 1.3, 1.6, 1.2); m.arms(f, 'L', 1.5, 1.3, 1.6, 1.2)
        elif kind == 'both': m.arms(f, 'R', 2.6, 0.5, 2.9, 0.3); m.arms(f, 'L', 2.6, 0.5, 2.9, 0.3)
    return m


@move('SH04', 'Trivela Bender')
def sh04():
    m = kick_base()
    # outside of the right boot: torso and hips bend over to the right, the leg swings out wide and the toes point in
    for f in (7, 8): m.k(f, croll=0.1 * (f - 6))
    frame(m, 9, R=(-0.5, -4.0, 45, 7.0, 0.3, 0.0), L=(-3.4, 4.0, -6), root_y=1.4, pz=24.2, cpitch=0.18, croll=0.22, proll=0.1, pyaw=-0.25)
    frame(m, 10, R=(-1.6, -8.5, 55, 11.0, 0.5, 0.2), L=(-3.0, 5.0, -6), root_y=2.0, pz=23.6, cpitch=0.2, croll=0.32, proll=0.18, pyaw=-0.45, root_x=0.6)
    frame(m, 11, R=(1.8, -1.0, 68, 8.5, 0.9, 0.35), L=(-3.0, 5.4, -6), root_y=2.4, pz=23.2, cpitch=0.2, croll=0.42, proll=0.24, pyaw=-0.15, root_x=0.8)
    frame(m, 12, R=(5.4, 7.6, 78, 3.6, 1.0, 0.45), L=(-2.8, 5.8, -6), root_y=2.7, pz=23.0, cpitch=0.2, croll=0.5, proll=0.28, pyaw=0.15, root_x=1.0)
    frame(m, 13, R=(5.8, 15.5, 62, 7.0, 0.9, 0.35), L=(-2.8, 6.0, -5), root_y=3.8, pz=23.4, cpitch=0.18, croll=0.4, proll=0.22, pyaw=0.35, root_x=0.8)
    frame(m, 14, R=(3.0, 20.0, 55, 10.0, 0.7, 0.3), L=(-3.0, 6.6, 10, 5.0), root_y=5.8, pz=24.6, cpitch=0.14, croll=0.28, proll=0.14, pyaw=0.55)
    frame(m, 15, R=(-0.8, 22.5, 45, 12.0, 0.4), L=(-3.0, 7.6, 14, 4.0), root_y=7.8, pz=25.2, cpitch=0.12, croll=0.16, proll=0.06, pyaw=0.7)          # leg swings across the body, still reaching
    frame(m, 16, R=(-1.0, 22.0, 30, 9.0), L=(-2.6, 9.0, 20, 5.0), root_y=9.8, pz=25.0, cpitch=0.1, croll=0.06, pyaw=0.5)
    frame(m, 17, R=(1.0, 20.0, 12, None), L=(-2.4, 11.0, 20, 6.0), root_y=12.0, pz=24.0, cpitch=0.1, croll=0.0, pyaw=0.2)
    arms_out(m, 11, (-0.2, 1.3, 0.2, 1.0), (1.2, 1.6, 1.6, 1.5)); arms_out(m, 12, (-0.3, 1.4, 0.0, 1.0), (1.3, 1.7, 1.7, 1.6))
    c = M.aim_ball(m, 12, 'boot', 'R', vin=(0.0, 0.0, 0.0), pre=0, off=(0, 0.6, 0.4))
    for f in range(0, 12): m.k(f, bx=c[0], by=c[1], bz=c[2], bvis=1.0)
    m.ball(13, path(11, speed=7.4, rise=0.12, curve=0.9, dip=0.3, start=(c[0], c[1] + 3.5, 3.6)), spin_x=1.4, spin_z=1.8)
    return m


@move('SH08', 'Volley')
def sh08():
    m = kick_base()
    # a flying strike: leaves the ground, leans right back, the shooting leg fully stretched at the ball, other leg trailing, arms wide
    frame(m, 8, R=(2.2, -2.5, 40, 4.0), L=(-2.4, 0.8, 5, 11.0), root_y=0.2, pz=25.2, cpitch=0.12)
    frame(m, 9, R=(2.2, -4.0, 40, 6.5), L=(-3.0, 1.2, -6), root_y=1.0, pz=22.6, cpitch=0.1, ppitch=0.05)          # plant and gather
    frame(m, 10, R=(2.4, -6.0, 45, 10.0), L=(-3.4, -1.5, 25, 8.0), root_y=2.0, pz=26.5, cpitch=-0.2, ppitch=-0.2, proll=0.12)   # springs off
    frame(m, 11, R=(2.6, 5.0, 55, 14.5), L=(-3.8, -5.0, 40, 12.0), root_y=3.0, pz=29.5, cpitch=-0.5, ppitch=-0.4, proll=0.22, pyaw=0.1)
    frame(m, 12, R=(2.4, 20.0, 66, 17.0), L=(-4.2, -6.5, 45, 15.5), root_y=3.8, pz=30.0, cpitch=-0.72, ppitch=-0.5, proll=0.3, pyaw=0.2, hpitch=0.35)
    frame(m, 13, R=(2.2, 22.5, 62, 20.0), L=(-4.0, -5.5, 40, 14.0), root_y=5.0, pz=29.0, cpitch=-0.6, ppitch=-0.42, proll=0.26, pyaw=0.2)
    frame(m, 14, R=(1.8, 21.0, 50, 17.0), L=(-3.0, 0.0, 30, 9.0), root_y=6.4, pz=26.6, cpitch=-0.3, ppitch=-0.2, proll=0.15)
    frame(m, 15, R=(1.8, 17.5, 25, 8.0), L=(-2.6, 8.0, 15, 3.0), root_y=8.0, pz=24.4, cpitch=0.05, ppitch=0.0, proll=0.05)
    frame(m, 16, R=(2.2, 14.0, 6, None), L=(-2.4, 6.0, 6, None), root_y=9.2, pz=23.0, cpitch=0.3, ppitch=0.15)           # lands bent
    frame(m, 17, R=(2.2, 12.0, 0, None), L=(-2.4, 8.0, 0, None), root_y=10.5, pz=24.2, cpitch=0.15)
    for f in range(18, 22): m.keys[f] = run_pose_at(f, 10.5)
    for f in (10, 11, 12, 13): arms_out(m, f, (-0.5, 1.3, -0.1, 1.2), (1.3, 1.6, 1.4, 1.5))
    m.ball(0, [(1.8, 11.0, 3.0)] * 1)
    c = M.aim_ball(m, 12, 'boot', 'R', vin=(0.0, -0.8, -3.6), pre=12)
    m.ball(13, fly(c, (0.0, 9.0, -0.15), 9, g=0.05), spin_x=2.4)
    return m


@move('SH29', 'Lob Volley')
def sh29():
    m = sh08()
    # same flying volley but the boot gets underneath: leg angled up, ball floats over the keeper
    frame(m, 12, R=(2.2, 17.0, 20, 14.0)); frame(m, 13, R=(2.0, 21.0, 10, 20.0)); frame(m, 14, R=(1.8, 20.0, 5, 23.0))
    c = M.aim_ball(m, 12, 'boot', 'R', vin=(0.0, -0.8, -3.6), pre=12)
    m.ball(13, fly(c, (0.0, 4.2, 2.3), 9, g=0.26), spin_x=-2.4)
    return m


@move('SH10', 'Diving Header')
def sh10():
    m = kick_base(); m.N = 26
    for f in range(8, 26): m.keys[f] = {}
    # run, plant and crouch, spring off both feet, throw the head at the ball, then drop and skid on the belly
    frame(m, 8, R=(2.2, -2.0, 40, 3.0), L=(-2.4, 0.5, 5, 10.0), root_y=0.2, pz=25.4, cpitch=0.25)
    frame(m, 9, R=(2.2, 1.0, -4, None), L=(-2.4, 0.4, -4, None), root_y=1.2, pz=20.0, cpitch=0.55, ppitch=0.3)           # deep crouch
    frame(m, 10, R=(2.0, 1.5, 70, 4.0), L=(-2.2, 0.0, 60, 6.0), root_y=2.6, pz=27.0, cpitch=0.4, ppitch=0.3)              # push off
    frame(m, 11, R=(2.0, -3.0, 50, 9.0), L=(-2.2, -4.0, 55, 11.0), root_y=5.2, pz=31.0, cpitch=0.85, ppitch=0.7, hpitch=-0.3)  # rising, tipping forward
    frame(m, 12, R=(2.0, -9.0, 40, 18.0), L=(-2.2, -9.5, 45, 20.0), root_y=8.4, pz=31.5, cpitch=1.32, ppitch=1.1, hpitch=-0.55)  # flat, head first
    frame(m, 13, R=(2.0, -9.0, 40, 18.0), L=(-2.2, -9.5, 45, 19.0), root_y=11.6, pz=29.5, cpitch=1.42, ppitch=1.2, hpitch=-0.4)
    frame(m, 14, R=(2.0, -5.0, 35, 15.0), L=(-2.2, -6.0, 40, 16.0), root_y=14.6, pz=25.5, cpitch=1.45, ppitch=1.25, hpitch=-0.2)
    frame(m, 15, R=(2.0, -1.0, 30, 11.0), L=(-2.2, -2.0, 35, 12.0), root_y=17.2, pz=20.0, cpitch=1.5, ppitch=1.3, hpitch=0.1)
    frame(m, 16, R=(2.0, 2.0, 25, 7.0), L=(-2.2, 1.0, 30, 8.0), root_y=19.6, pz=13.5, cpitch=1.5, ppitch=1.35, hpitch=0.35)
    for f in range(17, 26): frame(m, f, R=(2.0, 3.5 + 0.8 * (f - 17), 20, 5.0), L=(-2.2, 2.5 + 0.8 * (f - 17), 20, 5.5), root_y=21.0 + 0.9 * (f - 17), pz=8.0 - 0.1 * (f - 17), cpitch=1.5, ppitch=1.4, hpitch=0.45)
    for f in range(10, 13): arms_out(m, f, (2.2, 0.3, 2.5, 0.2), (2.2, 0.3, 2.5, 0.2))
    for f in range(13, 17): arms_out(m, f, (1.9, 0.4, 2.0, 0.3), (1.9, 0.4, 2.0, 0.3))
    for f in range(17, 26): arms_out(m, f, (1.7, 0.6, 1.7, 0.5), (1.7, 0.6, 1.7, 0.5))
    for f in (8, 9): arms_out(m, f, (-0.6, 0.8, 0.2, 0.5), (-0.6, 0.8, 0.2, 0.5))
    for f in range(0, 8): m.k(f, bvis=1.0)
    c = M.aim_ball(m, 12, 'head', vin=(-1.4, -1.8, -0.5), pre=12)
    m.ball(13, fly(c, (0.5, 8.5, 0.2), 12, g=0.12), spin_x=1.4)
    m.events = {'strike': 12}
    return m


@move('SH11', 'Glancing Header')
def sh11():
    m = kick_base()
    # standing leap to meet a cross from the right: head turns, the ball is only brushed on towards the far post
    frame(m, 8, R=(2.2, -2.0, 30, 6.0), L=(-2.4, 1.0, 10, 5.0), root_y=0.4, pz=25.0)
    frame(m, 9, R=(2.2, 0.6, -4, None), L=(-2.4, 0.5, -4, None), root_y=1.0, pz=22.0, cpitch=0.2, ppitch=0.1)
    frame(m, 10, R=(2.2, 0.0, 55, 4.0), L=(-2.4, 0.0, 55, 4.0), root_y=1.6, pz=27.5, cpitch=0.0, ppitch=0.0)
    frame(m, 11, R=(2.0, -2.0, 40, 9.0), L=(-2.4, -2.5, 40, 10.0), root_y=2.0, pz=31.0, cpitch=-0.15, ppitch=0.0, hyaw=0.2, hroll=0.15, proll=0.1)
    frame(m, 12, R=(2.0, -3.0, 38, 9.0), L=(-2.4, -3.5, 38, 10.0), root_y=2.4, pz=32.0, cpitch=-0.2, ppitch=-0.05, hyaw=0.7, hroll=0.3, hpitch=0.05, proll=0.14, cyaw=0.25)
    frame(m, 13, R=(2.0, -2.0, 36, 7.0), L=(-2.4, -2.5, 36, 8.0), root_y=2.8, pz=30.5, cpitch=-0.05, hyaw=0.5, hroll=0.1, proll=0.06)
    frame(m, 14, R=(2.2, 0.0, 22, 3.5), L=(-2.4, 0.0, 22, 3.5), root_y=3.2, pz=27.0, cpitch=0.1, hyaw=0.2)
    frame(m, 15, R=(2.2, 1.0, 4, None), L=(-2.4, 0.5, 4, None), root_y=3.8, pz=23.4, cpitch=0.25, hyaw=0.0)
    for f in range(16, 22): m.keys[f] = run_pose_at(f, 3.8)
    for f in (10, 11, 12): arms_out(m, f, (0.9, 1.5, 1.3, 1.3), (0.9, 1.5, 1.3, 1.3))
    c = M.aim_ball(m, 12, 'head', vin=(-3.2, -0.2, -0.45), pre=12)
    m.ball(13, fly(c, (-2.4, 6.0, 0.0), 9, g=0.08), spin_x=0.4, spin_z=1.6)
    return m


@move('SH12', 'Power Header')
def sh12():
    m = kick_base()
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
    c = M.aim_ball(m, 12, 'head', vin=(0.0, -3.0, -1.3), pre=12)
    m.ball(13, fly(c, (0.0, 10.5, -0.4), 9, g=0.06), spin_x=1.2)
    return m


@move('SH13', 'Rabona Strike')
def sh13():
    m = kick_base()
    # ball sits out to the left; the right leg loops BEHIND the planted left leg and strikes it from the left side of the body
    BX = -4.4
    for f in range(0, 8): m.k(f, bx=BX, by=10.5, bz=3.0)
    shift_x(m, 3, 7, -0.3, -2.2)
    frame(m, 8, R=(-0.4, -2.0, 30, 5.0), L=(-6.6, 3.0, -6), root_y=0.8, pz=24.6, root_x=-4.0, cpitch=0.14)
    frame(m, 9, R=(-5.4, -3.0, 40, 6.0), L=(-6.8, 5.8, -6), root_y=1.6, pz=24.6, root_x=-4.2, cpitch=0.2, pyaw=-0.35, proll=-0.06)
    frame(m, 10, R=(-8.8, -3.4, 52, 8.0), L=(-6.8, 6.4, -6), root_y=2.2, pz=24.0, root_x=-4.2, cpitch=0.26, pyaw=-0.6, proll=-0.16)   # leg swung round behind
    frame(m, 11, R=(-9.4, 2.0, 62, 6.4), L=(-6.8, 6.4, -6), root_y=2.4, pz=23.8, root_x=-4.2, cpitch=0.3, pyaw=-0.45, proll=-0.2)
    frame(m, 12, R=(-7.2, 9.0, 72, 3.2), L=(-6.8, 6.4, -6), root_y=2.6, pz=23.8, root_x=-4.2, cpitch=0.32, pyaw=-0.2, proll=-0.2)    # strike, leg still crossed
    frame(m, 13, R=(-5.0, 13.5, 62, 7.0), L=(-6.4, 6.4, -4), root_y=3.8, pz=24.0, root_x=-4.0, cpitch=0.26, pyaw=0.1, proll=-0.12)
    frame(m, 14, R=(-3.2, 15.5, 44, 9.0), L=(-6.0, 7.0, 10, 4.0), root_y=6.0, pz=24.4, root_x=-3.0, cpitch=0.2, pyaw=0.2)
    frame(m, 15, R=(-1.0, 17.0, 22, 5.0), L=(-5.0, 8.4, 20, 5.0), root_y=8.6, pz=24.4, root_x=-2.0)
    frame(m, 16, R=(0.4, 18.0, 8, None), L=(-3.4, 10.0, 20, 6.5), root_y=11.0, pz=23.8, root_x=-1.2)
    arms_out(m, 10, (0.2, 1.0, 0.8, 0.8), (0.6, 1.4, 1.2, 1.0)); arms_out(m, 12, (0.8, 1.2, 1.2, 1.0), (-0.2, 1.1, 0.4, 0.8))
    c = M.aim_ball(m, 12, 'boot', 'R', vin=(0.0, -0.3, 0.0), pre=12)
    m.ball(13, fly(c, (0.3, 7.0, 0.35), 10, g=0.1), spin_x=2.0, spin_z=-1.2)
    for f in range(0, 12): m.k(f, bx=BX, by=10.5, bz=3.0)
    return m


@move('SH23', 'Snap Shot')
def sh23():
    m = blank(16, 58, ball=(1.4, 8.0, 3.0), events={'strike': 7})
    # no windup: the knee lifts, the lower leg whips through, the body barely moves. Arms stay close and swing a little
    frame(m, 0, R=(2.2, 0.0, 0), L=(-2.2, 0.4, 0), hpitch=0.25, cpitch=0.1)
    frame(m, 2, R=(2.2, 0.0, 0), L=(-3.0, 1.4, 20, 3.0), root_y=0.2, pz=24.4, hpitch=0.3, cpitch=0.14)
    frame(m, 4, R=(2.4, -1.5, 40, 3.0), L=(-3.6, 2.6, -4), root_y=0.5, pz=24.2, hpitch=0.4, cpitch=0.2, pyaw=-0.1)
    frame(m, 5, R=(2.4, -2.8, 60, 7.0), L=(-3.6, 3.6, -6), root_y=0.8, pz=24.4, hpitch=0.5, cpitch=0.26, pyaw=-0.15)
    frame(m, 6, R=(2.2, 2.5, 76, 5.0), L=(-3.6, 4.2, -6), root_y=1.0, pz=24.4, cpitch=0.3, pyaw=0.0)
    frame(m, 7, R=(2.0, 7.5, 84, 3.4), L=(-3.6, 4.6, -6), root_y=1.2, pz=24.4, cpitch=0.34, pyaw=0.1)
    frame(m, 8, R=(1.8, 10.5, 66, 5.0), L=(-3.6, 4.8, -6), root_y=1.6, pz=24.4, cpitch=0.3, pyaw=0.12)
    frame(m, 10, R=(2.0, 9.0, 36, 6.0), L=(-3.2, 5.0, 8, 3.0), root_y=2.4, pz=24.6, cpitch=0.2)
    frame(m, 13, R=(2.2, 6.0, 8, None), L=(-2.6, 5.0, 8, None), root_y=2.8, pz=24.6, cpitch=0.12, hpitch=0.0)
    frame(m, 15, R=(2.2, 3.5, 0, None), L=(-2.2, 3.8, 0, None), root_y=2.8, pz=24.6, cpitch=0.1, hpitch=0.0)
    for f in (0, 2, 4): arms_out(m, f, (0.1, 0.35, 0.5, 0.2), (0.1, 0.35, 0.5, 0.2))
    arms_out(m, 5, (-0.3, 0.45, 0.2, 0.3), (0.5, 0.5, 0.9, 0.4)); arms_out(m, 7, (0.2, 0.4, 0.6, 0.3), (0.6, 0.5, 0.9, 0.4))
    for f in (10, 13, 15): arms_out(m, f, (0.2, 0.35, 0.5, 0.2), (0.2, 0.35, 0.5, 0.2))
    c = M.aim_ball(m, 7, 'boot', 'R', vin=(0.0, 0.0, 0.0), pre=0, off=(0, 1.6, 0.6))
    for f in range(0, 7): m.k(f, bx=c[0], by=c[1], bz=c[2], bvis=1.0)
    m.ball(8, fly(c, (0.0, 8.0, 0.0), 8, g=0.0), spin_x=2.0)
    return m


@move('SH26', 'Shot Fake')
def sh26():
    m = kick_base(); m.N = 30
    for f in range(8, 30): m.keys[f] = {}
    # dribbling in, the leg goes back as if to shoot... the boot stops over the ball, a quick drop of the shoulder, then the ball is carried on
    def dribble(f, ry):
        m.k(f, bx=1.2 + 0.5 * math.sin(f * 1.3), by=ry + 9.5 + 1.4 * abs(math.sin(f * 0.52 * math.pi)), bz=3.0, bvis=1.0)
    for f in range(0, 8): dribble(f, m.keys[f]['root_y'])
    frame(m, 8, R=(2.2, -4.0, 40, 5.0), L=(-3.0, 3.0, -6), root_y=0.6, pz=24.6, cpitch=0.16, pyaw=-0.1)
    frame(m, 9, R=(1.8, -9.0, 50, 12.0), L=(-4.6, 4.4, -6), root_y=1.4, pz=24.2, cpitch=0.26, pyaw=-0.34, proll=0.06)                # big backswing
    frame(m, 10, R=(1.6, -14.0, 56, 17.0), L=(-5.0, 4.8, -6), root_y=1.8, pz=24.0, cpitch=0.34, pyaw=-0.5)
    frame(m, 11, R=(1.6, 2.0, 66, 11.0), L=(-5.0, 5.0, -6), root_y=2.2, pz=24.0, cpitch=0.4, pyaw=-0.1)
    frame(m, 12, R=(1.6, 7.5, 70, 9.0), L=(-5.0, 5.2, -6), root_y=2.4, pz=24.0, cpitch=0.42, pyaw=0.1)                               # stops short
    frame(m, 13, R=(1.2, 8.0, 60, 9.0), L=(-5.0, 5.2, -6), root_y=2.4, pz=24.0, cpitch=0.42, pyaw=0.1)                               # hold
    frame(m, 14, R=(0.2, 8.2, 20, 5.0), L=(-4.2, 4.8, -6), root_y=2.6, pz=24.0, cpitch=0.3, pyaw=0.5, proll=-0.16, croll=-0.2, root_x=-0.8)   # step over, shoulder drops
    frame(m, 15, R=(-2.0, 7.0, 10, 2.5), L=(-3.0, 5.6, -6), root_y=3.2, pz=24.2, cpitch=0.24, pyaw=0.7, proll=-0.2, croll=-0.3, root_x=-1.4)
    frame(m, 16, R=(-2.6, 8.4, -4, None), L=(-2.0, 6.0, 12, 5.0), root_y=4.4, pz=24.6, cpitch=0.2, pyaw=0.4, proll=-0.1, croll=-0.15, root_x=-1.4)
    arms_out(m, 10, (-1.2, 0.5, -0.4, 0.4), (1.2, 1.6, 1.6, 1.5)); arms_out(m, 14, (0.2, 0.6, 0.6, 0.4), (1.3, 1.4, 1.6, 1.2))
    for f in range(8, 17): m.k(f, bx=1.2, by=11.5, bz=3.0, bvis=1.0)
    for f in range(17, 30):
        ry = 4.4 + 2.35 * (f - 16)
        k = run_pose_at(f, ry); m.keys[f] = k
        k.update(root_x=-1.4 * max(0.0, 1.0 - (f - 16) / 5.0), bvis=1.0, bx=-0.6 + 0.4 * math.sin(f * 1.3), by=ry + 9.0 + 1.3 * abs(math.sin(f * 0.52 * math.pi)), bz=3.0, brx=-2.0 * f)
        k['R_ax'] += k['root_x']; k['L_ax'] += k['root_x']
    m.ball(0, []); m.events = {'fake': 12}
    return m


@move('SH28', 'Composure Finish')
def sh28():
    m = kick_base()
    # simple and tidy: jogs in, eyes on the ball, a neat inside-foot tap, easy follow-through
    for f in range(8, 14): m.k(f, hpitch=0.65)
    frame(m, 9, R=(2.4, -3.0, 38, 6.0), L=(-4.0, 3.5, -6), root_y=1.5, pz=24.8, cpitch=0.12, ppitch=0.05, pyaw=-0.1)
    frame(m, 10, R=(2.6, -5.0, 42, 8.0), L=(-4.6, 5.5, -6), root_y=2.0, pz=24.4, cpitch=0.14, pyaw=-0.14)
    frame(m, 11, R=(2.8, 1.5, 50, 6.0, -1.1, 0.1), L=(-4.6, 6.0, -6), root_y=2.4, pz=24.3, cpitch=0.14, pyaw=0.05)
    frame(m, 12, R=(2.2, 8.0, 52, 3.6, -1.3, 0.1), L=(-4.4, 6.4, -6), root_y=2.8, pz=24.2, cpitch=0.16, pyaw=0.12)
    frame(m, 13, R=(1.4, 13.0, 48, 4.6, -1.0), L=(-4.2, 6.4, -6), root_y=4.0, pz=24.4, cpitch=0.14, pyaw=0.18, hpitch=0.3)
    frame(m, 14, R=(0.8, 16.5, 40, 5.5, -0.5), L=(-3.8, 6.2, -5), root_y=6.5, pz=24.4, cpitch=0.12, pyaw=0.14, hpitch=0.1)
    frame(m, 15, R=(1.6, 17.5, 25, 3.2, -0.2), L=(-3.0, 8.0, 18, 5.0), root_y=9.5, pz=24.4, cpitch=0.12, hpitch=0.0)
    frame(m, 16, R=(2.0, 19.5, 10, None), L=(-2.4, 10.0, 20, 6.5), root_y=12.2, pz=23.6, cpitch=0.14, hpitch=0.0)
    arms_out(m, 10, (-0.2, 0.6, 0.3, 0.3), (0.7, 1.1, 1.4, 0.8)); arms_out(m, 12, (-0.1, 0.6, 0.4, 0.3), (0.8, 1.1, 1.4, 0.9))
    m.ball(12, path(10, speed=5.8, rise=0.0, start=(1.4, 16.0, 3.0)), spin_x=1.6)
    m.events = {'strike': 12}
    return m



def snap_ball(m, rest=True, side='R', off=(0.0, 1.6, 0.6)):
    """make the ball leave from where the boot actually meets it: it rests at the contact point until then, and the existing flight is re-based onto it"""
    fc = m.events.get('strike', 12); ps = m.poses()
    c = M.boot_pos(ps[fc], side) + np.array(off)
    old = {f: (m.keys[f].get('bx'), m.keys[f].get('by'), m.keys[f].get('bz')) for f in range(fc, m.N) if m.keys.get(f, {}).get('bvis', 0) > 0.5 and m.keys[f].get('bx') is not None}
    o0 = np.array(old[fc]) if fc in old else None
    if rest:
        for f in range(0, fc): m.k(f, bx=float(c[0]), by=float(c[1]), bz=float(c[2]), bvis=1.0, brx=0.0, brz=0.0)
    m.k(fc, bx=float(c[0]), by=float(c[1]), bz=float(c[2]), bvis=1.0)
    if o0 is not None:
        for f, v in old.items():
            if f > fc: d = np.array(v) - o0; m.k(f, bx=float(c[0] + d[0]), by=float(c[1] + d[1]), bz=float(max(1.8, c[2] + d[2])))
    return m


SNAP_FULL = {'SH28', 'SH01', 'SH02', 'SH03', 'SH05', 'SH06', 'SH07', 'SH14', 'SH15', 'SH16', 'SH17', 'SH18', 'SH19', 'SH20', 'SH21', 'SH22', 'SH27'}
SNAP_POST = {'SH09', 'SH24', 'SH25', 'SH30'}


def style(id_, m):
    """personality passes: how the player arrives and how they finish"""
    if id_ == 'SH02': sprint(m); celebrate(m, 17, m.N, 'fist')
    elif id_ == 'SH07': sprint(m); celebrate(m, 17, m.N, 'wide')
    elif id_ == 'SH22': sprint(m, 9); celebrate(m, 18, m.N, 'both')
    elif id_ == 'SH18': shift_x(m, 0, 11, 8.0, 0.0)
    elif id_ == 'SH27': shift_x(m, 0, 11, -8.0, 0.0); celebrate(m, 17, m.N, 'fist')
    elif id_ == 'SH19': celebrate(m, 17, m.N, 'fist')
    elif id_ == 'SH20': celebrate(m, 17, m.N, 'wide')
    elif id_ == 'SH16': celebrate(m, 17, m.N, 'both')
    return m


def build(ids=None):
    out = []
    for id_, (label, fn) in MOVES.items():
        if ids and id_ not in ids: continue
        m = style(id_, fn())
        if id_ in SNAP_FULL: snap_ball(m)
        elif id_ in SNAP_POST: snap_ball(m, rest=False)
        name = id_.lower() + '_' + label.lower().replace(' ', '_')
        m.save(name, label, 'auto-generated by sprites/moves_shot.py'); out.append((id_, name))
    return out


if __name__ == '__main__':
    for id_, name in build(sys.argv[1:] or None): print(id_, name)
