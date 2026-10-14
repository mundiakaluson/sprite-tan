import tkinter as tk
from tkinter import ttk
import tables, validate


class CheckTab(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        bar = ttk.Frame(self); bar.pack(fill='x')
        ttk.Button(bar, text='Run checks', command=self.run).pack(side='left'); self.lbl = ttk.Label(bar, text=''); self.lbl.pack(side='left', padx=8)
        self.tv = ttk.Treeview(self, columns=('sev', 'table', 'id', 'msg'), show='headings')
        for c, w in (('sev', 70), ('table', 120), ('id', 90), ('msg', 700)): self.tv.heading(c, text=c); self.tv.column(c, width=w, stretch=(c == 'msg'))
        self.tv.tag_configure('error', foreground='#d84a4a'); self.tv.tag_configure('warn', foreground='#c89a20')
        self.tv.pack(fill='both', expand=True); self.run()

    def refresh(self):
        self.run()

    def run(self):
        self.tv.delete(*self.tv.get_children())
        res = validate.run()
        for sev, tb, rid, msg in sorted(res, key=lambda r: (r[0] != 'error', r[1], r[2])): self.tv.insert('', 'end', values=(sev, tb, rid, msg), tags=(sev,))
        e = sum(1 for r in res if r[0] == 'error'); w = len(res) - e
        self.lbl.config(text='All good' if not res else f'{e} errors, {w} warnings')
