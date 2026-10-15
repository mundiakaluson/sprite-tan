"""Titan scene player for the Cards tab: renders the card's cinematic (titan/scenes.py) in a background thread, then plays it at 25 fps from the clock."""
import os, sys, threading, time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import tables

TITAN_DIR = os.path.join(tables.ROOT, 'titan')


class TitanPanel(ttk.Frame):
    W, H = 456, 257

    def __init__(self, master):
        super().__init__(master); self.cid = None; self.frames = []; self.photos = {}; self.playing = True; self._t0 = time.perf_counter(); self._gen = 0; self._done = False
        self.cv = tk.Canvas(self, width=self.W, height=self.H, bg='#111', highlightthickness=0); self.cv.pack()
        r = ttk.Frame(self); r.pack(fill='x', pady=2)
        self.btn = ttk.Button(r, text='Pause', width=7, command=self.toggle); self.btn.pack(side='left')
        ttk.Button(r, text='Replay', width=7, command=self.replay).pack(side='left', padx=3)
        self.info = ttk.Label(r, text='', foreground='#8a90a0'); self.info.pack(side='left', padx=6)
        self.tick()

    def load(self, cid):
        self.cid = cid; self._gen += 1; self.frames = []; self.photos = {}; self._done = False; gen = self._gen
        self._msg = 'rendering scene...'
        threading.Thread(target=self._render, args=(cid, gen), daemon=True).start()

    def _render(self, cid, gen):
        try:
            if TITAN_DIR not in sys.path: sys.path.insert(0, TITAN_DIR)
            import scenes  # noqa: F401  (registers the scenes)
            import engine
            sc = engine.SCENES.get(cid)
            if sc is None: self._msg = 'no Titan scene for this card yet'; return
            for i in range(sc.N):
                if gen != self._gen: return
                self.frames.append(engine.render_frame(sc, i).resize((self.W, self.H), Image.NEAREST))
            self._done = True; self._t0 = time.perf_counter()
            self._msg = f'{sc.N} frames, {sc.N * 0.04:.1f}s'
        except Exception as e:
            self._msg = f'scene error: {e}'

    def replay(self): self._t0 = time.perf_counter(); self.playing = True; self.btn.config(text='Pause')
    def toggle(self):
        self.playing = not self.playing; self.btn.config(text='Pause' if self.playing else 'Play')
        if self.playing: self._t0 = time.perf_counter() - getattr(self, '_pos', 0) * 0.04

    def tick(self):
        if not self.winfo_exists(): return
        if getattr(self, '_msg', None) is not None and self.info.cget('text') != self._msg: self.info.config(text=self._msg)
        if self._done and self.frames and self.winfo_ismapped():
            if self.playing: self._pos = int((time.perf_counter() - self._t0) / 0.04) % len(self.frames)
            n = getattr(self, '_pos', 0) % len(self.frames)
            if n not in self.photos: self.photos[n] = ImageTk.PhotoImage(self.frames[n])
            self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self.photos[n])
        elif not self._done and self.cid:
            self.cv.delete('all'); self.cv.create_text(self.W // 2, self.H // 2, fill='#8a90a0', text=f'rendering... {len(self.frames)} frames')
        self.after(20, self.tick)
