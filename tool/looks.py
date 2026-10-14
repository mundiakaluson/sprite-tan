"""Player look: palettes from data/looks.csv, skin atlas painting (beard, glasses, chain...), and compositing of
body sheet + hair layer into a finished sprite frame. Uses the generator modules in sprites/."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
import tables

SPR = os.path.join(tables.ROOT, 'sprites')
OUT = os.path.join(SPR, 'out_uv')
if SPR not in sys.path:
    sys.path.insert(0, SPR)
import gen_uv as U  # noqa: E402

CW, CH = U.CW, U.CH
KITS = list(U.SKINS)


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette():
    t = tables.table('looks')
    out = {}
    for r in t.rows:
        out.setdefault(r['kind'], {})[r['key']] = r['hex']
    return out


def hair_styles():
    p = os.path.join(OUT, 'hair', 'hair_styles.json')
    if os.path.exists(p):
        try:
            d = json.load(open(p))
            return list(d['styles'])
        except Exception:
            pass
    return list(__import__('gen_hair').STYLE_ORDER)


def _fill(A_, reg, x0, y0, x1, y1, col):
    rx, ry, w, h = U.REG[reg]
    A_[ry + y0:ry + y1 + 1, rx + x0:rx + x1 + 1] = tuple(col) + (255,)


def _shade(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c)


def player_skin(p, kit=None):
    """96x24 RGBA atlas for one players.csv row (dict)."""
    pal = palette()
    kit = kit or ('keeper' if p.get('role') == 'GK' else 'home')
    tone = hexrgb(pal['skin'].get(str(p.get('skin') or '2'), '#eebe96'))
    hair = hexrgb(pal['hair'].get(p.get('hair_color') or 'brown', '#62422a'))
    style = p.get('hair_style') or 'H02_crop'
    s = dict(U.SKINS[kit], skin=tone, hair=hair, hair_style=style)
    A_ = U.make_skin(s)
    ac = {k: hexrgb(v) for k, v in pal.get('accent', {}).items()}
    beard = p.get('beard') or 'none'
    if beard == 'stubble':
        _fill(A_, 'HEAD', 4, 7, 7, 9, _shade(tone, 0.82)); _fill(A_, 'HEAD', 3, 8, 3, 9, _shade(tone, 0.82)); _fill(A_, 'HEAD', 8, 8, 8, 9, _shade(tone, 0.82))
    elif beard == 'short':
        _fill(A_, 'HEAD', 4, 8, 7, 9, hair); _fill(A_, 'HEAD', 3, 7, 3, 9, hair); _fill(A_, 'HEAD', 8, 7, 8, 9, hair)
    elif beard == 'full':
        _fill(A_, 'HEAD', 4, 6, 7, 9, hair); _fill(A_, 'HEAD', 3, 5, 3, 9, hair); _fill(A_, 'HEAD', 8, 5, 8, 9, hair)
        _fill(A_, 'HEAD', 5, 7, 6, 7, _shade(tone, 0.7))   # mouth gap
    g = p.get('glasses') or 'none'
    if g != 'none':
        lens = hexrgb(pal['glasses'].get(g, '#16161e')); frame = (28, 28, 36)
        _fill(A_, 'HEAD', 3, 4, 8, 4, frame)
        if g == 'dark':
            _fill(A_, 'HEAD', 4, 4, 7, 5, lens)
        else:
            _fill(A_, 'HEAD', 4, 5, 7, 5, lens); A_[U.REG['HEAD'][1] + 4, U.REG['HEAD'][0] + 4] = (34, 24, 30, 255); A_[U.REG['HEAD'][1] + 4, U.REG['HEAD'][0] + 7] = (34, 24, 30, 255)
    on = lambda k: str(p.get(k) or '0') not in ('0', '', 'none', 'no')
    if on('headband'):
        _fill(A_, 'HEAD', 0, 3, 15, 3, ac.get('headband', (244, 244, 250)))
    if on('wristband'):
        _fill(A_, 'FOREARM', 0, 4, 7, 5, ac.get('wristband', (244, 244, 250)))
    if on('chain'):
        c = ac.get('chain', (240, 192, 64))
        _fill(A_, 'CHEST', 8, 2, 12, 2, c); _fill(A_, 'CHEST', 10, 3, 10, 3, _shade(c, 1.1))
        _fill(A_, 'CHEST', 8, 1, 8, 1, c); _fill(A_, 'CHEST', 12, 1, 12, 1, c)
    if on('tattoo'):
        c = ac.get('tattoo', (60, 74, 120))
        for x in (1, 3, 5):
            _fill(A_, 'UPARM', x, 4, x, 5, c)
        _fill(A_, 'FOREARM', 0, 2, 7, 2, c)
    return A_


_sheets = {}


def sheet(path):
    if path not in _sheets or _sheets[path][0] != os.path.getmtime(path):
        _sheets[path] = (os.path.getmtime(path), np.array(Image.open(path).convert('RGBA')))
    return _sheets[path][1]


def anims():
    p = os.path.join(OUT, 'animations.json')
    try:
        return json.load(open(p))['animations']
    except Exception:
        return {}


def has_hair(style, anim):
    return os.path.exists(os.path.join(OUT, 'hair', f'{style}__{anim}.png'))


def frame_uv(anim, d, f):
    a = sheet(os.path.join(OUT, f'{anim}_uv_sheet.png'))
    return a[d * CH:(d + 1) * CH, f * CW:(f + 1) * CW]


def render(p, anim='run', d=0, f=0, kit=None, atlas=None, shadow=True):
    """Composite sprite (PIL RGBA, CWxCH) of player row p."""
    atlas = atlas if atlas is not None else player_skin(p, kit)
    out = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    if shadow:
        ImageDraw.Draw(out).ellipse([OXs() - 8, int(CH * .75) - 3, OXs() + 8, int(CH * .75) + 3], fill=(10, 10, 30, 70))
    n = anims().get(anim, {}).get('frames', 1)
    f %= max(1, n)
    out = Image.alpha_composite(out, U.apply_skin(frame_uv(anim, d, f), atlas))
    st = p.get('hair_style') or 'H02_crop'
    hp = os.path.join(OUT, 'hair', f'{st}__{anim}.png')
    if os.path.exists(hp):
        a = sheet(hp)
        out = Image.alpha_composite(out, U.apply_skin(a[d * CH:(d + 1) * CH, f * CW:(f + 1) * CW], atlas))
    return out


def OXs():
    return CW // 2
