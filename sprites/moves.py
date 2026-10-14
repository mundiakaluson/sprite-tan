"""Code-authored moves. A Move is a set of sparse keyframes on the same rig as the built-in animations (see gen_actions.py), written out as
data/animations/<name>.json so the tool, the Cards tab preview and the exporter all treat it like any other animation.

    import moves; m = moves.strike(bs=0.4); m.save('shot_x', 'Label')

Conventions: x lateral (right foot +), y forward (the way the ball is struck), z up. Angles in radians except foot pitch/yaw/roll helpers, which take degrees
where noted. Frame 12 is the contact frame for foot strikes; the run-in is frames 0-7."""
import copy, json, math, os
import gen_actions as A
from gen_actions import foot, footg, arm, pole, run_pose, BASE, gz

HERE = os.path.dirname(os.path.abspath(__file__))
ANIM_DIR = os.path.join(os.path.dirname(HERE), 'data', 'animations')
D = math.radians


class Move:
    def __init__(self, keys, N, ms=70, events=None):
        self.keys = copy.deepcopy(keys); self.N = N; self.ms = ms; self.events = dict(events or {'strike': 12}); self.loop = False

    def k(self, f, **kw):
        self.keys.setdefault(f, {}).update(kw); return self

    def foot(self, f, side, x, y, fp=0.0, fy=0.0, fr=0.0, z=None, c=0.0):
        """z=None puts the foot on the turf (fp in degrees); give z to hold it in the air."""
        self.keys.setdefault(f, {}).update(footg(side, x, y, fp, fy, fr, c) if z is None else foot(side, x, y, z, fp, fy, fr)); return self

    def arms(self, f, side, s1, a1, s2, a2):
        self.keys.setdefault(f, {}).update(arm(side, s1, a1, s2, a2)); return self

    def knee(self, f, side, x, y, z):
        self.keys.setdefault(f, {}).update(pole(side, x, y, z)); return self

    def ball(self, f0, path, spin_x=2.2, spin_z=0.0, spin_y=0.0):
        """path: positions for frames f0, f0+1, ... (x, y, z). Ball is visible from f0 on."""
        for i, (x, y, z) in enumerate(path):
            if f0 + i < self.N: self.keys.setdefault(f0 + i, {}).update(dict(bx=x, by=y, bz=z, brx=spin_x * i, brz=spin_z * i, bvis=1.0))
        return self

    def hide_ball_until(self, f):
        for g in range(0, f): self.keys.setdefault(g, {})['bvis'] = 0.0
        return self

    def poses(self):
        return A.build_anim({f: v for f, v in self.keys.items() if 0 <= f < self.N}, self.N)

    def save(self, name, label=None, desc=''):
        os.makedirs(ANIM_DIR, exist_ok=True)
        keys = {str(f): {k: (round(v, 5) if isinstance(v, float) else v) for k, v in sorted(self.keys[f].items())} for f in sorted(self.keys) if 0 <= f < self.N and self.keys[f]}
        a = dict(name=name, label=label or name, frames=self.N, ms=self.ms, loop=self.loop, ground=False, events=self.events, keys=keys, wind=[0, -0.1, 0], interp='smooth', note=desc)
        json.dump(a, open(os.path.join(ANIM_DIR, name + '.json'), 'w'), indent=1)
        return a


def kick_base():
    keys, N = A.kick_keys(); return Move(keys, N)


def finesse_base():
    keys, N = A.finesse_keys(); return Move(keys, N, 70, {'strike': 12})


def run_in(m, frames=8, y0=-19.8, step=2.3, ball=(1.2, 11.5, 3.0)):
    """(re)write the run-up, frames 0..frames-1, ending at the toe-off pose"""
    for f in range(frames):
        ry = y0 + step * f
        m.keys[f] = run_pose(BASE, (f - 6) / 12.0, ry)
        m.keys[f].update(dict(bx=ball[0], by=ball[1], bz=ball[2], bvis=1.0))
    return m


def path(n, speed=8.0, rise=0.0, curve=0.0, dip=0.0, start=(1.5, 18.5, 4.2), wob=0.0, lift0=0.0):
    """ball positions after contact: forward speed per frame, rise/frame (z), sideways curve per frame, late dip, wobble amplitude"""
    out = []; x, y, z = start; vz = rise
    for i in range(n):
        x += curve * (0.4 + 0.12 * i) + (wob * math.sin(i * 1.7) if wob else 0.0)
        y += speed; z = max(1.5, z + vz); vz -= dip * 0.12
        if lift0 and i < 2: z += lift0
        out.append((x, y, z))
    return out


def stand(f=0, ry=0.0, pz=24.6):
    """a relaxed standing pose (feet on the turf, shoulder-width) for moves that start from rest"""
    d = dict(root_x=0.0, root_y=ry, pz=pz, pyaw=0.0, ppitch=0.05, proll=0.0, cpitch=0.08, cyaw=0.0, croll=0.0, hyaw=0.0, hpitch=0.25, hroll=0.0)
    d.update(footg('R', 2.2, ry + 0.0, 0)); d.update(footg('L', -2.2, ry + 0.4, 0))
    d.update(arm('R', 0.1, 0.25, 0.4, 0.1)); d.update(arm('L', 0.1, 0.25, 0.4, 0.1))
    return d


def blank(N, ms=70, ball=(1.2, 11.5, 3.0), events=None):
    m = Move({}, N, ms, events or {'strike': 12})
    for f in range(N): m.keys[f] = {}
    m.keys[0] = stand(); m.keys[0].update(dict(bx=ball[0], by=ball[1], bz=ball[2], bvis=1.0)); return m
