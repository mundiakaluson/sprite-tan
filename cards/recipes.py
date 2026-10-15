"""Illustrated emblem recipes for the cards without a hand scene in cardlib2.EMB. Each recipe takes the category palette and
returns a 56x38 RGBA image. install(cardlib2.EMB) merges them in."""
import math
from PIL import Image, ImageDraw
from emblem import *
from emblem import W_, H_
from emblem2 import *
import cardlib2 as CL

EMB2 = {}
GREYC = GREY_SHIRT
WHITE_ = (244, 244, 250)


def card(*ids):
    def deco(fn):
        for i in ids: EMB2[i] = fn
        return fn
    return deco


def me(a, pal, x, y, pose='stand', f=1): person(a, x, y, pal['light'], pose, f)
def op(a, x, y, pose='stand', f=-1): person(a, x, y, GREYC, pose, f, opp=True)
def gk(a, pal, x, y, pose='stand', f=1): person(a, x, y, pal['main'], pose, f, keeper=True)
def lt(pal): return tuple(pal['light'])
def line(a, pts, col, w=1): ImageDraw.Draw(a).line(pts, fill=tuple(col[:3]) + ((col[3],) if len(col) > 3 else (255,)), width=w)
def sp(a, x, y, s=1): sparkle(ImageDraw.Draw(a), x, y, (255, 240, 160, 255), s)
SKIP_GROUND = [False]
def gnd(a, pal, y=33):
    if not SKIP_GROUND[0]: ground(a, y, pal)


# ====================================================================== PASS
@card('PS01')
def _(pal):
    a = new(); gnd(a, pal)
    carrow(a, bez((14, 24), (22, 24), (34, 24), (43, 24), 12), lt(pal), 2)
    me(a, pal, 7, 33, 'kick'); op(a, 22, 33); op(a, 33, 33); me(a, pal, 48, 33, 'run')
    return ball(a, 15, 31, 3)


@card('PS02')
def _(pal):
    a = new(); gnd(a, pal); pts = bez((13, 26), (20, 2), (36, 2), (45, 22), 24); dots(a, pts, lt(pal))
    op(a, 24, 33); op(a, 33, 33); me(a, pal, 7, 33, 'kick'); me(a, pal, 49, 33, 'run')
    shadow(a, 46, 34, 4, 1.2); return ball(a, 45, 21, 3.5)


@card('PS03')
def _(pal):
    a = new(); gnd(a, pal); speed_lines(a, 38, 20, pal, (1, 0), n=5, length=22, spread=16, seed=4)
    arrow(a, (14, 20), (46, 20), lt(pal), 3, 7); me(a, pal, 6, 33, 'kick'); me(a, pal, 50, 33)
    return ball(a, 34, 20, 4.5, rot=0.3)


@card('PS04')
def _(pal):
    a = new(); gnd(a, pal); carrow(a, bez((12, 28), (14, 8), (22, 8), (26, 18), 12), lt(pal), 2)
    arrow(a, (14, 15), (46, 15), lt(pal), 1, 4, 140)
    me(a, pal, 8, 33, 'kick'); me(a, pal, 29, 33, 'stand'); me(a, pal, 40, 33, 'run')
    carrow(a, bez((34, 26), (38, 26), (40, 30), (43, 29), 10), (255, 255, 255), 1)
    return ball(a, 44, 29, 3)


@card('PS05')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 30, 33, 'stand'); me(a, pal, 8, 33, 'stand')
    arrow(a, (26, 31), (15, 31), lt(pal), 2, 4); star(a, 29, 31, 1.5, 3.5, GOLD, pts=6)
    return ball(a, 21, 31, 3, rot=0.8)


@card('PS06')
def _(pal):
    a = new(); gnd(a, pal); eye(a, 20, 8, 7, slash=True); person(a, 20, 33, pal['light'], 'turn', 1)
    carrow(a, bez((24, 28), (30, 22), (38, 22), (46, 28), 12), lt(pal), 2); me(a, pal, 50, 33)
    return ball(a, 27, 27, 3)


@card('PS07')
def _(pal):
    a = new(); goalframe(a, 34, 4, 53, 21); pts = bez((9, 26), (14, 0), (32, 0), (42, 16), 24); dots(a, pts, lt(pal))
    me(a, pal, 6, 34, 'kick'); me(a, pal, 44, 34, 'header'); op(a, 33, 34, 'stand')
    return ball(a, 41, 14, 3.5)


@card('PS08')
def _(pal):
    a = new(); goalframe(a, 36, 6, 53, 22); gnd(a, pal); speed_lines(a, 30, 25, pal, (1, 0), n=4, length=18, spread=8, seed=6)
    arrow(a, (12, 27), (40, 27), lt(pal), 3, 6); me(a, pal, 6, 34, 'kick'); me(a, pal, 46, 34, 'kick')
    return ball(a, 30, 27, 3.5)


@card('PS09')
def _(pal):
    a = new(); line(a, [(50, 2), (50, 36)], (255, 255, 255, 140), 1); goalframe(a, 34, 2, 49, 14)
    carrow(a, bez((46, 20), (40, 20), (34, 24), (26, 28), 12), lt(pal), 2)
    me(a, pal, 44, 34, 'turn', -1); me(a, pal, 18, 34, 'run')
    return ball(a, 41, 28, 3)


@card('PS10')
def _(pal):
    a = new(); gnd(a, pal, 35); pts = bez((10, 24), (16, 0), (40, 0), (47, 24), 28); dots(a, pts, lt(pal))
    arrow(a, pts[-3], pts[-1], lt(pal), 2, 5); me(a, pal, 6, 35, 'kick'); me(a, pal, 49, 35, 'run')
    return ball(a, pts[14][0], pts[14][1], 4)


@card('PS11')
def _(pal):
    a = new(); gnd(a, pal); pts = bez((14, 22), (22, 0), (38, 2), (48, 18), 22); dots(a, pts, lt(pal))
    me(a, pal, 12, 34, 'kick'); circ_arrows(a, 16, 26, 4, (255, 240, 160), 1, 80)
    return ball(a, 46, 18, 4)


@card('PS12')
def _(pal):
    a = new(); gnd(a, pal); op(a, 28, 34); pts = bez((12, 28), (16, 6), (42, 4), (46, 26), 22); trail(a, pts, pal, 0.6, 2.4)
    me(a, pal, 7, 34, 'kick'); me(a, pal, 50, 34)
    return ball(a, 44, 24, 3.5)


@card('PS13')
def _(pal):
    a = new(); gnd(a, pal); op(a, 27, 34, 'jump'); pts = bez((12, 28), (18, 4), (36, 4), (45, 26), 22); dots(a, pts, lt(pal))
    me(a, pal, 7, 34, 'kick'); me(a, pal, 50, 34); shadow(a, 45, 34, 4, 1.2)
    return ball(a, 44, 24, 3.5)


@card('PS14')
def _(pal):
    a = new(); gnd(a, pal); chevrons(a, 22, 24, lt(pal), 3); me(a, pal, 14, 34, 'run')
    carrow(a, bez((20, 18), (28, 10), (38, 10), (46, 22), 12), (255, 255, 255), 1); me(a, pal, 49, 34)
    return ball(a, 44, 20, 3)


@card('PS15')
def _(pal):
    a = new(); gnd(a, pal); arrow(a, (12, 22), (46, 22), (255, 240, 160), 3, 7)
    op(a, 22, 34); op(a, 33, 34); star(a, 47, 22, 3, 7, GOLD, pts=8, inner=(255, 140, 70, 255)); me(a, pal, 6, 34, 'kick')
    return ball(a, 40, 22, 3.5)


@card('PS16')
def _(pal):
    a = new(); gnd(a, pal)
    for x in (8, 28, 48): me(a, pal, x, 34)
    arrow(a, (12, 24), (22, 24), lt(pal), 2, 4); arrow(a, (32, 24), (42, 24), lt(pal), 2, 4); check(a, 28, 8, (96, 220, 120), 0.9)
    return ball(a, 27, 31, 3)


@card('PS17')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 8, 34); me(a, pal, 46, 34, 'stand', -1)
    arrow(a, (14, 14), (40, 14), lt(pal), 1, 4, 110); arrow(a, (42, 22), (14, 22), lt(pal), 2, 5)
    return ball(a, 27, 22, 3.5)


@card('PS18')
def _(pal):
    a = new(); gnd(a, pal, 35); goalframe(a, 40, 3, 54, 14); pts = bez((10, 28), (18, -4), (38, -4), (47, 22), 28); dots(a, pts, lt(pal))
    me(a, pal, 6, 35, 'kick'); me(a, pal, 47, 35, 'run'); chevrons(a, 22, 20, lt(pal), 3)
    return ball(a, pts[16][0], pts[16][1], 4)


@card('PS19')
def _(pal):
    a = new(); flag(a, 6, 34, (250, 210, 60), 14); goalframe(a, 36, 4, 54, 20); pts = bez((10, 33), (16, 0), (32, -2), (42, 14), 24); dots(a, pts, lt(pal))
    me(a, pal, 44, 34, 'header'); op(a, 34, 34, 'jump'); me(a, pal, 12, 34, 'kick')
    return ball(a, 41, 13, 3.5)


@card('PS20')
def _(pal):
    a = new(); flag(a, 6, 34, (250, 210, 60), 14); gnd(a, pal); me(a, pal, 12, 34, 'kick'); me(a, pal, 26, 34, 'stand', -1); me(a, pal, 46, 34, 'run')
    arrow(a, (18, 30), (22, 30), lt(pal), 2, 4); arrow(a, (30, 20), (42, 20), lt(pal), 1, 4, 140)
    return ball(a, 20, 31, 3)


@card('PS21')
def _(pal):
    a = new(); goalframe(a, 38, 4, 54, 20); gnd(a, pal)
    for x in (16, 22, 28): op(a, x, 34)
    pts = bez((8, 28), (12, 0), (34, -2), (44, 16), 24); dots(a, pts, lt(pal)); me(a, pal, 7, 34, 'kick'); me(a, pal, 46, 34, 'header')
    return ball(a, 42, 14, 3.5)


@card('PS22')
def _(pal):
    a = new(); gnd(a, pal); clock(a, 44, 9, 6, 0.1); speed_lines(a, 36, 26, pal, (1, 0), n=3, length=16, spread=8, seed=2); me(a, pal, 12, 34, 'kick')
    bolt(a, 28, 14, 1.0); op(a, 26, 34, 'stand'); 
    return ball(a, 24, 28, 3.5)


@card('PS23')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 32, 34, 'turn'); me(a, pal, 8, 34, 'kick'); goalframe(a, 38, 4, 54, 18)
    carrow(a, bez((28, 22), (24, 18), (20, 20), (16, 26), 10), lt(pal), 2); arrow(a, (14, 16), (14, 8), (255, 255, 255), 1, 3, 150)
    return ball(a, 29, 26, 3)


@card('PS24')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 22, 34, 'header'); carrow(a, bez((26, 18), (32, 12), (38, 8), (46, 6), 10), lt(pal), 2)
    me(a, pal, 6, 34, 'kick'); star(a, 28, 19, 1.5, 3.5, GOLD, pts=6)
    return ball(a, 47, 7, 3.5)


@card('PS25')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 40, 34, 'run'); chevrons(a, 44, 22, lt(pal), 3); me(a, pal, 8, 34)
    arrow(a, (38, 14), (14, 14), lt(pal), 2, 5); 
    return ball(a, 26, 14, 3.5)



# ====================================================================== DRIBBLE
def rainbow(a, cx, cy, r, pal):
    d = ImageDraw.Draw(a)
    for i, c in enumerate(((236, 84, 76), (250, 210, 60), (96, 220, 120))): d.arc([cx - r + i * 2, cy - r + i * 2, cx + r - i * 2, cy + r - i * 2], 190, 350, fill=c + (255,), width=2)


@card('DR01')
def _(pal):
    a = new(); gnd(a, pal); op(a, 36, 34, 'tackle', -1); me(a, pal, 14, 34, 'run'); circ_arrows(a, 24, 24, 5, (255, 240, 160), 1, 60)
    arrow(a, (30, 14), (40, 14), (236, 84, 76), 2, 4); return ball(a, 24, 31, 3.5)


@card('DR02')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 34, 34, 'stand', -1); arrow(a, (30, 29), (14, 29), lt(pal), 2, 5); circ_arrows(a, 18, 20, 5, (255, 240, 160), 1, 80)
    return ball(a, 26, 31, 3.5)


@card('DR03')
def _(pal):
    a = new(); gnd(a, pal); op(a, 44, 34, 'tackle', -1); me(a, pal, 12, 34, 'run'); circ_arrows(a, 27, 26, 7, lt(pal), 2, 50)
    return ball(a, 27, 26, 4)


@card('DR04')
def _(pal):
    a = new(); gnd(a, pal); arrow(a, (8, 31), (48, 31), lt(pal), 2, 5); op(a, 28, 34, 'wide', -1); me(a, pal, 50, 34, 'run')
    return ball(a, 18, 31, 3.5)


@card('DR05')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 20, 34, 'run'); op(a, 38, 34, 'crouch', -1); arrow(a, (24, 12), (34, 12), (255, 255, 255, 120), 1, 4, 120); arrow(a, (34, 8), (22, 8), lt(pal), 2, 4)
    return ball(a, 29, 32, 3.5)


@card('DR06')
def _(pal):
    a = new(); gnd(a, pal); op(a, 28, 34, 'stand', 1); pts = bez((10, 28), (16, 2), (40, 2), (46, 26), 22); dots(a, pts, lt(pal)); me(a, pal, 6, 34, 'kick'); me(a, pal, 50, 34, 'run')
    return ball(a, 28, 4.5, 3.5, rot=0.9)


@card('DR07')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 28, 34, 'crouch'); arrow(a, (16, 22), (24, 22), lt(pal), 2, 4); arrow(a, (40, 28), (32, 28), lt(pal), 2, 4)
    return ball(a, 26, 32, 3.5)


@card('DR08')
def _(pal):
    a = new(); gnd(a, pal); op(a, 40, 34, 'crouch', -1); pts = bez((8, 28), (18, 28), (26, 14), (30, 26), 16); trail(a, pts, pal, 0.8, 2.4); me(a, pal, 16, 34, 'run'); arrow(a, (34, 10), (44, 10), (236, 84, 76), 2, 4)
    return ball(a, 30, 27, 3.5)


@card('DR09')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 22, 34, 'kick'); carrow(a, bez((30, 28), (36, 20), (26, 16), (14, 26), 14), lt(pal), 2); op(a, 40, 34, 'tackle', -1)
    return ball(a, 30, 30, 3.5)


@card('DR10')
def _(pal):
    a = new(); goalframe(a, 36, 4, 53, 18); gnd(a, pal); me(a, pal, 30, 34, 'kick'); carrow(a, bez((24, 28), (14, 28), (10, 24), (8, 16), 10), lt(pal), 2)
    star(a, 40, 26, 1.5, 3.5, GOLD, pts=6); return ball(a, 32, 33, 3.2)


@card('DR11')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 24, 34, 'tackle'); arrow(a, (32, 30), (46, 30), lt(pal), 2, 5); return ball(a, 31, 31, 3.5)


@card('DR12')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 26, 34, 'turn'); op(a, 44, 34, 'tackle', -1); arrow(a, (30, 24), (38, 24), (255, 255, 255, 140), 1, 4, 140)
    d = ImageDraw.Draw(a); d.polygon([(8, 10), (16, 10), (16, 17), (12, 22), (8, 17)], fill=lt(pal) + (255,)); return ball(a, 12, 32, 3.5)


@card('DR13')
def _(pal):
    a = new(); goalframe(a, 38, 4, 54, 18); gnd(a, pal); me(a, pal, 24, 34, 'turn'); op(a, 12, 34, 'tackle', 1); return ball(a, 29, 32, 3.5)


@card('DR14')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 12, 34, 'run'); pts = [(14, 24), (28, 28), (22, 16), (44, 26)]; line(a, pts, lt(pal), 2); arrow(a, (36, 22), (46, 27), lt(pal), 2, 5)
    return ball(a, 44, 28, 3.5)


@card('DR15')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 12, 34, 'run'); circ_arrows(a, 22, 22, 5, (255, 240, 160), 1, 70); circ_arrows(a, 32, 22, 5, (255, 240, 160), 1, 70); chevrons(a, 38, 28, lt(pal), 3)
    return ball(a, 24, 32, 3.2)


@card('DR16')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 28, 34, 'stand'); op(a, 10, 34, 'tackle', 1); carrow(a, bez((26, 30), (22, 14), (14, 14), (8, 26), 14), lt(pal), 2)
    star(a, 28, 31, 1.5, 3.5, GOLD, pts=6); return ball(a, 22, 20, 3.5)


@card('DR17')
def _(pal):
    a = new(); gnd(a, pal); op(a, 30, 34, 'crouch', 1); op(a, 40, 34, 'crouch', -1); speed_lines(a, 24, 22, pal, (1, 0), n=4, length=16, spread=10, seed=3); me(a, pal, 12, 34, 'run')
    arrow(a, (18, 22), (50, 22), lt(pal), 3, 6); return ball(a, 22, 31, 3.5)


@card('DR18')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 14, 34, 'run'); circ_arrows(a, 28, 20, 6, (255, 240, 160), 1, 70); circ_arrows(a, 40, 20, 6, lt(pal), 1, 70); star(a, 50, 8, 2, 5, GOLD, pts=6)
    return ball(a, 24, 32, 3.2)


@card('DR19')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 20, 34, 'kick'); me(a, pal, 6, 34); arrow(a, (24, 14), (12, 14), (255, 255, 255, 110), 1, 4, 110); op(a, 40, 34, 'tackle', -1); arrow(a, (44, 10), (32, 10), (236, 84, 76), 2, 4)
    return ball(a, 27, 32, 3.5)


@card('DR20')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 14, 34, 'run'); speed_lines(a, 34, 26, pal, (1, 0), n=3, length=12, spread=8, seed=9)
    for i, x in enumerate((26, 34, 42)): disc(ImageDraw.Draw(a), x, 31, 1.5 + i * 0.3, (255, 255, 255, 120 + i * 60))
    return ball(a, 48, 30, 3.5)


@card('DR21')
def _(pal):
    a = new(); gnd(a, pal); op(a, 14, 34, 'tackle', 1); me(a, pal, 30, 34, 'stand'); circ_arrows(a, 30, 20, 10, lt(pal), 2, 80); star(a, 8, 28, 1.5, 3.5, GOLD, pts=6)
    return ball(a, 40, 32, 3.5)


@card('DR22')
def _(pal):
    a = new(); gnd(a, pal); arrow(a, (24, 2), (24, 20), (255, 255, 255, 140), 1, 4, 140); me(a, pal, 24, 34, 'stand'); circ_arrows(a, 34, 20, 6, lt(pal), 1, 80)
    return ball(a, 29, 31, 3.5)


@card('DR23')
def _(pal):
    a = new(); gnd(a, pal); op(a, 20, 34); op(a, 36, 34); pts = bez((6, 26), (16, 34), (28, 12), (50, 26), 22); trail(a, pts, pal, 0.8, 2.4); me(a, pal, 6, 34, 'run')
    return ball(a, 49, 26, 3.5)


@card('DR24')
def _(pal):
    a = new(); gnd(a, pal); op(a, 8, 34, 'crouch'); flame(a, 26, 28, 14, pal); me(a, pal, 32, 34, 'run'); chevrons(a, 40, 20, lt(pal), 3)
    return ball(a, 46, 31, 3.5)


@card('DR25')
def _(pal):
    a = new(); line(a, [(2, 6), (54, 6)], (255, 255, 255, 170), 1); flag(a, 50, 8, (250, 210, 60), 7); me(a, pal, 24, 30, 'run'); chevrons(a, 34, 20, lt(pal), 3)
    return ball(a, 40, 28, 3.5)


@card('DR26')
def _(pal):
    a = new(); gnd(a, pal); op(a, 28, 34, 'stand', 1); rainbow(a, 28, 22, 14, pal); me(a, pal, 8, 34, 'kick'); me(a, pal, 50, 34, 'run')
    return ball(a, 42, 12, 3.5)


@card('DR27')
def _(pal):
    a = new(); gnd(a, pal); op(a, 14, 34, 'tackle', 1); pts = bez((28, 30), (40, 30), (40, 18), (30, 18), 14); trail(a, pts, pal, 1.0, 2.2); me(a, pal, 38, 34, 'stand', -1)
    return ball(a, 29, 18, 3.5)


@card('DR28')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 24, 34, 'tackle'); arrow(a, (34, 24), (22, 24), (255, 255, 255, 140), 2, 4, 140); arrow(a, (24, 18), (46, 18), lt(pal), 2, 5)
    return ball(a, 31, 31, 3.5)


@card('DR29')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 40, 34, 'wide', -1); me(a, pal, 10, 34, 'run'); arrow(a, (46, 31), (16, 31), lt(pal), 2, 5); star(a, 8, 20, 2, 5, GOLD, pts=6)
    return ball(a, 40, 31, 3.2)


@card('DR30')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 28, 34, 'arms_up'); circ_arrows(a, 28, 20, 12, lt(pal), 3, 60)
    for x, y in ((8, 8), (48, 10), (10, 30), (46, 30)): sp(a, x, y, 2)
    return ball(a, 40, 31, 3.2)



# ====================================================================== DEFEND
def burst(a, x, y, s=6): star(a, x, y, s * 0.5, s, GOLD, pts=8, inner=(255, 140, 70, 255))


def dbox(a, x0, y0, x1, y1, col, alpha=200):
    d = ImageDraw.Draw(a); c = tuple(col[:3]) + (alpha,)
    for x in range(x0, x1, 4): d.line([(x, y0), (x + 1, y0)], fill=c); d.line([(x, y1), (x + 1, y1)], fill=c)
    for y in range(y0, y1, 4): d.line([(x0, y), (x0, y + 1)], fill=c); d.line([(x1, y), (x1, y + 1)], fill=c)


@card('DF01')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 16, 34, 'tackle'); op(a, 42, 34, 'run', -1); burst(a, 30, 30, 5); return ball(a, 27, 32, 3)


@card('DF02')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 12, 34, 'slide'); op(a, 42, 34, 'jump', -1); flame(a, 8, 33, 5, pal); burst(a, 30, 31, 5); return ball(a, 27, 31, 3)


@card('DF03')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 14, 34, 'tackle'); op(a, 44, 34, 'run', -1); arrow(a, (32, 24), (40, 14), lt(pal), 2, 4); return ball(a, 29, 31, 3)


@card('DF04')
def _(pal):
    a = new(); gnd(a, pal); op(a, 6, 34, 'kick'); op(a, 50, 34, 'stand', -1); arrow(a, (12, 14), (44, 14), (255, 255, 255, 110), 1, 4, 110); me(a, pal, 28, 34, 'jump'); cross_mark(a, 36, 14, (236, 84, 76), 0.8)
    return ball(a, 28, 10, 3)


@card('DF05')
def _(pal):
    a = new(); goalframe(a, 40, 6, 54, 22); gnd(a, pal); op(a, 8, 34, 'kick'); me(a, pal, 28, 34, 'wide'); arrow(a, (14, 24), (24, 24), (236, 84, 76), 2, 4); return ball(a, 29, 24, 3)


@card('DF06')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 14, 34, 'tackle'); op(a, 38, 34, 'slide', -1); card_icon(a, 46, 10); return ball(a, 24, 31, 3)


@card('DF07')
def _(pal):
    a = new(); gnd(a, pal); op(a, 46, 34, 'run'); me(a, pal, 16, 34, 'run'); chevrons(a, 26, 20, lt(pal), 3); speed_lines(a, 10, 22, pal, (1, 0), n=3, length=10, spread=10, seed=2); return ball(a, 52, 31, 3)


@card('DF08')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 12, 34, 'tackle'); me(a, pal, 44, 34, 'tackle', -1); op(a, 28, 34, 'run'); arrow(a, (14, 8), (22, 8), lt(pal), 2, 4); arrow(a, (42, 8), (34, 8), lt(pal), 2, 4); return ball(a, 31, 32, 3)


@card('DF09')
def _(pal):
    a = new(); line(a, [(2, 10), (54, 10)], (255, 255, 255, 170), 1); gnd(a, pal)
    for x in (10, 24, 38): me(a, pal, x, 34)
    for x in (10, 24, 38): arrow(a, (x, 24), (x, 14), lt(pal), 2, 4)
    flag(a, 50, 34, (250, 210, 60), 12); return a


@card('DF10')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 28, 34, 'crouch'); arrow(a, (24, 14), (12, 14), lt(pal), 2, 4); op(a, 46, 34, 'run', -1); chevrons(a, 36, 22, (255, 255, 255), 2, -1, 3); return ball(a, 40, 32, 3)


@card('DF11')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 12, 34, 'run'); chevrons(a, 22, 20, lt(pal), 3); op(a, 42, 34, 'stand', -1); target(a, 46, 10, 5); return ball(a, 38, 32, 3)


@card('DF12')
def _(pal):
    a = new(); gnd(a, pal); op(a, 36, 34, 'run', 1); me(a, pal, 20, 34, 'stand'); line(a, [(25, 24), (32, 22)], SK, 2); card_icon(a, 48, 10); arrow(a, (40, 14), (30, 14), (236, 84, 76), 1, 4, 180); return a


@card('DF13')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 14, 34, 'run'); op(a, 40, 34, 'crouch', -1); burst(a, 28, 24, 6); chevrons(a, 18, 14, lt(pal), 2); return ball(a, 48, 32, 3)


@card('DF14')
def _(pal):
    a = new(); goalframe(a, 2, 14, 12, 30); pts = bez((18, 28), (22, 0), (44, -2), (50, 20), 24); dots(a, pts, lt(pal)); me(a, pal, 18, 34, 'kick'); return ball(a, pts[14][0], pts[14][1], 3.5)


@card('DF15')
def _(pal):
    a = new(); goalframe(a, 42, 6, 56, 22); gnd(a, pal); op(a, 6, 34, 'kick'); me(a, pal, 30, 34, 'jump'); arrow(a, (12, 22), (24, 22), (236, 84, 76), 2, 4); burst(a, 26, 22, 4); return ball(a, 30, 22, 3)


@card('DF16')
def _(pal):
    a = new(); gnd(a, pal); carrow(a, bez((50, 4), (40, 2), (34, 6), (28, 12), 10), (255, 255, 255, 120), 1); me(a, pal, 24, 34, 'header'); pts = bez((28, 14), (20, 4), (12, 2), (4, 10), 14); carrow(a, pts, lt(pal), 2); return ball(a, 29, 12, 3)


@card('DF17')
def _(pal):
    a = new(); gnd(a, pal); pts = bez((50, 18), (44, 2), (34, 2), (28, 14), 18); dots(a, pts, (255, 255, 255)); me(a, pal, 26, 34, 'jump'); op(a, 8, 34, 'run'); cross_mark(a, 42, 22, (236, 84, 76), 0.9); return ball(a, 28, 14, 3)


@card('DF18')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 12, 34, 'tackle'); op(a, 40, 34, 'run', -1); target(a, 28, 22, 6, (255, 255, 255)); return ball(a, 31, 31, 3)


@card('DF19')
def _(pal):
    a = new(); gnd(a, pal); person(a, 20, 34, lt(pal), 'run', 1); person(a, 14, 34, lt(pal), 'run', 1); op(a, 34, 34, 'run'); chevrons(a, 42, 20, (255, 255, 255), 2); return ball(a, 40, 32, 3)


@card('DF20')
def _(pal):
    a = new(); gnd(a, pal); dbox(a, 6, 6, 36, 34, lt(pal)); me(a, pal, 20, 34); op(a, 48, 34, 'run', -1); arrow(a, (46, 14), (38, 14), (236, 84, 76), 2, 4); return a


@card('DF21')
def _(pal):
    a = new(); goalframe(a, 2, 14, 10, 30); gnd(a, pal)
    for x in (20, 32, 44): me(a, pal, x, 34, 'stand', -1)
    for x in (20, 32, 44): arrow(a, (x, 20), (x - 6, 20), lt(pal), 2, 4)
    return a


@card('DF22')
def _(pal):
    a = new(); gnd(a, pal)
    for x in (10, 24, 38): me(a, pal, x, 34)
    for x in (10, 24, 38): arrow(a, (x + 4, 20), (x + 11, 20), lt(pal), 2, 4)
    chevrons(a, 46, 10, lt(pal), 2, 1, 3); return a


@card('DF23')
def _(pal):
    a = new(); gnd(a, pal); op(a, 6, 34, 'kick'); op(a, 50, 34, 'stand', -1); arrow(a, (12, 12), (44, 12), (255, 255, 255, 110), 1, 4, 110); me(a, pal, 28, 34, 'jump'); eye(a, 28, 4, 6); return ball(a, 28, 14, 3)


@card('DF24')
def _(pal):
    a = new(); gnd(a, pal); op(a, 8, 34, 'run'); me(a, pal, 24, 34, 'wide'); me(a, pal, 48, 34); arrow(a, (14, 22), (44, 22), (255, 255, 255, 100), 1, 4, 100); cross_mark(a, 36, 22, (236, 84, 76), 0.8); return ball(a, 14, 31, 3)


@card('DF25')
def _(pal):
    a = new(); gnd(a, pal); op(a, 28, 34, 'stand'); me(a, pal, 14, 34, 'run'); arrow(a, (30, 14), (46, 6), (255, 255, 255, 110), 1, 4, 110); arrow(a, (30, 18), (48, 20), (255, 255, 255, 110), 1, 4, 110); cross_mark(a, 40, 8, (236, 84, 76), 0.6); cross_mark(a, 42, 20, (236, 84, 76), 0.6); return ball(a, 31, 32, 3)


@card('DF26')
def _(pal):
    a = new(); gnd(a, pal); dbox(a, 4, 6, 52, 34, lt(pal), 120); me(a, pal, 14, 34); me(a, pal, 42, 34, 'stand', -1); circ_arrows(a, 28, 18, 7, lt(pal), 2, 70); return a


@card('DF27')
def _(pal):
    a = new(); goalframe(a, 38, 6, 54, 22); gnd(a, pal); op(a, 34, 34, 'run'); me(a, pal, 22, 34, 'run'); line(a, [(26, 26), (30, 25)], SK, 2); return ball(a, 40, 32, 3)


@card('DF28')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 8, 34, 'slide'); op(a, 38, 34, 'run', -1); sp(a, 6, 12, 2); sp(a, 48, 12, 1); drop(a, 18, 14); return ball(a, 24, 32, 3)


@card('DF29')
def _(pal):
    a = new(); goalframe(a, 2, 14, 10, 30); gnd(a, pal); me(a, pal, 24, 34, 'run'); carrow(a, bez((12, 12), (24, 4), (38, 6), (46, 16), 14), lt(pal), 2); op(a, 48, 34, 'run', -1); return ball(a, 44, 32, 3)


@card('DF30')
def _(pal):
    a = new(); gnd(a, pal)
    for x in (10, 20, 30, 40): me(a, pal, x, 34, 'stand')
    d = ImageDraw.Draw(a); d.polygon([(44, 4), (54, 4), (54, 12), (49, 18), (44, 12)], fill=lt(pal) + (255,)); check(a, 49, 9, (255, 255, 255), 0.5); return a


@card('DF31')
def _(pal):
    a = new(); goalframe(a, 34, 4, 54, 18); dbox(a, 30, 4, 54, 30, lt(pal)); gnd(a, pal); op(a, 44, 34, 'run', -1); me(a, pal, 36, 34, 'run', -1); return ball(a, 24, 31, 3)


@card('DF32')
def _(pal):
    a = new(); goalframe(a, 2, 12, 12, 30); gnd(a, pal); me(a, pal, 14, 34, 'stand'); carrow(a, bez((18, 30), (26, 20), (36, 14), (46, 12), 12), lt(pal), 2); star(a, 14, 31, 1.5, 3.5, GOLD, pts=6); return ball(a, 26, 20, 3)


@card('DF33')
def _(pal):
    a = new(); line(a, [(2, 6), (54, 6)], (255, 255, 255, 170), 1); gnd(a, pal); op(a, 36, 28, 'run', 1); me(a, pal, 20, 34, 'run'); arrow(a, (36, 12), (24, 20), lt(pal), 2, 5); return ball(a, 44, 26, 3)


@card('DF34')
def _(pal):
    a = new(); gnd(a, pal); op(a, 28, 34, 'crouch', 1); me(a, pal, 10, 34, 'tackle'); me(a, pal, 46, 34, 'tackle', -1); arrow(a, (14, 10), (22, 10), lt(pal), 2, 4); arrow(a, (42, 10), (34, 10), lt(pal), 2, 4); return ball(a, 33, 32, 3)


@card('DF35')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 12, 34, 'slide'); op(a, 38, 34, 'jump', -1); burst(a, 28, 28, 8); line(a, [(22, 14), (26, 20), (24, 24)], (255, 255, 255), 1); return ball(a, 44, 33, 3)


# ====================================================================== KEEPER
def kgoal(a, big=True): goalframe(a, 4, 3, 52, 26 if big else 20)


@card('GK01')
def _(pal):
    a = new(); kgoal(a); gnd(a, pal, 35); gk(a, pal, 28, 35, 'crouch'); chevrons(a, 12, 28, lt(pal), 2, 1, 3); chevrons(a, 44, 28, lt(pal), 2, -1, 3); return a


@card('GK02')
def _(pal):
    a = new(); kgoal(a); gnd(a, pal, 35); gk(a, pal, 24, 35, 'dive'); pts = bez((50, 34), (52, 12), (46, 6), (40, 8), 14); trail(a, pts, pal, 0.6, 2.2); return ball(a, 40, 9, 3.5)


@card('GK03')
def _(pal):
    a = new(); gnd(a, pal, 35); op(a, 46, 35, 'kick', -1); gk(a, pal, 24, 35, 'dive'); line(a, [(6, 14), (44, 30)], (255, 255, 255, 80), 1); line(a, [(6, 30), (44, 30)], (255, 255, 255, 80), 1); return ball(a, 40, 33, 3)


@card('GK04')
def _(pal):
    a = new(); gnd(a, pal, 35); carrow(a, bez((52, 4), (44, 2), (38, 6), (32, 12), 10), (255, 255, 255, 120), 1); gk(a, pal, 28, 35, 'jump'); carrow(a, bez((30, 14), (22, 4), (14, 4), (6, 10), 12), lt(pal), 2); burst(a, 31, 14, 4); return ball(a, 33, 13, 3)


@card('GK05')
def _(pal):
    a = new(); gnd(a, pal, 35); carrow(a, bez((52, 4), (44, 0), (36, 4), (30, 10), 10), (255, 255, 255, 120), 1); gk(a, pal, 28, 35, 'jump'); check(a, 44, 24, (96, 220, 120), 0.8); return ball(a, 30, 10, 3.5)


@card('GK06')
def _(pal):
    a = new(); goalframe(a, 2, 16, 10, 32); gnd(a, pal, 35); gk(a, pal, 24, 35, 'run'); chevrons(a, 32, 22, lt(pal), 3); op(a, 50, 35, 'run', -1); arrow(a, (14, 8), (44, 8), (255, 255, 255, 110), 1, 4, 110); return ball(a, 42, 33, 3)


@card('GK07')
def _(pal):
    a = new(); gnd(a, pal, 35); gk(a, pal, 10, 35, 'arms_up'); me(a, pal, 48, 35, 'run'); pts = bez((14, 12), (24, 4), (34, 4), (44, 14), 16); carrow(a, pts, lt(pal), 2); return ball(a, 14, 12, 3)


@card('GK08')
def _(pal):
    a = CL.R_glove(pal); a = ball(a, 29, 14, 5, rot=0.5); check(a, 46, 8, (96, 220, 120), 0.7); return a


@card('GK09')
def _(pal):
    a = new(); kgoal(a); gnd(a, pal, 35); gk(a, pal, 22, 35, 'dive'); pts = [(48 - i * 1.3, 31 + i * 0.1) for i in range(14)]; trail(a, pts, pal, 0.6, 2.2); return ball(a, 30, 32, 3.5)


@card('GK10')
def _(pal):
    a = new(); line(a, [(2, 8), (54, 8)], (255, 255, 255, 220), 2); gnd(a, pal, 35); gk(a, pal, 22, 35, 'jump'); carrow(a, bez((26, 12), (32, 8), (40, 0), (48, 4), 10), lt(pal), 2); return ball(a, 28, 4, 3.5)


@card('GK11')
def _(pal):
    a = new(); goalframe(a, 2, 4, 14, 24); gnd(a, pal, 35); gk(a, pal, 30, 35, 'run', -1); arrow(a, (24, 12), (14, 12), lt(pal), 2, 4); pts = bez((50, 14), (42, 0), (30, 0), (20, 10), 16); dots(a, pts, (255, 255, 255)); return ball(a, 46, 10, 3.5)


@card('GK12')
def _(pal):
    a = new(); gnd(a, pal, 35); op(a, 46, 35, 'run', -1); person(a, 20, 35, pal['main'], 'arms_up', 1, keeper=True); line(a, [(14, 22), (6, 16)], GLOVE, 2); return ball(a, 40, 33, 3)


@card('GK13')
def _(pal):
    a = new(); gnd(a, pal, 35); gk(a, pal, 24, 35, 'wide'); arrow(a, (36, 20), (46, 14), lt(pal), 2, 4); burst(a, 32, 20, 3); return ball(a, 31, 22, 3)


@card('GK14')
def _(pal):
    a = new(); goalframe(a, 2, 4, 52, 22); gnd(a, pal, 35); gk(a, pal, 24, 35, 'tackle'); burst(a, 40, 31, 4); arrow(a, (44, 30), (50, 20), lt(pal), 2, 4); return ball(a, 42, 32, 3)


@card('GK15')
def _(pal):
    a = new(); goalframe(a, 2, 20, 12, 34); gnd(a, pal, 35); gk(a, pal, 12, 35, 'arms_up')
    for x in (26, 36, 46): me(a, pal, x, 35)
    for x in (26, 36, 46): arrow(a, (x, 22), (x, 12), lt(pal), 2, 4)
    return a


@card('GK16')
def _(pal):
    a = new(); gnd(a, pal, 35); gk(a, pal, 8, 35, 'kick'); pts = bez((14, 30), (20, -4), (42, -4), (47, 22), 26); dots(a, pts, lt(pal)); me(a, pal, 49, 35, 'run'); return ball(a, pts[14][0], pts[14][1], 3.5)


@card('GK17')
def _(pal):
    a = new(); gnd(a, pal, 35); gk(a, pal, 12, 35, 'crouch'); me(a, pal, 44, 35, 'stand', -1); arrow(a, (20, 31), (36, 31), lt(pal), 2, 4); return ball(a, 22, 33, 3)


@card('GK18')
def _(pal):
    a = new(); gnd(a, pal, 35); gk(a, pal, 8, 35, 'arms_up'); pts = bez((10, 14), (22, -2), (38, -2), (48, 12), 20); dots(a, pts, lt(pal)); me(a, pal, 49, 35, 'run'); return ball(a, 10, 14, 3)


@card('GK19')
def _(pal):
    a = new(); goalframe(a, 2, 16, 10, 32); gnd(a, pal, 35); gk(a, pal, 24, 35, 'run'); eye(a, 40, 8, 6); arrow(a, (30, 14), (50, 14), (255, 255, 255, 110), 1, 4, 110); op(a, 50, 35, 'run', -1); return a


@card('GK20')
def _(pal):
    a = new(); kgoal(a); gnd(a, pal, 35); gk(a, pal, 24, 35, 'dive'); bolt(a, 46, 14, 1.2); burst(a, 38, 12, 4); return ball(a, 38, 12, 3)


@card('GK21')
def _(pal):
    a = new(); dbox(a, 8, 4, 48, 34, lt(pal)); gnd(a, pal, 35); gk(a, pal, 28, 35, 'arms_up'); op(a, 12, 35, 'run'); op(a, 44, 35, 'run', -1); star(a, 28, 6, 2, 5, GOLD, pts=6); return a


@card('GK22')
def _(pal):
    a = new(); line(a, [(6, 3), (6, 28)], (255, 255, 255, 220), 2); line(a, [(6, 3), (50, 3)], (255, 255, 255, 120), 1); gnd(a, pal, 35); gk(a, pal, 14, 35, 'crouch'); d = ImageDraw.Draw(a); d.polygon([(34, 8), (44, 8), (44, 16), (39, 22), (34, 16)], fill=lt(pal) + (255,)); return a


@card('GK23')
def _(pal):
    a = new(); kgoal(a); line(a, [(52, 3), (52, 26)], (255, 255, 255, 255), 2); gnd(a, pal, 35); gk(a, pal, 16, 35, 'run'); arrow(a, (24, 14), (44, 14), lt(pal), 2, 5); return a


@card('GK24')
def _(pal):
    a = new(); kgoal(a); gnd(a, pal, 35); gk(a, pal, 22, 35, 'dive'); sp(a, 40, 6, 2); pts = bez((52, 30), (50, 8), (46, 4), (38, 8), 14); trail(a, pts, pal, 0.6, 2.2); return ball(a, 37, 8, 3.5)


@card('GK25')
def _(pal):
    a = new(); goalframe(a, 2, 4, 20, 24); gnd(a, pal, 35); gk(a, pal, 16, 35, 'jump'); carrow(a, bez((22, 20), (30, 12), (38, 10), (46, 14), 10), lt(pal), 2); op(a, 48, 35, 'run', -1); burst(a, 22, 20, 4); return ball(a, 22, 20, 3)



# ====================================================================== SUPPORT
def txt(a, x, y, s, col=(255, 255, 255, 255), scale=1):
    from cardlib import draw_text
    draw_text(a, x, y, s, col, scale)


def swirl(a, x, y, col, r=5, turns=1.6):
    d = ImageDraw.Draw(a); pts = [(x + math.cos(t) * r * (1 - t / (turns * 2 * math.pi) * 0.6), y + math.sin(t) * r * (1 - t / (turns * 2 * math.pi) * 0.6)) for t in [i * 0.3 for i in range(int(turns * 21))]]
    d.line(pts, fill=tuple(col[:3]) + (255,), width=1)


@card('SP01')
def _(pal):
    a = new(); d = ImageDraw.Draw(a)
    for ox in (0, 12):
        d.line([(16 + ox, 4), (22 + ox, 30)], fill=(255, 150, 50, 255), width=7)
        for k in range(3): d.line([(14 + ox + k * 2, 10 + k * 7), (21 + ox + k * 2, 11 + k * 7)], fill=(40, 24, 24, 255), width=2)
        d.line([(20 + ox, 31), (28 + ox, 31)], fill=(28, 28, 40, 255), width=3)
    sp(a, 8, 8, 2); sp(a, 48, 22, 2); chevrons(a, 36, 18, lt(pal), 2, 1, 3); return a


@card('SP02')
def _(pal):
    a = new(); gnd(a, pal); pts = bez((6, 30), (14, 2), (30, 2), (42, 26), 20); dots(a, pts, lt(pal)); me(a, pal, 26, 22, 'jump'); chevrons(a, 44, 12, lt(pal), 2); shadow(a, 26, 34, 6); return a


@card('SP03')
def _(pal): return CL.EXTRA['flex'](pal)


@card('SP04')
def _(pal):
    a = new(); boot(a, 24, 24, 1); star(a, 44, 8, 2, 6, GOLD, pts=6); sp(a, 10, 8, 2); sp(a, 46, 28, 1); line(a, [(32, 14), (38, 10)], (255, 255, 255, 200), 1); return a


@card('SP05')
def _(pal):
    a = new(); d = ImageDraw.Draw(a)
    for r_ in (16, 11, 6): d.ellipse([28 - r_, 19 - r_, 28 + r_, 19 + r_], outline=(120, 230, 150, 255 - r_ * 8))
    d.pieslice([12, 3, 44, 35], 290, 350, fill=(120, 230, 150, 120)); d.line([(28, 19), (42, 8)], fill=(160, 255, 190, 255), width=1)
    for x, y in ((18, 12), (36, 26), (24, 28)): disc(d, x, y, 1.5, (255, 240, 160, 255))
    return ball(a, 34, 14, 3)


@card('SP06')
def _(pal):
    a = new(); d = ImageDraw.Draw(a); d.ellipse([16, 8, 40, 32], fill=SK); d.pieslice([16, 6, 40, 30], 180, 360, fill=(52, 36, 28, 255))
    d.arc([22, 18, 26, 21], 200, 340, fill=(30, 20, 20, 255), width=1); d.arc([30, 18, 34, 21], 200, 340, fill=(30, 20, 20, 255), width=1); d.arc([24, 22, 32, 28], 20, 160, fill=(150, 80, 70, 255), width=1)
    for y in (6, 11): d.arc([4, y, 14, y + 6], 180, 360, fill=lt(pal) + (255,)); d.arc([42, y, 52, y + 6], 180, 360, fill=lt(pal) + (255,))
    return outline(a)


@card('SP07')
def _(pal):
    a = new(); d = ImageDraw.Draw(a)
    for k, (x, y) in enumerate(((10, 10), (14, 20), (10, 30))): d.line([(x, y), (x + 26, y)], fill=(230, 240, 255, 255 - k * 40), width=1); swirl(a, x + 30, y - 2, (230, 240, 255), 4, 1.3)
    heart(a, 46, 22, 5); battery(a, 36, 6, 0.9, w=12, h=6); return a


@card('SP08')
def _(pal):
    a = new(); flame(a, 36, 22, 24, pal); a = ball(a, 40, 22, 6, rot=0.3); star(a, 14, 8, 2, 5, GOLD, pts=6); star(a, 12, 32, 1, 4, GOLD, pts=6); return a


@card('SP09')
def _(pal):
    a = new(); d = ImageDraw.Draw(a)
    for i, r_ in enumerate((17, 13)): d.ellipse([28 - r_, 19 - r_, 28 + r_, 19 + r_], outline=lt(pal) + (120 - i * 40,))
    clock(a, 28, 19, 8, 0.12); arrow(a, (44, 6), (50, 12), lt(pal), 2, 4); return a


@card('SP10')
def _(pal):
    a = new(); clock(a, 28, 19, 6, 0.0); circ_arrows(a, 28, 19, 12, lt(pal), 2, 60); return a


@card('SP11')
def _(pal):
    a = new(); d = ImageDraw.Draw(a); d.pieslice([8, 8, 48, 48], 180, 360, fill=(40, 40, 70, 255)); d.pieslice([8, 8, 48, 48], 300, 360, fill=(236, 84, 76, 255)); d.pieslice([12, 12, 44, 44], 180, 360, fill=(30, 30, 56, 255))
    d.line([(28, 28), (40, 12)], fill=(255, 255, 255, 255), width=2); txt(a, 21, 4, 'X2', (255, 240, 160, 255), 2); return a


@card('SP12')
def _(pal):
    a = new(); chain(a, 8, 22, 5, (220, 226, 245)); txt(a, 18, 6, '+2S', (255, 240, 160, 255), 2); return a


@card('SP13')
def _(pal):
    a = new(); battery(a, 28, 16, 0.85, w=26, h=14); arrow(a, (20, 28), (36, 28), (255, 255, 255, 140), 1, 4, 140); txt(a, 14, 32, 'SLOW', (255, 240, 160, 255)); return a


@card('SP14')
def _(pal):
    g = CL.EXTRA['glove'](pal).resize((39, 27), Image.NEAREST); a = new(); a.alpha_composite(g, (8, 8)); target(a, 46, 10, 5, (96, 220, 120)); return a


@card('SP15')
def _(pal):
    a = new(); d = ImageDraw.Draw(a); d.polygon([(18, 8), (38, 8), (42, 34), (14, 34)], fill=lt(pal) + (255,)); d.polygon([(22, 8), (34, 8), (28, 14)], fill=SK)
    a = outline(a); arrow(a, (12, 20), (4, 20), (255, 255, 255), 2, 4); arrow(a, (44, 20), (52, 20), (255, 255, 255), 2, 4); return a


@card('SP16')
def _(pal):
    a = new(); snow(a, 28, 19, 12, (190, 230, 255)); clock(a, 44, 8, 5, 0.0); drop(a, 10, 12); drop(a, 12, 30, (120, 200, 255)); return a


@card('SP17')
def _(pal):
    a = new(); gnd(a, pal)
    for x, y in ((8, 14), (20, 8), (32, 14), (44, 8)): note(a, x, y, lt(pal))
    pts = bez((6, 28), (16, 18), (30, 38), (48, 26), 16); trail(a, pts, pal, 0.8, 2.0); return ball(a, 48, 26, 4)


@card('SP18')
def _(pal):
    a = new(); boot(a, 28, 22, 1); chevrons(a, 8, 18, lt(pal), 3, 1, 4); speed_lines(a, 14, 24, pal, (1, 0), n=3, length=10, spread=12, seed=4); star(a, 46, 6, 1.5, 4, GOLD, pts=6); return a


@card('SP19')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 14, 34, 'run'); op(a, 38, 34, 'run', 1); arrow(a, (38, 14), (50, 14), (236, 84, 76), 2, 5); me(a, pal, 24, 34, 'stand'); return a


@card('SP20')
def _(pal):
    a = new(); gnd(a, pal); flag(a, 8, 34, (250, 210, 60), 16); me(a, pal, 22, 34, 'arms_up'); me(a, pal, 34, 34, 'arms_up'); me(a, pal, 46, 34, 'arms_up'); star(a, 28, 6, 2, 5, GOLD, pts=6); return a


@card('SP21')
def _(pal):
    a = new(); d = ImageDraw.Draw(a); d.rectangle([14, 10, 34, 26], fill=(250, 210, 60, 255)); d.rectangle([14, 10, 34, 12], fill=(255, 240, 160, 255)); a = outline(a).copy()
    txt(a, 21, 14, 'C', (34, 28, 60, 255), 3); arrow(a, (38, 14), (52, 8), lt(pal), 2, 4); arrow(a, (38, 22), (52, 28), lt(pal), 2, 4); return a


@card('SP22')
def _(pal):
    a = new(); gnd(a, pal); sun(a, 44, 9, 5); me(a, pal, 16, 34, 'run'); chevrons(a, 26, 22, lt(pal), 2); drop(a, 8, 12); return a


@card('SP23')
def _(pal):
    a = new(); circ_arrows(a, 28, 19, 11, lt(pal), 2, 60); a = ball(a, 28, 19, 5); check(a, 46, 8, (96, 220, 120), 0.7); return a


@card('SP24')
def _(pal):
    a = new(); eye(a, 28, 14, 14, (255, 200, 80)); me(a, pal, 28, 36, 'stand'); sp(a, 8, 8, 2); sp(a, 48, 8, 2); sp(a, 28, 3, 1); return a


@card('SP25')
def _(pal):
    a = new(); d = ImageDraw.Draw(a)
    for ox in (0, 12): d.line([(18 + ox, 6), (20 + ox, 30)], fill=SK, width=6); d.line([(18 + ox, 31), (26 + ox, 31)], fill=(28, 28, 40, 255), width=3)
    a = outline(a); chevrons(a, 42, 26, lt(pal), 2, 1, 3); drop(a, 8, 16); sp(a, 46, 6, 2); return a


@card('SP26')
def _(pal):
    a = new(); gnd(a, pal); op(a, 44, 34, 'run', -1); person(a, 24, 34, lt(pal), 'run', 1); pts = bez((12, 28), (20, 12), (32, 12), (40, 26), 14); dots(a, pts, lt(pal)); me(a, pal, 10, 34, 'stand')
    return a


@card('SP27')
def _(pal):
    a = new(); txt(a, 18, 4, '2', lt(pal) + (255,), 6); a = ball(a, 12, 30, 4); a = ball(a, 28, 30, 4); arrow(a, (18, 30), (22, 30), (255, 255, 255), 1, 3); arrow(a, (34, 30), (50, 30), lt(pal), 2, 4); return a


@card('SP28')
def _(pal):
    a = new(); d = ImageDraw.Draw(a); d.polygon([(18, 4), (38, 4), (38, 20), (28, 34), (18, 20)], fill=lt(pal) + (255,)); a = outline(a); star(a, 28, 16, 2, 6, (255, 140, 70, 255), pts=6)
    boot(a, 46, 30, -1, (236, 240, 252)); return a


@card('SP29')
def _(pal):
    a = new(); d = ImageDraw.Draw(a); d.ellipse([14, 5, 42, 33], fill=(240, 244, 252, 255)); a = outline(a); check(a, 28, 20, (96, 220, 120), 1.6); line(a, [(4, 30), (12, 34)], (255, 255, 255, 160), 2); return a


@card('SP30')
def _(pal):
    a = new(); a.alpha_composite(wings(a, 22, 20, pal, 0.55)); boot(a, 30, 24, 1); chevrons(a, 44, 8, lt(pal), 2, 1, 3); sp(a, 8, 8, 2); return a


# ====================================================================== TITAN
@card('TT01')
def _(pal):
    a = new(); gnd(a, pal); op(a, 22, 34); op(a, 34, 34); op(a, 46, 34, 'stand', -1); line(a, [(4, 30), (18, 12), (26, 26), (36, 8), (44, 22), (52, 10)], (255, 240, 120), 2); bolt(a, 8, 14, 1.0); me(a, pal, 6, 34, 'run'); return ball(a, 50, 10, 4)


@card('TT02')
def _(pal): return CL.R_gravity(pal)


@card('TT03')
def _(pal):
    a = new(); a.alpha_composite(wings(a, 28, 19, pal, 0.8)); eye(a, 28, 19, 12, (255, 200, 80))
    d = ImageDraw.Draw(a)
    for i, x in enumerate((10, 20, 36, 46)): d.rectangle([x - 3, 29, x + 3, 36], fill=(240, 240, 250, 255), outline=(14, 12, 26, 255))
    return a


@card('TT04')
def _(pal):
    a = new(); gnd(a, pal); op(a, 20, 34, 'crouch'); op(a, 32, 34, 'crouch'); op(a, 44, 34, 'crouch', -1); hourglass(a, 28, 10); pts = bez((4, 28), (14, 14), (22, 34), (36, 22), 16); trail(a, pts, pal, 0.8, 2.2); me(a, pal, 6, 34, 'run'); return ball(a, 48, 28, 3)


@card('TT05')
def _(pal):
    a = new(); goalframe(a, 34, 22, 54, 36); m = new(); person(m, 28, 30, pal['light'], 'jump', 1); m = m.rotate(150, resample=Image.NEAREST, center=(28, 20)); a.alpha_composite(m)
    star(a, 28, 8, 2, 6, GOLD, pts=6); arrow(a, (30, 12), (44, 26), lt(pal), 2, 5); return ball(a, 28, 6, 4)


@card('TT06')
def _(pal):
    a = new(); gnd(a, pal); clock(a, 28, 12, 8, 0.0); me(a, pal, 10, 34, 'run'); op(a, 46, 34, 'run', -1); snow(a, 8, 8, 4); snow(a, 48, 10, 4); return ball(a, 28, 32, 4)


@card('TT07')
def _(pal):
    a = new(); gnd(a, pal); flame(a, 30, 24, 26, pal); me(a, pal, 36, 34, 'run'); chevrons(a, 44, 14, lt(pal), 3); return a


@card('TT08')
def _(pal):
    a = new(); d = ImageDraw.Draw(a)
    for row in range(4):
        for k in range(5): x = 4 + k * 10 + (row % 2) * 5; d.rectangle([x, 6 + row * 7, x + 8, 12 + row * 7], fill=(150, 158, 190, 255), outline=(14, 12, 26, 255))
    d2 = ImageDraw.Draw(a); d2.polygon([(22, 8), (34, 8), (34, 20), (28, 28), (22, 20)], fill=lt(pal) + (255,), outline=(14, 12, 26, 255)); return a


@card('TT09')
def _(pal):
    a = new(); gnd(a, pal); op(a, 28, 34); me(a, pal, 6, 34, 'kick'); me(a, pal, 50, 34, 'stand', -1)
    for i, r_ in enumerate((6, 4)): ImageDraw.Draw(a).ellipse([28 - r_ - 8, 24 - r_, 28 + r_ + 8, 24 + r_], outline=lt(pal) + (90,))
    arrow(a, (12, 22), (44, 22), (200, 160, 255), 2, 5); return ball(a, 28, 22, 4, rot=0.3)


@card('TT10')
def _(pal):
    a = new(); goalframe(a, 44, 8, 55, 22); d = ImageDraw.Draw(a); d.line([(2, 36), (54, 36)], fill=lt(pal) + (90,)); pts = bez((6, 32), (2, 2), (50, 0), (46, 16), 30); trail(a, pts, pal, 0.5, 2.6); me(a, pal, 6, 36, 'kick'); return ball(a, 46, 16, 3.5)


@card('TT11')
def _(pal):
    a = new(); gnd(a, pal); flame(a, 44, 12, 26, pal); me(a, pal, 18, 34, 'header'); return ball(a, 25, 11, 4)


@card('TT12')
def _(pal):
    a = new(); kgoal(a); gnd(a, pal, 35); gk(a, pal, 24, 35, 'dive'); d = ImageDraw.Draw(a); d.line([(22, 28), (26, 24)], fill=(255, 255, 255, 220), width=1)
    star(a, 40, 12, 3, 8, (255, 255, 255, 255), pts=8); return ball(a, 40, 12, 4)


@card('TT13')
def _(pal):
    a = new(); gnd(a, pal, 33); me(a, pal, 12, 34, 'slide'); op(a, 38, 28, 'jump', -1); op(a, 48, 26, 'jump', -1); line(a, [(4, 36), (14, 32), (20, 36), (30, 31), (40, 36)], (255, 255, 255), 1); rings(a, 28, 35, pal, 3, 5, 0.3); burst(a, 28, 30, 5); return a


@card('TT14')
def _(pal):
    a = new(); gnd(a, pal); a.alpha_composite(wings(a, 26, 18, pal, 0.5)); me(a, pal, 26, 34, 'run'); circ_arrows(a, 10, 16, 5, (230, 240, 255), 1, 70); circ_arrows(a, 46, 22, 5, (230, 240, 255), 1, 70); return ball(a, 40, 32, 3)


@card('TT15')
def _(pal):
    a = new(); goalframe(a, 40, 14, 55, 34); flame(a, 36, 12, 30, pal); a = ball(a, 40, 14, 5, rot=0.3); star(a, 46, 22, 2, 6, GOLD, pts=8); sp(a, 8, 24, 2); return a


@card('TT16')
def _(pal):
    a = new(); gnd(a, pal); me(a, pal, 8, 34, 'kick'); me(a, pal, 28, 34); me(a, pal, 48, 34, 'stand', -1); line(a, [(12, 12), (18, 6), (22, 14), (28, 8)], (255, 240, 120), 2); line(a, [(30, 8), (36, 14), (40, 6), (46, 12)], (255, 240, 120), 2); return ball(a, 28, 8, 4)


@card('TT17')
def _(pal):
    a = new(); d = ImageDraw.Draw(a)
    for r_, c in ((14, (60, 24, 100, 255)), (10, (30, 12, 56, 255)), (5, (6, 4, 14, 255))): d.ellipse([28 - r_, 19 - r_ * 0.6, 28 + r_, 19 + r_ * 0.6], fill=c)
    rings(a, 28, 19, pal, 3, 4, 0.5); op(a, 8, 34, 'run'); op(a, 48, 34, 'run', -1); arrow(a, (14, 22), (22, 20), lt(pal), 2, 4); arrow(a, (44, 22), (34, 20), lt(pal), 2, 4); return a


@card('TT18')
def _(pal):
    a = new(); gnd(a, pal); line(a, [(28, 2), (28, 36)], (255, 255, 255, 200), 1); me(a, pal, 14, 34, 'kick'); person(a, 42, 34, pal['light'], 'kick', -1); sp(a, 28, 6, 2); a = ball(a, 20, 32, 3); return a


@card('TT19')
def _(pal):
    a = new(); heart(a, 24, 20, 11); heart(a, 40, 16, 6, (255, 150, 170)); sp(a, 8, 8, 2); sp(a, 48, 30, 2); battery(a, 44, 30, 1.0, w=12, h=6); return a


@card('TT20')
def _(pal):
    a = new(); gnd(a, pal); flame(a, 24, 31, 14, pal); me(a, pal, 28, 34, 'slide'); op(a, 46, 34, 'run', -1); chevrons(a, 8, 12, lt(pal), 3); cross_mark(a, 6, 28, (236, 84, 76), 0.7); return ball(a, 50, 34, 3)


@card('TT21')
def _(pal):
    a = new(); gnd(a, pal, 35); flame(a, 8, 6, 14, pal); pts = bez((6, 2), (12, 2), (26, 8), (34, 28), 16); trail(a, pts, pal, 0.8, 3.0); rings(a, 34, 34, pal, 3, 4, 0.3); me(a, pal, 46, 35, 'jump'); return ball(a, 34, 27, 5, rot=0.4)


@card('TT22')
def _(pal):
    a = new(); goalframe(a, 14, 4, 42, 24); target(a, 28, 14, 9, (236, 84, 76)); gnd(a, pal); me(a, pal, 6, 34, 'kick'); return ball(a, 18, 30, 3.5)


@card('TT23')
def _(pal):
    a = new(); gnd(a, pal)
    for x, y in ((10, 34), (24, 30), (38, 30), (50, 34)): me(a, pal, x, y)
    line(a, [(10, 22), (24, 18), (38, 18), (50, 22), (24, 18)], (255, 240, 160, 180), 1); star(a, 28, 6, 2, 5, GOLD, pts=6); return a


@card('TT24')
def _(pal):
    a = new(); clock(a, 28, 19, 8, 0.75); circ_arrows(a, 28, 19, 14, lt(pal), 1, 60); gnd(a, pal, 35); me(a, pal, 8, 35, 'kick'); return ball(a, 46, 30, 4)


@card('TT25')
def _(pal):
    a = new(); clock(a, 12, 12, 6, 0.3); clock(a, 30, 24, 7, 0.6); clock(a, 46, 10, 5, 0.9); line(a, [(18, 18), (22, 14), (24, 26)], (255, 240, 120), 2); bolt(a, 38, 18, 1.0); sp(a, 6, 30, 2); sp(a, 50, 28, 2); return a


def fit(a, big=2):
    """cards that used to show mini footballers: drop the ground line, centre what is left and double it when it is small, so the emblem reads at a glance"""
    import numpy as np
    bb = a.getbbox()
    if not bb: return a
    w, h = bb[2] - bb[0], bb[3] - bb[1]; crop = a.crop(bb); k = max(1, min(big, 50 // max(1, w), 26 // max(1, h)))
    if k > 1: crop = crop.resize((w * k, h * k), Image.NEAREST)
    out = Image.new('RGBA', a.size, (0, 0, 0, 0)); out.alpha_composite(crop, ((a.width - crop.width) // 2, min(a.height - crop.height, max(0, 22 - crop.height // 2)))); return out


def install(emb):
    emb.update(EMB2)
    import emblem2 as _e2
    def wrap(fn):
        def g(pal):
            _e2.COUNT[0] = 0; a = fn(pal)
            if _e2.COUNT[0] == 0: return a
            SKIP_GROUND[0] = True
            try: _e2.COUNT[0] = 0; a = fn(pal)
            finally: SKIP_GROUND[0] = False
            return fit(a)
        return g
    for k in list(emb): emb[k] = wrap(emb[k])
