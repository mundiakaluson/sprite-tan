import os, sys, math
import numpy as np
import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image, ImageTk, ImageDraw
import tables
BL_DIR = os.path.join(tables.ROOT, 'balls')
if BL_DIR not in sys.path: sys.path.insert(0, BL_DIR)
import balllib as BL

SLIDERS = [('gravity', 'Gravity m/s2', 0.5, 25, 0.05), ('air_drag', 'Air drag', 0.0, 0.04, 0.0005), ('magnus', 'Swerve (Magnus)', 0, 0.015, 0.0002), ('knuckle', 'Knuckle wobble m', 0, 1.5, 0.01),
           ('knuckle_speed', 'Knuckle above m/s', 3, 40, 0.5), ('crisis', 'Dip (drag jump)', 0, 3, 0.05), ('crisis_speed', 'Dip below m/s', 3, 40, 0.5), ('restitution', 'Bounce', 0, 1, 0.01),
           ('friction', 'Grip on grass', 0, 1.5, 0.01), ('roll_drag', 'Rolling drag', 0, 2, 0.01), ('spin_decay', 'Spin decay /s', 0, 1.5, 0.01), ('mass', 'Mass kg', 0.2, 1.0, 0.01),
           ('radius', 'Radius m (game)', 0.08, 0.3, 0.005), ('touch', 'First touch (gameplay)', 0.4, 1.6, 0.01), ('power', 'Kick power (gameplay)', 0.5, 1.6, 0.01)]
SHOT = [('speed', 'Speed m/s', 8, 45, 28), ('elev', 'Elevation deg', 0, 45, 8), ('azim', 'Aim sideways deg', -25, 25, 0), ('side', 'Side spin rad/s', -80, 80, 0), ('back', 'Back spin rad/s', -60, 60, 0), ('roll', 'Roll spin rad/s', -60, 60, 0)]
KICK_COLS = ('speed', 'elev', 'azim', 'side', 'back', 'roll')
COLS = ['#e8453c', '#3c8fe8', '#e8b83c', '#5bd17a', '#b36be8', '#e8863c']


def new_kick(t):
    n = 1
    while any(r['id'] == f'K{n:02d}' for r in t.rows): n += 1
    return dict(id=f'K{n:02d}', name='New kick', speed='25', elev='10', azim='0', side='0', back='0', roll='0', power='1.0', error='1.5', note='')


def new_ball(t):
    n = 1
    while any(r['id'] == f'B{n:02d}' for r in t.rows): n += 1
    return dict(id=f'B{n:02d}', name='New ball', mass='0.43', radius='0.17', gravity='9.81', air_drag='0.012', magnus='0.0058', knuckle='0.03', knuckle_speed='18', crisis='0', crisis_speed='14', restitution='0.75',
                friction='0.6', roll_drag='0.25', spin_decay='0.15', touch='1.0', power='1.0', pattern='classic', color_a='#f4f4f0', color_b='#23232b', color_c='#9a9aa6', shine='1', note='')


class BallsTab(ttk.Frame):
    """Ball studio: edit a ball's physics (gravity, drag, swerve, knuckle instability, bounce, grip), its pixel texture and its gameplay effect (first touch, kick power). The trajectory lab fires it and compares all balls."""
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('balls'); self.kt = tables.table('kick_styles'); self.i = None; self.fr = 0; self._map = {}; self.M = np.eye(3)
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw); pw.add(left)
        nb = ttk.Notebook(left); nb.pack(fill='both', expand=True); gb = ttk.Frame(nb); gk = ttk.Frame(nb); nb.add(gb, text='Balls'); nb.add(gk, text='Kick styles (spin)')
        self.kgrid = tables.Grid(gk, self.kt, new_row=new_kick, on_select=self.pick_kick, width_for=dict(id=45, name=110, note=260)); self.kgrid.pack(fill='both', expand=True)
        self.grid_ = tables.Grid(gb, self.t, choices=dict(pattern=BL.PATTERNS, shine=['0', '1']), new_row=new_ball, on_select=self.select,
                                 hide=tuple(k for k, *_ in SLIDERS if k not in ('mass',)) + ('note', 'color_a', 'color_b', 'color_c', 'shine', 'radius'), width_for=dict(id=50, name=110)); self.grid_.pack(fill='both', expand=True)
        ctl = ttk.LabelFrame(left, text='Physics + gameplay (live; Save writes data/balls.csv)', padding=6); ctl.pack(fill='x')
        self.sl = {}
        for n, (f, lab, lo, hi, st) in enumerate(SLIDERS):
            r, c = n // 2, (n % 2) * 2
            ttk.Label(ctl, text=lab).grid(row=r, column=c, sticky='w', padx=4); v = tk.DoubleVar(value=lo)
            ttk.Scale(ctl, from_=lo, to=hi, variable=v, length=130, command=lambda _v, f=f, st=st: self.slide(f, st)).grid(row=r, column=c + 1, padx=4, pady=1); self.sl[f] = (v, st)
        r0 = (len(SLIDERS) + 1) // 2; self.btn = {}
        for n, (f, lab) in enumerate((('color_a', 'Base'), ('color_b', 'Patches'), ('color_c', 'Seams'))):
            ttk.Label(ctl, text=lab).grid(row=r0, column=n * 2 if n < 2 else 0, sticky='w', padx=4) if n < 2 else None
        cf = ttk.Frame(ctl); cf.grid(row=r0, column=0, columnspan=4, sticky='w', pady=4)
        for f, lab in (('color_a', 'Base'), ('color_b', 'Patches'), ('color_c', 'Seams')):
            ttk.Label(cf, text=lab).pack(side='left', padx=(4, 2)); b = tk.Button(cf, width=6, command=lambda f=f: self.pick(f)); b.pack(side='left', padx=2); self.btn[f] = b
        ttk.Label(cf, text='  Pattern').pack(side='left'); self.pat = ttk.Combobox(cf, values=BL.PATTERNS, width=9, state='readonly'); self.pat.pack(side='left', padx=2)
        self.pat.bind('<<ComboboxSelected>>', lambda _e: self.set('pattern', self.pat.get()))
        self.shine = tk.IntVar(value=1); ttk.Checkbutton(cf, text='Shine', variable=self.shine, command=lambda: self.set('shine', str(self.shine.get()))).pack(side='left', padx=6)
        side = ttk.Frame(pw, padding=4, width=660); side.pack_propagate(False); pw.add(side)
        top = ttk.Frame(side); top.pack(fill='x')
        self.pv = tk.Canvas(top, width=150, height=150, bg='#46964a', highlightthickness=0); self.pv.pack(side='left')
        self.info = ttk.Label(top, text='', justify='left', wraplength=480); self.info.pack(side='left', padx=8, anchor='n')
        self.cv = tk.Canvas(side, width=640, height=330, bg='#2a5a32', highlightthickness=0); self.cv.pack(pady=4)
        c1 = ttk.LabelFrame(side, text='Trajectory lab: every ball is fired the same way; the selected ball is the thick line', padding=4); c1.pack(fill='x')
        self.v = {}
        for n, (k, lab, lo, hi, d) in enumerate(SHOT):
            ttk.Label(c1, text=lab).grid(row=n // 3, column=(n % 3) * 2, sticky='w', padx=2); self.v[k] = tk.DoubleVar(value=d)
            ttk.Scale(c1, from_=lo, to=hi, variable=self.v[k], length=85, command=lambda _v: self.plot()).grid(row=n // 3, column=(n % 3) * 2 + 1, padx=2, pady=1)
        pr = ttk.Frame(side); pr.pack(fill='x', pady=3)
        ttk.Label(pr, text='Kick style').pack(side='left'); self.ks = ttk.Combobox(pr, values=[r['name'] for r in self.kt.rows], width=18, state='readonly'); self.ks.pack(side='left', padx=4)
        self.ks.bind('<<ComboboxSelected>>', lambda _e: self.apply_style(self.ks.current()))
        ttk.Button(pr, text='New wobble (other seed)', command=self.reseed).pack(side='left', padx=6); self.seed = 1.0
        self.kt.listeners.append(lambda: self.ks.config(values=[r['name'] for r in self.kt.rows]))
        self.t.listeners.append(self.changed)
        if self.kt.rows: self.ks.current(0); self.apply_style(0)
        self.after(90, self.tick)

    def row(self): return self.t.rows[self.i] if self.i is not None and self.i < len(self.t.rows) else None
    def select(self, idx): self.i = idx[0] if idx else None; self.sync(); self.plot()

    def sync(self):
        r = self.row()
        if not r: return
        for f, (v, st) in self.sl.items(): v.set(BL.num(r, f))
        for f, b in self.btn.items():
            try: b.config(bg=r.get(f) or '#ffffff', activebackground=r.get(f) or '#ffffff')
            except tk.TclError: pass
        self.pat.set(r.get('pattern', 'classic')); self.shine.set(int(BL.num(r, 'shine', 1)))

    def set(self, f, v):
        if self.i is not None: self.t.set(self.i, f, v)

    def slide(self, f, st):
        if self.i is None: return
        v = round(self.sl[f][0].get() / st) * st; self.t.set(self.i, f, f'{v:.6g}', snap=False)

    def pick(self, f):
        r = self.row()
        if not r: return
        c = colorchooser.askcolor(color=r.get(f) or '#ffffff')[1]
        if c: self.set(f, c)

    def changed(self):
        self._map.clear(); self.plot()

    def pick_kick(self, idx):
        if idx: self.apply_style(idx[0])

    def apply_style(self, i):
        if i is None or i < 0 or i >= len(self.kt.rows): return
        k = self.kt.rows[i]
        for c in KICK_COLS: self.v[c].set(BL.num(k, c))
        self.M = np.eye(3); self.plot()

    def reseed(self): self.seed += 1; self.plot()

    # ---- spinning preview: the ball turns with the spin of the current kick, seen from behind the ball (slow motion)
    def spin_vec(self):
        return BL.spin_vector(self.v['roll'].get(), self.v['side'].get(), self.v['back'].get(), self.v['azim'].get())

    def tick(self):
        try:
            r = self.row()
            if r and self.winfo_viewable():
                if r['id'] not in self._map: self._map[r['id']] = BL.render_map(r)
                w = self.spin_vec(); self.M = BL.rot_axis(w, 0.03) @ self.M
                f = BL.render_orient(r, BL.CHASE_VIEW @ self.M, self._map[r['id']]).resize((144, 144), Image.NEAREST)
                bg = Image.new('RGBA', (150, 150), (70, 150, 74, 255)); bg.alpha_composite(f, (3, 3)); self._ph = ImageTk.PhotoImage(bg); self.pv.delete('all'); self.pv.create_image(0, 0, anchor='nw', image=self._ph)
        except Exception as e: self.info.config(text=f'preview error: {e}')
        self.after(60, self.tick)

    # ---- trajectory lab: side view (top) and top view (bottom) of every ball, fired the same way
    def plot(self):
        r = self.row()
        if not r or not self.winfo_viewable(): return
        s = {k: self.v[k].get() for k in self.v}; W, H = 640, 330; im = Image.new('RGB', (W, H), (42, 90, 50)); d = ImageDraw.Draw(im)
        side_box, top_box = (30, 8, W - 10, 168), (30, 182, W - 10, H - 8); rows = list(self.t.rows); res = {}
        for n, b in enumerate(rows):
            try: res[b['id']] = BL.trajectory(b, s['speed'], s['elev'], s['azim'], s['side'], s['back'], seed=self.seed, roll_spin=s['roll'])
            except Exception: pass
        sp_ = res.get(r['id']); xmax = min(120.0, max(20.0, float(sp_[:, 0].max()) * 1.1)) if sp_ is not None else 40.0; ymax = max(3.0, float(sp_[:, 1].max())) if sp_ is not None else 3.0; zr = max(3.0, float(np.abs(sp_[:, 2]).max())) if sp_ is not None else 3.0
        for box, ymin_, ymax_ in ((side_box, 0, ymax * 1.1), (top_box, -zr * 1.1, zr * 1.1)):
            d.rectangle(box, outline=(120, 170, 130)); [d.line([(box[0] + (box[2] - box[0]) * m / xmax, box[1]), (box[0] + (box[2] - box[0]) * m / xmax, box[3])], fill=(60, 110, 66)) for m in range(0, int(xmax), 10)]
        def px(box, x, y, lo, hi): return box[0] + (box[2] - box[0]) * x / xmax, box[3] - (box[3] - box[1]) * (y - lo) / (hi - lo)
        d.line([px(top_box, 0, 0, -zr * 1.1, zr * 1.1), px(top_box, xmax, 0, -zr * 1.1, zr * 1.1)], fill=(200, 220, 200)); d.line([px(side_box, 0, 0, 0, ymax * 1.1), px(side_box, xmax, 0, 0, ymax * 1.1)], fill=(200, 220, 200))
        for n, b in enumerate(rows):
            p = res.get(b['id'])
            if p is None: continue
            sel = b['id'] == r['id']; col = COLS[n % len(COLS)]; w = 3 if sel else 1; m = (p[:, 0] <= xmax) & (p[:, 1] <= ymax * 1.1) & (np.abs(p[:, 2]) <= zr * 1.1)
            d.line([px(side_box, x, y, 0, ymax * 1.1) for x, y in zip(p[m, 0], p[m, 1])], fill=col, width=w); d.line([px(top_box, x, z, -zr * 1.1, zr * 1.1) for x, z in zip(p[m, 0], p[m, 2])], fill=col, width=w)
            d.text((W - 150, 10 + n * 12), f"{b['id']} {b['name']}"[:22], fill=col)
        d.text((34, 10), 'side view (height)', fill=(210, 230, 210)); d.text((34, 184), f'top view (+- {zr:.1f} m sideways)', fill=(210, 230, 210)); d.text((W - 60, H - 20), f'{xmax:.0f} m', fill=(210, 230, 210))
        self._pl = ImageTk.PhotoImage(im); self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self._pl)
        p = res.get(r['id'])
        if p is not None:
            lat = float(np.interp(min(25.0, float(p[-1, 0])), p[:, 0], p[:, 2]))
            w = float(np.linalg.norm(self.spin_vec())); turn = 'barely turns (a knuckle ball)' if w < BL.SPIN_LO else f'spins {w:.0f} rad/s ({w / math.tau:.1f} turns a second)'
            self.info.config(text=f"{r['name']}, {turn}: flies {p[-1, 0]:.0f} m, peaks {p[:, 1].max():.1f} m high, {lat:+.2f} m sideways at 25 m. Gameplay: first touch x{BL.num(r, 'touch', 1):.2f}, kick power x{BL.num(r, 'power', 1):.2f} "
                                  f"(launch speed {s['speed'] * BL.num(r, 'power', 1):.1f} m/s). {r.get('note', '')}")

    def refresh(self): self._map.clear(); self.plot()
