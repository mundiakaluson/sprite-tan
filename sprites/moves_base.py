"""Base locomotion animations (looping, in place; the game moves the root and scales the playback rate to the speed).
Run:  python moves_base.py [name ...]  -> data/animations/base_*.json (+ data/gaits.csv); then bake with  python custom_anims.py base_walk  etc.
Gaits reuse the run cycle generator (gen_actions.run_pose) with different parameters; idle is a hand-keyed breathing stance."""
import csv, math, os, sys
import gen_actions as A
import moves as M
from moves_dribble import Dr
from moves_defend import hidden

RU = 0.45                      # sprite px per rig unit
GAITS = {}


def gait(name, label, N, ms, **P):
    p = dict(A.BASE); p.update(P); GAITS[name] = (label, N, ms, p)


#            frames/ms    ground fraction  stride (yc, yo)  foot lift   body dip / flight     lean / head       arms                 sway
gait('walk',       'Walk',       16, 70, stance=0.62, yc=3.4, yo=-4.6, lift=4.5, dip=0.9, flight=0.0, lean=0.04, head_pitch=0.0, arm=0.34, elbow=0.55, twist=0.14, sway=0.35)
gait('jog',        'Jog',        12, 66, stance=0.46, yc=4.6, yo=-7.8, lift=8.0, dip=1.7, flight=0.5, lean=0.10, head_pitch=0.0, arm=0.58, elbow=1.25, twist=0.18, sway=0.40)
gait('tired_run',  'Tired Run',  14, 82, stance=0.47, yc=3.6, yo=-6.6, lift=5.6, dip=2.9, flight=0.2, lean=0.30, head_pitch=0.34, arm=0.46, elbow=0.95, twist=0.10, sway=0.85)
gait('sprint',     'Sprint',     10, 52, stance=0.34, yc=6.4, yo=-11.8, lift=14.5, dip=2.7, flight=1.9, lean=0.34, head_pitch=-0.05, arm=1.12, elbow=1.75, twist=0.28, sway=0.45)


def gait_move(name):
    label, N, ms, P = GAITS[name]
    m = M.Move({}, N, ms, {}); m.loop = True
    for f in range(N):
        m.keys[f] = A.run_pose(P, f / N, 0.0); m.keys[f]['bvis'] = 0.0
    return m


def idle():
    N = 24; d = Dr(N, ms=100, speed=0.0); d.m.loop = True; d.m.events = {}
    for f in range(N):
        ph = 2 * math.pi * f / N
        d.at(f, R=(2.7, 0.5, 0, None), L=(-2.7, -0.5, 0, None), pz=22.75 + 0.11 * math.sin(ph) , cpitch=0.04 + 0.025 * math.sin(ph), ppitch=0.02, hpitch=0.05 - 0.02 * math.sin(ph),
             croll=0.025 * math.sin(ph * 0.5), proll=-0.012 * math.sin(ph * 0.5), hyaw=0.18 * math.sin(ph * 0.5 + 0.8), cyaw=0.03 * math.sin(ph * 0.5))
        d.arms(f, (0.10 + 0.03 * math.sin(ph), 0.2, 0.45, -0.08), (0.10 - 0.03 * math.sin(ph), 0.2, 0.45, -0.08))
    hidden(d)
    return d.m


MOVES = {'base_idle': ('Idle', idle)}
for n in GAITS: MOVES['base_' + n] = (GAITS[n][0], (lambda n=n: gait_move(n)))


def gaits_csv():
    """data/gaits.csv: for each gait the playback numbers the game needs: ground speed at the authored rate (px/s) = foot travel in stance / stance time"""
    rows = []
    for n, (label, N, ms, P) in GAITS.items():
        T = N * ms / 1000.0; stride = (P['yc'] - P['yo']) * RU
        rows.append(dict(id='base_' + n, name=label, frames=N, ms_per_frame=ms, cycle_s=round(T, 3), ground_speed_px_s=round((P['yc'] - P['yo']) / (P['stance'] * T) * RU, 1),
                         min_rate=0.6, max_rate=1.5, note='both-feet cycle; the game plays at rate = actual speed / ground_speed_px_s (clamped) to avoid foot slide'))
    with open(os.path.join(os.path.dirname(A.__file__), '..', 'data', 'gaits.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)


def build(ids=None):
    import moves_reactions as R
    out = []
    for name, (label, fn) in MOVES.items():
        if ids and name not in ids: continue
        fn().save(name, label, 'base locomotion, sprites/moves_base.py'); out.append(name)
    for name, (label, fn, loop) in R.MOVES.items():
        if ids and name not in ids: continue
        m = fn(); m.loop = loop; m.save(name, label, 'base reaction, sprites/moves_reactions.py'); out.append(name)
    import moves_fluid as FL
    for name, (label, fn, loop) in FL.MOVES.items():
        if ids and name not in ids: continue
        m = fn(); m.loop = loop; m.save(name, label, 'smoother clips, sprites/moves_fluid.py'); out.append(name)
    import moves_turns as T
    for name, (label, fn, loop) in T.MOVES.items():
        if ids and name not in ids: continue
        m = fn(); m.loop = loop; m.save(name, label, 'turn with the ball, sprites/moves_turns.py'); out.append(name)
    gaits_csv(); return out


if __name__ == '__main__':
    for n in build(sys.argv[1:] or None): print(n)
