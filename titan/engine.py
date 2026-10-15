"""Titan scene engine. A Titan scene is a function of the frame number: scene(c) is called once per frame with a context `c` and declares what is on the pitch
(sprites from the baked sheets, the ball, effects drawn under / over the sprites, camera, screen effects). The engine adds the shared Titan presentation: the hand of cards,
the real Titan card flying in, flash, dim + letterbox + banner, result text and the card going on cooldown.
Run:  python titan/scenes.py [TT01 ...]  -> export/titan/ttNN_name.gif (+ contact sheets in /tmp)"""
import sys, os, math, random, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
for p in ('sprites', 'cards'):
    sys.path.insert(0, os.path.join(ROOT, p))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import gen_uv as U
import cardlib2 as CL
import recipes
recipes.install(CL.EMB)

CW = CH = 40; OX, OY = 20, 30
PW, PH = 420, 240; VW, VH = 480, 270
OUT = os.path.join(ROOT, 'sprites', 'out_uv')
META = json.load(open(os.path.join(OUT, 'animations.json')))['animations']
SK = {n: U.make_skin(U.SKINS[n]) for n in ('home', 'away', 'keeper', 'third')}
_sheets = {}; _spr = {}
def _font(size=11):
    """a bold monospace font that exists on this machine (Linux / Windows / macOS), else Pillow's built-in one"""
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 'DejaVuSansMono-Bold.ttf', 'C:/Windows/Fonts/consolab.ttf', 'C:/Windows/Fonts/lucon.ttf',
              'C:/Windows/Fonts/cour.ttf', '/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/Monaco.ttf', '/Library/Fonts/Courier New Bold.ttf'):
        try: return ImageFont.truetype(f, size)
        except OSError: pass
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()


FONT = _font(11)
GOAL_X = 330; GOAL_Y0, GOAL_Y1 = 90, 150


def sheet(a):
    if a not in _sheets: _sheets[a] = Image.open(os.path.join(OUT, f'{a}_uv_sheet.png')).convert('RGBA')
    return _sheets[a]


def sprite(anim, k, di, skin):
    key = (anim, k, di, skin)
    if key not in _spr:
        arr = np.array(sheet(anim).crop((k * CW, di * CH, (k + 1) * CW, (di + 1) * CH)))
        _spr[key] = U.apply_skin(arr, SK[skin])
    return _spr[key]


def tint(im, rgb, a=255, mix=0.65):
    arr = np.array(im).astype(np.float32); m = arr[..., 3] > 0
    arr[..., :3] = np.where(m[..., None], arr[..., :3] * (1 - mix) + np.array(rgb) * mix, arr[..., :3])
    arr[..., 3] = np.where(m, np.minimum(arr[..., 3], a), 0)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def fade(im, a):
    arr = np.array(im); arr[..., 3] = (arr[..., 3].astype(np.float32) * a / 255).astype(np.uint8); return Image.fromarray(arr, 'RGBA')


def dir_index(dx, dy): return int(round(math.atan2(dx, dy * 2) / (2 * math.pi) * 32)) % 32


def unit(v):
    v = np.array(v, float); n = np.linalg.norm(v); return v / n if n > 1e-9 else np.array([1.0, 0.0])


def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def P(x, y): return np.array([float(x), float(y)])


def track(keys):
    """keys: [(frame, (x, y)), ...] -> f(i) position, smoothstep between keys (holds before the first / after the last)"""
    def f(i):
        if i <= keys[0][0]: return P(*keys[0][1])
        for (a, pa), (b, pb) in zip(keys, keys[1:]):
            if i <= b: return lerp(P(*pa), P(*pb), smooth((i - a) / (b - a)))
        return P(*keys[-1][1])
    return f


def line_track(keys):
    """like track() but linear (constant speed)"""
    def f(i):
        if i <= keys[0][0]: return P(*keys[0][1])
        for (a, pa), (b, pb) in zip(keys, keys[1:]):
            if i <= b: return lerp(P(*pa), P(*pb), (i - a) / (b - a))
        return P(*keys[-1][1])
    return f


def ak(anim, i, start, rate=1.0, loop=None):
    """animation frame index k for scene frame i (40 ms per scene frame), the animation starting at `start`"""
    m = META[anim]; n = m['frames']; loop = m['loop'] if loop is None else loop
    k = int(max(0, i - start) * 40 * rate / m['ms_per_frame'])
    return k % n if loop else min(k, n - 1)


def root_fwd(anim, k): m = META[anim]; r = m['root_forward_px']; return r[min(k, len(r) - 1)] - r[0]
def root_side(anim, k): m = META[anim]; r = m.get('root_side_px'); return 0.0 if not r else r[min(k, len(r) - 1)] - r[0]


def ground(face, d):
    """screen displacement for d px of travel along a ground direction `face` (screen vector; the pitch is squashed 2:1 vertically)"""
    g = np.array([face[0], face[1] * 2.0]); g = g / (np.linalg.norm(g) + 1e-9); return np.array([g[0] * d, g[1] * d / 2.0])


def pix_text(txt, col, S=3, shadow=(10, 8, 30)):
    w = int(FONT.getlength(txt)) + 4; im = Image.new('L', (w, 14), 0); ImageDraw.Draw(im).text((2, 0), txt, font=FONT, fill=255)
    a = np.array(im) > 110; out = np.zeros((16, w + 2, 4), np.uint8)
    sh = np.roll(np.roll(a, 1, 0), 1, 1); out[:14, :w][sh] = shadow + (255,); out[:14, :w][a] = col + (255,)
    return Image.fromarray(out, 'RGBA').resize(((w + 2) * S, 16 * S), Image.NEAREST)


def blob(w, h, cx, cy, rx, ry, col, a):
    y, x = np.mgrid[0:h, 0:w]; d = np.sqrt(((x - cx) / max(rx, .1)) ** 2 + ((y - cy) / max(ry, .1)) ** 2)
    al = np.clip(1.0 - d, 0, 1) ** 1.5 * a; im = np.zeros((h, w, 4), np.uint8); im[..., :3] = col; im[..., 3] = (al * 255).astype(np.uint8)
    return Image.fromarray(im, 'RGBA')


# ------------------------------------------------------------------ pitch
def make_pitch():
    im = Image.new('RGBA', (PW, PH)); d = ImageDraw.Draw(im)
    for x in range(0, PW, 22): d.rectangle([x, 0, x + 21, PH], fill=((58, 122, 62) if (x // 22) % 2 else (64, 130, 68)) + (255,))
    LN = (214, 226, 208, 255)
    d.line([(232, 40), (232, 200)], fill=LN); d.line([(232, 40), (GOAL_X, 40)], fill=LN); d.line([(232, 200), (GOAL_X, 200)], fill=LN)
    d.line([(GOAL_X, 40), (GOAL_X, 200)], fill=LN); d.line([(GOAL_X, 90), (GOAL_X, 150)], fill=LN)
    d.line([(0, 30), (PW, 30)], fill=LN); d.line([(0, 212), (PW, 212)], fill=LN); d.arc([-40, 80, 40, 160], -90, 90, fill=LN)
    for x in range(GOAL_X + 1, GOAL_X + 9, 2):                                           # the net behind the goal line
        d.line([(x, GOAL_Y0 - 3 + (x - GOAL_X) // 3), (x, GOAL_Y1 + 3 - (x - GOAL_X) // 3)], fill=(225, 232, 224, 120))
    for y in range(GOAL_Y0, GOAL_Y1 + 1, 4): d.line([(GOAL_X, y), (GOAL_X + 8, y)], fill=(225, 232, 224, 110))
    return im


PITCH = make_pitch()


# ------------------------------------------------------------------ the per-frame context
class Ctx:
    def __init__(s, sc, i):
        s.sc = sc; s.i = i; s.N = sc.N; s.t = i / sc.N
        t0, t1 = sc.titan
        s.ta = 0.0 if i < t0 else (clamp((i - t0) / 8) if i < t1 else clamp(1 - (i - t1) / 12))
        s.in_titan = t0 <= i < t1
        s.under = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); s.ud = ImageDraw.Draw(s.under)
        s.over = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); s.od = ImageDraw.Draw(s.over)
        s.scr = Image.new('RGBA', (VW, VH), (0, 0, 0, 0)); s.sd = ImageDraw.Draw(s.scr)        # screen overlay, drawn after the camera
        s.sprites = []; s.post = []; s.cam_xy = np.array([210.0, 120.0]); s.zoom = 2.0; s.shake_px = 0.0
        s.dim_rgb = (18, 22, 70); s.dim_amt = 0.0; s.hud = True; s.banner = True; s.flash_a = 0.0; s.flash_rgb = (255, 245, 210)
        s.letterbox = s.ta

    # --- things on the pitch
    def spr(s, anim, k, face, skin, p, tint_rgb=None, tint_a=255, alpha=255, mix=0.65, shadow=True, dy=0):
        di = face if isinstance(face, (int, np.integer)) else dir_index(face[0], face[1])
        im = sprite(anim, k, di, skin)
        if tint_rgb is not None: im = tint(im, tint_rgb, tint_a, mix)
        if alpha < 255: im = fade(im, alpha)
        s.sprites.append((p[1] + dy * 0.01, 'spr', (im, np.array(p, float), shadow)))

    def ball(s, p, z=0.0, r=1.0, col=(240, 240, 245), glow=None, alpha=255):
        s.sprites.append((p[1] + 0.2, 'ball', (np.array(p, float), z, r, col, glow, alpha)))

    def shadow(s, p, w=6, a=90): s.ud.ellipse([p[0] - w, p[1] - w / 3, p[0] + w, p[1] + w / 3], fill=(8, 8, 28, a))
    def cam(s, x, y, zoom): s.cam_xy = np.array([x, y], float); s.zoom = zoom
    def shake(s, px): s.shake_px = px
    def dim(s, amt, rgb=(18, 22, 70)): s.dim_amt = amt; s.dim_rgb = rgb
    def flash(s, a, rgb=(255, 245, 210)): s.flash_a = a; s.flash_rgb = rgb
    def after(s, fn): s.post.append(fn)

    # --- screen helpers
    def to_screen(s, p, z=0.0):
        x0, y0, vw, vh = s.view
        return ((p[0] - x0) * VW / vw, (p[1] - z - y0) * VH / vh)

    def text(s, x, y, txt, col, S=2, center=True):
        return                                                                  # no on-screen text in Titan scenes (the card says it)


# ------------------------------------------------------------------ the scene registry + runner
class Scene:
    def __init__(s, cid, fn, N, titan, color, result, tag=None):
        s.cid, s.fn, s.N, s.titan, s.color, s.result, s.tag = cid, fn, N, titan, color, result, tag


SCENES = {}


def scene(cid, N=120, titan=(30, 90), color=(255, 214, 80), result='', tag=None):
    def deco(fn):
        SCENES[cid] = Scene(cid, fn, N, titan, color, result, tag); return fn
    return deco


vy, vx = np.mgrid[0:VH, 0:VW]; VIG = np.clip(((vx - 240) / 260.0) ** 2 + ((vy - 135) / 170.0) ** 2, 0, 1)


def hud_card(d, x, y, S, hot=False, grey=False):
    w, h = 22 * S, 30 * S; col = (255, 214, 80) if hot else ((70, 74, 90) if grey else (120, 130, 160))
    d.rectangle([x, y, x + w, y + h], fill=(28, 24, 52, 255), outline=col, width=max(1, S // 2 + 1))
    d.rectangle([x + 2 * S, y + 3 * S, x + w - 2 * S, y + 17 * S], fill=((66, 40, 110) if hot else (36, 46, 84)) + (255,))
    d.rectangle([x + 2 * S, y + 20 * S, x + w - 2 * S, y + 22 * S], fill=col + (255,))
    d.rectangle([x + 2 * S, y + 24 * S, x + w // 2, y + 26 * S], fill=(col[0] // 2, col[1] // 2, col[2] // 2, 255))


_cards = {}
def card_face(cid, scale=4):
    if (cid, scale) not in _cards:
        import csv
        r = next(x for x in csv.DictReader(open(os.path.join(ROOT, 'data', 'cards.csv'), encoding='utf-8')) if x['id'] == cid)
        row = dict(id=cid, name=r['name'], cat=r['cat'], slots=int(r['slots']), succ=int(r['succ']), risk=int(r['risk']), cd=0, desc=r['description'], rarity=r['rarity'])
        pal = CL.CAT.get(row['cat'], CL.CAT['SHOT']); im = CL.card(row, CL.EMB[cid](pal), 'ready', 0.0)
        _cards[(cid, scale)] = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    return _cards[(cid, scale)]


def render_frame(sc, i):
    c = Ctx(sc, i)
    c.sc.fn(c)
    # ---- world
    wnp = np.array(PITCH).astype(np.float32)
    if c.dim_amt > 0: wnp[..., :3] = wnp[..., :3] * (1 - c.dim_amt) + np.array(c.dim_rgb) * c.dim_amt
    world = Image.fromarray(wnp.astype(np.uint8), 'RGBA'); world.alpha_composite(c.under)
    sh = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for y, kind, pl in c.sprites:
        if kind == 'spr' and pl[2]: p = pl[1]; sd.ellipse([p[0] - 6, p[1] - 2, p[0] + 6, p[1] + 2], fill=(8, 8, 28, 90))
        if kind == 'ball': p, z = pl[0], pl[1]; sd.ellipse([p[0] - 2, p[1] - 1, p[0] + 2, p[1] + 1], fill=(8, 8, 28, 90))
    world.alpha_composite(sh)
    for y, kind, pl in sorted(c.sprites, key=lambda a: a[0]):
        if kind == 'spr': im, p, _ = pl; world.alpha_composite(im, (int(round(p[0])) - OX, int(round(p[1])) - OY))
        else:
            p, z, r, col, glow, a = pl; bx, by = p[0], p[1] - z
            if glow: world.alpha_composite(blob(PW, PH, bx, by, 6 * r + 2, 6 * r + 2, glow, 0.8))
            bd = ImageDraw.Draw(world); rr = max(1.0, r)
            bd.ellipse([bx - rr, by - rr, bx + rr, by + rr], fill=col + (a,)); bd.point((int(bx + rr * 0.4), int(by + rr * 0.4)), fill=(40, 40, 60, a))
    world.alpha_composite(c.over)
    # ---- camera
    z = c.zoom; vw, vh = VW / z, VH / z
    sx = random.Random(i * 3).uniform(-1, 1) * c.shake_px; sy = random.Random(i * 5 + 1).uniform(-1, 1) * c.shake_px
    cx = min(max(c.cam_xy[0], vw / 2), PW - vw / 2); cy = min(max(c.cam_xy[1], vh / 2), PH - vh / 2)
    x0 = int(round(cx - vw / 2 + sx)); y0 = int(round(cy - vh / 2 + sy)); c.view = (x0, y0, vw, vh)
    crop = world.crop((x0, y0, x0 + int(round(vw)), y0 + int(round(vh)))).resize((VW, VH), Image.NEAREST).convert('RGBA')
    if c.post:
        arr = np.array(crop).astype(np.float32)
        for fn in c.post: arr = fn(arr)
        crop = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA')
    out = crop
    ov = Image.new('RGBA', (VW, VH), (0, 0, 0, 0)); od = ImageDraw.Draw(ov); ta = c.ta
    if ta > 0:
        rng = random.Random(i * 13 + 5)
        for _ in range(int(14 * ta)):                                              # speed lines
            y = rng.randint(30, 240); x = (rng.randint(0, 480) - i * 70) % 560 - 40; l = rng.randint(40, 120)
            od.line([(x, y), (x + l, y)], fill=(220, 240, 255, 60), width=1)
        v = (VIG * 150 * ta).astype(np.uint8); va = np.zeros((VH, VW, 4), np.uint8); va[..., 2] = 30; va[..., 3] = v
        ov.alpha_composite(Image.fromarray(va, 'RGBA'))
    out.alpha_composite(ov); out.alpha_composite(c.scr)
    od = ImageDraw.Draw(out); t0, t1 = sc.titan
    bar = int(26 * min(1.0, ta * 1.6))
    if bar: od.rectangle([0, 0, VW, bar], fill=(4, 4, 12, 255)); od.rectangle([0, VH - bar, VW, VH], fill=(4, 4, 12, 255))
    if c.flash_a > 0: out.alpha_composite(Image.new('RGBA', (VW, VH), c.flash_rgb + (int(255 * min(1, c.flash_a)),)))
    if t0 <= i < t0 + 5: out.alpha_composite(Image.new('RGBA', (VW, VH), (255, 245, 210, int(210 * (1 - (i - t0) / 5)))))     # the activation flash
    # the hand of cards (the Titan card goes hot, then onto cooldown); no on-screen text, the card says it
    if c.hud and (i < t0 + 1 or i >= t1 + 12):
        for ci in range(5):
            hot = (ci == 2) and i < t0 + 1; grey = (ci == 2) and i >= t1 + 12
            y = VH - 64 - (10 if (hot and t0 - 12 <= i < t0 + 1) else 0); x = 240 - 5 * 26 + ci * 52 + 4
            hud_card(od, x, y, 2, hot=hot, grey=grey)
            if grey:
                cd = min(1.0, (i - t1 - 12) / 38.0); od.pieslice([x + 8, y + 18, x + 36, y + 46], -90, -90 + 360 * (1 - cd), fill=(10, 10, 20, 170))
    return out.convert('RGB')


SC_TITLE = {}


def render(cid, outdir=None, every=1):
    sc = SCENES[cid]; frames = [render_frame(sc, i) for i in range(sc.N)]
    outdir = outdir or os.path.join(ROOT, 'export', 'titan'); os.makedirs(outdir, exist_ok=True)
    name = f"{cid.lower()}_{SC_TITLE[cid].lower().replace(' ', '_').replace(chr(39), '')}"
    frames[0].save(os.path.join(outdir, name + '.gif'), save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=False)
    return name, frames


def sheet_png(frames, path, cols=8, step=None, S=0.5):
    step = step or max(1, len(frames) // 24); fs = frames[::step][:24]
    w, h = int(VW * S), int(VH * S); rows = (len(fs) + cols - 1) // cols
    im = Image.new('RGB', (cols * w, rows * h))
    for n, f in enumerate(fs): im.paste(f.resize((w, h), Image.LANCZOS), ((n % cols) * w, (n // cols) * h))
    im.save(path)
