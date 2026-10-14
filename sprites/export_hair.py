"""Exports hair-layer sheets: out_uv/hair/<style>__<anim>.png  (same cell/rows/frames as the body sheets).
    python export_hair.py                         every style x every animation (built-in and custom)
    python export_hair.py --styles H11_x H12_y    only these styles
    python export_hair.py --anims run kick        only these animations"""
import os, sys, json, time
import numpy as np
from PIL import Image
import gen_uv as U, gen_hair as H
from gen_uv import CW, CH, DIRS, centered, ANIMS
from multiprocessing import Pool

OUT = 'out_uv/hair'


def job(args):
    anim, styles = args
    fn, ms, loop, ev = ANIMS[anim]
    poses, dust = fn()
    n = len(poses)
    cps = [centered(p) for p in poses]
    chains = {st: H.simulate(st, cps, loop, anim) for st in styles}
    sheets = {st: Image.new('RGBA', (CW * n, CH * len(DIRS)), (0, 0, 0, 0)) for st in styles}
    for r, dn in enumerate(DIRS):
        for k in range(n):
            sc, info = U.build_scene(cps[k], dn)
            for st in styles:
                uv = H.hair_layer(sc, info, st, chains[st][k])
                sheets[st].paste(Image.fromarray(uv, 'RGBA'), (k * CW, r * CH))
    os.makedirs(OUT, exist_ok=True)
    for st, im in sheets.items():
        im.save(f'{OUT}/{st}__{anim}.png')
    return anim, n


def write_meta():
    p = f'{OUT}/hair_styles.json'
    meta = json.load(open(p)) if os.path.exists(p) else {'layer': 'draw each hair sheet over the matching body sheet; same cell size, rows (32 directions) and frames; use the same skin atlas (HAIR region at 48,12 16x6 holds the hair colour)', 'files': '<style>__<anim>.png'}
    meta['styles'] = {s: dict(static_parts=len(H.STYLES[s]['static']), sway_chains=len(H.STYLES[s]['chains'])) for s in H.STYLE_ORDER}
    json.dump(meta, open(p, 'w'), indent=1)


def arg_list(flag):
    if flag not in sys.argv:
        return None
    out = []
    for a in sys.argv[sys.argv.index(flag) + 1:]:
        if a.startswith('--'):
            break
        out.append(a)
    return out


if __name__ == '__main__':
    t = time.time()
    styles = arg_list('--styles') or list(H.STYLE_ORDER)
    anims = arg_list('--anims') or list(ANIMS)
    with Pool(2) as p:
        for a, n in p.imap_unordered(job, [(a, styles) for a in anims]):
            print('done', a, n, round(time.time() - t), 's', flush=True)
    write_meta()
    print('finished', flush=True)
