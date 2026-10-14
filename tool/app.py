"""Pixel Football manager tool.  Run from the repo root:  python tool/app.py
Tabs: Players | Cards | Formations | Animations | Hair styles | Kits | Other tables | Checks | Build | Sprite import.
All data is plain CSV in data/ (edit in Excel too: changes on disk are picked up automatically)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from tkinter import ttk, messagebox
import tables


def main():
    root = tk.Tk(); root.title('Pixel Football - manager tool'); root.geometry('1360x820')
    try: ttk.Style().theme_use('clam')
    except tk.TclError: pass
    nb = ttk.Notebook(root); nb.pack(fill='both', expand=True)
    status = ttk.Label(root, text='Edits are written to data/*.csv when you press Save. Files changed in Excel reload automatically.', anchor='w'); status.pack(fill='x')
    from tab_players import PlayersTab
    from tab_cards import CardsTab
    from tab_formations import FormationsTab
    from tab_anim import AnimTab
    from tab_hair import HairTab
    from tab_kits import KitsTab
    from tab_tables import TablesTab
    from tab_check import CheckTab
    from tab_import import ImportTab
    from tab_build import BuildTab
    tabs = [('Players', PlayersTab), ('Cards', CardsTab), ('Formations', FormationsTab), ('Animations', AnimTab), ('Hair styles', HairTab), ('Kits', KitsTab), ('Other tables', TablesTab), ('Checks', CheckTab), ('Build', BuildTab), ('Sprite import', ImportTab)]
    built = {}
    for name, cls in tabs:
        try:
            w = cls(nb); built[name] = w; nb.add(w, text=name)
        except Exception as e:   # one broken tab should not stop the tool
            import traceback; traceback.print_exc(); f = ttk.Frame(nb); ttk.Label(f, text=f'{name} failed to load: {e}').pack(padx=20, pady=20); nb.add(f, text=name)
    nb.bind('<<NotebookTabChanged>>', lambda e: getattr(nb.nametowidget(nb.select()), 'refresh', lambda: None)())
    tables.watch_all(root, status=lambda m: status.config(text=m))

    def close():
        dirty = [t.name for t in tables._cache.values() if t.dirty]
        a = built.get('Animations')
        if a is not None and getattr(a, 'dirty', False): dirty.append('animation')
        if dirty and not messagebox.askyesno('Quit', 'Unsaved changes in: ' + ', '.join(dirty) + '\nQuit anyway?'): return
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', close)
    root.mainloop()


if __name__ == '__main__':
    main()
