"""Animation editor: pose sliders + keyframes on a timeline + live preview, exported through the real rig.
No drawing: you pose the 3D figure (hips, chest, head, feet, knees, arms, ball) and the tool interpolates between keys."""
import copy, json, math, os, queue, re, subprocess, sys, threading, tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import tables, looks
import custom_anims as C
import gen_uv as U
import gen_actions as A

DEG = 180 / math.pi
# (key, label, lo, hi, is_angle)
BODY = [('root_x', 'Sideways', -8, 8, 0), ('root_y', 'Forward', -14, 14, 0), ('pz', 'Hip height', 8, 30, 0),
        ('pyaw', 'Hips turn', -70, 70, 1), ('ppitch', 'Hips lean fwd', -60, 60, 1), ('proll', 'Hips tilt', -45, 45, 1),
        ('cyaw', 'Chest turn', -70, 70, 1), ('cpitch', 'Chest lean fwd', -60, 60, 1), ('croll', 'Chest tilt', -45, 45, 1),
        ('hyaw', 'Head turn', -70, 70, 1), ('hpitch', 'Head nod', -45, 45, 1), ('hroll', 'Head tilt', -35, 35, 1)]


def leg(s):
    return [(f'{s}_ax', 'Foot sideways', -12, 12, 0), (f'{s}_ay', 'Foot forward', -18, 18, 0), (f'{s}_az', 'Foot height (off when auto-ground)', 0, 14, 0),
            (f'{s}_lift', 'Lift off ground (auto-ground)', 0, 10, 0), (f'{s}_fp', 'Foot pitch (toe up)', -80, 80, 1), (f'{s}_fy', 'Foot turn', -90, 90, 1),
            (f'{s}_fr', 'Foot roll', -60, 60, 1), (f'{s}_kx', 'Knee out', -3, 3, 0), (f'{s}_ky', 'Knee forward', -3, 3, 0), (f'{s}_kz', 'Knee up', -3, 3, 0)]


def armp(s):
    return [(f'{s}_s1', 'Shoulder swing', -180, 180, 1), (f'{s}_a1', 'Shoulder out', -180, 180, 1),
            (f'{s}_s2', 'Elbow swing', -180, 180, 1), (f'{s}_a2', 'Elbow out', -180, 180, 1)]


BALL = [('bvis', 'Ball visible (0/1)', 0, 1, 0), ('bx', 'Ball sideways', -14, 14, 0), ('by', 'Ball forward', -14, 30, 0), ('bz', 'Ball height', 0, 16, 0),
        ('brx', 'Ball spin x', -20, 20, 0), ('brz', 'Ball spin z', -20, 20, 0)]
GROUPS = [('Body', BODY), ('Right leg', leg('R')), ('Left leg', leg('L')), ('Right arm', armp('R')), ('Left arm', armp('L')), ('Ball', BALL)]
ALLP = {k: (lo, hi, ang) for _, g in GROUPS for k, _, lo, hi, ang in g}
DEFAULT = dict(A.DEFAULT, R_lift=0.0, L_lift=0.0)
MIRROR_NEG = {'root_x', 'pyaw', 'proll', 'cyaw', 'croll', 'hyaw', 'hroll', 'R_ax', 'L_ax', 'R_kx', 'L_kx', 'R_fy', 'L_fy', 'R_fr', 'L_fr', 'bx', 'brz'}
TEMPLATES = ['blank (standing)', 'run', 'kick', 'finesse', 'guard', 'slide']
PREFIX = ('R_', 'L_')


class AnimTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.a = None; self.hist = []; self.redo = []; self._poses = None; self.f = 0; self.dirty = False; self.playing = False; self.clip = None; self.q = queue.Queue(); self.rows = {}
        self.dirv = tk.IntVar(value=2); self.onion = tk.BooleanVar(value=False); self.showball = tk.BooleanVar(value=True)
        self.kit = tk.StringVar(value='home'); self.hair = tk.BooleanVar(value=True); self._busy = False; self._after = None
        self.skin = looks.player_skin(dict(role='CM', skin='2', hair_color='brown', hair_style='H01_buzz'))
        self._build(); self.refresh_list(); self.after(200, self.poll)

    # ------------------------------------------------------------------ layout
    def _build(self):
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw, padding=4); pw.add(left, weight=2)
        top = ttk.Frame(left); top.pack(fill='x')
        self.sel = ttk.Combobox(top, state='readonly', width=18); self.sel.pack(side='left'); self.sel.bind('<<ComboboxSelected>>', lambda e: self.open(self.sel.get()))
        ttk.Button(top, text='New...', command=self.new).pack(side='left', padx=2)
        ttk.Button(top, text='Save', command=self.save).pack(side='left')
        ttk.Button(top, text='Delete', command=self.delete).pack(side='left', padx=2)
        pr = ttk.Frame(left); pr.pack(fill='x', pady=3)
        self.v_frames = tk.IntVar(value=8); self.v_ms = tk.IntVar(value=70); self.v_loop = tk.BooleanVar(); self.v_ground = tk.BooleanVar(value=True)
        self.v_events = tk.StringVar(); self.v_interp = tk.StringVar(value='smooth'); self.v_wx = tk.DoubleVar(value=0); self.v_wy = tk.DoubleVar(value=-0.1); self.v_wz = tk.DoubleVar(value=0)
        ttk.Label(pr, text='Frames').grid(row=0, column=0); sb = ttk.Spinbox(pr, from_=2, to=60, width=4, textvariable=self.v_frames, command=self.props); sb.grid(row=0, column=1)
        ttk.Label(pr, text='ms/frame').grid(row=0, column=2); ttk.Spinbox(pr, from_=20, to=300, increment=5, width=4, textvariable=self.v_ms, command=self.props).grid(row=0, column=3)
        ttk.Checkbutton(pr, text='Loop', variable=self.v_loop, command=self.props).grid(row=0, column=4, padx=4)
        ttk.Checkbutton(pr, text='Auto-ground feet', variable=self.v_ground, command=self.props).grid(row=0, column=5)
        ttk.Label(pr, text='Events (name=frame, ...)').grid(row=1, column=0, columnspan=3, sticky='w'); e = ttk.Entry(pr, textvariable=self.v_events); e.grid(row=1, column=3, columnspan=3, sticky='ew')
        e.bind('<FocusOut>', lambda ev: self.props()); e.bind('<Return>', lambda ev: self.props())
        for w in (sb,): w.bind('<Return>', lambda ev: self.props())
        pr2 = ttk.Frame(left); pr2.pack(fill='x')
        ttk.Label(pr2, text='Between keys').pack(side='left'); ic = ttk.Combobox(pr2, values=['smooth', 'linear', 'step'], textvariable=self.v_interp, state='readonly', width=7); ic.pack(side='left', padx=3)
        ic.bind('<<ComboboxSelected>>', lambda ev: self.props())
        ttk.Label(pr2, text='  Hair wind x y z').pack(side='left')
        for v in (self.v_wx, self.v_wy, self.v_wz):
            w = ttk.Spinbox(pr2, from_=-1, to=1, increment=0.05, width=5, textvariable=v, command=self.props); w.pack(side='left', padx=1); w.bind('<Return>', lambda ev: self.props())
        ttk.Button(pr2, text='Undo', width=5, command=self.undo).pack(side='left', padx=(10, 1)); ttk.Button(pr2, text='Redo', width=5, command=self.redo_).pack(side='left')
        self.bind_all('<Control-z>', lambda ev: self.undo()); self.bind_all('<Control-y>', lambda ev: self.redo_())
        nb = ttk.Notebook(left); nb.pack(fill='both', expand=True)
        for gname, params in GROUPS:
            fr = ttk.Frame(nb); nb.add(fr, text=gname)
            cv = tk.Canvas(fr, highlightthickness=0, width=420); sc = ttk.Scrollbar(fr, command=cv.yview); inner = ttk.Frame(cv)
            inner.bind('<Configure>', lambda ev, cv=cv: cv.configure(scrollregion=cv.bbox('all'))); cv.create_window(0, 0, window=inner, anchor='nw')
            cv.configure(yscrollcommand=sc.set); sc.pack(side='right', fill='y'); cv.pack(fill='both', expand=True)
            for n, (k, lab, lo, hi, ang) in enumerate(params):
                ttk.Label(inner, text=lab, width=28).grid(row=n, column=0, sticky='w')
                var = tk.DoubleVar(); s = ttk.Scale(inner, from_=lo, to=hi, variable=var, length=170, command=lambda v, k=k: self.slide(k)); s.grid(row=n, column=1, padx=2)
                val = tk.StringVar(value='0'); en = ttk.Entry(inner, textvariable=val, width=7); en.grid(row=n, column=2)
                en.bind('<Return>', lambda ev, k=k: self.type_value(k)); s.bind('<ButtonPress-1>', lambda ev: self.snap())
                key = ttk.Button(inner, text='◇', width=2, command=lambda k=k: self.toggle_key(k)); key.grid(row=n, column=3)
                self.rows[k] = (var, s, val, key)
        mid = ttk.Frame(pw, padding=4, width=470); mid.pack_propagate(False); pw.add(mid, weight=3)
        self.cv = tk.Canvas(mid, width=440, height=440, bg='#46964a', highlightthickness=0); self.cv.pack()
        c1 = ttk.Frame(mid); c1.pack(fill='x')
        ttk.Label(c1, text='Facing').pack(side='left'); ttk.Scale(c1, from_=0, to=31, variable=self.dirv, command=lambda e: (self.dirv.set(round(float(e))), self.render())).pack(side='left', fill='x', expand=True)
        ttk.Combobox(c1, values=looks.KITS, textvariable=self.kit, state='readonly', width=7).pack(side='left'); self.kit.trace_add('write', lambda *_: self.render())
        ttk.Checkbutton(c1, text='Onion', variable=self.onion, command=self.render).pack(side='left'); ttk.Checkbutton(c1, text='Ball', variable=self.showball, command=self.render).pack(side='left')
        self.tl = tk.Canvas(mid, height=54, bg='#23252b', highlightthickness=0); self.tl.pack(fill='x', pady=3); self.tl.bind('<Button-1>', self.tl_click); self.tl.bind('<B1-Motion>', self.tl_click)
        for row in ((('▶ Play', self.play), ('◀', lambda: self.go(self.f - 1)), ('▶', lambda: self.go(self.f + 1)), ('Key all', self.key_all), ('Clear keys here', self.clear_here)),
                    (('Copy', self.copy), ('Paste', self.paste), ('Insert frame', self.insert), ('Delete frame', self.remove_frame)),
                    (('Mirror L/R', self.mirror), ('Reverse', self.reverse), ('Stretch to N frames', self.stretch)),
                    (('Ball to R foot', lambda: self.ball_to('R')), ('Ball to L foot', lambda: self.ball_to('L')), ('Look at ball', self.look_ball))):
            c2 = ttk.Frame(mid); c2.pack(fill='x', pady=1)
            for t, fn in row:
                b = ttk.Button(c2, text=t, command=fn, width=len(t) + 2 if len(t) > 3 else 4); b.pack(side='left', padx=1)
                if t == '▶ Play': self.playb = b
        c4 = ttk.Frame(mid); c4.pack(fill='x', pady=1)
        ttk.Label(c4, text='Pose library').pack(side='left'); self.lib = ttk.Combobox(c4, values=self.lib_names(), state='readonly', width=16); self.lib.pack(side='left', padx=3)
        ttk.Button(c4, text='Apply here', width=9, command=self.lib_apply).pack(side='left'); ttk.Button(c4, text='Save this pose...', width=14, command=self.lib_save).pack(side='left', padx=2)
        c3 = ttk.Frame(mid); c3.pack(fill='x', pady=4)
        ttk.Button(c3, text='Export to game sprites', command=self.export).pack(side='left')
        ttk.Checkbutton(c3, text='+ hair layers', variable=self.hair).pack(side='left', padx=6)
        self.prog = ttk.Progressbar(c3, length=90, maximum=32); self.prog.pack(side='left'); self.msg = ttk.Label(c3, text=''); self.msg.pack(side='left', padx=6)
        self.help = ttk.Label(mid, justify='left', wraplength=440, foreground='#9aa0ae',
                              text='Move a slider to set a key for that part at this frame (◆ = keyed). Frames between keys are smoothed. Pick a template in New... to start from an existing move.')
        self.help.pack(anchor='w')

    # ------------------------------------------------------------------ file ops
    def refresh_list(self):
        names = C.files(); self.sel['values'] = names
        if self.a is None and names: self.sel.set(names[0]); self.open(names[0])
        elif self.a is None: self.draw_empty()

    def draw_empty(self):
        self.cv.delete('all'); self.cv.create_text(220, 220, fill='white', text='Press New... to create an animation')

    def confirm_discard(self):
        return not self.dirty or messagebox.askyesno('Animation', 'Discard unsaved changes to this animation?')

    def open(self, name):
        if self.a and self.a['name'] != name and not self.confirm_discard(): self.sel.set(self.a['name']); return
        self.a = C.load(name); self.dirty = False; self.f = 0; self.sel.set(name); self.sync_props(); self.update_all()

    def new(self):
        if not self.confirm_discard(): return
        name = simpledialog.askstring('New animation', 'Name (letters, numbers, _):', parent=self)
        if not name: return
        name = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
        if not name or name in C.files() or name in looks.anims():
            messagebox.showinfo('Animation', 'That name is empty or already used (including built-in moves). Pick another.'); return
        tpl = self.pick_template()
        if tpl is None: return
        if tpl.startswith('blank'):
            a = dict(name=name, label=name, frames=8, ms=70, loop=True, ground=True, events={}, keys={'0': {k: v for k, v in DEFAULT.items() if k in ALLP}}, wind=[0, -0.1, 0])
        else:
            fn = {'run': lambda: U.anim_run(), 'kick': A.anim_kick, 'finesse': A.anim_finesse, 'guard': A.anim_guard, 'slide': A.anim_slide}[tpl]
            poses = fn()[0]; meta = looks.anims().get(tpl, {})
            a = dict(name=name, label=name, frames=len(poses), ms=meta.get('ms_per_frame', 70), loop=bool(meta.get('loop', tpl in ('run', 'guard'))), ground=False,
                     events=dict(meta.get('events', {})), keys=C.bake(poses), wind=[0, -0.1, 0], template=tpl)
        self.a = a; self.dirty = True; self.f = 0; self.save(); self.refresh_names(); self.sync_props(); self.update_all()

    def pick_template(self):
        win = tk.Toplevel(self); win.title('Start from'); win.transient(self); win.grab_set(); res = []
        ttk.Label(win, text='Start from which pose set?').pack(padx=10, pady=6)
        cb = ttk.Combobox(win, values=TEMPLATES, state='readonly'); cb.set(TEMPLATES[0]); cb.pack(padx=10)
        ttk.Button(win, text='OK', command=lambda: (res.append(cb.get()), win.destroy())).pack(pady=8); self.wait_window(win)
        return res[0] if res else None

    def refresh_names(self):
        self.sel['values'] = C.files(); self.sel.set(self.a['name'])

    def save(self):
        if self.a:
            C.save(self.a); self.dirty = False; self.msg.config(text='saved')

    def delete(self):
        if not self.a or not messagebox.askyesno('Delete', f"Delete animation {self.a['name']}? (exported sprites stay)"): return
        os.remove(os.path.join(C.ANIM_DIR, self.a['name'] + '.json'))
        self.a = None; self.dirty = False; self.sel['values'] = C.files(); self.sel.set(''); self.refresh_list()
        if self.a is None: self.draw_empty()

    # ------------------------------------------------------------------ model
    def sync_props(self):
        a = self.a
        self.v_frames.set(a['frames']); self.v_ms.set(a.get('ms', 70)); self.v_loop.set(a.get('loop', False)); self.v_ground.set(a.get('ground', True))
        self.v_events.set(', '.join(f'{k}={v}' for k, v in a.get('events', {}).items())); self.v_interp.set(a.get('interp', 'smooth'))
        w = a.get('wind', [0, -0.1, 0]); self.v_wx.set(w[0]); self.v_wy.set(w[1]); self.v_wz.set(w[2])

    def props(self):
        if not self.a: return
        a = self.a
        self.snap()
        try:
            n = max(2, min(60, int(self.v_frames.get())))
        except (tk.TclError, ValueError):
            n = a['frames']
        a['frames'] = n; a['ms'] = int(self.v_ms.get()); a['loop'] = bool(self.v_loop.get()); a['ground'] = bool(self.v_ground.get())
        ev = {}
        for part in self.v_events.get().split(','):
            if '=' in part:
                k, v = part.split('=', 1)
                try: ev[k.strip()] = int(v)
                except ValueError: ev[k.strip()] = v.strip()
        a['events'] = ev; a['interp'] = self.v_interp.get(); a['wind'] = [self.v_wx.get(), self.v_wy.get(), self.v_wz.get()]
        a['keys'] = {f: v for f, v in a['keys'].items() if int(f) < n}; self.f = min(self.f, n - 1)
        self.mark(); self.update_all()

    def snap(self):
        if not self.a: return
        self.hist.append(copy.deepcopy(self.a)); self.hist = self.hist[-80:]; self.redo = []

    def undo(self):
        if self.hist and self.winfo_viewable():
            self.redo.append(copy.deepcopy(self.a)); self.a = self.hist.pop(); self.f = min(self.f, self.a['frames'] - 1); self.mark(); self.sync_props(); self.update_all()

    def redo_(self):
        if self.redo and self.winfo_viewable():
            self.hist.append(copy.deepcopy(self.a)); self.a = self.redo.pop(); self.f = min(self.f, self.a['frames'] - 1); self.mark(); self.sync_props(); self.update_all()

    def type_value(self, k):
        try: v = float(self.rows[k][2].get())
        except ValueError: self.update_labels(); return
        self.snap(); self.a['keys'].setdefault(str(self.f), {})[k] = v / DEG if ALLP[k][2] else v
        self.mark(); self.update_all()

    def mark(self):
        self.dirty = True; self.msg.config(text='unsaved')

    def poses(self):
        return C.build_poses(self.a)

    def plist(self):
        if self._poses is None: self._poses = self.poses()
        return self._poses

    def keyed(self, k, f=None):
        return k in self.a['keys'].get(str(self.f if f is None else f), {})

    def slide(self, k):
        if not self.a: return
        var, s, val, kb = self.rows[k]; v = var.get()
        if k == 'bvis': v = 1.0 if v >= 0.5 else 0.0
        self.a['keys'].setdefault(str(self.f), {})[k] = v / DEG if ALLP[k][2] else v
        self.mark(); self._poses = None; self.update_labels(only=k); self.render(); self.draw_tl()

    def toggle_key(self, k):
        self.snap()
        ks = self.a['keys'].setdefault(str(self.f), {})
        if k in ks:
            if sum(1 for fr in self.a['keys'].values() if k in fr) > 1: del ks[k]
        else:
            ks[k] = self.plist()[self.f].get(k, DEFAULT.get(k, 0.0))
        if not ks: self.a['keys'].pop(str(self.f), None)
        self.mark(); self.update_all()

    def key_all(self):
        self.snap()
        p = self.plist()[self.f]; ks = self.a['keys'].setdefault(str(self.f), {})
        for k in ALLP: ks[k] = p.get(k, DEFAULT.get(k, 0.0))
        self.mark(); self.update_all()

    def clear_here(self):
        self.snap()
        self.a['keys'].pop(str(self.f), None); self.mark(); self.update_all()

    def copy(self):
        self.clip = dict(self.plist()[self.f]); self.msg.config(text='copied frame')

    def paste(self):
        self.snap()
        if self.clip:
            self.a['keys'][str(self.f)] = {k: self.clip[k] for k in ALLP if k in self.clip}; self.mark(); self.update_all()

    def insert(self):
        self.snap()
        a = self.a
        if a['frames'] >= 60: return
        keys = {}
        for fk, v in a['keys'].items():
            f = int(fk); keys[str(f + 1 if f > self.f else f)] = v
        a['keys'] = keys; a['frames'] += 1; self.v_frames.set(a['frames']); self.mark(); self.go(self.f + 1); self.update_all()

    def remove_frame(self):
        self.snap()
        a = self.a
        if a['frames'] <= 2: return
        full = self.poses(); a['frames'] -= 1; self.v_frames.set(a['frames'])
        keys = {}
        for fk, v in a['keys'].items():
            f = int(fk)
            if f == self.f: continue
            keys[str(f - 1 if f > self.f else f)] = v
        a['keys'] = keys or {'0': {k: full[0].get(k, 0.0) for k in ALLP}}
        self.f = min(self.f, a['frames'] - 1); self.mark(); self.update_all()

    def mirror(self):
        self.snap()
        full = self.poses(); out = {}
        for f, p in enumerate(full):
            q = {}
            for k in ALLP:
                src = k
                if k[:2] in PREFIX: src = ('L_' if k[0] == 'R' else 'R_') + k[2:]
                v = p.get(src, DEFAULT.get(src, 0.0))
                q[k] = -v if (k in MIRROR_NEG) else v
            out[str(f)] = q
        self.a['keys'] = out; self.mark(); self.update_all()

    def reverse(self):
        self.snap()
        full = self.poses(); n = len(full)
        self.a['keys'] = {str(n - 1 - f): {k: p.get(k, 0.0) for k in ALLP} for f, p in enumerate(full)}; self.mark(); self.update_all()

    # ------------------------------------------------------------------ extra tools
    POSES = os.path.join(tables.DATA, 'poses.json')

    def lib_load(self):
        try: return json.load(open(self.POSES))
        except (OSError, ValueError): return {'stand': {k: v for k, v in DEFAULT.items() if k in ALLP}}

    def lib_names(self):
        return sorted(self.lib_load())

    def lib_save(self):
        if not self.a: return
        name = simpledialog.askstring('Pose library', 'Name this pose:', parent=self)
        if not name: return
        lib = self.lib_load(); p = self.plist()[self.f]; lib[name.strip()] = {k: p.get(k, DEFAULT.get(k, 0.0)) for k in ALLP}
        json.dump(lib, open(self.POSES, 'w'), indent=1); self.lib['values'] = sorted(lib); self.lib.set(name.strip())

    def lib_apply(self):
        if not self.a or not self.lib.get(): return
        self.snap(); self.a['keys'][str(self.f)] = dict(self.lib_load()[self.lib.get()]); self.mark(); self.update_all()

    def stretch(self):
        if not self.a: return
        n2 = simpledialog.askinteger('Stretch', 'New number of frames (2-60):', parent=self, minvalue=2, maxvalue=60, initialvalue=self.a['frames'])
        if not n2 or n2 == self.a['frames']: return
        self.snap(); old = self.poses(); n = len(old); loop = self.a.get('loop', False); keys = {}
        for f in range(n2):
            x = f * (n if loop else n - 1) / n2 if loop else f * (n - 1) / (n2 - 1)
            i = int(math.floor(x)); t = x - i; p0, p1 = old[i % n], old[(i + 1) % n if loop else min(i + 1, n - 1)]
            keys[str(f)] = {k: p0[k] + (p1[k] - p0[k]) * t for k in ALLP if k in p0}
        self.a['frames'] = n2; self.a['keys'] = keys; self.v_frames.set(n2); self.f = min(self.f, n2 - 1)
        for k, v in self.a.get('events', {}).items():
            if isinstance(v, int): self.a['events'][k] = round(v * (n2 - 1) / max(1, n - 1))
        self.sync_props(); self.mark(); self.update_all()

    def ball_to(self, s):
        if not self.a: return
        self.snap(); p = self.plist()[self.f]; ks = self.a['keys'].setdefault(str(self.f), {})
        ks.update(bvis=1.0, bx=p[f'{s}_ax'] + p.get('root_x', 0) * 0, by=p[f'{s}_ay'] + 3.2, bz=3.0); self.mark(); self.update_all()

    def look_ball(self):
        if not self.a: return
        self.snap(); p = self.plist()[self.f]; ks = self.a['keys'].setdefault(str(self.f), {})
        dx, dy = p['bx'] - p['root_x'], p['by'] - p['root_y']
        yaw = math.atan2(dx, max(0.5, dy)) - p['pyaw'] - p['cyaw']
        ks['hyaw'] = max(-1.0, min(1.0, yaw)); ks['hpitch'] = max(-0.2, min(0.6, 0.15 + 0.012 * math.hypot(dx, dy))); self.mark(); self.update_all()

    # ------------------------------------------------------------------ view
    def go(self, f):
        if not self.a: return
        self.f = f % self.a['frames']; self.update_all()

    def update_labels(self, only=None):
        if not self.a: return
        p = self.plist()[self.f]
        for k, (var, s, val, kb) in self.rows.items():
            if only and k != only: continue
            v = p.get(k, DEFAULT.get(k, 0.0)); disp = v * DEG if ALLP[k][2] else v
            var.set(max(ALLP[k][0], min(ALLP[k][1], disp))); val.set(f'{disp:.1f}')
            kb.config(text='◆' if self.keyed(k) else '◇')
            if k.endswith('_az'): s.state(['disabled'] if self.a.get('ground', True) else ['!disabled'])
            if k.endswith('_lift'): s.state(['!disabled'] if self.a.get('ground', True) else ['disabled'])

    def update_all(self):
        if not self.a: return
        self._poses = None; self.update_labels(); self.render(); self.draw_tl()

    def draw_tl(self):
        c = self.tl; c.delete('all'); n = self.a['frames']; W = c.winfo_width() or 440; w = (W - 20) / n
        for f in range(n):
            x = 10 + f * w; keyed = str(f) in self.a['keys']
            c.create_rectangle(x + 1, 8, x + w - 1, 34, fill='#e0b030' if keyed else '#3a3d48', outline='')
            if f == self.f: c.create_rectangle(x, 6, x + w, 36, outline='white', width=2)
            if n <= 30 or f % 2 == 0: c.create_text(x + w / 2, 44, text=str(f), fill='#9aa0ae', font=('TkDefaultFont', 7))
        for name, fr in self.a.get('events', {}).items():
            try: x = 10 + int(fr) * w; c.create_text(x + w / 2, 21, text='⚑', fill='#ff6a5a'); 
            except (ValueError, TypeError): pass

    def tl_click(self, ev):
        if not self.a: return
        n = self.a['frames']; w = ((self.tl.winfo_width() or 440) - 20) / n
        self.go(int(max(0, min(n - 1, (ev.x - 10) // w))))

    def frame_img(self, pose, dn, ball):
        return U.apply_skin(U.render_uv(U.centered(pose), dn, with_ball=ball), self._atlas())

    def _atlas(self):
        k = self.kit.get()
        if getattr(self, '_atlas_kit', None) != k:
            self._atlas_kit = k; self._atlas_arr = looks.player_skin(dict(role='CM', skin='2', hair_color='brown', hair_style='H01_buzz'), k)
        return self._atlas_arr

    def render(self):
        if not self.a: return
        full = self.plist()
        dn = U.DIRS[self.dirv.get()]; n = len(full)
        bg = Image.new('RGBA', (U.CW, U.CH), (70, 150, 74, 255))
        d = ImageDraw.Draw(bg)
        for y in range(0, U.CH, 6):
            if (y // 6) % 2: d.rectangle([0, y, U.CW, y + 5], fill=(78, 160, 82, 255))
        under, over = U.extras(U.centered(full[self.f]), dn)
        im = bg.copy(); im.alpha_composite(under)
        if self.onion.get():
            for off, tint in ((-1, (80, 120, 255)), (1, (255, 110, 90))):
                g = self.frame_img(full[(self.f + off) % n], dn, False).copy(); a = np.array(g)
                a[..., :3] = (a[..., :3] * 0.4 + np.array(tint) * 0.6).astype(np.uint8); a[..., 3] = (a[..., 3] * 0.45).astype(np.uint8)
                im.alpha_composite(Image.fromarray(a, 'RGBA'))
        body = self.frame_img(full[self.f], dn, self.showball.get() and full[self.f].get('bvis', 0) > 0.5)
        gh = U.leg_trail([full[(self.f - k) % n] for k in (1, 2, 3)], full[self.f], dn)
        if gh is not None: im.alpha_composite(gh)
        im.alpha_composite(body); im.alpha_composite(over)
        self._ph = ImageTk.PhotoImage(im.resize((440, 440), Image.NEAREST)); self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self._ph)
        self.cv.create_text(8, 8, anchor='nw', fill='white', text=f"{self.a['name']}  frame {self.f + 1}/{n}")

    # ------------------------------------------------------------------ playback
    def play(self):
        self.playing = not self.playing; self.playb.config(text='■ Stop' if self.playing else '▶ Play')
        if self.playing: self.step()

    def step(self):
        if not self.playing or not self.a: return
        self.go(self.f + 1); self._after = self.after(max(30, int(self.a.get('ms', 70))), self.step)

    # ------------------------------------------------------------------ export
    def export(self):
        if not self.a or self._busy: return
        self.save()
        if self.a['name'] in looks.anims() and not looks.anims()[self.a['name']].get('custom') and not messagebox.askyesno('Export', 'This overwrites a built-in animation sheet. Continue?'): return
        cmd = [sys.executable, os.path.join(looks.SPR, 'custom_anims.py'), self.a['name']] + (['--hair'] if self.hair.get() else [])
        self._busy = True; self.prog['value'] = 0; self.msg.config(text='exporting...')

        def run():
            try:
                pr = subprocess.Popen(cmd, cwd=looks.SPR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in pr.stdout: self.q.put(line.strip())
                pr.wait(); self.q.put('exit %d' % pr.returncode)
            except Exception as e:
                self.q.put(f'exit error {e}')
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        try:
            while True:
                s = self.q.get_nowait()
                if s.startswith('progress'): self.prog['value'] = int(s.split()[1].split('/')[0]); self.msg.config(text=s.split(' ', 2)[2] if len(s.split()) > 2 else '')
                elif s.startswith('exit'):
                    self._busy = False
                    ok = s.strip() == 'exit 0'; self.msg.config(text='exported - available in the Players preview' if ok else 'export failed: see console')
                    if not ok: print('export output:', s)
                else: print(s)
        except queue.Empty:
            pass
        self.after(200, self.poll)
