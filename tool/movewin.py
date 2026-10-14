"""Live move player for a skill card: plays the card's animation (data/animations/<id>_*.json), any of the 32 directions, auto-rotate."""
import time
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk
import looks  # puts sprites/ on the path
import gen_uv as U
import custom_anims as C
import moves as M
import aura
import overlays

KITS = ['home', 'away']


def find(cid):
    pre = cid.lower() + '_'
    return next((n for n in C.files() if n.startswith(pre)), None)


class MovePanel(ttk.Frame):
    """Small embedded player: set_card(card) loads data/animations/<id>_*.json; rotate by slider or auto-rotate."""
    def __init__(self, master, S=6):
        super().__init__(master); self.S = S; self.name = None; self.a = None; self.poses = []; self.f = 0; self.playing = True; self.cache = {}
        n = int(U.CW * S), int(U.CH * S)
        self.cv = tk.Canvas(self, width=n[0], height=n[1], bg='#222', highlightthickness=0); self.cv.pack()
        r = ttk.Frame(self); r.pack(fill='x', pady=2)
        self.playb = ttk.Button(r, text='Pause', width=6, command=self.toggle); self.playb.pack(side='left')
        self.dirv = tk.IntVar(value=8); self.rot = tk.BooleanVar(value=False); self.ball = tk.BooleanVar(value=True); self.spd = tk.DoubleVar(value=1.0)
        ttk.Checkbutton(r, text='auto-rotate', variable=self.rot).pack(side='left', padx=4)
        ttk.Checkbutton(r, text='ball', variable=self.ball).pack(side='left')
        ttk.Label(r, text='speed').pack(side='left', padx=(6, 2)); ttk.Scale(r, from_=0.25, to=2, variable=self.spd, length=70).pack(side='left')
        r2 = ttk.Frame(self); r2.pack(fill='x')
        ttk.Label(r2, text='angle').pack(side='left')
        ttk.Scale(r2, from_=0, to=31, variable=self.dirv, command=lambda e: (self.render(), self.after(1, lambda g=self._gen: self.warm(g))), length=n[0] - 150).pack(side='left', padx=4)
        self.foot = tk.StringVar(value='R'); ttk.Label(r2, text='foot').pack(side='left', padx=(4, 1))
        fc = ttk.Combobox(r2, values=['R', 'L'], textvariable=self.foot, state='readonly', width=2); fc.pack(side='left'); fc.bind('<<ComboboxSelected>>', lambda e: (self.render(), self.after(1, lambda g=self._gen: self.warm(g))))
        r3 = ttk.Frame(self); r3.pack(fill='x', pady=1)
        ttk.Label(r3, text='ball').pack(side='left')
        self.bstate = tk.StringVar(value='on the ground')
        bc = ttk.Combobox(r3, values=['on the ground', 'in the air: low', 'in the air: mid', 'in the air: high'], textvariable=self.bstate, state='readonly', width=16); bc.pack(side='left', padx=3)
        bc.bind('<<ComboboxSelected>>', lambda e: self.set_card(self.card))
        ttk.Label(r3, text='(passes: the game picks the air version from the ball height)', foreground='#8a90a0').pack(side='left')
        r4 = ttk.Frame(self); r4.pack(fill='x', pady=1)
        ttk.Label(r4, text='player is').pack(side='left')
        self.base = tk.StringVar(value='running')
        self.BASES = {'running': 'run', 'dribbling': 'dr17_drive_through', 'shooting': 'sh01_side_foot_place', 'jockeying': 'df10_jockey', 'sprinting': 'df07_recovery_sprint'}
        bb = ttk.Combobox(r4, values=list(self.BASES), textvariable=self.base, state='readonly', width=12); bb.pack(side='left', padx=3)
        bb.bind('<<ComboboxSelected>>', lambda e: self.set_card(self.card))
        ttk.Label(r4, text='(support cards ride on top of whatever the player is doing)', foreground='#8a90a0').pack(side='left')
        self.card = None; self.tc = 0; self._gen = 0; self._last = time.perf_counter(); self._acc = 0.0; self._tca = 0.0
        self.tick()

    def set_card(self, card):
        self.card = card; self.name = find(card['id']); self.cache = {}; self.f = 0
        st = self.bstate.get()
        if card['id'].startswith('PS') and st != 'on the ground': self.name = 'air_pass_' + st.split(': ')[1]
        if card['id'].startswith('SP') and aura.row(card['id']):
            self.name = self.BASES[self.base.get()]
            if self.name == 'run': self.a = {'label': 'Run', 'ms': U.ANIMS['run'][1] if isinstance(U.ANIMS['run'][1], (int, float)) else 70}; self.poses = list(U.ANIMS['run'][0]()[0])
            else: self.a = C.load(self.name); self.poses = C.build_poses(self.a)
            self.a = dict(self.a); self.a['label'] = card['name'] + ' on ' + self.base.get()
        elif self.name: self.a = C.load(self.name); self.poses = C.build_poses(self.a)
        else: self.a = None; self.poses = []
        self._gen += 1; self.render(); self.after(1, lambda g=self._gen: self.warm(g))

    def atlas(self):
        gk = bool(self.card and self.card['id'].startswith('GK'))
        if not hasattr(self, '_at'): self._at = {}
        if gk not in self._at:
            self._at[gk] = looks.player_skin(dict(role='GK' if gk else 'CM', skin='2', hair_color='brown', hair_style='H01_buzz'), 'keeper' if gk else 'home')
        return self._at[gk]

    def wq(self):
        """support overlay weight, quantised to 8 steps (0 = none) from the card's own timer"""
        ar = aura.row(self.card['id']) if self.card else None
        if not ar or not ar.get('overlay'): return 0
        dur = float(ar['duration_s']) * 1000 / 70; cyc = dur + 14
        return int(round(overlays.env((self.tc % cyc) / dur) * 8))

    def parts(self, f, d, ball, foot, wq=0):
        """the expensive part (ray-cast body, trail, shadow) for one frame/angle; cached as PIL layers"""
        key = (f, d, ball, foot, wq)
        if key not in self.cache:
            p = self.poses[f]; dn = U.DIRS[d]
            if wq:
                ar = aura.row(self.card['id']); p = overlays.apply(p, ar['overlay'], ar['side'], wq / 8.0, f)
            mp = M.mirror_pose if foot == 'L' else (lambda q: q)
            if foot == 'L': p = M.mirror_pose(p)
            under, over = U.extras(U.centered(p), dn)
            body = U.apply_skin(U.render_uv(U.centered(p), dn, with_ball=ball), self.atlas())
            gh = U.leg_trail([mp(self.poses[(f - k) % len(self.poses)]) for k in (1, 2, 3)], p, dn)
            if len(self.cache) > 1500: self.cache.clear()
            self.cache[key] = (under, gh, body, over)
        return self.cache[key]

    def render(self):
        self.cv.delete('all')
        if not self.poses:
            self.cv.create_text(int(U.CW * self.S) // 2, int(U.CH * self.S) // 2, fill='#8a90a0', text='No animation for this card yet'); return
        self.f %= len(self.poses); d = int(round(float(self.dirv.get()))) % 32
        ball = self.ball.get() and self.poses[self.f].get('bvis', 0) > 0.5
        under, gh, body, over = self.parts(self.f, d, ball, self.foot.get(), self.wq())
        ar = aura.row(self.card['id']) if self.card else None
        bg = U.bg_pitch(U.CW, U.CH); bg.alpha_composite(under)
        if ar:
            au, ao = aura.layers(ar, self.tc, U.CW, U.CH); bg.alpha_composite(au)
            if ar['scope'] in ('target', 'two', 'opponent'): bg.alpha_composite(aura.marker(ar, self.tc, U.CW, U.CH, 33, 31))
            if ar['scope'] == 'two': bg.alpha_composite(aura.marker(ar, self.tc, U.CW, U.CH, 7, 31))
        if gh is not None: bg.alpha_composite(gh)
        bg.alpha_composite(body); bg.alpha_composite(over)
        if ar: bg.alpha_composite(ao)
        self._img = ImageTk.PhotoImage(bg.resize((int(U.CW * self.S), int(U.CH * self.S)), Image.NEAREST))
        self.cv.create_image(0, 0, anchor='nw', image=self._img)
        self.cv.create_text(6, 6, anchor='nw', fill='white', text=f"{self.a['label']}  {self.f + 1}/{len(self.poses)}  angle {d}")
        if ar: self.cv.create_text(6, int(U.CH * self.S) - 6, anchor='sw', fill=ar['color'], text=f"aura: {ar['scope']}, {ar['shape']}, {ar['duration_s']}s")

    def warm(self, gen):
        """pre-render the uncached frames of the current angle a few at a time, so playback never stalls on first view"""
        if gen != self._gen or not self.poses or not self.winfo_exists(): return
        d = int(round(float(self.dirv.get()))) % 32; foot = self.foot.get(); done = 0
        for f in range(len(self.poses)):
            ball = self.ball.get() and self.poses[f].get('bvis', 0) > 0.5
            if (f, d, ball, foot) not in self.cache:
                self.parts(f, d, ball, foot); done += 1
                if done >= 2: break
        if done: self.after(1, lambda: self.warm(gen))

    def toggle(self):
        self.playing = not self.playing; self.playb.config(text='Pause' if self.playing else 'Play')

    def tick(self):
        """fixed 15 ms poll; the frame comes from the clock, so speed is constant even while frames are still being cached"""
        if not self.winfo_exists(): return
        now = time.perf_counter(); dt = (now - self._last) * 1000.0; self._last = now
        ms = (self.a.get('ms', 70) if self.a else 100) / max(self.spd.get(), 0.1)
        self._acc += dt; steps = int(self._acc // ms); self._acc -= steps * ms; self._tca += dt; ticks = int(self._tca // 70); self._tca -= ticks * 70; self.tc += ticks
        changed = bool(ticks and self.card and aura.row(self.card['id']))
        if self.playing and self.poses and steps:
            n = len(self.poses); old = self.f; self.f = (self.f + steps) % n; changed = True
            if self.rot.get() and old + steps >= n: self.dirv.set((int(float(self.dirv.get())) + 2) % 32); self.warm(self._gen)
        if changed and self.winfo_ismapped(): self.render()
        self.after(15, self.tick)
