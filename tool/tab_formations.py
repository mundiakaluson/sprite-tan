import tkinter as tk
from tkinter import ttk
import tables
from rules import *


class FormationsTab(ttk.Frame):
    """Formations table on the left, pitch on the right: drag dots to move slots, switch phase to see style offsets."""
    PW, PH = 300, 420

    def __init__(self, master):
        super().__init__(master)
        self.F = tables.table('formations'); self.S = tables.table('formation_slots'); self.St = tables.table('styles'); self.Fam = tables.table('formation_families')
        self.cur = None; self.drag = None; self.phase = tk.StringVar(value='BASE')
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw); pw.add(left, weight=3)
        top = ttk.PanedWindow(left, orient='vertical'); top.pack(fill='both', expand=True)
        self.gF = tables.Grid(top, self.F, choices=dict(family=['FOUR_BACK', 'THREE_BACK', 'FIVE_BACK']), new_row=self.new_formation, on_select=self.select,
                              width_for=dict(name=90, note=300))
        self.gS = tables.Grid(top, self.S, choices=dict(role=[r for r in ROLES if r != 'GK']), new_row=self.new_slot, width_for=dict(formation=80))
        top.add(self.gF, weight=1); top.add(self.gS, weight=1)
        side = ttk.Frame(pw, padding=6); pw.add(side, weight=1)
        r = ttk.Frame(side); r.pack(fill='x')
        for p in ['BASE'] + PHASES:
            ttk.Radiobutton(r, text=p, value=p, variable=self.phase, command=self.draw).pack(side='left')
        self.cv = tk.Canvas(side, width=self.PW + 20, height=self.PH + 20, bg='#3d8a45', highlightthickness=0); self.cv.pack(pady=4)
        self.cv.bind('<Button-1>', self.down); self.cv.bind('<B1-Motion>', self.move); self.cv.bind('<ButtonRelease-1>', self.up)
        self.info = ttk.Label(side, text='Pick a formation. Drag a dot to move that slot (BASE view).', wraplength=300, justify='left'); self.info.pack(anchor='w')
        self.settings = ttk.Label(side, text='', justify='left'); self.settings.pack(anchor='w', pady=4)
        for t in (self.F, self.S, self.St, self.Fam): t.listeners.append(self.draw)

    def new_formation(self, t):
        n = max([to_int(r['id'][1:], 0) for r in t.rows if r['id'][:1] == 'F'] + [0]) + 1
        r = {c: '' for c in t.cols}; r.update(id=f'F{n:02d}', name='New 4-4-2', family='FOUR_BACK', note=''); return r

    def new_slot(self, t):
        r = {c: '' for c in t.cols}
        r.update(formation=self.cur or '', slot=str(len([s for s in t.rows if s['formation'] == self.cur]) + 1), role='CM', style='box_to_box', x='50', y='50'); return r

    def select(self, idx):
        self.cur = self.F.rows[idx[0]]['id'] if idx else None
        self.gS.filter.set(self.cur or ''); self.draw()

    def slots(self):
        return [(i, s) for i, s in enumerate(self.S.rows) if s['formation'] == self.cur]

    def offs(self, style, ph):
        for r in self.St.rows:
            if r['style'] == style:
                k = ph.lower()
                return float(r.get(k + '_dx') or 0), float(r.get(k + '_dy') or 0)
        return 0.0, 0.0

    def xy(self, x, y):   # pitch coords (0-100, own goal at y=0 -> bottom) to canvas
        return 10 + x / 100 * self.PW, 10 + (1 - y / 100) * self.PH

    def draw(self):
        c = self.cv; c.delete('all'); W, H = self.PW, self.PH
        c.create_rectangle(10, 10, 10 + W, 10 + H, outline='white'); c.create_line(10, 10 + H / 2, 10 + W, 10 + H / 2, fill='white')
        c.create_oval(10 + W / 2 - 30, 10 + H / 2 - 30, 10 + W / 2 + 30, 10 + H / 2 + 30, outline='white')
        for y0 in (10, 10 + H - 64): c.create_rectangle(10 + W / 2 - 60, y0, 10 + W / 2 + 60, y0 + 64, outline='white')
        if not self.cur: return
        fam = next((r for r in self.F.rows if r['id'] == self.cur), None)
        sl = self.slots()
        x, y = self.xy(50, 4); c.create_oval(x - 7, y - 7, x + 7, y + 7, fill='#f0c040', outline='black'); c.create_text(x, y - 14, text='GK', fill='white')
        for i, s in sl:
            bx, by = to_int(s['x'], 50), to_int(s['y'], 50)
            if self.phase.get() != 'BASE':
                dx, dy = self.offs(s['style'], self.phase.get()); bx, by = max(0, min(100, bx + dx)), max(0, min(100, by + dy))
            px, py = self.xy(bx, by); c.create_oval(px - 8, py - 8, px + 8, py + 8, fill='#d63240', outline='white', tags=f's{i}')
            c.create_text(px, py, text=s['slot'], fill='white', tags=f's{i}'); c.create_text(px, py + 15, text=s['role'], fill='white', font=('TkDefaultFont', 7))
        if fam:
            d = next((r for r in self.Fam.rows if r['family'] == fam['family']), {})
            vals = {k: (fam.get(k) or d.get(k) or '-') + ('' if fam.get(k) else ' (family)') for k in FAMILY_KEYS}
            self.settings.config(text='\n'.join(f'{k:12} {v}' for k, v in vals.items()))
            self.info.config(text=f"{fam['name']}  {fam['note']}  [{len(sl)}/10 slots]")

    def down(self, ev):
        if self.phase.get() != 'BASE': return
        for it in self.cv.find_overlapping(ev.x, ev.y, ev.x, ev.y):
            for t in self.cv.gettags(it):
                if t.startswith('s'): self.drag = int(t[1:]); self.S.snapshot(); return

    def move(self, ev):
        if self.drag is None: return
        x = round(max(0, min(100, (ev.x - 10) / self.PW * 100))); y = round(max(0, min(100, (1 - (ev.y - 10) / self.PH) * 100)))
        r = self.S.rows[self.drag]; r['x'], r['y'] = str(x), str(y); self.S.dirty = True; self.draw()

    def up(self, ev):
        if self.drag is not None: self.drag = None; self.S.notify()
