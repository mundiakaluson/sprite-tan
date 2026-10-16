"""Smoother versions of the clips that looked robotic: the keeper's idle and dive, the jump and the fall.
Everything is sampled from continuous curves (eased phases, anticipation, overshoot, arms that lag the body) instead of a handful of hard poses."""
import math
import gen_actions as A
from moves_dribble import Dr
from moves_defend import hidden

PI = math.pi
READY = (1.15, 0.45, 1.55, 0.25)
REST = (0.12, 0.2, 0.45, -0.08)
MOVES = {}


def move(id_, label, loop=False):
    def deco(fn):
        MOVES[id_] = (label, fn, loop); return fn
    return deco


def sm(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def mix(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


def lag(fn, f, k=1.0):
    return fn(f - k)


def idle_pose(d, f, ph, scale=1.0, low=0.0, wide=0.0):
    """the keeper's ready stance at loop phase ph (0..2pi): knees soft, weight rocking, breathing, hands working, eyes scanning"""
    sw = math.sin(ph)                                        # weight side to side
    bob = 0.5 + 0.5 * math.sin(2 * ph - 1.2)                 # little knee dip twice per cycle
    toe = max(0.0, math.sin(2 * ph + 0.8)) ** 2              # a heel lifts now and then
    d.at(f, R=(3.1 + 0.25 * sw, 0.8, 0, 1.6 * toe if sw > 0 and toe > 0.15 else None), L=(-3.1 + 0.25 * sw, -0.6, 0, 1.6 * toe if sw < 0 and toe > 0.15 else None),
         pz=21.6 + 0.35 * bob - 0.15 * abs(sw), cpitch=0.5 + 0.35 * low + 0.04 * math.sin(2 * ph + 0.4), croll=0.07 * sw * scale, proll=-0.05 * sw * scale, hyaw=0.18 * math.sin(ph + 0.8) * scale, hpitch=0.25 + 0.03 * math.sin(2 * ph))
    wr = math.sin(2 * ph + 1.0)
    d.arms(f, (READY[0] + 0.06 * wr, READY[1] + 0.05 * math.sin(ph), READY[2] + 0.1 * wr, READY[3] + 0.08 * math.sin(2 * ph)), (READY[0] - 0.06 * wr, READY[1] - 0.05 * math.sin(ph), READY[2] - 0.1 * wr, READY[3] - 0.08 * math.sin(2 * ph + 0.5)))


@move('gk_set_low', 'Keeper Set Low (shot coming)', True)
def keeper_set_low():
    """a shot is likely: wider and lower, hands out in front, still rocking on the toes"""
    N = 20; d = Dr(N, ms=65, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N):
        idle_pose(d, f, 2 * PI * f / N, scale=0.6, low=1.6, wide=0.9)
        a = (1.35, 0.5, 1.7, 0.3); w = 0.08 * math.sin(4 * PI * f / N)
        d.arms(f, (a[0] + w, a[1], a[2] + w, a[3]), (a[0] - w, a[1], a[2] - w, a[3]))
    hidden(d); return d.m


@move('gk_shuffle', 'Keeper Side Shuffle', True)
def keeper_shuffle():
    """sidesteps to his right with his chest to the ball: lead foot reaches, trail foot follows without crossing, knees bent, hands ready (the game mirrors it for a left shuffle)"""
    N = 12; d = Dr(N, ms=55, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N):
        ph = 2 * PI * f / N; c = math.cos(ph); sn = math.sin(ph)
        lead = max(0.0, sn); trail = max(0.0, -sn)
        d.at(f, R=(3.3 + 1.7 * (0.5 + 0.5 * c), 0.8, 0, 1.8 * lead if lead > 0.1 else None), L=(-3.3 + 1.7 * (0.5 + 0.5 * -c) + 0.0, -0.6, 0, 1.8 * trail if trail > 0.1 else None),
             pz=21.2 - 0.35 * abs(sn), cpitch=0.5, croll=-0.06 * sn, proll=0.04 * sn, hyaw=-0.12, hpitch=0.25)
        w = 0.1 * sn
        d.arms(f, (READY[0] + w, READY[1], READY[2] + w, READY[3]), (READY[0] - w, READY[1], READY[2] - w, READY[3]))
    hidden(d); return d.m


@move('gk_ready_idle', 'Keeper Ready Idle', True)
def keeper_idle():
    N = 28; d = Dr(N, ms=75, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    for f in range(N): idle_pose(d, f, 2 * PI * f / N)
    hidden(d); return d.m


# ------------------------------------------------------------------------------------------------------------------ dive
DIVE_STRIKE = 5            # frames after f0 where the hands meet the ball (the clip's `strike`)
DIVE_LEN = 13              # frames from f0 until he is lying


def dive(d, f0, h=30.0, reach=(2.35, 0.5, 2.8, 0.2), lt=4.2, lie=6, roll=1.45):
    """sink and swing the arms back, drive off the push foot, stretch to full reach (frame f0+5), then fall away with the legs trailing, land on the hip and slide, lie.
    Returns the first frame after the lie."""
    LY = dict(R=(3.6, -3.0, 20, 5.0), L=(-0.5, -4.0, 20, 5.0))
    for i in range(DIVE_LEN):
        f = f0 + i
        c = sm(i / 2.0)                                              # coil 0..1 over the first frames
        L_ = sm((i - 2) / 3.0)                                       # launch 0..1 by the strike frame
        fall = sm((i - 6) / 6.0)                                     # fall away after the stretch
        imp = sm((i - 10) / 2.0)
        up = h - (h - 8.0) * (fall ** 1.6)                           # gravity: slow at the top, quicker down
        if i < 3: pz = 21.8 - 3.2 * c
        elif i < 6: pz = lerp(18.6, h, sm((i - 2.5) / 3.0) ** 0.8)
        else: pz = up
        if i == 11: pz += 1.1                                       # a small bounce as the hip lands
        cr = -(0.12 * c) - 1.05 * L_ - (roll - 1.05) * fall - 0.0
        cr = -min(abs(cr), roll)
        pr = cr + 0.1 * (1 - fall)
        # legs: push foot drives off, the other trails and swings up; both settle on the ground side
        air = L_ * (1 - imp)
        Rz = (9.0 * air + 3.0) if i >= 2 and i < 11 else None
        Lz = (11.0 * air + 2.0) if i >= 2 and i < 11 else None
        R = (lerp(3.0, 3.6, L_), lerp(0.8, -3.0, L_ * (1 - 0.3 * c)), 20 * L_, Rz) if i < 11 else (3.6, -3.0, 20, lerp(7.0, 5.0, imp))
        L = (lerp(-3.0, -0.6, L_), lerp(-0.6, -3.5, L_), 20 * L_, Lz) if i < 11 else (-0.5, -4.0, 20, lerp(8.0, 5.0, imp))
        if i < 2: R = (3.0, 0.8, 0, None); L = (-3.0, -0.6, 0, None)
        d.at(f, R=R, L=L, pz=pz, cpitch=lerp(0.7, 0.0, L_) * (1 - fall) + 0.0, croll=cr, proll=pr, hyaw=-0.85 * sm((i - 1) / 5.0), hpitch=0.2 * (1 - L_) + 0.1 * fall, hroll=-0.25 * L_ * (1 - fall))
        # arms: swing back on the coil, thrust to the reach (lagging the body a touch, with a little overshoot), cradle in on the way down, then out to the ground
        back = (0.6, 0.35, 1.0, 0.1)
        if i < 3: a = mix(READY, back, c)
        elif i < 6:
            u = sm((i - 2.0) / 3.0); a = mix(back, tuple(r * 1.04 for r in reach), u)
        else: a = mix(tuple(r * 1.04 for r in reach), reach, sm((i - 5) / 3.0))                    # hands stay out at the ball (a parry, not a cradle)
        d.arms(f, a, a)
    lat = {f0: 0.0, f0 + 2: lt * 0.25, f0 + 4: lt * 1.0, f0 + 6: lt * 0.9, f0 + 8: lt * 0.65, f0 + 10: lt * 0.35, f0 + 12: 0.15 * lt, f0 + 13: 0.0}
    d.lateral(**{f'f{k}': v for k, v in lat.items()})
    for f in range(f0 + DIVE_LEN, f0 + DIVE_LEN + lie):
        e = f - (f0 + DIVE_LEN)
        d.at(f, R=LY['R'], L=LY['L'], pz=8.0 + 0.25 * math.sin(e * 1.4) * max(0.0, 1 - e / 4.0), cpitch=0.0, croll=-roll, proll=-roll + 0.05, hyaw=-0.85)
        k = sm(e / 3.0); a = mix(reach, mix(reach, LYING_R, 0.55), k)                                  # the arms ease down onto the grass
        d.arms(f, a, a)
    return f0 + DIVE_LEN + lie


def getup(d, f0, n=8):
    """off the ground: roll onto the hands, push through a crouch, stand with the hands coming back to the ready position (eased, with the head leading)"""
    for i in range(n):
        u = (i + 1) / n; f = f0 + i
        s1 = sm(u / 0.5); s2 = sm((u - 0.4) / 0.6)
        d.at(f, R=(3.0, 0.8, 0, None), L=(-3.0, -0.6, 0, None), pz=lerp(8.0, 21.8, s2 ** 0.85) + 1.5 * math.sin(PI * s2) * 0.0, cpitch=0.9 * math.sin(PI * min(1.0, u * 0.9)) * 0.7 + 0.5 * s2, croll=-1.45 * (1 - s1), proll=-1.4 * (1 - s1),
             hyaw=-0.85 * (1 - s1), hpitch=0.3 * s1)
        d.arms(f, mix(mix(LYING_R, (1.5, 0.5, 1.5, 0.2), 0.6), READY, s2), mix(mix(LYING_R, (1.5, 0.5, 1.5, 0.2), 0.6), READY, s2))
    return f0 + n


# ------------------------------------------------------------------------------------------------------------------ jump
@move('base_jump', 'Jump')
def jump():
    """arms swing back and the knees load, then everything drives up together (arms lead, legs follow), a light tuck at the top, the legs reach for the ground and the knees soak up the landing"""
    N = 22; d = Dr(N, ms=55, speed=0.0); d.m.events = {'takeoff': 5, 'apex': 10, 'land': 15}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    H = 9.0
    for f in range(N):
        load = sm(f / 4.0) * (1 - sm((f - 4.0) / 1.2))                                 # 0..1..0 around the take-off
        t = (f - 5.0) / 10.0
        hgt = 4 * H * t * (1 - t) if 0.0 < t < 1.0 else 0.0
        land = sm((f - 14.5) / 2.0) * (1 - sm((f - 17.5) / 3.5))                       # knees absorb
        pz = 22.7 - 4.4 * load - 4.8 * land + hgt
        air = hgt > 0.2
        tuck = min(1.0, hgt / H) ** 0.8
        arm_up = sm((f - 2.5) / 3.0) * (1 - sm((f - 12.5) / 4.0))
        arm_back = load * (1 - sm((f - 3.0) / 1.5))
        a = mix(REST, (2.45, 0.55, 2.1, -0.08), arm_up)
        a = mix(a, (-0.9, 0.3, 0.2, -0.08), arm_back * 0.9)
        d.at(f, R=(2.8, 0.8 - 1.4 * tuck, 0 if not air else -20 * tuck, (1.0 + hgt * 0.9) if air else None), L=(-2.8, -0.6 + 0.5 * tuck, 0 if not air else -10 * tuck, (0.8 + hgt * 0.85) if air else None), pz=pz,
             cpitch=0.05 + 0.55 * load + 0.5 * land - 0.1 * tuck, ppitch=0.1 * load, hpitch=0.1 + 0.2 * (load + land))
        d.arms(f, a, mix(a, (a[0] * 0.92, a[1], a[2] * 0.95, a[3]), 0.6))
    hidden(d); return d.m


# ------------------------------------------------------------------------------------------------------------------ falls
LYING_R = (0.2, 0.25, 0.5, -0.05)       # arms along his body, slack, not up in the air
LYING_L = (0.15, 0.3, 0.45, -0.05)


def lying_pose(d, f, roll=1.45, pz=8.0):
    d.at(f, R=(3.6, -3.0, 20, 5.0), L=(-0.5, -4.0, 20, 5.0), pz=pz, cpitch=0.0, croll=-roll, proll=-roll + 0.05, hyaw=-0.85)
    d.arms(f, LYING_R, LYING_L)


def fall_clip(kind):
    """kind: 'side' (loses balance and tips over), 'trip' (feet go from under him, thrown forward, arms out, rolls onto the side), 'back' (shoved, spins and goes down on the hip). All end in the lying pose base_get_up starts from."""
    N = 26; d = Dr(N, ms=60, speed=0.0); d.m.events = {'impact': 10}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    P = dict(side=dict(lean=-0.3, spin=0.0, fwd=0.0, imp=10), trip=dict(lean=-0.15, spin=0.0, fwd=1.0, imp=9), back=dict(lean=-0.35, spin=1.0, fwd=-1.0, imp=10))[kind]
    imp = P['imp']
    for f in range(N):
        off = sm(f / 4.0)                                              # off balance
        tip = sm((f - 3.0) / (imp - 3.0))                              # tipping over, accelerating
        drop = tip ** 1.7
        end = sm((f - imp) / 5.0)                                      # settling into the lying pose
        bounce = 0.7 * math.sin(PI * min(1.0, max(0.0, (f - imp) / 3.0))) * (1 - end) if f >= imp else 0.0
        pz = lerp(22.7, 8.0, drop) - 1.0 * off * (1 - drop) + bounce
        roll = -(0.3 * off + 1.15 * drop) + (-0.0)
        roll = max(roll, -1.45 - 0.0) if f < imp else -1.45 - 0.03 * math.sin((f - imp) * 1.1) * (1 - end)
        cp = lerp(0.05, 0.3 + 0.5 * P['fwd'], off) * (1 - drop) + 0.0
        # feet: one catches at the ground, the other trails or kicks up
        trail = sm((f - 3.0) / 3.0) * (1 - sm((f - imp) / 2.0))
        Rz = None if f < 4 or f > imp + 1 else 2.0 + 6.0 * trail
        Lz = None if f < 5 or f > imp + 1 else 1.0 + 4.0 * trail
        if f > imp + 1: R = (3.6, -3.0, 20, 5.0); L = (-0.5, -4.0, 20, 5.0)
        else:
            R = (lerp(2.8, 3.6, drop), lerp(0.8, -3.0, drop), 20 * drop, Rz); L = (lerp(-2.8, -0.5, drop), lerp(-0.6, -4.0, drop), 20 * drop, Lz)
        d.at(f, R=R, L=L, pz=pz, cpitch=cp * (1 - end), croll=roll, proll=roll + 0.08 * (1 - end), hyaw=-0.85 * drop + (0.5 * P['spin'] * sm(f / 6.0) * (1 - drop)), hroll=-0.2 * off * (1 - end), pyaw=0.45 * P['spin'] * off * (1 - drop))
        wind = math.sin(f * 1.6) * off * (1 - drop)                    # arms flail, then reach for the ground
        flail = (0.12 + 1.5 * off, 0.2 + 1.0 * off, 0.45 + 0.9 * off, -0.08 + 0.3 * off)
        ground = (1.5, 0.45, 1.2, 0.1)
        r = mix((flail[0] + 0.5 * wind, flail[1], flail[2], flail[3]), ground, sm((f - 5.0) / 3.0)); l = mix((flail[0] - 0.5 * wind, flail[1], flail[2], flail[3]), (1.2, 0.5, 1.0, 0.1), sm((f - 6.0) / 3.0))
        r = mix(r, LYING_R, sm((f - imp) / 4.0)); l = mix(l, LYING_L, sm((f - imp) / 4.0))               # braced at the ground, then the arms go slack
        d.arms(f, r, l)
    d.lateral(**{'f3': 0.0, f'f{imp - 3}': 1.2, f'f{imp}': 1.0, f'f{imp + 3}': 0.0})
    hidden(d); return d.m


@move('base_fall', 'Fall')
def fall():
    return fall_clip('side')


@move('base_fall_trip', 'Fall (tripped)')
def fall_trip():
    return fall_clip('trip')


@move('base_fall_back', 'Fall (shoved back)')
def fall_back():
    return fall_clip('back')


@move('base_get_up', 'Get Up')
def get_up():
    N = 22; d = Dr(N, ms=60, speed=0.0); d.m.events = {}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    lying_pose(d, 0); lying_pose(d, 1)
    for f in range(2, N):
        u = (f - 1) / (N - 2.0)
        s1 = sm(u / 0.4); s2 = sm((u - 0.3) / 0.45); s3 = sm((u - 0.72) / 0.28)
        pz = lerp(8.0, 12.0, s1) if u < 0.4 else (lerp(12.0, 19.0, s2) if u < 0.75 else lerp(19.0, 22.7, s3))
        cp = 0.9 * s1 * (1 - s2) + 0.5 * s2 * (1 - s3) + 0.05 * s3
        d.at(f, R=(lerp(3.4, 3.0, s1), lerp(-3.0, 1.0, s1) + 0.1 * s2, 20 * (1 - s1), 5.0 * (1 - s1) if s1 < 1 else None), L=(lerp(-0.5, -3.0, s1), lerp(-4.0, -0.6, s1) - 0.8 * (1 - s2), 20 * (1 - s1), 5.0 * (1 - s1) if s1 < 1 else None),
             pz=pz, cpitch=cp, croll=-1.45 * (1 - s1), proll=-1.4 * (1 - s1), hyaw=-0.85 * (1 - s1), hpitch=0.3 * s1 * (1 - s3) + 0.05 * s3)
        d.arms(f, mix(LYING_R, mix((1.5, 0.5, 1.3, 0.2), REST, s3), s2), mix(LYING_L, mix((1.5, 0.6, 1.3, 0.2), REST, s3), s2))
    hidden(d); return d.m


# ------------------------------------------------------------------------------------------------------------------ clearing under pressure
def panic_clear(kind):
    """kind: 'flinch' or 'fall'. A hoof with everything behind it: a short flinch, the kicking leg cocked right back, planted left foot, then the whole leg whips through and up
    (strike frame 8) with the body thrown back and the arms flung wide. 'flinch' recovers into a stagger, 'fall' is carried over by the follow-through and goes down."""
    N = 26; d = Dr(N, ms=55, speed=0.0); d.m.events = {'strike': 8}
    for f in range(N): d.lt[f] = 0.0; d.sp[f] = 0.0
    fall = kind == 'fall'
    for f in range(N):
        shy = sm(f / 3.0) * (1 - sm((f - 4.0) / 3.0))                    # a flinch away from the opponent
        wind = sm((f - 1.0) / 4.0) * (1 - sm((f - 6.0) / 2.0))           # leg cocked right back
        swing = sm((f - 6.0) / 2.5) * (1 - sm((f - 10.0) / 4.0))         # then whipped through, hard and fast
        thru = sm((f - 8.0) / 3.0) * (1 - sm((f - 14.0) / 4.0))          # follow-through, foot high
        drop = sm((f - 11.0) / 8.0) if fall else 0.0
        end = sm((f - 19.0) / 4.0) if fall else 0.0
        rec = sm((f - 14.0) / 5.0) if not fall else 0.0
        lean = -0.3 * thru - 0.1 * shy + 0.2 * wind                      # leans back through the ball, forward as he winds
        pz = lerp(22.7 - 1.6 * shy - 1.2 * wind + 0.6 * swing, 8.0, drop)
        roll = -1.45 * drop
        ry = lerp(0.8 - 11.0 * wind + 17.0 * swing + 6.0 * thru, -3.0, drop)
        rz = 2.0 + 8.0 * wind + 6.0 * swing + 7.0 * thru
        R = (lerp(2.8, 3.6, drop), ry, -50 * wind + 45 * (swing + thru) + 20 * drop, (rz if f < 15 else None))
        L = (lerp(-2.8, -0.5, drop), lerp(-0.6 + 1.5 * wind, -4.0, drop), 20 * drop, None)     # the plant foot stays down
        d.at(f, R=R, L=L, pz=pz, cpitch=lean * (1 - drop), croll=roll, proll=roll + 0.06 * (1 - drop), ppitch=0.15 * wind - 0.2 * thru,
             hyaw=-0.85 * drop, hpitch=0.1 * shy, hroll=-0.1 * shy, pyaw=-0.12 * wind + 0.2 * (swing + thru) * (1 - drop))
        up = mix(REST, (1.9, 0.9, 1.7, 0.0), shy)
        wide = (-0.9, 0.5, 0.3, 0.0)                                      # arms thrown out and back for the swing
        r = mix(up, wide, max(swing, thru)); l = mix(up, (2.4, 0.7, 1.2, 0.0), max(swing, thru) * (1 - rec))
        l = mix(l, (1.2 + 0.4 * math.sin(f * 1.7), 0.5, 1.0, 0.0), rec)
        if fall:
            r = mix(r, LYING_R, sm((f - 15.0) / 4.0)); l = mix(l, LYING_L, sm((f - 15.0) / 4.0))
        d.arms(f, r, l)
    if fall: d.lateral(**{'f3': 0.0, 'f13': 1.0, 'f16': 0.0})
    hidden(d); return d.m


@move('cl01_panic_clear', 'Panic Clear (flinch, hack, stagger)')
def panic_flinch():
    return panic_clear('flinch')


@move('cl02_panic_clear_fall', 'Panic Clear (hack and fall)')
def panic_fall():
    return panic_clear('fall')
