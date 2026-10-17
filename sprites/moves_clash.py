"""Clash clips (the engagement close-up, Captain Tsubasa style but in our pixel world):
  cl01_clash_reach  : both players lunge for the same ball, kicking leg stretched out at it, plant leg bent deep behind, one arm flung back,
                      body thrown over the ball; a held loop that trembles (the grind while the cards are picked)
  cl02_clash_hurdle : the winner skips over the defender's sliding challenge: drive, take-off, lead knee up, trail leg tucked, arm up, lands running
Same framework as moves_contest.py. Run:  python moves_clash.py  -> data/animations/cl0*.json  (then bake: python custom_anims.py <name>)"""
import math, sys
from moves_dribble import Dr
from moves_defend import hidden
from moves_fluid import sm, mix, REST

PI = math.pi
MOVES = {}


def move(id_, label, loop=False):
    def deco(fn):
        MOVES[id_] = (label, fn, loop); return fn
    return deco


@move('cl01_clash_reach', 'Clash Reach (held lunge)', True)
def clash_reach():
    """thrown into the challenge: low over a deep-bent plant leg, the kicking leg stretched out at ball height, toe pointed at it, chest over it,
    the near arm flung back and up, the other out in front for balance; the whole thing strains (small shakes) as two players press on one ball"""
    N = 12; d = Dr(N, ms=70, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N):
        ph = 2 * PI * f / N
        sh = math.sin(ph * 2); tr = math.sin(ph * 3 + 0.7)
        d.at(f, R=(0.8, 13.2 + 0.4 * sh, 38, 3.0 + 0.2 * tr), L=(-2.4, -6.8, 0, None),
             pz=15.8 + 0.3 * tr, cpitch=0.5 + 0.04 * sh, ppitch=-0.1, croll=-0.12 + 0.03 * tr, proll=-0.06, cyaw=-0.18, pyaw=0.08,
             hpitch=0.35, hyaw=0.05 * tr)
        back = (-1.1 + 0.05 * sh, 0.55, -0.2, 0.3)                        # flung back and up: the drive
        front = (1.35, 0.75 + 0.05 * tr, 0.7, 0.25)                        # out in front: balance
        d.arms(f, back, front)
    hidden(d); return d.m


@move('cl02_clash_hurdle', 'Clash Hurdle (over the slide)')
def clash_hurdle():
    """he has won it: two driving strides, plants and takes off, the lead knee comes high, the trail leg tucks up behind (the defender slides under),
    one arm flung up high, the other forward; lands on the lead foot, knees give, and runs on"""
    N = 20; d = Dr(N, ms=55, speed=2.6); d.m.events = {'takeoff': 4, 'land': 13}
    d.speed(f0=2.6, f4=3.0, f12=3.0, f15=2.4, f19=2.8)
    H = 7.0
    for f in range(N):
        t = (f - 4) / 9.0
        hgt = 4 * H * t * (1 - t) if 0.0 < t < 1.0 else 0.0
        air = sm(min(1.0, hgt / H) * 1.5)
        land = sm((f - 12.0) / 1.5) * (1 - sm((f - 14.0) / 3.0))
        stride = math.sin(f * PI / 3.0)
        if 0.0 < t < 1.0:
            R = (2.0, 3.8 * air + 1.0, -20 * air, 1.0 + hgt + 5.0 * air)       # lead knee up, foot tucked under
            L = (-2.0, -3.5 * air - 0.5, -45 * air, 0.8 + hgt + 3.5 * air)     # trail leg folded up behind
        else:
            R = (2.6, 2.4 * stride, 0, (1.4 * max(0.0, stride)) if stride > 0.2 else None)
            L = (-2.6, -2.4 * stride, 0, (1.4 * max(0.0, -stride)) if stride < -0.2 else None)
        d.at(f, R=R, L=L, pz=22.0 + hgt - 3.5 * land - 0.8 * sm((f - 2.0) / 2.0) * (1 - sm((f - 4.0) / 1.0)),
             cpitch=0.25 + 0.15 * air + 0.3 * land, hpitch=0.15 * air, croll=0.06 * air)
        up = (2.9, 0.35, 2.7, 0.1)                                        # flung up high
        fwd = (1.4, 0.4, 1.1, 0.2)
        run_r = (0.6 * stride, 0.2, 1.2, 0.0); run_l = (-0.6 * stride, 0.2, 1.2, 0.0)
        d.arms(f, mix(run_r, up, air), mix(run_l, fwd, air))
    hidden(d); return d.m


def build(ids=None):
    out = []
    for id_, (label, fn, loop) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); m.loop = loop; m.save(id_, label, 'clash, sprites/moves_clash.py'); out.append(id_)
    return out


if __name__ == '__main__':
    for n in build(sys.argv[1:] or None): print(n)
