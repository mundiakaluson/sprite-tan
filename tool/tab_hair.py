"""Hair style editor: a style is a few static blobs (ellipsoids) plus optional swaying strands (chains)."""
import copy, json, os, queue, re, subprocess, sys, threading, tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import tables, looks
import gen_uv as U
import gen_hair as H
import custom_anims as C

STATIC = [('cx', 'c', 0, -8, 8), ('cy', 'c', 1, -8, 8), ('cz', 'c', 2, -6, 10), ('size x', 'abc', 0, .5, 8), ('size y', 'abc', 1, .5, 8), ('size z', 'abc', 2, .5, 8), ('pitch', 'pitch', None, -2, 2), ('roll', 'roll', None, -2, 2)]
CHAIN = [('anchor x', 'anchor', 0, -8, 8), ('anchor y', 'anchor', 1, -8, 8), ('anchor z', 'anchor', 2, -6, 8), ('dir x', 'dir', 0, -1, 1), ('dir y', 'dir', 1, -1, 1), ('dir z', 'dir', 2, -1, 1),
         ('segments', 'n', None, 1, 8), ('segment length', 'seg', None, .5, 5), ('root thickness', 'r0', None, .3, 4), ('tip thickness', 'r1', None, .3, 4),
         ('stiffness', 'k', None, .02, .6), ('damping', 'damp', None, .5, .98), ('gravity', 'grav', None, 0, .4), ('wind effect', 'wind', None, 0, 2)]
BUILTIN = {'run': lambda: U.ANIMS['run'][0]()[0], 'kick': lambda: U.ANIMS['kick'][0]()[0], 'finesse': lambda: U.ANIMS['finesse'][0]()[0],
           'guard': lambda: U.ANIMS['guard'][0]()[0], 'slide': lambda: U.ANIMS['slide'][0]()[0]}


def blank_static():
    return dict(c=[0, 0, 3], abc=[3, 3, 3], pitch=0.0, roll=0.0)


def blank_chain():
    return dict(anchor=[0, -3, 1], dir=[0, -0.2, -1], n=3, seg=2.5, r0=1.3, r1=0.9, k=0.2, damp=0.8, grav=0.1, wind=1.0)


class HairTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.d = H.styles_to_json(H.STYLES); self.cur = None; self.part = None; self.dirty = False; self.rev = 0; self.cache = {}; self.fr = 0; self.playing = False
        self.q = queue.Queue(); self._busy = False; self.fields = {}; self.anim = tk.StringVar(value='run'); self.dirv = tk.IntVar(value=3); self.zoom = tk.BooleanVar(value=True)
        self.hcol = tk.StringVar(value='brown'); self.skin = tk.StringVar(value='2'); self.pal = looks.palette()
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw, padding=4); pw.add(left)
        top = ttk.Frame(left); top.pack(fill='x')
        self.sel = ttk.Combobox(top, state='readonly', width=22, values=list(self.d)); self.sel.pack(side='left'); self.sel.bind('<<ComboboxSelected>>', lambda e: self.open(self.sel.get()))
        for t, fn in (('New', self.new), ('Duplicate', self.dup), ('Delete', self.delete), ('Save', self.save)):
            ttk.Button(top, text=t, command=fn, width=9).pack(side='left', padx=2)
        pl = ttk.LabelFrame(left, text='Parts (blobs and strands)', padding=4); pl.pack(fill='x', pady=4)
        self.lb = tk.Listbox(pl, height=7, exportselection=False); self.lb.pack(side='left', fill='x', expand=True); self.lb.bind('<<ListboxSelect>>', lambda e: self.pick())
        bb = ttk.Frame(pl); bb.pack(side='left', padx=4)
        for t, fn in (('+ Blob', self.add_static), ('+ Strand', self.add_chain), ('Remove', self.remove_part)):
            ttk.Button(bb, text=t, command=fn, width=9).pack(pady=1)
        self.ff = ttk.LabelFrame(left, text='Selected part', padding=4); self.ff.pack(fill='both', expand=True)
        ttk.Label(left, justify='left', foreground='#9aa0ae', wraplength=480,
                  text='Blobs are solid hair shapes on the head (x right, y forward, z up). Strands are chains of segments that sway when the player moves. '
                       'The preview re-runs the sway with the chosen animation. Save writes data/hair_styles.json; Export builds the sprite layers for this style.').pack(anchor='w', pady=4)
        side = ttk.Frame(pw, padding=4, width=470); side.pack_propagate(False); pw.add(side)
        self.cv = tk.Canvas(side, width=440, height=440, bg='#46964a', highlightthickness=0); self.cv.pack()
        r1 = ttk.Frame(side); r1.pack(fill='x', pady=2)
        ttk.Combobox(r1, values=list(BUILTIN), textvariable=self.anim, state='readonly', width=8).pack(side='left')
        ttk.Label(r1, text='Facing').pack(side='left'); ttk.Scale(r1, from_=0, to=31, variable=self.dirv, command=lambda e: (self.dirv.set(round(float(e))), self.draw())).pack(side='left', fill='x', expand=True)
        ttk.Checkbutton(r1, text='Zoom head', variable=self.zoom, command=self.draw).pack(side='left')
        r2 = ttk.Frame(side); r2.pack(fill='x', pady=2)
        ttk.Label(r2, text='Preview hair').pack(side='left'); c = ttk.Combobox(r2, values=list(self.pal['hair']), textvariable=self.hcol, state='readonly', width=10); c.pack(side='left', padx=3); c.bind('<<ComboboxSelected>>', lambda e: self.draw())
        ttk.Label(r2, text='skin').pack(side='left'); c = ttk.Combobox(r2, values=list(self.pal['skin']), textvariable=self.skin, state='readonly', width=3); c.pack(side='left', padx=3); c.bind('<<ComboboxSelected>>', lambda e: self.draw())
        self.playb = ttk.Button(r2, text='▶ Play sway', command=self.play); self.playb.pack(side='left', padx=6)
        r3 = ttk.Frame(side); r3.pack(fill='x', pady=4)
        ttk.Button(r3, text='Export this style to game sprites', command=self.export).pack(side='left'); self.msg = ttk.Label(r3, text=''); self.msg.pack(side='left', padx=6)
        self.after(300, self.poll)
        if self.d: self.sel.set(list(self.d)[1] if len(self.d) > 1 else list(self.d)[0]); self.open(self.sel.get())

    # ------------------------------------------------------------------ styles
    def open(self, name):
        self.cur = name; self.sel.set(name); self.part = None; self.refresh_parts(); self.changed(False)

    def refresh_parts(self):
        sp = self.d[self.cur]; self.lb.delete(0, 'end')
        for i, e in enumerate(sp['static']): self.lb.insert('end', f'Blob {i + 1}  at ({e["c"][0]:.1f}, {e["c"][1]:.1f}, {e["c"][2]:.1f})')
        for i, c in enumerate(sp['chains']): self.lb.insert('end', f'Strand {i + 1}  {c["n"]} segments')
        if not sp['static'] and not sp['chains']: self.lb.insert('end', '(bald / buzz: no parts, just the painted head)')
        if self.part is not None and self.part < self.lb.size(): self.lb.selection_set(self.part)
        self.build_fields()

    def new(self):
        name = simpledialog.askstring('New hair style', 'Name (e.g. mohawk):', parent=self)
        if not name: return
        slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        n = max([int(k[1:3]) for k in self.d if k[1:3].isdigit()] + [0]) + 1
        key = f'H{n:02d}_{slug}'; self.d[key] = copy.deepcopy(self.d.get('H02_crop', dict(static=[], chains=[])))
        self.sel['values'] = list(self.d); self.open(key); self.changed()

    def dup(self):
        if not self.cur: return
        n = max([int(k[1:3]) for k in self.d if k[1:3].isdigit()] + [0]) + 1
        key = f'H{n:02d}_{self.cur[4:]}_copy'; self.d[key] = copy.deepcopy(self.d[self.cur]); self.sel['values'] = list(self.d); self.open(key); self.changed()

    def delete(self):
        used = [r['id'] for r in tables.table('players').rows if r.get('hair_style') == self.cur]
        if used: messagebox.showinfo('Hair', f'{len(used)} players use {self.cur}. Change them first.'); return
        if not messagebox.askyesno('Delete', f'Delete {self.cur}?'): return
        del self.d[self.cur]; self.sel['values'] = list(self.d); self.open(list(self.d)[0]); self.changed()

    def save(self):
        H.save_styles(self.d); H.reload_styles(); self.dirty = False; self.msg.config(text='saved to data/hair_styles.json')

    def changed(self, mark=True):
        self.rev += 1; self.cache = {}
        if mark: self.dirty = True; self.msg.config(text='unsaved')
        self.draw()

    # ------------------------------------------------------------------ parts
    def add_static(self): self.d[self.cur]['static'].append(blank_static()); self.part = len(self.d[self.cur]['static']) - 1; self.refresh_parts(); self.changed()
    def add_chain(self): self.d[self.cur]['chains'].append(blank_chain()); self.part = len(self.d[self.cur]['static']) + len(self.d[self.cur]['chains']) - 1; self.refresh_parts(); self.changed()

    def remove_part(self):
        if self.part is None: return
        sp = self.d[self.cur]; ns = len(sp['static'])
        if self.part < ns: del sp['static'][self.part]
        else: del sp['chains'][self.part - ns]
        self.part = None; self.refresh_parts(); self.changed()

    def pick(self):
        s = self.lb.curselection(); self.part = s[0] if s else None; self.build_fields()

    def build_fields(self):
        for w in self.ff.winfo_children(): w.destroy()
        self.fields = {}
        if self.part is None or not self.cur: return
        sp = self.d[self.cur]; ns = len(sp['static'])
        if self.part >= ns + len(sp['chains']): return
        obj, spec = (sp['static'][self.part], STATIC) if self.part < ns else (sp['chains'][self.part - ns], CHAIN)
        for n, (lab, key, idx, lo, hi) in enumerate(spec):
            cur = obj[key] if idx is None else obj[key][idx]
            v = tk.DoubleVar(value=float(cur)); step = 1 if key == 'n' else 0.05 if hi <= 1 else 0.1
            ttk.Label(self.ff, text=lab, width=16).grid(row=n, column=0, sticky='w')
            s = ttk.Scale(self.ff, from_=lo, to=hi, variable=v, length=200, command=lambda e, o=obj, k=key, i=idx, v=v: self.setp(o, k, i, v)); s.grid(row=n, column=1)
            e = ttk.Spinbox(self.ff, from_=lo, to=hi, increment=step, textvariable=v, width=7, command=lambda o=obj, k=key, i=idx, v=v: self.setp(o, k, i, v)); e.grid(row=n, column=2, padx=3)
            e.bind('<Return>', lambda ev, o=obj, k=key, i=idx, v=v: self.setp(o, k, i, v))

    def setp(self, o, k, i, v):
        try: x = float(v.get())
        except (tk.TclError, ValueError): return
        if k == 'n': x = int(round(x))
        if i is None: o[k] = x
        else: o[k][i] = x
        self.changed()

    # ------------------------------------------------------------------ preview
    def poses(self):
        a = self.anim.get()
        if ('p', a) not in self.cache: self.cache[('p', a)] = [U.centered(p) for p in BUILTIN[a]()]
        return self.cache[('p', a)]

    def frame_img(self, f):
        a = self.anim.get(); dn = U.DIRS[self.dirv.get()]; key = ('f', a, dn, f)
        if key in self.cache: return self.cache[key]
        name = '_edit'; H.STYLES[name] = H.styles_from_json({name: self.d[self.cur]})[name]
        cps = self.poses(); n = len(cps)
        if ('c', a) not in self.cache: self.cache[('c', a)] = H.simulate(name, cps, a in ('run', 'guard'), a)
        chains = self.cache[('c', a)]
        sc, info = U.build_scene(cps[f % n], dn)
        body = U.finish_uv(sc); hair = H.hair_layer(sc, info, name, chains[f % n])
        atlas = looks.player_skin(dict(role='CM', skin=self.skin.get(), hair_color=self.hcol.get(), hair_style=self.cur))
        im = Image.new('RGBA', (U.CW, U.CH), (70, 150, 74, 255))
        ImageDraw.Draw(im).ellipse([U.CW // 2 - 8, int(U.CH * .75) - 3, U.CW // 2 + 8, int(U.CH * .75) + 3], fill=(50, 120, 56, 255))
        im.alpha_composite(U.apply_skin(body, atlas)); im.alpha_composite(U.apply_skin(hair, atlas))
        self.cache[key] = im
        return im

    def draw(self):
        if not self.cur or not self.winfo_exists(): return
        try:
            f = self.fr % len(self.poses()); im = self.frame_img(f)
            if self.zoom.get(): im = im.crop((8, 4, 32, 28))
            self._ph = ImageTk.PhotoImage(im.resize((440, 440), Image.NEAREST)); self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self._ph)
        except Exception as e:
            self.cv.delete('all'); self.cv.create_text(220, 220, fill='white', text=f'preview error: {e}')
        H.STYLES.pop('_edit', None)

    def play(self):
        self.playing = not self.playing; self.playb.config(text='■ Stop' if self.playing else '▶ Play sway')
        if self.playing: self.tick()

    def tick(self):
        if not self.playing: return
        self.fr = (self.fr + 1) % len(self.poses()); self.draw(); self.after(70, self.tick)

    # ------------------------------------------------------------------ export
    def export(self):
        if self._busy or not self.cur: return
        self.save()
        self._busy = True; self.msg.config(text='exporting (about a minute)...')
        cmd = [sys.executable, os.path.join(looks.SPR, 'export_hair.py'), '--styles', self.cur]

        def run():
            pr = subprocess.run(cmd, cwd=looks.SPR, capture_output=True, text=True); self.q.put(pr.returncode)
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        try:
            r = self.q.get_nowait(); self._busy = False
            self.msg.config(text='exported: pick it on a player to see it in the game preview' if r == 0 else 'export failed (see console)')
        except queue.Empty:
            pass
        self.after(300, self.poll)

    def refresh(self):
        self.d.keys()
