"""Aerial contest clips: waiting under a ball in the air, shoving the man off and taking it on the chest, and jumping off the opponent's shoulder to win the header.
Same framework as moves_fluid.py (eased continuous curves). The strike frame is where the ball is met (the game times the clip so that frame lands when the ball arrives)."""
import math
from moves_dribble import Dr
from moves_defend import hidden
from moves_fluid import sm, lerp, mix, REST, LYING_R

PI = math.pi
MOVES = {}


def move(id_, label, loop=False):
    def deco(fn):
        MOVES[id_] = (label, fn, loop); return fn
    return deco


@move('ct01_wait_air', 'Wait For The Ball (eyes up)', True)
def wait_air():
    """under a high ball: small adjusting steps, head tipped back following it, arms a little out for balance, weight on the toes"""
    N = 20; d = Dr(N, ms=70, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N):
        ph = 2 * PI * f / N
        sw = math.sin(ph); bob = 0.5 + 0.5 * math.sin(2 * ph)
        d.at(f, R=(2.9 + 0.3 * sw, 0.6 + 0.5 * max(0, sw), 0, 0.8 * max(0, sw) if sw > 0.3 else None), L=(-2.9 + 0.3 * sw, 0.6 + 0.5 * max(0, -sw), 0, 0.8 * max(0, -sw) if sw < -0.3 else None),
             pz=22.2 + 0.5 * bob, cpitch=-0.12 + 0.03 * sw, croll=0.05 * sw, proll=-0.04 * sw, hpitch=-0.55 + 0.05 * math.sin(2 * ph), hyaw=0.12 * math.sin(ph + 1.0))
        o = (0.9 + 0.06 * sw, 0.7, 0.9, 0.0)
        d.arms(f, o, (o[0] - 0.12 * sw, o[1], o[2], o[3]))
    hidden(d); return d.m


@move('ct02_push_chest', 'Shove Off And Chest Down')
def push_chest():
    """gets his body in front, the near arm drives into the opponent's back / shoulder (shoulders twist into it), then the shove is let go and the chest is thrown out
    for the ball (arms wide, head back) at the strike frame; knees take the drop"""
    N = 26; d = Dr(N, ms=60, speed=0.0); d.m.events = {'shove': 6, 'strike': 12}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N):
        load = sm(f / 4.0) * (1 - sm((f - 5.0) / 2.0))                   # shoulder cocked back
        shove = sm((f - 4.0) / 2.5) * (1 - sm((f - 9.0) / 3.0))          # drives through
        chest = sm((f - 8.0) / 3.5) * (1 - sm((f - 15.0) / 5.0))         # chest out for the ball
        settle = sm((f - 14.0) / 6.0)
        pz = 22.7 - 1.6 * load - 0.8 * shove + 0.9 * chest - 1.4 * settle * (1 - sm((f - 20.0) / 5.0))
        R = (2.9 + 1.0 * shove, 0.6 + 0.8 * shove, 0, None)
        L = (-2.9 - 0.6 * shove, 0.2 - 0.6 * shove, 0, None)
        d.at(f, R=R, L=L, pz=pz, cpitch=0.25 * shove - 0.4 * chest + 0.35 * settle * (1 - sm((f - 20.0) / 5.0)), cyaw=-0.35 * load + 0.55 * shove * (1 - chest),
             pyaw=-0.15 * load + 0.3 * shove * (1 - chest), croll=-0.2 * shove, proll=0.1 * shove, hpitch=-0.45 * chest - 0.2 * load, hyaw=0.4 * shove * (1 - chest))
        rest_r = REST
        r = mix(rest_r, (-0.5, 0.6, 0.5, 0.0), load)                      # near arm back
        r = mix(r, (1.6, 0.35, 0.3, 0.1), shove)                          # then straight into him
        r = mix(r, (1.3, 1.1, 1.3, 0.1), chest)                           # and out wide for the chest
        l = mix(REST, (1.1, 0.9, 1.2, 0.0), max(load, shove) * 0.7)
        l = mix(l, (1.3, 1.1, 1.3, 0.1), chest)
        d.arms(f, r, l)
    hidden(d); return d.m


@move('ct03_shoulder_leap', 'Shoulder Leap Header')
def shoulder_leap():
    """crouches, plants a hand on the opponent's shoulder and vaults off it: the body goes up higher than a normal jump with the hand pressing down, the other arm up for balance,
    head thrown back and snapped through the ball at the strike frame, knees soak the landing"""
    N = 28; d = Dr(N, ms=58, speed=0.0); d.m.events = {'takeoff': 6, 'strike': 12, 'land': 19}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    H = 13.0
    for f in range(N):
        crouch = sm(f / 5.0) * (1 - sm((f - 5.0) / 1.5))
        t = (f - 6.0) / 12.0
        hgt = 4 * H * t * (1 - t) if 0.0 < t < 1.0 else 0.0
        land = sm((f - 18.0) / 2.0) * (1 - sm((f - 21.0) / 5.0))
        hand = sm((f - 2.0) / 3.0) * (1 - sm((f - 12.0) / 5.0))           # hand down on his shoulder
        snap = sm((f - 9.0) / 3.0) * (1 - sm((f - 14.0) / 3.0))           # the head goes through the ball
        air = hgt > 0.3
        pz = 22.7 - 4.8 * crouch - 5.0 * land + hgt
        d.at(f, R=(2.8, 0.8 - 1.5 * min(1.0, hgt / H), -15 * min(1.0, hgt / H) if air else 0, (1.0 + hgt * 0.8) if air else None),
             L=(-2.8, -0.6 + 0.6 * min(1.0, hgt / H), -25 * min(1.0, hgt / H) if air else 0, (0.8 + hgt * 0.85) if air else None), pz=pz,
             cpitch=0.1 + 0.5 * crouch + 0.5 * land - 0.45 * (1 - crouch) * min(1.0, hgt / H) + 0.0, croll=0.35 * hand, proll=0.15 * hand, cyaw=0.25 * hand,
             hpitch=-0.6 * min(1.0, hgt / H) * (1 - snap) + 0.5 * snap, ppitch=0.1 * crouch)
        l_down = (0.7, 1.35, 0.5, 0.0)                                    # hand reaching down and out onto his shoulder
        r_up = (2.5, 0.6, 2.2, -0.05)
        l = mix(REST, l_down, hand); r = mix(REST, r_up, sm((f - 4.0) / 4.0) * (1 - sm((f - 15.0) / 5.0)))
        d.arms(f, r, l)
    hidden(d); return d.m
