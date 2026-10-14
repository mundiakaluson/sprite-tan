"""The 35 DEFEND skill animations (DF01-DF35). Run:  python moves_defend.py [id ...]  to (re)write data/animations/dfXX_*.json
Same framework as moves_dribble.py (local frame, heading, travel speed, lateral speed). The ball, where there is one, belongs to the opponent and is a preview only:
the game owns it. Tackles and clearances store a strike frame / contact point like the shots."""
import math, sys
import numpy as np
import gen_actions as A
import moves as M
import moves_shot as S
from moves_dribble import Dr, burst, PI, pch

MOVES = {}


def move(id_, label):
    def deco(fn):
        MOVES[id_] = (label, fn); return fn
    return deco


ARMS = (0.7, 0.9, 1.1, 0.6)


def stance(d, f, sw=0.0, low=0.0, **kw):
    base = dict(pz=22.6 - low, cpitch=0.3 + 0.1 * low, hpitch=0.3, croll=0.04 * sw, proll=0.02 * sw)
    base.update(kw)
    d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), **base); d.arms(f, ARMS, ARMS)


def run(d, f0, f1, lean=0.2, cad=1.0, fx=None):
    d.carry(f0, f1, lean=lean, cad=cad, ball=False)
    for f in range(f0, f1 + 1): d.m.k(f, bvis=0.0)
    if fx: d.fx[f0] = fx; d.fx[f1] = fx


def shuffle(d, f0, f1, per=4, lead='R', low=0.6, face=0.0):
    """small busy side-on steps: feet staggered, alternating lifts"""
    for f in range(f0, f1 + 1):
        ph = 2 * PI * (f - f0) / per; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.6, 3.0 + 0.8 * a, 0, 2.0 + 3.2 * a) if a > 0.05 else (2.6, 3.0, 0, None), L=(-2.6, -1.4 + 0.8 * b, 0, 2.0 + 3.2 * b) if b > 0.05 else (-2.6, -1.4, 0, None),
             pz=22.2 - low + 0.3 * math.cos(ph), cpitch=0.3, hpitch=0.35, croll=0.06 * math.sin(ph), pyaw=face, cyaw=face)
        d.arms(f, (0.5, 1.0, 1.1, 0.7), (0.9, 1.0, 1.2, 0.7))


def hidden(d, f0=0, f1=None):
    d.hide_ball(f0, (d.N - 1) if f1 is None else f1)


# ------------------------------------------------------------------ tackles and blocks
@move('DF01', 'Stand Tackle')
def df01():
    d = Dr(20, speed=0.0)
    for f in range(0, 4): stance(d, f, sw=math.sin(f * 1.6), ball=(1.0, 10.0 - 0.3 * f))
    d.at(4, R=(2.8, 1.5, 0, None), L=(-2.8, -0.4, 0, None), ball=(1.0, 9.4), pz=22.2, cpitch=0.4, hpitch=0.5)
    d.at(5, R=(1.8, 5.0, 40, 4.2), L=(-3.0, 0.2, 0, None), ball=(1.0, 9.0), pz=21.8, cpitch=0.5, hpitch=0.55)
    d.at(6, R=(1.4, 8.4, 52, 3.4, -0.9, 0.2), L=(-3.0, 0.6, 0, None), ball=(1.0, 9.0), pz=21.4, cpitch=0.56, hpitch=0.6, ppitch=0.2)      # planted, the boot comes through the ball
    d.at(7, R=(1.2, 10.4, 40, 4.0), L=(-3.0, 1.0, 0, None), ball=(1.6, 12.6), pz=21.6, cpitch=0.5)
    d.at(8, R=(1.8, 7.0, 20, 4.0), L=(-3.0, 0.6, 0, None), ball=(2.4, 15.0), cpitch=0.4)
    for f in range(9, 20): stance(d, f, sw=math.sin(f * 1.4), ball=(2.4 + 0.3 * (f - 8), 15.0 + 1.4 * (f - 8)))
    d.arms(5, (0.2, 0.7, 0.8, 0.5), (0.9, 1.1, 1.2, 0.8)); d.arms(6, (0.0, 0.6, 0.5, 0.4), (1.0, 1.1, 1.3, 0.8))
    d.m.events = {'strike': 6}
    return d.build()


@move('DF02', 'Slide Tackle')
def df02():
    import gen_uv as U
    poses = U.ANIMS['slide'][0]()[0]
    m = M.Move({}, len(poses), U.ANIMS['slide'][1], dict(U.ANIMS['slide'][3]))
    import custom_anims as C
    m.keys = {int(k): v for k, v in C.bake(poses, False).items()}
    m.events = {'strike': U.ANIMS['slide'][3].get('contact', 10)}
    return m


@move('DF03', 'Poke Tackle')
def df03():
    d = Dr(18, speed=0.0)
    for f in range(0, 4): stance(d, f, sw=math.sin(f * 1.5), ball=(1.0, 10.0))
    d.at(4, R=(2.8, 2.0, 20, None), L=(-2.8, -0.4, 0, None), ball=(1.0, 10.0), cpitch=0.4, hpitch=0.5)
    d.at(5, R=(2.0, 7.0, 75, 3.6), L=(-3.0, 0.4, 0, None), ball=(1.0, 10.0), cpitch=0.5, hpitch=0.55, pz=22.0)
    d.at(6, R=(1.6, 10.6, 86, 3.2), L=(-3.0, 0.6, 0, None), ball=(1.0, 10.0), cpitch=0.56, pz=21.8)                      # toe flicks out, no commitment
    d.at(7, R=(1.8, 9.0, 60, 3.8), L=(-3.0, 0.4, 0, None), ball=(2.2, 14.0), cpitch=0.44)
    d.at(8, R=(2.4, 4.0, 20, None), ball=(3.0, 17.0), cpitch=0.36)
    for f in range(9, 18): stance(d, f, sw=math.sin(f * 1.4), ball=(3.0 + 0.3 * (f - 8), 17.0 + 1.6 * (f - 8)))
    d.arms(5, (0.2, 0.7, 0.9, 0.5), (0.9, 1.0, 1.2, 0.7))
    d.m.events = {'strike': 6}
    return d.build()


@move('DF04', 'Intercept Lane')
def df04():
    d = Dr(20, speed=0.0)
    # eyes on the passer, a quick step across, the boot cuts the ball out as it rolls through
    for f in range(0, 4): stance(d, f, hyaw=0.6, ball=(16.0 - 1.4 * f, 7.0, 3.0))
    d.at(4, R=(3.4, 1.0, 10, None), L=(-2.4, 0.0, 0, None), ball=(10.4, 7.0), cpitch=0.4, hyaw=0.5, croll=0.25, pz=22.2)
    d.at(5, R=(5.0, 4.0, 30, 4.0), L=(-1.6, 1.0, 0, None), ball=(8.4, 7.0), cpitch=0.4, hyaw=0.4, croll=0.3, pz=21.8)
    d.at(6, R=(5.6, 7.0, 55, 3.2, -1.0, 0.1), L=(-1.0, 1.2, 0, None), ball=(6.2, 7.0), cpitch=0.44, hyaw=0.3, croll=0.34, pz=21.6)   # stretches across and meets it
    d.at(7, R=(4.4, 8.8, 40, 3.6, -0.8), L=(-1.4, 1.4, 0, None), ball=(5.6, 12.0), cpitch=0.4, croll=0.25)
    d.at(8, R=(3.0, 5.0, 10, None), ball=(5.4, 16.0), cpitch=0.34)
    d.lateral(f4=0.8, f6=0.4, f8=0.0)
    for f in range(9, 20): stance(d, f, ball=(5.4, 16.0 + 1.8 * (f - 8)))
    d.arms(5, (0.8, 1.1, 1.2, 0.8), (0.2, 0.9, 0.8, 0.6))
    d.m.events = {'strike': 6}
    return d.build()


@move('DF05', 'Block Lane')
def df05():
    d = Dr(22, speed=0.0); hidden(d)
    # slides across to the shooter's line and makes himself wide: legs apart, arms spread, chest square, braced
    for f in range(0, 5): stance(d, f, sw=math.sin(f * 1.4), hyaw=0.5)
    for f in range(5, 10):
        u = (f - 5) / 4.0
        d.at(f, R=(3.0 + 0.6 * u, 1.0, 0, None if f % 2 else 1.6), L=(-3.0 - 0.6 * u, 0.0, 0, None), pz=22.2 - 0.6 * u, cpitch=0.2, hpitch=0.2, croll=0.2 * (1 - u))
        d.arms(f, (0.9, 1.2, 1.3, 1.0), (0.9, 1.2, 1.3, 1.0))
    for f in range(10, 22):
        d.at(f, R=(3.6, 1.0, 0, None), L=(-3.6, 0.0, 0, None), pz=21.6 + 0.2 * math.sin(f), cpitch=0.16, hpitch=0.2)
        d.arms(f, (1.1, 1.35, 1.5, 1.2), (1.1, 1.35, 1.5, 1.2))
    d.lateral(f4=0.0, f6=1.4, f9=0.0)
    return d.build()


@move('DF06', 'Tactical Foul')
def df06():
    d = Dr(22, speed=2.0); run(d, 0, 5, 0.25)
    # chases, clips the runner's heel with a trailing leg, then holds a hand up: "sorry"
    d.at(6, R=(3.0, 8.0, 40, 4.0), L=(-2.4, 1.0, 20, None), cpitch=0.45, pz=23.4)
    d.at(7, R=(4.4, 11.0, 30, 3.0, -0.3, 0.2), L=(-2.4, 1.0, 20, None), cpitch=0.6, pz=22.6, croll=-0.2)                      # leg shoots out sideways at the ankle
    d.at(8, R=(5.0, 12.4, 25, 3.0), L=(-2.4, 2.0, 20, None), cpitch=0.6, pz=22.2, croll=-0.25, hpitch=0.5)
    d.at(9, R=(3.4, 9.0, 20, 4.0), L=(-2.0, 3.0, 10, None), cpitch=0.5, pz=23.0)
    for f in range(10, 22): stance(d, f, sw=0.0, hpitch=0.2)
    for f in range(12, 22): d.arms(f, (2.4, 0.5, 2.7, 0.3), (0.5, 0.7, 1.2, 0.4))
    d.arms(7, (0.6, 1.0, 1.0, 0.7), (1.0, 1.2, 1.4, 1.0))
    d.speed(f0=2.0, f9=0.6, f11=0.0)
    return d.build()


@move('DF07', 'Recovery Sprint')
def df07():
    d = Dr(18, speed=3.4); run(d, 0, 17, lean=0.4, fx=1.1)
    for f in range(18): d.m.k(f, hyaw=0.55 * math.sin(f * 0.5), hpitch=0.0); d.arms(f, None, None)
    return d.build()


@move('DF08', 'Double Team')
def df08():
    d = Dr(22, speed=3.0); run(d, 0, 7, lean=0.4, fx=0.9)
    # sprints in, brakes hard and squeezes in next to the first defender
    d.at(8, R=(2.6, 4.0, 20, None), L=(-2.6, -1.0, 0, None), pz=22.6, cpitch=0.5)
    for f in range(9, 22):
        u = min(1.0, (f - 9) / 3.0)
        d.at(f, R=(2.8, 1.0 + 1.5 * (1 - u), 0, None), L=(-2.8, -1.0, 0, None), pz=22.4 - 0.4 * u, cpitch=0.34, hpitch=0.3, croll=0.05 * math.sin(f))
        d.arms(f, (0.8, 1.1, 1.3, 0.8), (0.8, 1.1, 1.3, 0.8))
    d.speed(f0=3.0, f7=3.0, f9=1.0, f12=0.0); d.fx = {0: 0.9, 8: 0.8, 10: 0.0}
    d.turn(**{'f0': 0.0, 'f5': -0.4, 'f10': -0.4})
    return d.build()


@move('DF09', 'Offside Trap')
def df09():
    d = Dr(24, speed=0.0); hidden(d)
    # arm straight up, head along the line, the whole line steps up two strides together and freezes
    for f in range(0, 5): stance(d, f, hpitch=0.0, hyaw=0.7)
    run(d, 5, 12, lean=0.0, cad=0.6); d.speed(f0=0.0, f5=0.4, f8=1.6, f12=1.6, f14=0.0)
    for f in range(13, 24): stance(d, f, hpitch=0.0, hyaw=0.7 * math.sin(f * 0.3))
    for f in range(0, 24): d.arms(f, (2.7, 0.2, 3.0, 0.1), (0.5, 0.6, 1.0, 0.4))
    for f in range(5, 13): d.m.k(f, hyaw=0.7)
    return d.build()


@move('DF10', 'Jockey')
def df10():
    d = Dr(24, speed=-1.0); hidden(d)
    shuffle(d, 0, 23, per=4, low=0.8)                                                           # side-on, low, small busy steps, giving ground
    d.speed(f0=-1.2, f23=-1.2)
    for f in range(24): d.m.k(f, hyaw=-0.4, pyaw=0.5, cyaw=0.3); d.arms(f, (0.9, 1.1, 1.3, 0.8), (0.9, 1.1, 1.3, 0.8))
    return d.build()


@move('DF11', 'Press Trigger')
def df11():
    d = Dr(20, speed=0.0); hidden(d)
    for f in range(0, 4): stance(d, f, low=0.8, hpitch=0.45)
    d.at(4, R=(2.8, -1.0, 0, None), L=(-2.8, 2.5, 10, None), pz=21.4, cpitch=0.55)
    burst(d, 5, 13, 0.5)
    for f in range(5, 14): d.m.k(f, bvis=0.0)
    for f in range(14, 20): stance(d, f, low=0.6, hpitch=0.4)
    for f in range(14, 20): d.arms(f, (0.9, 1.1, 1.3, 0.8), (0.9, 1.1, 1.3, 0.8))
    d.speed(f0=0.0, f4=0.8, f6=3.0, f12=3.2, f15=0.2); d.fx = {0: 0.0, 5: 0.8, 11: 1.1, 14: 0.0}
    return d.build()


@move('DF12', 'Shirt Tug')
def df12():
    d = Dr(22, speed=2.2); run(d, 0, 5, 0.3)
    d.at(6, R=(3.0, 7.0, 30, 4.0), L=(-2.4, 1.0, 20, None), cpitch=0.5, croll=-0.15)
    for f in range(6, 12): d.arms(f, (1.5, 0.35, 1.55, 0.1), (0.8, 0.8, 1.2, 0.6))                              # arm reaches out for the shirt
    d.at(9, R=(2.0, 5.0, 10, None), L=(-2.4, 1.0, 0, None), cpitch=0.2, croll=0.15, ppitch=-0.1, pz=23.6)
    for f in range(9, 14): d.arms(f, (0.9, 0.5, 1.0, 0.3), (0.8, 0.8, 1.2, 0.6)); d.m.k(f, cpitch=-0.1, croll=0.2)  # hauls back, leaning away
    run(d, 14, 21, 0.1, cad=0.8)
    d.speed(f0=2.2, f8=1.0, f11=0.6, f14=1.8)
    return d.build()


@move('DF13', 'Shoulder Charge')
def df13():
    d = Dr(20, speed=3.0); run(d, 0, 5, 0.3)
    d.at(6, R=(2.6, 5.0, 20, None), L=(-2.6, 0.0, 0, None), cpitch=0.2, croll=-0.3, pz=23.2, cyaw=-0.3, pyaw=-0.1)
    d.at(7, R=(2.8, 6.0, 10, None), L=(-3.0, -1.0, 0, None), cpitch=0.2, croll=-0.55, proll=-0.25, cyaw=-0.5, pyaw=-0.2, pz=22.6, hyaw=0.4)   # shoulder dips and drives
    d.at(8, R=(2.6, 5.0, 10, None), L=(-3.2, 0.0, 0, None), cpitch=0.25, croll=-0.6, proll=-0.3, cyaw=-0.55, pz=22.4)
    d.at(9, R=(2.4, 4.0, 0, None), L=(-3.0, 0.0, 0, None), cpitch=0.2, croll=-0.3, cyaw=-0.3, pz=22.8)
    for f in range(6, 10): d.arms(f, (0.4, 0.5, 1.4, 0.2), (0.3, 0.4, 1.2, 0.2))                                  # arms tucked, shoulder leads
    run(d, 10, 19, 0.1)
    d.speed(f0=3.0, f6=2.6, f8=1.2, f10=1.8)
    return d.build()


@move('DF14', 'Clear the Lines')
def df14():
    m = S.sh22(); m.N = 22
    for f in range(0, 12): m.k(f, bx=2.0, by=11.5, bz=3.0, bvis=1.0)
    c = M.aim_ball(m, 12, 'boot', 'R', vin=(0, 0, 0), pre=0)
    for f in range(0, 12): m.k(f, bx=c[0], by=c[1], bz=c[2], bvis=1.0)
    m.ball(13, S.fly(c, (0.4, 6.4, 2.4), 9, g=0.18), spin_x=-1.2)
    for f in range(16, 22):
        m.arms(f, 'R', 0.3, 0.4, 0.7, 0.3); m.arms(f, 'L', 0.3, 0.4, 0.7, 0.3)
    return m


@move('DF15', 'Last Ditch Block')
def df15():
    d = Dr(22, speed=2.6); run(d, 0, 4, 0.3); hidden(d)
    d.at(5, R=(2.4, 6.0, 20, 5.0), L=(-2.4, 1.0, 10, None), cpitch=0.4, pz=24.0)
    d.at(6, R=(2.0, 3.0, 10, 7.0), L=(-2.0, -1.0, 10, 7.0), pz=26.0, cpitch=0.1, croll=-0.5, proll=-0.4, hyaw=-0.8)             # hurls himself across the line
    d.at(7, R=(2.6, 1.0, 20, 14.0), L=(-1.6, -3.0, 20, 13.0), pz=23.0, cpitch=0.0, croll=-0.95, proll=-0.8, hyaw=-0.9)
    d.at(8, R=(3.0, 0.0, 20, 14.0), L=(-1.0, -4.0, 20, 12.0), pz=19.0, cpitch=0.0, croll=-1.2, proll=-1.1, hyaw=-0.9)
    d.at(9, R=(3.4, -0.5, 20, 9.0), L=(-0.6, -4.5, 20, 8.0), pz=14.0, cpitch=0.0, croll=-1.4, proll=-1.3, hyaw=-0.9)
    for f in range(10, 22): d.at(f, R=(3.6, -0.5, 20, 5.0), L=(-0.4, -4.4, 20, 5.0), pz=8.0, cpitch=0.0, croll=-1.45, proll=-1.4, hyaw=-0.9)
    for f in range(6, 22): d.arms(f, (1.5, 0.15, 1.9, 0.1), (1.4, 0.15, 1.8, 0.1))                                  # arms crossed over the face
    d.speed(f0=2.6, f5=2.2, f9=1.2, f12=0.0)
    return d.build()


@move('DF16', 'Header Clear')
def df16():
    m = S.sh12()
    c = M.aim_ball(m, 12, 'head', vin=(1.4, -2.6, -1.0), pre=12)
    m.ball(13, S.fly(c, (1.4, 3.6, 2.8), 10, g=0.2), spin_x=1.2)
    for f in (10, 11, 12): m.arms(f, 'R', 0.6, 1.0, 0.8, 0.8); m.arms(f, 'L', 0.6, 1.0, 0.8, 0.8)
    return m


@move('DF17', 'Cut Out Cross')
def df17():
    d = Dr(22, speed=0.0)
    for f in range(0, 4): stance(d, f, hyaw=0.7, ball=(16.0 - 0.8 * f, 12.0, 24.0 - 1.4 * f))
    d.at(4, R=(3.0, 1.0, 10, None), L=(-2.4, 0.0, 0, None), ball=(12.4, 12.0, 19.0), cpitch=0.3, hyaw=0.6, croll=0.25)
    d.at(5, R=(3.6, 4.0, 40, 8.0), L=(-2.4, 1.0, 10, 5.0), ball=(10.4, 11.6, 17.0), cpitch=0.2, hyaw=0.5, croll=0.3, pz=26.0)
    d.at(6, R=(4.6, 7.0, 45, 16.0, -0.8, 0.5), L=(-2.4, 0.0, 10, 8.0), ball=(8.6, 10.6, 15.0), cpitch=0.1, hyaw=0.3, croll=0.38, pz=28.0)    # leaps and stretches the leg across
    d.at(7, R=(5.4, 8.6, 40, 14.4, -0.6, 0.4), L=(-2.4, -1.0, 20, 9.0), ball=(7.6, 10.0, 14.2), cpitch=0.1, croll=0.3, pz=27.0)
    d.at(8, R=(4.4, 8.0, 30, 10.0), L=(-2.0, 0.0, 20, 6.0), ball=(7.0, 14.0, 14.0), cpitch=0.2, croll=0.2, pz=25.0)
    d.at(9, R=(3.4, 5.0, 10, None), L=(-2.4, 1.0, 5, None), ball=(7.0, 16.0, 10.0), cpitch=0.3, pz=23.0)
    d.lateral(f4=0.8, f6=1.0, f9=0.0)
    for f in range(10, 22): stance(d, f, ball=(7.0, 17.0 + 2.0 * (f - 9), 3.0))
    d.arms(6, (0.9, 1.2, 1.3, 1.0), (0.4, 0.9, 1.0, 0.6))
    d.m.events = {'strike': 6}
    return d.build()


@move('DF18', 'Snuff Out')
def df18():
    d = Dr(20, speed=0.0)
    for f in range(0, 4): stance(d, f, ball=(1.0, 12.0 - 0.6 * f))
    d.at(4, R=(2.8, 3.0, 10, None), L=(-2.8, -1.0, 0, None), ball=(1.0, 9.6), pz=21.4, cpitch=0.5, hpitch=0.55)
    d.at(5, R=(2.4, 7.0, 15, None), L=(-3.0, 2.0, 10, 3.0), ball=(1.0, 9.8), pz=19.6, cpitch=0.72, hpitch=0.6, ppitch=0.3)       # springs in low
    d.at(6, R=(2.6, 9.6, 30, 3.0), L=(-3.0, 4.0, 10, None), ball=(1.0, 10.0), pz=18.6, cpitch=0.82, hpitch=0.6, ppitch=0.4)   # chest down, arms wide, shuts the space
    d.at(7, R=(2.6, 9.8, 30, 3.0), L=(-3.0, 4.4, 10, None), ball=(1.4, 13.0), pz=18.8, cpitch=0.78)
    for f in range(8, 20):
        u = min(1.0, (f - 8) / 4.0); stance(d, f, low=0.0, pz=18.8 + 3.8 * u, cpitch=0.78 - 0.48 * u, ball=(1.4 + 0.3 * (f - 8), 13.0 + 1.6 * (f - 8)))
    for f in (5, 6, 7): d.arms(f, (1.0, 1.0, 1.3, 0.8), (1.0, 1.0, 1.3, 0.8))
    d.speed(f0=0.0, f4=0.6, f6=1.2, f8=0.2)
    d.m.events = {'strike': 6}
    return d.build()


@move('DF19', 'Shadow Marking')
def df19():
    d = Dr(24, speed=1.8); hidden(d)
    run(d, 0, 23, lean=0.12, cad=0.75)
    for f in range(24):
        d.m.k(f, hyaw=0.9, pyaw=0.25, cyaw=0.3, hpitch=0.1)
        d.arms(f, (1.2, 0.5, 1.45, 0.2), (0.4, 0.5, 1.0, 0.3))                                                      # one hand on the striker's back
    return d.build()


@move('DF20', 'Zonal Cover')
def df20():
    d = Dr(28, speed=0.0); hidden(d)
    for f in range(28):
        sw = math.sin(f * 0.45)
        stance(d, f, hyaw=0.9 * math.sin(f * 0.32), hpitch=0.1, sw=sw)                                              # scanning left and right, weight shifting
        d.m.k(f, R_ax=2.8 + 0.5 * sw, L_ax=-2.8 + 0.5 * sw if False else -2.8)
        d.arms(f, (0.8 + 0.2 * sw, 1.0, 1.2, 0.7), (0.8 - 0.2 * sw, 1.0, 1.2, 0.7))
    d.lateral(f0=0.0)
    return d.build()


@move('DF21', 'Drop Deep')
def df21():
    d = Dr(22, speed=-2.4); hidden(d)
    d.carry(0, 21, lean=-0.05, cad=-1.0, ball=False)
    for f in range(22): d.m.k(f, bvis=0.0, hyaw=0.9, hpitch=0.1, pz=23.2, cpitch=0.1); d.arms(f, (0.6, 0.8, 1.0, 0.5), (0.9, 1.0, 1.3, 0.7))   # backpedalling, looking over the shoulder
    d.speed(f0=-2.4, f21=-2.4); d.fx = {0: 0.5, 21: 0.5}
    return d.build()


@move('DF22', 'Step Up')
def df22():
    d = Dr(24, speed=0.0); hidden(d)
    for f in range(0, 4): stance(d, f, hyaw=-0.5)
    run(d, 4, 13, lean=0.1, cad=0.7)
    d.speed(f0=0.0, f4=0.6, f7=2.2, f13=2.0, f15=0.0)
    for f in range(14, 24): stance(d, f, hyaw=-0.6)
    for f in range(0, 24): d.arms(f, (0.7, 0.9, 1.1, 0.6), (2.5, 0.4, 2.8, 0.3) if 3 < f < 18 else (0.7, 0.9, 1.1, 0.6))     # one hand up: "up, up"
    for f in range(4, 14): d.m.k(f, hyaw=-0.5, bvis=0.0)
    return d.build()


@move('DF23', 'Ball Hawk')
def df23():
    d = Dr(24, speed=0.0)
    for f in range(0, 6): stance(d, f, hyaw=0.2 * math.sin(f), ball=(10.0 - 0.2 * f, 18.0, 16.0))
    d.at(6, R=(2.6, 0.0, 20, None), L=(-2.8, 1.0, 0, None), ball=(9.0, 17.0, 17.0), low=0.0, pz=21.4, cpitch=0.5, hpitch=-0.1)    # reads it, coils
    d.at(7, R=(2.6, 4.0, 30, 6.0), L=(-2.8, 2.0, 20, 4.0), ball=(8.0, 15.0, 18.0), pz=27.0, cpitch=0.3, croll=0.2, hpitch=-0.2)    # explodes out
    d.at(8, R=(3.4, 9.0, 40, 16.0, -0.8, 0.5), L=(-2.4, 0.0, 20, 11.0), ball=(7.0, 13.0, 19.0), pz=29.0, cpitch=0.2, croll=0.3, hpitch=-0.2)
    d.at(9, R=(3.8, 12.0, 42, 21.0, -0.8, 0.5), L=(-2.4, -1.0, 20, 12.0), ball=(6.4, 12.4, 21.2), pz=29.4, cpitch=0.1, croll=0.34)      # leg up into the pass
    d.at(10, R=(3.4, 12.0, 30, 18.0), L=(-2.4, 0.0, 20, 9.0), ball=(6.6, 17.0, 22.0), pz=27.0, cpitch=0.2)
    d.at(11, R=(3.0, 8.0, 10, 8.0), L=(-2.4, 2.0, 15, 4.0), ball=(7.0, 22.0, 20.0), pz=25.0, cpitch=0.3)
    d.at(12, R=(2.8, 6.0, 0, None), L=(-2.6, 3.0, 0, None), ball=(7.4, 27.0, 14.0), pz=23.0, cpitch=0.4)
    d.speed(f0=0.0, f6=0.4, f8=2.4, f12=0.8, f14=0.0); d.lateral(f6=0.0, f8=1.0, f12=0.0)
    for f in range(13, 24): stance(d, f, ball=(7.6 + 0.3 * (f - 12), 28.0 + 2.0 * (f - 12), 4.0))
    for f in (8, 9, 10): d.arms(f, (0.9, 1.2, 1.3, 1.0), (0.5, 1.0, 1.0, 0.7))
    d.m.events = {'strike': 9}
    return d.build()


@move('DF24', 'Body Block')
def df24():
    d = Dr(24, speed=0.0); hidden(d)
    for f in range(24):
        sw = math.sin(f * 0.7)
        d.at(f, R=(3.2, 0.8, 0, None), L=(-3.2, -0.6, 0, None), pz=22.0, cpitch=0.2, hpitch=0.2, pyaw=0.7, cyaw=0.8, hyaw=-0.5, croll=0.08 * sw)   # side-on, wide, leaning into the runner
        d.arms(f, (1.1 + 0.1 * sw, 1.3, 1.5, 1.1), (0.4, 0.6, 1.4, 0.3))
    d.lateral(f0=0.0)
    return d.build()


@move('DF25', 'Shadow Press')
def df25():
    d = Dr(24, speed=2.0); hidden(d)
    run(d, 0, 23, lean=0.3, cad=0.9, fx=0.3)
    d.turn(**{'f0': 0.0, 'f23': -0.9})
    for f in range(24): d.m.k(f, hyaw=0.5); d.arms(f, (0.6, 0.8, 1.0, 0.6), (1.55, 0.35, 1.55, 0.15))        # curved run, arm pointing along the passing line
    return d.build()


@move('DF26', 'Rotate Cover')
def df26():
    d = Dr(26, speed=2.0); hidden(d)
    run(d, 0, 25, lean=0.2, cad=0.9)
    d.turn(**{'f0': 0.5, 'f8': 0.5, 'f13': -0.5, 'f25': -0.5})                                                   # peels one way, then cuts across into the vacated space
    for f in range(26): d.m.k(f, hyaw=0.6 if f < 9 else -0.4)
    for f in range(0, 10): d.arms(f, (0.5, 0.8, 1.0, 0.5), (1.55, 0.6, 1.55, 0.3))                                # points: "you go"
    return d.build()


@move('DF27', "Poacher's Guard")
def df27():
    d = Dr(24, speed=0.0); hidden(d)
    for f in range(24):
        ph = 2 * PI * f / 6.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.8, 1.0, 0, 2.0 + 3.0 * a) if a > 0.05 else (2.8, 1.0, 0, None), L=(-2.8, -0.6, 0, 2.0 + 3.0 * b) if b > 0.05 else (-2.8, -0.6, 0, None),
             pz=21.8, cpitch=0.34, hpitch=0.2, hyaw=0.8 * math.sin(f * 0.3), croll=0.06 * math.sin(ph))
        d.arms(f, (1.2, 0.4, 1.45, 0.2), (0.6, 0.9, 1.2, 0.6))
    d.lateral(f0=0.0, f4=0.8, f8=-0.8, f12=0.8, f16=-0.8, f20=0.8, f23=0.0)                                       # side-steps with the striker, hand on his back
    return d.build()


@move('DF28', 'Rescue Tackle')
def df28():
    d = Dr(22, speed=2.8); run(d, 0, 4, 0.35)
    for f in range(0, 8): d.m.k(f, bx=1.2, by=12.0 + 2.8 * f - 0.0, bz=3.0, bvis=1.0)
    d.at(5, R=(2.4, 7.0, 20, None), L=(-2.4, 0.0, 10, 4.0), ball=(1.0, 24.0), cpitch=0.5, pz=22.6)
    d.at(6, R=(1.8, 13.0, 45, 3.0), L=(-3.0, -3.0, 20, None), ball=(1.0, 26.0), cpitch=0.7, ppitch=0.3, pz=19.0)              # long desperate lunge
    d.at(7, R=(1.4, 17.4, 55, 3.0, -0.8, 0.2), L=(-3.0, -6.0, 20, None), ball=(1.0, 27.0), cpitch=0.9, ppitch=0.4, pz=16.4, hpitch=0.4)   # fully stretched, toe on the ball
    d.at(8, R=(1.4, 18.4, 40, 3.4), L=(-2.8, -6.4, 20, None), ball=(1.6, 24.0), cpitch=0.9, ppitch=0.4, pz=16.0)
    d.at(9, R=(1.8, 14.0, 20, None), L=(-2.6, -2.0, 20, None), ball=(2.0, 20.0), cpitch=0.7, pz=18.0)
    for f in range(10, 22): d.at(f, R=(2.4, 6.0 - 0.3 * (f - 10), 10, None), L=(-2.4, 1.0, 10, None), ball=(2.4, 18.0 + 1.0 * (f - 10)), cpitch=0.5 - 0.03 * (f - 10), pz=19.5 + 0.35 * (f - 10))
    for f in (6, 7, 8): d.arms(f, (-0.6, 0.9, -0.2, 0.8), (-0.4, 1.0, 0.0, 0.8))                                    # arms thrown back for balance
    d.speed(f0=2.8, f5=2.4, f8=1.2, f12=0.4)
    d.m.events = {'strike': 7}
    return d.build()


@move('DF29', 'Sweep')
def df29():
    d = Dr(22, speed=3.2); run(d, 0, 9, lean=0.4, fx=1.0)
    for f in range(0, 12): d.m.k(f, bx=1.2, by=26.0 + 2.0 * f, bz=3.0, bvis=1.0)
    d.at(10, R=(2.4, 6.0, 40, 5.0), L=(-2.4, 0.0, 10, None), ball=(1.0, 26.0), cpitch=0.5, pz=23.4)
    d.at(11, R=(1.8, 11.0, 70, 3.6), L=(-3.0, 2.0, 10, None), ball=(1.0, 24.0), cpitch=0.6, pz=22.6)
    d.at(12, R=(1.4, 15.0, 80, 3.2), L=(-3.0, 3.0, 10, None), ball=(1.0, 24.0), cpitch=0.6, pz=22.2)                         # clears it at full stretch
    d.at(13, R=(1.2, 17.0, 60, 4.6), L=(-3.0, 4.0, 10, None), ball=(1.0, 30.0, 8.0), cpitch=0.5, pz=22.6)
    d.at(14, R=(1.6, 14.0, 30, 6.0), L=(-3.0, 4.0, 10, None), ball=(1.0, 38.0, 14.0), cpitch=0.4, pz=23.4)
    for f in range(15, 22): d.m.k(f, bx=1.0, by=46.0 + 4 * (f - 15), bz=10.0, bvis=1.0)
    run(d, 15, 21, 0.1, cad=0.7)
    d.speed(f0=3.2, f10=2.6, f13=1.2, f15=0.8, f21=0.4); d.fx = {0: 1.0, 9: 1.0, 11: 0.0}
    d.m.events = {'strike': 12}
    return d.build()


@move('DF30', 'Clean Sheet Wall')
def df30():
    d = Dr(24, speed=0.0); hidden(d)
    for f in range(24):
        sw = math.sin(f * 0.5)
        d.at(f, R=(3.4, 0.6, 0, None), L=(-3.4, -0.4, 0, None), pz=22.2 + 0.25 * sw, cpitch=0.12, hpitch=0.1)
        d.arms(f, (1.7, 0.9, 2.6, 0.3), (1.7, 0.9, 2.6, 0.3))                                                          # arms raised and braced: a wall
    return d.build()


@move('DF31', 'Fox in the Box')
def df31():
    d = Dr(24, speed=0.0); hidden(d)
    for f in range(24):
        sw = math.sin(f * 0.8)
        d.at(f, R=(2.6, -0.4, 0, None), L=(-2.6, -1.4 + 0.5 * sw, 0, None), pz=21.8, cpitch=0.42, hpitch=-0.1, hyaw=-0.9, pyaw=0.2, croll=0.1 * sw)     # tight against the striker, looking over at the ball
        d.arms(f, (1.5, 0.3, 1.5, 0.2), (0.7, 0.9, 1.2, 0.6))
    d.lateral(f0=0.0)
    return d.build()


@move('DF32', 'Backheel Clear')
def df32():
    m = S.sh30()
    c = np.array([m.keys[12]['bx'], m.keys[12]['by'], m.keys[12]['bz']])
    m.ball(13, [(1.8 + 0.3 * i, 5.0 - 2.4 * i, 3.0 + 2.2 * i - 0.12 * i * i) for i in range(10)], spin_x=-1.6)             # flicked up and away off the line
    return m


@move('DF33', 'Trap the Winger')
def df33():
    d = Dr(24, speed=-0.6); hidden(d)
    shuffle(d, 0, 23, per=4, low=0.6)
    d.lateral(f0=0.8, f23=0.8); d.speed(f0=-0.8, f23=-0.8)
    for f in range(24): d.m.k(f, pyaw=-0.7, cyaw=-0.6, hyaw=0.5); d.arms(f, (1.5, 1.2, 1.5, 1.0), (0.5, 0.8, 1.2, 0.6))   # angled to show him the touchline, arm out as a wall
    return d.build()


@move('DF34', 'Tight Squeeze')
def df34():
    d = Dr(24, speed=0.6); hidden(d)
    for f in range(24):
        ph = 2 * PI * f / 6.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.2, 1.6 + 0.8 * a, 0, 1.6 + 2.4 * a) if a > 0.05 else (2.2, 1.6, 0, None), L=(-2.2, 0.6 + 0.8 * b, 0, 1.6 + 2.4 * b) if b > 0.05 else (-2.2, 0.6, 0, None),
             pz=20.6, cpitch=0.5, hpitch=0.5, croll=0.05 * math.sin(ph))
        d.arms(f, (0.5, 0.45, 1.5, 0.3), (0.5, 0.45, 1.5, 0.3))                                                      # elbows in, crowding the space
    return d.build()


@move('DF35', 'Crunching Block')
def df35():
    d = Dr(24, speed=2.4); run(d, 0, 4, 0.3)
    for f in range(0, 9): d.m.k(f, bx=1.0, by=14.0, bz=3.0, bvis=1.0)
    d.at(5, R=(2.4, 6.0, 20, 5.0), L=(-2.4, 1.0, 10, None), ball=(1.0, 14.0), cpitch=0.3, pz=23.6)
    d.at(6, R=(1.6, 9.0, -10, 4.0), L=(-2.4, 0.0, 10, None), ball=(1.0, 14.0), cpitch=-0.2, ppitch=-0.2, pz=21.0)             # drops back onto the heel, sole first
    d.at(7, R=(1.2, 13.2, -35, 4.0), L=(-3.0, -2.0, 20, 4.0), ball=(1.0, 14.0), cpitch=-0.45, ppitch=-0.4, pz=17.0)           # studs through the ball
    d.at(8, R=(1.2, 14.4, -40, 4.0), L=(-3.0, -3.0, 20, 4.0), ball=(1.6, 18.0, 5.0), cpitch=-0.55, ppitch=-0.5, pz=13.0)
    for f in range(9, 24): d.at(f, R=(1.2, 14.0, -35, 4.0), L=(-3.0, -3.4, 20, 4.0), ball=(2.0 + 0.2 * (f - 9), 22.0 + 2.2 * (f - 9), 3.0), cpitch=-0.6, ppitch=-0.55, pz=9.0 - 0.1 * (f - 9))
    for f in range(6, 24): d.arms(f, (-0.4, 0.9, -0.2, 0.8), (-0.3, 0.9, -0.1, 0.8))                                    # propped on his hands, sliding
    d.speed(f0=2.4, f5=2.2, f8=1.6, f14=0.2)
    d.m.events = {'strike': 7}
    return d.build()


def build(ids=None):
    out = []
    for id_, (label, fn) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); name = id_.lower() + '_' + label.lower().replace(' ', '_').replace("'", '')
        m.save(name, label, 'auto-generated by sprites/moves_defend.py'); out.append((id_, name))
    return out


if __name__ == '__main__':
    for id_, name in build(sys.argv[1:] or None): print(id_, name)
