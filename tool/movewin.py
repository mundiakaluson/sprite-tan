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


class MoveWin(tk.Toplevel):
    def __init__(self, master, card):
        super().__init__(master); self.title(f"Move: {card['id']} {card['name']}")
        self.name = find(card['id'])
        if not self.name:
            ttk.Label(self, text='No animation for this card yet.', padding=20).pack(); return
        self.a = C.load(self.name); self.poses = C.build_poses(self.a); self.f = 0; self.playing = True; self.cache = {}
        self.cv = tk.Canvas(self, width=440, height=440, bg='#222', highlightthickness=0); self.cv.pack()
        r = ttk.Frame(self, padding=4); r.pack(fill='x')
        self.playb = ttk.Button(r, text='Pause', command=self.toggle); self.playb.pack(side='left')
        self.dirv = tk.IntVar(value=8); self.rot = tk.BooleanVar(value=False); self.ball = tk.BooleanVar(value=True); self.spd = tk.DoubleVar(value=1.0)
        ttk.Checkbutton(r, text='auto-rotate', variable=self.rot).pack(side='left', padx=6)
        ttk.Checkbutton(r, text='ball', variable=self.ball).pack(side='left')
        ttk.Label(r, text='speed').pack(side='left', padx=(8, 2)); ttk.Scale(r, from_=0.25, to=2, variable=self.spd, length=80).pack(side='left')
        r2 = ttk.Frame(self, padding=4); r2.pack(fill='x')
        ttk.Label(r2, text='direction').pack(side='left')
        ttk.Scale(r2, from_=0, to=31, variable=self.dirv, command=lambda e: self.render(), length=300).pack(side='left', padx=4)
        ttk.Label(r2, text='(0 front, 8 side, 16 back)').pack(side='left')
        self.tick()

    def atlas(self):
        if not hasattr(self, '_at'):
            self._at = looks.player_skin(dict(role='CM', skin='2', hair_color='brown', hair_style='H01_buzz'), 'home')
        return self._at

    def render(self):
        d = int(round(float(self.dirv.get()))) % 32; p = self.poses[self.f]; dn = U.DIRS[d]
        ball = self.ball.get() and p.get('bvis', 0) > 0.5
        key = (self.f, d, ball)
        if key not in self.cache:
            bg = U.bg_pitch(U.CW, U.CH); under, over = U.extras(U.centered(p), dn)
            bg.alpha_composite(under); bg.alpha_composite(U.apply_skin(U.render_uv(U.centered(p), dn, with_ball=ball), self.atlas())); bg.alpha_composite(over)
            self.cache[key] = ImageTk.PhotoImage(bg.resize((440, 440), Image.NEAREST))
        self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self.cache[key])
        self.cv.create_text(8, 8, anchor='nw', fill='white', text=f"{self.a['label']}  frame {self.f + 1}/{len(self.poses)}  dir {d}")

    def toggle(self):
        self.playing = not self.playing; self.playb.config(text='Pause' if self.playing else 'Play')

    def tick(self):
        if not self.winfo_exists(): return
        if self.playing:
            self.f = (self.f + 1) % len(self.poses)
            if self.rot.get() and self.f == 0: self.dirv.set((int(float(self.dirv.get())) + 2) % 32)
        self.render(); self.after(int(self.a.get('ms', 70) / max(self.spd.get(), 0.1)), self.tick)
