"""Checks over the CSV data. Returns a list of (severity, table, row id, message)."""
import tables
from rules import *
import looks


def run():
    out = []
    add = lambda sev, tb, rid, msg: out.append((sev, tb, rid, msg))
    pal = looks.palette()
    styles = set(looks.hair_styles())
    P = tables.table('players').rows
    seen, names = {}, {}
    for r in P:
        i = r['id']
        if i in seen: add('error', 'players', i, 'duplicate id')
        seen[i] = 1
        if r['name'] in names: add('warn', 'players', i, f"same name as {names[r['name']]}")
        names[r['name']] = i
        if r['role'] not in ROLES: add('error', 'players', i, f"unknown role {r['role']}")
        rl = [x for x in (r.get('roles') or '').split('|') if x]
        if r['role'] not in rl: add('warn', 'players', i, 'roles list does not include main role')
        for x in rl:
            if x not in ROLES: add('error', 'players', i, f'unknown role {x} in roles')
        if r['rarity'] not in RARITY: add('error', 'players', i, f"unknown rarity {r['rarity']}")
        stats = GK_STATS if r['role'] == 'GK' else OUT_STATS
        for k in stats:
            v = to_int(r.get(k))
            if v is None or not 1 <= v <= 99: add('error', 'players', i, f'{k} must be 1-99')
        for k in (OUT_STATS if r['role'] == 'GK' else GK_STATS):
            if r.get(k): add('warn', 'players', i, f'{k} is set but not used by role {r["role"]}')
        if to_int(r.get('rating')) is None: add('error', 'players', i, 'rating missing')
        elif abs(to_int(r['rating']) - auto_rating(r)) > 3: add('warn', 'players', i, f"rating {r['rating']} differs from stats ({auto_rating(r)})")
        if r.get('skin') not in pal.get('skin', {}): add('error', 'players', i, f"skin {r.get('skin')} not in looks.csv")
        if r.get('hair_color') not in pal.get('hair', {}): add('error', 'players', i, f"hair_color {r.get('hair_color')} not in looks.csv")
        if r.get('hair_style') not in styles: add('error', 'players', i, f"hair_style {r.get('hair_style')} unknown")
        if r.get('beard') not in BEARD: add('error', 'players', i, 'beard must be ' + '/'.join(BEARD))
        if r.get('glasses') not in GLASSES: add('error', 'players', i, 'glasses must be ' + '/'.join(GLASSES))
        for k in ('chain', 'headband', 'wristband', 'tattoo'):
            if r.get(k) not in ('0', '1'): add('error', 'players', i, f'{k} must be 0 or 1')
        if r.get('foot', 'R') not in ('R', 'L'): add('error', 'players', i, 'foot must be R or L (the stronger foot)')
        if r.get('special') not in ('0', '1'): add('error', 'players', i, 'special must be 0 or 1')
        elif r.get('special') == '1' and r.get('rarity') not in ('RARE', 'EPIC', 'LEGEND'): add('error', 'players', i, 'special is only for RARE, EPIC and LEGEND')
    C = tables.table('cards').rows
    seen = set()
    for r in C:
        i = r['id']
        if i in seen: add('error', 'cards', i, 'duplicate id')
        seen.add(i)
        if r['cat'] not in CARD_CATS: add('error', 'cards', i, f"unknown cat {r['cat']}")
        if r['rarity'] not in RARITY: add('error', 'cards', i, f"unknown rarity {r['rarity']}")
        if r['timing'] not in TIMING: add('error', 'cards', i, 'timing must be ENGAGEMENT or ANYTIME')
        if r['kind'] not in KIND: add('error', 'cards', i, 'kind must be ACTION or BUFF')
        for k in ('succ', 'risk'):
            v = to_int(r.get(k))
            if v is None or not 0 <= v <= 100: add('error', 'cards', i, f'{k} must be 0-100')
        for k, lo, hi in (('ball_speed', 0, 10), ('ball_arc', 0, 10), ('ball_curve', -5, 5)):
            v = r.get(k, '')
            if v != '' and (to_int(v) is None or not lo <= to_int(v) <= hi): add('error', 'cards', i, f'{k} must be blank or a number {lo} to {hi}')
        for k, lo, hi in (('move_mult', 0, 3), ('anim_rate', 0.4, 2), ('travel', 0, 2), ('reach', 0, 10), ('steer', 0, 10), ('lock', 0, 10)):
            v = r.get(k, '')
            if v != '':
                try: ok = lo <= float(v) <= hi
                except ValueError: ok = False
                if not ok: add('error', 'cards', i, f'{k} must be blank or a number {lo} to {hi}')
        if to_int(r.get('cd')) is None or to_int(r['cd']) < 0: add('error', 'cards', i, 'cd must be a number >= 0')
        if to_int(r.get('slots')) is None or to_int(r['slots']) < 1: add('error', 'cards', i, 'slots must be >= 1')
        for s in (r.get('stats') or '').split('+'):
            if s and s not in OUT_STATS + GK_STATS: add('error', 'cards', i, f'unknown stat {s}')
        if not r.get('name'): add('error', 'cards', i, 'no name')
        for t in (r.get('engage') or '').split():
            if t not in ('duel', 'shot', 'pass', 'aerial', 'one_on_one'): add('error', 'cards', i, f'unknown engage type {t} (duel shot pass aerial one_on_one)')
        for kv in (r.get('effect') or '').split():
            if '=' not in kv: add('error', 'cards', i, f'effect "{kv}" must be key=value')
        if r.get('engage') and r.get('timing') != 'ENGAGEMENT': add('warn', 'cards', i, 'engage is set but timing is not ENGAGEMENT')
        if len(r.get('description') or '') > 120: add('warn', 'cards', i, 'description is long for a card face')
    F = tables.table('formations').rows
    fam = {r['family'] for r in tables.table('formation_families').rows}
    sty = {r['style'] for r in tables.table('styles').rows}
    slots = tables.table('formation_slots').rows
    for r in F:
        i = r['id']
        if r['family'] not in fam: add('error', 'formations', i, f"unknown family {r['family']}")
        for k in FAMILY_KEYS:
            if r.get(k) not in ('', None):
                try:
                    if not 0 <= float(r[k]) <= 1: add('error', 'formations', i, f'{k} must be 0-1 or blank')
                except ValueError: add('error', 'formations', i, f'{k} is not a number')
        sl = [s for s in slots if s['formation'] == i]
        if len(sl) != 10: add('error', 'formations', i, f'has {len(sl)} outfield slots, needs 10')
        for s in sl:
            if s['role'] not in ROLES or s['role'] == 'GK': add('error', 'formations', i, f"slot {s['slot']} bad role {s['role']}")
            if s['style'] not in sty: add('error', 'formations', i, f"slot {s['slot']} unknown style {s['style']}")
            for k in ('x', 'y'):
                v = to_int(s.get(k))
                if v is None or not 0 <= v <= 100: add('error', 'formations', i, f"slot {s['slot']} {k} must be 0-100")
    ids = {r['id'] for r in F}
    for s in slots:
        if s['formation'] not in ids: add('error', 'formation_slots', s['formation'], 'slot for unknown formation')
    import os, sys
    pk_dir = os.path.join(tables.ROOT, 'packs')
    if pk_dir not in sys.path: sys.path.insert(0, pk_dir)
    import packlib as PL
    data = dict(packs=tables.table('packs').rows, odds={r['pack']: r for r in tables.table('pack_odds').rows}, pools=tables.table('pack_pools').rows)
    ids = {}
    for r in data['packs']:
        if r['id'] in ids: add('error', 'packs', r['id'], 'duplicate id')
        ids[r['id']] = 1
        for sev, msg in PL.check(dict(pk=r, odds=data['odds'].get(r['id'], {}), pools=[x for x in data['pools'] if x['pack'] == r['id']]), tables.table('players').rows, tables.table('cards').rows): add(sev, 'packs', r['id'], msg)
    for k in data['odds']:
        if k not in ids: add('error', 'pack_odds', k, 'odds for an unknown pack')
    for x in data['pools']:
        if x['pack'] not in ids: add('error', 'pack_pools', x['pack'], 'pool row for an unknown pack')
    try:
        import json
        known = set(json.load(open(os.path.join(tables.ROOT, 'sprites', 'out_uv', 'animations.json')))['animations'])
        seen = {}
        for r in tables.table('animation_flow').rows:
            for k in ('from', 'to'):
                if r.get(k) not in known: add('error', 'animation_flow', r.get('from', ''), f"{k} '{r.get(k)}' is not a baked animation")
            if r.get('from') in seen: add('error', 'animation_flow', r['from'], 'two arrows leave this clip (only one is allowed)')
            seen[r.get('from')] = 1
            if r.get('mode') not in ('auto',): add('error', 'animation_flow', r.get('from', ''), "mode must be 'auto'")
    except (OSError, KeyError): pass
    try:
        sd = os.path.join(tables.ROOT, 'stadiums')
        if sd not in sys.path: sys.path.insert(0, sd)
        import stadiumlib as SL
        for sev, rid, msg in SL.check(tables.table('stadiums').rows): add(sev, 'stadiums', rid, msg)
        import goallib as GL
        for sev, rid, msg in GL.check(tables.table('goals').rows): add(sev, 'goals', rid, msg)
        gids = {r['id'] for r in tables.table('goals').rows}
        for r in tables.table('stadiums').rows:
            if r.get('goal') not in gids: add('error', 'stadiums', r['id'], f"goal {r.get('goal')} is not in goals.csv")
    except (OSError, KeyError, ImportError): pass
    try:
        bd = os.path.join(tables.ROOT, 'balls')
        if bd not in sys.path: sys.path.insert(0, bd)
        import balllib as BL
        for sev, rid, msg in BL.check(tables.table('balls').rows): add(sev, 'balls', rid, msg)
        for sev, rid, msg in BL.check_kicks(tables.table('kick_styles').rows): add(sev, 'kick_styles', rid, msg)
    except (OSError, KeyError, ImportError): pass
    import re
    for r in tables.table('kits').rows:
        for c in ('jersey', 'trim', 'shorts', 'shorts_trim', 'stripe', 'socks', 'sock_trim', 'boots', 'accent'):
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', r.get(c) or ''): add('error', 'kits', r['id'], f'{c} must be #rrggbb')
        for c in ('band', 'glove'):
            if r.get(c) and not re.fullmatch(r'#[0-9a-fA-F]{6}', r[c]): add('error', 'kits', r['id'], f'{c} must be #rrggbb or blank')
        if r.get('pattern') not in ('plain', 'hoop', 'hoops', 'stripes', 'sash'): add('error', 'kits', r['id'], 'unknown pattern')
    return out
