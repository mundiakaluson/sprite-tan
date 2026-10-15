"""Game manager tool (name in data/project.csv).  Run from the repo root:  python tool/app.py
Tabs: Dashboard (start page) | Players | Cards | Packs | Formations | Animations | Base animations | Hair styles | Kits | Stadiums | Goal simulator | Ball studio | Other tables | Checks | Build | Sprite import.
All data is plain CSV in data/ (edit in Excel too: changes on disk are picked up automatically)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
from tkinter import ttk, messagebox
import tables


def main():
    root = tk.Tk(); root.title(tables.project() + ' - manager tool'); root.geometry('1360x820')
    try: ttk.Style().theme_use('clam')
    except tk.TclError: pass
    nb = ttk.Notebook(root); nb.pack(fill='both', expand=True)
    exp_btn = ttk.Button(root, text='Export to game')   # sits in the tab strip, top right, same look as the other buttons
    exp_btn.place(relx=1.0, x=-6, y=2, anchor='ne')
    ref_btn = ttk.Button(root, text='Refresh dashboard', command=lambda: getattr(built.get('Dashboard'), 'refresh', lambda: None)())
    ref_btn.place(relx=1.0, x=-124, y=2, anchor='ne')
    status = ttk.Label(root, text='Edits are written to data/*.csv when you press Save. Files changed in Excel reload automatically.', anchor='w'); status.pack(fill='x')
    from tab_dashboard import DashboardTab
    from tab_players import PlayersTab
    from tab_cards import CardsTab
    from tab_packs import PacksTab
    from tab_formations import FormationsTab
    from tab_anim import AnimTab
    from tab_base import BaseTab
    from tab_hair import HairTab
    from tab_kits import KitsTab
    from tab_stadiums import StadiumsTab
    from tab_goalsim import GoalSimTab
    from tab_balls import BallsTab
    from tab_tables import TablesTab
    from tab_check import CheckTab
    from tab_import import ImportTab
    from tab_build import BuildTab
    tabs = [('Dashboard', DashboardTab), ('Players', PlayersTab), ('Cards', CardsTab), ('Packs', PacksTab), ('Formations', FormationsTab), ('Animations', AnimTab), ('Base animations', BaseTab), ('Hair styles', HairTab), ('Kits', KitsTab), ('Stadiums', StadiumsTab), ('Goal simulator', GoalSimTab), ('Ball studio', BallsTab), ('Other tables', TablesTab), ('Checks', CheckTab), ('Build', BuildTab), ('Sprite import', ImportTab)]
    built = {}
    for name, cls in tabs:
        try:
            w = cls(nb); built[name] = w; nb.add(w, text=name)
        except Exception as e:   # one broken tab should not stop the tool
            import traceback; traceback.print_exc(); f = ttk.Frame(nb); ttk.Label(f, text=f'{name} failed to load: {e}').pack(padx=20, pady=20); nb.add(f, text=name)
    if 'Dashboard' in built: built['Dashboard'].attach(nb, built); nb.select(built['Dashboard'])
    nb.bind('<<NotebookTabChanged>>', lambda e: getattr(nb.nametowidget(nb.select()), 'refresh', lambda: None)())
    tables.watch_all(root, status=lambda m: status.config(text=m))

    import export_dialog
    def show_last():
        le = export_dialog.export_game.last_export(); status.config(text=f'Last export to game: {le[0]} ({le[1]})' if le else 'Not exported to game yet')
    def do_export():
        dirty = [t for t in tables._cache.values() if t.dirty]
        if dirty:
            a = messagebox.askyesnocancel('Export', 'Unsaved changes in: ' + ', '.join(t.name for t in dirty) + '\nSave them before exporting?')
            if a is None: return
            if a: [t.save() for t in dirty]
        export_dialog.open_dialog(root, show_last)
    exp_btn.config(command=do_export); show_last()

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
