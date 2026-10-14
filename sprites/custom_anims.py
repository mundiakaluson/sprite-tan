"""Custom animations authored in the manager tool: data/animations/<name>.json.

A file holds sparse keyframes (only the pose parameters you touched) which are interpolated (PCHIP, wrapping when loop)
into full poses for the same rig the built-in animations use. Usage:
    python custom_anims.py                 list custom animations
    python custom_anims.py NAME [--hair]   render NAME into out_uv/ (body sheet, optional hair layers) and update animations.json
"""
import json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ANIM_DIR = os.path.join(os.path.dirname(HERE), 'data', 'animations')
OUT = os.path.join(HERE, 'out_uv')
EXTRA_DEFAULT = {'R_lift': 0.0, 'L_lift': 0.0, 'cx': 0.0, 'fxm': 0.0, 'fxd': 0.0, 'fxp': 0.0}   # cx: centre on x too; fxm/fxd/fxp: speed-mist strength, heading, phase


def files():
    return sorted(f[:-5] for f in os.listdir(ANIM_DIR) if f.endswith('.json')) if os.path.isdir(ANIM_DIR) else []


def load(name):
    return json.load(open(os.path.join(ANIM_DIR, name + '.json')))


def save(a):
    os.makedirs(ANIM_DIR, exist_ok=True)
    json.dump(a, open(os.path.join(ANIM_DIR, a['name'] + '.json'), 'w'), indent=1, sort_keys=False)


def _build(A, keys, N, loop, mode):
    """Like gen_actions.build_anim but with a choice of interpolation: smooth (PCHIP), linear, step (hold until next key)."""
    if mode == 'smooth':
        return A.build_anim(keys, N, loop)
    series = {}
    for f in sorted(keys):
        for k, v in keys[f].items():
            series.setdefault(k, []).append((f, v))
    out = []
    for f in range(N):
        pose = dict(A.DEFAULT)
        for k, pts in series.items():
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if loop and len(pts) > 1:
                xs = [x - N for x in xs] + xs + [x + N for x in xs]; ys = ys * 3
            if mode == 'step':
                i = max([j for j, x in enumerate(xs) if x <= f] or [0]); pose[k] = ys[i]
            else:
                pose[k] = float(np.interp(f, xs, ys))
        out.append(pose)
    return out


def build_poses(a):
    import gen_actions as A
    keys = {int(f): dict(v) for f, v in a['keys'].items()}
    keys = {f: v for f, v in keys.items() if 0 <= f < a['frames']}
    if not keys:
        keys = {0: {}}
    poses = _build(A, keys, a['frames'], a.get('loop', False), a.get('interp', 'smooth'))
    for p in poses:
        for k, v in EXTRA_DEFAULT.items():
            if k in a.get('keyed_extra', ()) or True:
                p.setdefault(k, v)
        if a.get('ground', True):
            for s in ('R', 'L'):
                p[f'{s}_az'] = A.gz(math.degrees(p[f'{s}_fp']), p[f'{s}_fy'], p[f'{s}_fr'], p.get(f'{s}_lift', 0.0))
    return poses


def bake(poses, ground=False):
    """Turn full poses (e.g. a built-in animation) into keyframes: constant params once, varying params every frame."""
    keys = {f: {} for f in range(len(poses))}
    for k in poses[0]:
        vals = [p.get(k, 0.0) for p in poses]
        if max(vals) - min(vals) < 1e-9:
            keys[0][k] = float(vals[0])
        else:
            for f, v in enumerate(vals):
                keys[f][k] = float(v)
    return {str(f): v for f, v in keys.items() if v}


def register(ANIMS):
    """Add every custom animation to gen_uv.ANIMS (name -> (fn, ms, loop, events)) so the batch exporters pick them up."""
    for n in files():
        try:
            a = load(n)
        except Exception as e:
            print('custom animation', n, 'unreadable:', e); continue
        ANIMS[n] = ((lambda a=a: (build_poses(a), None)), a.get('ms', 70), a.get('loop', False), a.get('events', {}))


# ---------------------------------------------------------------- export
def _dir_job(args):
    import gen_uv as U, gen_hair as H
    dn, cps, chains, styles, with_hair = args
    body, hair = [], {s: [] for s in styles}
    for k, cp in enumerate(cps):
        sc, info = U.build_scene(cp, dn)
        body.append(U.finish_uv(sc))
        if with_hair:
            for s in styles:
                hair[s].append(H.hair_layer(sc, info, s, chains[s][k]))
    return dn, body, hair


def export(name, with_hair=False, progress=print, procs=2):
    import gen_uv as U
    from PIL import Image
    from multiprocessing import Pool
    a = load(name)
    poses = build_poses(a)
    cps = [U.centered(p) for p in poses]
    n = len(poses)
    styles, chains = [], {}
    if with_hair:
        import gen_hair as H
        styles = list(H.STYLE_ORDER)
        H.WIND[name] = tuple(a.get('wind', (0.0, -0.1, 0.0)))
        chains = {s: H.simulate(s, cps, a.get('loop', False), name) for s in styles}
    sheet = Image.new('RGBA', (U.CW * n, U.CH * len(U.DIRS)), (0, 0, 0, 0))
    hs = {s: Image.new('RGBA', (U.CW * n, U.CH * len(U.DIRS)), (0, 0, 0, 0)) for s in styles}
    jobs = [(dn, cps, chains, styles, with_hair) for dn in U.DIRS]
    t = time.time(); done = 0
    with Pool(procs) as pool:
        for dn, body, hair in pool.imap_unordered(_dir_job, jobs):
            r = U.DIRS.index(dn)
            for k in range(n):
                sheet.paste(Image.fromarray(body[k], 'RGBA'), (k * U.CW, r * U.CH))
                for s in styles:
                    hs[s].paste(Image.fromarray(hair[s][k], 'RGBA'), (k * U.CW, r * U.CH))
            done += 1
            progress(f'progress {done}/{len(U.DIRS)} {int(time.time() - t)}s')
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, f'{name}_uv_sheet.png'))
    if styles:
        os.makedirs(os.path.join(OUT, 'hair'), exist_ok=True)
        for s, im in hs.items():
            im.save(os.path.join(OUT, 'hair', f'{s}__{name}.png'))
    mp = os.path.join(OUT, 'animations.json')
    meta = json.load(open(mp))
    meta['animations'][name] = dict(frames=n, ms_per_frame=a.get('ms', 70), loop=a.get('loop', False), events=a.get('events', {}),
                                    root_forward_px=[round(p['root_y'] * U.SC, 2) for p in poses], root_side_px=[round(p['root_x'] * U.SC, 2) for p in poses],
                                    mist=[round(p.get('fxm', 0.0), 2) for p in poses], custom=True)
    if a.get('contact'): meta['animations'][name]['contact'] = a['contact']
    json.dump(meta, open(mp, 'w'), indent=1)
    progress('done')


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    if not args:
        print('\n'.join(files()) or '(no custom animations yet)')
    else:
        export(args[0], '--hair' in sys.argv, progress=lambda s: print(s, flush=True))
