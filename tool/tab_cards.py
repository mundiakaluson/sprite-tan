import os, random, textwrap, tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import tables
from rules import *
from tab_players import next_id
import looks

SEEDS = os.path.join(tables.DATA, 'emblem_seeds.csv')
PREFIX = dict(SHOT='SH', PASS='PA', DRIBBLE='DR', DEFEND='DF', SUPPORT='SU', KEEPER='KP', TITAN='TI')


def seeds():
    if not os.path.exists(SEEDS):
        tables.write_csv(SEEDS, ['id', 'seed'], [])
    return tables.table('emblem_seeds')


def hexrgb(h):
    return looks.hexrgb(h)


def emblem(cid, cat, seed=None, n=12):
    """Symmetric pixel emblem, deterministic from the card id (or an explicit seed)."""
    rnd = random.Random(f'{cid}:{seed}' if seed else cid)
    g = [[0] * n for _ in range(n)]
    for y in range(n):
        for x in range(n // 2):
            d = ((x - n / 2 + .5) ** 2 + (y - n / 2 + .5) ** 2) ** .5
            g[y][x] = 1 if rnd.random() < max(0.25, 1.05 - d / (n / 2) * 0.62) else 0
    for _ in range(2):   # smooth so it reads as one shape
        h = [r[:] for r in g]
        for y in range(1, n - 1):
            for x in range(1, n // 2):
                c = sum(g[y + a][x + b] for a in (-1, 0, 1) for b in (-1, 0, 1))
                h[y][x] = 1 if c >= 4 else 0
        g = h
    for y in range(n):
        for x in range(n // 2): g[y][n - 1 - x] = g[y][x]
    base = hexrgb(CAT_COL.get(cat, '#9aa0ae'))
    im = Image.new('RGBA', (n + 2, n + 2), (0, 0, 0, 0)); px = im.load()
    for y in range(n):
        for x in range(n):
            if g[y][x]:
                k = 1.25 - 0.55 * y / n - (0.18 if (x in (0, n - 1) or not g[y][x - 1 if x else 0] or not g[y][min(n - 1, x + 1)]) else 0)
                px[x + 1, y + 1] = tuple(max(0, min(255, int(c * k))) for c in base) + (255,)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); op = out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if px[x, y][3]: op[x, y] = px[x, y]
            elif any(0 <= x + a < im.size[0] and 0 <= y + b < im.size[1] and px[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                op[x, y] = (20, 20, 32, 255)
    return out


def card_face(c, seed=None, scale=2):
    W, H = 120, 180
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rc = hexrgb(RARITY_COL.get(c.get('rarity'), '#9aa0ae')); cc = hexrgb(CAT_COL.get(c.get('cat'), '#9aa0ae'))
    d.rounded_rectangle([0, 0, W - 1, H - 1], 8, fill=rc); d.rounded_rectangle([3, 3, W - 4, H - 4], 6, fill=(30, 32, 44))
    d.rectangle([6, 6, W - 7, 17], fill=cc)
    f = ImageFont.load_default()
    d.text((9, 8), (c.get('cat') or '')[:8], fill=(255, 255, 255), font=f)
    d.text((W - 9, 8), c.get('timing', '')[:3] if c.get('timing') == 'ANYTIME' else 'ENG', fill=(255, 255, 255), font=f, anchor='ra')
    d.rectangle([6, 20, W - 7, 66], fill=(46, 50, 68))
    em = emblem(c.get('id', ''), c.get('cat'), seed).resize((14 * 3, 14 * 3), Image.NEAREST)
    im.alpha_composite(em, (W // 2 - 21, 23))
    name = c.get('name', '')
    d.text((W // 2, 74), name[:20], fill=(255, 255, 255), font=f, anchor='ma')
    d.text((W // 2, 85), c.get('stats') or c.get('kind', ''), fill=(170, 176, 196), font=f, anchor='ma')
    y = 98
    for k, lab in (('succ', 'SUCC'), ('risk', 'RISK'), ('cd', 'CD')):
        d.text((10, y), lab, fill=(150, 156, 176), font=f)
        v = to_int(c.get(k), 0)
        w = {'succ': v, 'risk': v, 'cd': min(100, v * 12)}[k]
        d.rectangle([42, y + 2, 42 + 50, y + 7], fill=(60, 64, 84)); d.rectangle([42, y + 2, 42 + int(50 * w / 100), y + 7], fill=(240, 90, 80) if k == 'risk' else cc)
        d.text((W - 8, y), str(v) + ('s' if k == 'cd' else ''), fill=(255, 255, 255), font=f, anchor='ra'); y += 11
    lines = textwrap.wrap(c.get('description', ''), 19)
    if len(lines) > 3: lines = lines[:3]; lines[2] = lines[2][:16] + '...'
    d.text((W // 2, 132), '\n'.join(lines), fill=(200, 204, 220), font=ImageFont.load_default(size=8) if hasattr(ImageFont, 'truetype') else f, anchor='ma', align='center', spacing=1)
    d.text((8, H - 17), f"{c.get('kind', '')}  x{c.get('slots', '')} slots", fill=(150, 156, 176), font=f)
    return im.resize((W * scale, H * scale), Image.NEAREST)


def new_card(t):
    r = {c: '' for c in t.cols}
    r.update(id=next_id(t, 'SH', 2), name='New Card', cat='SHOT', rarity='COMMON', slots='1', succ='70', risk='10', cd='4',
             timing='ENGAGEMENT', kind='ACTION', stats='SHO', description='Describe what it does.')
    return r


class CardsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('cards'); self.sd = seeds(); self.i = None
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        ch = dict(cat=CARD_CATS, rarity=RARITY, timing=TIMING, kind=KIND)
        self.grid = tables.Grid(pw, self.t, choices=ch, new_row=self.new, on_select=self.select, width_for=dict(name=150, description=320, stats=90))
        pw.add(self.grid, weight=3)
        side = ttk.Frame(pw, padding=6); pw.add(side, weight=1)
        self.cv = tk.Canvas(side, width=250, height=350, bg='#2a2c33', highlightthickness=0); self.cv.pack()
        ttk.Button(side, text='Re-roll emblem', command=self.reroll).pack(fill='x', pady=2)
        ttk.Button(side, text='Export all card faces (PNG)', command=self.export_all).pack(fill='x')
        ttk.Label(side, text='Edit cells in the table; the face updates live.\nEmblems are generated from the card id (placeholder art).', wraplength=240, justify='left').pack(pady=6)
        self.t.listeners.append(self.draw); self.sd.listeners.append(self.draw)

    def new(self, t):
        r = new_card(t); r['id'] = next_id(t, 'XX', 2); return r

    def select(self, idx):
        self.i = idx[0] if idx else None; self.draw()

    def seed(self, cid):
        for r in self.sd.rows:
            if r['id'] == cid: return r['seed']
        return None

    def draw(self):
        if self.i is None or self.i >= len(self.t.rows): return
        c = self.t.rows[self.i]
        self._ph = ImageTk.PhotoImage(card_face(c, self.seed(c['id']), 2)); self.cv.delete('all'); self.cv.create_image(125, 175, image=self._ph)

    def reroll(self):
        if self.i is None: return
        cid = self.t.rows[self.i]['id']; new = str(random.randint(1, 99999))
        for r in self.sd.rows:
            if r['id'] == cid: r['seed'] = new; break
        else:
            self.sd.rows.append(dict(id=cid, seed=new))
        self.sd.save(); self.draw()

    def export_all(self):
        out = os.path.join(tables.ROOT, 'export', 'cards'); os.makedirs(out, exist_ok=True)
        for c in self.t.rows:
            card_face(c, self.seed(c['id']), 4).save(os.path.join(out, c['id'] + '.png'))
        from tkinter import messagebox
        messagebox.showinfo('Export', f'Wrote {len(self.t.rows)} card faces to {out}')
