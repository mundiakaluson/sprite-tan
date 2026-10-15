"""Base animations: the player's own movement set (walk, jog, falls, jump...), kept apart from the skill cards. Rows come from data/base_animations.csv;
an animation is "built" when its anim file exists in data/animations. Gait numbers (data/gaits.csv) are shown for the locomotion loops."""
import os
import tkinter as tk
from tkinter import ttk
import tables, looks  # looks puts sprites/ on the path
import custom_anims as C
from movewin import MovePanel


class BaseTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.t = tables.table('base_animations'); self.g = tables.table('gaits')
        pw = tables.Split(self); pw.pack(fill='both', expand=True)
        left = ttk.Frame(pw, padding=6); pw.add(left, weight=1)
        ttk.Label(left, text='Base animations', font=('TkDefaultFont', 11, 'bold')).pack(anchor='w')
        ttk.Label(left, text='How a player moves, falls and recovers. Separate from the skill cards.', foreground='#8a90a0').pack(anchor='w', pady=(0, 4))
        self.tv = ttk.Treeview(left, columns=('state', 'note'), show='tree headings', selectmode='browse', height=18)
        self.tv.heading('#0', text='animation'); self.tv.heading('state', text='state'); self.tv.heading('note', text='note')
        self.tv.column('#0', width=190); self.tv.column('state', width=70, anchor='center'); self.tv.column('note', width=230)
        self.tv.pack(fill='both', expand=True); self.tv.bind('<<TreeviewSelect>>', lambda e: self.pick())
        self.tv.tag_configure('todo', foreground='#8a90a0')
        self.count = ttk.Label(left, text=''); self.count.pack(anchor='w', pady=3)
        right = ttk.Frame(pw, padding=6); pw.add(right, weight=2)
        self.mp = MovePanel(right, S=8, simple=True); self.mp.pack()
        self.info = ttk.Label(right, text='', justify='left', wraplength=420); self.info.pack(anchor='w', pady=6)
        self.t.listeners.append(self.fill); self.g.listeners.append(self.pick)
        self.fill()

    def built(self, r):
        a = (r.get('anim') or '').strip(); return bool(a) and a in C.files()

    def fill(self):
        sel = self.tv.selection(); self.tv.delete(*self.tv.get_children()); groups = {}; done = 0
        for i, r in enumerate(self.t.rows):
            g = r.get('group', '')
            if g not in groups: groups[g] = self.tv.insert('', 'end', iid='g_' + g, text=g, open=True)
            ok = self.built(r); done += ok
            self.tv.insert(groups[g], 'end', iid=str(i), text=r.get('name', ''), values=('built' if ok else 'planned', r.get('note', '')), tags=() if ok else ('todo',))
        self.count.config(text=f'{done} of {len(self.t.rows)} built')
        if sel and self.tv.exists(sel[0]): self.tv.selection_set(sel[0])

    def pick(self):
        sel = self.tv.selection()
        if not sel or sel[0].startswith('g_'): return
        r = self.t.rows[int(sel[0])]
        if self.built(r):
            self.mp.set_anim(r['anim'], r['name']); extra = ''
            gr = next((x for x in self.g.rows if x.get('id') == r['anim']), None)
            if gr: extra = f"\nGait: cycle {gr['cycle_s']} s, ground speed {gr['ground_speed_px_s']} px/s at the authored rate; the game plays it at speed / {gr['ground_speed_px_s']} (rate {gr['min_rate']} to {gr['max_rate']})."
            self.info.config(text=f"{r['name']}  ({r['anim']}){extra}")
        else:
            self.mp.set_anim(None); self.info.config(text=f"{r['name']}: not built yet. {r.get('note', '')}")
