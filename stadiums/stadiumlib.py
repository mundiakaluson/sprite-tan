"""Stadium art generated from data/stadiums.csv, for the 3D stadium scene in Godot (TV / broadcast camera with real perspective).
Per stadium (godot/assets/pitches/<id>/): pitch.png (flat top-down ground texture: mowing, markings, wear, light baked in), stand.png (crowd rows, tiles sideways),
boards.png (advertising strip), thumb.png, layout.json. The 3D parts (stands, goals, flags, towers) are built in Godot from these (scripts/stadium/stadium.gd).
Texture orientation: x = along the pitch (own goal on the left), y = across (top = the far touchline). 16 px per metre.
    python stadiums/stadiumlib.py [out_dir]     writes every stadium + a contact sheet"""
import os, sys, csv, math, json
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data')
PPM = 16                    # pixels per metre on the pitch texture
LEN, WID = 105.0, 68.0
APR = 6.0                   # metres of grass around the lines
TW, TH = int((LEN + 2 * APR) * PPM), int((WID + 2 * APR) * PPM)
LINE = (236, 240, 230)
SKY = dict(day=(142, 186, 232), dusk=(228, 138, 94), night=(8, 12, 28))


def P(a, b): return ((a + APR) * PPM, (b + APR) * PPM)


def load():
    with open(os.path.join(DATA, 'stadiums.csv'), encoding='utf-8-sig') as f: return [dict(r) for r in csv.DictReader(f)]
def hexrgb(h): h = h.strip().lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))
def num(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return d
def rng_for(row, seed=1): return np.random.default_rng(sum(ord(c) * (i + 3) for i, c in enumerate(row['id'])) + seed)


# ---------------------------------------------------------------------------------------------- pitch
def draw_grass(row, rng):
    ga, gb = hexrgb(row['grass_a']), hexrgb(row['grass_b'])
    yy, xx = np.mgrid[0:TH, 0:TW]; a = xx / PPM - APR; b = yy / PPM - APR; band = 5.25; mow = row['mow']
    if mow == 'checker': k = (np.floor(a / band) + np.floor(b / band)) % 2
    elif mow == 'diagonal': k = np.floor((a + b) / band) % 2
    elif mow == 'rings': k = np.floor(np.hypot(a - LEN / 2, b - WID / 2) / band) % 2
    else: k = np.floor(a / band) % 2
    base = np.where(k[..., None] == 1, np.array(gb), np.array(ga)).astype(np.float32)
    n = rng.random(k.shape)
    base *= np.where(n < 0.08, 0.88, np.where(n > 0.96, 1.07, 1.0))[..., None]
    bay = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    base += ((bay[yy % 4, xx % 4] - 0.5) * 5)[..., None]
    worn = num(row.get('worn')) / 100.0
    if worn > 0:
        mud = np.array([112, 92, 58], np.float32)
        for (pa, pb, ra, rb) in ((11, 34, 7, 10), (94, 34, 7, 10), (52.5, 34, 6, 6), (3, 34, 5, 14), (102, 34, 5, 14), (16, 34, 8, 12), (89, 34, 8, 12)):
            d = np.hypot((a - pa) / ra, (b - pb) / rb); m = np.clip(1 - d, 0, 1) ** 0.8 * worn
            m = (m > 0.18 + 0.55 * rng.random(m.shape) * (1 - m)).astype(np.float32) * np.clip(m * 1.4, 0, 0.85)
            base = base * (1 - m[..., None]) + mud * m[..., None]
    img = np.zeros((TH, TW, 4), np.uint8); img[..., :3] = np.clip(base, 0, 255).astype(np.uint8); img[..., 3] = 255
    return img


def arc_pts(ca, cb, r, a0, a1, n=80, keep=None):
    pts = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n); p = (ca + r * math.cos(t), cb + r * math.sin(t))
        if keep is None or keep(p): pts.append(p)
    return pts


def draw_markings(im):
    d = ImageDraw.Draw(im); W = 2
    def poly(pts, w=W): d.line([P(*p) for p in pts], fill=LINE + (255,), width=w, joint='curve')
    def dot(a, b): x, y = P(a, b); d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=LINE + (255,))
    poly([(0, 0), (0, WID), (LEN, WID), (LEN, 0), (0, 0)]); poly([(LEN / 2, 0), (LEN / 2, WID)]); poly(arc_pts(LEN / 2, WID / 2, 9.15, 0, 360, 120)); dot(LEN / 2, WID / 2)
    for end in (0, 1):
        s = 1 if end == 0 else -1; g = 0.0 if end == 0 else LEN; pa = g + s * 16.5; pw0, pw1 = WID / 2 - 20.16, WID / 2 + 20.16
        poly([(g, pw0), (pa, pw0), (pa, pw1), (g, pw1)]); poly([(g, WID / 2 - 9.16), (g + s * 5.5, WID / 2 - 9.16), (g + s * 5.5, WID / 2 + 9.16), (g, WID / 2 + 9.16)])
        spot = g + s * 11.0; dot(spot, WID / 2)
        poly(arc_pts(spot, WID / 2, 9.15, -90 if s == 1 else 90, 90 if s == 1 else 270, 80, keep=lambda p, s=s, pa=pa: (p[0] - pa) * s > 0.05))
    for ca, cb, a0 in ((0, 0, 0), (0, WID, 270), (LEN, WID, 180), (LEN, 0, 90)): poly(arc_pts(ca, cb, 1.0, a0, a0 + 90, 10))


def lighting(arr, time, pools, strength=1.0, centre_pool=True):
    """tint + light pools for the time of day. arr is an HxWx4 uint8 array; pools are (x, y, radius) in pixels."""
    H, W = arr.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]; a = arr[..., :3].astype(np.float32)
    if time == 'night':
        f = np.full((H, W), 0.66, np.float32)
        for (lx, ly, r) in pools: f += np.clip(1 - np.hypot((xx - lx) / r, (yy - ly) / r), 0, 1) ** 1.3 * 0.40 * max(0.4, strength)
        if centre_pool: f += np.clip(1 - np.hypot((xx - W / 2) / (W * 0.6), (yy - H / 2) / (H * 0.7)), 0, 1) * 0.12
        a *= np.clip(f, 0.3, 1.05)[..., None] * np.array([0.86, 0.94, 1.08])
    elif time == 'dusk':
        a *= np.array([1.06, 0.88, 0.74]) * 0.94
        v = np.clip(np.hypot((xx - W / 2) / (W * 0.65), (yy - H / 2) / (H * 0.65)) - 0.45, 0, 1) * 0.45; a *= (1 - v)[..., None]
    arr[..., :3] = np.clip(a, 0, 255).astype(np.uint8)
    return arr


def render_pitch(row):
    rng = rng_for(row); arr = draw_grass(row, rng); im = Image.fromarray(arr, 'RGBA'); draw_markings(im); arr = np.array(im)
    pools = [(x, y, TW * 0.5) for (x, y) in (P(-4, -4), P(-4, WID + 4), P(LEN + 4, -4), P(LEN + 4, WID + 4))] if str(row.get('towers', '0')) == '1' else [(TW / 2, TH / 2, TW * 0.6)]
    return Image.fromarray(lighting(arr, row['time'], pools, num(row.get('light'), 1.0)), 'RGBA')


# ---------------------------------------------------------------------------------------------- stand, boards, net
def seat_rows(d, box, rows, row_px, row, rng, cols, seat, stand):
    x0, y0, x1, y1 = box; dens = num(row['crowd']) / 100.0; cell = 6
    for r in range(rows):
        t = r / max(1, rows - 1); shade = mix(seat, stand, 0.35 + 0.5 * t); ya = y1 - (r + 1) * row_px; yb = ya + row_px - 1
        d.rectangle([x0, ya, x1, yb], fill=mix(stand, (0, 0, 0), 0.25 + 0.25 * t) + (255,))
        for cx in range(x0, x1 - cell + 1, cell):
            if ((cx - x0) // cell) % 16 == 0: d.rectangle([cx, ya, cx + 2, yb], fill=mix(stand, (0, 0, 0), 0.5) + (255,)); continue
            d.rectangle([cx, yb - 1, cx + cell - 2, yb], fill=shade + (255,))
            if rng.random() < dens * (0.95 - 0.35 * t):
                body = cols[int(rng.integers(0, len(cols)))]; hx = cx + 1
                d.rectangle([hx, yb - 4, hx + 3, yb - 1], fill=body + (255,)); d.rectangle([hx + 1, yb - 6, hx + 2, yb - 5], fill=(226, 178, 140, 255))


def render_stand(row):
    rng = rng_for(row, 2); stand = hexrgb(row['stand']); seat = hexrgb(row['seat']); trim = hexrgb(row['stand_trim'])
    cols = [hexrgb(c) for c in row['crowd_colors'].split(';') if c.strip()] or [(200, 200, 200)]
    w, h = 512, 192; im = Image.new('RGBA', (w, h), mix(stand, (0, 0, 0), 0.5) + (255,)); d = ImageDraw.Draw(im)
    seat_rows(d, (0, 0, w - 1, h - 1), 27, 7, row, rng, cols, seat, stand)
    d.rectangle([0, h - 3, w, h], fill=trim + (255,))                                    # trim along the pitch edge of the stand
    arr = lighting(np.array(im), row['time'], [], 1.0, centre_pool=False)
    if row['time'] == 'night': arr[..., :3] = np.clip(arr[..., :3].astype(np.float32) * 1.25, 0, 255).astype(np.uint8)   # crowd glows a little under the lights
    return Image.fromarray(arr, 'RGBA')


def render_boards(row):
    rng = rng_for(row, 3); bc = hexrgb(row['board']); alt = mix(bc, (20, 20, 30), 0.55); acc = mix(bc, (255, 255, 255), 0.5)
    im = Image.new('RGBA', (512, 16), alt + (255,)); d = ImageDraw.Draw(im); x = 0
    while x < 512:
        w = int(rng.integers(40, 90)); col = [bc, alt, acc][int(rng.integers(0, 3))]
        d.rectangle([x, 1, min(x + w, 512) - 2, 14], fill=col + (255,)); d.line([(x, 1), (min(x + w, 512) - 2, 1)], fill=mix(col, (255, 255, 255), 0.4) + (255,))
        for k in range(3): d.rectangle([x + 6 + k * 11, 6, x + 12 + k * 11, 9], fill=mix(col, (255, 255, 255), 0.55) + (255,))
        x += w
    arr = lighting(np.array(im), row['time'], [], 1.0, centre_pool=False)
    if row['time'] == 'night': arr[..., :3] = np.clip(arr[..., :3].astype(np.float32) * 1.3, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')


def render_net():
    im = Image.new('RGBA', (8, 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.line([(0, 0), (7, 0)], fill=(240, 244, 240, 200)); d.line([(0, 0), (0, 7)], fill=(240, 244, 240, 200)); return im


# ---------------------------------------------------------------------------------------------- output
def layout(row):
    return dict(id=row['id'], name=row['name'], time=row['time'], ppm=PPM, apron=APR, pitch_m=[LEN, WID], texture=[TW, TH], sky=SKY[row['time']],
                towers=str(row.get('towers', '0')) == '1', roof=str(row.get('roof', '0')) == '1', stand=list(hexrgb(row['stand'])), trim=list(hexrgb(row['stand_trim'])),
                light=num(row.get('light')), goal=row.get('goal', 'G01'), cam=dict(height=num(row.get('cam_height'), 26), back=num(row.get('cam_back'), 16), look_z=num(row.get('look_z'), -4), fov=num(row.get('fov'), 34)), capacity=int(num(row.get('capacity'))),
                view='TV side-on, perspective camera behind the near touchline; pitch x along (own goal at -x), z across (far touchline at -z)')


def render_all(out_dir, log=print, tick=None):
    rows = load(); os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):                                    # drop art from older layouts
        pth = os.path.join(out_dir, f)
        if os.path.isdir(pth):
            for g in os.listdir(pth):
                if g in ('backdrop.png', 'goal_back.png', 'goal_front.png', 'goal_far.png', 'goal_near.png', 'corner_flag.png'): os.remove(os.path.join(pth, g))
    for i, row in enumerate(rows):
        d = os.path.join(out_dir, row['id']); os.makedirs(d, exist_ok=True); p = render_pitch(row)
        p.save(os.path.join(d, 'pitch.png')); p.resize((TW // 4, TH // 4), Image.NEAREST).save(os.path.join(d, 'thumb.png'))
        render_stand(row).save(os.path.join(d, 'stand.png')); render_boards(row).save(os.path.join(d, 'boards.png'))
        json.dump(layout(row), open(os.path.join(d, 'layout.json'), 'w'), indent=1)
        log(f"  {row['id']} {row['name']}: pitch {TW}x{TH}")
        if tick: tick(i + 1, len(rows))
    json.dump([dict(id=r['id'], name=r['name'], time=r['time'], capacity=int(num(r.get('capacity')))) for r in rows], open(os.path.join(out_dir, 'stadiums.json'), 'w'), indent=1)
    return len(rows)


def check(rows):
    out = []; ids = set()
    for r in rows:
        if r['id'] in ids: out.append(('error', r['id'], 'duplicate id'))
        ids.add(r['id'])
        for c in ('grass_a', 'grass_b', 'stand', 'stand_trim', 'seat', 'board'):
            try: hexrgb(r[c])
            except Exception: out.append(('error', r['id'], f'{c} must be #rrggbb'))
        if r.get('time') not in ('day', 'dusk', 'night'): out.append(('error', r['id'], 'time must be day, dusk or night'))
        if r.get('mow') not in ('stripes', 'checker', 'diagonal', 'rings'): out.append(('error', r['id'], 'mow must be stripes, checker, diagonal or rings'))
    return out


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'export', 'stadiums')
    n = render_all(out); rows = load(); sheet = Image.new('RGB', (TW // 3 * n + 10 * (n + 1), TH // 3 + 20 + 80), (20, 20, 28))
    for i, r in enumerate(rows):
        sheet.paste(Image.open(os.path.join(out, r['id'], 'pitch.png')).convert('RGB').resize((TW // 3, TH // 3), Image.NEAREST), (10 + i * (TW // 3 + 10), 10))
        st = Image.open(os.path.join(out, r['id'], 'stand.png')).convert('RGB').resize((TW // 3, 80), Image.NEAREST); sheet.paste(st, (10 + i * (TW // 3 + 10), TH // 3 + 14))
    sheet.save(os.path.join(out, 'sheet.png')); print('wrote', n, 'stadiums to', out)
