"""
Football player sprite generator v2
- tiny software ray-caster: ellipsoids / sphere-chains, true orthographic camera (30 deg elevation)
- per-pixel z-buffer, toon-shaded with hand-picked 4-tone ramps, inner depth lines, sel-out outline
- run cycle driven by foot trajectories + 2-link IK (planted stance feet, flight phase, heel-up swing)
- 4 run styles with different stride, lean, arm drive, cadence and ball-touch rhythm
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ config
CW, CH = 72, 84
OX, OY = 36, 66
ELEV = math.radians(30)
sE, cE = math.sin(ELEV), math.cos(ELEV)
EX = np.array([1.0, 0.0, 0.0])
UP = np.array([0.0, -sE, cE])
NV = np.array([0.0, cE, sE])           # points toward the camera
LDIR = np.array([-0.55, 0.45, 0.70]); LDIR /= np.linalg.norm(LDIR)
FRAMES = 12
DIRS = ['S', 'SE', 'E', 'NE', 'N', 'NW', 'W', 'SW']
R2 = 0.70710678
VEC = {'S': (0, 1), 'SE': (R2, R2), 'E': (1, 0), 'NE': (R2, -R2),
       'N': (0, -1), 'NW': (-R2, -R2), 'W': (-1, 0), 'SW': (-R2, R2)}
I3 = np.eye(3)
BR = 3.0                                # ball radius (px)

SKIN, HAIR, JERSEY, TRIM, SHORTS, BOOT, ACCENT, BALL, PATCH = range(9)

# ------------------------------------------------------------------ palettes (shadow, dark, base, light)
SKINS = {
    'fair':  [(120, 66, 76), (178, 104, 100), (230, 160, 134), (250, 200, 170)],
    'tan':   [(108, 58, 52), (160, 92, 70), (204, 134, 96), (232, 168, 124)],
    'brown': [(58, 30, 34), (94, 52, 44), (138, 86, 60), (176, 120, 86)],
    'deep':  [(30, 16, 26), (58, 32, 34), (94, 58, 44), (134, 90, 66)],
}
HAIRS = {
    'black': [(10, 8, 16), (22, 18, 30), (40, 34, 50), (82, 72, 96)],
    'brown': [(30, 16, 18), (60, 36, 28), (98, 64, 42), (148, 104, 68)],
    'blond': [(100, 64, 44), (156, 110, 56), (210, 164, 86), (244, 214, 138)],
}
JERSEY_R = [(70, 14, 42), (140, 24, 52), (212, 44, 62), (246, 92, 82)]
TRIM_W = [(92, 98, 150), (166, 174, 208), (228, 232, 246), (255, 255, 255)]
SHORTS_W = [(84, 92, 148), (150, 160, 204), (214, 222, 244), (246, 250, 255)]
BOOTS = {
    'black': ([(8, 8, 16), (22, 22, 38), (46, 48, 76), (120, 126, 170)], [(120, 20, 40), (190, 40, 60), (240, 80, 90), (255, 140, 130)]),
    'white': ([(110, 112, 160), (170, 176, 212), (226, 230, 246), (255, 255, 255)], [(20, 20, 40), (40, 40, 70), (70, 70, 110), (120, 120, 160)]),
    'neon':  ([(24, 60, 40), (64, 150, 60), (160, 230, 60), (236, 255, 150)], [(8, 8, 16), (22, 22, 38), (46, 48, 76), (100, 106, 150)]),
}
BALL_W = [(96, 104, 158), (168, 178, 214), (230, 236, 248), (255, 255, 255)]
PATCH_D = [(14, 16, 32), (30, 34, 58), (48, 52, 84), (96, 104, 150)]
EYE_C = (26, 18, 28)
OUT_FALLBACK = (18, 16, 30)

# ------------------------------------------------------------------ run styles
STYLES = {
    # tall, long levers, long ground-covering stride, strong arm drive; pushes the ball well ahead
    'lengthy': dict(
        label='Lengthy', legs=1.08, trunk=1.04, build=1.00, stance=0.40,
        yc=5.6, yo=-9.6, lift=12.0, dip=2.2, flight=1.2, lean=0.16, arm=0.82, elbow=1.50,
        twist=0.22, head_pitch=0.00, sway=0.45, touch_every=2, push=9.5, tau_m=0.30, lat=1.4,
        cadence=2.9, skin='fair', hair='brown', hairstyle='crop', boots='white'),
    # forward lean, high knees, quick cadence, big knock-ons
    'explosive': dict(
        label='Explosive', legs=1.00, trunk=1.00, build=1.00, stance=0.36,
        yc=4.8, yo=-10.2, lift=14.5, dip=2.6, flight=1.7, lean=0.30, arm=1.00, elbow=1.68,
        twist=0.28, head_pitch=0.08, sway=0.40, touch_every=2, push=11.0, tau_m=0.25, lat=1.6,
        cadence=3.5, skin='brown', hair='black', hairstyle='fade', boots='neon'),
    # upright, relaxed, rhythmic; head up, soft touches every step
    'controlled': dict(
        label='Controlled', legs=1.00, trunk=1.00, build=0.97, stance=0.43,
        yc=4.2, yo=-8.0, lift=10.0, dip=2.0, flight=0.7, lean=0.09, arm=0.66, elbow=1.36,
        twist=0.16, head_pitch=-0.06, sway=0.55, touch_every=1, push=5.5, tau_m=0.36, lat=1.6,
        cadence=2.8, skin='tan', hair='black', hairstyle='tied', boots='black'),
    # low centre of gravity, short quick steps, wide balance arms, ball glued to the feet
    'stocky': dict(
        label='Stocky', legs=0.88, trunk=0.96, build=1.14, stance=0.45,
        yc=3.2, yo=-6.4, lift=8.5, dip=2.9, flight=0.35, lean=0.22, arm=0.74, elbow=1.46,
        twist=0.14, head_pitch=0.20, sway=0.65, touch_every=1, push=4.2, tau_m=0.40, lat=1.5,
        cadence=3.6, skin='deep', hair='black', hairstyle='afro', boots='white'),
}

# ------------------------------------------------------------------ tiny maths helpers
def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def face_matrix(f):
    fx, fy = f
    return np.array([[-fy, fx, 0], [fx, fy, 0], [0, 0, 1.0]])


def curve(keys, x):
    """periodic Catmull-Rom through (x_i, v_i) keys, x in [0,1)"""
    n = len(keys)
    x %= 1.0
    xs = [k[0] for k in keys]
    vs = [k[1] for k in keys]
    xx = x if x >= xs[0] else x + 1.0
    for i in range(n):
        x0 = xs[i]
        x1 = xs[i + 1] if i < n - 1 else xs[0] + 1.0
        if x0 <= xx < x1:
            tt = (xx - x0) / (x1 - x0)
            p0, p1, p2, p3 = vs[(i - 1) % n], vs[i], vs[(i + 1) % n], vs[(i + 2) % n]
            return 0.5 * ((2 * p1) + (-p0 + p2) * tt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * tt * tt
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * tt ** 3)
    return vs[0]


# foot pitch (deg, toes-down positive) over canonical leg phase: 0 = heel strike, 0.4 = toe-off
PITCH_KEYS = [(0.0, -12), (0.10, -1), (0.25, 4), (0.37, 28), (0.42, 40), (0.52, 36),
              (0.68, 16), (0.85, -4)]

FOOT_ABC = (1.65, 3.4, 1.35)


def foot_geom(p):
    """ankle->foot-centre offset (y,z) and lowest extent for a foot pitched p rad"""
    oy = 1.3 * math.cos(p) - 1.1 * math.sin(p)
    oz = -1.3 * math.sin(p) - 1.1 * math.cos(p)
    g = math.sqrt((FOOT_ABC[1] * math.sin(p)) ** 2 + (FOOT_ABC[2] * math.cos(p)) ** 2)
    return oy, oz, g


def leg_targets(tl, P):
    s = P['stance']
    yc, yo = P['yc'], P['yo']
    if tl < s:
        u = tl / s
        y = yc + (yo - yc) * u
        c = 0.0
        tc = 0.4 * u
    else:
        u = (tl - s) / (1 - s)
        m = (yo - yc) * (1 - s) / s * 0.35
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1
        h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2
        h11 = u ** 3 - u ** 2
        y = h00 * yo + h10 * m + h01 * yc + h11 * m
        c = P['lift'] * math.sin(math.pi * u ** 0.8) ** 1.2
        tc = 0.4 + 0.6 * u
    pitch = math.radians(curve(PITCH_KEYS, tc))
    return y, c, pitch


def ik(hy, hz, ay, az, L1, L2):
    dy, dz = ay - hy, az - hz
    d = math.hypot(dy, dz)
    d = min(max(d, abs(L1 - L2) + 0.05), L1 + L2 - 0.05)
    base = math.atan2(dy, -dz)
    cosA = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    A = math.acos(max(-1.0, min(1.0, cosA)))
    h = base + A
    ky, kz = hy + L1 * math.sin(h), hz - L1 * math.cos(h)
    ay2, az2 = hy + d * math.sin(base), hz - d * math.cos(base)
    return (ky, kz), (ay2, az2)


# ------------------------------------------------------------------ scene buffers & primitives
class Scene:
    def __init__(self):
        self.depth = np.full((CH, CW), -1e9, np.float32)
        self.mat = np.full((CH, CW), -1, np.int16)
        self.nrm = np.zeros((CH, CW, 3), np.float32)


def add_ellipsoid(sc, C, M, abc, matfn, pad=1.0):
    C = np.asarray(C, float)
    abc = np.asarray(abc, float)
    r = abc.max() + pad
    cx = OX + C[0]
    cy = OY - float(C @ UP)
    x0, x1 = max(0, int(math.floor(cx - r))), min(CW, int(math.ceil(cx + r)) + 1)
    y0, y1 = max(0, int(math.floor(cy - r))), min(CH, int(math.ceil(cy + r)) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    u = (np.arange(x0, x1) + 0.5 - OX)[None, :]
    w = (OY - (np.arange(y0, y1) + 0.5))[:, None]
    Q0 = u[..., None] * EX + w[..., None] * UP - C
    Ql = (Q0 @ M) / abc
    Nl = (NV @ M) / abc
    A = float(Nl @ Nl)
    B = Ql @ Nl
    Cc = (Ql * Ql).sum(-1) - 1.0
    disc = B * B - A * Cc
    ok = disc >= 0
    s = np.where(ok, (-B + np.sqrt(np.where(ok, disc, 0.0))) / A, -1e9)
    Lu = Ql + s[..., None] * Nl
    nw = (Lu / abc) @ M.T
    nw = nw / (np.linalg.norm(nw, axis=-1, keepdims=True) + 1e-9)
    Pw = Q0 + s[..., None] * NV + C
    m = matfn(Lu, nw, Pw)
    if np.isscalar(m):
        m = np.full(s.shape, m, np.int16)
    sub_d = sc.depth[y0:y1, x0:x1]
    upd = ok & (s > sub_d) & (m >= 0)
    sub_d[upd] = s[upd]
    sc.mat[y0:y1, x0:x1][upd] = m[upd]
    sc.nrm[y0:y1, x0:x1][upd] = nw[upd]


def add_limb(sc, A, B, rfun, mat_t, step=0.42):
    A = np.asarray(A, float)
    B = np.asarray(B, float)
    L = float(np.linalg.norm(B - A))
    n = max(2, int(L / step))
    for i in range(n + 1):
        t = i / n
        C = A + (B - A) * t
        r = rfun(t)
        add_ellipsoid(sc, C, I3, (r, r, r), lambda Lu, nw, Pw, t=t: mat_t(t, Lu, nw, Pw), pad=0.5)


# ------------------------------------------------------------------ jersey number
_d1 = [[0, 1, 0], [1, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 1]]
_d0 = [[1, 1, 1], [1, 0, 1], [1, 0, 1], [1, 0, 1], [1, 1, 1]]
NUM = np.array([_d1[r] + [0] + _d0[r] for r in range(5)])

# ------------------------------------------------------------------ hair styles (cond on head-local unit coords)
def hc_crop(lx, ly, lz):
    return (lz > 0.36) | ((ly < -0.05) & (lz > -0.30)) | ((np.abs(lx) > 0.6) & (lz > 0.05) & (ly < 0.4))


def hc_fade(lx, ly, lz):
    return (lz > 0.52) | ((ly < -0.15) & (lz > 0.02)) | ((np.abs(lx) > 0.7) & (lz > 0.3))


def hc_tied(lx, ly, lz):
    return (lz > 0.34) | ((ly < 0.0) & (lz > -0.45)) | ((np.abs(lx) > 0.55) & (lz > 0.0) & (ly < 0.4))


def hc_afro(lx, ly, lz):
    face = (ly > 0.42) & (lz < 0.46) & (np.abs(lx) < 1.0)
    return (lz > -0.30) & (~face)


def hc_all(lx, ly, lz):
    return np.ones_like(lx, bool)


ICO = []
_p = (1 + 5 ** 0.5) / 2
for a in (-1, 1):
    for b in (-_p, _p):
        ICO += [(0, a, b), (a, b, 0), (b, 0, a)]
ICO = np.array(ICO, float)
ICO /= np.linalg.norm(ICO, axis=1, keepdims=True)


# ------------------------------------------------------------------ the frame renderer
def render_frame(P, dname, k, with_ball=True, ramps=None):
    f = VEC[dname]
    Rf = face_matrix(f)
    t = k / FRAMES
    sc = Scene()
    b = P['build']
    Lt, Ls = 11.6 * P['legs'], 11.0 * P['legs']
    Lmax = Lt + Ls
    tr = P['trunk']
    hipW = 2.5 * b
    stance = P['stance']

    # ---- leg targets
    tg = {}
    for side in (1, -1):
        tl = (t + (0.0 if side > 0 else 0.5)) % 1.0
        tg[side] = leg_targets(tl, P)

    # ---- pelvis height: dip in stance, rise in flight, never over-extend a leg
    z0 = 2.4 + 0.945 * Lmax
    dip = 0.0
    for side in (1, -1):
        tl = (t + (0.0 if side > 0 else 0.5)) % 1.0
        if tl < stance:
            dip = max(dip, math.sin(math.pi * tl / stance))
    tm = t % 0.5
    flight = 0.0
    if tm > stance:
        flight = math.sin(math.pi * (tm - stance) / (0.5 - stance))
    zp = z0 - P['dip'] * dip + P['flight'] * flight

    cph = math.cos(2 * math.pi * (t - 0.88))        # +1 when right leg is most forward
    psi_p = 0.5 * P['twist'] * cph
    psi_c = -P['twist'] * cph
    psi_h = -0.55 * psi_c
    Rp0 = Rz(psi_p)
    for side in (1, -1):
        ay, c, pitch = tg[side]
        oy, oz, g = foot_geom(pitch)
        az = g + c - oz
        hy = (Rp0 @ np.array([side * hipW, 0, 0]))[1]
        dy = ay - hy
        zmax = az + math.sqrt(max(0.0, (Lmax - 0.5) ** 2 - dy * dy))
        zp = min(zp, zmax)

    sway = P['sway'] * math.cos(2 * math.pi * (t - 0.2))
    P0 = np.array([sway, 0.0, zp])

    lean = P['lean']
    Rp = Rp0 @ Rx(-0.35 * lean)
    Rc = Rz(psi_c) @ Rx(-lean)
    bob = 0.03 * math.sin(4 * math.pi * t)
    Rh = Rz(psi_h) @ Rx(-(P['head_pitch'] - 0.3 * lean + bob + 0.0))
    # head pitch is relative to world: undo trunk lean partially so head stays steadier
    Rh = Rz(psi_h) @ Rx(-(P['head_pitch'] + 0.25 * lean + bob))

    def W(v):
        return Rf @ np.asarray(v, float)

    def Mw(R):
        return Rf @ R

    # ---- skeleton (body-local)
    Wst = P0 + Rp @ np.array([0, 0, 6.2 * tr])
    chest_c = Wst + Rc @ np.array([0, 0.2, 4.2 * tr])
    neck_b = Wst + Rc @ np.array([0, 0.1, 8.7 * tr])
    neck_t = neck_b + Rh @ np.array([0, 0.25, 2.0])
    head_c = neck_t + Rh @ np.array([0, 0.45, 3.0])
    sh_off = 4.7 * b

    # ---- pelvis & torso
    add_ellipsoid(sc, W(P0 + Rp @ np.array([0, 0, 0.3])), Mw(Rp), (4.35 * b, 3.1, 3.3),
                  lambda Lu, nw, Pw: SHORTS)
    add_ellipsoid(sc, W(P0 + Rp @ np.array([0, 0, 4.4 * tr])), Mw(Rp), (4.05 * b, 2.95, 3.7 * tr),
                  lambda Lu, nw, Pw: JERSEY)

    def chest_mat(Lu, nw, Pw):
        lx, ly, lz = Lu[..., 0], Lu[..., 1], Lu[..., 2]
        m = np.full(lx.shape, JERSEY, np.int16)
        col = np.floor((lx + 0.62) / 1.24 * 7).astype(int)
        row = np.floor((0.60 - lz) / 0.80 * 5).astype(int)
        inn = (ly < -0.2) & (col >= 0) & (col < 7) & (row >= 0) & (row < 5)
        bits = NUM[np.clip(row, 0, 4), np.clip(col, 0, 6)]
        m[inn & (bits == 1)] = TRIM
        m[lz > 0.86] = TRIM
        vneck = (ly > 0.25) & (lz > 0.62) & (np.abs(lx) < (lz - 0.62) * 1.5)
        m[vneck] = SKIN
        return m
    add_ellipsoid(sc, W(chest_c), Mw(Rc), (4.95 * b, 3.45, 5.4 * tr), chest_mat)

    # ---- neck
    add_limb(sc, W(neck_b), W(neck_t), lambda t_: 1.75 * b, lambda t_, Lu, nw, Pw: SKIN)

    # ---- head
    abc_h = np.array([2.95, 3.3, 3.55])
    Mh = Mw(Rh)
    Ch = W(head_c)
    add_ellipsoid(sc, Ch, Mh, abc_h, lambda Lu, nw, Pw: SKIN)
    add_ellipsoid(sc, W(head_c + Rh @ np.array([0, 0.6, -1.7])), Mh, (2.2, 2.45, 2.05), lambda Lu, nw, Pw: SKIN)
    add_ellipsoid(sc, W(head_c + Rh @ np.array([0, 3.15, -0.45])), I3, (0.72, 0.72, 0.72), lambda Lu, nw, Pw: SKIN)
    for sd in (1, -1):
        add_ellipsoid(sc, W(head_c + Rh @ np.array([sd * 2.85, -0.2, -0.45])), I3, (0.85, 0.85, 0.85),
                      lambda Lu, nw, Pw: SKIN)

    def head_local(Pw):
        return ((Pw - Ch) @ Mh) / abc_h

    def hair_fn(cond):
        def fn(Lu, nw, Pw):
            h = head_local(Pw)
            return np.where(cond(h[..., 0], h[..., 1], h[..., 2]), HAIR, -1).astype(np.int16)
        return fn

    hs = P['hairstyle']
    if hs == 'crop':
        add_ellipsoid(sc, Ch + Mh @ np.array([0, -0.15, 0.1]), Mh, abc_h * 1.08, hair_fn(hc_crop))
    elif hs == 'fade':
        add_ellipsoid(sc, Ch + Mh @ np.array([0, -0.1, 0.0]), Mh, abc_h * 1.03, hair_fn(hc_fade))
        add_ellipsoid(sc, Ch + Mh @ np.array([0, 0.25, 2.55]), Mh, (2.55, 3.05, 1.75), lambda Lu, nw, Pw: HAIR)
    elif hs == 'tied':
        add_ellipsoid(sc, Ch + Mh @ np.array([0, -0.25, 0.05]), Mh, abc_h * 1.08, hair_fn(hc_tied))
        base = head_c + Rh @ np.array([0, -2.9, 1.0])
        pts = [base]
        theta = 0.75
        for i in range(6):
            amp = 0.30 * (i + 1) / 3.0
            th = theta + amp * math.sin(4 * math.pi * t - 0.9 - 0.55 * i)
            lat = 0.35 * i * math.sin(2 * math.pi * t - 0.5 - 0.4 * i)
            seg = np.array([lat * 0.25, -math.sin(th), -math.cos(th)]) * 1.55
            pts.append(pts[-1] + Rh @ seg)
        for i in range(6):
            add_limb(sc, W(pts[i]), W(pts[i + 1]), lambda t_, i=i: 1.25 - 0.1 * i - 0.1 * t_,
                     lambda t_, Lu, nw, Pw: HAIR, step=0.5)
    elif hs == 'afro':
        bounce = 0.35 * math.sin(4 * math.pi * t - 0.6)
        add_ellipsoid(sc, Ch + Mh @ np.array([0, -0.55, 1.05 + bounce]), Mh, (4.25, 4.2, 3.9), hair_fn(hc_afro))

    # ---- legs
    foot_info = {}
    for side in (1, -1):
        ay, c, pitch = tg[side]
        oy, oz, g = foot_geom(pitch)
        az = g + c - oz
        Hjt = P0 + Rp @ np.array([side * hipW, 0, -0.3])
        (ky, kz), (ay2, az2) = ik(Hjt[1], Hjt[2], ay, az, Lt, Ls)
        ax = P0[0] + side * 1.9
        kx = 0.5 * (Hjt[0] + ax) + side * 0.55
        Hp = np.array([Hjt[0], Hjt[1], Hjt[2]])
        Kp = np.array([kx, ky, kz])
        Ap = np.array([ax, ay2, az2])
        ts = 0.46

        def thigh_r(t_, b=b):
            return (3.45 * b - 0.35 * t_) if t_ < ts else (2.55 * b - 0.8 * (t_ - ts) / (1 - ts))

        def thigh_m(t_, Lu, nw, Pw, side=side):
            if t_ < 0.40:
                ln = nw @ Rf
                return np.where(side * ln[..., 0] > 0.55, JERSEY, SHORTS).astype(np.int16)
            if t_ < ts:
                return JERSEY
            return SKIN
        add_limb(sc, W(Hp), W(Kp), thigh_r, thigh_m)

        def shank_r(t_, b=b):
            return 2.15 * b + 0.45 * math.sin(math.pi * t_) - 0.85 * t_

        def shank_m(t_, Lu, nw, Pw):
            if t_ < 0.05:
                return SKIN
            if 0.10 <= t_ < 0.19:
                return TRIM
            return JERSEY
        add_limb(sc, W(Kp), W(Ap), shank_r, shank_m)

        # boot
        fdir = np.array([0, math.cos(pitch), -math.sin(pitch)])
        perp = np.array([0, math.sin(pitch), math.cos(pitch)])
        Mfoot = Rz(side * 0.10) @ np.stack([np.array([1.0, 0, 0]), fdir, perp], axis=1)
        fc = Ap + np.array([0, oy, oz])

        def boot_m(Lu, nw, Pw, side=side):
            m = np.full(Lu.shape[:2], BOOT, np.int16)
            m[(side * Lu[..., 0] > 0.45) & (np.abs(Lu[..., 2]) < 0.55) & (Lu[..., 1] > -0.4)] = ACCENT
            return m
        add_ellipsoid(sc, W(fc), Mw(Mfoot), FOOT_ABC, boot_m)
        foot_info[side] = (Ap, fc)

    # ---- arms
    for side in (1, -1):
        a = math.cos(2 * math.pi * (t - 0.4 + (0.0 if side > 0 else 0.5)))
        s_ang = 0.12 + P['arm'] * 0.9 * a
        e_ang = P['elbow'] + 0.30 * a
        J = Wst + Rc @ np.array([side * sh_off, 0.0, 6.0 * tr])
        Lu_, Lf_ = 7.8 * P['legs'] ** 0.5, 7.2 * P['legs'] ** 0.5
        U = np.array([side * 0.20, math.sin(s_ang), -math.cos(s_ang)])
        U /= np.linalg.norm(U)
        Ep = J + Lu_ * (Rc @ U) * 1.0
        beta = s_ang + e_ang
        Fv = np.array([-side * (0.10 + 0.25 * max(0.0, a)), math.sin(beta), -math.cos(beta)])
        Fv /= np.linalg.norm(Fv)
        Wr = Ep + Lf_ * (Rc @ Fv)
        Hd = Wr + 1.0 * (Rc @ Fv)
        add_ellipsoid(sc, W(J), I3, (2.35 * b, 2.35 * b, 2.35 * b), lambda Lu, nw, Pw: JERSEY)

        def up_r(t_, b=b):
            return (1.95 * b - 0.45 * t_) * (1.08 if t_ < 0.62 else 1.0)

        def up_m(t_, Lu, nw, Pw):
            if t_ < 0.50:
                return JERSEY
            if t_ < 0.64:
                return TRIM
            return SKIN
        add_limb(sc, W(J), W(Ep), up_r, up_m)
        add_limb(sc, W(Ep), W(Wr), lambda t_, b=b: 1.5 * b - 0.35 * t_, lambda t_, Lu, nw, Pw: SKIN)
        add_ellipsoid(sc, W(Hd), I3, (1.4, 1.4, 1.4), lambda Lu, nw, Pw: SKIN)

    # ---- ball (dribble touches)
    ball_world = None
    if with_ball:
        te = P['touch_every']
        period = 0.5 * te
        tau = (t % period) / period
        p_ = math.log(0.5) / math.log(P['tau_m'])
        dc = P['yc'] + 5.2
        d = dc + P['push'] * math.sin(math.pi * tau ** p_)
        side_t = 1.0 if (te == 2 or (t % 1.0) < 0.5) else -1.0
        lat = side_t * P['lat'] * (1 - tau) ** 1.3
        hop = 0.07 * P['push'] * max(0.0, math.sin(math.pi * min(1.0, tau / 0.55)))
        Cb = np.array([lat, d, BR + hop])
        roll = 2 * math.pi * 2 * t
        Mb = Mw(Rx(-roll))

        def ball_m(Lu, nw, Pw):
            lb = nw @ Mb
            dots = lb @ ICO.T
            return np.where(dots.max(-1) > 0.915, PATCH, BALL).astype(np.int16)
        add_ellipsoid(sc, W(Cb), I3, (BR, BR, BR), ball_m)
        ball_world = W(Cb)

    # ---- eyes (explicit pixels, only where the face is visible)
    eyes = []
    for sd in (-1, 1):
        L = np.array([sd * 0.36, math.sqrt(1 - 0.36 ** 2 - 0.10 ** 2), 0.10])
        pw = Ch + Mh @ (L * abc_h)
        eyes.append(pw)

    # ---- shading
    rgb, alpha = finish(sc, ramps, eyes)

    # ---- ground shadows
    sh = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    sd_ = ImageDraw.Draw(sh)
    pg = W(np.array([P0[0], P0[1], 0.0]))
    scx, scy = OX + pg[0] + 2.0, OY + pg[1] * sE - 0.8
    k_air = max(0.0, (zp - z0) * 0.04)
    rx, ry = 8.6 - k_air * 3, 3.6 - k_air
    sd_.ellipse([scx - rx, scy - ry, scx + rx, scy + ry], fill=(10, 10, 30, 78))
    sd_.ellipse([scx - rx * 0.6, scy - ry * 0.55, scx + rx * 0.6, scy + ry * 0.55], fill=(10, 10, 30, 40))
    if ball_world is not None:
        bx, by = OX + ball_world[0] + 1.0, OY + ball_world[1] * sE - 0.4
        sd_.ellipse([bx - 3.4, by - 1.6, bx + 3.4, by + 1.6], fill=(10, 10, 30, 90))
    out = np.dstack([rgb, alpha])
    spr = Image.fromarray(out.astype(np.uint8), 'RGBA')
    return Image.alpha_composite(sh, spr)


def finish(sc, ramps, eyes):
    mat = sc.mat
    opaque = mat >= 0
    lam = sc.nrm @ LDIR
    lvl = np.digitize(lam, [-0.18, 0.28, 0.74])
    m0 = np.clip(mat, 0, None)
    rgb = ramps[m0, lvl].astype(np.float32)

    # inner depth lines
    d = sc.depth
    pd = np.pad(d, 1, constant_values=-1e9)
    pm = np.pad(mat, 1, constant_values=-1)
    edge = np.zeros_like(opaque)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nd = pd[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW]
        nm = pm[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW]
        diff = nd - d
        edge |= opaque & (nm >= 0) & (((diff > 2.4) & (nm != mat)) | (diff > 5.5))
    rgb[edge] = ramps[m0, 0][edge] * 0.78

    # eyes
    for pw in eyes:
        px = int(math.floor(OX + pw[0]))
        py = int(math.floor(OY - float(pw @ UP)))
        if 0 <= px < CW and 0 <= py < CH and mat[py, px] == SKIN and abs(d[py, px] - float(pw @ NV)) < 1.6:
            rgb[py, px] = EYE_C

    alpha = np.where(opaque, 255, 0).astype(np.uint8)

    # sel-out outline
    pad_op = np.pad(opaque, 1, constant_values=False)
    pad_m = np.pad(mat, 1, constant_values=-1)
    pad_rgb = np.pad(ramps[m0, 0].astype(np.float32), ((1, 1), (1, 1), (0, 0)))
    out_mask = np.zeros_like(opaque)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = pad_op[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW]
        cand = nb & ~opaque & ~out_mask
        nbc = pad_rgb[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW] * 0.42
        rgb[cand] = nbc[cand]
        out_mask |= cand
    alpha[out_mask] = 255
    return np.clip(rgb, 0, 255), alpha


def build_ramps(P):
    bt, ac = BOOTS[P['boots']]
    rr = [SKINS[P['skin']], HAIRS[P['hair']], JERSEY_R, TRIM_W, SHORTS_W, bt, ac, BALL_W, PATCH_D]
    return np.array(rr, np.float32)


# ------------------------------------------------------------------ sheets / previews
def render_style(name, with_ball=True):
    P = STYLES[name]
    ramps = build_ramps(P)
    frames = {}
    for dn in DIRS:
        for k in range(FRAMES):
            frames[(dn, k)] = render_frame(P, dn, k, with_ball, ramps)
    return frames


def make_sheet(frames, path):
    sheet = Image.new('RGBA', (CW * FRAMES, CH * len(DIRS)), (0, 0, 0, 0))
    for r, dn in enumerate(DIRS):
        for k in range(FRAMES):
            sheet.paste(frames[(dn, k)], (k * CW, r * CH))
    sheet.save(path)


def pitch_bg(w, h, stripe=14):
    bg = Image.new('RGBA', (w, h), (78, 150, 74, 255))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, stripe):
        if (y // stripe) % 2:
            d.rectangle([0, y, w, y + stripe - 1], fill=(88, 164, 82, 255))
    return bg


def make_gif(frames, label, cadence, path, S=3):
    cols, rows = 4, 2
    cw_, ch_ = CW, CH
    W_, H_ = cw_ * cols, ch_ * rows
    font = ImageFont.load_default()
    out = []
    for k in range(FRAMES):
        bg = pitch_bg(W_, H_)
        for i, dn in enumerate(DIRS):
            bg.alpha_composite(frames[(dn, k)], ((i % cols) * cw_, (i // cols) * ch_))
        big = bg.resize((W_ * S, H_ * S), Image.NEAREST).convert('RGB')
        td = ImageDraw.Draw(big)
        for i, dn in enumerate(DIRS):
            td.text(((i % cols) * cw_ * S + 6, (i // cols) * ch_ * S + 4), dn, fill=(255, 255, 255), font=font)
        td.text((6, H_ * S - 14), f'{label}  ({cadence} steps/s)', fill=(255, 255, 255), font=font)
        out.append(big)
    dur = int(round(1000 * (2.0 / cadence) / FRAMES))
    out[0].save(path, save_all=True, append_images=out[1:], duration=dur, loop=0)


def make_strip(all_frames, path, dname='E', S=2):
    names = list(all_frames.keys())
    W_, H_ = CW * FRAMES, CH * len(names)
    bg = pitch_bg(W_, H_, 28)
    for r, n in enumerate(names):
        for k in range(FRAMES):
            bg.alpha_composite(all_frames[n][(dname, k)], (k * CW, r * CH))
    big = bg.resize((W_ * S, H_ * S), Image.NEAREST).convert('RGB')
    td = ImageDraw.Draw(big)
    font = ImageFont.load_default()
    for r, n in enumerate(names):
        td.text((6, r * CH * S + 4), STYLES[n]['label'], fill=(255, 255, 255), font=font)
    big.save(path)


def main(outdir='out_v2', only=None):
    os.makedirs(outdir, exist_ok=True)
    allb, allnb = {}, {}
    names = only or list(STYLES)
    for n in names:
        print('rendering', n, flush=True)
        allb[n] = render_style(n, True)
        allnb[n] = render_style(n, False)
        make_sheet(allb[n], f'{outdir}/{n}_run_dribble_sheet.png')
        make_sheet(allnb[n], f'{outdir}/{n}_run_body_only_sheet.png')
        make_gif(allb[n], STYLES[n]['label'], STYLES[n]['cadence'], f'{outdir}/{n}_preview.gif')
    make_strip(allb, f'{outdir}/gait_strip_E.png', 'E')
    make_strip(allb, f'{outdir}/gait_strip_S.png', 'S')


if __name__ == '__main__':
    main(only=sys.argv[1:] or None)
