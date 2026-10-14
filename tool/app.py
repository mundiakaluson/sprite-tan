"""Sprite manager (tkinter). Run:  python tool/app.py   (from the repo root)  or  python app.py  (from tool/).
Open any PNG sprite sheet, set or detect the grid, see the colour ramps, pick new colours, preview, export."""
import os, sys, tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
import numpy as np
from PIL import Image, ImageTk
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprite_core as S

BG = '#1e1f24'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Sprite manager'); self.geometry('1180x760'); self.configure(bg=BG)
        self.img = None; self.path = None; self.cols = None; self.cnt = None; self.ramps = []; self.idx = None
        self.out = None; self.zoom = tk.IntVar(value=4); self.cw = tk.IntVar(value=40); self.ch = tk.IntVar(value=40)
        self.row = tk.IntVar(value=0); self.fps = tk.IntVar(value=8); self.frame = 0; self.sel = None
        self.show_grid = tk.BooleanVar(value=True); self._tk = {}
        self._build(); self.after(120, self._tick)

    # ------------------------------------------------------------ layout
    def _build(self):
        left = ttk.Frame(self, padding=6); left.pack(side='left', fill='y')
        ttk.Button(left, text='Open sheet...', command=self.open).pack(fill='x')
        ttk.Button(left, text='Open game sheet...', command=lambda: self.open(self._game_dir())).pack(fill='x', pady=2)
        g = ttk.LabelFrame(left, text='Grid', padding=4); g.pack(fill='x', pady=4)
        for i, (t, v) in enumerate((('Cell W', self.cw), ('Cell H', self.ch))):
            ttk.Label(g, text=t).grid(row=i, column=0); ttk.Spinbox(g, from_=1, to=512, width=5, textvariable=v, command=self.regrid).grid(row=i, column=1)
        ttk.Button(g, text='Detect', command=self.detect).grid(row=2, column=0, columnspan=2, sticky='ew', pady=2)
        ttk.Checkbutton(g, text='Show grid', variable=self.show_grid, command=self.redraw).grid(row=3, column=0, columnspan=2)
        a = ttk.LabelFrame(left, text='Animation row', padding=4); a.pack(fill='x', pady=4)
        ttk.Label(a, text='Row').grid(row=0, column=0); ttk.Spinbox(a, from_=0, to=999, width=5, textvariable=self.row).grid(row=0, column=1)
        ttk.Label(a, text='FPS').grid(row=1, column=0); ttk.Spinbox(a, from_=1, to=30, width=5, textvariable=self.fps).grid(row=1, column=1)
        ttk.Label(left, text='Zoom').pack(anchor='w'); ttk.Scale(left, from_=1, to=12, variable=self.zoom, command=lambda e: (self.zoom.set(round(float(e))), self.redraw())).pack(fill='x')
        r = ttk.LabelFrame(left, text='Colour ramps (click a pixel to select)', padding=4); r.pack(fill='both', expand=True, pady=4)
        self.lb = tk.Listbox(r, width=30, height=12, exportselection=False); self.lb.pack(fill='both', expand=True)
        self.lb.bind('<<ListboxSelect>>', lambda e: self.select(self.lb.curselection()[0] if self.lb.curselection() else None))
        self.slot = ttk.Combobox(r, values=S.SLOTS, state='readonly'); self.slot.pack(fill='x', pady=2); self.slot.bind('<<ComboboxSelected>>', self.set_slot)
        ttk.Button(r, text='New colour...', command=self.pick).pack(fill='x')
        ttk.Button(r, text='Reset ramp', command=self.reset).pack(fill='x', pady=2)
        e = ttk.LabelFrame(left, text='Export', padding=4); e.pack(fill='x')
        ttk.Button(e, text='Baked PNG...', command=self.save_baked).pack(fill='x')
        ttk.Button(e, text='Indexed + palette...', command=self.save_indexed).pack(fill='x', pady=2)
        ttk.Button(e, text='Save scheme (json)...', command=self.save_scheme).pack(fill='x')
        right = ttk.Frame(self); right.pack(side='left', fill='both', expand=True)
        top = ttk.Frame(right); top.pack(fill='both', expand=True)
        self.cv = tk.Canvas(top, bg='#2a2c33', highlightthickness=0)
        xs = ttk.Scrollbar(top, orient='horizontal', command=self.cv.xview); ys = ttk.Scrollbar(top, command=self.cv.yview)
        self.cv.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        xs.pack(side='bottom', fill='x'); ys.pack(side='right', fill='y'); self.cv.pack(fill='both', expand=True)
        self.cv.bind('<Button-1>', self.click)
        self.prev = tk.Canvas(right, bg='#2a2c33', height=190, highlightthickness=0); self.prev.pack(fill='x')
        self.status = ttk.Label(right, text='Open a sprite sheet to start.'); self.status.pack(fill='x')

    def _game_dir(self):
        d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sprites', 'out_uv')
        return d if os.path.isdir(d) else None

    # ------------------------------------------------------------ loading
    def open(self, initial=None):
        p = filedialog.askopenfilename(initialdir=initial, filetypes=[('Images', '*.png *.gif *.bmp'), ('All', '*.*')])
        if not p: return
        self.path = p; self.img = S.load(p)
        self.cols, self.cnt = S.unique_colours(self.img)
        self.ramps = S.group_ramps(self.cols, self.cnt)
        self.idx = S.colour_index_map(self.img, self.cols) if len(self.cols) else None
        self.out = self.img; self.detect(); self.refresh_list()
        self.status.config(text=f'{os.path.basename(p)}  {self.img.size[0]}x{self.img.size[1]}  {len(self.cols)} colours  {len(self.ramps)} ramps')

    def detect(self):
        if not self.img: return
        w, h = S.detect_grid(self.img); self.cw.set(w); self.ch.set(h); self.regrid()

    def regrid(self):
        self.frame = 0; self.redraw()

    def refresh_list(self):
        self.lb.delete(0, 'end')
        for i, r in enumerate(self.ramps):
            c = r['target'] or r['base']
            self.lb.insert('end', f"{i}  #{c[0]:02x}{c[1]:02x}{c[2]:02x}  {r['slot']}  ({r['pixels']} px)")
            self.lb.itemconfig(i, bg='#%02x%02x%02x' % tuple(c), fg='white' if sum(c) < 380 else 'black')

    # ------------------------------------------------------------ ramp editing
    def select(self, i):
        self.sel = i
        if i is not None: self.slot.set(self.ramps[i]['slot'])
        self.redraw()

    def set_slot(self, _e=None):
        if self.sel is not None: self.ramps[self.sel]['slot'] = self.slot.get(); self.refresh_list(); self.lb.selection_set(self.sel)

    def pick(self):
        if self.sel is None: return
        r = self.ramps[self.sel]
        c = colorchooser.askcolor(color='#%02x%02x%02x' % tuple(r['target'] or r['base']))[0]
        if c: r['target'] = tuple(int(x) for x in c); self.rebake()

    def reset(self):
        if self.sel is not None: self.ramps[self.sel]['target'] = None; self.rebake()

    def rebake(self):
        self.out = S.apply(self.img, self.cols, self.ramps, self.idx); self.refresh_list()
        if self.sel is not None: self.lb.selection_set(self.sel)
        self.redraw()

    def click(self, ev):
        if self.img is None: return
        z = self.zoom.get(); x = int(self.cv.canvasx(ev.x) // z); y = int(self.cv.canvasy(ev.y) // z)
        if 0 <= x < self.img.size[0] and 0 <= y < self.img.size[1]:
            j = int(self.idx[y, x])
            for i, r in enumerate(self.ramps):
                if j in r['idx']:
                    self.lb.selection_clear(0, 'end'); self.lb.selection_set(i); self.lb.see(i); self.select(i); return
            cw, ch = self.cw.get(), self.ch.get()
            self.row.set(y // ch); self.frame = 0

    # ------------------------------------------------------------ drawing
    def _photo(self, im, z, key):
        p = ImageTk.PhotoImage(im.resize((im.size[0] * z, im.size[1] * z), Image.NEAREST)); self._tk[key] = p; return p

    def _checker(self, im, z):
        w, h = im.size; bg = Image.new('RGBA', (w, h), (60, 62, 70, 255))
        a = np.array(bg); a[(np.indices((h, w)).sum(0) // 4) % 2 == 0, :3] = (74, 76, 86)
        return Image.alpha_composite(Image.fromarray(a, 'RGBA'), im)

    def redraw(self):
        if self.img is None: return
        z = self.zoom.get(); im = self._checker(self.out, z)
        if self.sel is not None:   # highlight the selected ramp's pixels
            m = np.isin(self.idx, self.ramps[self.sel]['idx']); a = np.array(im); a[m] = (a[m] * 0.6 + np.array([255, 255, 0, 255]) * 0.4).astype(np.uint8); im = Image.fromarray(a, 'RGBA')
        self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self._photo(im, z, 'sheet'))
        W, H = self.img.size; self.cv.configure(scrollregion=(0, 0, W * z, H * z))
        if self.show_grid.get():
            cw, ch = max(1, self.cw.get()), max(1, self.ch.get())
            for x in range(0, W + 1, cw): self.cv.create_line(x * z, 0, x * z, H * z, fill='#4a90e2')
            for y in range(0, H + 1, ch): self.cv.create_line(0, y * z, W * z, y * z, fill='#4a90e2')

    def _tick(self):
        try:
            if self.img is not None:
                cw, ch = max(1, self.cw.get()), max(1, self.ch.get())
                rows = max(1, self.img.size[1] // ch); cols = max(1, self.img.size[0] // cw)
                r = min(self.row.get(), rows - 1); self.frame = (self.frame + 1) % cols
                f = self.out.crop((self.frame * cw, r * ch, self.frame * cw + cw, r * ch + ch))
                z = max(1, min(8, 180 // ch)); self.prev.delete('all')
                self.prev.create_image(10, 5, anchor='nw', image=self._photo(self._checker(f, z), z, 'frame'))
                # contact strip of the whole row
                strip = self.out.crop((0, r * ch, cols * cw, r * ch + ch)); zz = max(1, min(2, 900 // max(1, strip.size[0])))
                self.prev.create_image(10 + cw * z + 20, 5, anchor='nw', image=self._photo(self._checker(strip, zz), zz, 'strip'))
                self.prev.create_text(10, 185, anchor='sw', fill='white', text=f'row {r}  frame {self.frame + 1}/{cols}')
        except tk.TclError:
            pass
        self.after(max(30, 1000 // max(1, self.fps.get())), self._tick)

    # ------------------------------------------------------------ export
    def _need(self):
        if self.img is None: messagebox.showinfo('Sprite manager', 'Open a sheet first.'); return False
        return True

    def save_baked(self):
        if not self._need(): return
        p = filedialog.asksaveasfilename(defaultextension='.png', initialfile=os.path.splitext(os.path.basename(self.path))[0] + '_recolour.png')
        if p: self.out.save(p); self.status.config(text=f'Saved {p}')

    def save_indexed(self):
        if not self._need(): return
        p = filedialog.asksaveasfilename(defaultextension='.png', initialfile=os.path.splitext(os.path.basename(self.path))[0] + '_indexed.png')
        if not p: return
        try:
            S.export_indexed(self.img, self.cols, self.ramps, self.idx, p, os.path.splitext(p)[0] + '_palette.png')
            self.status.config(text=f'Saved {p} and *_palette.png')
        except ValueError as e:
            messagebox.showerror('Sprite manager', str(e))

    def save_scheme(self):
        if not self._need(): return
        p = filedialog.asksaveasfilename(defaultextension='.json')
        if p: S.save_scheme(p, self.ramps)


if __name__ == '__main__':
    App().mainloop()
