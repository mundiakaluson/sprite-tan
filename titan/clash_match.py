"""CLASH in the match view (no new screen): the same TV camera pushes in on the duel, both players snap into the clash lunge (cl01_clash_reach)
over the ball, their auras (team colours) meet at the ball with sparks, a timer ring burns down on the grass while the cards are picked, small
card chips flip on the reveal, one impact, then the camera eases back out while the result plays (here: the carrier hurdles the defender's slide,
cl02_clash_hurdle, leaving faint afterimages). Run:  python titan/clash_match.py  -> export/skills/clash_match.gif (+ /tmp/clash_match_sheet.png)"""
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import engine as E
from engine import P, unit, lerp, clamp, smooth, ak, root_fwd, ground, VW, VH
import fx

HOME, AWAY = 'home', 'away'
RED = [(255, 236, 170), (255, 170, 70), (235, 90, 40)]
BLUE = [(225, 245, 255), (130, 200, 255), (60, 120, 230)]
BALL = P(210, 122)
A_AT, D_AT = BALL + P(-9.5, 0.4), BALL + P(9.5, -0.4)          # where each stands in the lunge (toe on the ball)

T_HIT, T_SNAP = 16, 21          # the moment they meet, fully zoomed
T_PICK = 44                     # your pick
T_REV = 62                      # reveal
T_RES = 70                      # result plays
T_BACK = 96                     # back to normal play
N = 116


def zoom_at(i):
    if i < T_HIT: return 2.6
    if i < T_SNAP: return lerp(2.6, 5.2, smooth((i - T_HIT) / (T_SNAP - T_HIT)))
    if i < T_RES: return 5.2 + 0.25 * smooth((i - T_SNAP) / (T_REV - T_SNAP))          # creeps in while it grinds
    if i < T_RES + 12: return lerp(5.45, 4.2, smooth((i - T_RES) / 12))                  # stays close for the hurdle
    return lerp(4.2, 2.6, smooth((i - T_RES - 12) / (T_BACK - T_RES - 6)))


def heat_at(i):
    return clamp((i - T_SNAP) / (T_REV - T_SNAP)) if i < T_REV else 1.0


def wisps(c, src, tip, cols, i, seed, n=5, a=1.0):
    """aura strands: short curling flows that come off the player's body and legs and stream into the ball, flickering"""
    rng = random.Random(seed)
    for s in range(n):
        ph = rng.uniform(0, 6.28); amp = rng.uniform(0.8, 2.2); y0 = rng.uniform(-14, -2)
        start = src + P(rng.uniform(-3, 3), y0)
        pts = []
        for k in range(8):
            u = k / 7.0
            base = start + (tip - start) * u
            wob = math.sin(i * 0.55 + ph + u * 6.0) * amp * (1 - u * 0.7)
            pts.append((base[0], base[1] + wob))
        col = cols[s % len(cols)]
        al = int(210 * a * (0.55 + 0.45 * math.sin(i * 0.7 + ph)))
        c.od.line(pts, fill=col + (max(0, al),), width=1)


def chip(c, x, y, txt, col, a=255):
    t = E.pix_text(txt, col, 1)
    if a < 255: t = E.fade(t, a)
    c.scr.alpha_composite(t, (int(x - t.width / 2), int(y)))


def ring_timer(c, p, left, i):
    r = 14
    box = [p[0] - r, p[1] - r * 0.45, p[0] + r, p[1] + r * 0.45]
    c.ud.ellipse(box, outline=(20, 30, 20, 120), width=1)
    if left > 0:
        col = (255, 210, 90, 230) if left > 0.3 else (255, 90, 60, 230 if (i // 2) % 2 else 140)
        c.ud.arc(box, -90, -90 + 360 * left, fill=col, width=1)


def vignette(amt):
    yy, xx = np.mgrid[0:VH, 0:VW]
    m = np.clip(((xx - VW / 2) / (VW * 0.55)) ** 2 + ((yy - VH / 2) / (VH * 0.6)) ** 2, 0, 1) ** 1.5
    def fn(arr):
        arr[..., :3] = arr[..., :3] * (1 - m[..., None] * amt) + np.array([10, 10, 25]) * m[..., None] * amt
        return arr
    return fn


def stand(c, p, face, skin, i):
    c.spr('guard', int(i * 40 / 85) % 12, face, skin, p)


@E.scene('CLASH_MATCH_VIEW', N=N, titan=(999, 1000))
def clash_match(c):
    i = c.i; c.hud = False
    heat = heat_at(i)
    on = T_HIT <= i < T_RES + 6
    # ---- camera: same angle, pushes in on the ball, eases back out with the play
    z = zoom_at(i)
    fol = BALL if i < T_RES else lerp(BALL, BALL + P(22, 0), smooth((i - T_RES) / (T_BACK - T_RES)))
    pre = lerp(BALL + P(-12, 0), BALL, smooth(i / T_HIT)) if i < T_HIT else fol
    c.cam(pre[0], pre[1] - 8 * clamp((z - 2.6) / 2.6), z)
    # other players (they keep playing, a little held while it grinds)
    slow = 0.25 if T_SNAP <= i < T_RES else 1.0
    for p, f, sk in ((P(160, 150), P(1, -0.3), HOME), (P(255, 92), P(-1, 0.4), AWAY), (P(150, 98), P(1, 0.2), HOME), (P(262, 150), P(-1, -0.2), AWAY)):
        stand(c, p, f, sk, i * slow)
    # ---- before: the carrier runs at the jockeying defender
    if i < T_HIT:
        a = A_AT + P((i - T_HIT) * 1.0, 0); d = D_AT + P(-(i - T_HIT) * 0.25, 0)
        c.spr('run', int(i * 40 / 57) % 12, P(1, 0), HOME, a); c.ball(a + P(5.5, 0), 1.0 + abs(math.sin(i * 0.7)))
        c.spr('df10_jockey', ak('df10_jockey', i, 0, loop=True), P(-1, 0), AWAY, d)
    # ---- the clash: both in the lunge, trembling, ball between the toes
    elif i < T_RES:
        k = ak('cl01_clash_reach', i, T_HIT, 1.0, loop=True)
        jit = (random.Random(i).uniform(-0.4, 0.4), 0) if i >= T_SNAP else (0, 0)
        push = 0.6 * math.sin(i * 0.9) * heat
        c.spr('cl01_clash_reach', k, P(1, 0), HOME, A_AT + P(push + jit[0], 0))
        c.spr('cl01_clash_reach', (k + 5) % 12, P(-1, 0), AWAY, D_AT + P(push - jit[0], 0))
        c.ball(BALL + P(push * 0.5, 0), 0.9)
        # auras meet at the ball
        wisps(c, A_AT, BALL + P(0, -2), RED, i, 11, 4 + int(3 * heat), 0.5 + 0.5 * heat)
        wisps(c, D_AT, BALL + P(0, -2), BLUE, i, 23, 4 + int(3 * heat), 0.5 + 0.5 * heat)
        fx.glow(c, BALL + P(0, -2), 5 + 3 * heat, (255, 210, 140), 0.35 + 0.35 * heat, 'over')
        fx.burst(c, BALL + P(0, -2), i % 7, i * 13, n=3 + int(5 * heat), speed=1.0 + heat, col=(255, 220, 140), life=7, up=1.3)
        if i % 3 == 0: fx.burst(c, BALL + P(0, -2), i % 5, i * 7, n=2 + int(3 * heat), speed=1.3, col=(170, 220, 255), life=5, up=1.2)
        if T_HIT <= i < T_HIT + 6: fx.shock(c, BALL, i - T_HIT, (255, 230, 170), 6, 22, 2)          # the hit
        if i >= T_SNAP and i < T_REV: ring_timer(c, BALL, 1 - (i - T_SNAP) / (T_REV - T_SNAP), i)
        if T_REV <= i < T_REV + 6:
            fx.shock(c, BALL, i - T_REV, (255, 255, 255), 6, 30, 3)
            fx.burst(c, BALL + P(0, -3), i - T_REV, 99, n=26, speed=2.6, col=(255, 230, 150), life=9, up=1.6)
        if T_REV <= i < T_REV + 2: c.flash(0.55 if i == T_REV else 0.2)
        if T_REV <= i < T_REV + 3: c.shake(1.5)
    # ---- the result: he skips over the slide, faint afterimages; the defender slides through and stays down
    else:
        j = i - T_RES
        kh = ak('cl02_clash_hurdle', j, 0)
        a = A_AT + ground(P(1, 0), root_fwd('cl02_clash_hurdle', kh))
        if kh >= 19: a = a + P((j - 20) * 1.1, 0)
        for g in range(1, 5):                                                     # faint afterimages behind him
            jg = j - g * 2
            if jg < 0 or j > 26: continue
            kg = ak('cl02_clash_hurdle', jg, 0); pg = A_AT + ground(P(1, 0), root_fwd('cl02_clash_hurdle', kg))
            c.spr('cl02_clash_hurdle', kg, P(1, 0), HOME, pg, tint_rgb=(255, 170, 90), tint_a=int(110 - g * 22), mix=0.8, shadow=False)
        anim = 'cl02_clash_hurdle' if kh < 19 else 'run'
        c.spr(anim, kh if anim != 'run' else int(i * 40 / 57) % 12, P(1, 0), HOME, a)
        hgt = 3.0 * math.sin(math.pi * clamp((j - 3) / 8.0)) if 3 <= j <= 11 else 0.0
        c.ball(a + P(5.0, 0), 0.9 + hgt)
        ks = ak('df02_slide_tackle', j, 0, 1.2)
        c.spr('df02_slide_tackle', ks, P(-1, 0.05), AWAY, D_AT + ground(P(-1, 0.05), root_fwd('df02_slide_tackle', ks) * 0.8))
        if j < 10: fx.trail(c, [tuple(A_AT + P(-6 + q * 1.6, 2 + math.sin(q * 0.8 + j) * 1.5)) for q in range(int(4 + j * 1.2))], (255, 200, 140), 120, 1)
    # ---- the card chips: above each, small; face down until the reveal
    if T_SNAP <= i < T_RES + 8:
        a_scr = c_to_scr(c, A_AT + P(-2, -27)); d_scr = c_to_scr(c, D_AT + P(2, -27))
        fade = 255 if i < T_RES else int(255 * (1 - (i - T_RES) / 8))
        if i >= T_PICK: chip(c, a_scr[0], a_scr[1], 'ELASTICO', (255, 210, 150), fade)
        else: chip(c, a_scr[0], a_scr[1], '. . .', (200, 170, 150), fade)
        if i >= T_REV: chip(c, d_scr[0], d_scr[1], 'STAND TACKLE', (180, 215, 255), fade)
        else: chip(c, d_scr[0], d_scr[1], '?', (180, 215, 255), fade)
    if on: c.after(vignette(0.45 * smooth(clamp((i - T_HIT) / 4)) * (1 - smooth(clamp((i - T_RES) / 8)))))


def c_to_scr(c, p):
    """pitch point -> screen point for this frame's camera (the view is set after the scene, so recompute it here)"""
    z = c.zoom; vw, vh = VW / z, VH / z
    cx = min(max(c.cam_xy[0], vw / 2), E.PW - vw / 2); cy = min(max(c.cam_xy[1], vh / 2), E.PH - vh / 2)
    return ((p[0] - (cx - vw / 2)) * z, (p[1] - (cy - vh / 2)) * z)


def render():
    sc = E.SCENES['CLASH_MATCH_VIEW']
    frames = [E.render_frame(sc, i) for i in range(N)]
    out = os.path.join(E.ROOT, 'export', 'skills'); os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'clash_match.gif')
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=40, loop=0)
    E.sheet_png(frames, '/tmp/clash_match_sheet.png', step=max(1, N // 24))
    return path


if __name__ == '__main__':
    print(render())
