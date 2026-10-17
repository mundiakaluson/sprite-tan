"""Clash stance montage in the match view: several pairings back to back (attacker stance vs defender stance), each: run-in, camera push-in,
both strike their clash stance and hold it (auras meeting at the ball, the timer ring), the reveal impact. No wind streaks (particles in Godot).
Run:  python titan/clash_variants.py  -> export/skills/clash_variants.gif"""
import sys, os, math, random
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import engine as E
from engine import P, lerp, clamp, smooth, ak, VW, VH
import fx
import clash_match as CM

HOME, AWAY = 'home', 'away'
BALL = CM.BALL
PAIRS = [   # (attacker stance, defender stance, gap each side of the ball in px, label)
    ('cl03_clash_bolt', 'cl03_clash_bolt', 8.0, 'BOLT  vs  BOLT'),
    ('cl06_clash_sole', 'cl11_clash_arms_crossed', 9.5, 'SOLE ON THE BALL  vs  ARMS CROSSED'),
    ('cl07_clash_stepover', 'cl04_clash_low_guard', 9.0, 'STEP-OVER  vs  LOW GUARD'),
    ('cl10_clash_point', 'cl14_clash_bull', 10.0, 'PROUD POINT  vs  BULL CHARGE'),
    ('cl09_clash_aura_farm', 'cl08_clash_slide_load', 10.5, 'AURA FARM  vs  SLIDE LOADED'),
    ('cl13_clash_airborne', 'cl13_clash_airborne', 8.5, 'AIRBORNE  vs  AIRBORNE'),
    ('cl12_clash_beckon', 'cl05_clash_shoulder', 9.0, 'BECKON  vs  SHOULDER BRACE'),
    ('cl01_clash_reach', 'cl01_clash_reach', 9.5, 'LUNGE  vs  LUNGE'),
]
SEG = 44
RUN, HIT, HOLD_END = 8, 13, 38            # within a segment: run-in until RUN, zoomed by HIT, reveal at HOLD_END


def seg_frame(c, pair, i):
    sa, sd, gap, label = pair
    A_AT, D_AT = BALL + P(-gap, 0.3), BALL + P(gap, -0.3)
    z = 2.6 if i < RUN else (lerp(2.6, 5.2, smooth((i - RUN) / (HIT - RUN))) if i < HIT else 5.2 + 0.2 * smooth((i - HIT) / (HOLD_END - HIT)))
    c.cam(BALL[0], BALL[1] - 8 * clamp((z - 2.6) / 2.6), z)
    heat = clamp((i - HIT) / (HOLD_END - HIT))
    for p, f, sk in ((P(160, 150), P(1, -0.3), HOME), (P(255, 92), P(-1, 0.4), AWAY), (P(150, 98), P(1, 0.2), HOME), (P(262, 150), P(-1, -0.2), AWAY)):
        CM.stand(c, p, f, sk, i * (0.3 if i >= HIT else 1.0))
    if i < RUN:
        a = A_AT + P((i - RUN) * 1.1, 0); d = D_AT + P(-(i - RUN) * 1.1, 0)
        c.spr('base_sprint', int(i * 40 / 52) % 10, P(1, 0), HOME, a); c.ball(a + P(5.5, 0), 1.0)
        c.spr('base_sprint', int(i * 40 / 52 + 5) % 10, P(-1, 0), AWAY, d)
    else:
        ka = ak(sa, i, RUN, 1.0, loop=True); kd = ak(sd, i, RUN, 1.0, loop=True)
        jit = random.Random(i).uniform(-0.3, 0.3)
        c.spr(sa, ka, P(1, 0), HOME, A_AT + P(jit, 0))
        c.spr(sd, (kd + 5) % E.META[sd]['frames'], P(-1, 0), AWAY, D_AT + P(-jit, 0))
        c.ball(BALL, 0.9)
        CM.wisps(c, A_AT, BALL + P(0, -2), CM.RED, i, 11, 4 + int(3 * heat), 0.5 + 0.5 * heat)
        CM.wisps(c, D_AT, BALL + P(0, -2), CM.BLUE, i, 23, 4 + int(3 * heat), 0.5 + 0.5 * heat)
        fx.glow(c, BALL + P(0, -2), 5 + 3 * heat, (255, 210, 140), 0.3 + 0.35 * heat, 'over')
        fx.burst(c, BALL + P(0, -2), i % 7, i * 13, n=2 + int(5 * heat), speed=1.0 + heat, col=(255, 220, 140), life=7, up=1.3)
        if RUN <= i < RUN + 6: fx.shock(c, BALL, i - RUN, (255, 230, 170), 6, 22, 2)
        if HIT <= i < HOLD_END: CM.ring_timer(c, BALL, 1 - (i - HIT) / (HOLD_END - HIT), i)
        if HOLD_END <= i < HOLD_END + 6:
            fx.shock(c, BALL, i - HOLD_END, (255, 255, 255), 6, 30, 3)
            fx.burst(c, BALL + P(0, -3), i - HOLD_END, 99, n=24, speed=2.6, col=(255, 230, 150), life=9, up=1.6)
        if i == HOLD_END: c.flash(0.5)
        if HOLD_END <= i < HOLD_END + 3: c.shake(1.5)
        c.after(CM.vignette(0.45 * smooth(clamp((i - RUN) / 4))))
    t = E.pix_text(label, (255, 240, 200), 1)
    c.scr.alpha_composite(t, (8, VH - 22))


class Seg:
    pass


def render():
    frames = []
    for pair in PAIRS:
        @E.scene('CLASH_VAR', N=SEG, titan=(999, 1000))
        def _s(c, pair=pair):
            c.hud = False
            seg_frame(c, pair, c.i)
        sc = E.SCENES['CLASH_VAR']
        frames += [E.render_frame(sc, i) for i in range(SEG)]
    out = os.path.join(E.ROOT, 'export', 'skills'); os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'clash_variants.gif')
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=40, loop=0)
    E.sheet_png(frames, '/tmp/clash_var_sheet.png', step=SEG // 2 + 4, cols=6)
    return path, len(frames)


if __name__ == '__main__':
    print(render())
