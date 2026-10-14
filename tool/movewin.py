"""Live move player for a skill card: plays the card's animation (data/animations/<id>_*.json), any of the 32 directions, auto-rotate."""
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image, ImageTk
import looks  # puts sprites/ on the path
import gen_uv as U
import custom_anims as C

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
        ttk.Scale(r2, from_=0, to=31, variable=self.dirv, command=lambda e: self.render(), length=n[0] - 90).pack(side='left', padx=4)
        self.tick()

    def set_card(self, card):
        self.name = find(card['id']); self.cache = {}; self.f = 0
        if self.name: self.a = C.load(self.name); self.poses = C.build_poses(self.a)
        else: self.a = None; self.poses = []
        self.render()

    def atlas(self):
        if not hasattr(self, '_at'):
            self._at = looks.player_skin(dict(role='CM', skin='2', hair_color='brown', hair_style='H01_buzz'), 'home')
        return self._at

    def render(self):
        self.cv.delete('all')
        if not self.poses:
            self.cv.create_text(int(U.CW * self.S) // 2, int(U.CH * self.S) // 2, fill='#8a90a0', text='No animation for this card yet'); return
        self.f %= len(self.poses); d = int(round(float(self.dirv.get()))) % 32; p = self.poses[self.f]; dn = U.DIRS[d]
        ball = self.ball.get() and p.get('bvis', 0) > 0.5; key = (self.f, d, ball)
        if key not in self.cache:
            bg = U.bg_pitch(U.CW, U.CH); under, over = U.extras(U.centered(p), dn)
            bg.alpha_composite(under); bg.alpha_composite(U.apply_skin(U.render_uv(U.centered(p), dn, with_ball=ball), self.atlas())); bg.alpha_composite(over)
            self.cache[key] = ImageTk.PhotoImage(bg.resize((int(U.CW * self.S), int(U.CH * self.S)), Image.NEAREST))
            if len(self.cache) > 700: self.cache.clear()
        self.cv.create_image(0, 0, anchor='nw', image=self.cache[key])
        self.cv.create_text(6, 6, anchor='nw', fill='white', text=f"{self.a['label']}  {self.f + 1}/{len(self.poses)}  angle {d}")

    def toggle(self):
        self.playing = not self.playing; self.playb.config(text='Pause' if self.playing else 'Play')

    def tick(self):
        if not self.winfo_exists(): return
        if self.playing and self.poses:
            self.f = (self.f + 1) % len(self.poses)
            if self.rot.get() and self.f == 0: self.dirv.set((int(float(self.dirv.get())) + 2) % 32)
        if self.winfo_ismapped(): self.render()
        self.after(int((self.a.get('ms', 70) if self.a else 100) / max(self.spd.get(), 0.1)), self.tick)
