"""EXPORT TO GAME: copy / render everything the Godot project needs into godot/ in one go.
    python tool/export_game.py                 all steps
    python tool/export_game.py data packs      only these steps (names below)
The manager tool's big EXPORT button calls run() on a worker thread. Pure PIL / numpy, no Tk windows are opened here.

What lands where (godot/ is the Godot 4 project; assets/ and data/ are generated and git-ignored, shaders/ is tracked):
  data/             every data/*.csv and *.json (not progress), looks_index.csv, players_cards_index.csv, export_manifest.json
  assets/sprites/   *_uv_sheet.png (12-ish frames across, 32 directions down, 40x40 cells), animations.json, skin_*.png
  assets/hair/      hair layer sheets
  assets/looks/     one 96x24 skin atlas per player (the shader recolours the sprite with it)
  assets/cards/     skill card faces (64x90) and tooltips
  assets/players/   player card faces, tooltips and shimmer strips for the special (foil) players
  assets/packs/     pack wrappers drawn from data/packs.csv and the card backs per tier
  shaders/          uv_skin.gdshader"""
import os, sys, json, shutil, time, csv, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GODOT = os.path.join(ROOT, 'godot')
for p in ('tool', 'cards', 'sprites', 'packs', 'titan'):
    sys.path.insert(0, os.path.join(ROOT, p))

UV = os.path.join(ROOT, 'sprites', 'out_uv')
DATA = os.path.join(ROOT, 'data')
SKIP_DATA = ('progress.csv', 'progress.csv.bak', 'players_invented_names.csv')


class Ctx:
    def __init__(s, log, tick, out):
        s.log = log; s.tick = tick; s.out = out; s.counts = {}

    def path(s, *p):
        d = os.path.join(s.out, *p); os.makedirs(os.path.dirname(d) if os.path.splitext(d)[1] else d, exist_ok=True); return d


def _copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)


def _tables():
    import tables
    return tables


# ------------------------------------------------------------------------------------------------ steps
def step_data(c):
    n = 0
    for f in sorted(os.listdir(DATA)):
        full = os.path.join(DATA, f)
        if not os.path.isfile(full) or f in SKIP_DATA or f.endswith('.bak'): continue
        if f.endswith('.csv') or f.endswith('.json'): _copy(full, c.path('data', f)); n += 1
    c.counts['data files'] = n; c.log(f'copied {n} data files')


def step_sprites(c):
    sheets = [f for f in sorted(os.listdir(UV)) if f.endswith('_uv_sheet.png')]; skins = [f for f in sorted(os.listdir(UV)) if f.startswith('skin_') and 'template' not in f]
    for i, f in enumerate(sheets + skins):
        _copy(os.path.join(UV, f), c.path('assets', 'sprites', f)); c.tick(i + 1, len(sheets) + len(skins))
    _copy(os.path.join(UV, 'animations.json'), c.path('assets', 'sprites', 'animations.json'))
    _copy(os.path.join(UV, 'uv_skin.gdshader'), c.path('shaders', 'uv_skin.gdshader'))
    c.counts['sprite sheets'] = len(sheets); c.counts['skin atlases'] = len(skins); c.log(f'copied {len(sheets)} sprite sheets, {len(skins)} skin atlases, animations.json and the shader')


def step_hair(c):
    d = os.path.join(UV, 'hair'); fs = [f for f in sorted(os.listdir(d)) if f.endswith('.png')] if os.path.isdir(d) else []
    for i, f in enumerate(fs): _copy(os.path.join(d, f), c.path('assets', 'hair', f)); c.tick(i + 1, len(fs))
    c.counts['hair sheets'] = len(fs); c.log(f'copied {len(fs)} hair layer sheets')


def step_looks(c):
    import looks
    from PIL import Image
    T = _tables(); rows = T.table('players').rows; lines = ['id,hair_style,atlas,kit_slot']
    for i, r in enumerate(rows):
        Image.fromarray(looks.player_skin(r)).save(c.path('assets', 'looks', f"{r['id']}.png"))
        lines.append(f"{r['id']},{r['hair_style']},looks/{r['id']}.png,{'keeper' if r['role'] == 'GK' else 'outfield'}"); c.tick(i + 1, len(rows))
    open(c.path('data', 'looks_index.csv'), 'w', newline='').write('\n'.join(lines) + '\n')
    c.counts['player looks'] = len(rows); c.log(f'wrote {len(rows)} player look atlases')


def step_cards(c):
    from tab_cards import card_face, tooltip
    T = _tables(); rows = T.table('cards').rows
    for i, r in enumerate(rows):
        card_face(r, 'ready', 0, 1).save(c.path('assets', 'cards', f"{r['id']}.png")); tooltip(r, 1).save(c.path('assets', 'cards', f"{r['id']}_tip.png")); c.tick(i + 1, len(rows))
    c.counts['skill cards'] = len(rows); c.log(f'drew {len(rows)} skill card faces and tooltips')


def step_players(c):
    import playercard
    from PIL import Image
    T = _tables(); rows = T.table('players').rows; N = 36; idx = ['id,face,tooltip,special,shimmer_strip,shimmer_frames']; sp = 0
    for i, r in enumerate(rows):
        pid = r['id']; special = str(r.get('special', '0')) == '1'
        playercard.card(r, special=None).save(c.path('assets', 'players', f'{pid}.png')); playercard.popup(r).save(c.path('assets', 'players', f'{pid}_tip.png')); strip = ''
        if special:
            fr = [playercard.card(r, t=k / N) for k in range(N)]; sh = Image.new('RGBA', (64 * N, 90)); [sh.paste(f, (64 * k, 0)) for k, f in enumerate(fr)]
            sh.save(c.path('assets', 'players', f'{pid}_shimmer.png')); strip = f'players/{pid}_shimmer.png'; sp += 1
        idx.append(f"{pid},players/{pid}.png,players/{pid}_tip.png,{1 if special else 0},{strip},{N if special else 0}"); c.tick(i + 1, len(rows))
    open(c.path('data', 'players_cards_index.csv'), 'w', newline='').write('\n'.join(idx) + '\n')
    c.counts['player cards'] = len(rows); c.counts['shimmer strips'] = sp; c.log(f'drew {len(rows)} player cards ({sp} with a {N}-frame shimmer strip)')


def step_packs(c):
    import packlib as PL, design2 as D, opening as O
    data = PL.load(); packs = data['packs']
    for i, pk in enumerate(packs): D.foil_bag(pk).save(c.path('assets', 'packs', f"{pk['id']}.png")); c.tick(i + 1, len(packs) + 5)
    for j, r in enumerate(PL.RARS): O.card_back(r).save(c.path('assets', 'packs', f'back_{r.lower()}.png')); c.tick(len(packs) + j + 1, len(packs) + 5)
    c.counts['pack wrappers'] = len(packs); c.log(f'drew {len(packs)} pack wrappers and {len(PL.RARS)} card backs')


def step_manifest(c):
    try: commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception: commit = ''
    m = dict(exported=time.strftime('%Y-%m-%d %H:%M:%S'), exported_unix=int(time.time()), git=commit, counts=c.counts)
    json.dump(m, open(c.path('data', 'export_manifest.json'), 'w'), indent=1); c.log('wrote export_manifest.json')


STEPS = [('data', 'CSV data', step_data), ('sprites', 'Player sprite sheets + skins', step_sprites), ('hair', 'Hair layers', step_hair), ('looks', 'Player look atlases', step_looks),
         ('cards', 'Skill cards', step_cards), ('players', 'Player cards', step_players), ('packs', 'Pack wrappers + card backs', step_packs), ('manifest', 'Manifest', step_manifest)]


def run(log=print, progress=None, only=None, out=None):
    """run the export. progress(step_index, step_count, title, done, total) is called as it goes. Returns (ok, counts, errors)."""
    out = out or GODOT; steps = [s for s in STEPS if not only or s[0] in only or s[0] == 'manifest']
    errors = []; c = Ctx(log, lambda *a: None, out); n = len(steps)
    for i, (key, title, fn) in enumerate(steps):
        log(f'[{i + 1}/{n}] {title}')
        if progress: progress(i, n, title, 0, 1)
        c.tick = (lambda d, t, i=i, title=title: progress(i, n, title, d, t)) if progress else (lambda *a: None)
        try: fn(c)
        except Exception as e:
            import traceback; errors.append((key, str(e))); log(f'  FAILED: {e}\n' + traceback.format_exc())
    if progress: progress(n, n, 'done', 1, 1)
    log('export finished' + (f' with {len(errors)} problem(s)' if errors else ' without problems') + f'  ->  {out}')
    return (not errors), c.counts, errors


def last_export():
    """(time string, git commit) of the last export, or None"""
    try: m = json.load(open(os.path.join(GODOT, 'data', 'export_manifest.json'))); return m.get('exported'), m.get('git')
    except Exception: return None


if __name__ == '__main__':
    only = [a for a in sys.argv[1:] if not a.startswith('-')] or None
    ok, counts, errs = run(only=only)
    sys.exit(0 if ok else 1)
