"""Pack logic shared by the game, the tool and the preview. Everything comes from three CSVs in data/:
  packs.csv       one row per pack: price, source (shop / ranked / event), item counts, wrapper look, guarantee, pity, schedule (start / end), active, sort
  pack_odds.csv   rarity odds per pack (percent, should add up to 100)
  pack_pools.csv  what a pack may contain: rows per pack, kind (player/card), category (role or card category), rarity, id, mode (include/exclude), weight
A pack with no pool rows draws from everything.  Pity state (packs since the last pity-rarity pull) belongs to the player's save, not to the data.
Nothing here needs Tk, so the game can port it as is.  Functions take plain row dicts, so the tool can pass unsaved edits."""
import os, csv, random, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data')
RARS = ['COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGEND']
SOURCES = ['shop', 'ranked', 'event']
FOILS = ['', 'aurora', 'galaxy', 'rainbow']
SILS = ['bust', 'cards', 'both']
PACK_COLS = ['id', 'name', 'source', 'price', 'player_items', 'card_items', 'tier', 'foil', 'silhouette', 'guarantee_min', 'pity_rarity', 'pity_start', 'pity_step', 'pity_hard', 'start', 'end', 'sort', 'active', 'note']
POOL_COLS = ['pack', 'kind', 'category', 'rarity', 'id', 'mode', 'weight', 'note']


def read(name):
    with open(os.path.join(DATA, name + '.csv'), encoding='utf-8-sig') as f:
        return [dict(r) for r in csv.DictReader(f)]


def load():
    """the three pack tables from disk"""
    return dict(packs=read('packs'), odds={r['pack']: r for r in read('pack_odds')}, pools=read('pack_pools'))


def num(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d


def inum(v, d=0):
    try: return int(float(v))
    except (TypeError, ValueError): return d


def bundle(pid, data=None):
    """one pack's definition + odds + pool rows"""
    data = data or load(); pk = next(r for r in data['packs'] if r['id'] == pid)
    return dict(pk=pk, odds=data['odds'].get(pid, {}), pools=[r for r in data['pools'] if r['pack'] == pid])


# ---------------------------------------------------------------------------------------------------- schedule
def parse_time(s):
    s = (s or '').strip()
    if not s: return None
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try: return datetime.datetime.strptime(s, fmt)
        except ValueError: pass
    raise ValueError(f'bad date "{s}" (use YYYY-MM-DD or YYYY-MM-DD HH:MM)')


def state(pk, now=None):
    """hidden | upcoming | live | expired.  Expired and hidden packs are not in the shop."""
    now = now or datetime.datetime.now()
    if str(pk.get('active', '1')).strip() not in ('1', 'true', 'True', 'yes'): return 'hidden'
    try: a, b = parse_time(pk.get('start')), parse_time(pk.get('end'))
    except ValueError: return 'hidden'
    if a and now < a: return 'upcoming'
    if b and now > b: return 'expired'
    return 'live'


def shop(data=None, now=None, source='shop'):
    """packs to show now, in sort order. Event (limited) packs appear only inside their window."""
    data = data or load()
    return sorted([r for r in data['packs'] if state(r, now) == 'live' and r.get('source') in ((source,) if isinstance(source, str) else source) and inum(r.get('price')) >= 0], key=lambda r: inum(r.get('sort'), 999))


def limited(pk): return bool((pk.get('end') or '').strip())


# ---------------------------------------------------------------------------------------------------- odds + pity
def pity_on(pk): return inum(pk.get('pity_hard')) > 0 or num(pk.get('pity_step')) > 0


def pity_extra(pk, dry):
    """percentage points moved up to the pity rarity and better, after `dry` packs without one"""
    if not pity_on(pk) or dry < inum(pk.get('pity_start')): return 0.0
    return num(pk.get('pity_step')) * (dry - inum(pk.get('pity_start')) + 1)


def weights(pk, odds, dry=0):
    """the five rarity weights (sum 100) with the pity boost for a dry spell of `dry` packs"""
    w = [max(0.0, num(odds.get(r.lower()))) for r in RARS]; tot = sum(w) or 1.0; w = [x * 100.0 / tot for x in w]
    ex = pity_extra(pk, dry)
    if ex > 0:
        r = RARS.index(pk.get('pity_rarity') or 'RARE'); low = sum(w[:r]); mv = min(ex, low)
        if mv > 0 and low > 0:
            hi = sum(w[r:]); w = [x * (1 - mv / low) if i < r else x for i, x in enumerate(w)]
            w = [x + (mv * x / hi if hi > 0 else (mv if i == r else 0)) if i >= r else x for i, x in enumerate(w)]
    return w


def odds_total(odds): return sum(num(odds.get(r.lower())) for r in RARS)


# ---------------------------------------------------------------------------------------------------- pools
def _match(row, item, kind):
    cat = (row.get('category') or '').strip(); rar = (row.get('rarity') or '').strip(); i = (row.get('id') or '').strip()
    have = item.get('role') if kind == 'player' else item.get('cat')
    return (not cat or cat == have) and (not rar or rar == item.get('rarity')) and (not i or i == item.get('id'))


def eligible(kind, pools, rows, fallback=True):
    """{rarity: [(row, weight), ...]} for this pack and kind. No include rows = everything; exclude rows always remove. A rarity the pool leaves empty falls back to the whole table."""
    inc = [p for p in pools if p.get('kind') == kind and (p.get('mode') or 'include') == 'include']
    exc = [p for p in pools if p.get('kind') == kind and p.get('mode') == 'exclude']
    out = {r: [] for r in RARS}
    for it in rows:
        if it.get('rarity') not in out: continue
        if any(_match(p, it, kind) for p in exc): continue
        if inc:
            ws = [num(p.get('weight'), 1.0) or 1.0 for p in inc if _match(p, it, kind)]
            if not ws: continue
            out[it['rarity']].append((it, max(ws)))
        else: out[it['rarity']].append((it, 1.0))
    if fallback:
        for r in RARS:
            if not out[r]: out[r] = [(it, 1.0) for it in rows if it.get('rarity') == r]
    return out


class Pools:
    """eligible items per kind, built once per pack"""
    def __init__(self, b, players, cards):
        self.p = eligible('player', b['pools'], players); self.c = eligible('card', b['pools'], cards)
        self.allp = players; self.allc = cards

    def draw(self, kind, rar, rng):
        L = (self.p if kind == 'player' else self.c)[rar]
        if not L: L = [(x, 1.0) for x in (self.allp if kind == 'player' else self.allc)]
        return rng.choices([x for x, _ in L], [w for _, w in L])[0]


# ---------------------------------------------------------------------------------------------------- roll
def roll(b, players, cards, rng=None, dry=0, best=None, pools=None):
    """one pack: a list of dict(kind, rarity, row), best card last. dry = packs opened since the last pity-rarity pull.
    Guarantee (guarantee_min) and hard pity each make sure one item is at least that rarity. `best` forces a minimum best rarity (previews only)."""
    rng = rng or random.Random(); pk = b['pk']; pools = pools or Pools(b, players, cards)
    P, C = inum(pk.get('player_items')), inum(pk.get('card_items')); w = weights(pk, b['odds'], dry)
    def attempt():
        items = [['player', rng.choices(RARS, w)[0]] for _ in range(P)] + [['card', rng.choices(RARS, w)[0]] for _ in range(C)]
        need = []
        gm = (pk.get('guarantee_min') or '').strip().upper()
        if gm in RARS: need.append(RARS.index(gm))
        if pity_on(pk) and inum(pk.get('pity_hard')) > 0 and dry >= inum(pk.get('pity_hard')) - 1: need.append(RARS.index(pk.get('pity_rarity') or 'RARE'))
        for n in need:
            if items and max(RARS.index(r) for _, r in items) < n: k = rng.randrange(len(items)); items[k][1] = RARS[n]
        return items
    for _ in range(300):
        items = attempt()
        if best is None or not items or max(RARS.index(r) for _, r in items) >= RARS.index(best): break
    pull = [dict(kind=k, rarity=r, row=pools.draw(k, r, rng)) for k, r in items]
    pull.sort(key=lambda x: RARS.index(x['rarity']))
    return pull


def next_dry(pk, pull, dry):
    """the new dry-spell counter after opening this pack"""
    if not pity_on(pk): return 0
    r = RARS.index(pk.get('pity_rarity') or 'RARE')
    return 0 if any(RARS.index(x['rarity']) >= r for x in pull) else dry + 1


# ---------------------------------------------------------------------------------------------------- simulator
def simulate(b, players, cards, n=10000, seed=1):
    """open n packs in a row the way one player would (pity counter carried), and report what comes out"""
    rng = random.Random(seed); pk = b['pk']; pools = Pools(b, players, cards); P, C = inum(pk.get('player_items')), inum(pk.get('card_items'))
    items = {r: 0 for r in RARS}; best = {r: 0 for r in RARS}; dry = 0; hits = 0; gap = 0; gaps = []; longest = 0; boosted = 0; hard = 0; pr = RARS.index(pk.get('pity_rarity') or 'RARE')
    base_hit = 0
    for _ in range(n):
        if pity_extra(pk, dry) > 0: boosted += 1
        if inum(pk.get('pity_hard')) > 0 and dry >= inum(pk.get('pity_hard')) - 1: hard += 1
        pull = roll(b, players, cards, rng, dry, pools=pools)
        for x in pull: items[x['rarity']] += 1
        if pull: best[max((x['rarity'] for x in pull), key=RARS.index)] += 1
        h = any(RARS.index(x['rarity']) >= pr for x in pull)
        gap += 1
        if h: hits += 1; gaps.append(gap); longest = max(longest, gap); gap = 0
        dry = next_dry(pk, pull, dry)
    total_items = max(1, sum(items.values())); price = num(pk.get('price'))
    rare_pl = {r: sum(items[x] for x in RARS[i:]) for i, r in enumerate(RARS)}
    return dict(n=n, items={r: items[r] * 100.0 / total_items for r in RARS}, best={r: best[r] * 100.0 / n for r in RARS},
                at_least={r: sum(best[x] for x in RARS[i:]) * 100.0 / n for i, r in enumerate(RARS)},
                pity_rarity=RARS[pr], hit_rate=hits * 100.0 / n, avg_gap=(sum(gaps) / len(gaps)) if gaps else float('inf'), longest_dry=longest,
                boosted=boosted * 100.0 / n, hard=hard * 100.0 / n, price=price, per_pack_items=P + C,
                cost_per_hit=(price * n / hits) if hits else float('inf'), cost_per_legend=(price * n / best['LEGEND']) if best['LEGEND'] else float('inf'),
                cost_per_epic=(price * n / sum(best[x] for x in ('EPIC', 'LEGEND'))) if (best['EPIC'] + best['LEGEND']) else float('inf'))


def report(res, name=''):
    L = [f"{name}: {res['n']} packs, {res['per_pack_items']} items each, price {res['price']:.0f}"]
    L.append('  items      ' + '  '.join(f"{r[:3]} {res['items'][r]:5.1f}%" for r in RARS))
    L.append('  best/pack  ' + '  '.join(f"{r[:3]} {res['best'][r]:5.1f}%" for r in RARS))
    L.append('  at least   ' + '  '.join(f"{r[:3]} {res['at_least'][r]:5.1f}%" for r in RARS))
    L.append(f"  pity ({res['pity_rarity']}+): hit {res['hit_rate']:.1f}% of packs, avg gap {res['avg_gap']:.1f}, longest dry {res['longest_dry']}, boosted {res['boosted']:.1f}% of packs, hard-guaranteed {res['hard']:.1f}%")
    L.append(f"  cost per {res['pity_rarity'].lower()}+ pack {res['cost_per_hit']:.0f}, per epic+ pack {res['cost_per_epic']:.0f}, per legend pack {res['cost_per_legend']:.0f}")
    return '\n'.join(L)


def check(b, players=None, cards=None):
    """problems with one pack as (severity, message)"""
    out = []; pk = b['pk']; add = lambda s, m: out.append((s, m))
    if not (pk.get('name') or '').strip(): add('error', 'no name')
    if pk.get('source') not in SOURCES: add('error', f"source must be one of {'/'.join(SOURCES)}")
    if inum(pk.get('price'), -1) < 0: add('error', 'price must be 0 or more')
    if pk.get('source') == 'shop' and inum(pk.get('price')) == 0: add('warn', 'shop pack with price 0')
    if inum(pk.get('player_items'), -1) < 0 or inum(pk.get('card_items'), -1) < 0: add('error', 'item counts must be 0 or more')
    elif inum(pk.get('player_items')) + inum(pk.get('card_items')) == 0: add('error', 'pack has no items')
    if pk.get('tier') not in RARS: add('error', 'tier must be a rarity')
    if (pk.get('foil') or '') not in FOILS: add('error', 'foil must be blank / aurora / galaxy / rainbow')
    if pk.get('silhouette') not in SILS: add('error', 'silhouette must be bust / cards / both')
    gm = (pk.get('guarantee_min') or '').strip()
    if gm and gm not in RARS: add('error', 'guarantee_min must be blank or a rarity')
    if pity_on(pk):
        if pk.get('pity_rarity') not in RARS: add('error', 'pity_rarity must be a rarity')
        if inum(pk.get('pity_hard')) > 0 and inum(pk.get('pity_hard')) <= inum(pk.get('pity_start')): add('warn', 'pity_hard is not after pity_start')
    try:
        a, z = parse_time(pk.get('start')), parse_time(pk.get('end'))
        if a and z and z <= a: add('error', 'end is not after start')
        if pk.get('source') == 'event' and not z: add('warn', 'event pack with no end date')
    except ValueError as e: add('error', str(e))
    t = odds_total(b['odds'])
    if not b['odds']: add('error', 'no row in pack_odds.csv')
    elif abs(t - 100) > 0.5: add('warn', f'odds add up to {t:g}, not 100')
    for p in b['pools']:
        if p.get('kind') not in ('player', 'card'): add('error', 'pool row kind must be player or card')
        if (p.get('mode') or 'include') not in ('include', 'exclude'): add('error', 'pool mode must be include or exclude')
        if p.get('rarity') and p['rarity'] not in RARS: add('error', f"pool rarity {p['rarity']} unknown")
    if players is not None and cards is not None:
        for kind, rows, n in (('player', players, inum(pk.get('player_items'))), ('card', cards, inum(pk.get('card_items')))):
            if not n: continue
            el = eligible(kind, b['pools'], rows, fallback=False); odds = weights(pk, b['odds'])
            for i, r in enumerate(RARS):
                if odds[i] > 0 and not el[r]: add('warn', f'no {kind} of rarity {r} in the pool (the pack falls back to the whole table for it)')
    return out


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.join(ROOT, 'tool'))
    data = load(); players = read('players'); cards = read('cards'); n = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    ids = [sys.argv[1]] if len(sys.argv) > 1 and sys.argv[1] != 'all' else [r['id'] for r in data['packs']]
    for pid in ids:
        b = bundle(pid, data); print(report(simulate(b, players, cards, n), b['pk']['name']))
        for s, m in check(b, players, cards): print(f'  [{s}] {m}')
