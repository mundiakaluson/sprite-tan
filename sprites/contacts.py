"""Writes the ball contact point of every shot / pass / air-pass animation: where the boot (or head) meets the ball at the strike frame, relative to the player's root, in the
player's own frame (x right, y forward, z up). The game is the owner of the ball: it plays the animation so that this point lands on the ball (moving the player a little) and
launches the ball itself on the strike frame. Stored as `contact` in data/animations/<name>.json and out_uv/animations.json.   python contacts.py"""
import json, os
import numpy as np
import moves as M
import custom_anims as C


def contact(name):
    a = C.load(name); ps = C.build_poses(a); f = a['events'].get('strike')
    if f is None: return None
    p = ps[f]; b = np.array([p['bx'], p['by'], p['bz']]); root = np.array([p['root_x'], p['root_y'], 0.0])
    cands = {'boot_R': M.boot_pos(p, 'R'), 'boot_L': M.boot_pos(p, 'L'), 'head': M.head_pos(p)[0]}
    kind = min(cands, key=lambda k: np.linalg.norm(cands[k] - b))
    if np.linalg.norm(cands[kind] - b) > 6.0: return None          # the ball is not struck in this move (feints)
    v = b - root
    return dict(frame=int(f), part=kind, x=round(float(v[0]), 2), y=round(float(v[1]), 2), z=round(float(v[2]), 2))


if __name__ == '__main__':
    mp = os.path.join(C.OUT, 'animations.json'); meta = json.load(open(mp)); n = 0
    for name in C.files():
        if not name.startswith(('sh', 'ps', 'air_pass', 'df', 'gk', 'tt')): continue
        c = contact(name); a = C.load(name)
        if c: a['contact'] = c; n += 1
        else: a.pop('contact', None)
        C.save(a)
        if name in meta['animations']:
            if c: meta['animations'][name]['contact'] = c
            else: meta['animations'][name].pop('contact', None)
    json.dump(meta, open(mp, 'w'), indent=1); print('contacts written for', n, 'animations')
