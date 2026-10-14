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

PREFIX = dict(SHOT='SH', PASS='PS', DRIBBLE='DR', DEFEND='DF', SUPPORT='SP', KEEPER='GK', TITAN='TT')
# Illustrated emblems exist for SH01-SH30. Everything else gets a placeholder by category until its own emblem is drawn.
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
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        ch = dict(cat=CARD_CATS, rarity=RARITY, timing=TIMING, kind=KIND)
        self.grid = tables.Grid(pw, self.t, choices=ch, new_row=new_card, on_select=self.select, width_for=dict(name=150, description=320, stats=90))
        pw.add(self.grid)
        side = ttk.Frame(pw, padding=6, width=330); side.pack_propagate(False); pw.add(side)
        self.cv = tk.Canvas(side, width=300, height=400, bg='#1e1f2a', highlightthickness=0); self.cv.pack()
        r = ttk.Frame(side); r.pack(fill='x', pady=3)
        ttk.Combobox(r, values=['ready', 'cooldown', 'unavailable'], textvariable=self.state, state='readonly', width=11).pack(side='left')
        self.state.trace_add('write', lambda *_: self.draw())
        ttk.Scale(r, from_=0, to=1, variable=self.cool, command=lambda e: self.draw()).pack(side='left', fill='x', expand=True, padx=4)
        self.tip = tk.Canvas(side, width=300, height=190, bg='#1e1f2a', highlightthickness=0); self.tip.pack(pady=2)
        ttk.Button(side, text='Preview a hand of 8', command=self.hand).pack(fill='x', pady=2)
        ttk.Button(side, text='Export all card faces + tooltips (PNG)', command=self.export_all).pack(fill='x')
        self.note = ttk.Label(side, text='', wraplength=300, justify='left', foreground='#9aa0ae'); self.note.pack(anchor='w', pady=4)
        self.t.listeners.append(self.draw)

    def select(self, idx):
        self.i = idx[0] if idx else None; self.draw()

    def draw(self):
        if self.i is None or self.i >= len(self.t.rows): return
        c = self.t.rows[self.i]
        try:
            self._ph = ImageTk.PhotoImage(card_face(c, self.state.get(), float(self.cool.get()), 4)); self.cv.delete('all'); self.cv.create_image(150, 200, image=self._ph)
            self._tp = ImageTk.PhotoImage(tooltip(c, 2)); self.tip.delete('all'); self.tip.create_image(150, 95, image=self._tp)
            self.note.config(text='' if has_art(c['id']) else 'Placeholder emblem (category default). This card has no illustrated emblem yet.')
        except Exception as e:
            self.note.config(text=f'card error: {e}')

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
