"""The 25 KEEPER skill animations (GK01-GK25). Run:  python moves_keeper.py [id ...]
Same framework as the dribbles / defend moves (player's own frame, forward +y; dives go to the player's RIGHT, the game mirrors for left dives).
The ball is the game's: here it is only a preview. Incoming balls are authored in world coords (W), carried balls relative to the root (H)."""
import math, sys
from moves_dribble import Dr, burst, PI, pch
import moves_shot as S

MOVES = {}
READY = (1.15, 0.45, 1.55, 0.25)        # hands low and forward, palms to the ball
UP = (2.7, 0.2, 3.0, 0.1)


def move(id_, label):
    def deco(fn):
        MOVES[id_] = (label, fn); return fn
    return deco


class K(Dr):
    def __init__(s, N, speed=0.0):
        super().__init__(N, speed=speed); s.W = {}; s.H = {}; s.hit = None
        for f in range(N): s.m.k(f, bvis=0.0)

    def world(s, f, x, y, z=3.0): s.W[f] = (x, y, z)
    def held(s, f, x=0.0, y=5.0, z=14.0): s.H[f] = (x, y, z)

    def shot(s, f_hit, p_hit, start=None, f0=0, out=(0.0, 3.0, 2.0), after=None, g=0.2):
        """ball runs from `start` at f0 to p_hit at f_hit, then leaves with velocity `out` per frame (until the end)"""
        start = start or (p_hit[0] * 0.6, 34.0, max(p_hit[2] * 0.7, 2.5))
        for f in range(f0, f_hit + 1):
            u = (f - f0) / max(1, f_hit - f0); s.world(f, *(start[i] + (p_hit[i] - start[i]) * u for i in range(3)))
        for i, q in enumerate(S.fly(p_hit, out, s.N - f_hit - 1, g=g)): s.world(f_hit + 1 + i, *q)
        s.hit = f_hit; s.m.events = {'strike': f_hit}

    def done(s):
        m = s.build()
        for f, (x, y, z) in s.W.items(): m.keys[f].update(bx=x, by=y, bz=z, bvis=1.0)
        for f, (x, y, z) in s.H.items():
            k = m.keys[f]; m.keys[f].update(bx=k['root_x'] + x, by=k['root_y'] + y, bz=z, bvis=1.0)
        return m


def ready(d, f, bounce=0.0, low=0.0, **kw):
    base = dict(pz=21.8 - low + bounce, cpitch=0.5 + 0.1 * low, hpitch=0.25)
    base.update(kw)
    d.at(f, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), **base); d.arms(f, READY, READY)


def idle(d, f0, f1, **kw):
    for f in range(f0, f1 + 1): ready(d, f, bounce=0.35 * math.sin(f * 0.7), **kw)


def dive(d, f0, h=30.0, reach=(2.35, 0.5, 2.8, 0.2), lt=4.2, lie=8, roll=1.45):
    """coil, push off, flight, land and lie; returns the first frame after the lie. Save frame = f0+3."""
    d.at(f0, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=19.8, cpitch=0.7, hpitch=0.2, croll=-0.1); d.arms(f0, READY, READY)
    d.at(f0 + 1, R=(4.2, -1.4, 20, 2.0), L=(-2.4, 0.4, 0, 5.0), pz=24.0, cpitch=0.4, croll=-0.5, proll=-0.35, hyaw=-0.3); d.arms(f0 + 1, (1.9, 0.45, 2.3, 0.3), (1.9, 0.45, 2.3, 0.3))
    d.at(f0 + 2, R=(3.4, -3.0, 20, 9.0), L=(-1.4, -2.5, 20, 11.0), pz=h - 2, cpitch=0.1, croll=-0.9, proll=-0.8, hyaw=-0.7); d.arms(f0 + 2, reach, reach)
    d.at(f0 + 3, R=(3.4, -3.5, 20, 12.0), L=(-1.0, -3.5, 20, 12.0), pz=h, cpitch=0.0, croll=-1.15, proll=-1.05, hyaw=-0.8); d.arms(f0 + 3, reach, reach)
    d.at(f0 + 4, R=(3.4, -3.0, 20, 9.0), L=(-0.8, -3.8, 20, 9.0), pz=h * 0.55, cpitch=0.0, croll=-1.35, proll=-1.25, hyaw=-0.85); d.arms(f0 + 4, reach, reach)
    for f in range(f0 + 5, f0 + 5 + lie):
        d.at(f, R=(3.6, -3.0, 20, 5.0), L=(-0.5, -4.0, 20, 5.0), pz=8.0, cpitch=0.0, croll=-roll, proll=-roll + 0.05, hyaw=-0.85); d.arms(f, reach, reach)
    e = f0 + 5 + lie
    d.lateral(**{f'f{f0}': 0.0, f'f{f0 + 1}': lt * 0.6, f'f{f0 + 2}': lt, f'f{f0 + 4}': lt * 0.5, f'f{f0 + 5}': 0.3, f'f{f0 + 6}': 0.0})
    return e


def getup(d, f0, n=6):
    for i in range(n):
        u = (i + 1) / n; f = f0 + i
        d.at(f, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=8.0 + 13.8 * u, cpitch=0.5 * u, croll=-1.45 * (1 - u), proll=-1.4 * (1 - u), hyaw=-0.85 * (1 - u), hpitch=0.25 * u)
        d.arms(f, READY, READY)
    return f0 + n


# --------------------------------------------------------------------------------------------------
@move('GK01', 'Set Stance')
def gk01():
    d = K(20)
    for f in range(20):                                           # settles into the ready crouch, bouncing on his toes, hands out
        u = min(1.0, f / 6.0); ph = math.sin(f * 0.9)
        d.at(f, R=(3.0 + 0.4 * u, 0.8, 0, 2.0 if ph > 0.5 else None), L=(-3.0 - 0.4 * u, -0.6, 0, 2.0 if ph < -0.5 else None), pz=23.0 - 1.8 * u + 0.4 * ph, cpitch=0.1 + 0.5 * u, hpitch=0.25 * u)
        d.arms(f, (0.5 + 0.65 * u, 0.7 - 0.25 * u, 1.1 + 0.45 * u, 0.5 - 0.25 * u), (0.5 + 0.65 * u, 0.7 - 0.25 * u, 1.1 + 0.45 * u, 0.5 - 0.25 * u))
    return d.done()


@move('GK02', 'Reach Dive')
def gk02():
    d = K(30); idle(d, 0, 4)
    d.shot(8, (9.5, 5.0, 22.0), start=(12.0, 36.0, 6.0), f0=0, out=(0.9, 2.6, 1.4))
    e = dive(d, 5, h=33.0, reach=(2.5, 0.5, 2.9, 0.2), lt=4.4)
    # the ball hits at f8 above; long stretch to the top corner
    getup(d, e, 30 - e) if e < 30 else None
    return d.done()


@move('GK03', 'Smother')
def gk03():
    d = K(26, 2.8); idle(d, 0, 2)
    for f in range(0, 12): d.world(f, 0.6, 30.0 - 1.6 * f, 3.0)
    burst(d, 3, 7, 0.4)
    for f in range(3, 8): d.m.k(f, bvis=0.0)
    d.speed(f0=0.0, f3=2.8, f7=2.2, f9=1.0, f12=0.0); d.fx = {0: 0.0, 3: 0.8, 8: 0.0}
    d.at(8, R=(2.8, 6.0, 20, 4.0), L=(-2.8, 0.0, 10, None), pz=21.0, cpitch=0.8, hpitch=0.3); d.arms(8, (1.2, 0.4, 1.7, 0.3), (1.2, 0.4, 1.7, 0.3))
    d.at(9, R=(2.4, 8.0, 20, 4.0), L=(-2.4, -3.0, 10, 5.0), pz=15.0, cpitch=1.0, ppitch=0.3, hpitch=0.4); d.arms(9, (1.4, 0.4, 1.9, 0.2), (1.4, 0.4, 1.9, 0.2))         # throws his body at the ball's feet
    d.at(10, R=(2.0, 6.0, 20, 4.0), L=(-2.0, -5.0, 10, 4.0), pz=10.0, cpitch=1.2, ppitch=0.4, hpitch=0.4); d.arms(10, (1.5, 0.3, 2.2, 0.1), (1.5, 0.3, 2.2, 0.1))
    for f in range(11, 26): d.at(f, R=(2.0, 5.0, 20, 4.0), L=(-2.0, -5.0, 10, 4.0), pz=9.0, cpitch=1.25, ppitch=0.4, hpitch=0.4); d.arms(f, (1.6, 0.3, 2.4, 0.1), (1.6, 0.3, 2.4, 0.1))
    for f in range(10, 26): d.world(f, 0.2, 29.0 - 1.6 * 10 + 0.0 + 14.5 * 0, 2.5)
    d.m.events = {'strike': 10}
    return d.done()


@move('GK04', 'Punch Clear')
def gk04():
    d = K(24); idle(d, 0, 3)
    d.shot(8, (1.0, 9.0, 24.0), start=(7.0, 30.0, 30.0), out=(-0.9, 2.6, 1.0))
    d.at(4, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=20.6, cpitch=0.6); d.arms(4, READY, READY)
    d.at(5, R=(3.0, 1.0, 0, 3.0), L=(-3.0, -0.4, 0, 3.0), pz=26.0, cpitch=0.3); d.arms(5, (1.7, 0.3, 2.4, 0.2), (1.7, 0.3, 2.4, 0.2))
    d.at(6, R=(3.0, 1.4, 0, 8.0), L=(-3.0, 0.4, 0, 8.0), pz=31.0, cpitch=0.1); d.arms(6, (2.2, 0.2, 2.9, 0.1), (2.2, 0.2, 2.9, 0.1))                # jumps, fists high
    d.at(7, R=(3.0, 1.8, 0, 10.0), L=(-3.0, 0.4, 0, 9.0), pz=33.0, cpitch=0.0, hpitch=-0.1); d.arms(7, (2.0, 0.2, 2.0, 0.1), (2.0, 0.2, 2.0, 0.1))
    d.at(8, R=(3.0, 1.8, 0, 10.0), L=(-3.0, 0.4, 0, 9.0), pz=33.5, cpitch=-0.1, hpitch=-0.2); d.arms(8, (1.9, 0.2, 1.65, 0.1), (1.9, 0.2, 1.65, 0.1))   # both fists drive through the ball
    d.at(9, R=(3.0, 1.0, 0, 5.0), L=(-3.0, 0.0, 0, 5.0), pz=29.0, cpitch=0.2); d.arms(9, (1.6, 0.3, 1.5, 0.2), (1.6, 0.3, 1.5, 0.2))
    d.at(10, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=23.0, cpitch=0.5); d.arms(10, READY, READY)
    for f in range(11, 24): ready(d, f, bounce=0.3 * math.sin(f))
    return d.done()


@move('GK05', 'Claim Cross')
def gk05():
    d = K(26); idle(d, 0, 3)
    d.shot(9, (0.6, 7.0, 30.0), start=(8.0, 32.0, 18.0), out=(0.0, 0.0, 0.0), g=0.0)
    d.at(4, R=(3.0, 1.0, 0, None), L=(-3.0, 0.0, 0, None), pz=20.6, cpitch=0.6); d.arms(4, READY, READY)
    d.at(5, R=(2.4, 3.0, 20, 4.0), L=(-3.0, 0.0, 0, None), pz=25.0, cpitch=0.3); d.arms(5, (2.0, 0.3, 2.6, 0.2), (2.0, 0.3, 2.6, 0.2))
    d.at(6, R=(2.2, 4.0, 20, 9.0), L=(-3.0, 1.0, 10, 9.0), pz=31.0, cpitch=0.0); d.arms(6, UP, UP)                                            # one-knee drive, hands to the sky
    d.at(7, R=(2.2, 4.5, 20, 11.0), L=(-3.0, 1.0, 10, 8.0), pz=34.0, cpitch=-0.05, hpitch=-0.35); d.arms(7, UP, UP)
    d.at(8, R=(2.2, 4.5, 20, 11.0), L=(-3.0, 1.0, 10, 8.0), pz=35.0, cpitch=-0.05, hpitch=-0.4); d.arms(8, UP, UP)
    d.at(9, R=(2.2, 4.5, 20, 10.0), L=(-3.0, 1.0, 10, 7.0), pz=35.0, cpitch=-0.05, hpitch=-0.4); d.arms(9, UP, UP)
    d.at(10, R=(2.6, 3.0, 20, 6.0), L=(-3.0, 0.6, 10, 4.0), pz=31.0, cpitch=0.1, hpitch=0.0); d.arms(10, (1.9, 0.5, 2.5, 0.3), (1.9, 0.5, 2.5, 0.3))
    d.at(11, R=(2.8, 1.0, 0, None), L=(-3.0, -0.4, 0, None), pz=21.0, cpitch=0.45); d.arms(11, (1.0, 0.6, 2.4, 0.4), (1.0, 0.6, 2.4, 0.4))     # lands with it cradled to the chest
    for f in range(12, 26): d.at(f, R=(2.8, 1.0, 0, None), L=(-3.0, -0.4, 0, None), pz=22.4, cpitch=0.2, hpitch=0.1); d.arms(f, (0.9, 0.7, 2.4, 0.5), (0.9, 0.7, 2.4, 0.5))
    for f in range(9, 12): d.W[f] = (0.6, 7.0 - 0.0, 30.0 - (f - 9) * 6)
    for f in range(12, 26): d.H[f] = (0.0, 4.2, 16.0)
    d.W = {f: v for f, v in d.W.items() if f < 12}
    d.m.events = {'strike': 9}
    return d.done()


@move('GK06', 'Sweeper Rush')
def gk06():
    d = K(24, 3.4); burst(d, 0, 9, 0.4)
    for f in range(0, 10): d.m.k(f, bvis=0.0)
    for f in range(0, 10): d.world(f, 0.8, 34.0 + 1.0 * f - 0.0, 3.0)
    d.at(10, R=(2.4, 6.0, 40, 5.0), L=(-2.4, 0.0, 10, None), pz=23.4, cpitch=0.5); d.arms(10, (-0.3, 0.9, 0.3, 0.8), (1.4, 0.8, 1.7, 0.6))
    d.at(11, R=(1.8, 11.0, 70, 3.6), L=(-3.0, 2.0, 10, None), pz=22.6, cpitch=0.6); d.arms(11, (-0.5, 0.9, 0.1, 0.8), (1.4, 0.8, 1.7, 0.6))
    d.at(12, R=(1.4, 15.0, 80, 3.2), L=(-3.0, 3.0, 10, None), pz=22.2, cpitch=0.6); d.arms(12, (-0.6, 0.9, 0.0, 0.8), (1.4, 0.8, 1.7, 0.6))
    d.at(13, R=(1.2, 17.0, 60, 4.6), L=(-3.0, 4.0, 10, None), pz=22.6, cpitch=0.5)
    d.at(14, R=(1.6, 14.0, 30, 6.0), L=(-3.0, 4.0, 10, None), pz=23.4, cpitch=0.4)
    burst(d, 15, 23, 0.1)
    for f in range(15, 24): d.m.k(f, bvis=0.0)
    d.speed(f0=3.4, f10=2.6, f13=1.0, f15=0.8, f23=0.4); d.fx = {0: 1.0, 9: 1.0, 11: 0.0}
    d.shot(12, (1.2, 18.2 + 3.6 * 0 + 0, 3.0), start=(0.8, 43.0, 3.0), f0=0, out=(0.0, 4.2, 3.0))
    d.m.events = {'strike': 12}
    return d.done()


@move('GK07', 'Quick Throw')
def gk07():
    d = K(22); idle(d, 0, 1)
    for f in range(0, 7): d.held(f, 0.5, 5.0, 15.0)
    d.at(2, R=(3.0, 1.0, 0, None), L=(-3.0, -0.6, 0, None), pz=22.0, cpitch=0.3, hyaw=-0.2); d.arms(2, (1.0, 0.6, 1.8, 0.5), (1.0, 0.6, 1.8, 0.5))
    d.at(3, R=(3.0, 0.6, 0, None), L=(-3.0, 1.2, 10, None), pz=22.2, cpitch=0.1, pyaw=0.3, hyaw=-0.3); d.arms(3, (0.2, 0.5, 1.4, 0.4), (1.0, 0.6, 1.8, 0.5))                   # arm cocked back
    d.at(4, R=(3.0, 0.6, 0, None), L=(-3.0, 3.0, 10, None), pz=22.4, cpitch=0.3, pyaw=-0.2, hyaw=0.1); d.arms(4, (2.0, 0.3, 1.8, 0.2), (0.9, 0.8, 1.5, 0.5))                   # fast snap forward
    d.at(5, R=(3.0, 0.6, 0, None), L=(-3.0, 4.4, 10, None), pz=22.0, cpitch=0.5, pyaw=-0.3); d.arms(5, (1.8, 0.2, 1.3, 0.1), (0.9, 0.8, 1.5, 0.5))
    for f in range(6, 22): ready(d, f, bounce=0.2 * math.sin(f)); d.m.k(f, hyaw=0.0)
    for i, q in enumerate(S.fly((3.0, 9.0, 18.0), (0.5, 3.4, 0.5), 15, g=0.18)): d.world(5 + i, *q)
    for f in range(0, 5): d.held(f, 0.5 + 0.2 * f, 5.0 + 0.5 * f, 16.0 - 0.5 * f) if f > 2 else None
    d.m.events = {'strike': 5}
    return d.done()


@move('GK08', 'Big Hands')
def gk08():
    d = K(24); idle(d, 0, 3)
    d.shot(8, (0.3, 7.0, 16.0), start=(0.5, 34.0, 14.0), out=(0, 0, 0), g=0.0)
    d.at(4, R=(3.2, 0.8, 0, None), L=(-3.2, -0.6, 0, None), pz=21.0, cpitch=0.55); d.arms(4, (1.3, 0.5, 1.6, 0.3), (1.3, 0.5, 1.6, 0.3))
    d.at(5, R=(3.4, 1.0, 0, None), L=(-3.4, -0.4, 0, None), pz=21.4, cpitch=0.4); d.arms(5, (1.45, 0.45, 1.55, 0.2), (1.45, 0.45, 1.55, 0.2))              # hands wide and open, giving the ball a big target
    d.at(6, R=(3.4, 1.0, 0, None), L=(-3.4, -0.4, 0, None), pz=21.8, cpitch=0.35); d.arms(6, (1.5, 0.4, 1.55, 0.15), (1.5, 0.4, 1.55, 0.15))
    d.at(7, R=(3.4, 1.0, 0, None), L=(-3.4, -0.4, 0, None), pz=21.8, cpitch=0.3); d.arms(7, (1.5, 0.35, 1.55, 0.1), (1.5, 0.35, 1.55, 0.1))
    d.at(8, R=(3.2, 1.0, 0, None), L=(-3.2, -0.4, 0, None), pz=21.6, cpitch=0.35, hpitch=0.3); d.arms(8, (1.35, 0.3, 1.5, 0.1), (1.35, 0.3, 1.5, 0.1))
    for f in range(9, 24):
        u = min(1.0, (f - 9) / 4.0); d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=21.6 + 1.0 * u, cpitch=0.4 - 0.1 * u, hpitch=0.35)
        d.arms(f, (1.35 - 0.3 * u, 0.3 + 0.4 * u, 1.5 + 0.9 * u, 0.1 + 0.3 * u), (1.35 - 0.3 * u, 0.3 + 0.4 * u, 1.5 + 0.9 * u, 0.1 + 0.3 * u))        # clutches it into the chest
        d.held(f, 0.0, 4.5, 15.5)
    d.W = {f: v for f, v in d.W.items() if f <= 8}
    d.m.events = {'strike': 8}
    return d.done()


@move('GK09', 'Low Dive')
def gk09():
    d = K(26); idle(d, 0, 2)
    d.shot(5, (8.5, 5.0, 3.0), start=(11.0, 34.0, 2.5), out=(0.5, 2.0, 0.0), g=0.0)
    e = dive(d, 3, h=16.0, reach=(2.0, 0.55, 2.3, 0.3), lt=4.2, lie=6, roll=1.5)
    d.W = {f: (min(v[0], 12.0), v[1], 2.0) for f, v in d.W.items()}
    getup(d, e, 26 - e) if e < 26 else None
    d.m.events = {'strike': 6}
    return d.done()


@move('GK10', 'High Palm')
def gk10():
    d = K(26); idle(d, 0, 3)
    d.shot(8, (2.0, 7.0, 31.0), start=(6.0, 34.0, 14.0), out=(0.4, 1.4, 1.6), g=0.12)
    d.at(4, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=20.4, cpitch=0.65); d.arms(4, READY, READY)
    d.at(5, R=(3.0, 1.4, 10, 3.0), L=(-3.0, 0.0, 0, 3.0), pz=26.0, cpitch=0.3, croll=-0.15); d.arms(5, (1.6, 0.3, 2.2, 0.2), (1.2, 0.5, 1.8, 0.3))
    d.at(6, R=(3.0, 1.8, 10, 9.0), L=(-3.0, 0.6, 0, 9.0), pz=32.0, cpitch=0.0, croll=-0.3); d.arms(6, (2.5, 0.2, 2.9, 0.1), (1.2, 0.5, 1.8, 0.3))
    d.at(7, R=(3.0, 2.0, 10, 11.0), L=(-3.0, 0.6, 0, 9.0), pz=34.5, cpitch=-0.05, croll=-0.35, hpitch=-0.3); d.arms(7, (2.8, 0.2, 3.0, 0.05), (1.2, 0.5, 1.8, 0.3))   # one arm stretched flat to the sky
    d.at(8, R=(3.0, 2.0, 10, 11.0), L=(-3.0, 0.6, 0, 9.0), pz=35.0, cpitch=-0.1, croll=-0.4, hpitch=-0.35); d.arms(8, (2.9, 0.2, 3.0, 0.05), (1.2, 0.5, 1.8, 0.3))
    d.at(9, R=(3.0, 1.4, 0, 6.0), L=(-3.0, 0.0, 0, 5.0), pz=31.0, cpitch=0.1, croll=-0.2); d.arms(9, (2.0, 0.4, 2.4, 0.3), (1.2, 0.5, 1.8, 0.3))
    d.at(10, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=22.4, cpitch=0.5); d.arms(10, READY, READY)
    for f in range(11, 26): ready(d, f, bounce=0.3 * math.sin(f))
    return d.done()


@move('GK11', 'Backpedal')
def gk11():
    d = K(26, -2.4)
    d.shot(15, (2.0, -9.0, 30.0), start=(3.0, 20.0, 12.0), out=(0.3, -1.4, 1.2), g=0.12)
    for f in range(0, 8):
        ph = 2 * PI * f / 4.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.8, -0.5 - 1.0 * a, 0, 2.0 + 3 * a) if a > .05 else (2.8, -0.5, 0, None), L=(-2.8, -0.9 - 1.0 * b, 0, 2.0 + 3 * b) if b > .05 else (-2.8, -0.9, 0, None), pz=22.4, cpitch=-0.1, hpitch=-0.35)   # backpedalling, looking up at the ball
        d.arms(f, (0.9, 0.6, 1.6, 0.5), (0.9, 0.6, 1.6, 0.5))
    d.at(8, R=(3.0, -1.0, 0, 3.0), L=(-3.0, -1.0, 0, 3.0), pz=22.0, cpitch=-0.2, hpitch=-0.45); d.arms(8, (1.6, 0.4, 2.2, 0.3), (1.6, 0.4, 2.2, 0.3))
    d.at(9, R=(3.0, -1.0, 0, 6.0), L=(-3.0, -2.0, 0, 6.0), pz=26.0, cpitch=-0.3, hpitch=-0.5); d.arms(9, (2.2, 0.3, 2.7, 0.2), (1.5, 0.4, 2.0, 0.3))
    for f in (10, 11, 12, 13, 14): d.at(f, R=(3.0, -1.0, 0, 8.0), L=(-3.0, -2.5, 0, 8.0), pz=28.0 - 0.4 * (f - 10), cpitch=-0.35, hpitch=-0.55); d.arms(f, (2.6, 0.2, 2.9, 0.1), (1.5, 0.4, 2.0, 0.3))
    d.at(15, R=(3.0, -1.0, 0, 8.0), L=(-3.0, -2.5, 0, 8.0), pz=27.0, cpitch=-0.35, hpitch=-0.55); d.arms(15, (2.9, 0.2, 3.0, 0.05), (1.5, 0.4, 2.0, 0.3))               # leaps and tips it over
    for f in range(16, 20): d.at(f, R=(3.0, -1.0, 0, 5.0), L=(-3.0, -2.0, 0, 5.0), pz=24.0 - 0.8 * (f - 16), cpitch=-0.1); d.arms(f, (2.2, 0.3, 2.4, 0.3), (1.5, 0.4, 2.0, 0.3))
    for f in range(20, 26): ready(d, f, bounce=0.2 * math.sin(f))
    d.speed(f0=-2.4, f8=-1.4, f12=-0.4, f16=0.0)
    return d.done()


@move('GK12', 'Starfish')
def gk12():
    d = K(26, 2.2); idle(d, 0, 1)
    for f in range(0, 9): d.world(f, 0.6, 24.0 - 1.4 * f, 2.5)
    for f in range(2, 6): d.m.k(f, bvis=0.0)
    burst(d, 2, 5, 0.3)
    d.at(6, R=(3.0, 3.0, 20, 3.0), L=(-3.0, 0.0, 10, None), pz=22.0, cpitch=0.5); d.arms(6, (1.0, 0.7, 1.6, 0.4), (1.0, 0.7, 1.6, 0.4))
    d.at(7, R=(5.0, 3.0, 20, 5.0), L=(-5.0, 1.0, 20, 5.0), pz=19.0, cpitch=0.3, hpitch=0.3); d.arms(7, (1.4, 0.75, 1.6, 0.6), (1.4, 0.75, 1.6, 0.6))
    d.at(8, R=(7.0, 2.0, 30, 3.0), L=(-7.0, 2.0, 30, 3.0), pz=15.0, cpitch=0.1, hpitch=0.3); d.arms(8, (1.5, 0.75, 1.9, 0.55), (1.5, 0.75, 1.9, 0.55))             # sprawls into a big X
    d.at(9, R=(8.4, 2.0, 30, 3.0), L=(-8.4, 2.0, 30, 3.0), pz=13.0, cpitch=0.0, hpitch=0.3); d.arms(9, (1.9, 0.75, 2.2, 0.55), (1.9, 0.75, 2.2, 0.55))
    for f in range(10, 26): d.at(f, R=(8.4, 2.0, 30, 3.0), L=(-8.4, 2.0, 30, 3.0), pz=13.0, cpitch=0.0, hpitch=0.3); d.arms(f, (1.9, 0.75, 2.2, 0.55), (1.9, 0.75, 2.2, 0.55))
    d.speed(f0=2.2, f5=1.8, f9=0.6, f11=0.0)
    d.shot(9, (1.2, 14.0, 2.5), start=(0.6, 24.0, 2.5), out=(0.3, -1.0, 0.8))
    return d.done()


@move('GK13', 'Parry Stance')
def gk13():
    d = K(24); idle(d, 0, 3)
    d.shot(9, (4.5, 7.0, 15.0), start=(7.0, 34.0, 14.0), out=(1.2, 1.5, 0.8))
    for f in range(4, 9):
        u = (f - 4) / 4.0
        d.at(f, R=(3.4, 0.8, 0, None), L=(-3.4, -0.6, 0, None), pz=21.2, cpitch=0.5, croll=-0.15 * u); d.arms(f, (1.5, 0.5 - 0.1 * u, 1.55, 0.2), (1.5, 0.5, 1.55, 0.3 + 0.2 * u))     # flat palms turned out
    d.at(9, R=(3.4, 0.8, 0, None), L=(-3.4, -0.6, 0, None), pz=21.2, cpitch=0.45, croll=-0.3); d.arms(9, (1.5, 0.55, 1.2, 0.1), (1.5, 0.3, 1.8, 0.6))                       # a firm push sideways
    d.at(10, R=(3.4, 0.8, 0, None), L=(-3.4, -0.6, 0, None), pz=21.6, cpitch=0.4, croll=-0.2); d.arms(10, (1.4, 0.6, 1.6, 0.2), (1.4, 0.4, 1.6, 0.3))
    for f in range(11, 24): ready(d, f, bounce=0.2 * math.sin(f))
    return d.done()


@move('GK14', 'Kick Save')
def gk14():
    d = K(24); idle(d, 0, 3)
    d.shot(7, (5.0, 3.0, 5.0), start=(3.0, 20.0, 5.0), out=(2.2, 1.6, 0.9))
    d.at(4, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=20.6, cpitch=0.6); d.arms(4, READY, READY)
    d.at(5, R=(3.6, 2.5, 0, 5.0), L=(-3.0, -0.6, 0, None), pz=21.0, cpitch=0.5, croll=0.15); d.arms(5, (1.1, 0.8, 1.2, 0.5), (0.7, 0.6, 1.3, 0.4))
    d.at(6, R=(5.2, 3.8, 30, 4.4), L=(-3.0, -0.6, 0, None), pz=20.4, cpitch=0.5, croll=0.3, proll=0.12); d.arms(6, (1.2, 0.8, 1.2, 0.5), (0.6, 0.5, 1.3, 0.4))                   # leg shoots out to the side
    d.at(7, R=(6.6, 3.2, 40, 4.0), L=(-3.0, -0.6, 0, None), pz=20.0, cpitch=0.5, croll=0.35, proll=0.15); d.arms(7, (1.2, 0.8, 1.2, 0.5), (0.5, 0.5, 1.3, 0.4))
    d.at(8, R=(5.8, 2.8, 30, 4.0), L=(-3.0, -0.6, 0, None), pz=20.6, cpitch=0.5, croll=0.25); d.arms(8, (1.1, 0.8, 1.2, 0.5), (0.6, 0.5, 1.3, 0.4))
    d.at(9, R=(3.4, 1.0, 0, None), L=(-3.0, -0.6, 0, None), pz=21.6, cpitch=0.5); d.arms(9, READY, READY)
    for f in range(10, 24): ready(d, f, bounce=0.25 * math.sin(f))
    return d.done()


@move('GK15', 'Command the Line')
def gk15():
    d = K(26); idle(d, 0, 3)
    for f in range(4, 26):
        u = min(1.0, (f - 4) / 3.0); s = math.sin((f - 4) * 0.7)
        d.at(f, R=(2.8, 1.0, 0, None), L=(-2.8, -0.4, 0, None), pz=22.6, cpitch=0.15, hpitch=-0.1 + 0.1 * s, hyaw=0.3 * s * u, pyaw=0.12 * s * u)          # stands tall, sweeping an arm forward to push the line up, shouting
        sweep = 1.45 + 0.35 * math.sin((f - 4) * 0.9)
        d.arms(f, (sweep, 0.3, 1.5, 0.15), READY if f < 8 else (1.0, 0.7, 1.4, 0.4))
    return d.done()


@move('GK16', 'Long Kick')
def gk16():
    d = K(26); idle(d, 0, 1)
    for f in range(0, 5): d.held(f, 0.2, 5.0, 15.0 - 0.5 * f)
    d.at(2, R=(3.0, 1.0, 0, None), L=(-3.0, 0.0, 0, None), pz=22.2, cpitch=0.3, hpitch=0.4); d.arms(2, (1.0, 0.6, 1.8, 0.5), (1.0, 0.6, 1.8, 0.5))
    d.at(3, R=(2.6, 1.6, 10, None), L=(-3.0, 3.0, 5, None), pz=22.4, cpitch=0.3, hpitch=0.5); d.arms(3, (1.4, 0.5, 1.5, 0.4), (1.0, 0.7, 1.4, 0.4))
    d.at(4, R=(2.6, -3.0, 40, 5.0), L=(-3.4, 4.5, 5, None), pz=22.8, cpitch=-0.1, pyaw=-0.2, hpitch=0.5); d.arms(4, (1.2, 0.8, 1.2, 0.5), (1.6, 0.7, 1.6, 0.4))                  # drops it, swings back
    d.at(5, R=(2.4, -6.0, 55, 8.0), L=(-3.4, 5.0, 5, None), pz=23.0, cpitch=-0.2, pyaw=-0.3, hpitch=0.5); d.arms(5, (0.8, 0.9, 1.0, 0.6), (1.7, 0.8, 1.7, 0.5))
    d.at(6, R=(2.4, 2.0, 60, 5.0, -1.1, 0.1), L=(-3.4, 5.0, 5, None), pz=23.4, cpitch=0.1, pyaw=0.0, hpitch=0.5); d.arms(6, (0.8, 0.9, 1.0, 0.6), (1.7, 0.8, 1.7, 0.5))
    d.at(7, R=(1.4, 9.0, 60, 4.0, -1.2, 0.1), L=(-3.4, 5.2, 5, None), pz=23.6, cpitch=0.2, pyaw=0.15); d.arms(7, (0.4, 0.9, 0.8, 0.6), (1.7, 0.8, 1.7, 0.5))
    d.at(8, R=(1.0, 15.0, 40, 6.0), L=(-3.4, 5.4, 5, None), pz=24.0, cpitch=0.1, pyaw=0.2); d.arms(8, (0.4, 0.9, 0.8, 0.6), (1.7, 0.8, 1.7, 0.5))
    d.at(9, R=(0.8, 19.0, 25, 8.0), L=(-3.0, 6.0, 10, None), pz=24.0, cpitch=0.0, pyaw=0.2); d.arms(9, (0.4, 0.9, 0.8, 0.6), (1.7, 0.8, 1.7, 0.5))
    for f in range(10, 26): d.at(f, R=(1.0 + 0.2 * (f - 10), 17.0 - 0.8 * (f - 10), 20, 6.0 - 0.4 * (f - 10) if f < 20 else None), L=(-3.0, 6.0 - 0.3 * (f - 10), 10, None), pz=24.0 - 0.15 * (f - 10), cpitch=0.1, pyaw=0.15 * (1 - (f - 10) / 15)); d.arms(f, READY, READY)
    c = (0.8, 7.5, 3.0)
    for f in range(0, 5): d.W.pop(f, None)
    for i, q in enumerate(S.fly((0.6, 8.6, 2.6), (0.5, 4.4, 3.0), 18, g=0.2)): d.world(7 + i, *q)
    d.m.events = {'strike': 7}
    return d.done()


@move('GK17', 'Roll Out')
def gk17():
    d = K(22); idle(d, 0, 1)
    for f in range(0, 6): d.held(f, 0.3, 5.5, 13.0 - 1.0 * f)
    d.at(2, R=(3.0, 1.0, 0, None), L=(-3.0, 0.0, 0, None), pz=21.0, cpitch=0.6, hpitch=0.35); d.arms(2, (1.0, 0.6, 1.8, 0.5), (1.0, 0.6, 1.8, 0.5))
    d.at(3, R=(3.0, 0.0, 0, None), L=(-3.0, 3.5, 10, None), pz=19.6, cpitch=0.8, hpitch=0.35); d.arms(3, (0.4, 0.5, 1.2, 0.4), (1.0, 0.6, 1.5, 0.5))                  # low bowl: arm swings back,
    d.at(4, R=(3.0, 0.0, 0, None), L=(-3.0, 5.0, 10, None), pz=19.0, cpitch=0.95, hpitch=0.3); d.arms(4, (1.3, 0.4, 1.4, 0.2), (1.0, 0.6, 1.5, 0.5))                    # sweeps through low,
    d.at(5, R=(3.0, 0.0, 0, None), L=(-3.0, 5.4, 10, None), pz=18.8, cpitch=1.0, hpitch=0.3); d.arms(5, (1.45, 0.35, 1.4, 0.1), (1.0, 0.6, 1.5, 0.5))                    # and lets go along the grass
    for f in range(6, 22):
        u = min(1.0, (f - 6) / 5.0); d.at(f, R=(3.0, 0.4, 0, None), L=(-3.0, 4.0 - 3.2 * u, 10, None), pz=18.8 + 3.0 * u, cpitch=1.0 - 0.5 * u, hpitch=0.3); d.arms(f, (1.2 - 0.05 * u, 0.5, 1.4 + 0.1 * u, 0.2), READY)
    for i, q in enumerate(S.fly((1.0, 8.5, 2.0), (0.2, 2.6, 0.0), 16, g=0.0)): d.world(5 + i, *q)
    d.m.events = {'strike': 5}
    return d.done()


@move('GK18', 'Throw Long')
def gk18():
    d = K(26); idle(d, 0, 1)
    for f in range(0, 5): d.held(f, 0.3, 5.0, 16.0)
    d.at(2, R=(3.0, 1.0, 0, None), L=(-3.0, 0.0, 0, None), pz=22.0, cpitch=0.3, hyaw=-0.3); d.arms(2, (1.0, 0.6, 1.8, 0.5), (1.0, 0.6, 1.8, 0.5))
    d.at(3, R=(3.0, -1.0, 0, None), L=(-3.0, 3.0, 10, None), pz=22.4, cpitch=-0.35, pyaw=0.5, hyaw=-0.5); d.arms(3, (-0.1, 0.6, 0.0, 0.5), (1.5, 0.6, 1.5, 0.4))                   # javelin wind-up: arm all the way back
    d.at(4, R=(3.0, -1.6, 0, None), L=(-3.0, 4.6, 10, None), pz=23.0, cpitch=-0.5, pyaw=0.7, hyaw=-0.6); d.arms(4, (-0.3, 0.6, -0.2, 0.5), (1.5, 0.6, 1.5, 0.4))
    d.at(5, R=(3.0, -0.4, 0, None), L=(-3.0, 4.4, 10, None), pz=23.2, cpitch=0.0, pyaw=0.1, hyaw=-0.2); d.arms(5, (1.5, 0.3, 2.0, 0.2), (1.5, 0.6, 1.5, 0.4))
    d.at(6, R=(3.0, 0.6, 0, 3.0), L=(-3.0, 4.6, 10, None), pz=23.4, cpitch=0.5, pyaw=-0.4, hyaw=0.2); d.arms(6, (2.1, 0.3, 1.9, 0.1), (1.0, 0.8, 1.4, 0.5))                    # snaps through, arm high and long
    d.at(7, R=(3.0, 1.8, 0, 4.0), L=(-3.0, 4.6, 10, None), pz=23.4, cpitch=0.7, pyaw=-0.5, hyaw=0.2); d.arms(7, (1.7, 0.3, 1.2, 0.1), (1.0, 0.8, 1.4, 0.5))
    for f in range(8, 26):
        u = min(1.0, (f - 8) / 6.0); d.at(f, R=(3.0, 1.0, 0, None), L=(-3.0, 4.0 - 3.4 * u, 10, None), pz=23.0 - 0.8 * u, cpitch=0.7 - 0.2 * u, pyaw=-0.5 * (1 - u), hyaw=0.1); d.arms(f, (1.3 - 0.1 * u, 0.5, 1.4, 0.2), READY)
    for i, q in enumerate(S.fly((2.0, 8.0, 31.0), (0.7, 3.8, 1.1), 17, g=0.15)): d.world(6 + i, *q)
    for f in range(0, 6): d.held(f, 0.3, 5.0, 16.0) if f < 3 else d.held(f, 1.5, -4.0 + 1.0 * f, 28.0)
    d.m.events = {'strike': 6}
    return d.done()


@move('GK19', 'Read the Run')
def gk19():
    d = K(26, 0.0); idle(d, 0, 2)
    for f in range(0, 12): d.world(f, 1.0, 34.0 - 2.0 * f, 2.5)
    for f in range(3, 12):
        ph = 2 * PI * (f - 3) / 3.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.8, 1.5 + 1.6 * a, 0, 2.0 + 3 * a) if a > .05 else (2.8, 1.5, 0, None), L=(-2.8, 0.5 + 1.6 * b, 0, 2.0 + 3 * b) if b > .05 else (-2.8, 0.5, 0, None), pz=21.4, cpitch=0.5, hpitch=0.1, hyaw=0.15 * math.sin(f))  # small creeping steps, eyes on the runner
        d.arms(f, (1.1, 0.55, 1.5, 0.35), (1.1, 0.55, 1.5, 0.35))
    d.at(12, R=(3.0, 3.0, 20, None), L=(-3.0, -1.0, 10, 4.0), pz=20.6, cpitch=0.7); d.arms(12, (1.4, 0.4, 1.7, 0.2), (1.4, 0.4, 1.7, 0.2))
    d.at(13, R=(2.6, 5.0, 20, 3.0), L=(-2.6, 0.0, 10, 3.0), pz=20.0, cpitch=0.85, hpitch=0.3); d.arms(13, (1.5, 0.35, 1.8, 0.15), (1.5, 0.35, 1.8, 0.15))          # steps out and gets down first
    for f in range(14, 26): d.at(f, R=(2.6, 5.0, 20, None), L=(-2.6, 0.0, 10, None), pz=20.0 + 0.2 * (f - 14), cpitch=0.85 - 0.04 * (f - 14), hpitch=0.3); d.arms(f, (1.5, 0.35, 1.8, 0.15), (1.5, 0.35, 1.8, 0.15))
    d.speed(f0=0.0, f3=0.3, f11=0.5, f13=1.4, f15=0.0)
    d.shot(13, (1.2, 17.0, 2.5), start=(1.0, 34.0 - 2.0 * 12 + 0.0, 2.5), f0=12, out=(0.1, -0.8, 0.3))
    for f in range(0, 12): d.world(f, 1.0, 34.0 - 2.0 * f, 2.5)
    d.m.events = {'strike': 13}
    return d.done()


@move('GK20', 'Cat Reflexes')
def gk20():
    d = K(22); idle(d, 0, 3)
    d.shot(6, (2.4, 6.0, 20.0), start=(4.0, 20.0, 20.0), out=(0.8, 1.2, 0.6))
    d.at(4, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=21.0, cpitch=0.5, croll=0.1); d.arms(4, (1.3, 0.5, 1.55, 0.2), (1.3, 0.5, 1.55, 0.3))                        # twitch: flinches a split second early
    d.at(5, R=(3.6, 1.0, 10, 3.0), L=(-2.6, 0.0, 0, None), pz=22.4, cpitch=0.3, croll=-0.3, proll=-0.1, hyaw=-0.3); d.arms(5, (2.0, 0.45, 2.3, 0.2), (1.2, 0.5, 1.7, 0.3))
    d.at(6, R=(4.0, 1.0, 10, 5.0), L=(-2.4, 0.0, 0, 4.0), pz=24.0, cpitch=0.1, croll=-0.5, proll=-0.2, hyaw=-0.4); d.arms(6, (2.4, 0.5, 2.7, 0.2), (1.2, 0.5, 1.7, 0.3))        # one-handed flick up and across
    d.at(7, R=(4.0, 1.0, 10, 5.0), L=(-2.4, 0.0, 0, 4.0), pz=24.0, cpitch=0.1, croll=-0.55, proll=-0.2, hyaw=-0.4); d.arms(7, (2.5, 0.5, 2.8, 0.2), (1.2, 0.5, 1.7, 0.3))
    d.at(8, R=(3.4, 1.0, 0, 3.0), L=(-2.8, 0.0, 0, None), pz=22.4, cpitch=0.3, croll=-0.3); d.arms(8, (2.0, 0.45, 2.3, 0.3), (1.2, 0.5, 1.7, 0.3))
    d.lateral(f4=0.0, f5=1.2, f6=1.8, f8=0.6, f10=0.0)
    for f in range(9, 22): ready(d, f, bounce=0.3 * math.sin(f))
    return d.done()


@move('GK21', 'Dominate Box')
def gk21():
    d = K(28, 1.0); idle(d, 0, 2)
    for f in range(3, 10):
        ph = 2 * PI * (f - 3) / 4.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.8, 1.5 + 1.8 * a, 0, 2.0 + 3 * a) if a > .05 else (2.8, 1.5, 0, None), L=(-2.8, 0.5 + 1.8 * b, 0, 2.0 + 3 * b) if b > .05 else (-2.8, 0.5, 0, None), pz=22.6, cpitch=0.2, hpitch=0.0)  # strides out, arms spread wide: "mine"
        d.arms(f, (1.5, 0.45, 1.6, 0.2), (1.5, 0.45, 1.6, 0.2))
    d.shot(15, (0.6, 9.0, 31.0), start=(8.0, 36.0, 16.0), out=(0, 0, 0), g=0.0)
    d.at(10, R=(2.8, 2.0, 0, None), L=(-2.8, 0.0, 0, None), pz=21.4, cpitch=0.5); d.arms(10, READY, READY)
    d.at(11, R=(2.8, 3.0, 20, 4.0), L=(-2.8, 0.0, 0, None), pz=24.0, cpitch=0.3); d.arms(11, (2.0, 0.3, 2.6, 0.2), (2.0, 0.3, 2.6, 0.2))
    d.at(12, R=(2.6, 4.0, 20, 9.0), L=(-2.8, 1.0, 0, 8.0), pz=31.0, cpitch=0.0); d.arms(12, UP, UP)
    d.at(13, R=(2.6, 4.0, 20, 10.0), L=(-2.8, 1.0, 0, 8.0), pz=34.0, cpitch=-0.05, hpitch=-0.35); d.arms(13, UP, UP)
    for f in (14, 15): d.at(f, R=(2.6, 4.0, 20, 10.0), L=(-2.8, 1.0, 0, 8.0), pz=34.5, cpitch=-0.05, hpitch=-0.4); d.arms(f, UP, UP)
    d.at(16, R=(2.8, 2.0, 10, 5.0), L=(-2.8, 0.6, 0, 4.0), pz=30.0, cpitch=0.1); d.arms(16, (1.9, 0.5, 2.5, 0.3), (1.9, 0.5, 2.5, 0.3))
    d.at(17, R=(2.8, 1.0, 0, None), L=(-2.8, -0.4, 0, None), pz=21.4, cpitch=0.45); d.arms(17, (1.0, 0.6, 2.4, 0.4), (1.0, 0.6, 2.4, 0.4))
    for f in range(18, 28): d.at(f, R=(2.8, 1.0, 0, None), L=(-2.8, -0.4, 0, None), pz=22.4, cpitch=0.2, hpitch=0.1); d.arms(f, (0.9, 0.7, 2.4, 0.5), (0.9, 0.7, 2.4, 0.5)); d.held(f, 0.0, 4.2, 16.0)
    d.W = {f: v for f, v in d.W.items() if f <= 15}
    d.speed(f0=0.0, f3=1.0, f9=0.8, f11=0.0)
    d.m.events = {'strike': 15}
    return d.done()


@move('GK22', 'Near Post Guard')
def gk22():
    d = K(26); idle(d, 0, 1)
    for f in range(2, 14):
        ph = 2 * PI * (f - 2) / 4.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(3.0 + 0.8 * a, 0.8, 0, 2.0 + 3 * a) if a > .05 else (3.0, 0.8, 0, None), L=(-3.0 + 0.8 * b, -0.6, 0, 2.0 + 3 * b) if b > .05 else (-3.0, -0.6, 0, None), pz=21.0, cpitch=0.5, hpitch=0.2, croll=0.08 * math.sin(ph))   # side-steps to the post
        d.arms(f, (1.2, 0.5, 1.5, 0.3), (1.2, 0.5, 1.5, 0.3))
    d.lateral(f0=0.0, f2=1.4, f12=1.0, f14=0.0)
    for f in range(14, 26): d.at(f, R=(3.4, 0.8, 0, None), L=(-3.2, -0.6, 0, None), pz=20.8, cpitch=0.5, hpitch=0.2, hyaw=-0.4); d.arms(f, (1.3, 0.6, 1.5, 0.3), (1.0, 0.8, 1.3, 0.4))      # tucked in tight against the post, arm out to seal the gap
    return d.done()


@move('GK23', 'Far Post Reach')
def gk23():
    d = K(30); idle(d, 0, 2)
    for f in range(3, 8):
        ph = 2 * PI * (f - 3) / 4.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(3.2 + 1.0 * a, 0.8, 0, 2.0 + 3 * a) if a > .05 else (3.2, 0.8, 0, None), L=(-3.0 + 1.0 * b, -0.6, 0, 2.0 + 3 * b) if b > .05 else (-3.0, -0.6, 0, None), pz=21.0, cpitch=0.5, hpitch=0.2)
        d.arms(f, (1.2, 0.5, 1.5, 0.3), (1.2, 0.5, 1.5, 0.3))
    d.lateral(f3=1.6, f7=0.8, f8=0.0)
    d.shot(11, (12.0, 5.0, 24.0), start=(15.0, 34.0, 10.0), out=(1.0, 2.8, 1.4))
    e = dive(d, 8, h=31.0, reach=(2.45, 0.5, 2.9, 0.15), lt=4.4, lie=6)
    getup(d, e, 30 - e) if e < 30 else None
    return d.done()


@move('GK24', 'Fingertip Save')
def gk24():
    d = K(30); idle(d, 0, 4)
    d.shot(8, (11.5, 5.0, 32.0), start=(14.0, 36.0, 10.0), out=(1.2, 3.0, 1.6), g=0.15)
    e = dive(d, 5, h=36.0, reach=(2.55, 0.5, 3.0, 0.1), lt=4.8, lie=7, roll=1.4)
    for f in range(5, e): d.m.k(f, hroll=-0.2)
    getup(d, e, 30 - e) if e < 30 else None
    return d.done()


@move('GK25', 'Rebound Clear')
def gk25():
    d = K(24); idle(d, 0, 1)
    for f in range(0, 5): d.world(f, 1.4, 8.0 + 0.3 * f, 2.5)
    d.at(2, R=(3.0, 1.0, 0, None), L=(-3.0, 0.0, 0, None), pz=20.4, cpitch=0.7, hpitch=0.4); d.arms(2, (1.2, 0.55, 1.6, 0.3), (1.2, 0.55, 1.6, 0.3))
    d.at(3, R=(2.8, 2.5, 10, None), L=(-3.0, -1.0, 0, 3.0), pz=17.0, cpitch=0.9, hpitch=0.4); d.arms(3, (0.8, 0.8, 1.4, 0.5), (1.6, 0.6, 1.7, 0.4))                    # scrambles up off the ground
    d.at(4, R=(2.4, 5.0, 40, 5.0), L=(-3.0, -1.0, 0, None), pz=19.6, cpitch=0.7, hpitch=0.4); d.arms(4, (0.5, 0.8, 1.0, 0.6), (1.6, 0.6, 1.7, 0.4))
    d.at(5, R=(1.6, 9.0, 60, 4.2), L=(-3.0, -1.0, 0, None), pz=20.8, cpitch=0.7, hpitch=0.4); d.arms(5, (0.3, 0.8, 0.8, 0.6), (1.6, 0.6, 1.7, 0.4))                     # swings through low: a desperate hack
    d.at(6, R=(1.2, 12.0, 70, 4.0), L=(-3.0, -1.0, 0, None), pz=21.4, cpitch=0.6); d.arms(6, (0.3, 0.8, 0.8, 0.6), (1.6, 0.6, 1.7, 0.4))
    d.at(7, R=(1.4, 14.0, 50, 6.0), L=(-3.0, -1.0, 0, None), pz=22.0, cpitch=0.5)
    d.at(8, R=(1.8, 13.0, 30, 6.0), L=(-3.0, 0.0, 0, None), pz=22.4, cpitch=0.4)
    for f in range(9, 24): ready(d, f, bounce=0.3 * math.sin(f))
    for f in range(5, 24): d.W.pop(f, None)
    for f in range(0, 6): d.world(f, 1.4, 8.0 + 0.3 * f, 2.5)
    for i, q in enumerate(S.fly((1.4, 10.8, 2.5), (0.5, 3.4, 2.6), 18, g=0.2)): d.world(6 + i, *q)
    d.speed(f0=0.0, f4=0.8, f7=0.0)
    d.m.events = {'strike': 6}
    return d.done()


def build(ids=None):
    out = []
    for id_, (label, fn) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); name = id_.lower() + '_' + label.lower().replace(' ', '_').replace("'", '')
        m.save(name, label, 'auto-generated by sprites/moves_keeper.py'); out.append((id_, name))
    return out


if __name__ == '__main__':
    for id_, name in build(sys.argv[1:] or None): print(id_, name)
