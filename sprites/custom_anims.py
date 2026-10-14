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
EXTRA_DEFAULT = {'R_lift': 0.0, 'L_lift': 0.0}


def files():
    return sorted(f[:-5] for f in os.listdir(ANIM_DIR) if f.endswith('.json')) if os.path.isdir(ANIM_DIR) else []


def load(name):
    return json.load(open(os.path.join(ANIM_DIR, name + '.json')))


def save(a):
    os.makedirs(ANIM_DIR, exist_ok=True)
    json.dump(a, open(os.path.join(ANIM_DIR, a['name'] + '.json'), 'w'), indent=1, sort_keys=False)


def build_poses(a):
    import gen_actions as A
    keys = {int(f): dict(v) for f, v in a['keys'].items()}
    keys = {f: v for f, v in keys.items() if 0 <= f < a['frames']}
    if not keys:
        keys = {0: {}}
    poses = A.build_anim(keys, a['frames'], a.get('loop', False))
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
                                    root_forward_px=[round(p['root_y'] * U.SC, 2) for p in poses], custom=True)
    json.dump(meta, open(mp, 'w'), indent=1)
    progress('done')


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    if not args:
        print('\n'.join(files()) or '(no custom animations yet)')
    else:
        export(args[0], '--hair' in sys.argv, progress=lambda s: print(s, flush=True))
