"""Packs tab: create / duplicate / delete packs and edit everything about them. Data: data/packs.csv, data/pack_odds.csv, data/pack_pools.csv (logic in packs/packlib.py).
Sections: Definition + schedule | Odds, guarantee and pity | Pools | Look (wrapper, tilt shimmer) | Simulator | Opening preview (with the skip button)."""
import os, sys, threading, queue, random, datetime, types
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import tables
from rules import ROLES

PK = os.path.join(tables.ROOT, 'packs')
if PK not in sys.path: sys.path.insert(0, PK)
import packlib as PL
import design2 as D
import opening as O
from playercard import RC

CARD_CATS = ['SHOT', 'PASS', 'DRIBBLE', 'SUPPORT', 'DEFEND', 'KEEPER', 'TITAN']


class PacksTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('packs'); self.o = tables.table('pack_odds'); self.p = tables.table('pack_pools')
        self.players = tables.table('players'); self.cards = tables.table('cards')
        self.i = None; self.loading = False; self.q = queue.Queue(); self.frames = None; self.scene = None; self.fi = 0; self.playing = False; self.after_id = None
        self._wr = {}; self._tilt = None; self.tilt_i = 0
        bar = ttk.Frame(self); bar.pack(fill='x', padx=6, pady=4)
        for txt, fn in (('Save all', self.save), ('Reload', self.reload), ('Undo', self.undo), ('+ New pack', self.new), ('Duplicate', self.dup), ('Delete', self.delete)):
            ttk.Button(bar, text=txt, command=fn).pack(side='left', padx=2)
        self.msg = ttk.Label(bar, text='', foreground='#8a90a0'); self.msg.pack(side='left', padx=10)
        left = ttk.Frame(self, padding=(6, 0)); left.pack(side='left', fill='y')
        self.right = ttk.Frame(self, padding=6); self.right.pack(side='left', fill='both', expand=True)
        cols = ('source', 'price', 'items', 'state')
        self.tv = ttk.Treeview(left, columns=cols, show='tree headings', selectmode='browse', height=20)
        self.tv.heading('#0', text='pack'); self.tv.column('#0', width=150)
        for c, w in zip(cols, (60, 55, 50, 75)): self.tv.heading(c, text=c); self.tv.column(c, width=w, anchor='center')
        self.tv.pack(fill='y', expand=True); self.tv.bind('<<TreeviewSelect>>', lambda e: self.pick())
        for k, col in (('live', '#8fd79a'), ('upcoming', '#e6c46a'), ('expired', '#c46a6a'), ('hidden', '#8a90a0')): self.tv.tag_configure(k, foreground=col)
        self.nb = ttk.Notebook(self.right); self.nb.pack(fill='both', expand=True)
        self.build_def(); self.build_odds(); self.build_pools(); self.build_look(); self.build_sim(); self.build_open()
        for tb in (self.t, self.o, self.p): tb.listeners.append(self.on_data)
        self.nb.bind('<<NotebookTabChanged>>', lambda e: self.wrapper())
        self.fill(); self.poll()

    # ------------------------------------------------------------------ data helpers
    def row(self): return self.t.rows[self.i] if self.i is not None and self.i < len(self.t.rows) else None
    def pid(self): r = self.row(); return r['id'] if r else None
    def orow(self):
        pid = self.pid()
        if pid is None: return None
        r = next((x for x in self.o.rows if x['pack'] == pid), None)
        if r is None:
            self.o.snapshot(); r = dict(pack=pid, common='50', uncommon='32', rare='14', epic='3.5', legend='0.5'); self.o.rows.append(r); self.o.dirty = True
        return r
    def prows(self): pid = self.pid(); return [x for x in self.p.rows if x['pack'] == pid]
    def bundle(self): return dict(pk=self.row(), odds=self.orow(), pools=self.prows())

    def setv(self, col, val):
        if self.loading or self.i is None: return
        self.t.set(self.i, col, val)

    def seto(self, col, val):
        if self.loading or self.i is None: return
        o = self.orow(); i = self.o.rows.index(o); self.o.set(i, col, val)

    def on_data(self):
        try: self.fill(keep=True); self.refresh_views()
        except tk.TclError: pass

    def msgs(self, text): self.msg.config(text=text)

    def save(self):
        for tb in (self.t, self.o, self.p): tb.save()
        self.msgs('saved packs, pack_odds and pack_pools')

    def reload(self):
        for tb in (self.t, self.o, self.p): tb.load()
        self.msgs('reloaded')

    def undo(self):
        for tb in (self.t, self.o, self.p):
            if tb.undo: tb.do_undo(); break

    def new_id(self, base='pack'):
        ids = {r['id'] for r in self.t.rows}; n = 1
        while f'{base}{n}' in ids: n += 1
        return f'{base}{n}'

    def new(self):
        pid = self.new_id(); self.t.snapshot()
        self.t.rows.append(dict(id=pid, name='New Pack', source='shop', price='500', player_items='2', card_items='2', tier='COMMON', foil='', silhouette='bust', guarantee_min='', pity_rarity='RARE', pity_start='8', pity_step='2', pity_hard='25',
                                start='', end='', sort=str(10 * (len(self.t.rows) + 1)), active='1', note=''))
        self.o.rows.append(dict(pack=pid, common='50', uncommon='32', rare='14', epic='3.5', legend='0.5'))
        self.t.dirty = self.o.dirty = True; self.t.notify(); self.select_index(len(self.t.rows) - 1)

    def dup(self):
        r = self.row()
        if not r: return
        pid = self.new_id(r['id'] + '_copy'); self.t.snapshot(); self.o.snapshot(); self.p.snapshot()
        nr = dict(r); nr['id'] = pid; nr['name'] = r['name'] + ' Copy'; self.t.rows.append(nr)
        o = self.orow(); self.o.rows.append(dict(o, pack=pid))
        for x in self.prows(): self.p.rows.append(dict(x, pack=pid))
        self.t.dirty = self.o.dirty = self.p.dirty = True; self.t.notify(); self.select_index(len(self.t.rows) - 1)

    def delete(self):
        r = self.row()
        if not r or not messagebox.askyesno('Delete pack', f"Delete {r['name']} and its odds and pools?"): return
        pid = r['id']; self.t.snapshot(); self.o.snapshot(); self.p.snapshot()
        self.t.rows.remove(r); self.o.rows = [x for x in self.o.rows if x['pack'] != pid]; self.p.rows = [x for x in self.p.rows if x['pack'] != pid]
        self.t.dirty = self.o.dirty = self.p.dirty = True; self.i = None; self.t.notify()

    # ------------------------------------------------------------------ list
    def fill(self, keep=False):
        sel = self.i; self._filling = True; self.tv.delete(*self.tv.get_children())
        for i, r in enumerate(self.t.rows):
            st = PL.state(r); n = PL.inum(r.get('player_items')) + PL.inum(r.get('card_items'))
            self.tv.insert('', 'end', iid=str(i), text=r.get('name', ''), values=(r.get('source', ''), r.get('price', ''), n, st), tags=(st,))
        if sel is not None and self.tv.exists(str(sel)): self.tv.selection_set(str(sel))
        self._filling = False
        if sel is None and self.t.rows and not keep: self.select_index(0)

    def select_index(self, i):
        if self.tv.exists(str(i)): self.tv.selection_set(str(i)); self.tv.see(str(i))
        self.i = i; self.pick()

    def pick(self):
        if getattr(self, '_filling', False): return
        sel = self.tv.selection()
        if sel: self.i = int(sel[0])
        self.load_fields(); self.refresh_views()

    # ------------------------------------------------------------------ definition
    def build_def(self):
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text='Definition'); self.v = {}
        def field(r, label, key, kind='entry', values=None, w=22, hint=''):
            ttk.Label(f, text=label).grid(row=r, column=0, sticky='e', padx=4, pady=3)
            var = tk.StringVar(); self.v[key] = var
            if kind == 'combo': wd = ttk.Combobox(f, textvariable=var, values=values, state='readonly', width=w - 2)
            elif kind == 'spin': wd = ttk.Spinbox(f, textvariable=var, from_=values[0], to=values[1], width=w - 2)
            else: wd = ttk.Entry(f, textvariable=var, width=w)
            wd.grid(row=r, column=1, sticky='w', pady=3)
            if hint: ttk.Label(f, text=hint, foreground='#8a90a0').grid(row=r, column=2, sticky='w', padx=6)
            var.trace_add('write', lambda *_: self.setv(key, var.get()))
        ttk.Label(f, text='id').grid(row=0, column=0, sticky='e', padx=4); self.idl = ttk.Label(f, text='', foreground='#8a90a0'); self.idl.grid(row=0, column=1, sticky='w')
        field(1, 'name', 'name', hint='shown on the wrapper (a trailing "Pack" is added by the art)')
        field(2, 'source', 'source', 'combo', PL.SOURCES, hint='shop = bought with coins, ranked = weekly reward (not for sale), event = limited')
        field(3, 'price (coins)', 'price', 'spin', (0, 100000), hint='0 for reward packs')
        field(4, 'player items', 'player_items', 'spin', (0, 12)); field(5, 'card items', 'card_items', 'spin', (0, 12))
        field(6, 'sort', 'sort', 'spin', (0, 999), hint='shop order, low first')
        field(7, 'start', 'start', hint='YYYY-MM-DD or YYYY-MM-DD HH:MM, blank = always')
        field(8, 'end', 'end', hint='blank = never ends. Expired packs leave the shop')
        ttk.Label(f, text='state').grid(row=9, column=0, sticky='e', padx=4, pady=3); self.stl = ttk.Label(f, text=''); self.stl.grid(row=9, column=1, columnspan=2, sticky='w')
        self.active = tk.IntVar(value=1); ttk.Checkbutton(f, text='active (untick to hide from the shop)', variable=self.active, command=lambda: self.setv('active', str(self.active.get()))).grid(row=10, column=1, sticky='w', pady=3)
        field(11, 'note', 'note', w=60)
        self.chk = tk.Text(f, height=7, width=84, bg='#1b1d27', fg='#d8dcea', relief='flat'); self.chk.grid(row=12, column=0, columnspan=3, sticky='we', pady=(12, 0))
        self.chk.tag_configure('error', foreground='#ff8a80'); self.chk.tag_configure('warn', foreground='#ffd36a'); self.chk.tag_configure('ok', foreground='#8fd79a')

    # ------------------------------------------------------------------ odds / pity
    def build_odds(self):
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text='Odds, guarantee, pity'); self.ov = {}
        ttk.Label(f, text='Rarity odds per item (percent)', font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, columnspan=4, sticky='w')
        self.obar = tk.Canvas(f, width=420, height=22, bg='#14161f', highlightthickness=0); self.obar.grid(row=1, column=0, columnspan=4, sticky='w', pady=4)
        for k, r in enumerate(PL.RARS):
            ttk.Label(f, text=r.title() + '  \u25a0', foreground='#%02x%02x%02x' % tuple(int(v * 0.8) for v in RC[r]['main'])).grid(row=2 + k, column=0, sticky='e', padx=4)
            var = tk.StringVar(); self.ov[r.lower()] = var; ttk.Spinbox(f, textvariable=var, from_=0, to=100, increment=0.5, width=8).grid(row=2 + k, column=1, sticky='w', pady=2)
            var.trace_add('write', lambda *_, key=r.lower(), var=var: (self.seto(key, var.get()), self.odds_view()))
        self.tot = ttk.Label(f, text=''); self.tot.grid(row=7, column=0, columnspan=2, sticky='w', padx=4, pady=4)
        ttk.Button(f, text='Scale to 100', command=self.normalise).grid(row=7, column=2, sticky='w')
        ttk.Separator(f).grid(row=8, column=0, columnspan=4, sticky='we', pady=8)
        ttk.Label(f, text='Guarantee and pity', font=('TkDefaultFont', 10, 'bold')).grid(row=9, column=0, columnspan=4, sticky='w')
        self.gv = {}
        def fld(r, label, key, kind, values, hint):
            ttk.Label(f, text=label).grid(row=r, column=0, sticky='e', padx=4, pady=2); var = tk.StringVar(); self.gv[key] = var
            wd = ttk.Combobox(f, textvariable=var, values=values, state='readonly', width=10) if kind == 'combo' else ttk.Spinbox(f, textvariable=var, from_=0, to=1000, increment=1, width=8)
            wd.grid(row=r, column=1, sticky='w'); ttk.Label(f, text=hint, foreground='#8a90a0').grid(row=r, column=2, columnspan=2, sticky='w', padx=6)
            var.trace_add('write', lambda *_: (self.setv(key, var.get()), self.odds_view()))
        fld(10, 'guarantee at least', 'guarantee_min', 'combo', [''] + PL.RARS, 'every pack holds one item at this rarity or better (blank = none)')
        fld(11, 'pity rarity', 'pity_rarity', 'combo', PL.RARS, 'the rarity the dry-spell counter watches')
        fld(12, 'boost starts after', 'pity_start', 'spin', None, 'packs without that rarity before the odds start to lift')
        fld(13, 'boost per pack', 'pity_step', 'spin', None, 'percentage points moved up to that rarity and better, per extra dry pack')
        fld(14, 'hard guarantee at', 'pity_hard', 'spin', None, 'this many dry packs in a row force one (0 = off). Boost 0 and hard 0 = pity off')
        ttk.Label(f, text='Odds after a dry spell of').grid(row=15, column=0, sticky='e', padx=4, pady=(10, 2)); self.dry = tk.IntVar(value=0)
        ttk.Scale(f, from_=0, to=40, variable=self.dry, length=240, command=lambda e: self.odds_view()).grid(row=15, column=1, columnspan=2, sticky='w', pady=(10, 2)); self.dryl = ttk.Label(f, text=''); self.dryl.grid(row=15, column=3, sticky='w')
        self.pv = ttk.Label(f, text='', justify='left'); self.pv.grid(row=16, column=0, columnspan=4, sticky='w', padx=4)

    def normalise(self):
        o = self.orow()
        if not o: return
        t = PL.odds_total(o) or 1
        for k in PL.RARS: self.ov[k.lower()].set(f"{PL.num(o.get(k.lower())) * 100 / t:.1f}".rstrip('0').rstrip('.'))

    def odds_view(self):
        o = self.orow(); r = self.row()
        if not o or not r: return
        t = PL.odds_total(o); self.tot.config(text=f'total {t:g}%' + ('' if abs(t - 100) < 0.05 else '   (should be 100)'), foreground='#8fd79a' if abs(t - 100) < 0.05 else '#ff8a80')
        dry = int(self.dry.get()); w = PL.weights(r, o, dry); self.dryl.config(text=f'{dry} packs')
        self.obar.delete('all'); x = 0
        for k, name in enumerate(PL.RARS):
            ww = 420 * w[k] / 100.0; self.obar.create_rectangle(x, 0, x + ww, 22, fill='#%02x%02x%02x' % RC[name]['main'], outline=''); x += ww
        self.pv.config(text='   '.join(f'{n[:3].title()} {w[k]:.1f}%' for k, n in enumerate(PL.RARS)) + (f"\nboost now: +{PL.pity_extra(r, dry):g} points toward {r.get('pity_rarity')}+" if PL.pity_on(r) else '\npity is off for this pack'))

    # ------------------------------------------------------------------ pools
    def build_pools(self):
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text='Pools')
        ttk.Label(f, text='What this pack can contain. No rows for a kind = everything. Include rows narrow it; exclude rows remove. Weight raises or lowers the chance inside the pool.', foreground='#8a90a0', wraplength=720, justify='left').pack(anchor='w')
        cols = ('kind', 'category', 'rarity', 'id', 'mode', 'weight', 'note')
        self.ptv = ttk.Treeview(f, columns=cols, show='headings', height=9, selectmode='browse')
        for c, w in zip(cols, (60, 90, 90, 70, 70, 60, 260)): self.ptv.heading(c, text=c); self.ptv.column(c, width=w, anchor='w')
        self.ptv.pack(fill='x', pady=6); self.ptv.bind('<<TreeviewSelect>>', lambda e: self.pool_load())
        fm = ttk.Frame(f); fm.pack(fill='x'); self.pf = {}
        spec = (('kind', ['player', 'card'], 8), ('category', [''] + ROLES + CARD_CATS, 10), ('rarity', [''] + PL.RARS, 10), ('id', None, 8), ('mode', ['include', 'exclude'], 9), ('weight', None, 6), ('note', None, 28))
        for k, (name, vals, w) in enumerate(spec):
            ttk.Label(fm, text=name).grid(row=0, column=k, sticky='w', padx=2); var = tk.StringVar(); self.pf[name] = var
            (ttk.Combobox(fm, textvariable=var, values=vals, width=w) if vals else ttk.Entry(fm, textvariable=var, width=w)).grid(row=1, column=k, padx=2)
        self.pf['kind'].set('player'); self.pf['mode'].set('include'); self.pf['weight'].set('1')
        br = ttk.Frame(f); br.pack(fill='x', pady=6)
        ttk.Button(br, text='Add row', command=self.pool_add).pack(side='left'); ttk.Button(br, text='Update selected', command=self.pool_upd).pack(side='left', padx=4); ttk.Button(br, text='Delete selected', command=self.pool_del).pack(side='left')
        ttk.Label(f, text='Category: for players the main role (ST, CB...), for cards SHOT / PASS / DRIBBLE / SUPPORT / DEFEND / KEEPER / TITAN. id: one specific player or card (PL010, SH03).', foreground='#8a90a0', wraplength=720, justify='left').pack(anchor='w')
        self.pinfo = tk.Text(f, height=6, width=84, bg='#1b1d27', fg='#d8dcea', relief='flat'); self.pinfo.pack(fill='x', pady=8)

    def pool_rows(self): return self.prows()

    def pool_fill(self):
        self.ptv.delete(*self.ptv.get_children())
        for x in self.pool_rows(): self.ptv.insert('', 'end', iid=str(self.p.rows.index(x)), values=tuple(x.get(c, '') for c in ('kind', 'category', 'rarity', 'id', 'mode', 'weight', 'note')))
        lines = []
        b = self.bundle()
        for kind, rows in (('players', self.players.rows), ('cards', self.cards.rows)):
            el = PL.eligible(kind[:-1], b['pools'], rows, fallback=False)
            lines.append(f'{kind}: ' + '   '.join(f'{r[:3].title()} {len(el[r])}' for r in PL.RARS) + f'   (of {len(rows)})')
        self.pinfo.delete('1.0', 'end'); self.pinfo.insert('end', '\n'.join(lines))

    def pool_load(self):
        sel = self.ptv.selection()
        if not sel: return
        x = self.p.rows[int(sel[0])]
        for k, v in self.pf.items(): v.set(x.get(k, ''))

    def pool_vals(self): return {k: v.get().strip() for k, v in self.pf.items()}

    def pool_add(self):
        if self.i is None: return
        self.p.snapshot(); x = dict(pack=self.pid(), **self.pool_vals()); self.p.rows.append(x); self.p.dirty = True; self.p.notify()

    def pool_upd(self):
        sel = self.ptv.selection()
        if not sel: return
        self.p.snapshot(); self.p.rows[int(sel[0])].update(self.pool_vals()); self.p.dirty = True; self.p.notify()

    def pool_del(self):
        sel = self.ptv.selection()
        if not sel: return
        self.p.snapshot(); del self.p.rows[int(sel[0])]; self.p.dirty = True; self.p.notify()

    # ------------------------------------------------------------------ look
    def build_look(self):
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text='Look'); self.lv = {}
        left = ttk.Frame(f); left.pack(side='left', anchor='n')
        for r, (label, key, vals) in enumerate((('tier (colour)', 'tier', PL.RARS), ('foil', 'foil', PL.FOILS), ('silhouette', 'silhouette', PL.SILS))):
            ttk.Label(left, text=label).grid(row=r, column=0, sticky='e', padx=4, pady=4); var = tk.StringVar(); self.lv[key] = var
            ttk.Combobox(left, textvariable=var, values=vals, state='readonly', width=12).grid(row=r, column=1, sticky='w')
            var.trace_add('write', lambda *_, key=key, var=var: (self.setv(key, var.get()), self.wrapper()))
        self.tilt = tk.IntVar(value=1); ttk.Checkbutton(left, text='tilt shimmer', variable=self.tilt, command=self.wrapper).grid(row=4, column=1, sticky='w', pady=6)
        ttk.Label(left, text='The wrapper is drawn from this data: count, tier, name and\ncost come from the Definition tab. Foil and tier give the\nrarity feel; silhouette picks the picture.', foreground='#8a90a0', justify='left').grid(row=5, column=0, columnspan=2, sticky='w', pady=10)
        self.wc = tk.Canvas(f, width=400, height=520, bg='#16131f', highlightthickness=0); self.wc.pack(side='left', padx=20)
        self.wimg = None

    def wrapper(self):
        r = self.row()
        if not r: return
        key = tuple(r.get(k, '') for k in ('name', 'tier', 'foil', 'silhouette', 'player_items', 'card_items', 'price'))
        if self._wr.get('key') != key:
            art = D.foil_bag(r); self._wr = dict(key=key, art=art, tilt=None)
        if not getattr(self, '_looping', False): self.tilt_i = 0
        self.wdraw()

    def wdraw(self):
        if not self.winfo_exists(): return
        w = self._wr
        if not w: return
        if self.nb.index(self.nb.select()) != 3: return                                  # only draw while the Look tab is showing
        if self.tilt.get():
            if w['tilt'] is None: w['tilt'] = O.tilt_frames(types.SimpleNamespace(art=w['art']), 32)
            im = w['tilt'][self.tilt_i % 32]; self.tilt_i += 1
            im = im.crop((120, 0, 360, 270)).resize((400, 450), Image.NEAREST); bg = Image.new('RGB', (400, 520), (22, 19, 31)); bg.paste(im.convert('RGB'), (0, 35)); im = bg
        else:
            im = Image.new('RGBA', (400, 520), (22, 19, 31, 255)); im.alpha_composite(w['art'].resize((256, 384), Image.NEAREST), (72, 68))
        self.wimg = ImageTk.PhotoImage(im.convert('RGB')); self.wc.delete('all'); self.wc.create_image(0, 0, image=self.wimg, anchor='nw')
        if self.tilt.get(): self.after(60, self.wdraw)

    # ------------------------------------------------------------------ simulator
    def build_sim(self):
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text='Simulator')
        top = ttk.Frame(f); top.pack(fill='x')
        ttk.Label(top, text='Packs to open').pack(side='left'); self.nsim = tk.StringVar(value='10000'); ttk.Spinbox(top, textvariable=self.nsim, from_=100, to=200000, increment=1000, width=9).pack(side='left', padx=4)
        ttk.Button(top, text='Run this pack', command=lambda: self.run_sim(False)).pack(side='left', padx=2); ttk.Button(top, text='Compare all packs', command=lambda: self.run_sim(True)).pack(side='left', padx=2)
        self.simst = ttk.Label(top, text='', foreground='#8a90a0'); self.simst.pack(side='left', padx=10)
        ttk.Label(f, text='Opens packs in a row the way one player would, carrying the pity counter. Uses the current (even unsaved) odds, pools and pity.', foreground='#8a90a0').pack(anchor='w', pady=4)
        self.sc = tk.Canvas(f, width=700, height=170, bg='#14161f', highlightthickness=0); self.sc.pack(anchor='w')
        self.st = tk.Text(f, height=16, width=110, bg='#1b1d27', fg='#d8dcea', relief='flat', font=('Courier', 9)); self.st.pack(fill='both', expand=True, pady=6)

    def run_sim(self, everything):
        try: n = max(100, int(self.nsim.get()))
        except ValueError: n = 10000
        if not everything and self.i is None: return
        bs = [dict(pk=dict(r), odds=dict(next((x for x in self.o.rows if x['pack'] == r['id']), {})), pools=[dict(x) for x in self.p.rows if x['pack'] == r['id']]) for r in (self.t.rows if everything else [self.row()])]
        pl = [dict(r) for r in self.players.rows]; cd = [dict(r) for r in self.cards.rows]; self.simst.config(text='running...')
        def work():
            out = []
            for b in bs: out.append((b, PL.simulate(b, pl, cd, n)))
            self.q.put(('sim', out, everything))
        threading.Thread(target=work, daemon=True).start()

    def sim_show(self, out, everything):
        self.simst.config(text='done'); self.st.delete('1.0', 'end'); self.sc.delete('all')
        if everything:
            self.st.insert('end', f"{'pack':<22}{'price':>7}{'items':>6}{'rare+/pack':>12}{'epic+/pack':>12}{'legend/pack':>13}{'coins/epic+':>13}{'coins/legend':>14}\n")
            for b, r in out:
                self.st.insert('end', f"{b['pk']['name'][:21]:<22}{r['price']:>7.0f}{r['per_pack_items']:>6}{r['at_least']['RARE']:>11.1f}%{r['at_least']['EPIC']:>11.1f}%{r['at_least']['LEGEND']:>12.1f}%{r['cost_per_epic']:>13.0f}{r['cost_per_legend']:>14.0f}\n")
            return
        b, r = out[0]; self.st.insert('end', PL.report(r, b['pk']['name']) + '\n')
        for s, m in PL.check(b, [dict(x) for x in self.players.rows], [dict(x) for x in self.cards.rows]): self.st.insert('end', f'[{s}] {m}\n')
        for row, (lab, key) in enumerate((('items', 'items'), ('best in pack', 'best'), ('at least', 'at_least'))):
            y = 14 + row * 50; self.sc.create_text(4, y + 10, text=lab, anchor='w', fill='#aab', font=('TkDefaultFont', 8)); x = 90
            for k, name in enumerate(PL.RARS):
                v = r[key][name]; ww = 560 * v / (100.0 if key != 'at_least' else 100.0) if key != 'at_least' else 110 * v / 100.0
                if key != 'at_least':
                    self.sc.create_rectangle(x, y, x + ww, y + 22, fill='#%02x%02x%02x' % RC[name]['main'], outline='')
                    if ww > 30: self.sc.create_text(x + ww / 2, y + 11, text=f'{v:.1f}%', fill='#101018', font=('TkDefaultFont', 8, 'bold'))
                    x += ww
                else:
                    xx = 90 + k * 118; self.sc.create_rectangle(xx, y, xx + ww, y + 22, fill='#%02x%02x%02x' % RC[name]['main'], outline=''); self.sc.create_text(xx + 112, y + 11, text=f'{name[:3].title()} {v:.0f}%', anchor='e', fill='#d8dcea', font=('TkDefaultFont', 8))

    # ------------------------------------------------------------------ opening preview
    def build_open(self):
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text='Opening preview')
        top = ttk.Frame(f); top.pack(fill='x')
        ttk.Button(top, text='Roll + play', command=lambda: self.open_new(True)).pack(side='left'); ttk.Button(top, text='Same pull again', command=lambda: self.open_new(False)).pack(side='left', padx=3)
        ttk.Label(top, text='best at least').pack(side='left', padx=(10, 2)); self.best = tk.StringVar(value='any'); ttk.Combobox(top, textvariable=self.best, values=['any'] + PL.RARS[2:], state='readonly', width=8).pack(side='left')
        ttk.Label(top, text='dry spell').pack(side='left', padx=(10, 2)); self.odry = tk.StringVar(value='0'); ttk.Spinbox(top, textvariable=self.odry, from_=0, to=100, width=4).pack(side='left')
        self.pause_b = ttk.Button(top, text='Pause', command=self.open_pause); self.pause_b.pack(side='left', padx=(14, 2))
        self.skip_b = ttk.Button(top, text='Skip >>', command=self.open_skip); self.skip_b.pack(side='left', padx=2)
        self.ost = ttk.Label(top, text='', foreground='#8a90a0'); self.ost.pack(side='left', padx=10)
        self.oc = tk.Canvas(f, width=720, height=405, bg='#000', highlightthickness=0); self.oc.pack(pady=6, anchor='w'); self.oimg = None
        self.pb = ttk.Progressbar(f, length=720); self.pb.pack(anchor='w')
        self.pull_l = ttk.Label(f, text='', justify='left', wraplength=720); self.pull_l.pack(anchor='w', pady=4)
        ttk.Label(f, text='Skip jumps to the summary row. In the game the skip button does the same, and duplicates level the card up.', foreground='#8a90a0').pack(anchor='w')

    def open_new(self, reroll):
        if self.i is None: return
        if reroll or self.scene is None: self.seed = random.randrange(1, 10 ** 6)
        best = None if self.best.get() == 'any' else self.best.get()
        try: dry = int(self.odry.get())
        except ValueError: dry = 0
        self.playing = False; self.frames = None; self.ost.config(text='rendering frames...'); self.pb.config(value=0, maximum=100)
        b = self.bundle(); b = dict(pk=dict(b['pk']), odds=dict(b['odds']), pools=[dict(x) for x in b['pools']])
        pl = [dict(r) for r in self.players.rows]; cd = [dict(r) for r in self.cards.rows]; seed = self.seed
        def work():
            try:
                s = O.Scene(b, seed, best, dry, pl, cd); self.q.put(('scene', s))
                fr = []
                for i in range(s.N): fr.append(s.frame(i)); (i % 12 == 0) and self.q.put(('prog', i, s.N))
                self.q.put(('frames', s, fr))
            except Exception as e:
                import traceback; self.q.put(('err', traceback.format_exc()))
        threading.Thread(target=work, daemon=True).start()

    def open_pause(self):
        if self.frames and self.fi >= len(self.frames) - 1: self.fi = 0; self.playing = False
        self.playing = not self.playing; self.pause_b.config(text='Pause' if self.playing else 'Play')
        if self.playing: self.open_tick()

    def open_skip(self):
        if self.frames is None or self.scene is None: return
        self.fi = self.scene.skip_to(self.fi); self.playing = True; self.pause_b.config(text='Pause'); self.open_tick(force=True)

    def open_tick(self, force=False):
        if self.after_id: self.after_cancel(self.after_id); self.after_id = None
        if not self.frames or (not self.playing and not force): return
        i = min(self.fi, len(self.frames) - 1); self.oimg = ImageTk.PhotoImage(self.frames[i].resize((720, 405), Image.NEAREST)); self.oc.delete('all'); self.oc.create_image(0, 0, image=self.oimg, anchor='nw')
        self.ost.config(text=f'frame {i + 1} / {len(self.frames)}' + ('   (skipped to summary)' if i >= self.scene.T_sum else ''))
        if self.fi < len(self.frames) - 1: self.fi += 1; self.after_id = self.after(40, self.open_tick)
        else: self.playing = False; self.pause_b.config(text='Replay')

    # ------------------------------------------------------------------ plumbing
    def poll(self):
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == 'sim': self.sim_show(m[1], m[2])
                elif m[0] == 'scene':
                    s = m[1]; self.pull_l.config(text='Pull: ' + ',  '.join(f"{x['rarity'].title()} {x['row'].get('name')}" for x in s.pull))
                elif m[0] == 'prog': self.pb.config(value=100.0 * m[1] / m[2])
                elif m[0] == 'frames':
                    self.scene, self.frames = m[1], m[2]; self.pb.config(value=100); self.fi = 0; self.playing = True; self.pause_b.config(text='Pause'); self.ost.config(text='playing'); self.open_tick()
                elif m[0] == 'err': self.ost.config(text='error (see console)'); print(m[1])
        except queue.Empty: pass
        try: self.after(120, self.poll)
        except tk.TclError: pass

    def load_fields(self):
        r = self.row(); self.loading = True
        try:
            if not r:
                return
            self.idl.config(text=r['id'])
            for k, var in self.v.items(): var.set(r.get(k, ''))
            self.active.set(1 if str(r.get('active', '1')) in ('1', 'true', 'True') else 0)
            o = self.orow()
            for k, var in self.ov.items(): var.set(o.get(k, ''))
            for k, var in self.gv.items(): var.set(r.get(k, ''))
            for k, var in self.lv.items(): var.set(r.get(k, ''))
        finally: self.loading = False

    def refresh_views(self):
        r = self.row()
        if not r: return
        st = PL.state(r); a, z = None, None
        try: a, z = PL.parse_time(r.get('start')), PL.parse_time(r.get('end'))
        except ValueError as e: st = f'bad date: {e}'
        extra = ''
        if st == 'upcoming' and a: extra = f' (opens in {(a - datetime.datetime.now()).days} days)'
        if st == 'live' and z: extra = f' (ends in {(z - datetime.datetime.now()).days} days)'
        self.stl.config(text=st + extra); self.odds_view(); self.pool_fill()
        self.chk.delete('1.0', 'end'); res = PL.check(self.bundle(), [dict(x) for x in self.players.rows], [dict(x) for x in self.cards.rows])
        if not res: self.chk.insert('end', 'no problems', 'ok')
        for s, m in res: self.chk.insert('end', f'[{s}] {m}\n', s)
        self.wrapper()

    def refresh(self): self.fill(keep=True)
