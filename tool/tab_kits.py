import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image, ImageTk
import tables, looks
from rules import *

FIELDS = ['jersey', 'trim', 'shorts', 'shorts_trim', 'stripe', 'socks', 'sock_trim', 'boots', 'accent', 'band', 'glove']
LABEL = dict(jersey='Shirt', trim='Collar / number', shorts='Shorts', shorts_trim='Shorts hem', stripe='Shorts stripe', socks='Socks', sock_trim='Sock top',
             boots='Boots', accent='Boot detail', band='Pattern colour', glove='Keeper gloves')
PATTERNS = ['plain', 'hoop', 'hoops', 'stripes', 'sash']
LOOKS = [dict(role='CM', skin='2', hair_color='brown', hair_style='H02_crop'), dict(role='ST', skin='5', hair_color='black', hair_style='H05_curly', beard='short'),
         dict(role='CB', skin='3', hair_color='blonde', hair_style='H04_quiff'), dict(role='LW', skin='6', hair_color='black', hair_style='H06_afro'),
         dict(role='GK', skin='1', hair_color='ginger', hair_style='H01_buzz'), dict(role='CDM', skin='4', hair_color='darkbrown', hair_style='H09_ponytail')]


def new_kit(t):
    r = {c: '' for c in t.cols}
    r.update(id=f'kit{len(t.rows) + 1}', name='New kit', pattern='plain', jersey='#2a6ad8', trim='#f4f4fa', shorts='#f4f4fa', shorts_trim='#2a6ad8', stripe='#2a6ad8',
             socks='#2a6ad8', sock_trim='#f4f4fa', boots='#1c1c2c', accent='#f0c040', number='8')
    return r


class KitsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('kits'); self.i = None; self.fr = 0
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw); pw.add(left)
        self.grid = tables.Grid(left, self.t, choices=dict(pattern=PATTERNS), new_row=new_kit, on_select=self.select, width_for=dict(id=70, name=90)); self.grid.pack(fill='both', expand=True)
        sw = ttk.LabelFrame(left, text='Colours (click a swatch)', padding=6); sw.pack(fill='x')
        self.btn = {}
        for n, f in enumerate(FIELDS):
            ttk.Label(sw, text=LABEL[f]).grid(row=n // 4 * 2, column=n % 4, sticky='w', padx=6)
            b = tk.Button(sw, width=10, relief='raised', command=lambda f=f: self.pick(f)); b.grid(row=n // 4 * 2 + 1, column=n % 4, padx=6, pady=(0, 6)); self.btn[f] = b
        side = ttk.Frame(pw, padding=4, width=500); side.pack_propagate(False); pw.add(side)
        self.cv = tk.Canvas(side, width=480, height=330, bg='#46964a', highlightthickness=0); self.cv.pack()
        ttk.Label(side, justify='left', foreground='#9aa0ae', wraplength=440,
                  text='Edit the table or click a swatch. Pattern uses the "Pattern colour" (blank = collar colour). The kit file is data/kits.csv; the game '
                       'sprites pick it up the next time gen_uv.py or the exporters run. Keeper gloves only show on kits with a glove colour.').pack(anchor='w', pady=6)
        self.t.listeners.append(self.sync); self.after(110, self.tick)

    def select(self, idx):
        self.i = idx[0] if idx else None; self.sync()

    def sync(self):
        if self.i is None or self.i >= len(self.t.rows): return
        r = self.t.rows[self.i]
        for f, b in self.btn.items():
            c = r.get(f) or ''
            try: b.config(bg=c or '#d9d9d9', activebackground=c or '#d9d9d9', text='' if c else 'none')
            except tk.TclError: b.config(bg='#d9d9d9', text='?')

    def pick(self, f):
        if self.i is None: return
        cur = self.t.rows[self.i].get(f) or '#ffffff'
        c = colorchooser.askcolor(color=cur, title=LABEL[f])[1]
        if c: self.t.set(self.i, f, c)

    def tick(self):
        try:
            if self.i is not None and self.i < len(self.t.rows) and self.winfo_viewable():
                kid = self.t.rows[self.i]['id']; self.fr += 1
                W = Image.new('RGBA', (40 * 6, 40), (70, 150, 74, 255))
                for n, p in enumerate(LOOKS):
                    kit = kid
                    W.alpha_composite(looks.render(p, 'run', (n * 5 + 2) % 32, self.fr, kit, shadow=True), (n * 40, 0))
                big = Image.new('RGBA', (480, 330), (70, 150, 74, 255)); big.alpha_composite(W.resize((480, 80), Image.NEAREST), (0, 10))
                # large close-ups: front and back view
                for n, d in enumerate((0, 16)):
                    f = looks.render(LOOKS[0], 'guard', d, self.fr % 12, kid).resize((200, 200), Image.NEAREST); big.alpha_composite(f, (10 + n * 220, 130))
                self._ph = ImageTk.PhotoImage(big); self.cv.delete('all'); self.cv.create_image(0, 0, anchor='nw', image=self._ph)
        except Exception as e:
            self.cv.delete('all'); self.cv.create_text(220, 160, fill='white', text=f'preview error: {e}')
        self.after(110, self.tick)

    def refresh(self):
        looks.KITS[:] = looks.kit_ids()
