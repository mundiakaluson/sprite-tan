"""The 30 SUPPORT skill animations (SP01-SP30): short body gestures (buffs and actions). The glow / numbers are drawn game-side.
Run:  python moves_support.py [id ...]"""
import math, sys
from moves_dribble import Dr, burst, PI
from moves_defend import stance, run, shuffle, hidden

MOVES = {}
UP = (2.7, 0.2, 3.0, 0.1); FWD = (1.55, 0.35, 1.55, 0.15); REST = (0.5, 0.7, 1.1, 0.5); GUARD = (0.7, 0.9, 1.1, 0.6)
HIPS = (0.9, 1.4, 0.5, 1.3)


def move(id_, label):
    def deco(fn):
        MOVES[id_] = (label, fn); return fn
    return deco


def _cl(a):
    return a if a is None else (a[0], min(a[1], 0.45), a[2], a[3])


def D(n, speed=0.0):
    d = Dr(n, speed=speed); hidden(d)
    raw = d.arms
    d.arms = lambda f, r, l, _raw=raw: _raw(f, _cl(r), _cl(l))      # no T-poses: abduction capped
    return d


def idle(d, f0, f1, arms=REST, **kw):
    for f in range(f0, f1 + 1):
        stance(d, f, **kw); d.arms(f, arms, arms)


def env(f, a, b, n):
    """0 -> 1 -> 0 envelope between frames a..b"""
    if f <= a or f >= n: return 0.0
    return math.sin(PI * (f - a) / (n - a))


@move('SP01', 'Tiger Legs')
def sp01():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 14):                                   # fast alternating knee shakes, low and coiled
        ph = 2 * PI * (f - 4) / 3.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.8, 1.0, 0, 3.0 + 4 * a) if a > .05 else (2.8, 1.0, 0, None), L=(-2.8, -0.4, 0, 3.0 + 4 * b) if b > .05 else (-2.8, -0.4, 0, None), pz=21.4, cpitch=0.4, hpitch=0.3)
        d.arms(f, (0.5, 0.9, 1.3, 0.8), (0.5, 0.9, 1.3, 0.8))
    for f in range(14, 24): stance(d, f, low=0.7, hpitch=0.4); d.arms(f, (0.5, 0.9, 1.3, 0.8), (0.5, 0.9, 1.3, 0.8))
    return d.build()


@move('SP02', 'Leap Sprint')
def sp02():
    d = D(22, 2.4); run(d, 0, 4, 0.3)
    d.at(5, R=(2.6, 4.0, 20, 5.0), L=(-2.6, 0.0, 10, None), pz=22.6, cpitch=0.5)
    d.at(6, R=(2.8, 10.0, 40, 16.0), L=(-2.8, -6.0, 40, 14.0), pz=30.0, cpitch=0.3)                  # big bound, legs split in the air
    d.at(7, R=(2.8, 12.0, 40, 18.0), L=(-2.8, -7.0, 40, 16.0), pz=33.0, cpitch=0.3)
    d.at(8, R=(2.8, 9.0, 30, 10.0), L=(-2.8, -4.0, 30, 10.0), pz=29.0, cpitch=0.35)
    d.at(9, R=(2.6, 5.0, 20, None), L=(-2.6, -1.0, 10, 4.0), pz=23.4, cpitch=0.45)
    for f in range(5, 10): d.arms(f, (-0.2, 0.9, 0.2, 0.8), (1.9, 0.5, 2.1, 0.4))
    run(d, 10, 21, 0.35, fx=1.0)
    d.speed(f0=2.4, f5=2.0, f7=3.6, f9=3.0, f12=3.2); d.fx[0] = 0.0
    return d.build()


@move('SP03', 'Muscle Up')
def sp03():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 24):                                    # double bicep pose, chest out, small tremble
        u = min(1.0, (f - 4) / 4.0); t = 0.05 * math.sin(f * 2.2)
        d.at(f, R=(3.2, 0.6, 0, None), L=(-3.2, -0.4, 0, None), pz=22.4, cpitch=-0.15 * u, hpitch=-0.05, croll=t)
        d.arms(f, (1.0 + 0.6 * u, 1.2, 1.55 + 0.5 * u, 0.9), (1.0 + 0.6 * u, 1.2, 1.55 + 0.5 * u, 0.9))
    return d.build()


@move('SP04', 'Sharp Boots')
def sp04():
    d = D(22); idle(d, 0, 2)
    for f in range(3, 22):
        ph = (f - 3) % 6
        a = 1.0 if ph in (2, 3) else 0.0
        d.at(f, R=(2.8, 3.0 + 3 * a, 0, 4.0 if a else None), L=(-2.8, -0.6, 0, None), pz=22.4, cpitch=0.45, hpitch=0.7)     # taps toe on the turf, looks down
        d.arms(f, REST, REST)
    return d.build()


@move('SP05', 'Radar Vision')
def sp05():
    d = D(26); idle(d, 0, 2)
    for f in range(3, 26):
        s = math.sin((f - 3) * 0.55)
        stance(d, f, hyaw=0.9 * s, hpitch=-0.05, pyaw=0.2 * s)
        d.arms(f, (2.3, 0.2, 2.0, 0.5) if True else REST, REST)                                 # hand shading the eyes
    return d.build()


@move('SP06', 'Calm Head')
def sp06():
    d = D(26); idle(d, 0, 3)
    for f in range(4, 26):
        u = env(f, 3, 26, 26)
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.6 + 0.4 * u, cpitch=-0.1 * u, hpitch=-0.5 * u)           # deep breath: arms rise, head tips back
        d.arms(f, (0.5 + 1.2 * u, 0.7 + 0.4 * u, 1.1 + 1.0 * u, 0.5), (0.5 + 1.2 * u, 0.7 + 0.4 * u, 1.1 + 1.0 * u, 0.5))
    return d.build()


@move('SP07', 'Second Wind')
def sp07():
    d = D(28)
    for f in range(0, 12):                                    # bent double, hands on knees, panting
        u = 0.03 * math.sin(f * 1.6)
        d.at(f, R=(2.8, 0.4, 0, None), L=(-2.8, -0.4, 0, None), pz=20.0 + u * 20, cpitch=0.95 + u, hpitch=0.2)
        d.arms(f, (0.4, 0.5, 0.3, 0.2), (0.4, 0.5, 0.3, 0.2))
    for f in range(12, 28):
        u = min(1.0, (f - 12) / 6.0)                          # straightens up, big inhale, arms out
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=20.0 + 3.0 * u, cpitch=0.95 - 1.0 * u, hpitch=-0.3 * u)
        d.arms(f, (0.4 + 1.1 * u, 0.5 + 0.7 * u, 0.3 + 0.8 * u, 0.2), (0.4 + 1.1 * u, 0.5 + 0.7 * u, 0.3 + 0.8 * u, 0.2))
    return d.build()


@move('SP08', 'Hot Streak')
def sp08():
    d = D(22); idle(d, 0, 2)
    d.at(3, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=21.4, cpitch=0.4)
    d.at(4, R=(2.8, 1.0, 0, 4.0), L=(-2.8, -0.6, 0, 4.0), pz=30.0, cpitch=0.1)                 # hop with a fist pump
    d.at(5, R=(2.8, 1.0, 0, 6.0), L=(-2.8, -0.6, 0, 6.0), pz=32.0, cpitch=0.0)
    d.at(6, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.4, cpitch=0.3)
    for f in (3, 4, 5, 6): d.arms(f, (0.7, 0.9, 1.1, 0.6), UP if f in (4, 5) else (1.2, 0.8, 1.8, 0.5))
    idle(d, 7, 21, arms=GUARD)
    return d.build()


@move('SP09', 'Cooldown Pulse')
def sp09():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 24):
        c = 1.0 if (f - 4) % 6 in (3, 4) else 0.0             # claps twice, hands meeting in front of the chest
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.6, cpitch=0.15, hpitch=0.1)
        d.arms(f, (1.4, 0.9 - 0.8 * c, 1.8, 0.1 if c else 0.6), (1.4, 0.9 - 0.8 * c, 1.8, 0.1 if c else 0.6))
    return d.build()


@move('SP10', 'Reset Button')
def sp10():
    d = D(22); idle(d, 0, 4)
    for f in range(5, 22):
        p = max(0.0, math.sin(PI * (f - 5) / 5.0)) if f < 11 else 0.0     # right arm jabs forward like pressing a button
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.6, cpitch=0.2 + 0.1 * p, hpitch=0.3)
        d.arms(f, (1.2 + 0.4 * p, 0.3, 1.45 + 0.1 * p, 0.15), REST)
    return d.build()


@move('SP11', 'Overdrive')
def sp11():
    d = D(28); idle(d, 0, 2)
    for f in range(3, 28):
        u = min(1.0, (f - 3) / 8.0); t = 0.08 * math.sin(f * 3.1) * u
        d.at(f, R=(3.4, 0.6, 0, None), L=(-3.4, -0.4, 0, None), pz=21.4 - 0.4 * u, cpitch=0.5 * (1 - u) + 0.2, hpitch=-0.3 * u, croll=t)     # crouch, shake, arms flung out and back
        d.arms(f, (0.5 + 0.2 * u, 0.9 + 0.8 * u, 1.0 - 0.6 * u, 0.9 + 0.5 * u), (0.5 + 0.2 * u, 0.9 + 0.8 * u, 1.0 - 0.6 * u, 0.9 + 0.5 * u))
    return d.build()


@move('SP12', 'Focus Chain')
def sp12():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 24):
        e = 1.0 if 12 <= f < 18 else 0.0                       # two fists up, then one extends, holding the line
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.4, cpitch=0.3, hpitch=0.25)
        d.arms(f, (1.6 + 0.0 * e, 0.4, 1.55 + 0.05 * e, 0.2 if e else 0.8), (1.5, 0.7, 1.6, 0.9))
    return d.build()


@move('SP13', 'Stamina Boost')
def sp13():
    d = D(24)
    for f in range(24):
        ph = 2 * PI * f / 8.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.8, 0.8, 0, 3.0 + 3 * a) if a > .05 else (2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, 3.0 + 3 * b) if b > .05 else (-2.8, -0.6, 0, None), pz=22.6, cpitch=0.1, hpitch=-0.1)  # easy jog on the spot
        d.arms(f, (0.5 + 0.5 * a, 0.9, 1.0 + 0.6 * a, 0.9), (0.5 + 0.5 * b, 0.9, 1.0 + 0.6 * b, 0.9))
    return d.build()


@move('SP14', 'Steady Hands')
def sp14():
    d = D(24)
    for f in range(24):
        p = 1.0 if (f % 8) in (3, 4) else 0.0
        d.at(f, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=21.4, cpitch=0.5, hpitch=0.2)                 # keeper's crouch, hands patting together
        d.arms(f, (1.3, 0.8 - 0.5 * p, 1.6, 0.5), (1.3, 0.8 - 0.5 * p, 1.6, 0.5))
    return d.build()


@move('SP15', 'Chest Out')
def sp15():
    d = D(22); idle(d, 0, 3)
    for f in range(4, 22):
        u = min(1.0, (f - 4) / 4.0)
        d.at(f, R=(3.2, 0.8, 0, None), L=(-3.2, -0.6, 0, None), pz=23.0, cpitch=-0.3 * u, hpitch=-0.15 * u, ppitch=-0.1 * u)  # puffs out the chest, hands on hips
        d.arms(f, HIPS, HIPS)
    return d.build()


@move('SP16', 'Cold Blood')
def sp16():
    d = D(26); idle(d, 0, 3)
    for f in range(4, 26):
        s = math.sin((f - 4) * 0.7) * min(1.0, (f - 4) / 3.0)
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.8, cpitch=0.0, hyaw=0.5 * s, croll=0.05 * s, hpitch=0.0)    # shrug and a slow shake of the head
        up = 0.5 * max(0.0, math.sin((f - 4) * 0.5))
        d.arms(f, (0.6 + up, 1.2, 1.2 + up, 1.0), (0.6 + up, 1.2, 1.2 + up, 1.0))
    return d.build()


@move('SP17', 'Rhythm')
def sp17():
    d = D(24)
    for f in range(24):
        s = math.sin(2 * PI * f / 8.0)
        d.at(f, R=(2.8 + 0.5 * s, 0.8, 0, 2.0 if s > .3 else None), L=(-2.8 + 0.5 * s, -0.6, 0, 2.0 if s < -.3 else None), pz=22.6 + 0.8 * abs(math.cos(2 * PI * f / 8.0)), cpitch=0.2, croll=0.12 * s)  # bouncing from foot to foot to a beat
        d.arms(f, (0.8 + 0.5 * s, 1.0, 1.2 + 0.5 * s, 0.7), (0.8 - 0.5 * s, 1.0, 1.2 - 0.5 * s, 0.7))
    return d.build()


@move('SP18', 'Pace Surge')
def sp18():
    d = D(22)
    for f in range(0, 5): stance(d, f, low=0.9, cpitch=0.7, hpitch=0.3); d.arms(f, (0.2, 0.9, 0.6, 0.8), (1.0, 0.9, 1.4, 0.8))   # sprinter's crouch
    burst(d, 5, 21, 0.5)
    for f in range(5, 22): d.m.k(f, bvis=0.0)
    d.speed(f0=0.0, f4=0.6, f6=3.0, f12=3.6); d.fx = {0: 0.0, 5: 0.8, 8: 1.2}
    return d.build()


@move('SP19', 'Wide Open')
def sp19():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 24):
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.6, cpitch=0.1, hyaw=-0.8, pyaw=-0.25, hpitch=0.0)     # sweeps an arm out wide: "go wide"
        w = min(1.0, (f - 4) / 4.0)
        d.arms(f, (1.57, 1.3 * w + 0.1, 1.57, 1.5 * w + 0.1), REST)
    return d.build()


@move('SP20', 'Rally the Team')
def sp20():
    d = D(26); idle(d, 0, 2)
    for f in range(3, 26):
        h = 1.0 if (f - 3) % 8 in (4, 5) else 0.0             # both arms up, clapping overhead and hopping
        d.at(f, R=(2.8, 0.8, 0, 3.0 if h else None), L=(-2.8, -0.6, 0, 3.0 if h else None), pz=22.6 + 6 * h, cpitch=-0.1, hpitch=-0.2)
        d.arms(f, (2.7, 0.2 if not (f - 3) % 4 else 0.7, 3.0, 0.1), (2.7, 0.2 if not (f - 3) % 4 else 0.7, 3.0, 0.1))
    return d.build()


@move('SP21', "Captain's Orders")
def sp21():
    d = D(28); idle(d, 0, 3)
    for f in range(4, 28):
        s = -0.9 if f < 15 else 0.9                            # points one way, then the other
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.8, cpitch=0.1, hyaw=s, pyaw=0.25 * s)
        d.arms(f, (1.57, 1.3, 1.57, 1.4) if f < 15 else REST, REST if f < 15 else (1.57, 1.3, 1.57, 1.4))
    return d.build()


@move('SP22', 'Warm Up')
def sp22():
    d = D(26)
    for f in range(26):
        sw = math.sin(2 * PI * f / 10.0)
        d.at(f, R=(2.8, 0.8 + 5 * max(0, sw), 0, 5 * max(0, sw) + 2 if sw > .1 else None), L=(-2.8, -0.6, 0, None), pz=22.6, cpitch=0.2 + 0.2 * max(0, sw), hpitch=0.1)    # leg swings with arm circles
        a = 2 * PI * f / 10.0
        d.arms(f, (1.57 + 0.9 * math.sin(a), 1.2, 1.57 + 0.9 * math.cos(a), 1.2), (1.57 - 0.9 * math.sin(a), 1.2, 1.57 - 0.9 * math.cos(a), 1.2))
    return d.build()


@move('SP23', 'Muscle Memory')
def sp23():
    d = D(26); idle(d, 0, 2)
    for f in range(3, 26):
        k = (f - 3) % 8
        lift = 1.0 if k in (2, 3) else 0.0                     # the same little step twice, tapping the temple between
        d.at(f, R=(2.8, 0.8 + 3 * lift, 0, 4.0 if lift else None), L=(-2.8, -0.6, 0, None), pz=22.6, cpitch=0.2, hpitch=0.2, hyaw=0.2 * lift)
        d.arms(f, (2.4, 0.2, 2.0, 0.9) if k >= 5 else REST, REST)
    return d.build()


@move('SP24', 'Sixth Sense')
def sp24():
    d = D(26); idle(d, 0, 3)
    for f in range(4, 26):
        s = math.sin((f - 4) * 0.5)
        stance(d, f, hyaw=0.9 * s, hpitch=-0.05)
        d.arms(f, (2.5, 0.3, 2.3, 0.9), REST)                                                   # fingertip to the temple, head sweeping
    return d.build()


@move('SP25', 'Fresh Legs')
def sp25():
    d = D(28)
    for f in range(28):
        ph = 2 * PI * f / 8.0; a = max(0.0, math.sin(ph)); b = max(0.0, -math.sin(ph))
        d.at(f, R=(2.8, 0.8 + 3 * a, 0, 4.0 + 6 * a) if a > .05 else (2.8, 0.8, 0, None), L=(-2.8, -0.6 + 3 * b, 0, 4.0 + 6 * b) if b > .05 else (-2.8, -0.6, 0, None), pz=22.6, cpitch=0.45, hpitch=0.5)   # hands on knees, shaking the legs out
        d.arms(f, (0.5, 0.6, 0.5, 0.3), (0.5, 0.6, 0.5, 0.3))
    return d.build()


@move('SP26', 'Decoy Run')
def sp26():
    d = D(26, 2.2); run(d, 0, 25, 0.25, cad=0.9, fx=0.5)
    d.turn(**{'f0': 0.0, 'f8': 0.5, 'f14': 0.5, 'f20': -0.3, 'f25': -0.3})
    for f in range(26): d.m.k(f, hyaw=-0.5); d.arms(f, (0.6, 0.8, 1.0, 0.6), (1.55, 0.35, 1.55, 0.15))        # drags the defenders, calling for it with a pointing arm
    return d.build()


@move('SP27', 'Two Touch')
def sp27():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 24):
        k = (f - 4) % 8
        t = 1.0 if k in (1, 5) else 0.0                        # two quick taps of the boot
        d.at(f, R=(2.8, 1.5 + 2 * t, 0, 2.5 if t else None), L=(-2.8, -0.6, 0, None), pz=22.6, cpitch=0.3, hpitch=0.4)
        d.arms(f, (1.57, 0.4, 2.2, 0.2), REST)                                                   # two fingers up
    return d.build()


@move('SP28', 'Battle Ready')
def sp28():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 24):
        hit = 1.0 if f in (8, 9, 14, 15) else 0.0              # slams a fist into the palm, low and wide
        d.at(f, R=(3.4, 0.8, 0, None), L=(-3.4, -0.6, 0, None), pz=21.4, cpitch=0.45, hpitch=0.3)
        d.arms(f, (1.5, 0.9 - 0.7 * hit, 1.7, 0.15 if hit else 0.7), (1.5, 0.9 - 0.7 * hit, 1.7, 0.15 if hit else 0.7))
    return d.build()


@move('SP29', 'Clean Slate')
def sp29():
    d = D(24); idle(d, 0, 3)
    for f in range(4, 24):
        s = math.sin((f - 4) * 0.8)
        d.at(f, R=(2.8, 0.8, 0, None), L=(-2.8, -0.6, 0, None), pz=22.6, cpitch=0.15, hyaw=0.2 * s)  # wipes the board clean: a flat hand sweeping side to side
        d.arms(f, (1.57, 0.2 + 0.9 * (0.5 + 0.5 * s), 1.57, 0.2 + 0.9 * (0.5 + 0.5 * s)), (1.57, 0.2 + 0.9 * (0.5 - 0.5 * s), 1.57, 0.2 + 0.9 * (0.5 - 0.5 * s)))
    return d.build()


@move('SP30', 'Warp Boots')
def sp30():
    d = D(24)
    for f in range(0, 8):
        s = math.sin(f * 2.6)
        d.at(f, R=(2.8, 1.0, 0, 3.0 if s > 0 else None), L=(-2.8, -0.6, 0, 3.0 if s < 0 else None), pz=22.0, cpitch=0.3, hpitch=0.5)       # stomps the boots together...
        d.arms(f, GUARD, GUARD)
    burst(d, 8, 23, 0.5)
    for f in range(8, 24): d.m.k(f, bvis=0.0)
    d.speed(f0=0.0, f7=0.4, f9=4.2, f23=4.4); d.fx = {0: 0.0, 8: 1.3, 23: 1.3}                       # ...and vanishes down the pitch
    return d.build()


def build(ids=None):
    out = []
    for id_, (label, fn) in MOVES.items():
        if ids and id_ not in ids: continue
        m = fn(); name = id_.lower() + '_' + label.lower().replace(' ', '_').replace("'", '')
        m.save(name, label, 'auto-generated by sprites/moves_support.py'); out.append((id_, name))
    return out


if __name__ == '__main__':
    for id_, name in build(sys.argv[1:] or None): print(id_, name)
