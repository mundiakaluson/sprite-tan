"""Design mock of the top-of-pitch score bug (EA FC style): scores, clock, period, red cards, added time, and ranked / unranked variants. Not wired into the game yet."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'cards')); sys.path.insert(0, os.path.join(ROOT, 'sprites'))
from PIL import Image, ImageDraw
import hudlib, cardlib
from cardlib import draw_text, text_w

GOLD = (255, 200, 70); STEEL = (150, 160, 190); DIM = (140, 146, 176); WHITE = (255, 255, 255); ORANGE = (255, 150, 60); RED = (236, 60, 52)
S = hudlib.style(); A = hudlib.render_assets()


def T(im, x, y, s, col=WHITE, k=1):
    draw_text(im, x, y + 1 if False else y, s, col + (255,), k)


def shadowed(im, x, y, s, col=WHITE, k=1):
    draw_text(im, x + k, y + k, s, (0, 0, 0, 200), k); draw_text(im, x, y, s, col + (255,), k)


def cards_red(im, x, y, n):
    d = ImageDraw.Draw(im)
    for i in range(n):
        d.rectangle([x + i * 5, y, x + i * 5 + 3, y + 5], fill=RED + (255,), outline=(120, 20, 20, 255)); im.putpixel((x + i * 5 + 1, y + 1), (255, 170, 160, 255))
    return x + n * 5


def seg(im, x, y, w, h, accent, ranked=False):
    hudlib._nine(im, A['panel'], x, y, w, h, accent)
    if ranked:                                                    # gold studs on the top corners: the ranked mark
        d = ImageDraw.Draw(im)
        for cx in (x + 2, x + w - 3): d.rectangle([cx - 1, y - 1, cx + 1, y + 1], fill=GOLD + (255,)); im.putpixel((cx, y), (255, 250, 200, 255))


def tag(im, x, y, text, col, fill_dark=True):
    w = text_w(text) + 10
    hudlib._nine(im, A['panel'], x, y, w, 11, col)
    shadowed(im, x + 5, y + 3, text, col)
    return w


def clock_block(im, x, y, w, accent, clock, period, added=None, ranked=False):
    seg(im, x, y, w, 24, accent, ranked)
    cw = text_w(clock, 2)
    cx = x + (w - cw - (text_w(added) + 3 if added else 0)) // 2
    shadowed(im, cx, y + 4, clock, WHITE, 2)
    if added: shadowed(im, cx + cw + 3, y + 7, added, ORANGE, 1)
    shadowed(im, x + (w - text_w(period)) // 2, y + 17, period, DIM, 1)


def team_seg(im, x, y, w, accent, name, score, kit, reds, side, ranked=False):
    """side 'L' = home (chip, name, cards ... score at the right), 'R' = away (score at the left ... name, chip)"""
    seg(im, x, y, w, 24, accent, ranked)
    d = ImageDraw.Draw(im)
    sc = str(score); sw = text_w(sc, 2)
    if side == 'L':
        d.rectangle([x + 5, y + 6, x + 8, y + 17], fill=kit + (255,)); d.rectangle([x + 5, y + 6, x + 5, y + 17], fill=tuple(min(255, v + 50) for v in kit) + (255,))
        shadowed(im, x + 13, y + 5, name, WHITE, 1)
        if reds: cards_red(im, x + 13, y + 14, reds)
        shadowed(im, x + w - 7 - sw, y + 6, sc, WHITE, 2)
    else:
        d.rectangle([x + w - 9, y + 6, x + w - 6, y + 17], fill=kit + (255,)); d.rectangle([x + w - 9, y + 6, x + w - 9, y + 17], fill=tuple(min(255, v + 50) for v in kit) + (255,))
        shadowed(im, x + 7, y + 6, sc, WHITE, 2)
        nx = x + w - 13 - text_w(name)
        shadowed(im, nx, y + 5, name, WHITE, 1)
        if reds: cards_red(im, nx, y + 14, reds)


def bug_a(st, W=300, H=60):
    """A: top-left, FC style. [HOME 1][0 AWAY][clock]; the match tag sits on top, stakes underneath"""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); acc = GOLD if st['ranked'] else STEEL
    tag(im, 0, 0, 'RANKED' if st['ranked'] else 'UNRANKED', GOLD if st['ranked'] else DIM)
    if st['ranked']: shadowed(im, 60, 3, st['div'], GOLD, 1)
    y = 13
    team_seg(im, 0, y, 92, (214, 50, 64) if False else acc, st['h'], st['hs'], st['hk'], st['hr'], 'L', st['ranked'])
    team_seg(im, 91, y, 92, acc, st['a'], st['as'], st['ak'], st['ar'], 'R', st['ranked'])
    clock_block(im, 182, y, 74, acc, st['clock'], st['period'], st.get('added'), st['ranked'])
    if st['ranked']: shadowed(im, 2, y + 28, 'WIN +%d   LOSS -%d' % (st['win'], st['loss']), (255, 220, 130), 1)
    return im


def bug_b(st, W=300, H=60):
    """B: top centre, symmetrical. [chip HOME 1][clock][0 AWAY chip]; the tag is centred above, stakes centred below"""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); acc = GOLD if st['ranked'] else STEEL
    cx = W // 2; y = 13
    t = 'RANKED' if st['ranked'] else 'UNRANKED'; tw = text_w(t) + 10
    tag(im, cx - tw // 2, 0, t, GOLD if st['ranked'] else DIM)
    team_seg(im, cx - 37 - 92 + 1, y, 92, acc, st['h'], st['hs'], st['hk'], st['hr'], 'L', st['ranked'])
    team_seg(im, cx + 37 - 1, y, 92, acc, st['a'], st['as'], st['ak'], st['ar'], 'R', st['ranked'])
    clock_block(im, cx - 37, y, 74, acc, st['clock'], st['period'], st.get('added'), st['ranked'])
    if st['ranked']:
        s = 'WIN +%d   LOSS -%d   %s' % (st['win'], st['loss'], st['div']); shadowed(im, cx - text_w(s) // 2, y + 28, s, (255, 220, 130), 1)
    return im


STATES = [
    dict(ranked=False, h='HOME', a='AWAY', hs=0, as_=0, hk=(214, 50, 64), ak=(236, 238, 246), hr=0, ar=0, clock='12:34', period='1ST HALF'),
    dict(ranked=True, div='DIV 3', win=24, loss=18, h='HOME', a='AWAY', hs=2, as_=1, hk=(214, 50, 64), ak=(236, 238, 246), hr=0, ar=1, clock='67:12', period='2ND HALF'),
    dict(ranked=True, div='DIV 3', win=24, loss=18, h='HOME', a='AWAY', hs=2, as_=2, hk=(214, 50, 64), ak=(236, 238, 246), hr=1, ar=1, clock='90:00', period='ET 1ST HALF', added='+3'),
]
for s in STATES: s['as'] = s.pop('as_')


def sheet(fn, path, crop):
    W, H = 960, 3 * 62 + 8
    im = Image.new('RGBA', (W, H), (60, 124, 58, 255)); d = ImageDraw.Draw(im)
    for x in range(0, W, 120): d.rectangle([x, 0, x + 59, H], fill=(66, 132, 62, 255))
    for i, st in enumerate(STATES):
        b = fn(st); im.alpha_composite(b, (crop(b), 4 + i * 62))
    im = im.resize((W * 2, H * 2), Image.NEAREST); im.save(path); return path


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(sheet(bug_a, os.path.join(out, 'scorebug_A.png'), lambda b: 8))
    print(sheet(bug_b, os.path.join(out, 'scorebug_B.png'), lambda b: (960 - b.width) // 2))
