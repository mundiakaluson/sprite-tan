"""
UV-lookup sprite pipeline (the 'skin texture' technique):
  * animation sheets store, per pixel, WHICH TEXEL of a small skin atlas to show (R=x, G=y) and a tone (B)
  * the skin atlas (96x24) is painted once; kits / skin tones / hair / mud are just different atlases
Reuses the pose engine from gen_actions.py (kick, finesse, guard, slide) + a run cycle.
"""
import math, os, sys, json, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import gen_player_v2 as G
import gen_actions as A
from gen_actions import BASE, Ry, ik3, run_pose, DEFAULT, foot_mat
from gen_player_v2 import (VEC, DIRS, I3, Rz, Rx, NV, UP, EX, sE, cE, face_matrix, FOOT_ABC, NUM, ICO, LDIR)

NDIR = int(os.environ.get('UV_DIRS', 32))          # facing directions rendered (8 = compass only)
if NDIR != 8:
    DIRS = [f'a{i:02d}' for i in range(NDIR)]       # a00 = facing the camera (S), then increasing towards E, N, W
    VEC = {d: (math.sin(2 * math.pi * i / NDIR), math.cos(2 * math.pi * i / NDIR)) for i, d in enumerate(DIRS)}
PREV_DIRS = [DIRS[i * NDIR // 8] for i in range(8)]
SC = float(os.environ.get('UV_SC', 0.45))      # world units -> pixels
CW = CH = int(round(56 * SC / 0.62 / 2)) * 2
OX, OY = CW // 2, int(round(CH * 0.75))
OUTLINE = os.environ.get('UV_OUTLINE', '0') == '1'   # 0 = no outline, tonal separation only
CK = 1.12                    # chunkier limbs for the simple look

# ------------------------------------------------------------------ skin atlas layout (x, y, w, h)
REG = dict(CHEST=(0, 0, 28, 12), WAIST=(28, 0, 28, 5), SHORTS=(28, 5, 28, 7),
           THIGH=(56, 0, 12, 10), SHANK=(68, 0, 12, 10), UPARM=(80, 0, 8, 6), FOREARM=(88, 0, 8, 6),
           HEAD=(0, 12, 16, 10), NECK=(16, 12, 8, 3), BOOT=(24, 12, 12, 6), HAND=(36, 12, 4, 2), BALL=(40, 12, 8, 6), HAIR=(48, 12, 16, 6))
ATLAS_W, ATLAS_H = 96, 24
PID = {n: i for i, n in enumerate(REG)}

# tone table shared by the Python compositor and the Godot shader: out = base * MUL + ADD
TONE_MUL = np.array([[.55, .52, .72], [.78, .76, .90], [1, 1, 1], [.72, .72, .72], [.45, .42, .60], [.32, .30, .42]], np.float32)
TONE_ADD = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0], [.28 * 255, .28 * 245, .28 * 225], [0, 0, 0], [0, 0, 0]], np.float32)
TONE_STEP = 40


# ------------------------------------------------------------------ tiny UV ray-caster
class SceneUV:
    def __init__(self):
        self.depth = np.full((CH, CW), -1e9, np.float32)
        self.ux = np.full((CH, CW), -1, np.int16)
        self.uy = np.zeros((CH, CW), np.int16)
        self.pid = np.full((CH, CW), -1, np.int16)
        self.nrm = np.zeros((CH, CW, 3), np.float32)


def uv_angular(reg, phi, v):
    rx, ry, w, h = REG[reg]
    u = np.mod(phi + 0.75 * np.pi, 2 * np.pi) / (2 * np.pi)
    x = rx + np.clip((u * w).astype(int), 0, w - 1)
    y = ry + np.clip((np.asarray(v) * h).astype(int), 0, h - 1)
    return x, y


def add_ell(sc, C, M, abc, uvfn, pid, pad=1.0):
    C = np.asarray(C, float)
    abc = np.asarray(abc, float)
    r = (abc.max() + pad) * SC + 1
    cx, cy = OX + C[0] * SC, OY - float(C @ UP) * SC
    x0, x1 = max(0, int(math.floor(cx - r))), min(CW, int(math.ceil(cx + r)) + 1)
    y0, y1 = max(0, int(math.floor(cy - r))), min(CH, int(math.ceil(cy + r)) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    u = ((np.arange(x0, x1) + 0.5 - OX) / SC)[None, :]
    w = ((OY - (np.arange(y0, y1) + 0.5)) / SC)[:, None]
    Q0 = u[..., None] * EX + w[..., None] * UP - C
    Ql = (Q0 @ M) / abc
    Nl = (NV @ M) / abc
    Aq = float(Nl @ Nl)
    B = Ql @ Nl
    Cc = (Ql * Ql).sum(-1) - 1.0
    disc = B * B - Aq * Cc
    ok = disc >= 0
    s = np.where(ok, (-B + np.sqrt(np.where(ok, disc, 0.0))) / Aq, -1e9)
    Lu = Ql + s[..., None] * Nl
    nw = (Lu / abc) @ M.T
    nw = nw / (np.linalg.norm(nw, axis=-1, keepdims=True) + 1e-9)
    X, Y = uvfn(Lu, nw)
    upd = ok & (s > sc.depth[y0:y1, x0:x1]) & (X >= 0)
    sc.depth[y0:y1, x0:x1][upd] = s[upd]
    sc.ux[y0:y1, x0:x1][upd] = X[upd]
    sc.uy[y0:y1, x0:x1][upd] = Y[upd]
    sc.pid[y0:y1, x0:x1][upd] = pid
    sc.nrm[y0:y1, x0:x1][upd] = nw[upd]


def ell_uv(reg, flip=1.0):
    def fn(Lu, nw):
        return uv_angular(reg, np.arctan2(flip * Lu[..., 0], Lu[..., 1]), (1 - Lu[..., 2]) / 2)
    return fn


def const_uv(reg, cx, cy):
    rx, ry, w, h = REG[reg]

    def fn(Lu, nw):
        return np.full(nw.shape[:2], rx + cx, int), np.full(nw.shape[:2], ry + cy, int)
    return fn


def boot_uv(side):
    def fn(Lu, nw):
        phi = np.arctan2(side * Lu[..., 0], Lu[..., 2])
        return uv_angular('BOOT', phi, (Lu[..., 1] + 1) / 2)
    return fn


def add_limb(sc, A_, B_, rfun, reg, pid, fwd0, right0, step=0.35):
    A_, B_ = np.asarray(A_, float), np.asarray(B_, float)
    L = float(np.linalg.norm(B_ - A_))
    a = (B_ - A_) / (L + 1e-9)
    f = fwd0 - a * float(fwd0 @ a)
    if np.linalg.norm(f) < 0.35:
        r_ = right0 - a * float(right0 @ a)
        r_ /= np.linalg.norm(r_) + 1e-9
        f = np.cross(r_, a)
    f = f / (np.linalg.norm(f) + 1e-9)
    right = np.cross(a, f)
    n = max(2, int(L / step))
    rx, ry, w, h = REG[reg]
    for i in range(n + 1):
        t = i / n
        r = rfun(t)

        def fn(Lu, nw, t=t):
            X, _ = uv_angular(reg, np.arctan2(nw @ right, nw @ f), 0.0)
            return X, np.full(X.shape, ry + min(h - 1, int(t * h)), int)
        add_ell(sc, A_ + (B_ - A_) * t, I3, (r, r, r), fn, pid, pad=0.5)


# ------------------------------------------------------------------ the body, as UV
def build_scene(pose, dname, with_ball=False):
    P = BASE
    f = VEC[dname]
    Rf = face_matrix(f)
    sc = SceneUV()
    g = lambda k: pose[k]
    b = P['build']
    Lt, Ls = 11.6 * P['legs'], 11.0 * P['legs']
    tr = P['trunk']
    hipW = 2.5 * b
    P0 = np.array([g('root_x'), g('root_y'), g('pz')])
    Rp = Rz(g('pyaw')) @ Rx(-g('ppitch')) @ Ry(g('proll'))
    Rc = Rz(g('cyaw')) @ Rx(-g('cpitch')) @ Ry(g('croll'))
    Rh = Rz(g('hyaw')) @ Rx(-g('hpitch')) @ Ry(g('hroll'))
    W = lambda v: Rf @ np.asarray(v, float)
    Mw = lambda R: Rf @ R
    fwd0, right0 = Rf @ np.array([0, 1.0, 0]), Rf @ np.array([1.0, 0, 0])

    Wst = P0 + Rp @ np.array([0, 0, 6.2 * tr])
    chest_c = Wst + Rc @ np.array([0, 0.2, 4.2 * tr])
    neck_b = Wst + Rc @ np.array([0, 0.1, 8.7 * tr])
    neck_t = neck_b + Rh @ np.array([0, 0.25, 2.0])
    head_c = neck_t + Rh @ np.array([0, 0.45, 3.0])
    sh_off = 4.7 * b

    add_ell(sc, W(P0 + Rp @ np.array([0, 0, 0.3])), Mw(Rp), (4.35 * b, 3.1, 3.3), ell_uv('SHORTS'), PID['SHORTS'])
    add_ell(sc, W(P0 + Rp @ np.array([0, 0, 4.4 * tr])), Mw(Rp), (4.05 * b, 2.95, 3.7 * tr), ell_uv('WAIST'), PID['WAIST'])
    add_ell(sc, W(chest_c), Mw(Rc), (4.95 * b, 3.45, 5.4 * tr), ell_uv('CHEST'), PID['CHEST'])
    add_limb(sc, W(neck_b), W(neck_t), lambda t_: 1.75 * b, 'NECK', PID['NECK'], fwd0, right0)
    add_ell(sc, W(head_c), Mw(Rh), (3.05, 3.35, 3.6), ell_uv('HEAD'), PID['HEAD'])

    for s, side in (('R', 1), ('L', -1)):
        Hj = P0 + Rp @ np.array([side * hipW, 0, -0.3])
        Ank = np.array([g(s + '_ax'), g(s + '_ay'), g(s + '_az')])
        pv = np.array([g(s + '_kx'), g(s + '_ky'), g(s + '_kz')])
        K, A2 = ik3(Hj, Ank, Lt, Ls, pv)
        ts = 0.46

        def thigh_r(t_, b=b):
            return CK * ((3.45 * b - 0.35 * t_) if t_ < ts else (2.55 * b - 0.8 * (t_ - ts) / (1 - ts)))
        add_limb(sc, W(Hj), W(K), thigh_r, 'THIGH', PID['THIGH'], fwd0, right0)
        add_limb(sc, W(K), W(A2), lambda t_, b=b: CK * (2.15 * b + 0.45 * math.sin(math.pi * t_) - 0.85 * t_),
                 'SHANK', PID['SHANK'], fwd0, right0)
        Mf = foot_mat(g(s + '_fp'), g(s + '_fy'), g(s + '_fr'))
        fc = A2 + Mf @ np.array([0, 1.3, -1.1])
        add_ell(sc, W(fc), Mw(Mf), tuple(np.array(FOOT_ABC) * 1.05), boot_uv(side), PID['BOOT'])

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
        add_ell(sc, W(J), I3, (2.35 * b,) * 3, const_uv('UPARM', 3, 0), PID['UPARM'])
        add_limb(sc, W(J), W(Ep), lambda t_, b=b: CK * (1.95 * b - 0.45 * t_) * (1.08 if t_ < 0.62 else 1.0),
                 'UPARM', PID['UPARM'], fwd0, right0)
        add_limb(sc, W(Ep), W(Wr), lambda t_, b=b: CK * (1.5 * b - 0.35 * t_), 'FOREARM', PID['FOREARM'], fwd0, right0)
        add_ell(sc, W(Hd), I3, (1.5,) * 3, const_uv('HAND', 1, 0), PID['HAND'])

    if with_ball and g('bvis') > 0.5:
        Mb = Mw(Rz(g('brz')) @ Rx(-g('brx')))
        add_ell(sc, W(np.array([g('bx'), g('by'), g('bz')])), Mb, (A.BR,) * 3, ell_uv('BALL'), PID['BALL'])
    info = dict(head_c=head_c, Rh=Rh, Rf=Rf, W=W, Mw=Mw, fwd0=fwd0, right0=right0)
    return sc, info


def render_uv(pose, dname, with_ball=False):
    return finish_uv(build_scene(pose, dname, with_ball)[0])


def finish_uv(sc):
    op = sc.ux >= 0
    lam = sc.nrm @ LDIR
    tone = np.digitize(lam, [-0.18, 0.28, 0.74]).astype(np.int16)
    d = sc.depth
    pd = np.pad(d, 1, constant_values=-1e9)
    pp = np.pad(sc.pid, 1, constant_values=-1)
    edge = np.zeros_like(op)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nd = pd[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW]
        npid = pp[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW]
        diff = nd - d
        edge |= op & (npid >= 0) & (((diff > 3.6) & (npid != sc.pid)) | (diff > 9.0))
    tone[edge] = 4 if OUTLINE else 1
    ux, uy = sc.ux.copy(), sc.uy.copy()
    pux = np.pad(sc.ux, 1, constant_values=-1)
    puy = np.pad(sc.uy, 1, constant_values=0)
    pop = np.pad(op, 1, constant_values=False)
    outm = np.zeros_like(op)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = pop[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW]
        cand = nb & ~op & ~outm
        ux[cand] = pux[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW][cand]
        uy[cand] = puy[1 + dy:1 + dy + CH, 1 + dx:1 + dx + CW][cand]
        outm |= cand
    if not OUTLINE:
        outm = np.zeros_like(op)
    tone[outm] = 5
    alpha = np.where(op | outm, 255, 0).astype(np.uint8)
    uv = np.zeros((CH, CW, 4), np.uint8)
    full = op | outm
    uv[..., 0] = np.where(full, ux, 0)
    uv[..., 1] = np.where(full, uy, 0)
    uv[..., 2] = np.where(full, tone * TONE_STEP, 0)
    uv[..., 3] = alpha
    return uv


# ------------------------------------------------------------------ skins
def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


GLYPH = {'0': ["111", "101", "101", "101", "111"], '1': ["010", "110", "010", "010", "111"],
         '2': ["111", "001", "111", "100", "111"], '3': ["111", "001", "011", "001", "111"],
         '4': ["101", "101", "111", "001", "001"], '5': ["111", "100", "111", "001", "111"],
         '6': ["111", "100", "111", "101", "111"], '7': ["111", "001", "010", "010", "010"],
         '8': ["111", "101", "111", "101", "111"], '9': ["111", "101", "111", "001", "111"]}


def make_skin(s):
    A_ = np.zeros((ATLAS_H, ATLAS_W, 4), np.uint8)

    def fill(reg, x0, y0, x1, y1, col):
        rx, ry, w, h = REG[reg]
        A_[ry + y0:ry + y1 + 1, rx + x0:rx + x1 + 1] = tuple(col) + (255,)
    j, j2, sh, sh2, sk = s['jersey'], s['trim'], s['shorts'], s['shorts_trim'], s['skin']
    hair, sock, boot, acc = s['hair'], s['socks'], s['boots'], s['accent']
    # chest: [left 0-6 | front 7-13 | right 14-20 | back 21-27]
    fill('CHEST', 0, 0, 27, 11, j)
    fill('CHEST', 0, 0, 27, 0, j2)                         # collar ring
    fill('CHEST', 9, 1, 11, 2, sk)                         # V-neck
    band = s.get('band') or j2
    pat = s.get('pattern') or ('hoop' if s.get('band') else 'plain')
    if pat == 'hoop':
        fill('CHEST', 0, 6, 27, 7, band)
    elif pat == 'hoops':
        fill('CHEST', 0, 4, 27, 5, band); fill('CHEST', 0, 8, 27, 9, band)
    elif pat == 'stripes':
        for cx in range(0, 28, 4):
            fill('CHEST', cx, 1, cx + 1, 11, band)
    elif pat == 'sash':
        for r in range(1, 12):
            fill('CHEST', max(0, min(27, 5 + r)), r, max(0, min(27, 6 + r)), r, band)
    num = s['number']
    digs = list(num)
    x0 = 21 + (7 - (len(digs) * 3 + (len(digs) - 1))) // 2
    for di, ch in enumerate(digs):
        for r, row in enumerate(GLYPH[ch]):
            for c, bit in enumerate(row):
                if bit == '1':
                    rx, ry, _, _ = REG['CHEST']
                    A_[ry + 3 + r, rx + x0 + di * 4 + c] = j2 + (255,)
    fill('WAIST', 0, 0, 27, 4, j)
    fill('SHORTS', 0, 0, 27, 6, sh)
    fill('SHORTS', 0, 0, 27, 0, sh2)
    for cx in (3, 17):
        fill('SHORTS', cx, 1, cx, 6, s['stripe'])
    # thigh: [left 0-2 | front 3-5 | right 6-8 | back 9-11], rows 0-3 shorts, 4 hem, 5-9 skin
    fill('THIGH', 0, 0, 11, 3, sh)
    for cx in (1, 7):
        fill('THIGH', cx, 0, cx, 3, s['stripe'])
    fill('THIGH', 0, 4, 11, 4, sh2)
    fill('THIGH', 0, 5, 11, 9, sk)
    fill('SHANK', 0, 0, 11, 0, sk)
    fill('SHANK', 0, 1, 11, 1, s['sock_trim'])
    fill('SHANK', 0, 2, 11, 9, sock)
    fill('UPARM', 0, 0, 7, 2, j)
    fill('UPARM', 0, 3, 7, 3, j2)
    fill('UPARM', 0, 4, 7, 5, sk)
    fill('FOREARM', 0, 0, 7, 5, sk)
    fill('HAND', 0, 0, 3, 1, s.get('glove', sk))
    fill('NECK', 0, 0, 7, 2, sk)
    # boot [inner 0-2 | top 3-5 | outer 6-8 | sole 9-11], rows heel->toe
    fill('BOOT', 0, 0, 11, 5, boot)
    fill('BOOT', 4, 0, 4, 3, (240, 240, 250))
    fill('BOOT', 7, 1, 7, 4, acc)
    fill('BOOT', 9, 0, 11, 5, tuple(int(c * 0.55) for c in boot))
    # head [left 0-3 | front 4-7 | right 8-11 | back 12-15]
    if s.get('hair_style') == 'H01_buzz':
        fill('HEAD', 0, 0, 15, 1, hair)
        fill('HEAD', 0, 2, 3, 2, hair); fill('HEAD', 8, 2, 15, 2, hair)
        fill('HEAD', 4, 2, 7, 2, sk)
        fill('HEAD', 0, 3, 15, 9, sk)
        fill('HEAD', 12, 3, 15, 4, hair)
    else:
        fill('HEAD', 0, 0, 15, 2, hair)
        fill('HEAD', 0, 3, 3, 3, hair); fill('HEAD', 8, 3, 15, 3, hair)
        fill('HEAD', 4, 3, 7, 3, sk)
        fill('HEAD', 0, 4, 15, 9, sk)
        fill('HEAD', 12, 3, 15, 6, hair)
        fill('HEAD', 0, 4, 0, 4, hair); fill('HEAD', 11, 4, 11, 4, hair)
    # hair geometry texture: base colour with faint vertical strands
    fill('HAIR', 0, 0, 15, 5, hair)
    for cx in range(1, 16, 4):
        fill('HAIR', cx, 0, cx, 5, tuple(int(c * 0.88) for c in hair))
    for cx in (4, 7):
        fill('HEAD', cx, 4, cx, 4, (34, 24, 30))
    # ball
    fill('BALL', 0, 0, 7, 5, (244, 246, 252))
    fill('BALL', 0, 0, 7, 0, (36, 38, 60)); fill('BALL', 0, 5, 7, 5, (36, 38, 60))
    for (cx, cy) in ((1, 2), (3, 3), (5, 2), (7, 3)):
        fill('BALL', cx, cy, cx, cy, (36, 38, 60))
    if s.get('mud'):
        add_mud(A_, random.Random(11))
    return A_


def add_mud(A_, rng):
    mud = [(128, 94, 58), (156, 116, 72), (100, 72, 46)]

    def splat(reg, y0, y1, p):
        rx, ry, w, h = REG[reg]
        for y in range(y0, y1 + 1):
            for x in range(w):
                if rng.random() < p * (0.4 + 0.6 * (y - y0 + 1) / (y1 - y0 + 1)):
                    A_[ry + y, rx + x] = rng.choice(mud) + (255,)
    splat('THIGH', 5, 9, 0.85); splat('SHANK', 2, 9, 1.10); splat('BOOT', 0, 5, 0.80)
    splat('SHORTS', 2, 6, 0.65); splat('WAIST', 1, 4, 0.55); splat('CHEST', 7, 11, 0.55)
    splat('FOREARM', 2, 5, 0.45); splat('UPARM', 3, 5, 0.3)


SKINS = {
    'home': dict(jersey=hexc('d63240'), trim=hexc('f4f4fa'), shorts=hexc('f0f0f8'), shorts_trim=hexc('d63240'),
                 stripe=hexc('d63240'), socks=hexc('d63240'), sock_trim=hexc('f4f4fa'), skin=hexc('eebe96'),
                 hair=hexc('62422a'), boots=hexc('f0f0fa'), accent=hexc('24243c'), number='10'),
    'away': dict(jersey=hexc('eceef6'), trim=hexc('24306e'), shorts=hexc('24306e'), shorts_trim=hexc('eceef6'),
                 stripe=hexc('eceef6'), socks=hexc('eceef6'), sock_trim=hexc('24306e'), skin=hexc('8a5a3c'),
                 hair=hexc('14101a'), boots=hexc('1c1c2c'), accent=hexc('f0c040'), number='7'),
    'keeper': dict(jersey=hexc('3caa5a'), trim=hexc('fad63c'), shorts=hexc('1c1c28'), shorts_trim=hexc('fad63c'),
                   stripe=hexc('3caa5a'), socks=hexc('1c1c28'), sock_trim=hexc('fad63c'), skin=hexc('5c3a28'),
                   hair=hexc('14101a'), boots=hexc('f08a30'), accent=hexc('1c1c28'), number='1', glove=hexc('e8f03c')),
    'third': dict(jersey=hexc('22222e'), trim=hexc('ecba3c'), shorts=hexc('ecba3c'), shorts_trim=hexc('22222e'),
                  stripe=hexc('22222e'), socks=hexc('22222e'), sock_trim=hexc('ecba3c'), skin=hexc('d09468'),
                  hair=hexc('d6a64c'), boots=hexc('62e04a'), accent=hexc('1c1c28'), number='9', band=hexc('ecba3c')),
}


def load_kits(path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'kits.csv')):
    """data/kits.csv (edited in the manager tool) replaces/extends the built-in kits above. Colours are #rrggbb; blank = not used."""
    import csv
    if not os.path.exists(path):
        return
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        k = {c: hexc(r[c]) for c in ('jersey', 'trim', 'shorts', 'shorts_trim', 'stripe', 'socks', 'sock_trim', 'boots', 'accent') if r.get(c)}
        for c in ('band', 'glove'):
            if r.get(c):
                k[c] = hexc(r[c])
        k['number'] = r.get('number') or '10'
        k['pattern'] = r.get('pattern') or 'plain'
        base = SKINS.get(r['id'], SKINS['home'])
        SKINS[r['id']] = dict(base, **k) if r['id'] in SKINS else dict(SKINS['home'], **k)
        for opt in ('band', 'glove'):
            if opt not in k:
                SKINS[r['id']].pop(opt, None)


load_kits()
SKINS['home_muddy'] = dict(SKINS['home'], mud=True)
SKIN_ORDER = [k for k in SKINS if k != 'home_muddy'] + ['home_muddy']


def apply_skin(uv, skin):
    x = uv[..., 0].astype(int).clip(0, ATLAS_W - 1)
    y = uv[..., 1].astype(int).clip(0, ATLAS_H - 1)
    base = skin[y, x, :3].astype(np.float32)
    t = np.rint(uv[..., 2] / TONE_STEP).astype(int).clip(0, 5)
    out = np.clip(base * TONE_MUL[t] + TONE_ADD[t], 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([out, uv[..., 3]]), 'RGBA')


# ------------------------------------------------------------------ preview extras (shadow + turf), not part of the sprite
def extras(pose, dname, dust=None):
    f = VEC[dname]
    Rf = face_matrix(f)
    g = lambda k: pose[k]
    pts = [(g('root_x'), g('root_y')), (g('R_ax'), g('R_ay')), (g('L_ax'), g('L_ay'))]
    wp = np.array([(Rf @ np.array([p[0], p[1], 0]))[:2] for p in pts])
    x0, x1, y0, y1 = wp[:, 0].min(), wp[:, 0].max(), wp[:, 1].min(), wp[:, 1].max()
    scx, scy = OX + ((x0 + x1) / 2 + 2.0) * SC, OY + ((y0 + y1) / 2) * sE * SC - 0.5
    rx = max(8.2, (x1 - x0) / 2 + 5.5) * SC
    ry = max(3.4, (y1 - y0) / 2 * sE + 2.8) * SC
    under = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(under)
    d.ellipse([scx - rx, scy - ry, scx + rx, scy + ry], fill=(10, 10, 30, 80))
    if g('bvis') > 0.5:
        bw = Rf @ np.array([g('bx'), g('by'), 0])
        bx_, by_ = OX + (bw[0] + 1.0 + g('bz') * 0.25) * SC, OY + bw[1] * sE * SC
        d.ellipse([bx_ - 2.2, by_ - 1.1, bx_ + 2.2, by_ + 1.1], fill=(10, 10, 30, 90))
    over = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    if dust:
        for (x, y, z, size, col, a) in dust:
            p = Rf @ np.array([x, y, z])
            px, py = int(math.floor(OX + p[0] * SC)), int(math.floor(OY - float(p @ UP) * SC))
            tgt = under if z < 2.0 else over
            if 0 <= px < CW and 0 <= py < CH:
                tgt.putpixel((px, py), col + (a,))
                if size > 1 and px + 1 < CW:
                    tgt.putpixel((px + 1, py), col + (a,))
    return under, over


def leg_trail(prev, cur, dname, atlas=None, n=3):
    """speed effect for the plain dribbles ('fxm' > 0): quicksilver legs. Grey translucent afterimages of the LEGS ONLY from the previous frames of the same
    animation, pushed back along the direction of travel, plus short speed streaks off the boots. A game-side effect (the game draws the previous frames' leg rows
    tinted grey, under the sprite). prev = previous world poses, nearest first; cur = this frame's world pose. Returns an RGBA layer or None."""
    m = cur.get('fxm', 0.0)
    if m < 0.02 or not prev: return None
    Rf = face_matrix(VEC[dname]); T = cur.get('fxd', 0.0)
    pv = Rf @ np.array([-math.sin(T), math.cos(T), 0.0]); sx, sy = pv[0] * SC, -float(pv @ UP) * SC
    L = max(math.hypot(sx, sy), 0.6 * SC); ux, uy = -sx / L, -sy / L
    cc = centered(cur)
    hp = Rf @ np.array([cc['root_x'], cc['root_y'], cc['pz']]); hip_row = int(OY - float(hp @ UP) * SC) + 3
    out = np.zeros((CH, CW, 4), np.uint8)
    for i, pp in enumerate(prev[:n], 1):
        al = np.array(render_uv(centered(pp, cur), dname, False))[..., 3] > 0
        al[:hip_row] = False
        ox = int(round(ux * 2.2 * i)); oy = int(round(uy * 2.2 * i))
        sh = np.zeros_like(al); ys0, ys1 = max(0, oy), min(CH, CH + oy); xs0, xs1 = max(0, ox), min(CW, CW + ox)
        sh[ys0:ys1, xs0:xs1] = al[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox]
        out[sh] = (200, 205, 216, int(130 * m * (1.0 - 0.3 * (i - 1))))
    for s_ in ('R', 'L'):                                   # streaks trailing off each boot
        fp = Rf @ np.array([cc[s_ + '_ax'], cc[s_ + '_ay'], cc[s_ + '_az']])
        px, py = OX + fp[0] * SC, OY - float(fp @ UP) * SC
        for j in range(1, 9):
            x, y = int(round(px + ux * j)), int(round(py + uy * j))
            if 0 <= x < CW and 0 <= y < CH and out[y, x, 3] < 150: out[y, x] = (214, 218, 228, int(150 * m * (1 - j / 9.0)))
    return Image.fromarray(out, 'RGBA')


def bg_pitch(w, h, stripe=12):
    bg = Image.new('RGBA', (w, h), (78, 150, 74, 255))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, stripe):
        if (y // stripe) % 2:
            d.rectangle([0, y, w, y + stripe - 1], fill=(88, 164, 82, 255))
    return bg


# ------------------------------------------------------------------ animations
def anim_run():
    return [dict(DEFAULT, **run_pose(BASE, k / 12.0, 0.0)) for k in range(12)], None


def centered(pose, ref=None):
    p = dict(pose)
    dy = (ref or p)['root_y']
    for k in ('root_y', 'R_ay', 'L_ay', 'by'):
        p[k] = p[k] - dy
    if p.get('cx', 0.0) > 0.5:      # moves that travel sideways (turns, cuts): centre on x as well
        dx = (ref or p)['root_x']
        for k in ('root_x', 'R_ax', 'L_ax', 'bx'):
            p[k] = p[k] - dx
    return p


ANIMS = {
    'run': (anim_run, 57, True, {}),
    'kick': (A.anim_kick, 70, False, {'strike': 12}),
    'finesse': (A.anim_finesse, 70, False, {'strike': 12, 'curl': 'right-to-left'}),
    'guard': (A.anim_guard, 85, True, {}),
    'slide': (A.anim_slide, 70, False, {'contact': 10}),
}


try:   # animations authored in the manager tool (data/animations/*.json)
    import custom_anims
    custom_anims.register(ANIMS)
except ImportError:
    pass


def write_sheet(frames, n, path):
    sheet = Image.new('RGBA', (CW * n, CH * len(DIRS)), (0, 0, 0, 0))
    for r, dn in enumerate(DIRS):
        for k in range(n):
            sheet.paste(Image.fromarray(frames[(dn, k)], 'RGBA'), (k * CW, r * CH))
    sheet.save(path)


def main(outdir='out_uv'):
    os.makedirs(outdir, exist_ok=True)
    skins = {n: make_skin(SKINS[n]) for n in SKIN_ORDER}
    for n, arr in skins.items():
        Image.fromarray(arr, 'RGBA').save(f'{outdir}/skin_{n}.png')
    meta = dict(cell=[CW, CH], origin=[OX, OY], px_per_world_unit=SC, directions=DIRS, direction_degrees=[round(360.0 * i / len(DIRS), 3) for i in range(len(DIRS))],
                atlas=dict(size=[ATLAS_W, ATLAS_H], regions={k: list(v) for k, v in REG.items()}),
                encoding='R=skin texel x, G=skin texel y, B=tone*40 (0 shadow,1 dark,2 base,3 light,4 inner line,5 outline), A=1 for sprite pixels',
                animations={})
    shipped, preview = {}, {}
    for name, (fn, ms, loop, events) in ANIMS.items():
        print('animation', name, flush=True)
        poses, dust = fn()
        n = len(poses)
        ship = {(dn, k): render_uv(centered(poses[k]), dn) for dn in DIRS for k in range(n)}
        write_sheet(ship, n, f'{outdir}/{name}_uv_sheet.png')
        shipped[name] = ship
        prev = {(dn, k): render_uv(poses[k], dn, with_ball=name != 'guard') for dn in PREV_DIRS for k in range(n)}
        preview[name] = (poses, dust, prev, n)
        meta['animations'][name] = dict(frames=n, ms_per_frame=ms, loop=loop, events=events,
                                        root_forward_px=[round(p['root_y'] * SC, 2) for p in poses])
    json.dump(meta, open(f'{outdir}/animations.json', 'w'), indent=1)

    # skin swap preview (uses the shipped, root-centred run sheet): 5 skins x 3 facings
    S = 4
    facings = [DIRS[0], DIRS[NDIR // 4], DIRS[NDIR // 2]]
    frames_out = []
    for k in range(12):
        bg = bg_pitch(CW * 5, CH * 3)
        for ci, sn in enumerate(SKIN_ORDER):
            for ri, dn in enumerate(facings):
                spr = apply_skin(shipped['run'][(dn, k)], skins[sn])
                shadow = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
                ImageDraw.Draw(shadow).ellipse([OX - 7, OY - 2.6, OX + 7, OY + 2.6], fill=(10, 10, 30, 80))
                tile = Image.alpha_composite(shadow, spr)
                bg.alpha_composite(tile, (ci * CW, ri * CH))
        big = bg.resize((bg.width * S, bg.height * S), Image.NEAREST).convert('RGB')
        td = ImageDraw.Draw(big)
        for ci, sn in enumerate(SKIN_ORDER):
            td.text((ci * CW * S + 6, 4), sn, fill=(255, 255, 255), font=ImageFont.load_default())
        frames_out.append(big)
    frames_out[0].save(f'{outdir}/skins_preview.gif', save_all=True, append_images=frames_out[1:], duration=57, loop=0)

    # all actions x 8 directions with the home skin (root motion baked in, ball + turf added for the preview)
    S = 3
    order = ['run', 'kick', 'finesse', 'guard', 'slide']
    Nf = 22
    out = []
    for f_ in range(Nf):
        bg = bg_pitch(CW * 8, CH * len(order))
        for ri, an in enumerate(order):
            poses, dust, prev, n = preview[an]
            k = f_ % n
            for ci, dn in enumerate(PREV_DIRS):
                spr = apply_skin(prev[(dn, k)], skins['home'])
                under, over = extras(poses[k], dn, dust[k] if dust else None)
                tile = Image.alpha_composite(Image.alpha_composite(under, spr), over)
                bg.alpha_composite(tile, (ci * CW, ri * CH))
        big = bg.resize((bg.width * S, bg.height * S), Image.NEAREST).convert('RGB')
        td = ImageDraw.Draw(big)
        for ri, an in enumerate(order):
            td.text((6, ri * CH * S + 4), an, fill=(255, 255, 255), font=ImageFont.load_default())
        out.append(big)
    out[0].save(f'{outdir}/actions_preview.gif', save_all=True, append_images=out[1:], duration=70, loop=0)

    # paintable template
    T = 8
    tpl = Image.new('RGBA', (ATLAS_W * T, ATLAS_H * T), (40, 40, 52, 255))
    skin_img = Image.fromarray(skins['home'], 'RGBA').resize((ATLAS_W * T, ATLAS_H * T), Image.NEAREST)
    tpl.alpha_composite(skin_img)
    d = ImageDraw.Draw(tpl)
    for nme, (rx, ry, w, h) in REG.items():
        d.rectangle([rx * T, ry * T, (rx + w) * T - 1, (ry + h) * T - 1], outline=(255, 255, 0, 255))
        d.text((rx * T + 3, ry * T + 2), nme, fill=(255, 255, 0, 255), font=ImageFont.load_default())
        if nme in ('CHEST', 'WAIST', 'SHORTS', 'THIGH', 'SHANK', 'HEAD', 'BOOT', 'BALL'):
            for q in range(1, 4):
                xx = (rx + w * q / 4) * T
                d.line([xx, ry * T, xx, (ry + h) * T], fill=(120, 220, 255, 140), width=1)
    tpl.convert('RGB').save(f'{outdir}/skin_template_8x.png')

    open(f'{outdir}/uv_skin.gdshader', 'w').write(GDSHADER)
    open(f'{outdir}/README.txt', 'w').write(README)


GDSHADER = """shader_type canvas_item;
// Godot 4. Put this on a Sprite2D/AnimatedSprite2D that shows a *_uv_sheet.png frame.
// Import the sheet with: Filter = Nearest, Mipmaps = off, Compress = Lossless, no sRGB/"source_color" hint.
uniform sampler2D skin : filter_nearest, repeat_disable;

const vec3 TONE_MUL[6] = vec3[6](
    vec3(0.55, 0.52, 0.72), vec3(0.78, 0.76, 0.90), vec3(1.0), vec3(0.72),
    vec3(0.45, 0.42, 0.60), vec3(0.32, 0.30, 0.42));
const vec3 TONE_ADD[6] = vec3[6](
    vec3(0.0), vec3(0.0), vec3(0.0), vec3(0.28 * 1.0, 0.28 * 0.96, 0.28 * 0.88),
    vec3(0.0), vec3(0.0));

void fragment() {
    vec4 m = texture(TEXTURE, UV);
    if (m.a < 0.5) { discard; }
    ivec2 texel = ivec2(int(m.r * 255.0 + 0.5), int(m.g * 255.0 + 0.5));
    vec3 base = texelFetch(skin, texel, 0).rgb;
    int tone = clamp(int(m.b * 255.0 / 40.0 + 0.5), 0, 5);
    COLOR = vec4(base * TONE_MUL[tone] + TONE_ADD[tone], 1.0);
}
"""

README = """UV-lookup sprites
=================
*_uv_sheet.png   frames across, 8 directions down (S, SE, E, NE, N, NW, W, SW), 56x56 cells, origin (28,42)
                 pixel = (R: skin texel x, G: skin texel y, B: tone*40, A)
skin_*.png       96x24 skin atlas. Paint these. skin_template_8x.png shows the regions.
                 Body parts are 'unwrapped' as 4 panels: [left | front | right | back]
animations.json  frame counts, timing, strike/contact frames, root motion per frame
uv_skin.gdshader Godot 4 shader that applies a skin atlas to a sheet

Sheets are root-centred: move the player node in code using root_forward_px from animations.json.
Import with nearest filtering, no mipmaps, lossless, and no colour-space conversion.
"""

if __name__ == '__main__':
    main()
