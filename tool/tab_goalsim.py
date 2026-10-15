import os, sys, threading, queue, time
import numpy as np
import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image, ImageTk
import tables
ST_DIR = os.path.join(tables.ROOT, 'stadiums')
if ST_DIR not in sys.path: sys.path.insert(0, ST_DIR)
import stadiumlib as SL, goallib as GL, preview as PV

SLIDERS = [('stiffness', 'Net stiffness', 0.05, 1.0, 0.01), ('damping', 'Net damping', 0.0, 0.1, 0.002), ('gravity', 'Net sag / gravity', 0, 20, 0.5), ('drag', 'Net drag on ball', 0, 30, 0.5),
           ('post_sway', 'Post stiffness', 5, 300, 1), ('post_damp', 'Post damping', 0, 20, 0.2), ('bounce', 'Frame bounce', 0, 1, 0.05), ('stretch', 'Stretch (0 hard, 1 soft)', 0, 1, 0.01), ('wear', 'Wear % (0 new)', 0, 100, 1)]
GEOM = [('width', 'Width m', 3, 9, 0.02), ('height', 'Height m', 1.5, 3, 0.02), ('depth', 'Depth top m', 0.5, 4, 0.05), ('depth_low', 'Depth ground m', 0.5, 4, 0.05), ('mesh', 'Net cell m', 0.2, 0.7, 0.01)]
VIEWS = ['Front side', 'Behind the goal', 'TV camera']
X0 = SL.LEN / 2


def new_goal(t):
    n = 1
    while any(r['id'] == f'G{n:02d}' for r in t.rows): n += 1
    return dict(id=f'G{n:02d}', name='New goal', width='7.32', height='2.44', depth='2.0', depth_low='2.0', mesh='0.35', post_radius='0.06', post_color='#f6f6f2', net_color='#f0f4f0', net_alpha='200', stretch='0.2', wear='0',
                stiffness='0.55', damping='0.015', gravity='6.0', drag='7.0', post_sway='60', post_damp='4.0', bounce='0.55', note='')


class GoalSimTab(ttk.Frame):
    """Goal simulator: pick a goal style, fire the ball at it, watch the net and posts react, tune the numbers and Save (data/goals.csv)."""
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('goals'); self.st = tables.table('stadiums'); self.i = None; self.net = None; self.q = queue.Queue(); self.bg = None; self.bgkey = None; self.cache = {}; self.bgbusy = False
        self.ball = None; self.running = False; self.trail = []; self.info = ''; self.nets = None
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw); pw.add(left)
        self.grid_ = tables.Grid(left, self.t, new_row=new_goal, on_select=self.select, hide=('note', 'post_color', 'net_color', 'net_alpha', 'post_radius'), width_for=dict(id=50, name=110)); self.grid_.pack(fill='both', expand=True)
        ctl = ttk.LabelFrame(left, text='Net and post feel (live; Save writes data/goals.csv)', padding=6); ctl.pack(fill='x')
        self.sl = {}
        for n, (f, lab, lo, hi, st) in enumerate(SLIDERS + GEOM):
            r, c = n // 2, (n % 2) * 2
            ttk.Label(ctl, text=lab).grid(row=r, column=c, sticky='w', padx=4)
            v = tk.DoubleVar(value=lo); ttk.Scale(ctl, from_=lo, to=hi, variable=v, length=120, command=lambda _v, f=f, st=st: self.slide(f, st)).grid(row=r, column=c + 1, padx=4, pady=1); self.sl[f] = (v, st)
        self.btn = {}
        r0 = (len(SLIDERS + GEOM) + 1) // 2
        for n, (f, lab) in enumerate((('post_color', 'Posts'), ('net_color', 'Net'))):
            ttk.Label(ctl, text=lab + ' colour').grid(row=r0, column=n * 2, sticky='w', padx=4)
            b = tk.Button(ctl, width=8, command=lambda f=f: self.pick(f)); b.grid(row=r0, column=n * 2 + 1, sticky='w', padx=4, pady=3); self.btn[f] = b
        side = ttk.Frame(pw, padding=4, width=660); side.pack_propagate(False); pw.add(side)
        self.cv = tk.Canvas(side, width=640, height=360, bg='#10131a', highlightthickness=0); self.cv.pack()
        c1 = ttk.LabelFrame(side, text='Shot', padding=6); c1.pack(fill='x', pady=4)
        self.v = dict(speed=tk.DoubleVar(value=24), aimz=tk.DoubleVar(value=1.5), aimy=tk.DoubleVar(value=1.4), fromz=tk.DoubleVar(value=-4), dist=tk.DoubleVar(value=16))
        for n, (k, lab, lo, hi) in enumerate((('speed', 'Speed m/s', 5, 45), ('aimz', 'Aim across m', -6, 6), ('aimy', 'Aim height m', 0, 4), ('fromz', 'From across m', -20, 20), ('dist', 'Distance m', 6, 30))):
            ttk.Label(c1, text=lab).grid(row=n // 3, column=(n % 3) * 2, sticky='w', padx=2); ttk.Scale(c1, from_=lo, to=hi, variable=self.v[k], length=85).grid(row=n // 3, column=(n % 3) * 2 + 1, padx=2, pady=1)
        bar = ttk.Frame(side); bar.pack(fill='x', pady=2)
        ttk.Button(bar, text='Shoot  (Space)', command=self.shoot).pack(side='left'); ttk.Button(bar, text='Reset net', command=self.reset).pack(side='left', padx=4)
        ttk.Button(bar, text='Hit the post', command=lambda: self.preset(3.66, 1.2)).pack(side='left'); ttk.Button(bar, text='Top bin', command=lambda: self.preset(3.0, 2.2)).pack(side='left', padx=4)
        ttk.Button(bar, text='Crossbar', command=lambda: self.preset(0.0, 2.44)).pack(side='left')
        bar2 = ttk.Frame(side); bar2.pack(fill='x', pady=2)
        ttk.Label(bar2, text='View').pack(side='left'); self.view = ttk.Combobox(bar2, values=VIEWS, width=14, state='readonly'); self.view.set(VIEWS[0]); self.view.pack(side='left')
        self.view.bind('<<ComboboxSelected>>', lambda _e: self.make_bg())
        ttk.Label(bar2, text='  Stadium').pack(side='left'); self.stad = ttk.Combobox(bar2, values=[r['id'] for r in self.st.rows], width=6, state='readonly'); self.stad.set(self.st.rows[0]['id'] if self.st.rows else ''); self.stad.pack(side='left')
        self.stad.bind('<<ComboboxSelected>>', lambda _e: self.make_bg())
        self.msg = ttk.Label(side, text='', foreground='#9aa0ae'); self.msg.pack(anchor='w')
        ttk.Label(side, justify='left', foreground='#9aa0ae', wraplength=620,
                  text='Pick a goal in the grid and shoot. The net is a mesh of linked points: the front edge and the ground edge are pegged, the rest billows and settles. Stiffness = how tight the net is; '
                       'damping = how fast it calms down; drag = how much the net slows the ball. Posts and bar wobble when hit. The same numbers drive the Godot goal (scripts/stadium/goal.gd).').pack(anchor='w', pady=4)
        self.t.listeners.append(self.table_changed); self.after(33, self.tick); self.after(150, self.poll); self.bind_all('<space>', lambda e: self.shoot() if self.winfo_viewable() and not isinstance(self.focus_get(), (tk.Entry, ttk.Entry, ttk.Combobox)) else None)

    # ---- selection and edits
    def row(self): return self.t.rows[self.i] if self.i is not None and self.i < len(self.t.rows) else None

    def select(self, idx):
        self.i = idx[0] if idx else None; self.sync(); self.build_net(); self.make_bg()

    def sync(self):
        r = self.row()
        if not r: return
        for f, (v, st) in self.sl.items(): v.set(GL.f(r, f))
        for f, b in self.btn.items():
            try: b.config(bg=r.get(f) or '#ffffff', activebackground=r.get(f) or '#ffffff')
            except tk.TclError: pass

    def slide(self, f, st):
        if self.i is None: return
        v = round(self.sl[f][0].get() / st) * st; self.t.set(self.i, f, f'{v:g}', snap=False)

    def pick(self, f):
        r = self.row()
        if not r: return
        c = colorchooser.askcolor(color=r.get(f) or '#ffffff')[1]
        if c: self.t.set(self.i, f, c)

    def table_changed(self):
        r = self.row()
        if not r or not self.net: return
        geo = tuple(r.get(k) for k in ('width', 'height', 'depth', 'depth_low', 'mesh', 'wear'))
        if geo != getattr(self, '_geo', None): self.build_net()
        else:
            for n in self.nets.values(): n.apply(r)
        self.sync() if False else None

    def build_net(self):
        r = self.row()
        if not r: return
        self._geo = tuple(r.get(k) for k in ('width', 'height', 'depth', 'depth_low', 'mesh', 'wear')); self.net = GL.Net(r); self.nets = {1: self.net, -1: GL.Net(r)}; self.ball = None; self.trail = []; self.info = ''

    def reset(self): self.build_net()

    # ---- background (stadium without goals), cached per view
    def make_bg(self):
        r = self.stad_row()
        if not r or self.bgbusy: return
        self.bgbusy = True; view = self.view.get(); rr = dict(r); self.msg.config(text='rendering the stadium...')

        def work():
            try:
                cam = self.camera(rr, view); img = PV.render(rr, cam=cam, size=(960, 540), cache=self.cache, goals=False); self.q.put(('bg', (img.resize((640, 360), Image.LANCZOS), cam, view)))
            except Exception as e: self.q.put(('err', repr(e)))
        threading.Thread(target=work, daemon=True).start()

    def stad_row(self):
        for r in self.st.rows:
            if r['id'] == self.stad.get(): return r
        return self.st.rows[0] if self.st.rows else None

    @staticmethod
    def camera(row, view):
        if view == 'Behind the goal': return PV.Cam.look((X0 + 9.0, 2.6, 5.0), (X0 - 6.0, 1.0, 0.0), 46)
        if view == 'TV camera': return PV.Cam.look((X0 - 14.0, 24.0, 34 + 14.0), (X0 - 14.0, 0.0, -2.0), 36)
        return PV.Cam.look((X0 - 15.0, 4.2, 15.0), (X0 + 0.5, 1.0, 0.0), 40)

    def poll(self):
        try:
            while True:
                k, v = self.q.get_nowait()
                if k == 'bg': self.bgbusy = False; self.bg, self.cam, _ = v; self.msg.config(text='')
                else: self.bgbusy = False; self.msg.config(text='error: ' + v)
        except queue.Empty: pass
        self.after(150, self.poll)

    # ---- shot
    def preset(self, z, y): self.v['aimz'].set(z); self.v['aimy'].set(y); self.shoot()

    def shoot(self):
        if self.net is None: return
        sp = self.v['speed'].get(); tz, ty = self.v['aimz'].get(), self.v['aimy'].get(); fz, dist = self.v['fromz'].get(), self.v['dist'].get()
        p0 = np.array([X0 - dist, GL.BALL_R, fz]); tgt = np.array([X0, ty, tz]); d = tgt - p0; dh = float(np.hypot(d[0], d[2])); t = dh / sp
        vel = np.array([d[0] / t, (d[1] + 0.5 * 9.81 * t * t) / t, d[2] / t]); self.ball = [p0, vel]; self.trail = []; self.running = True; self.info = ''
        self.hit_log = []

    def tick(self):
        t0 = time.time()
        try:
            if self.winfo_viewable() and self.bg is not None and self.net is not None: self.step_and_draw()
        except Exception as e: self.msg.config(text=f'sim error: {e!r}')
        self.after(max(5, 33 - int((time.time() - t0) * 1000)), self.tick)

    def step_and_draw(self):
        dt = GL.STEP; sub = 4
        for _ in range(sub):
            ball = None
            if self.ball is not None:
                p, v = self.ball; p, v = GL.ball_flight(p, v, dt)
                loc = (p - np.array([X0, 0, 0]), v, GL.BALL_R); nv, hits = self.net.step(dt, ball=loc if abs(p[0] - X0) < 4 and abs(p[2]) < 6 else None)
                if nv is not None and hits: v = nv
                for h in hits:
                    if h[0] != 'net' and (not self.hit_log or self.hit_log[-1] != h[0]): self.hit_log.append(h[0]); self.info = 'hit the ' + h[0] + (' post' if h[0] != 'bar' else '')
                    elif h[0] == 'net' and not self.info: self.info = 'in the net'
                self.ball = [p, v]; self.trail.append(p.copy())
                if abs(v).sum() < 0.3 and p[1] < 0.2: self.ball = [p, np.zeros(3)]
            else: self.net.step(dt)
            self.nets[-1].step(dt)
        img = self.bg.copy(); full = self.cam
        from PIL import ImageDraw
        sc = 640 / 960.0; small = PV.Cam.look(full.pos, full.pos + full.fwd, 1) if False else None
        cam = PV.Cam(size=(640, 360)); cam.pos, cam.fwd, cam.right, cam.up, cam.f = full.pos, full.fwd, full.right, full.up, full.f * sc
        d = ImageDraw.Draw(img, 'RGBA')
        for tp in self.trail[-60::3]:
            x, y, z = cam.pt(tp)
            if z > 0.5: d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(255, 255, 255, 90))
        PV.draw_goal(img, cam, self.nets[-1], -1); PV.draw_goal(img, cam, self.net, 1)
        if self.ball is not None:
            p = self.ball[0]; px, py, pz = cam.pt(p); gx, gy, _ = cam.pt((p[0], 0, p[2])); r = max(2.5, cam.f * GL.BALL_R / max(pz, 0.5))
            d.ellipse([gx - r * 1.1, gy - r * 0.4, gx + r * 1.1, gy + r * 0.4], fill=(0, 0, 0, 90)); d.ellipse([px - r, py - r, px + r, py + r], fill=(250, 250, 250, 255), outline=(30, 30, 30, 255))
        d.text((8, 6), f'{self.info}   net energy {self.net.energy:.1f}', fill=(230, 230, 240, 255))
        self._ph = ImageTk.PhotoImage(img); self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self._ph)

    def refresh(self):
        self.cache.clear(); self.make_bg()
