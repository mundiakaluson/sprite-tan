"""HUD art in the language of the cards (cards/cardlib2.py): the dark field (12,13,20), a 1 px frame with cut corners and a 1 px inner edge, the 3x5 pixel font,
category / rarity colours. Everything is generated here so the HUD and the cards stay consistent; colours come from data/hud_style.csv.
  render_assets()  -> {name: PIL image} for godot/assets/ui/ (panel, buttons x5, strip, rings); the game tints the near-white frames with an accent colour.
  preview(path)    -> a 960x540 mock of the match screen (needs the card libs); python hud/hudlib.py out.png
Nine-patch margins: panel and buttons are 16x16 with a margin of 4 (PixelPanel / PixelButton in godot/scripts/ui)."""
import os, sys, csv, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
from PIL import Image, ImageDraw

NINE = 16          # size of the nine-patch images
MARGIN = 4         # nine-patch margin


def hexrgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def style():
    out = {}
    for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'hud_style.csv'), encoding='utf-8')):
        out[r['key']] = hexrgb(r['value'])
    return out


def _mix(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _frame(im, edge, fill, inner):
    """card frame: 1 px edge, cut corners, a point at each inner corner, 1 px inner edge, flat fill"""
    w, h = im.size; px = im.load(); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(0, 0, 0, 0))
    d.rectangle([1, 1, w - 2, h - 2], fill=fill + (255,))
    d.rectangle([2, 2, w - 3, h - 3], outline=inner + (255,))
    d.rectangle([3, 3, w - 4, h - 4], fill=fill + (255,))
    for x in range(2, w - 2): px[x, 0] = edge + (255,); px[x, h - 1] = edge + (255,)
    for y in range(2, h - 2): px[0, y] = edge + (255,); px[w - 1, y] = edge + (255,)
    for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)): px[x, y] = edge + (255,)


def panel(S):
    im = Image.new('RGBA', (NINE, NINE)); _frame(im, S['frame'], S['base'], S['inner']); return im


def button(S, state):
    im = Image.new('RGBA', (NINE, NINE))
    if state == 'normal':    _frame(im, _mix(S['frame'], S['base'], 0.25), _mix(S['base'], S['field_hi'], 0.7), S['inner'])
    elif state == 'hover':   _frame(im, S['frame'], _mix(S['field_hi'], (255, 255, 255), 0.08), _mix(S['inner'], (255, 255, 255), 0.25))
    elif state == 'pressed':
        _frame(im, S['frame'], (8, 9, 14), (4, 5, 9)); d = ImageDraw.Draw(im)
        d.line([(3, 3), (NINE - 4, 3)], fill=(2, 3, 6, 255)); d.line([(3, 3), (3, NINE - 4)], fill=(2, 3, 6, 255))
    elif state == 'disabled': _frame(im, S['frame_dim'], S['base'], S['base'])
    elif state == 'active':                                    # a toggled-on button: bright frame, lit field (the tint colour shows through it)
        _frame(im, (255, 255, 255), _mix(S['field_hi'], (255, 255, 255), 0.35), (255, 255, 255))
        px = im.load()
        for y in range(3, NINE - 3):
            for x in range(3, NINE - 3): px[x, y] = _mix(S['base'], (255, 255, 255), 0.32 + 0.1 * (y - 3) / (NINE - 6)) + (255,)
    return im


def strip(S, w=960, h=120):
    """the HUD strip under the pitch: the card's dark field with a faint diagonal weave, lighter at the top, a frame-coloured line on top"""
    im = Image.new('RGBA', (w, h)); px = im.load()
    for y in range(h):
        k = y / (h - 1)
        for x in range(w):
            col = _mix(S['field_hi'], S['base'], min(1.0, k * 1.6))
            if (x - y // 2) % 9 == 0 and y > 4: col = _mix(col, S['text_dim'], 0.05)
            px[x, y] = col + (255,)
    d = ImageDraw.Draw(im)
    d.line([(0, 0), (w, 0)], fill=_mix(S['frame'], S['base'], 0.4) + (255,)); d.line([(0, 1), (w, 1)], fill=S['inner'] + (255,))
    return im


def _ellipse_points(rx, ry):
    pts = set(); n = int(8 * (rx + ry))
    for i in range(n):
        a = 2 * math.pi * i / n; pts.add((int(round(math.cos(a) * rx)), int(round(math.sin(a) * ry))))
    return pts


def ring(dashed=False, rx=13, ry=5):
    """a pixel ellipse seen on the grass: 2 px thick; dashed = a target ring"""
    w, h = rx * 2 + 3, ry * 2 + 4; im = Image.new('RGBA', (w, h)); px = im.load()
    for (x, y) in sorted(_ellipse_points(rx, ry), key=lambda p: math.atan2(p[1], p[0])):
        ang = math.atan2(y, x)
        if dashed and int((ang + math.pi) / (2 * math.pi) * 16) % 2: continue
        for dy in (0, 1): px[x + rx + 1, y + ry + 1 + dy] = (255, 255, 255, 255)
    return im


def render_assets():
    S = style()
    out = {'panel': panel(S), 'strip': strip(S), 'ring_select': ring(False), 'ring_target': ring(True, 15, 6)}
    for st in ('normal', 'hover', 'pressed', 'disabled', 'active'): out['button_' + st] = button(S, st)
    return out


# ------------------------------------------------------------------ preview (mock of the match screen, with the real card faces)
def _nine(dst, tex, x, y, w, h, tint=None):
    m = MARGIN; t = tex.copy()
    if tint:
        px = t.load()
        for yy in range(t.height):
            for xx in range(t.width):
                r, g, b, a = px[xx, yy]
                if a: px[xx, yy] = (r * tint[0] // 255, g * tint[1] // 255, b * tint[2] // 255, a)
    parts = {}
    xs = [(0, m, x, m), (m, NINE - m, x + m, w - 2 * m), (NINE - m, NINE, x + w - m, m)]
    ys = [(0, m, y, m), (m, NINE - m, y + m, h - 2 * m), (NINE - m, NINE, y + h - m, m)]
    for (sy0, sy1, dy, dh) in ys:
        for (sx0, sx1, dx, dw) in xs:
            piece = t.crop((sx0, sy0, sx1, sy1)).resize((dw, dh), Image.NEAREST); dst.alpha_composite(piece, (dx, dy))


def preview(path):
    sys.path.insert(0, os.path.join(ROOT, 'cards')); sys.path.insert(0, os.path.join(ROOT, 'sprites'))
    import cardlib, cardlib2
    from cardlib import draw_text, text_w, CAT
    import emblem
    S = style(); A = render_assets()
    im = Image.new('RGBA', (960, 540), (58, 120, 56, 255)); d = ImageDraw.Draw(im)
    for x in range(0, 960, 120): d.rectangle([x, 0, x + 59, 419], fill=(66, 132, 62, 255))
    im.alpha_composite(A['strip'], (0, 420))
    steel = (150, 160, 190)
    def label(x, y, s, col=(255, 255, 255), k=1):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if False else ():
            pass
        cardlib.draw_text(im, x, y, s, col + (255,), k)
    _nine(im, A['panel'], 4, 424, 192, 28, (214, 50, 64)); label(10, 429, 'HOME 0 - 0 AWAY', (255, 255, 255), 2); label(150, 440, "12'", (140, 146, 176))
    label(8, 456, 'J. MARTINEZ', (255, 255, 255))
    for i, (t, st) in enumerate([('THROUGH', 'normal'), ('RUN', 'hover'), ('PRESS', 'disabled'), ('TACKLE', 'disabled')]):
        bx = 4 + (i % 2) * 98; by = 466 + (i // 2) * 24
        _nine(im, A['button_' + st], bx, by, 94, 20, steel); col = {'normal': (255, 255, 255), 'hover': (255, 255, 255), 'disabled': (90, 94, 116)}[st]
        label(bx + 47 - text_w(t) // 2, by + 7, t, col)
    _nine(im, A['panel'], 200, 424, 539, 100, steel)
    import csv as _csv
    cards = [r for r in _csv.DictReader(open(os.path.join(ROOT, 'data', 'cards.csv'), encoding='utf-8'))]
    pick = []
    for cat in ('SHOT', 'SHOT', 'PASS', 'PASS', 'DRIBBLE', 'DRIBBLE', 'DEFEND', 'DEFEND'):
        for c in cards:
            if c['cat'] == cat and c not in pick: pick.append(c); break
    import recipes
    recipes.install(cardlib2.EMB)
    for i, c in enumerate(pick):
        row = dict(id=c['id'], name=c['name'], cat=c['cat'], slots=int(c['slots']), succ=int(c['succ']), risk=int(c['risk']), cd=int(c['cd']), desc=c.get('description', ''), rarity=c.get('rarity', ''))
        art = cardlib2.EMB.get(c['id'], cardlib2.R_impact)(CAT[c['cat']])
        im.alpha_composite(cardlib2.card(row, art), (205 + i * 67, 429))
    # team panel
    _nine(im, A['panel'], 742, 424, 214, 62, steel); label(750, 429, 'TEAM', (140, 146, 176))
    for i, t in enumerate(['AUTO', 'PRESS HIGH', 'MID BLOCK', 'PARK BUS', 'PUSH UP', 'COUNTER']):
        bx = 748 + (i % 3) * 68; by = 440 + (i // 3) * 22; st = 'active' if i == 0 else 'normal'
        _nine(im, A['button_' + st], bx, by, 64, 18, steel if i else (214, 50, 64)); label(bx + 32 - text_w(t) // 2, by + 6, t)
    # command box
    _nine(im, A['panel'], 742, 490, 214, 46, (90, 230, 255)); label(750, 496, 'THROUGH  L. MARTINEZ', (90, 230, 255), 1)
    label(750, 508, 'LET GO: THROUGH BALL, HE RUNS ONTO IT', (140, 146, 176)); label(750, 518, 'DRAG FURTHER FOR A LOB OVER THE TOP', (140, 146, 176))
    # rings
    im.alpha_composite(A['ring_select'].point(lambda v: v), (100, 300)); r2 = A['ring_target']; px = r2.load()
    for y in range(r2.height):
        for x in range(r2.width):
            if px[x, y][3]: px[x, y] = (90, 230, 255, 255)
    im.alpha_composite(r2, (300, 300))
    im.save(path); return path


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'preview.png')
    print(preview(out))
