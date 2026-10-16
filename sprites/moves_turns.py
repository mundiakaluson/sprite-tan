"""Turn-with-the-ball clips: the footwork and body of a player who turns to pass (planted foot, stepping round, lean, arms for balance).
All turn to his RIGHT (the game mirrors them for a left turn). The sprite itself turns by direction, so these only add the twist that leads the turn (shoulders first)
and the weight: heavy = wide braking plant and arms out, normal = plant and step round, sharp = quick drop of the shoulder and crossover, spin = low fast spin on the ball."""
import math
import gen_actions as A
from moves_dribble import Dr
from moves_reactions import lay, smooth, env, STAND_R, STAND_L, ARM_REST

MOVES = {}


def move(id_, label, loop=False):
    def deco(fn):
        MOVES[id_] = (label, fn, loop); return fn
    return deco


def arms(a, b):
    return (a, b)


def build(N, ms, steps, body, arm):
    d = Dr(N, ms=ms, speed=0.0); d.m.events = {'turn': N // 2}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    lay(d, steps, body, arm)
    return d.m


@move('tn01_heavy_turn', 'Heavy Turn')
def heavy():
    """big man at speed: braking plant of the outside (left) foot wide in front, body leaning back, arms out, a late short step round"""
    N = 18
    steps = [('L', 0, 5, (-4.6, 3.8), 3.0), ('R', 7, 12, (3.6, -0.4), 3.5), ('L', 12, 16, (-3.0, 0.2), 2.5)]
    e = lambda f: env(f, 0, 4, 10, 17)
    body = lambda f: dict(pz=22.7 - 2.4 * e(f), cpitch=0.05 - 0.22 * e(f), ppitch=-0.1 * e(f), croll=0.32 * e(f), proll=0.18 * e(f), cyaw=0.35 * e(f), hyaw=0.55 * e(f), pyaw=0.12 * e(f), hpitch=0.05)
    arm = lambda f: arms((0.12 + 0.5 * e(f), 0.2 + 1.5 * e(f), 0.45 + 0.4 * e(f), -0.08), (0.12 + 0.6 * e(f), 0.2 + 1.5 * e(f), 0.45 + 0.4 * e(f), -0.08))
    return build(N, 62, steps, body, arm)


@move('tn02_plant_turn', 'Plant And Turn')
def plant():
    """left foot plants beside the body, he leans into the turn and the right foot steps round; arms tucked and balanced"""
    N = 13
    steps = [('L', 0, 3, (-3.4, 2.4), 2.5), ('R', 4, 9, (3.4, -1.2), 3.0)]
    e = lambda f: env(f, 0, 3, 8, 12)
    body = lambda f: dict(pz=22.7 - 1.6 * e(f), cpitch=0.05 + 0.14 * e(f), croll=0.28 * e(f), proll=0.14 * e(f), cyaw=0.4 * e(f), hyaw=0.6 * e(f), pyaw=0.1 * e(f))
    arm = lambda f: arms((0.12 + 0.2 * e(f), 0.2 + 0.7 * e(f), 0.45 + 0.4 * e(f), -0.08), (0.12 + 0.5 * e(f), 0.2 + 0.4 * e(f), 0.45 + 0.9 * e(f), -0.08 + 0.3 * e(f)))
    return build(N, 54, steps, body, arm)


@move('tn03_sharp_turn', 'Sharp Turn')
def sharp():
    """quick: the shoulder drops, the left foot crosses in front and the right whips round; head up, low centre of gravity"""
    N = 10
    steps = [('L', 0, 3, (-1.0, 2.8), 2.2), ('R', 3, 7, (3.8, -1.0), 2.8)]
    e = lambda f: env(f, 0, 2, 6, 9)
    body = lambda f: dict(pz=22.7 - 2.2 * e(f), cpitch=0.05 + 0.3 * e(f), croll=0.5 * e(f), proll=0.26 * e(f), cyaw=0.55 * e(f), hyaw=0.7 * e(f), pyaw=0.2 * e(f), hpitch=-0.1 * e(f))
    arm = lambda f: arms((0.12 + 0.1 * e(f), 0.2 + 0.4 * e(f), 0.45 + 0.8 * e(f), -0.08), (0.12 + 0.7 * e(f), 0.2 + 0.5 * e(f), 0.45 + 1.0 * e(f), -0.08 + 0.4 * e(f)))
    return build(N, 48, steps, body, arm)


@move('tn04_spin_turn', 'Spin Turn')
def spin():
    """the skilled turn: drops low over the ball, spins on the left foot with the right trailing, arms tight, then pops up"""
    N = 12
    steps = [('R', 1, 5, (1.0, -3.2), 3.4), ('R', 5, 9, (3.0, 0.2), 2.4)]
    e = lambda f: env(f, 0, 2, 7, 11)
    body = lambda f: dict(pz=22.7 - 3.0 * e(f), cpitch=0.05 + 0.4 * e(f), croll=0.22 * e(f), proll=0.1 * e(f), cyaw=0.7 * e(f), hyaw=0.8 * e(f), pyaw=0.35 * e(f), hpitch=-0.1 * e(f))
    arm = lambda f: arms((0.12 + 0.3 * e(f), 0.2 + 0.5 * e(f), 0.45 + 0.9 * e(f), -0.08), (0.12 + 0.3 * e(f), 0.2 + 0.5 * e(f), 0.45 + 0.9 * e(f), -0.08))
    return build(N, 52, steps, body, arm)
