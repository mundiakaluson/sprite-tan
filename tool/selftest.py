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
sys.path.insert(0, os.path.join(tables.ROOT, 'packs'))
import packlib as PL, random, design2
data = PL.load(); pl = PL.read('players'); cd = PL.read('cards')
for pk in data['packs']:
    b = PL.bundle(pk['id'], data); res = PL.simulate(b, pl, cd, 300, 1)
    assert abs(sum(res['items'].values()) - 100) < 1e-6 and design2.foil_bag(pk).size == (64, 96)
    for _ in range(20):
        pull = PL.roll(b, pl, cd, random.Random(_)); assert len(pull) == PL.inum(pk['player_items']) + PL.inum(pk['card_items'])
        g = (pk.get('guarantee_min') or '').strip()
        if g: assert max(PL.RARS.index(x['rarity']) for x in pull) >= PL.RARS.index(g)
b = PL.bundle('legend', data); w0 = PL.weights(b['pk'], b['odds'], 0); w9 = PL.weights(b['pk'], b['odds'], 12); assert abs(sum(w9) - 100) < 1e-6 and w9[4] > w0[4]
assert PL.state(dict(active='1', start='2000-01-01', end='2000-02-01')) == 'expired' and PL.state(dict(active='0')) == 'hidden'
print('packs ok')
print('ok')
