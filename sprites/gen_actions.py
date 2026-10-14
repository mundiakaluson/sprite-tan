"""
Action animations on the Lengthy base character:
  kick (driven instep), finesse (inside-foot curler), guard (jockey), slide tackle.
Built on gen_player_v2's ray-caster. Poses are keyframed in body-local world coordinates
(x right, y forward, z up); the whole thing is rotated to each of the 8 facings at render time.
"""
import math, os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import gen_player_v2 as G
from gen_player_v2 import (CW, CH, OX, OY, sE, cE, UP, NV, EX, VEC, DIRS, I3, BR, SKIN, HAIR, JERSEY, TRIM,
                           SHORTS, BOOT, ACCENT, BALL, PATCH, STYLES, Scene, add_ellipsoid, add_limb,
                           finish, build_ramps, face_matrix, Rz, Rx, NUM, ICO, FOOT_ABC, foot_geom,
                           leg_targets, hc_crop, curve)

BASE = STYLES['lengthy']
FPS_MS = 70


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def foot_mat(fp, fy, fr):
    return Rz(fy) @ Rx(-fp) @ Ry(fr)


def gz(fp_deg, fy=0.0, fr=0.0, c=0.0):
    """ankle height so the foot rests on the ground (plus clearance c)"""
    M = foot_mat(math.radians(fp_deg), fy, fr)
    ext = np.linalg.norm((M.T @ np.array([0, 0, 1.0])) * np.array(FOOT_ABC))
    oz = (M @ np.array([0, 1.3, -1.1]))[2]
    return ext + c - oz


# ------------------------------------------------------------------ pose parameters
DEFAULT = dict(root_x=0.0, root_y=0.0, pz=22.0, pyaw=0.0, ppitch=0.0, proll=0.0,
               cyaw=0.0, cpitch=0.0, croll=0.0, hyaw=0.0, hpitch=0.0, hroll=0.0,
               bx=0.0, by=10.0, bz=3.0, brx=0.0, brz=0.0, bvis=0.0)
for _s, _sd in (('R', 1), ('L', -1)):
    DEFAULT.update({f'{_s}_ax': _sd * 2.0, f'{_s}_ay': 0.0, f'{_s}_az': 2.4, f'{_s}_fp': 0.0,
                    f'{_s}_fy': 0.0, f'{_s}_fr': 0.0, f'{_s}_kx': _sd * 0.3, f'{_s}_ky': 1.0, f'{_s}_kz': 0.1,
                    f'{_s}_s1': 0.0, f'{_s}_a1': 0.2, f'{_s}_s2': 1.2, f'{_s}_a2': 0.0})


def foot(s, x, y, z, fp, fy=0.0, fr=0.0):
    return {f'{s}_ax': x, f'{s}_ay': y, f'{s}_az': z, f'{s}_fp': math.radians(fp), f'{s}_fy': fy, f'{s}_fr': fr}


def footg(s, x, y, fp, fy=0.0, fr=0.0, c=0.0):
    return foot(s, x, y, gz(fp, fy, fr, c), fp, fy, fr)


def arm(s, s1, a1, s2, a2):
    return {f'{s}_s1': s1, f'{s}_a1': a1, f'{s}_s2': s2, f'{s}_a2': a2}


def pole(s, x, y, z):
    return {f'{s}_kx': x, f'{s}_ky': y, f'{s}_kz': z}


# ------------------------------------------------------------------ keyframe interpolation (PCHIP)
def pchip(xs, ys, x):
    n = len(xs)
    if n == 1 or x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    h = [xs[j + 1] - xs[j] for j in range(n - 1)]
    d = [(ys[j + 1] - ys[j]) / h[j] for j in range(n - 1)]
    m = [0.0] * n
    if n == 2:
        m = [d[0], d[0]]
    else:
        for j in range(1, n - 1):
            if d[j - 1] * d[j] <= 0:
                m[j] = 0.0
            else:
                w1, w2 = 2 * h[j] + h[j - 1], h[j] + 2 * h[j - 1]
                m[j] = (w1 + w2) / (w1 / d[j - 1] + w2 / d[j])

        def end(h0, h1, d0, d1):
            v = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
            if v * d0 <= 0:
                return 0.0
            if d0 * d1 <= 0 and abs(v) > 3 * abs(d0):
                return 3 * d0
            return v
        m[0] = end(h[0], h[1], d[0], d[1])
        m[-1] = end(h[-1], h[-2], d[-1], d[-2])
    i = max(j for j in range(n - 1) if xs[j] <= x)
    t = (x - xs[i]) / h[i]
    h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
    return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]


def build_anim(keys, N, loop=False):
    series = {}
    for f in sorted(keys):
        for k, v in keys[f].items():
            series.setdefault(k, []).append((f, v))
    frames = []
    for f in range(N):
        pose = dict(DEFAULT)
        for k, pts in series.items():
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            if loop and len(pts) > 1:
                xs = [x - N for x in xs] + xs + [x + N for x in xs]
                ys = ys * 3
            pose[k] = pchip(xs, ys, f)
        frames.append(pose)
    return frames


# ------------------------------------------------------------------ run pose (same kinematics as v2)
def run_pose(P, t, root_y=0.0, root_x=0.0):
    b = P['build']
    Lt, Ls = 11.6 * P['legs'], 11.0 * P['legs']
    Lmax = Lt + Ls
    hipW = 2.5 * b
    stance = P['stance']
    tg = {}
    for side in (1, -1):
        tl = (t + (0.0 if side > 0 else 0.5)) % 1.0
        tg[side] = leg_targets(tl, P)
    z0 = 2.4 + 0.945 * Lmax
    dip = 0.0
    for side in (1, -1):
        tl = (t + (0.0 if side > 0 else 0.5)) % 1.0
        if tl < stance:
            dip = max(dip, math.sin(math.pi * tl / stance))
    tm = t % 0.5
    flight = math.sin(math.pi * (tm - stance) / (0.5 - stance)) if tm > stance else 0.0
    zp = z0 - P['dip'] * dip + P['flight'] * flight
    cph = math.cos(2 * math.pi * (t - 0.88))
    psi_p, psi_c = 0.5 * P['twist'] * cph, -P['twist'] * cph
    psi_h = -0.55 * psi_c
    Rp0 = Rz(psi_p)
    for side in (1, -1):
        ay, c, pitch = tg[side]
        oy, oz, g = foot_geom(pitch)
        az = g + c - oz
        hy = (Rp0 @ np.array([side * hipW, 0, 0]))[1]
        zmax = az + math.sqrt(max(0.0, (Lmax - 0.5) ** 2 - (ay - hy) ** 2))
        zp = min(zp, zmax)
    sway = P['sway'] * math.cos(2 * math.pi * (t - 0.2))
    lean = P['lean']
    bob = 0.03 * math.sin(4 * math.pi * t)
    pose = dict(root_x=root_x + sway, root_y=root_y, pz=zp, pyaw=psi_p, ppitch=0.35 * lean, proll=0.0,
                cyaw=psi_c, cpitch=lean, croll=0.0, hyaw=psi_h, hpitch=P['head_pitch'] + 0.25 * lean + bob, hroll=0.0)
    for s, side in (('R', 1), ('L', -1)):
        ay, c, pitch = tg[side]
        oy, oz, g = foot_geom(pitch)
        pose.update(foot(s, root_x + sway + side * 1.9, root_y + ay, g + c - oz, math.degrees(pitch), -side * 0.08, 0.0))
        pose.update(pole(s, side * 0.3, 1.0, 0.1))
        a = math.cos(2 * math.pi * (t - 0.4 + (0.0 if side > 0 else 0.5)))
        s_ang = 0.12 + P['arm'] * 0.9 * a
        e_ang = P['elbow'] + 0.30 * a
        cc = 0.10 + 0.25 * max(0.0, a)
        pose.update(arm(s, s_ang, 0.195, s_ang + e_ang, -math.asin(cc / math.sqrt(1 + cc * cc))))
    return pose


# ------------------------------------------------------------------ 3D two-bone IK
def ik3(H, A, L1, L2, pole_v):
    v = A - H
    d0 = float(np.linalg.norm(v))
    d = min(max(d0, abs(L1 - L2) + 0.05), L1 + L2 - 0.05)
    dirv = v / (d0 + 1e-9)
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    pp = pole_v - dirv * float(pole_v @ dirv)
    n = float(np.linalg.norm(pp))
    pp = pp / n if n > 1e-4 else np.array([0, 1.0, 0])
    K = H + dirv * a + pp * h
    return K, H + dirv * d


# ------------------------------------------------------------------ renderer
def render_pose(P, dname, pose, ramps, dust=None):
    f = VEC[dname]
    Rf = face_matrix(f)
    sc = Scene()
    g = lambda k: pose[k]
    b = P['build']
    Lt, Ls = 11.6 * P['legs'], 11.0 * P['legs']
    tr = P['trunk']
    hipW = 2.5 * b
    P0 = np.array([g('root_x'), g('root_y'), g('pz')])
    Rp = Rz(g('pyaw')) @ Rx(-g('ppitch')) @ Ry(g('proll'))
    Rc = Rz(g('cyaw')) @ Rx(-g('cpitch')) @ Ry(g('croll'))
    Rh = Rz(g('hyaw')) @ Rx(-g('hpitch')) @ Ry(g('hroll'))

    def W(v):
        return Rf @ np.asarray(v, float)

    def Mw(R):
        return Rf @ R

    Wst = P0 + Rp @ np.array([0, 0, 6.2 * tr])
    chest_c = Wst + Rc @ np.array([0, 0.2, 4.2 * tr])
    neck_b = Wst + Rc @ np.array([0, 0.1, 8.7 * tr])
    neck_t = neck_b + Rh @ np.array([0, 0.25, 2.0])
    head_c = neck_t + Rh @ np.array([0, 0.45, 3.0])
    sh_off = 4.7 * b

    add_ellipsoid(sc, W(P0 + Rp @ np.array([0, 0, 0.3])), Mw(Rp), (4.35 * b, 3.1, 3.3), lambda Lu, nw, Pw: SHORTS)
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
        m[(ly > 0.25) & (lz > 0.62) & (np.abs(lx) < (lz - 0.62) * 1.5)] = SKIN
        return m
    add_ellipsoid(sc, W(chest_c), Mw(Rc), (4.95 * b, 3.45, 5.4 * tr), chest_mat)
    add_limb(sc, W(neck_b), W(neck_t), lambda t_: 1.75 * b, lambda t_, Lu, nw, Pw: SKIN)

    abc_h = np.array([2.95, 3.3, 3.55])
    Mh = Mw(Rh)
    Ch = W(head_c)
    add_ellipsoid(sc, Ch, Mh, abc_h, lambda Lu, nw, Pw: SKIN)
    add_ellipsoid(sc, W(head_c + Rh @ np.array([0, 0.6, -1.7])), Mh, (2.2, 2.45, 2.05), lambda Lu, nw, Pw: SKIN)
    add_ellipsoid(sc, W(head_c + Rh @ np.array([0, 3.15, -0.45])), I3, (0.72, 0.72, 0.72), lambda Lu, nw, Pw: SKIN)
    for sd in (1, -1):
        add_ellipsoid(sc, W(head_c + Rh @ np.array([sd * 2.85, -0.2, -0.45])), I3, (0.85, 0.85, 0.85),
                      lambda Lu, nw, Pw: SKIN)

    def hair_fn(Lu, nw, Pw):
        h = ((Pw - Ch) @ Mh) / abc_h
        return np.where(hc_crop(h[..., 0], h[..., 1], h[..., 2]), HAIR, -1).astype(np.int16)
    add_ellipsoid(sc, Ch + Mh @ np.array([0, -0.15, 0.1]), Mh, abc_h * 1.08, hair_fn)

    # legs
    for s, side in (('R', 1), ('L', -1)):
        Hj = P0 + Rp @ np.array([side * hipW, 0, -0.3])
        A = np.array([g(s + '_ax'), g(s + '_ay'), g(s + '_az')])
        pv = np.array([g(s + '_kx'), g(s + '_ky'), g(s + '_kz')])
        K, A2 = ik3(Hj, A, Lt, Ls, pv)
        ts = 0.46

        def thigh_r(t_, b=b):
            return (3.45 * b - 0.35 * t_) if t_ < ts else (2.55 * b - 0.8 * (t_ - ts) / (1 - ts))

        def thigh_m(t_, Lu, nw, Pw, side=side):
            if t_ < 0.40:
                ln = nw @ Rf
                return np.where(side * ln[..., 0] > 0.55, JERSEY, SHORTS).astype(np.int16)
            return JERSEY if t_ < ts else SKIN
        add_limb(sc, W(Hj), W(K), thigh_r, thigh_m)

        def shank_r(t_, b=b):
            return 2.15 * b + 0.45 * math.sin(math.pi * t_) - 0.85 * t_

        def shank_m(t_, Lu, nw, Pw):
            if t_ < 0.05:
                return SKIN
            return TRIM if 0.10 <= t_ < 0.19 else JERSEY
        add_limb(sc, W(K), W(A2), shank_r, shank_m)
        Mf = foot_mat(g(s + '_fp'), g(s + '_fy'), g(s + '_fr'))
        fc = A2 + Mf @ np.array([0, 1.3, -1.1])

        def boot_m(Lu, nw, Pw, side=side):
            m = np.full(Lu.shape[:2], BOOT, np.int16)
            m[(side * Lu[..., 0] > 0.45) & (np.abs(Lu[..., 2]) < 0.55) & (Lu[..., 1] > -0.4)] = ACCENT
            return m
        add_ellipsoid(sc, W(fc), Mw(Mf), FOOT_ABC, boot_m)

    # arms
    for s, side in (('R', 1), ('L', -1)):
        J = Wst + Rc @ np.array([side * sh_off, 0.0, 6.0 * tr])
        Lu_, Lf_ = 7.8 * P['legs'] ** 0.5, 7.2 * P['legs'] ** 0.5

        def dv(sa, aa, side=side):
            v = np.array([side * math.sin(aa), math.sin(sa) * math.cos(aa), -math.cos(sa) * math.cos(aa)])
            return v / np.linalg.norm(v)
        Ep = J + Lu_ * (Rc @ dv(g(s + '_s1'), g(s + '_a1')))
        fv = Rc @ dv(g(s + '_s2'), g(s + '_a2'))
        Wr = Ep + Lf_ * fv
        Hd = Wr + 1.0 * fv
        add_ellipsoid(sc, W(J), I3, (2.35 * b, 2.35 * b, 2.35 * b), lambda Lu, nw, Pw: JERSEY)

        def up_r(t_, b=b):
            return (1.95 * b - 0.45 * t_) * (1.08 if t_ < 0.62 else 1.0)

        def up_m(t_, Lu, nw, Pw):
            return JERSEY if t_ < 0.50 else (TRIM if t_ < 0.64 else SKIN)
        add_limb(sc, W(J), W(Ep), up_r, up_m)
        add_limb(sc, W(Ep), W(Wr), lambda t_, b=b: 1.5 * b - 0.35 * t_, lambda t_, Lu, nw, Pw: SKIN)
        add_ellipsoid(sc, W(Hd), I3, (1.4, 1.4, 1.4), lambda Lu, nw, Pw: SKIN)

    # ball
    ball_w = None
    if g('bvis') > 0.5:
        Cb = np.array([g('bx'), g('by'), g('bz')])
        Mb = Mw(Rz(g('brz')) @ Rx(-g('brx')))

        def ball_m(Lu, nw, Pw):
            dots = (nw @ Mb) @ ICO.T
            return np.where(dots.max(-1) > 0.915, PATCH, BALL).astype(np.int16)
        add_ellipsoid(sc, W(Cb), I3, (BR, BR, BR), ball_m)
        ball_w = (W(Cb), Cb[2])

    # eyes
    eyes = []
    for sd in (-1, 1):
        L = np.array([sd * 0.36, math.sqrt(1 - 0.36 ** 2 - 0.10 ** 2), 0.10])
        eyes.append(Ch + Mh @ (L * abc_h))
    rgb, alpha = finish(sc, ramps, eyes)

    # shadow: ellipse around the body footprint
    pts = [P0[:2]] + [np.array([g(s + '_ax'), g(s + '_ay')]) for s in ('R', 'L')] + [head_c[:2] * 0.6 + P0[:2] * 0.4]
    wp = np.array([(Rf @ np.array([p[0], p[1], 0]))[:2] for p in pts])
    x0, x1 = wp[:, 0].min(), wp[:, 0].max()
    y0, y1 = wp[:, 1].min(), wp[:, 1].max()
    scx, scy = OX + (x0 + x1) / 2 + 2.0, OY + (y0 + y1) / 2 * sE - 0.8
    rx = max(8.2, (x1 - x0) / 2 + 5.5)
    ry = max(3.4, (y1 - y0) / 2 * sE + 2.8)
    air = max(0.0, (P0[2] - 24.0) * 0.05)
    sh = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    sd_ = ImageDraw.Draw(sh)
    sd_.ellipse([scx - rx + air * 2, scy - ry + air, scx + rx - air * 2, scy + ry - air], fill=(10, 10, 30, 78))
    sd_.ellipse([scx - rx * 0.6, scy - ry * 0.55, scx + rx * 0.6, scy + ry * 0.55], fill=(10, 10, 30, 40))
    if ball_w is not None:
        bw, bz = ball_w
        bx_, by_ = OX + bw[0] + 1.0 + bz * 0.25, OY + bw[1] * sE - 0.4
        k = max(0.4, 1 - (bz - 3) * 0.04)
        sd_.ellipse([bx_ - 3.4 * k, by_ - 1.6 * k, bx_ + 3.4 * k, by_ + 1.6 * k], fill=(10, 10, 30, 90))
    spr = Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), 'RGBA')

    under, over = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)), Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    if dust:
        for (x, y, z, size, col, a) in dust:
            p = W([x, y, z])
            px, py = int(math.floor(OX + p[0])), int(math.floor(OY - float(p @ UP)))
            tgt = under if z < 2.0 else over
            for dx in range(size):
                for dy in range(max(1, size - 1)):
                    if 0 <= px + dx < CW and 0 <= py + dy < CH:
                        tgt.putpixel((px + dx, py + dy), col + (a,))
    out = Image.alpha_composite(sh, under)
    out = Image.alpha_composite(out, spr)
    return Image.alpha_composite(out, over)


# ------------------------------------------------------------------ animations
def ball_keys(f_contact, path, spin_x=2.2, spin_z=0.0, last=None):
    """path: list of (x,y,z) for frames f_contact, f_contact+1, ..."""
    keys = {}
    for i, (x, y, z) in enumerate(path):
        keys[f_contact + i] = dict(bx=x, by=y, bz=z, brx=spin_x * i, brz=spin_z * i, bvis=1.0)
    return keys


def merge(keys, f, d):
    keys.setdefault(f, {}).update(d)


def anim_kick():
    N = 22
    keys = {}
    rooty_run = [-19.8, -17.5, -15.2, -12.9, -10.6, -8.3, -6.0, -3.0]
    for f in range(8):
        keys[f] = run_pose(BASE, (f - 6) / 12.0, rooty_run[f])
        keys[f].update(dict(bx=1.2, by=11.5, bz=3.0, bvis=1.0))

    def K(f, **kw):
        merge(keys, f, kw)

    # f8 toe-off, L leg swinging through
    K(8, root_y=0.5, pz=25.0, ppitch=0.08, pyaw=-0.05, cpitch=0.10, cyaw=0.05, hpitch=0.25)
    merge(keys, 8, foot('R', 2.0, -0.5, gz(32, c=0.6), 32)); merge(keys, 8, foot('L', -2.4, 1.0, 11.0, 5))
    merge(keys, 8, arm('R', -0.2, 0.45, 0.9, 0.2)); merge(keys, 8, arm('L', 0.5, 0.8, 1.2, 0.4))
    # f9 backswing starting, L foot coming in
    K(9, root_y=1.5, pz=24.8, ppitch=0.10, pyaw=-0.2, cpitch=0.14, cyaw=0.10, hpitch=0.38)
    merge(keys, 9, foot('R', 2.2, -6.5, 9.5, 40)); merge(keys, 9, foot('L', -4.2, 2.8, 6.2, -10))
    merge(keys, 9, arm('R', -0.45, 0.55, 0.2, 0.3)); merge(keys, 9, arm('L', 0.7, 1.0, 1.3, 0.7))
    # f10 plant + backswing apex
    K(10, root_y=2.0, pz=24.2, ppitch=0.10, pyaw=-0.32, cpitch=0.16, cyaw=0.16, hpitch=0.5)
    merge(keys, 10, foot('R', 2.6, -9.5, 13.5, 45)); merge(keys, 10, footg('L', -5.0, 4.6, -6))
    merge(keys, 10, arm('R', -0.6, 0.6, -0.1, 0.35)); merge(keys, 10, arm('L', 0.8, 1.15, 1.4, 0.9))
    merge(keys, 10, pole('L', -0.25, 1.0, 0.2))
    # f11 thigh whips forward, shank lagging
    K(11, root_y=2.0, pz=24.2, ppitch=0.10, pyaw=0.0, cpitch=0.14, cyaw=0.0, hpitch=0.5)
    merge(keys, 11, foot('R', 2.2, 5.0, 9.0, 58)); merge(keys, 11, footg('L', -5.0, 4.6, -6))
    merge(keys, 11, arm('R', -0.55, 0.62, 0.0, 0.4)); merge(keys, 11, arm('L', 0.85, 1.2, 1.45, 0.95))
    # f12 CONTACT
    K(12, root_y=2.5, pz=24.0, ppitch=0.06, pyaw=0.22, cpitch=0.08, cyaw=-0.14, hpitch=0.52)
    merge(keys, 12, foot('R', 1.8, 7.8, 4.9, 62)); merge(keys, 12, footg('L', -5.0, 4.6, -6))
    merge(keys, 12, arm('R', -0.5, 0.62, 0.1, 0.4)); merge(keys, 12, arm('L', 0.9, 1.25, 1.5, 1.0))
    # follow-through
    K(13, root_y=3.8, pz=24.4, ppitch=0.06, pyaw=0.38, cpitch=0.12, cyaw=-0.24, hpitch=0.3)
    merge(keys, 13, foot('R', 0.9, 14.5, 9.5, 56)); merge(keys, 13, footg('L', -5.0, 4.6, -4))
    merge(keys, 13, arm('R', 0.1, 0.7, 0.9, 0.4)); merge(keys, 13, arm('L', 0.5, 1.2, 1.2, 0.9))
    K(14, root_y=5.8, pz=24.7, ppitch=0.1, pyaw=0.48, cpitch=0.14, cyaw=-0.3, hpitch=0.15)
    merge(keys, 14, foot('R', 0.4, 18.5, 14.0, 48)); merge(keys, 14, foot('L', -4.6, 4.2, 3.8, 20))
    merge(keys, 14, arm('R', 0.4, 0.8, 1.3, 0.5)); merge(keys, 14, arm('L', 0.1, 1.2, 0.9, 0.8))
    K(15, root_y=8.5, pz=24.8, ppitch=0.14, pyaw=0.35, cpitch=0.16, cyaw=-0.24, hpitch=0.1)
    merge(keys, 15, foot('R', 0.0, 21.0, 15.5, 38)); merge(keys, 15, foot('L', -3.5, 2.5, 8.0, 30))
    merge(keys, 15, arm('R', 0.5, 0.6, 1.4, 0.3)); merge(keys, 15, arm('L', -0.2, 1.0, 0.8, 0.6))
    K(16, root_y=11.5, pz=24.5, ppitch=0.16, pyaw=0.2, cpitch=0.18, cyaw=-0.12, hpitch=0.05)
    merge(keys, 16, foot('R', 0.8, 22.0, 12.0, 20)); merge(keys, 16, foot('L', -2.5, 4.0, 9.0, 25))
    merge(keys, 16, arm('R', 0.5, 0.45, 1.4, 0.2)); merge(keys, 16, arm('L', -0.4, 0.8, 0.9, 0.4))
    # R foot lands, back to a run
    K(17, root_y=14.8, pz=22.6, ppitch=0.12, pyaw=0.1, cpitch=0.2, cyaw=-0.05, hpitch=0.1)
    merge(keys, 17, footg('R', 1.8, 21.0, -10)); merge(keys, 17, foot('L', -2.0, 6.5, 8.5, 28))
    for f in range(18, 22):
        keys[f] = run_pose(BASE, (f - 17) / 12.0, 14.8 + 3.17 * (f - 17))
    # ball: rests, struck at f12, driven away on a rising line
    keys[12].update(dict(bx=1.2, by=11.5, bz=3.0, bvis=1.0, brx=0.0))
    for i, (x, y, z) in enumerate([(1.5, 18.5, 4.2), (1.8, 26.0, 6.8), (2.0, 34.0, 10.0), (2.1, 42.5, 13.5), (2.1, 51.5, 17.0)]):
        merge(keys, 13 + i, dict(bx=x, by=y, bz=z, brx=2.2 * (i + 1), bvis=1.0))
    # --- power-drive character: chest over the ball, huge straight backswing, hop through
    for f, cp in ((9, 0.25), (10, 0.34), (11, 0.38), (12, 0.40), (13, 0.34), (14, 0.22)):
        merge(keys, f, dict(cpitch=cp, ppitch=cp * 0.5, hpitch=0.55))
    merge(keys, 10, foot('R', 1.6, -14.5, 17.5, 52)); merge(keys, 10, arm('R', -0.9, 0.5, -0.3, 0.3))
    merge(keys, 10, arm('L', 1.0, 1.5, 1.5, 1.2))
    merge(keys, 11, foot('R', 1.8, 0.5, 11.0, 66)); merge(keys, 11, arm('L', 1.0, 1.6, 1.5, 1.3))
    merge(keys, 12, foot('R', 1.2, 8.2, 4.6, 74)); merge(keys, 12, footg('L', -3.6, 5.2, -6))
    merge(keys, 13, foot('R', 0.4, 16.0, 11.0, 66)); merge(keys, 13, footg('L', -3.6, 5.2, -4))
    K(14, root_y=6.5, pz=27.5, ppitch=0.2, pyaw=0.25, cyaw=-0.15)
    merge(keys, 14, foot('R', 0.2, 20.0, 19.0, 55)); merge(keys, 14, foot('L', -3.6, 5.5, 8.0, 20))
    merge(keys, 15, foot('R', 0.0, 20.5, 17.5, 40)); merge(keys, 15, foot('L', -3.0, 3.5, 10.0, 25))
    return build_anim(keys, N), None


def anim_finesse():
    """Right-foot inside-of-foot curler: angled approach, wide bent plant leg, big lean away
    from the kicking side, arms flung wide, short open-hip backswing, foot sweeps ACROSS the
    body, ball starts left of target and bends back right."""
    N = 24
    keys = {}
    rooty_run = [-19.8, -17.5, -15.2, -12.9, -10.6, -8.3, -6.0, -3.5]
    for f in range(8):
        keys[f] = run_pose(BASE, (f - 6) / 12.0, rooty_run[f])
        keys[f].update(dict(bx=1.5, by=11.5, bz=3.0, bvis=1.0, pyaw=-0.05 * f, cyaw=0.03 * f, proll=0.02 * f))

    def K(f, **kw):
        merge(keys, f, kw)
    # f8: last long stride, body opening up, lowering
    K(8, root_y=-2.0, root_x=-1.0, pz=24.0, ppitch=0.06, pyaw=-0.40, proll=0.14, cpitch=0.08, cyaw=0.2, croll=0.10, hpitch=0.3)
    merge(keys, 8, foot('R', 2.5, -4.0, gz(30, c=0.6), 30)); merge(keys, 8, foot('L', -4.0, 1.5, 10.0, 5))
    merge(keys, 8, arm('R', -0.2, 0.8, 0.9, 0.3)); merge(keys, 8, arm('L', 0.3, 1.0, 1.0, 0.6))
    # f9: plant foot reaching WIDE
    K(9, root_y=-1.5, root_x=-2.5, pz=23.0, ppitch=0.06, pyaw=-0.50, proll=0.22, cpitch=0.06, cyaw=0.3, croll=0.20, hpitch=0.45)
    merge(keys, 9, foot('R', 4.5, -4.5, 8.0, 32, -0.6)); merge(keys, 9, footg('L', -7.6, 2.4, -6))
    merge(keys, 9, arm('R', -0.2, 1.2, 0.5, 0.8)); merge(keys, 9, arm('L', 0.3, 1.5, 0.8, 1.2))
    merge(keys, 9, pole('L', -1.0, 1.0, 0.3))
    # f10: deep bent plant, big lean away, short backswing out to the right, toe turned out
    K(10, root_y=-0.5, root_x=-3.5, pz=21.6, ppitch=0.04, pyaw=-0.55, proll=0.30, cpitch=0.04, cyaw=0.35, croll=0.28, hpitch=0.55)
    merge(keys, 10, foot('R', 6.2, -2.0, 8.5, 26, -1.1, 0.1)); merge(keys, 10, footg('L', -7.8, 2.8, -6))
    merge(keys, 10, arm('R', -0.2, 1.5, 0.3, 1.1)); merge(keys, 10, arm('L', 0.3, 1.7, 0.7, 1.4))
    merge(keys, 10, pole('R', 1.2, 0.8, 0.1)); merge(keys, 10, pole('L', -1.0, 1.0, 0.3))
    # f11: foot comes in low, arms still wide
    K(11, root_y=-0.2, root_x=-3.7, pz=21.4, ppitch=0.04, pyaw=-0.35, proll=0.32, cpitch=0.04, cyaw=0.25, croll=0.30, hpitch=0.58)
    merge(keys, 11, foot('R', 4.8, 3.0, 5.0, 14, -1.25, 0.15)); merge(keys, 11, footg('L', -7.8, 2.8, -6))
    merge(keys, 11, arm('R', -0.1, 1.5, 0.4, 1.1)); merge(keys, 11, arm('L', 0.3, 1.75, 0.7, 1.4))
    merge(keys, 11, pole('R', 1.2, 0.8, 0.1)); merge(keys, 11, pole('L', -1.0, 1.0, 0.3))
    # f12: CONTACT inside of the foot, ball low and in front-right of the foot
    K(12, root_y=0.2, root_x=-3.8, pz=21.2, ppitch=0.04, pyaw=-0.05, proll=0.32, cpitch=0.04, cyaw=0.0, croll=0.30, hpitch=0.58)
    merge(keys, 12, foot('R', 2.6, 6.6, 3.9, 10, -1.3, 0.1)); merge(keys, 12, footg('L', -7.8, 2.8, -6))
    merge(keys, 12, arm('R', 0.0, 1.45, 0.5, 1.0)); merge(keys, 12, arm('L', 0.3, 1.75, 0.7, 1.4))
    merge(keys, 12, pole('R', 1.2, 0.8, 0.1)); merge(keys, 12, pole('L', -1.0, 1.0, 0.3))
    # f13: long sweep across the body, hips spinning through
    K(13, root_y=1.2, root_x=-3.6, pz=21.8, ppitch=0.06, pyaw=0.35, proll=0.28, cpitch=0.06, cyaw=-0.25, croll=0.25, hpitch=0.4)
    merge(keys, 13, foot('R', -1.2, 11.5, 7.0, 20, -0.9)); merge(keys, 13, footg('L', -7.6, 2.8, -4))
    merge(keys, 13, arm('R', 0.3, 1.1, 0.8, 0.8)); merge(keys, 13, arm('L', 0.2, 1.6, 0.8, 1.2))
    merge(keys, 13, pole('R', 0.0, 1.0, 0.1))
    K(14, root_y=2.8, root_x=-3.0, pz=22.6, ppitch=0.08, pyaw=0.65, proll=0.22, cpitch=0.08, cyaw=-0.42, croll=0.18, hpitch=0.25)
    merge(keys, 14, foot('R', -5.4, 13.5, 11.0, 30, -0.2)); merge(keys, 14, foot('L', -7.2, 2.8, 2.5, 10))
    merge(keys, 14, arm('R', 0.5, 0.9, 1.1, 0.5)); merge(keys, 14, arm('L', 0.0, 1.5, 0.6, 1.0))
    merge(keys, 14, pole('R', -0.8, 1.0, 0.2))
    K(15, root_y=4.8, root_x=-2.0, pz=23.4, ppitch=0.10, pyaw=0.70, proll=0.12, cpitch=0.10, cyaw=-0.45, croll=0.10, hpitch=0.15)
    merge(keys, 15, foot('R', -6.0, 13.0, 12.5, 30, 0.3)); merge(keys, 15, foot('L', -6.0, 3.0, 5.0, 20))
    merge(keys, 15, arm('R', 0.5, 0.8, 1.2, 0.4)); merge(keys, 15, arm('L', -0.1, 1.3, 0.7, 0.8))
    merge(keys, 15, pole('R', -1.0, 1.0, 0.2))
    K(16, root_y=7.5, root_x=-1.0, pz=23.8, ppitch=0.12, pyaw=0.50, proll=0.05, cpitch=0.12, cyaw=-0.35, croll=0.04, hpitch=0.08)
    merge(keys, 16, foot('R', -3.0, 13.5, 11.0, 28)); merge(keys, 16, foot('L', -4.5, 3.0, 8.0, 25))
    merge(keys, 16, arm('R', 0.5, 0.6, 1.3, 0.2)); merge(keys, 16, arm('L', -0.3, 1.0, 0.8, 0.5))
    K(17, root_y=10.5, root_x=0.0, pz=23.4, ppitch=0.14, pyaw=0.30, cpitch=0.16, cyaw=-0.18, hpitch=0.08)
    merge(keys, 17, footg('R', 0.5, 15.5, -10)); merge(keys, 17, foot('L', -3.0, 4.0, 9.0, 25))
    merge(keys, 17, arm('R', 0.5, 0.4, 1.3, 0.1)); merge(keys, 17, arm('L', -0.4, 0.8, 0.9, 0.4))
    K(18, root_y=13.5, root_x=0.0, pz=22.6, ppitch=0.12, pyaw=0.12, cpitch=0.2, cyaw=-0.06, hpitch=0.1)
    merge(keys, 18, footg('R', 1.8, 19.0, -10)); merge(keys, 18, foot('L', -2.0, 6.5, 8.5, 28))
    for f in range(19, 24):
        keys[f] = run_pose(BASE, (f - 18) / 12.0, 13.5 + 3.17 * (f - 18))
    # ---- v3: visible knee-fold WIND-UP (thigh back, shank folded up, toe down), opposite arm back/out
    merge(keys, 8, foot('R', 2.8, -6.0, 9.0, 55)); merge(keys, 8, pole('R', 0.8, 1.0, -0.3))
    merge(keys, 8, arm('R', 0.5, 0.9, 1.2, 0.5)); merge(keys, 8, arm('L', -0.4, 1.0, 0.8, 0.5))
    merge(keys, 9, foot('R', 3.2, -9.5, 11.5, 62)); merge(keys, 9, pole('R', 0.8, 1.0, -0.3))
    merge(keys, 9, arm('R', 0.6, 1.2, 1.2, 0.7)); merge(keys, 9, arm('L', -0.6, 1.4, 0.7, 0.8))
    merge(keys, 9, dict(cpitch=0.14, ppitch=0.10))
    merge(keys, 10, foot('R', 3.6, -12.5, 14.5, 68)); merge(keys, 10, pole('R', 0.9, 1.0, -0.3))
    merge(keys, 10, arm('R', 0.6, 1.4, 1.2, 0.8)); merge(keys, 10, arm('L', -0.7, 1.6, 0.6, 1.0))
    merge(keys, 11, foot('R', 4.2, -3.0, 9.5, 62, -0.9, 0.1)); merge(keys, 11, pole('R', 1.0, 1.0, -0.2))
    merge(keys, 11, arm('R', 0.5, 1.6, 1.1, 1.0)); merge(keys, 11, arm('L', -0.5, 1.7, 0.6, 1.2))
    merge(keys, 12, foot('R', 2.4, 6.4, 4.0, 52, -1.3, 0.1)); merge(keys, 12, arm('R', 0.3, 1.7, 1.0, 1.1))
    merge(keys, 12, arm('L', -0.3, 1.5, 0.7, 1.1))
    for f_ in (9, 10, 11, 12):
        keys[f_]['proll'] = keys[f_].get('proll', 0) * 0.75; keys[f_]['croll'] = keys[f_].get('croll', 0) * 0.75
    # ---- v4: follow-through = leg stays long/straight and swings ACROSS the plant leg (no knee fold)
    merge(keys, 13, foot('R', -4.0, 20.5, 8.5, 28, -0.7)); merge(keys, 13, pole('R', -0.2, 1.0, 0.0))
    merge(keys, 14, foot('R', -8.0, 21.5, 11.0, 30, -0.3)); merge(keys, 14, pole('R', -0.4, 1.0, 0.0))
    merge(keys, 15, foot('R', -10.0, 22.0, 12.5, 30, 0.2)); merge(keys, 15, pole('R', -0.5, 1.0, 0.0))
    merge(keys, 16, foot('R', -7.0, 20.5, 10.5, 28));      merge(keys, 16, pole('R', -0.4, 1.0, 0.0))
    merge(keys, 17, foot('R', -3.5, 15.5, 4.0, 25));       merge(keys, 17, pole('R', 0.0, 1.0, 0.1))
    # ---- v5: plant leg only moderately flexed (refs: near-upright, firm plant), narrower stance, calmer lean
    for f_, pz_, rx_, pr_, lx_, ly_ in ((9, 24.2, -1.6, 0.14, -5.6, 2.4), (10, 23.8, -2.2, 0.17, -6.0, 2.7),
                                         (11, 23.5, -2.3, 0.18, -6.0, 2.7), (12, 23.3, -2.4, 0.18, -6.0, 2.7),
                                         (13, 23.6, -2.3, 0.16, -5.8, 2.7)):
        merge(keys, f_, dict(pz=pz_, root_x=rx_, proll=pr_, croll=pr_ * 0.8))
        merge(keys, f_, footg('L', lx_, ly_, -6 if f_ < 13 else -4)); merge(keys, f_, pole('L', -0.3, 1.0, 0.1))
    merge(keys, 14, dict(pz=23.8, root_x=-2.0, proll=0.12)); merge(keys, 14, pole('L', -0.3, 1.0, 0.1))
    merge(keys, 8, dict(pz=24.6, root_x=-0.8))
    # ---- v6: real SPINE BEND: pelvis stays level-ish, chest side-bends away from the kicking leg and
    #      extends back (C-curve), head counter-tilts to keep eyes on the ball, chest counter-rotates
    for f_, cp, cr, pr, hr, cy in ((8, 0.10, 0.08, 0.06, -0.05, 0.15), (9, 0.04, 0.18, 0.08, -0.10, 0.28),
                                   (10, -0.04, 0.28, 0.08, -0.18, 0.36), (11, -0.12, 0.36, 0.08, -0.24, 0.30),
                                   (12, -0.18, 0.42, 0.06, -0.28, 0.10), (13, -0.20, 0.40, 0.06, -0.26, -0.20),
                                   (14, -0.12, 0.30, 0.06, -0.20, -0.38), (15, -0.02, 0.18, 0.05, -0.10, -0.40),
                                   (16, 0.06, 0.08, 0.03, -0.04, -0.30)):
        merge(keys, f_, dict(cpitch=cp, croll=cr, proll=pr, hroll=hr, cyaw=cy))
    keys[12].update(dict(bx=1.5, by=11.5, bz=3.0, bvis=1.0, brx=0.0, brz=0.0))
    # starts LEFT of the target line, bends back to the right (right-foot finesse curl)
    path = [(0.2, 18.5, 4.4), (-1.8, 25.0, 7.0), (-3.8, 31.5, 9.6), (-5.2, 37.5, 11.8), (-5.8, 43.5, 13.6),
            (-5.4, 49.0, 14.8), (-4.4, 54.0, 15.4), (-2.9, 58.5, 15.6), (-1.2, 62.5, 15.4)]
    for i, (x, y, z) in enumerate(path):
        merge(keys, 13 + i, dict(bx=x, by=y, bz=z, brx=0.8 * (i + 1), brz=-1.6 * (i + 1), bvis=1.0))
    return build_anim(keys, N), None


def anim_guard():
    N = 12
    keys = {}
    for f in range(N):
        t = f / N
        k = {}
        k.update(dict(root_x=0.55 * math.sin(2 * math.pi * t), root_y=0.0,
                      pz=19.8 + 0.5 * math.cos(4 * math.pi * t), ppitch=0.14, pyaw=0.08 * math.sin(2 * math.pi * t),
                      cpitch=0.24, cyaw=-0.12 * math.sin(2 * math.pi * t), croll=0.03 * math.sin(2 * math.pi * t),
                      hpitch=0.02 + 0.02 * math.cos(4 * math.pi * t), hyaw=0.06 * math.sin(2 * math.pi * t)))
        # backward shuffle: stance foot slides forward relative to the body, swing foot skims back
        for s, side, stag, off in (('R', 1, 2.0, 0.0), ('L', -1, -1.0, 0.5)):
            tl = (t + off) % 1.0
            lo, hi = -3.5 + stag, 3.0 + stag
            if tl < 0.5:
                y = lo + (hi - lo) * (tl / 0.5)
                c = 0.0
            else:
                u = (tl - 0.5) / 0.5
                y = hi + (lo - hi) * (u * u * (3 - 2 * u))
                c = 2.2 * math.sin(math.pi * u)
            fp = 4.0 + 10.0 * c / 2.2
            k.update(foot(s, side * 5.0 + k['root_x'], y, gz(fp, -side * 0.12, 0.0, c), fp, -side * 0.12))
            k.update(pole(s, side * 0.7, 1.0, 0.1))
            a = math.sin(2 * math.pi * (t + off))
            k.update(arm(s, 0.35 + 0.12 * a, 1.05, 1.15 + 0.1 * a, 0.55))
        keys[f] = k
    return build_anim(keys, N, loop=True), None


def anim_slide():
    N = 22
    keys = {}
    ry_run = [-20.0, -17.0, -14.0, -11.0]
    for f in range(4):
        keys[f] = run_pose(BASE, 0.5 + (f - 3) / 12.0, ry_run[f])
        keys[f].update(dict(bx=1.5, by=30.0, bz=3.0, bvis=1.0))

    def K(f, **kw):
        merge(keys, f, kw)
    # drop and slide
    K(4, root_y=-8.5, pz=19.8, ppitch=0.1, pyaw=0.1, proll=-0.05, cpitch=0.1, croll=-0.05, hpitch=0.1)
    merge(keys, 4, footg('L', -2.4, -5.4, -5)); merge(keys, 4, foot('R', 2.3, -2.0, 10.0, 15))
    merge(keys, 4, arm('R', 0.2, 0.9, 0.9, 0.9)); merge(keys, 4, arm('L', -0.3, 0.8, 0.5, 0.7))
    K(5, root_y=-6.0, pz=15.5, ppitch=0.0, pyaw=0.1, proll=-0.28, cpitch=-0.2, croll=-0.28, hpitch=0.0)
    merge(keys, 5, foot('L', -3.4, -4.5, 3.4, 15)); merge(keys, 5, foot('R', 2.5, 5.0, 8.5, 5))
    merge(keys, 5, arm('R', 0.1, 1.3, 0.2, 1.4)); merge(keys, 5, arm('L', -0.6, 0.8, -0.2, 0.6))
    K(6, root_y=-3.0, pz=10.5, ppitch=-0.2, pyaw=0.05, proll=-0.65, cpitch=-0.5, croll=-0.55, hpitch=0.0, hroll=-0.2)
    merge(keys, 6, foot('L', -3.6, -3.0, 3.0, 20)); merge(keys, 6, foot('R', 2.6, 11.5, 6.5, 0))
    merge(keys, 6, arm('R', 0.0, 1.7, 0.0, 1.8)); merge(keys, 6, arm('L', -1.0, 0.7, -0.6, 0.5))
    merge(keys, 6, pole('L', -0.6, 1.0, 0.6))
    K(7, root_y=-0.5, pz=6.8, ppitch=-0.45, pyaw=0.0, proll=-0.95, cpitch=-0.7, croll=-0.8, hpitch=0.0, hroll=-0.3)
    merge(keys, 7, foot('L', -3.8, -1.5, 3.0, 25)); merge(keys, 7, foot('R', 2.7, 16.5, 4.8, -5))
    merge(keys, 7, arm('R', 0.0, 1.9, 0.0, 2.0)); merge(keys, 7, arm('L', -1.3, 0.7, -0.9, 0.5))
    K(8, root_y=1.0, pz=4.9, ppitch=-0.55, pyaw=0.0, proll=-1.1, cpitch=-0.85, croll=-0.95, hpitch=0.05, hroll=-0.35)
    merge(keys, 8, foot('L', -3.9, 0.0, 3.0, 25)); merge(keys, 8, foot('R', 2.7, 20.0, 4.0, -8))
    merge(keys, 8, arm('R', 0.0, 1.95, 0.0, 2.05)); merge(keys, 8, arm('L', -1.4, 0.7, -1.0, 0.5))
    K(9, root_y=2.0, pz=4.7, ppitch=-0.55, proll=-1.1, cpitch=-0.85, croll=-0.95, hpitch=0.05, hroll=-0.35)
    merge(keys, 9, foot('L', -3.9, 0.8, 3.0, 25)); merge(keys, 9, foot('R', 2.6, 22.0, 3.7, -6))
    # contact
    K(10, root_y=2.6, pz=4.7, ppitch=-0.55, proll=-1.1, cpitch=-0.85, croll=-0.95, hpitch=0.05, hroll=-0.35)
    merge(keys, 10, foot('L', -3.9, 1.2, 3.0, 25)); merge(keys, 10, foot('R', 2.5, 23.2, 3.6, 10))
    K(11, root_y=3.2, pz=4.7, ppitch=-0.55, proll=-1.1, cpitch=-0.85, croll=-0.95, hpitch=0.05, hroll=-0.35)
    merge(keys, 11, foot('L', -3.9, 1.6, 3.0, 25)); merge(keys, 11, foot('R', 2.5, 23.8, 3.8, 15))
    K(13, root_y=3.6, pz=4.8, ppitch=-0.55, proll=-1.1, cpitch=-0.85, croll=-0.95, hpitch=0.05, hroll=-0.35)
    merge(keys, 13, foot('L', -3.9, 1.8, 3.0, 25)); merge(keys, 13, foot('R', 2.5, 24.0, 3.6, 5))
    merge(keys, 13, arm('R', 0.0, 1.9, 0.0, 2.0)); merge(keys, 13, arm('L', -1.4, 0.7, -1.0, 0.5))
    # recover
    K(14, root_y=3.8, pz=5.6, ppitch=-0.5, proll=-0.9, cpitch=-0.5, croll=-0.7, hpitch=0.1, hroll=-0.3)
    merge(keys, 14, foot('L', -3.4, 3.0, 3.2, 20)); merge(keys, 14, foot('R', 2.4, 18.0, 5.5, 0))
    merge(keys, 14, arm('R', 0.2, 1.4, 0.6, 1.2)); merge(keys, 14, arm('L', -1.0, 0.8, -0.5, 0.6))
    K(15, root_y=4.2, pz=8.8, ppitch=-0.2, proll=-0.55, cpitch=-0.1, croll=-0.35, hpitch=0.1, hroll=-0.15)
    merge(keys, 15, footg('L', -3.2, 4.5, 10)); merge(keys, 15, foot('R', 2.2, 11.0, 6.5, 0))
    merge(keys, 15, arm('R', 0.4, 1.0, 0.9, 0.8)); merge(keys, 15, arm('L', -0.2, 0.9, 0.6, 0.6))
    merge(keys, 15, pole('L', -0.3, 1.0, 0.3))
    K(16, root_y=4.8, pz=13.5, ppitch=0.2, proll=-0.2, cpitch=0.25, croll=-0.1, hpitch=0.15, hroll=0.0)
    merge(keys, 16, footg('L', -3.0, 3.8, 0)); merge(keys, 16, footg('R', 2.4, 9.5, 0, c=0.0))
    merge(keys, 16, arm('R', 0.5, 0.9, 1.1, 0.6)); merge(keys, 16, arm('L', 0.3, 0.9, 1.0, 0.6))
    K(17, root_y=5.2, pz=18.5, ppitch=0.3, proll=0.0, cpitch=0.4, croll=0.0, hpitch=0.2)
    merge(keys, 17, footg('L', -3.0, 3.6, 0)); merge(keys, 17, footg('R', 2.6, 9.0, 0))
    merge(keys, 17, arm('R', 0.4, 0.9, 1.2, 0.5)); merge(keys, 17, arm('L', 0.4, 0.9, 1.2, 0.5))
    for f in (18, 19, 20, 21):
        K(f, root_y=5.6 + 0.2 * (f - 18), pz=21.0 + 0.3 * (f == 18) + 0.4 * (f > 18), ppitch=0.2, proll=0.0,
          cpitch=0.3, croll=0.0, hpitch=0.1)
        merge(keys, f, footg('L', -3.2, 3.6, 0)); merge(keys, f, footg('R', 2.8, 9.0, 0))
        merge(keys, f, arm('R', 0.4, 0.95, 1.2, 0.5)); merge(keys, f, arm('L', 0.4, 0.95, 1.2, 0.5))
    # ball: rests, poked away at f10
    for i, (x, y, z) in enumerate([(1.5, 30.0, 3.0), (1.9, 35.5, 3.8), (2.1, 41.0, 4.6), (2.2, 46.0, 5.2)]):
        merge(keys, 10 + i, dict(bx=x, by=y, bz=z, brx=2.0 * i, bvis=1.0))
    poses = build_anim(keys, N)

    # turf spray: from the hip/leg while sliding, and at the lead foot
    rng = random.Random(7)
    parts = []
    for f in range(5, 13):
        ry = poses[f]['root_y']
        for _ in range(3):
            parts.append((f, -3.0 + rng.uniform(-2.2, 2.2), ry + rng.uniform(-2, 3), 0.8,
                          rng.uniform(-0.9, 0.9), rng.uniform(0.2, 1.1), rng.uniform(0.5, 1.2)))
    for f in range(8, 12):
        for _ in range(2):
            parts.append((f, 2.5 + rng.uniform(-1.5, 1.5), poses[f]['R_ay'] + rng.uniform(-1, 1), 0.8,
                          rng.uniform(-0.8, 0.8), rng.uniform(0.0, 0.7), rng.uniform(0.5, 1.0)))
    cols = [(176, 214, 124), (150, 196, 104), (196, 160, 110), (226, 232, 170)]
    dust = []
    for f in range(N):
        lst = []
        for (f0, x, y, z, vx, vy, vz) in parts:
            age = f - f0
            if 0 <= age <= 4:
                zz = z + vz * age - 0.22 * age * age
                if zz < 0.4:
                    zz = 0.4
                col = cols[(f0 * 7 + int(x * 10)) % 4]
                lst.append((x + vx * age, y + vy * age, zz, 2 if age <= 1 else 1, col, 255 - 45 * age))
        dust.append(lst)
    return poses, dust


# ------------------------------------------------------------------ output helpers
def render_all(name, poses, dust):
    ramps = build_ramps(BASE)
    frames = {}
    for dn in DIRS:
        for k, pose in enumerate(poses):
            frames[(dn, k)] = render_pose(BASE, dn, pose, ramps, dust[k] if dust else None)
    return frames


def make_sheet(frames, n, path):
    sheet = Image.new('RGBA', (CW * n, CH * len(DIRS)), (0, 0, 0, 0))
    for r, dn in enumerate(DIRS):
        for k in range(n):
            sheet.paste(frames[(dn, k)], (k * CW, r * CH))
    sheet.save(path)


def pitch_bg(w, h, stripe=14):
    bg = Image.new('RGBA', (w, h), (78, 150, 74, 255))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, stripe):
        if (y // stripe) % 2:
            d.rectangle([0, y, w, y + stripe - 1], fill=(88, 164, 82, 255))
    return bg


def make_gif(frames, n, label, path, dur=FPS_MS, S=3):
    cols, rows = 4, 2
    W_, H_ = CW * cols, CH * rows
    font = ImageFont.load_default()
    out = []
    for k in range(n):
        bg = pitch_bg(W_, H_)
        for i, dn in enumerate(DIRS):
            bg.alpha_composite(frames[(dn, k)], ((i % cols) * CW, (i // cols) * CH))
        big = bg.resize((W_ * S, H_ * S), Image.NEAREST).convert('RGB')
        td = ImageDraw.Draw(big)
        for i, dn in enumerate(DIRS):
            td.text(((i % cols) * CW * S + 6, (i // cols) * CH * S + 4), dn, fill=(255, 255, 255), font=font)
        td.text((6, H_ * S - 14), f'{label}  frame {k + 1}/{n}', fill=(255, 255, 255), font=font)
        out.append(big)
    out[0].save(path, save_all=True, append_images=out[1:], duration=dur, loop=0)


def make_strip(frames, n, label, dname, path, S=2, per_row=11):
    rows = (n + per_row - 1) // per_row
    W_, H_ = CW * per_row, CH * rows
    bg = pitch_bg(W_, H_, 28)
    for k in range(n):
        bg.alpha_composite(frames[(dname, k)], ((k % per_row) * CW, (k // per_row) * CH))
    big = bg.resize((W_ * S, H_ * S), Image.NEAREST).convert('RGB')
    ImageDraw.Draw(big).text((6, 4), f'{label} ({dname})', fill=(255, 255, 255), font=ImageFont.load_default())
    big.save(path)


ANIMS = {
    'kick': (anim_kick, 'Kick (driven instep)', FPS_MS),
    'finesse': (anim_finesse, 'Finesse (inside-foot curler)', FPS_MS),
    'guard': (anim_guard, 'Guard (jockey)', 85),
    'slide': (anim_slide, 'Slide tackle', FPS_MS),
}


def main(outdir='out_actions', only=None):
    os.makedirs(outdir, exist_ok=True)
    for name in (only or list(ANIMS)):
        fn, label, dur = ANIMS[name]
        print('building', name, flush=True)
        poses, dust = fn()
        frames = render_all(name, poses, dust)
        n = len(poses)
        make_sheet(frames, n, f'{outdir}/{name}_sheet.png')
        make_gif(frames, n, label, f'{outdir}/{name}_preview.gif', dur)
        make_strip(frames, n, label, 'E', f'{outdir}/{name}_strip_E.png')
        make_strip(frames, n, label, 'S', f'{outdir}/{name}_strip_S.png')


if __name__ == '__main__':
    main(only=sys.argv[1:] or None)
