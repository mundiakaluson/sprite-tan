"""Goal styles (data/goals.csv) and the spring-mesh net simulation. The same maths is in godot/scripts/stadium/goal_net.gd: keep them in step.
Goal local coordinates (metres): origin = centre of the goal line on the ground, +x = outward (behind the goal, into the net), y up, z across the mouth.
Net = four panels (back, roof, two sides) of linked points. Front edge (on the posts and bar) and the ground edge are pinned; the rest swings (Verlet + springs).
    net = Net(goal_row); net.step(dt, ball=(pos, vel, radius)) -> new ball velocity, hits
"""
import os, csv
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data')
SUB = 3                     # constraint iterations per step
STEP = 1.0 / 120.0          # fixed physics step
SWAY_SCALE = 0.02           # post top moves this many metres per unit of wobble offset (bar bounces half of that)


def load():
    with open(os.path.join(DATA, 'goals.csv'), encoding='utf-8-sig') as f: return [dict(r) for r in csv.DictReader(f)]


def style(gid, rows=None):
    for r in (rows or load()):
        if r['id'] == gid: return r
    return (rows or load())[0]


def f(r, k, d=0.0):
    try: return float(r.get(k))
    except (TypeError, ValueError): return d


def check(rows):
    out = []; ids = set()
    for r in rows:
        if r['id'] in ids: out.append(('error', r['id'], 'duplicate id'))
        ids.add(r['id'])
        for k, lo, hi in (('width', 1, 12), ('height', 1, 4), ('depth', 0.3, 5), ('depth_low', 0.3, 5), ('mesh', 0.1, 1), ('post_radius', 0.02, 0.2), ('stiffness', 0.05, 1), ('damping', 0, 0.2),
                          ('gravity', 0, 20), ('drag', 0, 30), ('post_sway', 5, 400), ('post_damp', 0, 30), ('bounce', 0, 1), ('net_alpha', 0, 255)):
            if not lo <= f(r, k, -1) <= hi: out.append(('error', r['id'], f'{k} must be {lo} to {hi}'))
        for k in ('post_color', 'net_color'):
            s = r.get(k, '')
            if not (len(s) == 7 and s[0] == '#'): out.append(('error', r['id'], f'{k} must be #rrggbb'))
    return out


class Wobble:
    """a damped spring for a post or the bar: offset x, velocity v"""
    def __init__(s, k, c): s.k, s.c, s.x, s.v = k, c, 0.0, 0.0
    def step(s, dt): s.v += (-s.k * s.x - s.c * s.v) * dt; s.x += s.v * dt
    def hit(s, impulse): s.v += impulse
    @property
    def energy(s): return abs(s.x) + abs(s.v) * 0.05


class Net:
    def __init__(self, g):
        self.g = g; self.hw = f(g, 'width', 7.32) / 2; self.h = f(g, 'height', 2.44); self.dep = f(g, 'depth', 2.0); self.dep_low = f(g, 'depth_low', self.dep)
        self.mesh = max(0.1, f(g, 'mesh', 0.35)); self.stiff = f(g, 'stiffness', 0.5); self.damp = f(g, 'damping', 0.02); self.grav = f(g, 'gravity', 6.0); self.drag = f(g, 'drag', 6.0)
        self.pr = f(g, 'post_radius', 0.06); self.bounce = f(g, 'bounce', 0.55)
        self.build(); self.t = 0.0
        k, c = f(g, 'post_sway', 50), f(g, 'post_damp', 3.5)
        self.posts = dict(left=Wobble(k, c), right=Wobble(k, c), bar=Wobble(k * 1.3, c))
        self.touching = False

    def apply(self, g):
        """take new physics numbers from the row without rebuilding the mesh (geometry changes need a new Net)"""
        self.g = g; self.stiff = f(g, 'stiffness', 0.5); self.damp = f(g, 'damping', 0.02); self.grav = f(g, 'gravity', 6.0); self.drag = f(g, 'drag', 6.0); self.bounce = f(g, 'bounce', 0.55)
        k, c = f(g, 'post_sway', 50), f(g, 'post_damp', 3.5)
        for n, w in self.posts.items(): w.k, w.c = k * (1.3 if n == 'bar' else 1.0), c

    # ---- mesh
    def build(self):
        hw, h, d, dl = self.hw, self.h, self.dep, self.dep_low; pts = {}; P = []; edges = set()
        def node(p):
            key = tuple(int(round(v * 1000)) for v in p)
            if key not in pts: pts[key] = len(P); P.append(p)
            return pts[key]
        def panel(c00, c10, c11, c01):
            c00, c10, c11, c01 = map(np.array, (c00, c10, c11, c01))
            nu = max(1, int(round(np.linalg.norm(c10 - c00) / self.mesh))); nv = max(1, int(round(np.linalg.norm(c01 - c00) / self.mesh))); idx = {}
            for i in range(nu + 1):
                for j in range(nv + 1):
                    u, v = i / nu, j / nv; p = (c00 * (1 - u) + c10 * u) * (1 - v) + (c01 * (1 - u) + c11 * u) * v; idx[i, j] = node(tuple(p))
            for i in range(nu + 1):
                for j in range(nv + 1):
                    if i < nu: edges.add(tuple(sorted((idx[i, j], idx[i + 1, j]))))
                    if j < nv: edges.add(tuple(sorted((idx[i, j], idx[i, j + 1]))))
        panel((d, h, -hw), (d, h, hw), (dl, 0, hw), (dl, 0, -hw))                       # back
        panel((0, h, -hw), (0, h, hw), (d, h, hw), (d, h, -hw))                          # roof
        panel((0, 0, -hw), (0, h, -hw), (d, h, -hw), (dl, 0, -hw))                       # side (z = -hw)
        panel((0, 0, hw), (0, h, hw), (d, h, hw), (dl, 0, hw))                           # side (z = +hw)
        self.p = np.array(P, float); self.prev = self.p.copy(); self.home = self.p.copy()
        self.edges = np.array(sorted(edges), int); self.rest = np.linalg.norm(self.p[self.edges[:, 0]] - self.p[self.edges[:, 1]], axis=1)
        self.pin = (self.p[:, 0] < 1e-3) | (self.p[:, 1] < 1e-3) | ((np.abs(self.p[:, 1] - h) < 1e-3) & (np.abs(self.p[:, 0] - d) < 1e-3))   # front frame, ground, rear top bar

    def reset(self): self.p[:] = self.home; self.prev[:] = self.home; self.t = 0.0
    @property
    def energy(self): return float(np.abs(self.p - self.prev).sum() + sum(w.energy for w in self.posts.values()))

    # ---- simulation
    def step(self, dt=STEP, ball=None):
        """advance by dt. ball = (pos, vel, radius) in goal-local metres or None. Returns (ball velocity or None, [hit events])"""
        hits = []; newv = None
        vel = (self.p - self.prev) * (1.0 - self.damp)
        self.prev = self.p.copy(); self.p = self.p + vel; self.p[:, 1] -= self.grav * dt * dt * 0.5 * (~self.pin)
        if ball is not None:
            bp, bv, br = np.array(ball[0], float), np.array(ball[1], float), float(ball[2]); newv = bv.copy()
            d = self.p - bp; dist = np.linalg.norm(d, axis=1); near = (dist < br + self.mesh * 0.4) & (~self.pin)
            self.touching = bool(near.any())
            if self.touching:
                dn = d[near] / np.maximum(dist[near], 1e-6)[:, None]; self.p[near] = bp + dn * (br + self.mesh * 0.4); self.prev[near] = self.p[near] - bv * dt * 0.6
                newv = newv * float(np.exp(-self.drag * dt * min(10, int(near.sum())) / 3.0)); hits.append(('net', bp))
            # inside the goal the net is a soft wall (back, roof, sides): the ball cannot pass through it, the mesh bulges to show it
            if 0.0 < bp[0] and abs(bp[2]) < self.hw + br and bp[1] < self.h:
                A = NET_A * self.stiff; C = NET_C; dd = bp[0] + br - (self.dep_low + (self.dep - self.dep_low) * min(1.0, max(0.0, bp[1] / self.h)))
                if dd > 0: newv[0] -= A * dd * dt; newv *= (1 - min(0.9, C * dt)); hits.append(('net', bp))
                dd = abs(bp[2]) + br - self.hw; sg = 1.0 if bp[2] > 0 else -1.0
                if dd > 0: newv[2] -= sg * A * dd * dt; newv *= (1 - min(0.9, C * dt)); hits.append(('net', bp))
                dd = bp[1] + br - self.h
                if dd > 0: newv[1] -= A * dd * dt; newv *= (1 - min(0.9, C * dt)); hits.append(('net', bp))
            # posts and bar: capsules
            for name, a, b in (('left', (0, 0, -self.hw), (0, self.h, -self.hw)), ('right', (0, 0, self.hw), (0, self.h, self.hw)), ('bar', (0, self.h, -self.hw), (0, self.h, self.hw))):
                a, b = np.array(a, float), np.array(b, float); ab = b - a; t = float(np.clip(np.dot(bp - a, ab) / np.dot(ab, ab), 0, 1)); cp = a + ab * t
                dv = bp - cp; dd = float(np.linalg.norm(dv))
                if dd < br + self.pr and dd > 1e-6:
                    nn = dv / dd; vn = float(np.dot(newv, nn))
                    if vn < 0: newv = newv - (1 + self.bounce) * vn * nn; self.posts[name].hit(-vn * 0.8); hits.append((name, bp))
        for _ in range(SUB):
            a, b = self.edges[:, 0], self.edges[:, 1]; d = self.p[b] - self.p[a]; L = np.maximum(np.linalg.norm(d, axis=1), 1e-9); corr = (d * ((L - self.rest) / L)[:, None]) * self.stiff
            wa = (~self.pin[a]).astype(float)[:, None]; wb = (~self.pin[b]).astype(float)[:, None]; tot = np.maximum(wa + wb, 1e-9)
            np.add.at(self.p, a, corr * wa / tot); np.add.at(self.p, b, -corr * wb / tot)
            self.p[self.pin] = self.home[self.pin]
        for w in self.posts.values(): w.step(dt)
        self.t += dt
        return newv, hits


NET_A = 1100.0               # how hard the net wall pushes the ball back (m/s^2 per metre of penetration, times stiffness)
NET_C = 22.0                 # the net soaks up the ball's speed while it is touching (1/s)
BALL_R = 0.17                # ball radius in the game (a real ball is 0.11 m; slightly bigger reads better on screen)


def ball_flight(pos, vel, dt, g=9.81, drag=0.012):
    """plain ball physics for the simulator: gravity + air drag + a bounce on the ground"""
    pos = np.array(pos, float); vel = np.array(vel, float); vel[1] -= g * dt; vel *= (1 - drag * dt * 10); pos = pos + vel * dt
    if pos[1] < BALL_R and vel[1] < 0: pos[1] = BALL_R; vel[1] *= -0.6; vel[[0, 2]] *= 0.92
    return pos, vel


if __name__ == '__main__':
    import time
    for g in load():
        n = Net(g); t0 = time.time(); peak = 0; e = []
        for i in range(720):
            nv, h = n.step(STEP, ball=((0.1 + i * 0.18, 1.2, 0.5), (22, 0, 0), BALL_R) if i < 20 else None); peak = max(peak, n.energy)
            if i in (60, 240, 480, 719): e.append(round(n.energy, 3))
        print(g['id'], 'nodes', len(n.p), 'springs', len(n.edges), 'peak', round(peak, 2), 'energy at .5s/2s/4s/6s', e, 'ms/step', round((time.time() - t0) / 720 * 1000, 2))
