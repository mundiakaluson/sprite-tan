"""Cards tab. The card face is the pixel design from cards/cardlib2.py (slot count, category, illustrated emblem, name, success / risk / cooldown).
The description is NOT on the card: it shows in the hover tooltip (cardlib2.popup)."""
import os, random, sys, tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import tables
from rules import *
from tab_players import next_id
import looks  # puts sprites/ on the path

CARDS_DIR = os.path.join(tables.ROOT, 'cards')
if CARDS_DIR not in sys.path:
    sys.path.insert(0, CARDS_DIR)
import cardlib2 as CL  # noqa: E402
import recipes  # noqa: E402
recipes.install(CL.EMB)   # illustrated emblems for every card in cards.csv

PREFIX = dict(SHOT='SH', PASS='PS', DRIBBLE='DR', DEFEND='DF', SUPPORT='SP', KEEPER='GK', TITAN='TT')
# All 200 shipped cards have an illustrated emblem (SH01-SH30 in cardlib2, the rest in recipes.py). A new card gets a category placeholder until you draw one.
PLACEHOLDER = dict(PASS=CL.R_two_arrows, DRIBBLE=CL.R_toe, DEFEND=CL.EXTRA['shield'], SUPPORT=CL.EXTRA['flex'], KEEPER=CL.EXTRA['glove'], TITAN=CL.R_bolt, SHOT=CL.R_impact)


def row(c):
    """cards.csv row (strings) -> dict the card renderer expects."""
    i = lambda k, d=0: to_int(c.get(k), d)
    return dict(id=c.get('id', ''), name=c.get('name', ''), cat=c.get('cat', 'SHOT'), slots=i('slots', 1), succ=i('succ'), risk=i('risk'), cd=i('cd'),
                desc=c.get('description', ''), rarity=c.get('rarity', ''))


def has_art(cid):
    return cid in CL.EMB


def art(c):
    pal = CL.CAT.get(c['cat'], CL.CAT['SHOT'])
    fn = CL.EMB.get(c['id']) or PLACEHOLDER.get(c['cat'], CL.R_impact)
    return fn(pal)


def card_face(c, state='ready', t=0.0, scale=4):
    r = row(c); im = CL.card(r, art(r), state, t)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def tooltip(c, scale=4):
    im = CL.popup(row(c)); return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def new_card(t):
    r = {c: '' for c in t.cols}
    r.update(id=next_id(t, 'XX', 2), name='New Card', cat='SHOT', rarity='COMMON', slots='1', succ='70', risk='10', cd='4',
             timing='ENGAGEMENT', kind='ACTION', stats='SHO', description='Describe what it does.')
    return r


class CardsTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('cards'); self.i = None; self.state = tk.StringVar(value='ready'); self.cool = tk.DoubleVar(value=0.5)
        self.loading = False; self.w = {}
        self.toolbar()
        pw = tables.Split(self); pw.pack(side='left', fill='both', expand=True)
        ch = dict(cat=CARD_CATS, rarity=RARITY, timing=TIMING, kind=KIND)
        self.grid = tables.Grid(pw, self.t, choices=ch, new_row=new_card, on_select=self.select, width_for=dict(name=150, description=320, stats=90), editable=False)
        pw.add(self.grid)
        side = ttk.Frame(pw, padding=6, width=470); side.pack_propagate(False); pw.add(side)
        top = ttk.Frame(side); top.pack(fill='x')
        self.cv = tk.Canvas(top, width=140, height=190, bg='#1e1f2a', highlightthickness=0); self.cv.pack(side='left')
        self.tip = tk.Canvas(top, width=300, height=190, bg='#1e1f2a', highlightthickness=0); self.tip.pack(side='left', padx=(4, 0))
        r = ttk.Frame(side); r.pack(fill='x', pady=3)
        ttk.Combobox(r, values=['ready', 'cooldown', 'unavailable'], textvariable=self.state, state='readonly', width=11).pack(side='left')
        self.state.trace_add('write', lambda *_: self.draw())
        ttk.Label(r, text='served').pack(side='left', padx=(6, 0))
        ttk.Scale(r, from_=0, to=1, variable=self.cool, command=lambda e: self.draw()).pack(side='left', fill='x', expand=True, padx=4)
        import movewin
        self.mp = movewin.MovePanel(side, S=7); self.mp.pack(pady=2)
        import titanwin
        self.tw = titanwin.TitanPanel(side)       # Titan cards play their full cinematic here instead of the move panel
        self.edit_btn = ttk.Button(side, text='✎ Edit this move (Animations tab)', command=self.edit_move); self.edit_btn.pack(fill='x', pady=2)
        ttk.Button(side, text='Preview a hand of 8', command=self.hand).pack(fill='x', pady=2)
        ttk.Button(side, text='Export all card faces + tooltips (PNG)', command=self.export_all).pack(fill='x')
        self.note = ttk.Label(side, text='', wraplength=300, justify='left', foreground='#9aa0ae'); self.note.pack(anchor='w', pady=4)
        self.t.listeners.append(self.draw); self.t.listeners.append(self.load_form)

    # ------------------------------------------------------------------ left toolbar: sort, show, edit the selected card(s)
    SORTS = [('id', 'id'), ('name', 'name'), ('category', 'cat'), ('rarity', 'rarity'), ('slots', 'slots'), ('success', 'succ'), ('risk', 'risk'), ('cooldown', 'cd')]

    def toolbar(self):
        tb = ttk.Frame(self, padding=6, width=262); tb.pack(side='left', fill='y'); tb.pack_propagate(False)
        sf = ttk.LabelFrame(tb, text='Sort', padding=4); sf.pack(fill='x')
        self.sortv = tk.StringVar(value='id'); self.desc = tk.IntVar(value=0)
        cb = ttk.Combobox(sf, values=[n for n, _ in self.SORTS], textvariable=self.sortv, state='readonly', width=11); cb.pack(side='left'); cb.bind('<<ComboboxSelected>>', lambda e: self.apply_sort())
        ttk.Checkbutton(sf, text='high to low', variable=self.desc, command=self.apply_sort).pack(side='left', padx=6)
        ff = ttk.LabelFrame(tb, text='Show', padding=4); ff.pack(fill='x', pady=4)
        self.flt = {}
        for n, (k, vals) in enumerate((('cat', CARD_CATS), ('rarity', RARITY), ('timing', TIMING), ('kind', KIND))):
            ttk.Label(ff, text={'cat': 'category'}.get(k, k)).grid(row=n, column=0, sticky='w')
            v = tk.StringVar(value='all'); self.flt[k] = v
            c = ttk.Combobox(ff, values=['all'] + vals, textvariable=v, state='readonly', width=14); c.grid(row=n, column=1, sticky='ew', pady=1); c.bind('<<ComboboxSelected>>', lambda e: self.apply_filter())
        ttk.Button(ff, text='Show all', command=self.clear_filter).grid(row=4, column=0, columnspan=2, sticky='ew', pady=(3, 0))
        ef = ttk.LabelFrame(tb, text='Selected card', padding=4); ef.pack(fill='x')
        self.sel_lbl = ttk.Label(ef, text='nothing selected', foreground='#8a90a0'); self.sel_lbl.grid(row=0, column=0, columnspan=2, sticky='w')
        fields = (('name', 'entry', None), ('cat', 'combo', CARD_CATS), ('rarity', 'combo', RARITY), ('timing', 'combo', TIMING), ('kind', 'combo', KIND), ('stats', 'entry', None), ('engage', 'entry', None), ('effect', 'entry', None),
                  ('slots', 'spin', (1, 12)), ('succ', 'spin', (1, 100)), ('risk', 'spin', (0, 100)), ('cd', 'spin', (0, 99)),
                  ('ball_speed', 'spin', (0, 10)), ('ball_arc', 'spin', (0, 10)), ('ball_curve', 'spin', (-5, 5)),
                  ('move_mult', 'fspin', (0, 3)), ('anim_rate', 'fspin', (0.4, 2)), ('travel', 'fspin', (0, 2)), ('reach', 'fspin', (0, 10)), ('steer', 'fspin', (0, 10)), ('lock', 'fspin', (0, 10)))
        lab = dict(move_mult='move speed x', anim_rate='anim rate x', travel='travel x', reach='reach', steer='steer', lock='lock (s)', cat='category', succ='success', cd='cooldown', ball_speed='ball speed', ball_arc='ball arc', ball_curve='ball curve')
        for n, (k, kind, arg) in enumerate(fields, 1):
            ttk.Label(ef, text=lab.get(k, k)).grid(row=n, column=0, sticky='w')
            if kind == 'combo':
                w = ttk.Combobox(ef, values=arg, state='readonly', width=14); w.bind('<<ComboboxSelected>>', lambda e, k=k, w=w: self.put(k, w.get()))
            elif kind == 'entry':
                w = ttk.Entry(ef, width=17); w.bind('<Return>', lambda e, k=k, w=w: self.put(k, w.get())); w.bind('<FocusOut>', lambda e, k=k, w=w: self.put(k, w.get()))
            elif kind == 'fspin':
                w = ttk.Spinbox(ef, from_=arg[0], to=arg[1], increment=0.1, width=6, command=lambda k=k: self.put_float(k)); w.bind('<Return>', lambda e, k=k: self.put_float(k)); w.bind('<FocusOut>', lambda e, k=k: self.put_float(k))
            else:
                w = ttk.Spinbox(ef, from_=arg[0], to=arg[1], width=6, command=lambda k=k: self.put_num(k)); w.bind('<Return>', lambda e, k=k: self.put_num(k)); w.bind('<FocusOut>', lambda e, k=k: self.put_num(k))
            w.grid(row=n, column=1, sticky='w', pady=1); self.w[k] = w
        ttk.Label(ef, text='description').grid(row=len(fields) + 1, column=0, sticky='nw')
        self.desc_w = tk.Text(ef, width=17, height=5, wrap='word', font=('TkDefaultFont', 9)); self.desc_w.grid(row=len(fields) + 1, column=1, sticky='w', pady=1)
        self.desc_w.bind('<FocusOut>', lambda e: self.put('description', self.desc_w.get('1.0', 'end').strip()))
        self.rng = dict((k, a) for k, _, a in fields if _ in ('spin', 'fspin'))

    def apply_sort(self):
        col = dict(self.SORTS)[self.sortv.get()]; self.grid.sort_col = col; self.grid.sort_rev = bool(self.desc.get()); self.grid.fill()

    def apply_filter(self):
        f = {k: v.get() for k, v in self.flt.items() if v.get() != 'all'}
        self.grid.extra_filter = (lambda r: all(r.get(k) == v for k, v in f.items())) if f else None; self.grid.fill()

    def clear_filter(self):
        for v in self.flt.values(): v.set('all')
        self.apply_filter()

    def idxs(self):
        return [i for i in self.grid.selected_indices() if i < len(self.t.rows)]

    def put(self, k, v):
        if self.loading: return
        ix = self.idxs()
        if not ix: return
        if all(self.t.rows[i].get(k, '') == v for i in ix): return
        self.t.snapshot()
        for i in ix: self.t.set(i, k, v, snap=False)

    def put_num(self, k):
        if self.loading: return
        v = to_int(self.w[k].get()); lo, hi = self.rng[k]
        if v is None: self.load_form(); return
        self.put(k, str(max(lo, min(hi, v))))

    def put_float(self, k):
        if self.loading: return
        t = self.w[k].get().strip(); lo, hi = self.rng[k]
        if t == '': self.put(k, ''); return
        try: v = max(lo, min(hi, float(t)))
        except ValueError: self.load_form(); return
        self.put(k, '%g' % round(v, 2))

    def load_form(self):
        ix = self.idxs(); self.loading = True
        try:
            if not ix:
                self.sel_lbl.config(text='nothing selected'); return
            r = self.t.rows[ix[0]]
            self.sel_lbl.config(text=f"{r['id']}  {r['name']}" if len(ix) == 1 else f'{len(ix)} cards selected: edits apply to all')
            for k, w in self.w.items():
                v = r.get(k, '')
                if isinstance(w, ttk.Combobox): w.set(v)
                elif w.get() != v: w.delete(0, 'end'); w.insert(0, v)
            d = r.get('description', '')
            if self.desc_w.get('1.0', 'end').strip() != d: self.desc_w.delete('1.0', 'end'); self.desc_w.insert('1.0', d)
        finally:
            self.loading = False

    def select(self, idx):
        self.i = idx[0] if idx else None; self.load_form(); self.draw()

    def draw(self):
        if self.i is None or self.i >= len(self.t.rows): return
        c = self.t.rows[self.i]
        try:
            self._ph = ImageTk.PhotoImage(card_face(c, self.state.get(), float(self.cool.get()), 2)); self.cv.delete('all'); self.cv.create_image(70, 95, image=self._ph)
            self._tp = ImageTk.PhotoImage(tooltip(c, 2)); self.tip.delete('all'); self.tip.create_image(150, 95, image=self._tp); self.show_motion(c)
            self.note.config(text='' if has_art(c['id']) else 'Placeholder emblem (category default). Add a recipe for this id in cards/recipes.py.')
        except Exception as e:
            self.note.config(text=f'card error: {e}')

    def show_motion(self, c):
        if getattr(self, '_mp_id', None) == c['id']: return
        self._mp_id = c['id']
        if c['id'].startswith('TT'):
            self.mp.pack_forget(); self.tw.pack(pady=2, before=self.edit_btn); self.tw.load(c['id'])
        else:
            self.tw.pack_forget(); self.mp.pack(pady=2, before=self.edit_btn); self.mp.set_card(c)

    def edit_move(self):
        if self.i is None: return
        import movewin
        name = movewin.find(self.t.rows[self.i]['id'])
        if not name: messagebox.showinfo('Move', 'No animation for this card yet.'); return
        nb = self.master
        for w in nb.winfo_children():
            if hasattr(w, 'open') and hasattr(w, 'plist'):
                nb.select(w); w.refresh_list(); w.open(name); return

    def hand(self):
        rows = random.sample(self.t.rows, min(8, len(self.t.rows))); win = tk.Toplevel(self); win.title('Hand preview (cooldown and unavailable states mixed in)')
        W = Image.new('RGBA', (8 * 64 * 2 + 9 * 6, 90 * 2 + 12), (24, 26, 38, 255))
        for n, c in enumerate(rows):
            st = ('ready', 'ready', 'cooldown', 'ready', 'unavailable', 'ready', 'cooldown', 'ready')[n]
            f = card_face(c, st, 0.4, 2); W.alpha_composite(f, (6 + n * (128 + 6), 6))
        self._hand = ImageTk.PhotoImage(W); tk.Label(win, image=self._hand, bd=0).pack()

    def export_all(self):
        out = os.path.join(tables.ROOT, 'export', 'cards'); os.makedirs(out, exist_ok=True)
        for c in self.t.rows:
            card_face(c, 'ready', 0, 4).save(os.path.join(out, c['id'] + '.png')); tooltip(c, 4).save(os.path.join(out, c['id'] + '_tooltip.png'))
        messagebox.showinfo('Export', f'Wrote {len(self.t.rows)} cards and tooltips to {out}')
