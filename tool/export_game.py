"""EXPORT TO GAME: copy / render everything the Godot project needs into godot/ in one go.
    python tool/export_game.py                 all steps
    python tool/export_game.py data packs      only these steps (names below)
The manager tool's big EXPORT button calls run() on a worker thread. Pure PIL / numpy, no Tk windows are opened here.

What lands where (godot/ is the Godot 4 project; assets/ and data/ are generated and git-ignored, shaders/ is tracked):
  data/             every data/*.csv and *.json (not progress), looks_index.csv, card_rules.json, export_manifest.json
  assets/sprites/   *_uv_sheet.png (12-ish frames across, 32 directions down, 40x40 cells), animations.json, skin_*.png
  assets/hair/      hair layer sheets
  assets/looks/     one 96x24 skin atlas per player (the shader recolours the sprite with it)
  assets/cards/     skill card faces (64x90) and tooltips
  assets/faces/     one small head-and-shoulders image per player; the card itself is assembled in the game
  assets/card/      shared card layers: bg_/top_ per rarity, foil_ strips (36 frames) per foil style
  assets/font/      the 3x5 pixel font (atlas + chars.txt); data/card_rules.json has the layout numbers
  assets/packs/     pack wrappers drawn from data/packs.csv and the card backs per tier
  animations/players/ player_library.tres (one Animation per sprite sheet) and player_flow.tres (AnimationTree state machine, arrows from data/animation_flow.csv); tracked in git
  shaders/          uv_skin.gdshader"""
import os, sys, json, shutil, time, csv, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GODOT = os.path.join(ROOT, 'godot')
for p in ('tool', 'cards', 'sprites', 'packs', 'titan', 'stadiums', 'balls'):
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
    """player cards are modular: shared layers per rarity / foil style, one small face per player, text and stats drawn in the game from the CSV"""
    import playercard as PC, foil
    from PIL import Image
    import cardlib
    T = _tables(); rows = T.table('players').rows; N = 36; steps = len(rows) + 5 + 5 + 3 + 1; n = 0
    for r in PC.RC:
        PC.bg_layer(r).save(c.path('assets', 'card', f'bg_{r.lower()}.png')); PC.top_layer(r).save(c.path('assets', 'card', f'top_{r.lower()}.png')); n += 10 // len(PC.RC); c.tick(n, steps)
    for st in foil.STYLE_BY_RARITY.values():
        sh = Image.new('RGBA', (64 * N, 90))
        for k in range(N): sh.paste(PC.bg_layer([q for q, v in foil.STYLE_BY_RARITY.items() if v == st][0], st, k / N), (64 * k, 0))
        sh.save(c.path('assets', 'card', f'foil_{st}.png')); n += 1; c.tick(n, steps)
    # pixel font atlas: 4x6 cells, 16 per row; chars.txt lists them in order
    chars = ''.join(sorted(cardlib.G.keys())); W = 16; fa = Image.new('RGBA', (W * 4, ((len(chars) + W - 1) // W) * 6), (0, 0, 0, 0))
    for i, ch in enumerate(chars):
        cell = Image.new('RGBA', (4, 6), (0, 0, 0, 0)); cardlib.draw_text(cell, 0, 0, ch, (255, 255, 255, 255)); fa.paste(cell, ((i % W) * 4, (i // W) * 6))
    fa.save(c.path('assets', 'font', 'pixel.png')); open(c.path('assets', 'font', 'chars.txt'), 'w', encoding='utf-8').write(chars)
    rules = dict(card_size=[64, 90], out_stats=PC.OUT_STATS, gk_stats=PC.GK_STATS, rating_w=PC.RATING_W, rarity_colours={k: {kk: list(vv) for kk, vv in v.items()} for k, v in PC.RC.items()},
                 stat_colour=list(PC.STAT_COL), foil_by_rarity=foil.STYLE_BY_RARITY, foil_frames=N, ink=list(cardlib.INK), panel=list(cardlib.PANEL), foil_shimmer=foil.SHIM, face_offset=[11, 21], font_cell=[4, 6], font_columns=W)
    json.dump(rules, open(c.path('data', 'card_rules.json'), 'w'), indent=1)
    for i, r in enumerate(rows):
        PC.face_layer(r).save(c.path('assets', 'faces', f"{r['id']}.png")); c.tick(n + i + 1, steps)
    c.counts['player faces'] = len(rows); c.log(f'wrote {len(rows)} player faces, {len(PC.RC)} rarity layers x2, {len(foil.STYLE_BY_RARITY)} foil strips, the pixel font and card_rules.json')


def step_animations(c):
    """one Godot Animation per sprite sheet (AnimationPlayer library) + an AnimationTree state machine whose arrows come from data/animation_flow.csv.
    Written to godot/animations/players/ (tracked in git: they only name clips, they never point at generated images)."""
    meta = json.load(open(os.path.join(UV, 'animations.json')))['animations']; names = sorted(meta); out = os.path.join(c.out, 'animations', 'players'); os.makedirs(out, exist_ok=True)
    flow = [r for r in csv.DictReader(open(os.path.join(DATA, 'animation_flow.csv'), encoding='utf-8-sig')) if r['from'] in meta and r['to'] in meta]
    # --- library
    L = ['[gd_resource type="AnimationLibrary" load_steps=%d format=3]\n' % (len(names) + 1)]
    for n in names:
        m = meta[n]; fr = int(m['frames']); ms = float(m['ms_per_frame']) / 1000.0
        times = ', '.join(f'{i * ms:.4f}' for i in range(fr)); trans = ', '.join('1' for _ in range(fr))
        L.append(f'[sub_resource type="Animation" id="Animation_{n}"]\nresource_name = "{n}"\nlength = {fr * ms:.4f}\nloop_mode = {1 if m.get("loop") else 0}\nstep = {ms:.4f}')
        def track(i, typ, path, keys, extra=''):
            L.append(f'tracks/{i}/type = "{typ}"\ntracks/{i}/imported = false\ntracks/{i}/enabled = true\ntracks/{i}/path = NodePath("{path}")\ntracks/{i}/interp = 1\ntracks/{i}/loop_wrap = true\ntracks/{i}/keys = {{\n{keys}\n}}')
        track(0, 'value', 'Sprite:sheet', f'"times": PackedFloat32Array(0),\n"transitions": PackedFloat32Array(1),\n"update": 1,\n"values": ["{n}"]')
        track(1, 'value', 'Sprite:frame_index', f'"times": PackedFloat32Array({times}),\n"transitions": PackedFloat32Array({trans}),\n"update": 1,\n"values": [{", ".join(str(i) for i in range(fr))}]')
        ev = sorted((int(f), k) for k, f in (m.get('events') or {}).items() if isinstance(f, int) and not isinstance(f, bool) and 0 <= f < fr)
        if ev:
            vals = ', '.join('{\n"args": ["%s"],\n"method": &"clip_event_fired"\n}' % k for f, k in ev)
            track(2, 'method', 'Sprite', f'"times": PackedFloat32Array({", ".join(f"{f * ms:.4f}" for f, k in ev)}),\n"transitions": PackedFloat32Array({", ".join("1" for _ in ev)}),\n"values": [{vals}]')
        L.append('')
    L.append('[resource]\n_data = {\n' + ',\n'.join(f'&"{n}": SubResource("Animation_{n}")' for n in names) + '\n}\n')
    open(os.path.join(out, 'player_library.tres'), 'w', newline='\n').write('\n'.join(L))
    # --- state machine (the graph you see in the AnimationTree panel)
    chained = {r['from'] for r in flow}; ordered = []
    for r in flow:
        for k in (r['from'], r['to']):
            if k not in ordered: ordered.append(k)
    groups = {}
    for n in names:
        if n not in ordered: groups.setdefault(n.split('_')[0].rstrip('0123456789') or n, []).append(n)
    pos = {}; col_w, row_h = 230, 80
    ordered_rows = [ordered] if ordered else []
    for g in sorted(groups): ordered_rows.append(groups[g])
    y = 0
    for row in ordered_rows:
        for i, n in enumerate(row): pos[n] = (i % 8 * col_w, y + i // 8 * row_h)
        y += ((len(row) + 7) // 8) * row_h + 60
    # chains laid out left to right: source column 0, target column 1 for the seeded flows
    if ordered:
        srcs = []; tgts = []
        for r in flow:
            if r['from'] not in srcs: srcs.append(r['from'])
            if r['to'] not in tgts: tgts.append(r['to'])
        for i, n in enumerate(srcs): pos[n] = (0, i * row_h)
        for i, n in enumerate(tgts):
            if n not in srcs: pos[n] = (col_w * 1.5, i * row_h * 2)
        oy = max(v[1] for k, v in pos.items() if k in srcs + tgts) + row_h + 60
        base_y = oy
        for row in ordered_rows[1:]:
            for i, n in enumerate(row): pos[n] = (i % 8 * col_w, base_y + i // 8 * row_h)
            base_y += ((len(row) + 7) // 8) * row_h + 60
    S = ['[gd_resource type="AnimationNodeStateMachine" load_steps=%d format=3]\n' % (len(names) + len(flow) + 2)]
    for n in names: S.append(f'[sub_resource type="AnimationNodeAnimation" id="AnimationNodeAnimation_{n}"]\nanimation = &"{n}"\n')
    S.append('[sub_resource type="AnimationNodeStateMachineTransition" id="Transition_start"]\nadvance_mode = 2\n')
    for i, r in enumerate(flow): S.append(f'[sub_resource type="AnimationNodeStateMachineTransition" id="Transition_{i}"]\nswitch_mode = 2\nadvance_mode = 2\n')
    R = ['[resource]', 'states/Start/position = Vector2(-260, 0)', 'states/End/position = Vector2(-260, 90)']
    for n in names: R.append(f'states/{n}/node = SubResource("AnimationNodeAnimation_{n}")\nstates/{n}/position = Vector2({pos[n][0]:.0f}, {pos[n][1]:.0f})')
    tr = ['"Start", "base_idle", SubResource("Transition_start")'] + [f'"{r["from"]}", "{r["to"]}", SubResource("Transition_{i}")' for i, r in enumerate(flow)]
    R.append('transitions = [' + ', '.join(tr) + ']\ngraph_offset = Vector2(-300, -60)')
    open(os.path.join(out, 'player_flow.tres'), 'w', newline='\n').write('\n'.join(S) + '\n' + '\n'.join(R) + '\n')
    c.counts['animations'] = len(names); c.counts['flow arrows'] = len(flow); c.log(f'wrote {len(names)} animations (AnimationPlayer library) and a state machine with {len(flow)} arrows from data/animation_flow.csv')


def step_packs(c):
    import packlib as PL, design2 as D, opening as O
    data = PL.load(); packs = data['packs']
    for i, pk in enumerate(packs): D.foil_bag(pk).save(c.path('assets', 'packs', f"{pk['id']}.png")); c.tick(i + 1, len(packs) + 5)
    for j, r in enumerate(PL.RARS): O.card_back(r).save(c.path('assets', 'packs', f'back_{r.lower()}.png')); c.tick(len(packs) + j + 1, len(packs) + 5)
    c.counts['pack wrappers'] = len(packs); c.log(f'drew {len(packs)} pack wrappers and {len(PL.RARS)} card backs')


def step_balls(c):
    import balllib as BL
    n = BL.render_all(c.path('assets', 'balls'), log=c.log, tick=c.tick); c.counts['balls'] = n
    c.log(f'drew {n} ball texture sheets (physics numbers go with data/balls.csv)')


def step_stadiums(c):
    import stadiumlib as SL
    n = SL.render_all(c.path('assets', 'pitches'), log=c.log, tick=c.tick); c.counts['stadiums'] = n
    c.log(f'drew {n} stadiums (pitch, stands, goals, flag)')


def step_manifest(c):
    try: commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception: commit = ''
    m = dict(exported=time.strftime('%Y-%m-%d %H:%M:%S'), exported_unix=int(time.time()), git=commit, counts=c.counts)
    json.dump(m, open(c.path('data', 'export_manifest.json'), 'w'), indent=1); c.log('wrote export_manifest.json')


STEPS = [('data', 'CSV data', step_data), ('sprites', 'Player sprite sheets + skins', step_sprites), ('hair', 'Hair layers', step_hair), ('looks', 'Player look atlases', step_looks),
         ('animations', 'Animation library + flow graph', step_animations), ('cards', 'Skill cards', step_cards), ('players', 'Player cards', step_players), ('packs', 'Pack wrappers + card backs', step_packs), ('stadiums', 'Pitches + stadiums', step_stadiums), ('balls', 'Ball textures', step_balls), ('manifest', 'Manifest', step_manifest)]


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
