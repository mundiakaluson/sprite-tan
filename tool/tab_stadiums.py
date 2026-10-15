import os, sys, threading, queue
import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image, ImageTk
import tables
ST_DIR = os.path.join(tables.ROOT, 'stadiums')
if ST_DIR not in sys.path: sys.path.insert(0, ST_DIR)
import stadiumlib as SL, goallib as GL, preview as PV

COLOURS = [('grass_a', 'Grass light'), ('grass_b', 'Grass dark'), ('stand', 'Stands'), ('stand_trim', 'Stand trim'), ('seat', 'Seats'), ('board', 'Ad boards')]
SLIDERS = [('crowd', 'Crowd %', 0, 100, 1), ('worn', 'Worn pitch %', 0, 100, 1), ('light', 'Floodlights', 0, 1.5, 0.05),
           ('cam_height', 'Camera height', 8, 60, 0.5), ('cam_back', 'Camera back', -10, 40, 0.5), ('look_z', 'Aim across', -20, 10, 0.5), ('fov', 'Field of view', 15, 70, 1)]
CHOICES = dict(time=['day', 'dusk', 'night'], mow=['stripes', 'checker', 'diagonal', 'rings'], roof=['0', '1'], towers=['0', '1'])


def new_stadium(t):
    n = 1
    while any(r['id'] == f'ST{n:02d}' for r in t.rows): n += 1
    r = {c: '' for c in t.cols}
    r.update(id=f'ST{n:02d}', name='New stadium', time='day', grass_a='#3f7d3c', grass_b='#4a8c44', mow='stripes', worn='20', stand='#6a4a3a', stand_trim='#c9b28a', seat='#b8c0c8', board='#d9c07a',
             crowd='60', crowd_colors='#c8372d;#f2f2f2;#2d4fa8;#e8c33a', roof='0', towers='0', light='1.0', goal='G01', capacity='20000', net_wear='', cam_height='26', cam_back='16', look_z='-4', fov='34')
    return r


class StadiumsTab(ttk.Frame):
    """Stadium editor: the table on the left, colour / crowd / camera controls under it, a live preview from the TV camera on the right."""
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('stadiums'); self.goals = tables.table('goals'); self.i = None; self.cache = {}; self.q = queue.Queue(); self.busy = False; self.pending = False; self.cam_x = 0.0; self._job = None
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw); pw.add(left)
        self.grid_ = tables.Grid(left, self.t, choices=dict(CHOICES, goal=[r['id'] for r in self.goals.rows]), new_row=new_stadium, on_select=self.select,
                                 hide=('note', 'crowd_colors', 'grass_a', 'grass_b', 'stand', 'stand_trim', 'seat', 'board', 'cam_height', 'cam_back', 'look_z', 'fov', 'worn', 'crowd', 'light', 'capacity'),
                                 width_for=dict(id=60, name=120)); self.grid_.pack(fill='both', expand=True)
        ctl = ttk.LabelFrame(left, text='Look (changes are live in the preview; Save writes data/stadiums.csv)', padding=6); ctl.pack(fill='x')
        self.btn = {}
        for n, (f, lab) in enumerate(COLOURS):
            ttk.Label(ctl, text=lab).grid(row=0, column=n, sticky='w', padx=4)
            b = tk.Button(ctl, width=7, relief='raised', command=lambda f=f: self.pick(f)); b.grid(row=1, column=n, padx=4, pady=(0, 6)); self.btn[f] = b
        self.sl = {}; self.lb = {}
        for n, (f, lab, lo, hi, st) in enumerate(SLIDERS):
            r, c = 2 + n // 2, (n % 2) * 2
            ttk.Label(ctl, text=lab).grid(row=r, column=c, sticky='w', padx=4)
            v = tk.DoubleVar(value=lo); s = ttk.Scale(ctl, from_=lo, to=hi, variable=v, length=120, command=lambda _v, f=f, st=st: self.slide(f, st)); s.grid(row=r, column=c + 1, sticky='w', padx=4, pady=2)
            self.sl[f] = (v, st)
        ttk.Label(ctl, text='Crowd colours').grid(row=7, column=0, sticky='w', padx=4)
        self.cc = tk.StringVar(); e = ttk.Entry(ctl, textvariable=self.cc, width=34); e.grid(row=7, column=1, columnspan=3, sticky='w', pady=2)
        e.bind('<Return>', lambda _e: self.set('crowd_colors', self.cc.get())); e.bind('<FocusOut>', lambda _e: self.set('crowd_colors', self.cc.get()))
        side = ttk.Frame(pw, padding=4, width=660); side.pack_propagate(False); pw.add(side)
        self.cv = tk.Canvas(side, width=640, height=360, bg='#10131a', highlightthickness=0); self.cv.pack()
        row = ttk.Frame(side); row.pack(fill='x', pady=4); ttk.Label(row, text='Camera along the pitch (preview)').pack(side='left')
        self.cx = tk.DoubleVar(value=0); ttk.Scale(row, from_=-38, to=38, variable=self.cx, length=260, command=lambda _v: self.cam_move()).pack(side='left', padx=6)
        self.msg = ttk.Label(side, text='', foreground='#9aa0ae'); self.msg.pack(anchor='w')
        ttk.Label(side, justify='left', foreground='#9aa0ae', wraplength=620,
                  text='The preview is a software render of the same camera and parts the game uses (floodlights and goal styles included). Pick the goal style in the grid (goal column; styles live in the Goal simulator tab). '
                       'The three camera sliders and field of view are saved per stadium. Press Export to game to write the art.').pack(anchor='w', pady=6)
        self.t.listeners.append(self.changed); self.after(120, self.poll)

    # ---- selection / editing
    def select(self, idx):
        self.i = idx[0] if idx else None; self.sync(); self.schedule()

    def row(self): return self.t.rows[self.i] if self.i is not None and self.i < len(self.t.rows) else None

    def sync(self):
        r = self.row()
        if not r: return
        for f, b in self.btn.items():
            c = r.get(f) or ''
            try: b.config(bg=c or '#d9d9d9', activebackground=c or '#d9d9d9', text='')
            except tk.TclError: b.config(bg='#d9d9d9', text='?')
        for f, (v, st) in self.sl.items(): v.set(SL.num(r.get(f)))
        self.cc.set(r.get('crowd_colors', ''))

    def set(self, f, val):
        if self.i is not None: self.t.set(self.i, f, val)

    def pick(self, f):
        r = self.row()
        if not r: return
        c = colorchooser.askcolor(color=r.get(f) or '#ffffff', title=dict(COLOURS)[f])[1]
        if c: self.set(f, c)

    def slide(self, f, st):
        v = self.sl[f][0].get(); v = round(v / st) * st
        if self.i is not None: self.t.set(self.i, f, f'{v:g}', snap=False)

    def cam_move(self): self.cam_x = self.cx.get(); self.schedule(80)

    def changed(self):
        self.sync(); self.schedule()

    # ---- preview (rendered off the Tk thread; Tk objects only touched here)
    def schedule(self, ms=300):
        if self._job: self.after_cancel(self._job)
        self._job = self.after(ms, self.render)

    def render(self):
        self._job = None
        r = self.row()
        if not r or not self.winfo_viewable(): return
        if self.busy: self.pending = True; return
        self.busy = True; self.msg.config(text='rendering...'); rr = dict(r); x = self.cam_x

        def work():
            try: img = PV.render(rr, cam=PV.Cam.from_row(rr, x=x, size=(960, 540)), cache=self.cache); self.q.put(('ok', img.resize((640, 360), Image.LANCZOS)))
            except Exception as e: self.q.put(('err', repr(e)))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            while True:
                k, v = self.q.get_nowait(); self.busy = False
                if k == 'ok': self._ph = ImageTk.PhotoImage(v); self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self._ph); self.msg.config(text='')
                else: self.msg.config(text='preview error: ' + v)
                if self.pending: self.pending = False; self.schedule(50)
        except queue.Empty: pass
        self.after(120, self.poll)

    def refresh(self):
        self.cache.clear(); self.schedule(50)
