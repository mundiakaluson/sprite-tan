"""
Hair styles for the UV sprite pipeline.

Hair is rendered as a SEPARATE layer sheet (same cell size, same UV encoding) that is drawn over the body sheet.
Only hair pixels that are nearer to the camera than the body are kept, so a ponytail behind the neck is hidden by
the body and a fringe in front of the face covers it, with one body sheet shared by every hair style.

Style = static ellipsoids in head space + optional sway chains (springy strands).
Head space: x = right, y = forward (face), z = up, origin = head centre (head ellipsoid radii 3.05, 3.35, 3.6).
"""
import math, os, copy, json
import numpy as np
from PIL import Image, ImageDraw
import gen_uv as U
from gen_uv import (SC, CW, CH, OX, OY, PID, REG, build_scene, finish_uv, add_ell, add_limb, ell_uv, SceneUV,
                    centered, apply_skin, make_skin, SKINS, DIRS, NDIR)
from gen_actions import BASE
from gen_player_v2 import Rz, Rx, I3

HAIR_PID = PID['HAIR']


# ------------------------------------------------------------------ style definitions
def E(c, abc, pitch=0.0, roll=0.0):
    return dict(c=np.array(c, float), abc=np.array(abc, float), pitch=pitch, roll=roll)


def CH_(anchor, direction, n, seg, r0, r1, k=0.20, damp=0.80, grav=0.10, wind=1.0):
    return dict(anchor=np.array(anchor, float), dir=np.array(direction, float) / np.linalg.norm(direction),
                n=n, seg=seg, r0=r0, r1=r1, k=k, damp=damp, grav=grav, wind=wind)


CAP = E((0, -0.8, 1.7), (3.30, 3.90, 3.40))

STYLES = {
    'H01_buzz': dict(static=[], chains=[]),
    'H02_crop': dict(static=[E((0, -0.7, 1.35), (3.15, 3.65, 3.40))], chains=[]),
    'H03_sidepart': dict(static=[CAP, E((1.6, 0.9, 4.6), (3.3, 3.2, 1.9), roll=0.55), E((2.4, 2.4, 3.4), (1.5, 1.2, 1.2))], chains=[]),
    'H04_quiff': dict(static=[CAP, E((0, 2.6, 5.2), (2.8, 2.6, 2.6), pitch=-0.9)], chains=[]),
    'H05_curly': dict(static=[
        E((0, -0.8, 1.9), (3.9, 4.2, 3.6)),
        E((0, 0.9, 5.0), (2.0, 2.0, 1.8)), E((-2.3, -0.2, 4.4), (2.0, 2.0, 1.8)), E((2.3, -0.2, 4.4), (2.0, 2.0, 1.8)),
        E((0, -2.2, 4.5), (2.1, 2.0, 1.8)), E((-3.6, -1.0, 2.6), (1.7, 1.9, 1.8)), E((3.6, -1.0, 2.6), (1.7, 1.9, 1.8)),
        E((-2.0, -3.4, 2.4), (1.8, 1.7, 1.7)), E((2.0, -3.4, 2.4), (1.8, 1.7, 1.7))], chains=[]),
    'H06_afro': dict(static=[E((0, -1.0, 3.1), (5.4, 5.4, 4.8))], chains=[]),
    'H07_braids': dict(static=[E((0, -0.7, 1.5), (3.25, 3.75, 3.45))], chains=[
        CH_((-2.2, -2.4, 0.4), (-0.25, -0.35, -1), 3, 2.6, 1.3, 0.9),
        CH_((2.2, -2.4, 0.4), (0.25, -0.35, -1), 3, 2.6, 1.3, 0.9),
        CH_((-0.9, -3.2, 0.9), (-0.05, -0.2, -1), 4, 2.6, 1.3, 0.9, k=0.17),
        CH_((0.9, -3.2, 0.9), (0.05, -0.2, -1), 4, 2.6, 1.3, 0.9, k=0.17)]),
    'H08_long': dict(static=[CAP], chains=[
        CH_((0, -3.0, 1.0), (0, -0.25, -1), 4, 2.5, 2.3, 1.5, k=0.14, damp=0.84),
        CH_((-2.6, -2.0, 0.8), (-0.15, -0.2, -1), 3, 2.4, 1.5, 1.0, k=0.16, damp=0.84),
        CH_((2.6, -2.0, 0.8), (0.15, -0.2, -1), 3, 2.4, 1.5, 1.0, k=0.16, damp=0.84)]),
    'H09_ponytail': dict(static=[E((0, -0.8, 1.6), (3.25, 3.8, 3.45)), E((0, -3.4, 2.9), (1.8, 1.8, 1.8))], chains=[
        CH_((0, -3.5, 2.7), (0, -0.55, -1), 4, 2.3, 1.5, 0.8, k=0.15, damp=0.82)]),
    'H10_bun': dict(static=[E((0, -0.8, 1.6), (3.25, 3.8, 3.45)), E((0, -1.2, 6.0), (2.8, 2.8, 2.7))], chains=[]),
}
STYLE_ORDER = list(STYLES)
# wind (character-local, units per frame of lateral push) applied to chains, per animation
WIND = {'run': (0.0, -0.32, 0.10), 'guard': (0.0, 0.0, 0.0), 'kick': (0.0, -0.08, 0.0),
        'finesse': (0.0, -0.08, 0.0), 'slide': (0.0, -0.3, 0.1)}


# ------------------------------------------------------------------ head frame of a pose (character-local)
def head_frame(pose):
    P = BASE
    g = lambda k: pose[k]
    tr = P['trunk']
    P0 = np.array([g('root_x'), g('root_y'), g('pz')])
    Rp = Rz(g('pyaw')) @ Rx(-g('ppitch')) @ U.Ry(g('proll'))
    Rc = Rz(g('cyaw')) @ Rx(-g('cpitch')) @ U.Ry(g('croll'))
    Rh = Rz(g('hyaw')) @ Rx(-g('hpitch')) @ U.Ry(g('hroll'))
    Wst = P0 + Rp @ np.array([0, 0, 6.2 * tr])
    neck_b = Wst + Rc @ np.array([0, 0.1, 8.7 * tr])
    neck_t = neck_b + Rh @ np.array([0, 0.25, 2.0])
    return neck_t + Rh @ np.array([0, 0.45, 3.0]), Rh


# ------------------------------------------------------------------ sway simulation
def simulate(style, poses, loop, anim):
    """per frame, per chain: (n+1, 3) points in character-local space (index 0 = anchor on the head)."""
    chains = STYLES[style]['chains']
    n_f = len(poses)
    if not chains:
        return [[] for _ in range(n_f)]
    wind = np.array(WIND.get(anim, (0, 0, 0)), float)
    hf = [head_frame(p) for p in poses]
    state = []
    for ch in chains:
        hc, Rh = hf[0]
        a0 = hc + Rh @ ch['anchor']
        d = Rh @ ch['dir']
        pts = np.array([a0 + d * ch['seg'] * i for i in range(ch['n'] + 1)])
        state.append([pts.copy(), pts.copy()])
    seq = list(range(n_f)) * 4 if loop else [0, 0, 0] + list(range(n_f))
    out = []
    for step, fi in enumerate(seq):
        hc, Rh = hf[fi]
        res = []
        for ci, ch in enumerate(chains):
            pts, prev = state[ci]
            a0 = hc + Rh @ ch['anchor']
            d = Rh @ ch['dir']
            new = pts.copy()
            new[0] = a0
            for i in range(1, ch['n'] + 1):
                rest = a0 + d * ch['seg'] * i
                vel = (pts[i] - prev[i]) * ch['damp']
                acc = (rest - pts[i]) * ch['k'] + np.array([0, 0, -ch['grav']]) + wind * ch['wind']
                new[i] = pts[i] + vel + acc
                v = new[i] - new[i - 1]
                new[i] = new[i - 1] + v / (np.linalg.norm(v) + 1e-9) * ch['seg']
            state[ci] = [new, pts]
            res.append(new.copy())
        if step >= len(seq) - n_f:
            out.append(res)
    return out


# ------------------------------------------------------------------ rendering one hair layer
def hair_layer(body_sc, info, style, chain_pts):
    """UV image of the hair pixels that are in front of the body."""
    sc = copy.deepcopy(body_sc)
    body_depth = body_sc.depth.copy()
    body_op = body_sc.ux >= 0
    hc, Rh, W, Mw = info['head_c'], info['Rh'], info['W'], info['Mw']
    spec = STYLES[style]
    for e in spec['static']:
        M = Mw(Rh @ Rx(-e['pitch']) @ U.Ry(e['roll']))
        add_ell(sc, W(hc + Rh @ e['c']), M, tuple(e['abc']), ell_uv('HAIR'), HAIR_PID, pad=0.5)
    for ch, pts in zip(spec['chains'], chain_pts):
        n = ch['n']
        for i in range(n):
            a, b = pts[i], pts[i + 1]
            r_a = ch['r0'] + (ch['r1'] - ch['r0']) * i / n
            r_b = ch['r0'] + (ch['r1'] - ch['r0']) * (i + 1) / n
            add_limb(sc, W(a), W(b), lambda t, r_a=r_a, r_b=r_b: r_a + (r_b - r_a) * t, 'HAIR', HAIR_PID,
                     info['fwd0'], info['right0'], step=0.9)
    uv = finish_uv(sc)
    keep = (sc.pid == HAIR_PID) & (sc.depth > np.where(body_op, body_depth, -1e9))
    uv[~keep] = 0
    return uv


# ------------------------------------------------------------------ skin helpers
def hair_skin(hair_rgb, style='H02_crop', base='home'):
    s = dict(SKINS[base], hair=hair_rgb, hair_style=style)
    return make_skin(s)


# ------------------------------------------------------------------ styles as data (data/hair_styles.json, edited in the manager tool)
STYLES_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'hair_styles.json')
_CH_KEYS = ('n', 'seg', 'r0', 'r1', 'k', 'damp', 'grav', 'wind')


def styles_to_json(styles):
    out = {}
    for name, sp in styles.items():
        out[name] = dict(
            static=[dict(c=[round(float(x), 3) for x in e['c']], abc=[round(float(x), 3) for x in e['abc']], pitch=round(float(e['pitch']), 3), roll=round(float(e['roll']), 3)) for e in sp['static']],
            chains=[dict(anchor=[round(float(x), 3) for x in c['anchor']], dir=[round(float(x), 3) for x in c['dir']], **{k: c[k] for k in _CH_KEYS}) for c in sp['chains']])
    return out


def styles_from_json(d):
    out = {}
    for name, sp in d.items():
        out[name] = dict(static=[E(e['c'], e['abc'], e.get('pitch', 0.0), e.get('roll', 0.0)) for e in sp.get('static', [])],
                         chains=[CH_(c['anchor'], c['dir'], c['n'], c['seg'], c['r0'], c['r1'], c.get('k', .2), c.get('damp', .8), c.get('grav', .1), c.get('wind', 1.0)) for c in sp.get('chains', [])])
    return out


def save_styles(d=None):
    json.dump(d if d is not None else styles_to_json(STYLES), open(STYLES_JSON, 'w'), indent=1)


def reload_styles():
    global STYLES, STYLE_ORDER
    d = json.load(open(STYLES_JSON))
    STYLES.clear(); STYLES.update(styles_from_json(d))
    STYLE_ORDER[:] = list(STYLES)


if os.path.exists(STYLES_JSON):
    reload_styles()
else:
    save_styles()
