import os, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import numpy as np
import tables, looks, playercard, foil
from rules import *

EXPORT = os.path.join(tables.ROOT, 'export')


def next_id(t, prefix, width=3):
    n = max([to_int(r['id'][len(prefix):], 0) for r in t.rows if r['id'].startswith(prefix)] + [0]) + 1
    return f'{prefix}{n:0{width}d}'


def new_player(t):
    r = {c: '' for c in t.cols}
    r.update(id=next_id(t, 'PL'), name='New Player', rarity='COMMON', role='CM', roles='CM', rating='60', skin='2',
             hair_style='H02_crop', hair_color='brown', beard='none', glasses='none', chain='0', headband='0', wristband='0', tattoo='0', special='0')
    for k in OUT_STATS: r[k] = '60'
    r['rating'] = str(auto_rating(r))
    return r


class PlayersTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('players'); self.i = None; self.loading = False; self.fr = 0; self.pal = looks.palette()
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        ch = dict(rarity=RARITY, role=ROLES, skin=list(self.pal['skin']), hair_style=looks.hair_styles(), hair_color=list(self.pal['hair']),
                  beard=BEARD, glasses=GLASSES, chain=['0', '1'], headband=['0', '1'], wristband=['0', '1'], tattoo=['0', '1'], special=['0', '1'])
        self.grid = tables.Grid(pw, self.t, choices=ch, new_row=new_player, on_select=self.select,
                                width_for=dict(name=150, roles=80), extra_buttons=[('Auto rating', self.auto_rating)])
        pw.add(self.grid, weight=3)
        side = ttk.Frame(pw, padding=6); pw.add(side, weight=1)
        self.nb = ttk.Notebook(side); self.nb.pack(fill='x')
        self.cv = tk.Canvas(self.nb, width=340, height=280, bg='#46964a', highlightthickness=0); self.nb.add(self.cv, text='Sprite')
        cf = ttk.Frame(self.nb); self.nb.add(cf, text='Card')
        self.cc = tk.Canvas(cf, width=340, height=280, bg='#14161f', highlightthickness=0); self.cc.pack()
        self.tip = tk.IntVar(value=1); self.shim = tk.IntVar(value=1)
        cr = ttk.Frame(cf); cr.pack(fill='x')
        ttk.Checkbutton(cr, text='tooltip', variable=self.tip).pack(side='left'); ttk.Checkbutton(cr, text='shimmer', variable=self.shim).pack(side='left', padx=6)
        self.cstyle = ttk.Combobox(cr, values=['auto'] + list(playercard.STYLES), state='readonly', width=8); self.cstyle.set('auto'); self.cstyle.pack(side='left')
        self.ct = 0; self._cache = {}
        row = ttk.Frame(side); row.pack(fill='x', pady=2)
        self.anim = ttk.Combobox(row, values=list(looks.anims()), state='readonly', width=9); self.anim.set('run'); self.anim.pack(side='left')
        self.kit = ttk.Combobox(row, values=['auto'] + looks.KITS, state='readonly', width=7); self.kit.set('auto'); self.kit.pack(side='left', padx=3)
        self.dir = tk.IntVar(value=0)
        ttk.Label(row, text='Facing').pack(side='left'); ttk.Scale(row, from_=0, to=31, variable=self.dir, command=lambda e: self.dir.set(round(float(e)))).pack(side='left', fill='x', expand=True)
        self.name = ttk.Label(side, text='Select a player', font=('TkDefaultFont', 11, 'bold')); self.name.pack(anchor='w')
        lf = ttk.LabelFrame(side, text='Look', padding=4); lf.pack(fill='x', pady=4)
        self.w = {}
        for n, (k, vals) in enumerate((('skin', list(self.pal['skin'])), ('hair_style', looks.hair_styles()), ('hair_color', list(self.pal['hair'])), ('beard', BEARD), ('glasses', GLASSES))):
            ttk.Label(lf, text=k).grid(row=n, column=0, sticky='w')
            c = ttk.Combobox(lf, values=vals, state='readonly', width=16); c.grid(row=n, column=1, sticky='ew', pady=1)
            c.bind('<<ComboboxSelected>>', lambda e, k=k, c=c: self.put(k, c.get())); self.w[k] = c
        self.flags = {}
        fb = ttk.Frame(lf); fb.grid(row=5, column=0, columnspan=2)
        for k in ('chain', 'headband', 'wristband', 'tattoo', 'special'):
            v = tk.IntVar(); self.flags[k] = v
            ttk.Checkbutton(fb, text=k, variable=v, command=lambda k=k, v=v: self.put(k, str(v.get()))).pack(side='left')
        sf = ttk.LabelFrame(side, text='Stats', padding=4); sf.pack(fill='x')
        self.sf = sf; self.stat = {}
        for n, k in enumerate(OUT_STATS + GK_STATS):
            ttk.Label(sf, text=k).grid(row=n // 3, column=(n % 3) * 2)
            s = ttk.Spinbox(sf, from_=1, to=99, width=4, command=lambda k=k: self.put_stat(k)); s.grid(row=n // 3, column=(n % 3) * 2 + 1, padx=(0, 6), pady=1)
            s.bind('<Return>', lambda e, k=k: self.put_stat(k)); s.bind('<FocusOut>', lambda e, k=k: self.put_stat(k)); self.stat[k] = s
        self.rating = ttk.Label(sf, text=''); self.rating.grid(row=4, column=0, columnspan=6, sticky='w')
        eb = ttk.Frame(side); eb.pack(fill='x', pady=6)
        ttk.Button(eb, text='Export this look (PNG)', command=self.export_one).pack(fill='x')
        ttk.Button(eb, text='Export all 300 looks + index', command=self.export_all).pack(fill='x', pady=2)
        ttk.Button(eb, text='Export card faces + tooltips (+ shimmer strips)', command=self.export_cards).pack(fill='x')
        self.t.listeners.append(self.reload_form)
        self.after(90, self.tick)

    def refresh(self):
        self.anim['values'] = list(looks.anims()); self.kit['values'] = ['auto'] + looks.kit_ids(); self.w['hair_style']['values'] = looks.hair_styles()

    def select(self, idx):
        self.i = idx[0] if idx else None; self.reload_form()

    def row(self):
        return self.t.rows[self.i] if self.i is not None and self.i < len(self.t.rows) else None

    def reload_form(self):
        r = self.row()
        if not r: return
        self.name.config(text=f"{r['name']}  ({r['role']}, {r['rating']})")
        for k, c in self.w.items(): c.set(r.get(k, ''))
        for k, v in self.flags.items(): v.set(1 if r.get(k) == '1' else 0)
        gk = r['role'] == 'GK'
        for k, s in self.stat.items():
            s.config(state='normal' if (k in GK_STATS) == gk else 'disabled'); s.delete(0, 'end'); s.insert(0, r.get(k, ''))
        self.rating.config(text=f"rating {r['rating']}  (from stats: {auto_rating(r)})")

    def put(self, k, v):
        if self.i is not None: self.t.set(self.i, k, v)

    def put_stat(self, k):
        if self.i is None: return
        v = to_int(self.stat[k].get())
        if v is not None: self.t.set(self.i, k, str(max(1, min(99, v))))

    def auto_rating(self, grid=None):
        sel = self.grid.selected_indices() or range(len(self.t.rows))
        self.t.snapshot()
        for i in sel: self.t.rows[i]['rating'] = str(auto_rating(self.t.rows[i]))
        self.t.dirty = True; self.t.notify()

    def tick(self):
        try:
            r = self.row()
            if r and self.winfo_viewable() and self.nb.index(self.nb.select()) == 1:
                self.draw_card(r)
            elif r and self.winfo_viewable():
                a = self.anim.get() or 'run'
                n = looks.anims().get(a, {}).get('frames', 1); self.fr = (self.fr + 1) % max(1, n)
                kit = None if self.kit.get() == 'auto' else self.kit.get()
                im = looks.render(r, a, self.dir.get(), self.fr, kit).resize((240, 240), Image.NEAREST)
                self._ph = ImageTk.PhotoImage(im); self.cv.delete('all'); self.cv.create_image(150, 130, image=self._ph)
        except Exception as e:
            self.name.config(text=f'preview error: {e}')
        self.after(90, self.tick)

    def draw_card(self, r):
        kit = None if self.kit.get() == 'auto' else self.kit.get()
        st = None if self.cstyle.get() == 'auto' else self.cstyle.get()
        special = st or (foil.STYLE_BY_RARITY.get(r.get('rarity')) if r.get('special') == '1' else None)
        N = 36
        if special and self.shim.get(): self.ct = (self.ct + 1) % N
        else: self.ct = 0
        key = (tuple(sorted(r.items())), kit, special, self.ct)
        im = self._cache.get(key)
        if im is None:
            if len(self._cache) > 200: self._cache.clear()
            im = playercard.card(r, kit, special=special, t=self.ct / N).resize((192, 270), Image.NEAREST); self._cache[key] = im
        self._cph = ImageTk.PhotoImage(im); self.cc.delete('all'); self.cc.create_image(4, 5, image=self._cph, anchor='nw')
        if self.tip.get():
            tp = playercard.popup(r, 142); self._tph = ImageTk.PhotoImage(tp); self.cc.create_image(196, 5, image=self._tph, anchor='nw')

    def export_cards(self):
        out = os.path.join(EXPORT, 'players'); os.makedirs(out, exist_ok=True)
        idx = ['id,face,tooltip,special,shimmer_strip,shimmer_frames']
        N = 36
        for r in self.t.rows:
            pid = r['id']
            sp = r.get('special') == '1'
            playercard.card(r, special=None).resize((256, 360), Image.NEAREST).save(os.path.join(out, f'{pid}.png'))
            tp = playercard.popup(r); tp.resize((tp.width * 4, tp.height * 4), Image.NEAREST).save(os.path.join(out, f'{pid}_tip.png'))
            strip = ''
            if sp:
                fr = [playercard.card(r, t=k / N) for k in range(N)]
                sh = Image.new('RGBA', (64 * N, 90)); [sh.paste(f, (64 * k, 0)) for k, f in enumerate(fr)]
                sh.save(os.path.join(out, f'{pid}_shimmer.png')); strip = f'players/{pid}_shimmer.png'
            idx.append(f"{pid},players/{pid}.png,players/{pid}_tip.png,{1 if sp else 0},{strip},{N if sp else 0}")
        open(os.path.join(EXPORT, 'players_cards_index.csv'), 'w').write('\n'.join(idx) + '\n')
        messagebox.showinfo('Export', f'Wrote {len(self.t.rows)} player cards to {out}\n(special players also get a {N}-frame shimmer strip, 64x90 per frame; the shimmer is the first 30% of the loop)')

    def export_one(self):
        r = self.row()
        if not r: return
        p = filedialog.asksaveasfilename(defaultextension='.png', initialfile=f"{r['id']}_look.png")
        if p: Image.fromarray(looks.player_skin(r)).save(p)

    def export_all(self):
        os.makedirs(os.path.join(EXPORT, 'looks'), exist_ok=True)
        lines = ['id,hair_style,atlas,kit_slot']
        for r in self.t.rows:
            Image.fromarray(looks.player_skin(r)).save(os.path.join(EXPORT, 'looks', f"{r['id']}.png"))
            lines.append(f"{r['id']},{r['hair_style']},looks/{r['id']}.png,{'keeper' if r['role'] == 'GK' else 'outfield'}")
        open(os.path.join(EXPORT, 'looks_index.csv'), 'w').write('\n'.join(lines) + '\n')
        messagebox.showinfo('Export', f'Wrote {len(self.t.rows)} look atlases to {os.path.join(EXPORT, "looks")}')
