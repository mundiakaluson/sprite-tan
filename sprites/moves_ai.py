"""Clips for the real-football AI layer (behaviour catalogue batches 1-7, godot/CLAUDE.md "Real-football AI layer").
Same framework as moves_contest.py (eased continuous curves). Run:  python moves_ai.py [id ...]  -> data/animations/<id>.json, then bake each:
python custom_anims.py <id>  (or the tool's Animations tab), then Export to game.
  sc01_shoulder_check   a look over the right shoulder (scanning before receiving; the game mirrors it for the left)
  ti01_throw_in         a standing throw-in, both hands, ball behind the head, arched back, whip            (ball track: the game keeps the ball in his hands)
  ti02_long_throw       a run-up long throw: three steps, plant both feet, big arch, catapult
  bl01_block            side-on block: steps across the line of the shot, leg out, arms tucked behind the back, flinch at the strike
  gk36_punch            keeper two-fist punch: crouch, jump, both fists driven through the ball
  wl01_wall_stand       in the wall: feet together, hands covering, little bounce (loop)
  wl02_wall_jump        the wall jumps as the free kick is struck, hands covering, head turned away
  sh01_shield           shielding the ball: low, wide, side-on, the near arm held out against the man, glancing back at him (loop)
  jk01_jockey           side-on jockey: low, short shuffles, weight on the balls of the feet, eyes on the ball (loop)
  fl01_shirt_pull       tactical foul: reaches out, grabs the shirt and drags back, leaning away
  pk01_penalty_runup    penalty run-up: a few steps with a stutter before the strike (the game then plays the shot)
  gk37_penalty_line     keeper on his line at a penalty: wide, arms out, swaying side to side (loop)
  ap01_offside_appeal   a defender appeals for offside: arm straight up, looking across at the linesman, walking out"""
import math, sys
from moves_dribble import Dr
from moves_defend import hidden
from moves_fluid import sm, lerp, mix, REST

PI = math.pi
MOVES = {}


def move(id_, label, loop=False):
    def deco(fn):
        MOVES[id_] = (label, fn, loop); return fn
    return deco


def still(d):
    for f in range(d.N): d.lt[f] = 0.0; d.sp[f] = 0.0


def stand(d, f, **kw):
    b = dict(pz=22.7, cpitch=0.05, hpitch=0.1); b.update(kw)
    d.at(f, R=(2.9, 0.4, 0, None), L=(-2.9, -0.2, 0, None), **b)


def bump(f, a, b, c, e):
    """0 -> 1 between frames a..b, holds, 1 -> 0 between c..e"""
    return sm((f - a) / max(b - a, 0.01)) * (1 - sm((f - c) / max(e - c, 0.01)))


# ---------------------------------------------------------------- scanning
@move('sc01_shoulder_check', 'Shoulder Check (scan)')
def shoulder_check():
    """the head snaps round over the right shoulder, the shoulders follow a little, a beat looking, and back to the ball"""
    N = 10; d = Dr(N, ms=45, speed=0.0); d.m.events = {'look': 4}; still(d)
    for f in range(N):
        u = bump(f, 0, 3, 5.5, 9)
        stand(d, f, hyaw=-1.3 * u, cyaw=-0.45 * u, pyaw=-0.12 * u, hpitch=0.1 - 0.08 * u, pz=22.7 - 0.2 * u)
        d.arms(f, mix(REST, (0.35, 0.3, 0.8, -0.05), u), mix(REST, (0.1, 0.25, 0.5, -0.1), u))
    hidden(d); return d.m


# ---------------------------------------------------------------- throw-ins
def throw_body(d, f0, N, big=1.0):
    """wind: the ball goes up and back behind the head, the back arches; whip: everything comes through, release at f0 + 7"""
    for f in range(f0, N):
        t = f - f0
        up = sm(t / 3.0)                                       # ball lifted overhead
        back = bump(t, 2, 5.5, 6.5, 8.0)                       # behind the head, arched
        whip = sm((t - 6.0) / 2.0)                             # through
        fol = sm((t - 8.0) / 4.0)                              # follow-through, settle
        arch = -0.35 * big * back + 0.4 * whip * (1 - 0.5 * fol)
        d.at(f, R=(2.4, 2.2, 0, None), L=(-2.4, -1.6 if big < 1.2 else -3.0, 0, None if t < 7 or big < 1.2 else 0.8),   # back toe drags on a long throw
             pz=22.7 - 0.8 * back - 0.9 * whip * (1 - fol), cpitch=arch, ppitch=0.15 * whip - 0.1 * back, hpitch=-0.25 * back + 0.2 * whip)
        a_up = (2.9, 0.18, 3.0, 0.1)
        a_back = (3.2, 0.2, 3.55, 0.15)
        a_rel = (2.0, 0.15, 1.7, 0.05)
        a = mix(mix(REST, a_up, up), a_back, back)
        a = mix(a, a_rel, whip)
        a = mix(a, mix(a_rel, (1.0, 0.2, 1.1, 0.0), 0.6), fol)
        d.arms(f, a, a)


def ball_overhead(d, f_from, f_to):
    """the ball between his hands from f_from up to the release (the game keeps the real ball there through the clip)"""
    from moves_keeper import ball_in_hands
    ball_in_hands(d.m, range(f_from, f_to + 1))
    for f in range(f_to + 1, d.N): d.m.k(f, bvis=0.0)
    for f in range(0, f_from): d.m.k(f, bvis=0.0)


@move('ti01_throw_in', 'Throw-In')
def throw_in():
    N = 18; d = Dr(N, ms=55, speed=0.0); d.m.events = {'strike': 7}; still(d)
    throw_body(d, 0, N, 1.0)
    ball_overhead(d, 0, 7)
    return d.m


@move('ti02_long_throw', 'Long Throw (run-up)')
def long_throw():
    N = 24; f0 = 6; d = Dr(N, ms=55, speed=0.0); d.m.events = {'strike': f0 + 7}
    for f in range(N): d.lt[f] = 0.0
    d.speed(f0=2.2, f5=2.0, f6=0.4, f8=0.0)
    for f in range(f0):                                        # run-up with the ball held up in front
        ph = f / 6.0 * 2 * PI
        sw = math.sin(ph)
        d.at(f, R=(2.6, 2.0 * sw, 0, 2.2 * max(0, -sw) if sw < -0.2 else None), L=(-2.6, -2.0 * sw, 0, 2.2 * max(0, sw) if sw > 0.2 else None),
             pz=22.9 + 0.4 * abs(math.cos(ph)), cpitch=0.12, hpitch=0.05)
        d.arms(f, (2.6, 0.18, 2.9, 0.1), (2.6, 0.18, 2.9, 0.1))
    throw_body(d, f0, N, 1.4)
    ball_overhead(d, 0, f0 + 7)
    return d.m


# ---------------------------------------------------------------- blocks, keeper punch, the wall
@move('bl01_block', 'Block (side-on, arms behind)')
def block():
    """steps across into the line of the shot, turns side-on and slides the near leg out wide, arms tucked behind the back (no handball), flinches as it is struck"""
    N = 16; d = Dr(N, ms=50, speed=0.0); d.m.events = {'strike': 6}; still(d)
    d.lateral(f0=0.0, f2=1.2, f5=0.6, f7=0.0)
    for f in range(N):
        step = sm(f / 3.0)
        out = bump(f, 2, 5, 9, 14)
        flinch = bump(f, 5, 6.5, 7.5, 11)
        d.at(f, R=(lerp(2.9, 7.5, out), lerp(0.4, 1.2, out), 15 * out, None), L=(-2.9, -0.4, 0, None),
             pz=22.7 - 3.6 * out - 0.6 * step, cyaw=0.7 * step * (1 - sm((f - 12) / 4.0)), pyaw=0.45 * step * (1 - sm((f - 12) / 4.0)),
             croll=-0.25 * out, cpitch=0.25 * out + 0.2 * flinch, hyaw=0.3 * flinch, hpitch=0.25 + 0.2 * flinch)
        behind = (-0.7, 0.35, -0.2, -0.6)                       # hands clasped behind the back
        d.arms(f, mix(REST, behind, step * (1 - sm((f - 12) / 4.0))), mix(REST, behind, step * (1 - sm((f - 12) / 4.0))))
    hidden(d); return d.m


@move('gk36_punch', 'Keeper Punch (two fists)')
def punch():
    N = 22; d = Dr(N, ms=50, speed=0.0); d.m.events = {'takeoff': 5, 'strike': 10, 'land': 15}; still(d)
    H = 9.0
    for f in range(N):
        crouch = sm(f / 4.0) * (1 - sm((f - 4.0) / 1.5))
        t = (f - 5.0) / 10.0
        hgt = 4 * H * t * (1 - t) if 0.0 < t < 1.0 else 0.0
        land = bump(f, 14, 16, 17, 21)
        air = hgt > 0.3
        drive = bump(f, 8, 10, 12, 15)
        d.at(f, R=(2.6, 0.6, -10 if air else 0, (1.0 + hgt) if air else None), L=(-2.2, -1.2, -25 if air else 0, (2.5 + hgt * 0.9) if air else None),
             pz=22.7 - 3.8 * crouch - 3.0 * land + hgt, cpitch=0.3 * crouch + 0.35 * land - 0.25 * min(1.0, hgt / H) + 0.25 * drive,
             hpitch=-0.5 * min(1.0, hgt / H) + 0.2 * drive)
        cocked = (2.1, 0.25, 3.2, 0.1)                          # fists up by the face
        thrown = (2.75, 0.12, 2.7, 0.05)                        # driven up and through
        a = mix(REST, cocked, sm((f - 2.0) / 4.0))
        a = mix(a, thrown, drive)
        a = mix(a, REST, sm((f - 15.0) / 5.0))
        d.arms(f, a, a)
    hidden(d); return d.m


COVER = (0.35, 0.12, 1.25, -0.75)                               # upper arm down, forearm across the front


@move('wl01_wall_stand', 'Wall: Stand And Cover', True)
def wall_stand():
    N = 16; d = Dr(N, ms=70, speed=0.0); d.m.loop = True; d.m.events = {}; still(d)
    for f in range(N):
        ph = 2 * PI * f / N
        d.at(f, R=(1.3, 0.2, 0, 0.3 * max(0.0, math.sin(ph)) or None), L=(-1.3, 0.1, 0, 0.3 * max(0.0, -math.sin(ph)) or None),
             pz=22.5 + 0.25 * math.sin(2 * ph), cpitch=0.08, hpitch=0.05, hyaw=0.06 * math.sin(ph))
        w = 0.04 * math.sin(2 * ph)
        d.arms(f, (COVER[0] + w, COVER[1], COVER[2], COVER[3]), (COVER[0] - w, COVER[1], COVER[2], COVER[3]))
    hidden(d); return d.m


@move('wl02_wall_jump', 'Wall: Jump')
def wall_jump():
    N = 18; d = Dr(N, ms=50, speed=0.0); d.m.events = {'takeoff': 3, 'strike': 7, 'land': 11}; still(d)
    H = 7.0
    for f in range(N):
        crouch = sm(f / 2.5) * (1 - sm((f - 2.5) / 1.0))
        t = (f - 3.0) / 8.0
        hgt = 4 * H * t * (1 - t) if 0.0 < t < 1.0 else 0.0
        land = bump(f, 10, 12, 13, 17)
        air = hgt > 0.3
        d.at(f, R=(1.3, 0.2, -20 if air else 0, (0.5 + hgt) if air else None), L=(-1.3, 0.1, -20 if air else 0, (0.5 + hgt) if air else None),
             pz=22.5 - 3.0 * crouch - 2.4 * land + hgt, cpitch=0.2 * crouch + 0.25 * land + 0.15 * min(1.0, hgt / H),
             hyaw=0.55 * bump(f, 4, 6, 9, 12), hpitch=0.3 * bump(f, 4, 6, 9, 12))
        d.arms(f, COVER, COVER)
    hidden(d); return d.m


# ---------------------------------------------------------------- shielding, jockeying, the tactical foul
@move('sh01_shield', 'Shield The Ball', True)
def shield():
    """low and wide, side-on, the left arm out and bent against the man behind, glancing back at him, small adjusting steps"""
    N = 18; d = Dr(N, ms=65, speed=0.0); d.m.loop = True; d.m.events = {}; still(d)
    for f in range(N):
        ph = 2 * PI * f / N
        sw = math.sin(ph)
        d.at(f, R=(4.0 + 0.4 * sw, 1.2, 0, 0.6 if sw > 0.6 else None), L=(-4.2 - 0.3 * sw, -0.8, 0, 0.6 if sw < -0.6 else None),
             pz=19.8 + 0.3 * math.sin(2 * ph), cpitch=0.42, ppitch=0.12, cyaw=0.35 + 0.05 * sw, pyaw=0.15, croll=0.08 * sw,
             hyaw=0.9 + 0.35 * math.sin(ph + 0.6), hpitch=0.35)
        d.arms(f, (0.9, 0.6, 1.4, 0.3), (0.95 + 0.08 * sw, 1.05, 0.7, 0.9))          # left arm out to the side against him
    hidden(d); return d.m


@move('jk01_jockey', 'Jockey Side-On', True)
def jockey():
    """side-on and low, the front foot leading, short shuffles back without crossing the feet, hands low and out, eyes on the ball"""
    N = 16; d = Dr(N, ms=60, speed=0.0); d.m.loop = True; d.m.events = {}; still(d)
    for f in range(N):
        ph = 2 * PI * f / N
        sw = math.sin(ph)
        d.at(f, R=(3.4 + 0.8 * sw, 2.6, 0, 0.7 * max(0.0, sw) if sw > 0.3 else None), L=(-3.4 + 0.8 * sw, -2.2, 0, 0.7 * max(0.0, -sw) if sw < -0.3 else None),
             pz=20.2 + 0.35 * abs(math.cos(ph)), cpitch=0.38, ppitch=0.1, cyaw=-0.45, pyaw=-0.35, hyaw=0.35, hpitch=0.45)
        d.arms(f, (0.55, 0.55, 0.9, 0.35), (0.55, 0.55, 0.9, 0.35))
    hidden(d); return d.m


@move('fl01_shirt_pull', 'Shirt Pull (tactical foul)')
def shirt_pull():
    """lunges a step, the right hand grabs the shirt (strike), and he drags back leaning away from him, left arm pumping for balance"""
    N = 18; d = Dr(N, ms=55, speed=0.0); d.m.events = {'strike': 6}; still(d)
    d.speed(f0=1.5, f5=1.2, f7=0.0)
    for f in range(N):
        reach = bump(f, 1, 5, 7, 9)
        drag = bump(f, 6, 9, 13, 17)
        d.at(f, R=(2.8, 1.5 + 2.0 * reach - 2.5 * drag, 0, None), L=(-2.8, -0.6 + 1.5 * reach - 3.5 * drag, 0, None),
             pz=22.3 - 1.0 * reach - 1.2 * drag, cpitch=0.35 * reach - 0.4 * drag, cyaw=0.25 * reach - 0.2 * drag, hpitch=0.1 + 0.1 * reach)
        r = mix(REST, (1.55, 0.05, 1.6, -0.1), reach)                 # arm straight out at his back
        r = mix(r, (0.85, 0.1, 1.75, -0.1), drag)                       # fist pulled in to the chest
        l = mix(REST, (-0.4, 0.5, 0.2, 0.2), reach + drag * 0.6)
        d.arms(f, r, l)
    hidden(d); return d.m


# ---------------------------------------------------------------- penalties, the offside appeal
@move('pk01_penalty_runup', 'Penalty Run-Up (stutter)')
def penalty_runup():
    """a short angled run, a stutter step (a hop on the left foot, a beat watching the keeper), then into the strike stride"""
    N = 20; d = Dr(N, ms=60, speed=0.0); d.m.events = {'strike': 19}
    for f in range(N): d.lt[f] = 0.0
    d.speed(f0=1.6, f7=1.7, f9=0.3, f13=0.3, f15=1.9, f19=2.0)
    for f in range(N):
        stut = bump(f, 8, 9.5, 12, 13.5)
        ph = f / 6.0 * 2 * PI
        sw = math.sin(ph) * (1 - stut)
        d.at(f, R=(2.6, 2.4 * sw, 0, (2.0 * max(0, -sw) if sw < -0.2 else None) if stut < 0.5 else 1.2), L=(-2.6, -2.4 * sw, 0, 2.0 * max(0, sw) if sw > 0.2 else None),
             pz=22.8 + 0.4 * abs(math.cos(ph)) * (1 - stut) + 0.6 * stut, cpitch=0.15 - 0.08 * stut, hpitch=0.15 - 0.15 * stut, hyaw=0.12 * stut)
        sa = 0.5 * math.sin(ph) * (1 - stut)
        d.arms(f, (0.2 - sa, 0.3 + 0.3 * stut, 0.9, -0.05), (0.2 + sa, 0.3 + 0.3 * stut, 0.9, -0.05))
    hidden(d); return d.m


@move('gk37_penalty_line', 'Keeper On The Line (penalty)', True)
def penalty_line():
    N = 20; d = Dr(N, ms=60, speed=0.0); d.m.loop = True; d.m.events = {}; still(d)
    for f in range(N):
        ph = 2 * PI * f / N
        sw = math.sin(ph)
        d.at(f, R=(3.6 + 0.9 * sw, 0.2, 0, 0.8 if sw > 0.7 else None), L=(-3.6 + 0.9 * sw, 0.0, 0, 0.8 if sw < -0.7 else None),
             pz=21.4 + 0.3 * abs(math.cos(ph)), cpitch=0.3, croll=0.1 * sw, hpitch=0.25)
        w = 0.15 * math.sin(2 * ph)
        d.arms(f, (1.25, 1.2 + w, 1.4, 1.1), (1.25, 1.2 - w, 1.4, 1.1))              # arms out wide, waving
    hidden(d); return d.m


@move('ap01_offside_appeal', 'Offside Appeal (arm up)')
def offside_appeal():
    N = 22; d = Dr(N, ms=60, speed=0.0); d.m.events = {}; still(d)
    d.speed(f0=0.0, f3=0.9, f18=0.9, f21=0.0)
    for f in range(N):
        up = bump(f, 0, 4, 16, 21)
        ph = f / 8.0 * 2 * PI
        sw = math.sin(ph) * sm((f - 2.0) / 2.0) * (1 - sm((f - 18.0) / 3.0))
        d.at(f, R=(2.7, 1.8 * sw, 0, 1.2 * max(0, -sw) if sw < -0.3 else None), L=(-2.7, -1.8 * sw, 0, 1.2 * max(0, sw) if sw > 0.3 else None),
             pz=22.8 + 0.2 * abs(math.cos(ph)), cpitch=0.0, hyaw=0.85 * up, cyaw=0.15 * up, hpitch=-0.05 * up)
        d.arms(f, mix(REST, (3.05, 0.12, 3.1, 0.1), up), mix(REST, (0.3 - 0.2 * sw, 0.3, 0.8, 0.0), up))
    hidden(d); return d.m


def build(ids=None):
    out = []
    for name, (label, fn, loop) in MOVES.items():
        if ids and name not in ids: continue
        m = fn(); m.loop = loop; m.save(name, label, 'AI layer, sprites/moves_ai.py'); out.append(name)
    return out


if __name__ == '__main__':
    for n in build(sys.argv[1:] or None): print(n)
