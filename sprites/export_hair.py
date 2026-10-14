"""Exports hair-layer sheets: out_uv/hair/<style>__<anim>.png  (same cell/rows/frames as the body sheets)."""
import os, sys, json, time
import numpy as np
from PIL import Image
import gen_uv as U, gen_hair as H
from gen_uv import CW, CH, DIRS, centered, ANIMS
from multiprocessing import Pool

OUT = 'out_uv/hair'

def job(args):
    anim, = args
    fn, ms, loop, ev = ANIMS[anim]
    poses, dust = fn()
    n = len(poses)
    cps = [centered(p) for p in poses]
    chains = {st: H.simulate(st, cps, loop, anim) for st in H.STYLE_ORDER}
    sheets = {st: Image.new('RGBA', (CW * n, CH * len(DIRS)), (0, 0, 0, 0)) for st in H.STYLE_ORDER}
    for r, dn in enumerate(DIRS):
        for k in range(n):
            sc, info = U.build_scene(cps[k], dn)
            for st in H.STYLE_ORDER:
                uv = H.hair_layer(sc, info, st, chains[st][k])
                sheets[st].paste(Image.fromarray(uv, 'RGBA'), (k * CW, r * CH))
    os.makedirs(OUT, exist_ok=True)
    for st, im in sheets.items():
        im.save(f'{OUT}/{st}__{anim}.png')
    return anim, n

if __name__ == '__main__':
    t = time.time()
    with Pool(2) as p:
        for a, n in p.imap_unordered(job, [(a,) for a in ANIMS]):
            print('done', a, n, round(time.time() - t), 's', flush=True)
