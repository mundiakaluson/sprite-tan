"""Headless checks (no window): python tool/selftest.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprite_core as S, validate, looks, tables
import custom_anims as C, gen_actions as A

im = S.load(os.path.join(looks.OUT, 'run_uv_sheet.png')); assert S.detect_grid(im) == (40, 40)
poses = A.anim_kick()[0]
back = C.build_poses(dict(frames=len(poses), loop=False, ground=False, keys=C.bake(poses)))
assert max(abs(back[f][k] - poses[f][k]) for f in range(len(poses)) for k in poses[f]) < 1e-9
r = validate.run(); errs = [x for x in r if x[0] == 'error']
print('data checks:', len(errs), 'errors,', len(r) - len(errs), 'warnings')
p = tables.table('players').rows[2]; assert looks.render(p, 'run', 0, 3).getbbox()
import playercard
for p in tables.table('players').rows[::25]: assert playercard.card(p).size == (64, 90) and playercard.card(p, special=True, t=0.1).size == (64, 90)
assert playercard.popup(p).width > 0
print('ok')
