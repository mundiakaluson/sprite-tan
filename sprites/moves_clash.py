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


def retired(id_, label, loop=False):          # kept for reference, not built (looked poor at match zoom)
    def deco(fn): return fn
    return deco


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


@move('cl03_clash_bolt', 'Clash Bolt (frozen head-on sprint)', True)
def clash_bolt():
    """the two have bolted at each other: caught mid-stride, thrown forward hard, the front knee driving up, the back leg stretched out behind
    with only the toe still on the grass (the push-off), arms pumping opposite (front arm bent up in front, back arm driven behind), eyes on the man.
    Held while the cards are picked: it strains (the lean, the knee and the arms shiver a little) so it never looks paused"""
    N = 12; d = Dr(N, ms=70, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N):
        ph = 2 * PI * f / N
        sh = math.sin(ph * 2); tr = math.sin(ph * 3 + 0.7)
        d.at(f, R=(1.6, 5.4 + 0.2 * sh, -30, 7.4 + 0.3 * tr), L=(-1.4, -11.0 - 0.2 * sh, 52, 0.6),
             pz=20.2 + 0.25 * tr, cpitch=0.85 + 0.03 * sh, ppitch=0.35, croll=0.04 * tr, cyaw=0.12, pyaw=-0.1,
             hpitch=-0.45, hyaw=-0.04 * tr)
        front = (1.5 + 0.05 * sh, 0.15, 2.1, 0.0)                        # bent up in front (the arm opposite the driving knee)
        back = (-1.0 - 0.05 * sh, 0.2, 0.7, 0.0)                         # driven back behind him
        d.arms(f, back, front)
    hidden(d); return d.m


# ---------------------------------------------------------------- more clash stances (held loops). Which one a player strikes comes from
# his role and personality (players.csv traits): sprinters bolt, defenders crouch or load a slide, proud players aura-farm or point.
HIP = (-0.15, 0.95, 1.55, -1.25)          # hand on the hip: elbow out, forearm folded back in
def held(N=12, ms=70):
    d = Dr(N, ms=ms, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    return d


@retired('cl04_clash_low_guard', 'Clash Low Guard', True)
def low_guard():
    """the defender's set: wide, low, weight on the toes, arms out low and wide to make himself big, eyes on the ball"""
    d = held()
    for f in range(d.N):
        ph = 2 * PI * f / d.N; tr = math.sin(ph * 2)
        d.at(f, R=(4.6, 1.2 + 0.2 * tr, 0, None), L=(-4.6, -0.6 - 0.2 * tr, 0, None), pz=18.4 + 0.25 * math.sin(ph * 3), cpitch=0.42, ppitch=0.15, hpitch=-0.1, croll=0.04 * tr)
        a = (0.55, 1.05 + 0.04 * tr, 0.8, 0.25)
        d.arms(f, a, (a[0], a[1] - 0.08 * tr, a[2], a[3]))
    hidden(d); return d.m


@move('cl05_clash_shoulder', 'Clash Shoulder Brace', True)
def shoulder():
    """turned side-on, the lead shoulder dropped into the contact, feet staggered and braced, lead arm tucked, back arm driving"""
    d = held()
    for f in range(d.N):
        ph = 2 * PI * f / d.N; tr = math.sin(ph * 3 + 0.4)
        d.at(f, R=(2.4, 3.8, 0, None), L=(-2.4, -4.8, 25, 0.4), pz=19.8 + 0.2 * tr, cpitch=0.35, ppitch=0.15, cyaw=0.62, pyaw=0.3, croll=0.22 + 0.03 * tr, hyaw=-0.45, hpitch=-0.1)
        d.arms(f, (-0.6, 0.3, 0.7, 0.0), (0.3, 0.12, 1.7, -0.7))
    hidden(d); return d.m


@move('cl06_clash_sole', 'Clash Sole On The Ball', True)
def sole():
    """cocky: upright, the sole resting on top of the ball, hands on the hips, a little bounce, looking straight at him"""
    d = held(14)
    for f in range(d.N):
        ph = 2 * PI * f / d.N
        d.at(f, R=(0.9, 5.2, 12, 4.4 + 0.25 * math.sin(ph)), L=(-2.2, -1.4, 0, None), pz=23.0 + 0.2 * math.sin(ph * 2), cpitch=-0.06, hpitch=-0.12, cyaw=0.1)
        d.arms(f, HIP, HIP)
    hidden(d); return d.m


@move('cl07_clash_stepover', 'Clash Step-Over Freeze', True)
def stepover():
    """caught in the middle of a step-over: the leg circling out over the ball, body leaning the other way, arms wide for balance"""
    d = held()
    for f in range(d.N):
        ph = 2 * PI * f / d.N; tr = math.sin(ph * 2)
        d.at(f, R=(3.8 + 0.2 * tr, 4.4, 0, 4.2 + 0.3 * tr), L=(-2.6, -1.0, 0, None), pz=21.2, cpitch=0.25, croll=-0.28, proll=-0.1, hpitch=0.1)
        d.arms(f, (0.7, 1.35, 0.5, 0.3), (0.5, 1.25 + 0.05 * tr, 0.6, 0.3))
    hidden(d); return d.m


@move('cl08_clash_slide_load', 'Clash Slide Loaded', True)
def slide_load():
    """dropping into a slide: back knee folded deep, the leading leg shot out along the grass at the ball, leaning back, one hand reaching down"""
    d = held()
    for f in range(d.N):
        ph = 2 * PI * f / d.N; tr = math.sin(ph * 3)
        d.at(f, R=(1.0, 12.4 + 0.3 * tr, 55, 1.2), L=(-2.0, -2.2, 0, None), pz=14.8 + 0.2 * tr, cpitch=-0.25, ppitch=-0.35, hpitch=0.3)
        d.arms(f, (1.6, 0.5, 1.0, 0.1), (-0.3, 0.7, 0.2, 0.0))
    hidden(d); return d.m


@move('cl09_clash_aura_farm', 'Clash Aura Farm', True)
def aura_farm():
    """the proud one: does not bother to move. Stands tall, chest out, chin up, arms hanging a little away from the body, fists loose; just breathes"""
    d = held(16, 80)
    for f in range(d.N):
        ph = 2 * PI * f / d.N; br = math.sin(ph)
        d.at(f, R=(3.0, 0.4, 0, None), L=(-3.0, -0.2, 0, None), pz=23.5 + 0.15 * br, cpitch=-0.16 - 0.03 * br, hpitch=-0.28, croll=0.0)
        a = (0.08, 0.42 + 0.03 * br, 0.25, 0.1)
        d.arms(f, a, a)
    hidden(d); return d.m


@move('cl10_clash_point', 'Clash Proud Point', True)
def point():
    """points straight at the opponent, arm locked out, other hand on the hip, chin up: you, come on then"""
    d = held(16, 80)
    for f in range(d.N):
        ph = 2 * PI * f / d.N; jab = 0.06 * math.sin(ph * 2)
        d.at(f, R=(2.8, 0.6, 0, None), L=(-2.8, -0.4, 0, None), pz=23.3, cpitch=-0.1, hpitch=-0.2, cyaw=-0.15, pyaw=-0.08)
        d.arms(f, (1.5 + jab, 0.12, 1.5 + jab, 0.0), HIP)
    hidden(d); return d.m


@retired('cl11_clash_arms_crossed', 'Clash Arms Crossed', True)
def arms_crossed():
    """the wall: feet apart, arms folded across the chest, weight back, unimpressed"""
    d = held(16, 80)
    for f in range(d.N):
        ph = 2 * PI * f / d.N; br = math.sin(ph)
        d.at(f, R=(3.6, 0.2, 0, None), L=(-3.6, 0.0, 0, None), pz=23.2 + 0.12 * br, cpitch=-0.12, hpitch=-0.15)
        d.arms(f, (0.45, 0.2, 1.65, -1.35), (0.5, 0.2, 1.6, -1.3))
    hidden(d); return d.m


@move('cl12_clash_beckon', 'Clash Beckon', True)
def beckon():
    """come on then: one hand out in front, palm up, fingers curling him in, the other on the hip, a little rock on the heels"""
    d = held(12, 75)
    for f in range(d.N):
        ph = 2 * PI * f / d.N; cu = 0.5 + 0.5 * math.sin(ph * 2)
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.8, 0, None), pz=23.0 + 0.15 * math.sin(ph), cpitch=-0.05 - 0.05 * math.sin(ph), hpitch=-0.15)
        d.arms(f, (1.0, 0.2, 1.8 + 0.8 * cu, 0.0), HIP)
    hidden(d); return d.m


@move('cl13_clash_airborne', 'Clash Airborne Kick', True)
def airborne():
    """both off the ground into it (the Tsubasa picture): leaping, the kicking leg cocked out high at the ball, the other tucked under,
    leaning back, arms flung out for balance; hangs in the air with a slight float"""
    d = held()
    for f in range(d.N):
        ph = 2 * PI * f / d.N; fl = math.sin(ph)
        up = 5.5 + 0.4 * fl
        d.at(f, R=(1.0, 9.0, 20, 9.5 + up), L=(-1.6, -2.4, -40, 4.5 + up), pz=23.0 + up, cpitch=-0.28, ppitch=-0.2, hpitch=0.35, croll=0.05 * fl)
        d.arms(f, (2.2, 0.9, 1.8, 0.2), (-0.8, 0.85, 0.5, 0.2))
    hidden(d); return d.m


@move('cl14_clash_bull', 'Clash Bull Charge', True)
def bull():
    """head down, shoulders forward, arms thrown back, charging straight through him"""
    d = held()
    for f in range(d.N):
        ph = 2 * PI * f / d.N; tr = math.sin(ph * 3)
        d.at(f, R=(2.0, 4.6, 0, 1.0), L=(-1.8, -7.2, 42, 0.5), pz=20.4 + 0.2 * tr, cpitch=0.95, ppitch=0.3, hpitch=0.45)
        a = (-0.95, 0.35 + 0.03 * tr, 0.8, 0.0)
        d.arms(f, a, (a[0], a[1], a[2], a[3]))
    hidden(d); return d.m


# ================================================================ the big set: one builder, many stances
# pose(f, ph) returns (R, L, body dict, right arm, left arm); `up` lifts the whole body (airborne). Tiers for the airborne ones: the game picks
# how high / how extreme from the player's stats (PHY + PAC for height, DRI + SHO for the acrobatic ones), 1 = athletic, 2 = elite, 3 = godlike.
UPA = (2.8, 0.25, 2.9, 0.1)        # arm straight up
WIDE = (0.25, 1.55, 0.35, 0.2)     # arm out to the side
BACK = (-1.0, 0.3, 0.7, 0.0)       # driven back
FWD = (1.5, 0.15, 1.4, 0.0)        # straight out in front
BENTUP = (1.5, 0.15, 2.2, 0.0)     # bent up in front (running)
FLEX = (0.3, 1.45, 2.6, 0.3)       # upper arm out, forearm up: the bicep
PALM = (1.1, 0.35, 1.3, 0.3)       # palm out, open


def stance(id_, label, pose, N=12, ms=70):
    def fn():
        d = held(N, ms)
        for f in range(d.N):
            ph = 2 * PI * f / d.N
            R, L, body, ra, la = pose(f, ph)
            d.at(f, R=R, L=L, **body); d.arms(f, ra, la)
        hidden(d); return d.m
    MOVES[id_] = (label, fn, True)


def air(lift, fl, ph):
    return lift + 0.5 * math.sin(ph) * fl


# ---- airborne family (tier in the id: a1 athletic, a2 elite, a3 godlike)
stance('cl20_air_knee_drive_a1', 'Air Knee Drive (athletic)', lambda f, ph: (
    (1.6, 2.5, -30, 7.5 + air(4, 1, ph)), (-1.6, -2.0, -40, 5.0 + air(4, 1, ph)),
    dict(pz=24 + air(4, 1, ph), cpitch=0.1, hpitch=-0.2), UPA, WIDE))
stance('cl21_air_scissor_a2', 'Air Scissor (elite)', lambda f, ph: (
    (1.0, 8.5 + 0.6 * math.sin(ph * 2), 25, 9.0 + air(7, 1, ph)), (-1.2, -6.5 - 0.6 * math.sin(ph * 2), 45, 4.0 + air(7, 1, ph)),
    dict(pz=24 + air(7, 1, ph), cpitch=0.05, ppitch=-0.1, hpitch=0.1, croll=0.05 * math.sin(ph)), WIDE, (0.4, 1.4, 0.5, 0.2)))
stance('cl22_air_flying_kick_a2', 'Air Flying Side Kick (elite)', lambda f, ph: (
    (1.0, 11.0, 15, 12.0 + air(7, 1, ph)), (-1.0, -2.5, -60, 6.5 + air(7, 1, ph)),
    dict(pz=23 + air(7, 1, ph), cpitch=-0.55, ppitch=-0.45, croll=0.25, hpitch=0.35), (2.0, 1.1, 1.6, 0.2), (-0.6, 1.0, 0.4, 0.2)))
stance('cl23_air_bicycle_a3', 'Air Bicycle Set (godlike)', lambda f, ph: (
    (0.8, 6.0, -20, 18.0 + air(10, 1, ph)), (-0.8, 2.0, 30, 9.0 + air(10, 1, ph)),
    dict(pz=22 + air(10, 1, ph), cpitch=-1.15, ppitch=-0.9, hpitch=0.6), (0.2, 1.5, 0.3, 0.3), (0.3, 1.4, 0.3, 0.3)))
stance('cl24_air_superman_a3', 'Air Superman Dive (godlike)', lambda f, ph: (
    (1.0, -9.0, 70, 10.0 + air(9, 1, ph)), (-1.0, -9.5, 70, 10.5 + air(9, 1, ph)),
    dict(pz=19 + air(9, 1, ph), cpitch=1.35, ppitch=1.2, hpitch=-0.9), BACK, BACK))
stance('cl25_air_split_a3', 'Air Split (godlike)', lambda f, ph: (
    (1.2, 11.0, 10, 9.0 + air(10, 1, ph)), (-1.2, -11.0, 50, 9.0 + air(10, 1, ph)),
    dict(pz=21 + air(10, 1, ph), cpitch=0.1, hpitch=-0.15), WIDE, WIDE))
stance('cl26_air_tornado_a3', 'Air Tornado Twist (godlike)', lambda f, ph: (
    (3.0, 6.0, 0, 8.0 + air(9, 1, ph)), (-1.0, -1.0, -50, 6.0 + air(9, 1, ph)),
    dict(pz=24 + air(9, 1, ph), cyaw=0.9 + 0.12 * math.sin(ph * 2), pyaw=0.4, croll=-0.2, hyaw=-0.7), (0.9, 0.2, 2.2, -0.9), (0.9, 0.2, 2.2, -0.9)))
stance('cl27_air_volley_cock_a2', 'Air Volley Cocked (elite)', lambda f, ph: (
    (1.2, -6.5, 60, 13.0 + air(6, 1, ph)), (-1.2, 2.0, -30, 6.0 + air(6, 1, ph)),
    dict(pz=24 + air(6, 1, ph), cpitch=0.5, ppitch=0.3, hpitch=0.4), FWD, (-0.4, 1.3, 0.4, 0.2)))
stance('cl28_air_hover_god_a3', 'Air Hover (godlike)', lambda f, ph: (
    (1.6, 1.5, -40, 6.0 + air(13, 1.6, ph)), (-1.6, -1.0, -40, 6.5 + air(13, 1.6, ph)),
    dict(pz=24 + air(13, 1.6, ph), cpitch=-0.05, hpitch=-0.25), (0.35, 1.7, 0.6, 0.6), (0.35, 1.7, 0.6, 0.6)))
stance('cl29_air_header_leap_a1', 'Air Header Leap (athletic)', lambda f, ph: (
    (1.6, -2.0, -45, 6.5 + air(5, 1, ph)), (-1.6, -2.5, -45, 6.0 + air(5, 1, ph)),
    dict(pz=24 + air(5, 1, ph), cpitch=-0.35, hpitch=-0.6), (2.3, 0.8, 2.0, 0.2), (2.3, 0.8, 2.0, 0.2)))
stance('cl30_air_overhead_a3', 'Air Overhead Arc (godlike)', lambda f, ph: (
    (0.8, 9.0, -30, 22.0 + air(11, 1, ph)), (-0.8, -3.0, 40, 12.0 + air(11, 1, ph)),
    dict(pz=21 + air(11, 1, ph), cpitch=-1.35, ppitch=-1.1, croll=0.15, hpitch=0.8), UPA, WIDE))

# ---- attackers on the ground
stance('cl31_bolt_low', 'Bolt Low', lambda f, ph: (
    (1.6, 6.0, -30, 6.0 + 0.3 * math.sin(ph * 3)), (-1.4, -12.0, 55, 0.5),
    dict(pz=18.8 + 0.25 * math.sin(ph * 3), cpitch=1.05, ppitch=0.45, hpitch=-0.7), BACK, BENTUP))
stance('cl32_cut_plant', 'Cut Planted', lambda f, ph: (
    (5.5, 1.5, 0, None), (-1.0, -1.0, 0, 1.0),
    dict(pz=19.0 + 0.2 * math.sin(ph * 3), croll=-0.45, proll=-0.25, cpitch=0.3, hyaw=-0.3), (0.6, 1.4, 0.6, 0.3), (0.8, 0.4, 1.2, 0.1)))
stance('cl33_drag_back', 'Drag Back Freeze', lambda f, ph: (
    (0.6, 3.5, 10, 4.2), (-2.2, -2.5, 0, None),
    dict(pz=22.0, cpitch=-0.25, ppitch=-0.1, hpitch=0.2), (0.5, 0.9, 0.6, 0.2), (0.5, 0.9, 0.6, 0.2)))
stance('cl34_spin_back', 'Spin, Back To Him', lambda f, ph: (
    (2.6, 1.0, 0, None), (-2.6, -1.0, 0, None),
    dict(pz=21.6, cyaw=2.6 + 0.08 * math.sin(ph * 2), pyaw=2.3, cpitch=0.3, hyaw=0.9), (0.4, 1.2, 0.5, 0.2), (0.9, 0.6, 1.0, 0.1)))
stance('cl35_shoulder_drop', 'Shoulder Drop Feint', lambda f, ph: (
    (3.2, 2.0, 0, None), (-2.6, -1.5, 0, 0.8),
    dict(pz=20.4, croll=0.55 + 0.04 * math.sin(ph * 2), proll=0.2, cpitch=0.3, hyaw=0.4), (0.1, 0.6, 0.4, 0.1), (0.4, 1.6, 0.5, 0.3)))
stance('cl36_heel_lift', 'Heel Lift Set', lambda f, ph: (
    (0.2, -3.5, -60, 7.5), (-2.2, 0.5, 0, None),
    dict(pz=22.6, cpitch=0.15, hpitch=0.2), (0.4, 1.2, 0.5, 0.2), (0.4, 1.2, 0.5, 0.2)))
stance('cl37_scream_charge', 'Scream Charge', lambda f, ph: (
    (2.0, 4.2, 0, 1.5), (-1.8, -6.5, 40, 0.5),
    dict(pz=21.0, cpitch=0.25, hpitch=-0.6), (-0.6, 1.0, 0.4, 0.2), (-0.6, 1.0, 0.4, 0.2)))

# ---- defenders
stance('cl40_block_stretch', 'Block Stretch', lambda f, ph: (
    (6.5, 4.0, 30, 2.5 + 0.2 * math.sin(ph * 3)), (-2.4, -1.5, 0, None),
    dict(pz=18.6, croll=-0.35, cpitch=0.25, proll=-0.2), WIDE, (0.6, 0.5, 0.8, 0.2)))
stance('cl41_stand_tackle', 'Stand Tackle Lunge', lambda f, ph: (
    (0.9, 9.5, 20, 1.8 + 0.2 * math.sin(ph * 3)), (-2.2, -4.0, 0, None),
    dict(pz=18.0, cpitch=0.55, ppitch=0.1, hpitch=0.35), BACK, (1.0, 0.8, 0.8, 0.2)))
stance('cl42_jockey_side', 'Jockey Side-On', lambda f, ph: (
    (3.4, 1.8 + 0.3 * math.sin(ph), 0, None), (-3.0, -2.2, 0, None),
    dict(pz=20.4 + 0.2 * math.sin(ph * 2), cyaw=0.5, pyaw=0.35, cpitch=0.35, hyaw=-0.5), (0.7, 0.9, 0.9, 0.2), (0.5, 0.3, 0.9, 0.1)))
stance('cl43_hip_check', 'Hip Check', lambda f, ph: (
    (3.0, 2.0, 0, None), (-3.0, -2.0, 0, None),
    dict(pz=20.8, pyaw=0.8, cyaw=0.6, proll=0.3, croll=0.15, cpitch=0.2, hyaw=-0.6), (-0.4, 0.5, 1.2, 0.0), (0.3, 1.0, 1.0, 0.2)))
stance('cl44_intercept_reach', 'Intercept Reach', lambda f, ph: (
    (5.0, 7.0, 25, 1.5), (-2.0, -3.0, 0, None),
    dict(pz=18.4, croll=-0.4, cpitch=0.45, hyaw=0.3), FWD, (0.2, 1.4, 0.4, 0.2)))
stance('cl45_slide_full', 'Full Slide', lambda f, ph: (
    (0.8, 13.5 + 0.4 * math.sin(ph * 3), 70, 1.0), (-1.4, 1.0, 40, 1.0),
    dict(pz=11.5, cpitch=-0.55, ppitch=-0.6, hpitch=0.5), (1.5, 0.6, 1.0, 0.1), (-0.5, 0.9, 0.2, 0.0)))

# ---- showmen (the proud ones)
stance('cl50_shrug', 'Shrug, Is That All', lambda f, ph: (
    (3.0, 0.4, 0, None), (-3.0, -0.2, 0, None),
    dict(pz=23.4 + 0.1 * math.sin(ph), cpitch=-0.12, hpitch=-0.2, hroll=0.15), (0.6, 1.2, 1.5, 0.6), (0.6, 1.2, 1.5, 0.6)), 16, 80)
stance('cl51_finger_wag', 'Finger Wag, No No', lambda f, ph: (
    (2.8, 0.6, 0, None), (-2.8, -0.4, 0, None),
    dict(pz=23.3, cpitch=-0.08, hpitch=-0.15, hyaw=0.12 * math.sin(ph * 2)), (1.0, 0.3 + 0.35 * math.sin(ph * 2), 2.3, 0.0), HIP), 12, 75)
stance('cl52_flex', 'Flex', lambda f, ph: (
    (3.2, 0.3, 0, None), (-3.2, -0.3, 0, None),
    dict(pz=23.2 + 0.1 * math.sin(ph), cpitch=-0.15, hpitch=-0.25), FLEX, FLEX), 16, 80)
stance('cl53_roar', 'Roar', lambda f, ph: (
    (3.4, 0.6, 0, None), (-3.4, -0.4, 0, None),
    dict(pz=22.2 + 0.2 * math.sin(ph * 2), cpitch=0.3, hpitch=-0.75), (0.5, 0.9, 0.9, 0.4), (0.5, 0.9, 0.9, 0.4)))
stance('cl54_hands_behind', 'Hands Behind, Calm', lambda f, ph: (
    (2.6, 0.4, 0, None), (-2.6, -0.2, 0, None),
    dict(pz=23.5 + 0.1 * math.sin(ph), cpitch=-0.1, hpitch=-0.15), (-0.5, 0.3, 1.4, 0.6), (-0.5, 0.3, 1.4, 0.6)), 16, 80)
stance('cl55_temple', 'Finger To Temple', lambda f, ph: (
    (2.8, 0.4, 0, None), (-2.8, -0.3, 0, None),
    dict(pz=23.3, cpitch=-0.05, hpitch=-0.1), (0.4, 1.0, 2.9, -0.6), HIP), 16, 80)
stance('cl56_salute', 'Salute', lambda f, ph: (
    (2.6, 0.3, 0, None), (-2.6, -0.2, 0, None),
    dict(pz=23.5, cpitch=-0.12, hpitch=-0.2), (1.2, 0.9, 2.8, -0.7), (0.1, 0.3, 0.3, 0.0)), 16, 80)
stance('cl57_palm_out', 'Stop Sign Palm', lambda f, ph: (
    (2.8, 0.8, 0, None), (-2.8, -0.6, 0, None),
    dict(pz=23.2, cpitch=0.0, hpitch=-0.2, cyaw=-0.1), (1.5, 0.2, 1.65, 0.0), HIP), 16, 80)


def build(ids=None):
    out = []
    for id_, (label, fn, loop) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); m.loop = loop; m.save(id_, label, 'clash, sprites/moves_clash.py'); out.append(id_)
    return out


if __name__ == '__main__':
    for n in build(sys.argv[1:] or None): print(n)
