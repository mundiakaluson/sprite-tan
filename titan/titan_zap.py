import sys, math, random, json
sys.path.insert(0, '/home/claude')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import gen_uv as U

CW = CH = 40; OX, OY = 20, 30
M = json.load(open('/home/claude/out_uv/animations.json'))['animations']
SK = {'home': U.make_skin(U.SKINS['home']), 'away': U.make_skin(U.SKINS['away'])}
SHEETS = {n: Image.open(f'/home/claude/out_uv/{n}_uv_sheet.png').convert('RGBA') for n in ('run', 'guard', 'slide')}
cache = {}
def sprite(anim, k, di, skin):
    key = (anim, k, di, skin)
    if key not in cache:
        arr = np.array(SHEETS[anim].crop((k * CW, di * CH, (k + 1) * CW, (di + 1) * CH)))
        cache[key] = U.apply_skin(arr, SK[skin])
    return cache[key]
def tint(im, rgb, a):
    arr = np.array(im).astype(np.float32); m = arr[..., 3] > 0
    arr[..., :3] = np.where(m[..., None], arr[..., :3] * 0.35 + np.array(rgb) * 0.65, arr[..., :3])
    arr[..., 3] = np.where(m, a, 0)
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')

def dir_index(dx, dy):                       # screen-ground vector -> sprite row (0 = facing camera, 8 = east)
    return int(round(math.atan2(dx, dy * 2) / (2 * math.pi) * 32)) % 32
def ang_of(di): return 2 * math.pi * di / 32

# ---------------------------------------------------------------- pitch (native pixels)
PW, PH = 420, 240
pitch = Image.new('RGBA', (PW, PH))
pd = ImageDraw.Draw(pitch)
for x in range(0, PW, 22):
    pd.rectangle([x, 0, x + 21, PH], fill=((58, 122, 62) if (x // 22) % 2 else (64, 130, 68)) + (255,))
LN = (214, 226, 208, 255)
pd.line([(232, 40), (232, 200)], fill=LN); pd.line([(232, 40), (330, 40)], fill=LN); pd.line([(232, 200), (330, 200)], fill=LN)
pd.line([(330, 40), (330, 200)], fill=LN); pd.line([(330, 90), (330, 150)], fill=LN)
pd.line([(0, 30), (PW, 30)], fill=LN); pd.line([(0, 212), (PW, 212)], fill=LN)
pd.arc([-40, 80, 40, 160], -90, 90, fill=LN)
pitch_np = np.array(pitch).astype(np.float32)

# ---------------------------------------------------------------- attacker path
WP = [(50, 120), (76, 121), (92, 131), (108, 109), (124, 131), (142, 119), (175, 120), (210, 120), (300, 120)]
def catmull(P, n=40):
    P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [np.array(p, float) for p in P[i - 1:i + 3]]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(P[-1], float)); return np.array(out)
PATH = catmull(WP); SEG = np.r_[0, np.cumsum(np.linalg.norm(np.diff(PATH, axis=0), axis=1))]
def path_at(s):
    s = min(max(s, 0), SEG[-1] - 1e-3); i = np.searchsorted(SEG, s) - 1; i = max(i, 0)
    t = (s - SEG[i]) / (SEG[i + 1] - SEG[i]); p = PATH[i] * (1 - t) + PATH[i + 1] * t
    d = PATH[min(i + 3, len(PATH) - 1)] - PATH[i]; return p, d / (np.linalg.norm(d) + 1e-9)

# ---------------------------------------------------------------- timeline
N = 150; DT = 0.04
def scale(i):
    if i < 30: return 1.0
    if i < 34: return 0.0
    if i < 36: return 0.2
    if i < 100: return 0.4
    if i < 118: return 0.4 + 0.6 * (i - 100) / 18
    return 1.0
def titan_amt(i):                                   # 0..1 dim / aura strength
    if i < 30: return 0.0
    if i < 38: return (i - 30) / 8
    if i < 102: return 1.0
    if i < 114: return 1 - (i - 102) / 12
    return 0.0
def zoom(i):
    for lim, z in ((37, 3), (43, 4), (51, 5), (59, 6), (92, 6), (98, 5), (104, 4)):
        if i < lim: return z
    return 3

defs = [dict(x=92, y=118, skin='away'), dict(x=108, y=120, skin='away'), dict(x=124, y=118, skin='away')]
for d in defs: d['ang'] = ang_of(24); d['k'] = 0
slide_start = None; slide_pos = None; slide_dir = None
att_s = 0.0; att_k = 0.0; cur = None; last_run = np.array([50.0,120.0]); bolts = []; ghosts = []
ZF = [46, 68, 90, 108]; ZT = [(100, 109), (116, 132), (133, 109), (152, 120)]
zface = [dir_index(100-73, 109-120), dir_index(116-100, 132-109), dir_index(133-116, 109-132), dir_index(152-133, 120-109)]
dg = 0.0; cam = np.array([75.0, 118.0]); hist = []
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 11)
def pix_text(txt, col, S=3, shadow=(10, 8, 30)):
    w = int(font.getlength(txt)) + 4; im = Image.new('L', (w, 14), 0); ImageDraw.Draw(im).text((2, 0), txt, font=font, fill=255)
    a = np.array(im) > 110; out = np.zeros((16, w + 2, 4), np.uint8)
    sh = np.roll(np.roll(a, 1, 0), 1, 1); out[:14, :w][sh] = shadow + (255,)
    out[:14, :w][a] = col + (255,)
    return Image.fromarray(out, 'RGBA').resize(((w + 2) * S, 16 * S), Image.NEAREST)

vig = np.zeros((270, 480), np.float32)
yy, xx = np.mgrid[0:270, 0:480]; vig = np.clip(((xx - 240) / 260.0) ** 2 + ((yy - 135) / 170.0) ** 2, 0, 1)
frames = []
for i in range(N):
    sc = scale(i); ta = titan_amt(i); titan = 38 <= i < 102
    dg += DT * sc
    # attacker: runs in, then ZAPS between points (no running), then runs out
    if i < 30:
        att_k += 0.7; att_s += 0.84; pos, tdir = path_at(att_s); pos = pos.copy(); adi = dir_index(tdir[0], tdir[1]); mode = 'run'; last_run = pos.copy()
    else:
        mode = 'stance'
    if i >= 30:
        pos = cur.copy() if cur is not None else last_run.copy()
    cur = pos.copy() if i < 30 else cur
    # zap schedule
    for zi, zf in enumerate(ZF):
        if i == zf:
            src = cur.copy(); dst = np.array(ZT[zi], float)
            bolts.append((zf, src, dst)); ghosts.append((zf, src, zface[zi]))
        if i == zf + 2:
            cur = np.array(ZT[zi], float)
    if i >= 30 and i < 112:
        pos = cur.copy()
        nxt = next((j for j, zf in enumerate(ZF) if zf + 2 > i), None)
        if nxt is None: face = np.array([1.0, 0.0])
        else:
            v = np.array(ZT[nxt], float) - pos; face = v / (np.linalg.norm(v) + 1e-9)
        adi = dir_index(face[0], face[1]); tdir = face; mode = 'stance'
        if any(zf <= i <= zf + 1 for zf in ZF): mode = 'hidden'
        rk = int(dg * 1000 / 85) % 12
    elif i >= 112:
        if i == 112: run_x = cur[0]; att_k = 0.0
        att_k += 0.7; cur = cur + np.array([0.84, 0.0]); pos = cur.copy(); adi = 8; tdir = np.array([1.0, 0.0]); mode = 'run'; rk = int(att_k) % 12
    else:
        rk = int(att_k) % 12
    hist.append((pos.copy(), rk, adi))
    # defenders
    for j, d in enumerate(defs):
        want = math.atan2(pos[0] - d['x'], (pos[1] - d['y']) * 2)
        diff = (want - d['ang'] + math.pi) % (2 * math.pi) - math.pi
        rate = 1.3 * sc * DT
        d['ang'] += max(-rate, min(rate, diff))
    if slide_start is None and i >= 40:
        slide_start = dg; sd = np.array([pos[0] + 2 - defs[1]['x'], pos[1] + 4 - defs[1]['y']]); slide_dir = sd / np.linalg.norm(sd)
        slide_pos = np.array([defs[1]['x'], defs[1]['y']]); slide_di = dir_index(slide_dir[0], slide_dir[1])

    # camera
    z = zoom(i)
    look = np.array([pos[0] + (14 if z <= 4 else 9), 0.35 * pos[1] + 0.65 * 120.0 - 2])
    cam += (look - cam) * (0.3 if i > 30 else 0.12)
    vw, vh = 480 / z, 270 / z
    cx = min(max(cam[0], vw / 2), PW - vw / 2); cy = min(max(cam[1], vh / 2), PH - vh / 2)

    # world layer
    wnp = pitch_np.copy()
    if ta > 0:
        wnp[..., :3] = wnp[..., :3] * (1 - 0.5 * ta) + np.array([18, 22, 70]) * 0.5 * ta
    world = Image.fromarray(wnp.astype(np.uint8), 'RGBA')
    actors = []
    for j, d in enumerate(defs):
        if j == 1 and slide_start is not None:
            k = min(int((dg - slide_start) * 1000 / 70), 21)
            fwd = M['slide']['root_forward_px'][k] - M['slide']['root_forward_px'][0]
            p = slide_pos + np.array([slide_dir[0] * fwd, slide_dir[1] * fwd * 0.5])
            actors.append((p[1], 'slide', k, slide_di, 'away', p))
        else:
            k = int(dg * 1000 / 85) % 12
            actors.append((d['y'], 'guard', k, int(round(d['ang'] / (2 * math.pi) * 32)) % 32, 'away', np.array([d['x'], d['y']])))
    if mode != 'hidden': actors.append((pos[1], 'run' if mode == 'run' else 'guard', rk, adi, 'home', pos))
    actors.sort(key=lambda a: a[0])
    sh = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); sd_ = ImageDraw.Draw(sh)
    for _, an, k, di, skn, p in actors:
        sd_.ellipse([p[0] - 6, p[1] - 2, p[0] + 6, p[1] + 2], fill=(8, 8, 28, 90))
    world.alpha_composite(sh)
    # aura ring under attacker
    if ta > 0:
        rng = random.Random(i * 7 + 1); pulse = 1 + 0.12 * math.sin(i * 0.7)
        ring = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
        rd.ellipse([pos[0] - 11 * pulse, pos[1] - 4.5 * pulse, pos[0] + 11 * pulse, pos[1] + 4.5 * pulse], outline=(255, 214, 80, int(230 * ta)))
        rd.ellipse([pos[0] - 7 * pulse, pos[1] - 3 * pulse, pos[0] + 7 * pulse, pos[1] + 3 * pulse], outline=(120, 230, 255, int(200 * ta)))
        for _ in range(7):
            sx = pos[0] + rng.uniform(-8, 8); sy = pos[1] - rng.uniform(0, 24); rd.point((int(sx), int(sy)), fill=(255, 230, 120, int(240 * ta)))
        world.alpha_composite(ring)
    # ghosts left behind at each departure + lightning bolts
    for (gf, gp, gd) in ghosts:
        age = i - gf
        if 0 <= age < 12:
            g = tint(sprite('guard', int(gf * 0.3) % 12, gd, 'home'), (120, 235, 255), int(150 * (1 - age / 12)))
            world.alpha_composite(g, (int(gp[0]) - OX, int(gp[1]) - OY))
    bl = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
    for (bf, A, B) in bolts:
        age = i - bf
        if 0 <= age <= 3:
            rng = random.Random(bf * 31 + age * 7); A2 = A + np.array([0, -10.0]); B2 = B + np.array([0, -10.0])
            pts = [tuple(A2)]
            for t in np.linspace(0, 1, 7)[1:-1]:
                q = A2 * (1 - t) + B2 * t; pts.append((q[0] + rng.uniform(-5, 5), q[1] + rng.uniform(-7, 7)))
            pts.append(tuple(B2))
            fade = 1 - age / 4.0
            bd.line(pts, fill=(80, 200, 255, int(170 * fade)), width=4)
            bd.line(pts, fill=(200, 245, 255, int(255 * fade)), width=2)
            bd.line(pts, fill=(255, 255, 255, int(255 * fade)), width=1)
    for zf, T in zip(ZF, ZT):
        age = i - (zf + 2)
        if 0 <= age < 6:
            r = 4 + age * 3.2; a_ = int(230 * (1 - age / 6))
            bd.ellipse([T[0] - r, T[1] - r * 0.45, T[0] + r, T[1] + r * 0.45], outline=(255, 235, 140, a_))
            bd.ellipse([T[0] - r * 0.6, T[1] - r * 0.27, T[0] + r * 0.6, T[1] + r * 0.27], outline=(150, 240, 255, a_))
    world.alpha_composite(bl)
    for _, an, k, di, skn, p in actors:
        jx = jy = 0
        if skn == 'home' and any(zf - 6 <= i < zf for zf in ZF):
            rr = random.Random(i * 5); jx, jy = rr.choice((-1, 0, 1)), rr.choice((0, 0, 1))
        spr_ = sprite(an, k, di, skn)
        if skn == 'home' and any(zf + 2 <= i <= zf + 3 for zf in ZF): spr_ = tint(spr_, (255, 255, 255), 255)
        world.alpha_composite(spr_, (int(round(p[0])) - OX + jx, int(round(p[1])) - OY + jy))
        if skn == 'home':                                        # ball
            f = tdir; bp = p + f * 5.5 + np.array([0, 0.0]); bz = (1.0 + abs(math.sin(att_k * math.pi / 3)) * 1.2) if an == 'run' else 0.8
            bx, by = int(round(bp[0])), int(round(bp[1] - bz))
            for dx, dy, c in ((0, 0, (240, 240, 245)), (1, 0, (240, 240, 245)), (0, 1, (240, 240, 245)), (1, 1, (40, 40, 60))):
                world.putpixel((bx + dx, by + dy), c + (255,))
    # camera crop + integer upscale
    x0 = int(round(cx - vw / 2)); y0 = int(round(cy - vh / 2))
    crop = world.crop((x0, y0, x0 + int(round(vw)), y0 + int(round(vh)))).resize((480, 270), Image.NEAREST)
    out = crop.convert('RGBA')
    ov = Image.new('RGBA', (480, 270), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    if ta > 0:                                                  # speed lines + vignette
        rng = random.Random(i * 13 + 5)
        for _ in range(int(16 * ta)):
            y = rng.randint(30, 240); x = (rng.randint(0, 480) - i * 70) % 560 - 40; l = rng.randint(40, 120)
            od.line([(x, y), (x + l, y)], fill=(220, 240, 255, 70), width=1)
        v = (vig * 150 * ta).astype(np.uint8); varr = np.zeros((270, 480, 4), np.uint8); varr[..., 2] = 30; varr[..., 3] = v
        ov.alpha_composite(Image.fromarray(varr, 'RGBA'))
    out.alpha_composite(ov)
    od = ImageDraw.Draw(out)
    bar = int(26 * min(1.0, ta * 1.6))                           # letterbox
    if bar: od.rectangle([0, 0, 480, bar], fill=(4, 4, 12, 255)); od.rectangle([0, 270 - bar, 480, 270], fill=(4, 4, 12, 255))
    # flash
    if 30 <= i < 35:
        fl = Image.new('RGBA', (480, 270), (255, 245, 210, int(210 * (1 - (i - 30) / 5)))); out.alpha_composite(fl)
    # banner lives in the letterbox bar
    if 33 <= i < 108 and bar >= 20:
        a = pix_text('TITAN  -  ZIP ZAP', (255, 214, 80), 2)
        out.alpha_composite(a, (240 - a.width // 2, max(0, (bar - a.height) // 2)))
    # HUD hand (normal play) + card flying in
    def card(x, y, S, hot=False, grey=False, label=''):
        w, h = 22 * S, 30 * S
        col = (255, 214, 80) if hot else (120, 130, 160)
        if grey: col = (70, 74, 90)
        od.rectangle([x, y, x + w, y + h], fill=(28, 24, 52, 255), outline=col, width=max(1, S // 2 + 1))
        od.rectangle([x + 2 * S, y + 3 * S, x + w - 2 * S, y + 17 * S], fill=((66, 40, 110) if hot else (36, 46, 84)) + (255,))
        od.rectangle([x + 2 * S, y + 20 * S, x + w - 2 * S, y + 22 * S], fill=col + (255,))
        od.rectangle([x + 2 * S, y + 24 * S, x + w // 2, y + 26 * S], fill=(col[0] // 2, col[1] // 2, col[2] // 2, 255))
    show_hud = i < 31 or i >= 112
    if show_hud:
        lift = 0
        for ci in range(5):
            hot = (ci == 2) and i < 31; grey = (ci == 2) and i >= 112
            y = 270 - 64 - (10 if (hot and 18 <= i < 31) else 0)
            x = 240 - 5 * 26 + ci * 52 + 4
            card(x, y, 2, hot=hot, grey=grey)
            if grey:
                cd = min(1.0, (i - 112) / 38.0)
                od.pieslice([x + 8, y + 18, x + 36, y + 46], -90, -90 + 360 * (1 - cd), fill=(10, 10, 20, 170))
    if 22 <= i < 100:
        t = min(1, (i - 22) / 8); t2 = min(1, (100 - i) / 8); e = min(t, t2)
        S = 4; w = 22 * S
        card(480 - 24 - w - 8, int(270 - 40 - e * 150), S, hot=True)
        ci = sprite('run', 3, 8, 'home').resize((40 * 2, 40 * 2), Image.NEAREST)
        cxp = 480 - 24 - w - 8; cyp = int(270 - 40 - e * 150)
        if e > 0.3:
            out.alpha_composite(ci, (cxp + w // 2 - 40, cyp + 3 * S))
            od.rectangle([cxp + 2 * S, cyp + 3 * S, cxp + 2 * S + 1, cyp + 17 * S], fill=(255, 214, 80, 255))
    if i >= 122:
        t = min(1, (i - 122) / 6)
        b = pix_text('3 DEFENDERS BEATEN', (255, 214, 80), 2)
        out.alpha_composite(b, (240 - b.width // 2, int(56 - 20 * (1 - t))))
    frames.append(out.convert('RGB'))
frames[0].save('/home/claude/titan/titan_zipzap.gif', save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
for i in (10, 31, 44, 46, 47, 48, 49, 52, 70, 92, 100, 125):
    frames[i].save(f'/home/claude/titan/f{i:03d}.png')
print('ok', len(frames), slide_start)
