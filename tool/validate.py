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
        if to_int(r.get('cd')) is None or to_int(r['cd']) < 0: add('error', 'cards', i, 'cd must be a number >= 0')
        if to_int(r.get('slots')) is None or to_int(r['slots']) < 1: add('error', 'cards', i, 'slots must be >= 1')
        for s in (r.get('stats') or '').split('+'):
            if s and s not in OUT_STATS + GK_STATS: add('error', 'cards', i, f'unknown stat {s}')
        if not r.get('name'): add('error', 'cards', i, 'no name')
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
    for r in tables.table('pack_odds').rows:
        try:
            tot = sum(float(r[k]) for k in ('common', 'uncommon', 'rare', 'epic', 'legend'))
            if abs(tot - 100) > 0.5: add('warn', 'pack_odds', r['pack'], f'odds add up to {tot}, not 100')
        except ValueError: add('error', 'pack_odds', r['pack'], 'non-numeric odds')
    import re
    for r in tables.table('kits').rows:
        for c in ('jersey', 'trim', 'shorts', 'shorts_trim', 'stripe', 'socks', 'sock_trim', 'boots', 'accent'):
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', r.get(c) or ''): add('error', 'kits', r['id'], f'{c} must be #rrggbb')
        for c in ('band', 'glove'):
            if r.get(c) and not re.fullmatch(r'#[0-9a-fA-F]{6}', r[c]): add('error', 'kits', r['id'], f'{c} must be #rrggbb or blank')
        if r.get('pattern') not in ('plain', 'hoop', 'hoops', 'stripes', 'sash'): add('error', 'kits', r['id'], 'unknown pattern')
    return out
