"""Game constants shared by editors and validation (kept in one place; the CSVs hold the tweakable values)."""
ROLES = ['GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST']
OUT_STATS = ['PAC', 'SHO', 'PAS', 'DRI', 'DEF', 'PHY']
GK_STATS = ['REF', 'HAN', 'POS']
RARITY = ['COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGEND']
RARITY_COL = dict(COMMON='#9aa0ae', UNCOMMON='#4fb86a', RARE='#4a90e2', EPIC='#a85fd8', LEGEND='#f0b030')
CARD_CATS = ['SHOT', 'PASS', 'DRIBBLE', 'DEFEND', 'SUPPORT', 'KEEPER', 'TITAN']
CAT_COL = dict(SHOT='#de4c3e', PASS='#4284e2', DRIBBLE='#46b86c', SUPPORT='#ecc63c', DEFEND='#30b8b0', KEEPER='#9264dc', TITAN='#ffce46')
TIMING = ['ENGAGEMENT', 'ANYTIME']
KIND = ['ACTION', 'BUFF']
BEARD = ['none', 'stubble', 'short', 'full']
GLASSES = ['none', 'clear', 'dark']
# rating weights per role over PAC SHO PAS DRI DEF PHY (from scripts/gen_players.py)
RATING_W = {"CB": (.1, 0, .1, 0, .5, .3), "LB": (.25, 0, .2, .2, .25, .1), "RB": (.25, 0, .2, .2, .25, .1),
            "CDM": (.05, .05, .25, .1, .35, .2), "CM": (.1, .15, .35, .25, .1, .05), "CAM": (.1, .25, .3, .3, 0, .05),
            "LW": (.25, .2, .15, .3, 0, .1), "RW": (.25, .2, .15, .3, 0, .1), "ST": (.15, .45, .05, .15, 0, .2)}
FAMILY_KEYS = ['line_height', 'width', 'compactness', 'press', 'overlap', 'directness', 'counter', 'risk']
PHASES = ['BUILD', 'ATTACK', 'DEFEND']


def auto_rating(p):
    def v(k):
        try: return float(p.get(k) or 0)
        except ValueError: return 0.0
    if p.get('role') == 'GK':
        return int(round(v('REF') * .4 + v('HAN') * .3 + v('POS') * .3))
    w = RATING_W.get(p.get('role'))
    return int(round(sum(a * v(k) for a, k in zip(w, OUT_STATS)))) if w else 0


def to_int(s, default=None):
    try: return int(float(s))
    except (TypeError, ValueError): return default
