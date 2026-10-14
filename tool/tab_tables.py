import tkinter as tk
from tkinter import ttk
import tables


class TablesTab(ttk.Frame):
    """Any other CSV in data/ (packs, looks palette, styles, families...) in the same editable grid."""
    SKIP = {'players', 'cards', 'formations', 'formation_slots', 'players_invented_names'}

    def __init__(self, master):
        super().__init__(master)
        import os
        names = sorted(f[:-4] for f in os.listdir(tables.DATA) if f.endswith('.csv') and f[:-4] not in self.SKIP)
        bar = ttk.Frame(self); bar.pack(fill='x')
        ttk.Label(bar, text='Table').pack(side='left'); self.cb = ttk.Combobox(bar, values=names, state='readonly'); self.cb.pack(side='left', padx=4)
        self.cb.bind('<<ComboboxSelected>>', lambda e: self.show(self.cb.get())); self.body = ttk.Frame(self); self.body.pack(fill='both', expand=True)
        self.g = None
        if names: self.cb.set(names[0]); self.show(names[0])

    def show(self, name):
        if self.g: self.g.destroy()
        self.g = tables.Grid(self.body, tables.table(name), width_for=dict(note=300)); self.g.pack(fill='both', expand=True)
