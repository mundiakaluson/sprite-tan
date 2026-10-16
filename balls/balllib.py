"""Ball studio library: ball rows (data/balls.csv), flight physics, pixel-art texture sheets. Physics is mirrored in godot/scripts/ball/ball_physics.gd: keep the two in step.
Ball textures: an equirectangular panel map per ball (<id>_map.png) written by the export step. The game draws the 14 px ball with a shader (shaders/ball.gdshader) that wraps the map round
a sphere and turns it with the ball's real spin, so a trivela spins about a tilted axis, a knuckle ball barely turns, a rolling ball rolls. render_orient() here does the same for the tool.
Kick styles (data/kick_styles.csv) give the spin: roll = about the travel axis, side = about the vertical axis, back = about the horizontal axis across the travel (backspin).
World: x along the pitch, y up, z across. Metres, seconds. spin = angular velocity vector (rad/s): +z = backspin when moving along +x, +y = side spin.
    python balls/balllib.py [out_dir]   writes sheets + a contact sheet"""
import os, sys, csv, math, json
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data')
STEP = 1.0 / 120.0
SPIN_LO = 15.0                  # below this spin rate (rad/s) a fast ball can knuckle
KNU_W2 = 48.0                   # knuckle (metres of wobble) -> sideways acceleration: wobble runs at about 1 to 2 Hz, a = x * (2 pi f)^2
FRAMES, CELL, DIAM = 16, 16, 14
MAP_W, MAP_H = 512, 256
PATTERNS = ['classic', 'voronoi8', 'stripes', 'rings', 'plain']


def load():
    with open(os.path.join(DATA, 'balls.csv'), encoding='utf-8-sig') as f: return [dict(r) for r in csv.DictReader(f)]
def num(r, k, d=0.0):
    try: return float(r.get(k))
    except (TypeError, ValueError): return d
def hexrgb(h): h = h.strip().lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def load_kicks():
    with open(os.path.join(DATA, 'kick_styles.csv'), encoding='utf-8-sig') as f: return [dict(r) for r in csv.DictReader(f)]


def check_kicks(rows):
    out = []; ids = set()
    for r in rows:
        i = r['id']
        if i in ids: out.append(('error', i, 'duplicate id'))
        ids.add(i)
        for k, lo, hi in (('speed', 3, 50), ('elev', 0, 60), ('azim', -30, 30), ('side', -100, 100), ('back', -100, 100), ('roll', -100, 100), ('power', 0.3, 1.5), ('error', 0, 15)):
            if not lo <= num(r, k, -1e9) <= hi: out.append(('error', i, f'{k} must be {lo} to {hi}'))
    return out


def spin_vector(roll, side, back, azim_deg=0.0):
    """world spin from the kick's roll / side / back numbers for a ball travelling along azim (0 = +x): ex = travel, ey = up, ez = ex x ey"""
    a = math.radians(azim_deg); ex = np.array([math.cos(a), 0.0, math.sin(a)]); ey = np.array([0.0, 1.0, 0.0]); ez = np.cross(ex, ey)
    return ex * roll + ey * side + ez * back


def rot_axis(w, dt):
    """rotation matrix for angular velocity w (rad/s) over dt seconds (Rodrigues)"""
    ang = float(np.linalg.norm(w)) * dt
    if ang < 1e-9: return np.eye(3)
    k = np.asarray(w, float) / np.linalg.norm(w); K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


CHASE_VIEW = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])      # world -> view for a camera behind the ball looking along +x


def style(bid, rows=None):
    rows = rows or load()
    for r in rows:
        if r['id'] == bid: return r
    return rows[0]


def check(rows):
    out = []; ids = set()
    for r in rows:
        i = r['id']
        if i in ids: out.append(('error', i, 'duplicate id'))
        ids.add(i)
        for k, lo, hi in (('mass', 0.1, 2), ('radius', 0.05, 0.4), ('gravity', 0.5, 25), ('air_drag', 0, 0.1), ('magnus', 0, 0.03), ('knuckle', 0, 2), ('knuckle_speed', 3, 40), ('crisis', 0, 3), ('crisis_speed', 3, 40),
                          ('restitution', 0, 1), ('friction', 0, 2), ('roll_drag', 0, 3), ('spin_decay', 0, 3), ('spin_drag', 0, 3), ('touch', 0.3, 2), ('power', 0.3, 2), ('shine', 0, 1)):
            v = num(r, k, -1e9)
            if not lo <= v <= hi: out.append(('error', i, f'{k} must be {lo} to {hi}'))
        if r.get('pattern') not in PATTERNS: out.append(('error', i, 'pattern must be ' + '/'.join(PATTERNS)))
        for k in ('color_a', 'color_b', 'color_c'):
            s = r.get(k, '')
            if not (len(s) == 7 and s[0] == '#'): out.append(('error', i, f'{k} must be #rrggbb'))
    return out


# ------------------------------------------------------------------------------------------------ physics
def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))) if a != b else (1.0 if x >= b else 0.0)
    return t * t * (3 - 2 * t)


def phase(seed, k): return ((math.sin(seed * 12.9898 + k * 78.233) * 43758.5453) % 1.0) * math.tau


class Ball:
    """flight + bounce + roll. Call step(dt). pos/vel/spin are numpy 3-vectors."""
    def __init__(self, row, seed=1.0):
        self.r = row; self.seed = seed; self.pos = np.array([0.0, num(row, 'radius', 0.17), 0.0]); self.vel = np.zeros(3); self.spin = np.zeros(3); self.t = 0.0
        self.g = num(row, 'gravity', 9.81); self.rad = num(row, 'radius', 0.17); self.drag = num(row, 'air_drag', 0.012); self.mag = num(row, 'magnus', 0.0058); self.knu = num(row, 'knuckle', 0)
        self.knu_v = num(row, 'knuckle_speed', 18); self.crisis = num(row, 'crisis', 0); self.crisis_v = num(row, 'crisis_speed', 14); self.e = num(row, 'restitution', 0.75)
        self.mu = num(row, 'friction', 0.6); self.roll = num(row, 'roll_drag', 0.25); self.sdec = num(row, 'spin_decay', 0.15); self.spin_drag = num(row, 'spin_drag', 0.0)

    def accel(self):
        v = self.vel; sp = float(np.linalg.norm(v)); a = np.array([0.0, -self.g, 0.0])
        k = self.drag * (1 + self.crisis * smooth(self.crisis_v + 2.5, self.crisis_v - 2.5, sp)) if self.crisis > 0 else self.drag      # drag jumps up below the critical speed
        k *= 1 + self.spin_drag * min(1.0, abs(self.spin[1]) / 40.0)                                                                       # side spin costs speed: a curler slows as it bends
        a -= k * sp * v
        a += self.mag * np.cross(self.spin, v)                                                                                          # Magnus: spin curves the ball
        if self.knu > 0 and sp > 1.0:                                                                                                    # knuckle: fast, nearly spin-free ball wobbles sideways
            amp = self.knu * smooth(self.knu_v * 0.6, self.knu_v, sp) * (1 - smooth(SPIN_LO * 0.5, SPIN_LO, float(np.linalg.norm(self.spin))))
            if amp > 0:
                u = np.cross(v, [0, 1, 0]); un = np.linalg.norm(u)
                if un > 1e-6:
                    u /= un; w = np.cross(u, v); w /= max(np.linalg.norm(w), 1e-6); t = self.t
                    n1 = (math.sin(math.tau * 1.1 * t + phase(self.seed, 1)) + 0.6 * math.sin(math.tau * 2.3 * t + phase(self.seed, 2))) / 1.6
                    n2 = (math.sin(math.tau * 0.9 * t + phase(self.seed, 3)) + 0.6 * math.sin(math.tau * 2.0 * t + phase(self.seed, 4))) / 1.6
                    a += amp * KNU_W2 * (n1 * u + 0.6 * n2 * w)
        return a

    def contact(self, normal_impulse):
        rv = np.array([0.0, -self.rad, 0.0]); vc = self.vel + np.cross(self.spin, rv); vct = np.array([vc[0], 0.0, vc[2]]); mag = float(np.linalg.norm(vct))
        if mag > 1e-6:
            J = min(self.mu * normal_impulse, mag / 2.5); dv = -vct / mag * J                                                         # hollow ball: tangential slip dies at 1/(1+1/1.5)
            self.vel += dv; self.spin += np.cross(rv, dv) * 1.5 / (self.rad ** 2)

    def step(self, dt=STEP):
        self.vel += self.accel() * dt; self.pos += self.vel * dt; self.spin *= math.exp(-self.sdec * dt); self.t += dt; bounced = 0.0
        if self.pos[1] <= self.rad:
            self.pos[1] = self.rad
            if self.vel[1] < -0.8:
                vin = -self.vel[1]; self.vel[1] = vin * self.e; self.contact(vin * (1 + self.e)); bounced = vin
            else:
                self.vel[1] = 0.0; self.contact(self.g * dt); k = math.exp(-self.roll * dt); self.vel[0] *= k; self.vel[2] *= k
        return bounced


def launch(row, speed, elev_deg=15.0, azim_deg=0.0, side_spin=0.0, back_spin=0.0, seed=1.0, h=0.3, roll_spin=0.0):
    b = Ball(row, seed); e, a = math.radians(elev_deg), math.radians(azim_deg)
    b.pos = np.array([0.0, max(h, b.rad), 0.0]); b.vel = np.array([math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a)]) * speed * num(row, 'power', 1.0)
    b.spin = spin_vector(roll_spin, side_spin, back_spin, azim_deg); return b


def trajectory(row, speed, elev_deg=15, azim_deg=0, side_spin=0, back_spin=0, seed=1.0, t_max=3.5, roll_spin=0.0):
    b = launch(row, speed, elev_deg, azim_deg, side_spin, back_spin, seed, roll_spin=roll_spin); pts = [b.pos.copy()]; n = int(t_max / STEP)
    for i in range(n):
        b.step()
        if i % 2 == 0: pts.append(b.pos.copy())
    return np.array(pts)


# ------------------------------------------------------------------------------------------------ textures
def _centres(kind):
    phi = (1 + 5 ** 0.5) / 2; ico = []
    for s1 in (-1, 1):
        for s2 in (-1, 1): ico += [(0, s1, s2 * phi), (s1, s2 * phi, 0), (s2 * phi, 0, s1)]
    dod = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for s1 in (-1, 1):
        for s2 in (-1, 1): dod += [(0, s1 / phi, s2 * phi), (s1 / phi, s2 * phi, 0), (s2 * phi, 0, s1 / phi)]
    if kind == 'classic': return np.array([np.array(c) / np.linalg.norm(c) for c in ico + dod]), 12
    return np.array([np.array(c) / np.linalg.norm(c) for c in [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]]), 0


def panel_colour(n, row):
    """colour of the ball surface at unit vectors n (Nx3, in the ball's own frame) -> Nx3 floats"""
    a, b, c = (np.array(hexrgb(row[k]), float) for k in ('color_a', 'color_b', 'color_c')); pat = row.get('pattern', 'classic'); out = np.tile(a, (len(n), 1)); seam = np.zeros(len(n), bool)
    if pat in ('classic', 'voronoi8'):
        C, npent = _centres(pat); d = n @ C.T; o = np.argsort(-d, axis=1); i1, i2 = o[:, 0], o[:, 1]; gap = d[np.arange(len(n)), i1] - d[np.arange(len(n)), i2]; seam = gap < (0.03 if pat == 'classic' else 0.055)
        if pat == 'classic': out[i1 < npent] = b
        else: par = np.array([(C[i] > 0).sum() % 2 for i in range(len(C))]); out[par[i1] == 1] = b
    elif pat == 'stripes':
        lon = np.arctan2(n[:, 2], n[:, 0]); k = np.floor((lon + math.pi) / math.tau * 8).astype(int); out[k % 2 == 1] = b; f = ((lon + math.pi) / math.tau * 8) % 1.0; seam = (f < 0.06) | (f > 0.94)
    elif pat == 'rings':
        k = np.floor((n[:, 1] + 1) / 2 * 6).astype(int); out[k % 2 == 1] = b; f = ((n[:, 1] + 1) / 2 * 6) % 1.0; seam = (f < 0.05) | (f > 0.95)
    else:
        out[np.abs(n[:, 1]) < 0.12] = b; seam = (np.abs(np.abs(n[:, 0]) - 0.0) < 0.05) | (np.abs(n[:, 2]) < 0.05)
    out[seam] = c
    return out


def render_map(row):
    """the equirectangular panel map the game wraps round the ball (u = longitude, v = latitude, v = 0 at the top pole)"""
    yy, xx = np.mgrid[0:MAP_H, 0:MAP_W]; lon = ((xx + 0.5) / MAP_W - 0.5) * math.tau; lat = (0.5 - (yy + 0.5) / MAP_H) * math.pi
    n = np.stack([np.cos(lat) * np.cos(lon), np.sin(lat), np.cos(lat) * np.sin(lon)], -1).reshape(-1, 3)
    return Image.fromarray(panel_colour(n, row).reshape(MAP_H, MAP_W, 3).astype(np.uint8), 'RGB')


def render_orient(row, M=None, map_img=None):
    """the 16x16 ball sprite for an orientation M (3x3, ball-local -> view space: x right, y up, z towards the viewer). Mirrors shaders/ball.gdshader."""
    M = np.eye(3) if M is None else M; mp = np.asarray(map_img or render_map(row)); mh, mw = mp.shape[:2]
    yy, xx = np.mgrid[0:CELL, 0:CELL]; R = DIAM / 2
    nx = (xx + 0.5 - CELL / 2) / R; ny = -(yy + 0.5 - CELL / 2) / R; r2 = nx ** 2 + ny ** 2; inside = r2 <= 1.0; nz = np.sqrt(np.clip(1 - r2, 0, 1))
    n = np.stack([nx, ny, nz], -1)[inside]; nl = n @ M                                                                  # = M.T @ n for each row
    lon = np.arctan2(nl[:, 2], nl[:, 0]); lat = np.arcsin(np.clip(nl[:, 1], -1, 1))
    mx = np.clip(((lon / math.tau + 0.5) * mw).astype(int), 0, mw - 1); my = np.clip(((0.5 - lat / math.pi) * mh).astype(int), 0, mh - 1); col = mp[my, mx].astype(float)
    L = np.array([-0.45, 0.6, 0.66]); L /= np.linalg.norm(L); lam = np.clip(n @ L, 0, 1); band = np.digitize(lam, [0.18, 0.5, 0.8]); col = np.clip(col * np.array([0.74, 0.88, 1.0, 1.08])[band][:, None], 0, 255)
    if num(row, 'shine') > 0.5: col[lam > 0.93] = (255, 255, 255)
    img = np.zeros((CELL, CELL, 4), np.uint8); rgb = np.zeros((CELL, CELL, 3), np.uint8); rgb[inside] = col.astype(np.uint8); img[..., :3] = rgb; img[..., 3] = np.where(inside, 255, 0)
    edge = inside & (r2 > (1 - 2.0 / R) ** 2); img[edge, :3] = (img[edge, :3] * 0.62).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


def render_frame(row, angle):
    """one frame of the ball rolled about the horizontal axis by `angle` radians (for contact sheets)"""
    c, s_ = math.cos(angle), math.sin(angle); return render_orient(row, np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]]))


def render_sheet(row):
    sheet = Image.new('RGBA', (CELL * FRAMES, CELL), (0, 0, 0, 0))
    for i in range(FRAMES): sheet.paste(render_frame(row, math.tau * i / FRAMES), (i * CELL, 0))
    return sheet


def render_all(out_dir, log=print, tick=None):
    rows = load(); os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):                                       # drop old flipbook sheets
        if f.endswith('.png') and not f.endswith('_map.png') and f != 'sheet.png': os.remove(os.path.join(out_dir, f))
    for i, r in enumerate(rows):
        render_map(r).save(os.path.join(out_dir, r['id'] + '_map.png')); log(f"  {r['id']} {r['name']}: panel map")
        if tick: tick(i + 1, len(rows))
    return len(rows)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'export', 'balls'); n = render_all(out); rows = load()
    sheet = Image.new('RGBA', (CELL * FRAMES * 4, CELL * 4 * len(rows)), (60, 110, 70, 255))
    for j, r in enumerate(rows): sheet.alpha_composite(render_sheet(r).resize((CELL * FRAMES * 4, CELL * 4), Image.NEAREST), (0, j * CELL * 4))
    sheet.save(os.path.join(out, 'sheet.png')); print('wrote', n, 'balls to', out)
    for r in rows:
        for kk in load_kicks():
            nm = kk['name']; p = trajectory(r, num(kk, 'speed'), num(kk, 'elev'), num(kk, 'azim'), num(kk, 'side'), num(kk, 'back'), roll_spin=num(kk, 'roll')); print(r['id'], nm, 'range', round(float(p[-1, 0]), 1), 'lateral at 25m', round(float(np.interp(25, p[:, 0], p[:, 2])), 2), 'peak', round(float(p[:, 1].max()), 2))
