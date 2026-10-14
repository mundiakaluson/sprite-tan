import os, time, tkinter as tk
from tkinter import ttk, messagebox
import tables, looks, validate
from rules import *

ROOT = tables.ROOT
STATUS = ['todo', 'doing', 'done']
ICON = dict(todo='[ ]', doing='[~]', done='[x]')


def ago(path):
    try:
        s = time.time() - os.path.getmtime(path)
    except OSError:
        return 'never'
    return 'just now' if s < 60 else f'{s / 60:.0f} min ago' if s < 3600 else f'{s / 3600:.0f} h ago' if s < 86400 else f'{s / 86400:.0f} days ago'


def newest(folder):
    best = 0; n = 0
    for dp, _, fs in os.walk(folder):
        for f in fs: n += 1; best = max(best, os.path.getmtime(os.path.join(dp, f)))
    return n, best


class DashboardTab(ttk.Frame):
    """Start page: project progress, live numbers from the data, and a command panel."""

    def __init__(self, master):
        super().__init__(master)
        self.app = None
        top = ttk.Frame(self, padding=(10, 8)); top.pack(fill='x')
        ttk.Label(top, text=tables.project(), font=('TkDefaultFont', 16, 'bold')).pack(side='left')
        self.sub = ttk.Label(top, text='', foreground='#8a90a0'); self.sub.pack(side='left', padx=12)
        ttk.Button(top, text='Refresh', command=self.refresh).pack(side='right')
        body = ttk.Frame(self, padding=(10, 0)); body.pack(fill='both', expand=True)
        left = ttk.Frame(body); left.pack(side='left', fill='both', expand=True)
        right = ttk.Frame(body, width=330); right.pack(side='right', fill='y', padx=(12, 0)); right.pack_propagate(False)

        # numbers
        self.tiles = ttk.Frame(left); self.tiles.pack(fill='x')
        self.bars = ttk.LabelFrame(left, text='Squad and deck', padding=6); self.bars.pack(fill='x', pady=8)
        self.cv_r = tk.Canvas(self.bars, height=30, highlightthickness=0); self.cv_r.pack(fill='x')
        self.lb_r = ttk.Label(self.bars, text=''); self.lb_r.pack(anchor='w')
        self.cv_c = tk.Canvas(self.bars, height=30, highlightthickness=0); self.cv_c.pack(fill='x', pady=(6, 0))
        self.lb_c = ttk.Label(self.bars, text=''); self.lb_c.pack(anchor='w')

        # roadmap
        rf = ttk.LabelFrame(left, text='Roadmap  (double-click a row to change its status)', padding=6); rf.pack(fill='both', expand=True)
        pr = ttk.Frame(rf); pr.pack(fill='x')
        self.pbar = ttk.Progressbar(pr, maximum=100); self.pbar.pack(side='left', fill='x', expand=True); self.plbl = ttk.Label(pr, text='', width=16); self.plbl.pack(side='left', padx=6)
        self.tv = ttk.Treeview(rf, columns=('st', 'stage', 'item', 'note'), show='headings', height=12, selectmode='browse')
        for c, w, st in (('st', 40, False), ('stage', 70, False), ('item', 440, True), ('note', 160, True)): self.tv.heading(c, text=c if c != 'st' else ''); self.tv.column(c, width=w, stretch=st)
        self.tv.tag_configure('done', foreground='#7a8090'); self.tv.tag_configure('doing', foreground='#e0b030'); self.tv.tag_configure('todo', foreground='#1c1f2a')
        self.tv.pack(fill='both', expand=True, pady=4); self.tv.bind('<Double-1>', self.cycle)

        # commands
        cp = ttk.LabelFrame(right, text='Commands', padding=8); cp.pack(fill='x')
        def group(title, items):
            ttk.Label(cp, text=title, foreground='#8a90a0').pack(anchor='w', pady=(6, 1))
            for t, fn in items: ttk.Button(cp, text=t, command=fn).pack(fill='x', pady=1)
        group('Data', [('Save all edits', self.save_all), ('Reload everything from disk', self.reload_all), ('Run data checks', self.checks)])
        group('Build  (opens the Build tab)', [('Self-test', lambda: self.build(0)), ('Rebuild body sheets and skins', lambda: self.build(1)), ('Rebuild hair layers', lambda: self.build(2))])
        group('Export for the game', [('Player look atlases', lambda: self.call('Players', 'export_all')), ('Player cards + shimmer strips', lambda: self.call('Players', 'export_cards')), ('Skill card faces + tooltips', lambda: self.call('Cards', 'export_all'))])
        group('Open', [('Data folder', lambda: tables.open_external(os.path.join(ROOT, 'data'))), ('Export folder', self.open_export), ('players.csv in Excel', lambda: tables.open_external(os.path.join(ROOT, 'data', 'players.csv')))])
        group('Go to', [])
        gf = ttk.Frame(cp); gf.pack(fill='x'); self.gof = gf
        lf = ttk.LabelFrame(right, text='Activity', padding=4); lf.pack(fill='both', expand=True, pady=(8, 0))
        self.log = tk.Text(lf, height=4, wrap='word', state='disabled', bg='#12141c', fg='#c8ccd8', font=('TkDefaultFont', 9)); self.log.pack(fill='both', expand=True)
        self.t = tables.table('progress'); self.refresh()

    # ------------------------------------------------------------------ wiring
    def attach(self, nb, built):
        self.nb, self.built = nb, built
        for k, n in enumerate(('Players', 'Cards', 'Formations', 'Animations', 'Hair styles', 'Kits')):
            if n in built: ttk.Button(self.gof, text=n, width=9, command=lambda n=n: self.go(n)).grid(row=k // 3, column=k % 3, padx=1, pady=1, sticky='ew')
        for c in range(3): self.gof.columnconfigure(c, weight=1)

    def go(self, name):
        w = self.built.get(name)
        if w is not None: self.nb.select(w)

    def call(self, tab, method):
        w = self.built.get(tab)
        if w is None: return
        self.note(f'{tab}: {method}')
        getattr(w, method)(); self.refresh()

    def build(self, i):
        from tab_build import JOBS
        w = self.built.get('Build')
        if w is None: return
        self.go('Build'); t, s, c, _ = JOBS[i]; w.start([(t, s, c)]); self.note(f'started: {t}')

    def note(self, s):
        self.log.config(state='normal'); self.log.insert('end', time.strftime('%H:%M  ') + s + '\n'); self.log.see('end'); self.log.config(state='disabled')

    def save_all(self):
        n = [t.name for t in tables._cache.values() if t.dirty]
        for t in tables._cache.values():
            if t.dirty: t.save()
        self.note('saved: ' + ', '.join(n) if n else 'nothing to save'); self.refresh()

    def reload_all(self):
        dirty = [t.name for t in tables._cache.values() if t.dirty]
        if dirty and not messagebox.askyesno('Reload', 'Unsaved edits in ' + ', '.join(dirty) + ' will be lost. Reload anyway?'): return
        for t in tables._cache.values(): t.load()
        self.note('reloaded all tables'); self.refresh()

    def checks(self):
        r = validate.run(); e = sum(1 for x in r if x[0] == 'error')
        self.note(f'checks: {e} errors, {len(r) - e} warnings'); self.go('Checks'); self.refresh()

    def open_export(self):
        p = os.path.join(ROOT, 'export'); os.makedirs(p, exist_ok=True); tables.open_external(p)

    def cycle(self, e):
        iid = self.tv.identify_row(e.y)
        if not iid: return
        i = int(iid); st = self.t.rows[i]['status']; nxt = STATUS[(STATUS.index(st) + 1) % 3] if st in STATUS else 'todo'
        self.t.set(i, 'status', nxt); self.t.save(); self.refresh()

    # ------------------------------------------------------------------ numbers
    def tile(self, col, title, big, small=''):
        f = ttk.LabelFrame(self.tiles, text=title, padding=(8, 2)); f.grid(row=0, column=col, sticky='nsew', padx=(0, 6)); self.tiles.columnconfigure(col, weight=1)
        ttk.Label(f, text=big, font=('TkDefaultFont', 18, 'bold')).pack(anchor='w'); ttk.Label(f, text=small, foreground='#8a90a0').pack(anchor='w')

    def stack(self, cv, parts, colours):
        cv.delete('all'); cv.update_idletasks(); W = max(cv.winfo_width(), 300); tot = sum(v for _, v in parts) or 1; x = 0
        for k, v in parts:
            w = W * v / tot
            if v: cv.create_rectangle(x, 4, x + w, 26, fill=colours[k], outline=''); x += w
        return ', '.join(f'{k.title()} {v}' for k, v in parts)

    def refresh(self):
        P = tables.table('players').rows; C = tables.table('cards').rows
        res = validate.run(); errs = sum(1 for r in res if r[0] == 'error'); warns = len(res) - errs
        try:
            import tab_cards; art = sum(1 for c in C if tab_cards.has_art(c['id']))
        except Exception:
            art = 0
        spec = sum(1 for p in P if p.get('special') == '1'); an = looks.anims(); custom = sum(1 for a in an.values() if a.get('custom'))
        for w in self.tiles.winfo_children(): w.destroy()
        self.tile(0, 'Players', str(len(P)), f'{spec} special')
        self.tile(1, 'Skill cards', str(len(C)), f'{art} with emblems')
        self.tile(2, 'Formations', str(len(tables.table('formations').rows)), '')
        self.tile(3, 'Animations', str(len(an)), f'{custom} custom')
        self.tile(4, 'Hair / kits', f'{len(looks.hair_styles())} / {len(looks.kit_ids())}', 'styles / kits')
        self.tile(5, 'Data checks', 'OK' if not res else f'{errs} err', f'{warns} warnings')
        self.lb_r.config(text=self.stack(self.cv_r, [(r, sum(1 for p in P if p['rarity'] == r)) for r in RARITY], RARITY_COL))
        self.lb_c.config(text=self.stack(self.cv_c, [(k, sum(1 for c in C if c['cat'] == k)) for k in CARD_CATS], CAT_COL))
        # roadmap
        self.tv.delete(*self.tv.get_children()); done = 0
        for i, r in enumerate(self.t.rows):
            st = r.get('status', 'todo'); done += st == 'done'
            self.tv.insert('', 'end', iid=str(i), values=(ICON.get(st, '[ ]'), r['stage'], r['item'], r.get('note', '')), tags=(st,))
        n = len(self.t.rows) or 1; self.pbar['value'] = 100 * done / n; self.plbl.config(text=f'{done} of {len(self.t.rows)} done')
        # freshness
        out = os.path.join(looks.OUT, 'run_uv_sheet.png'); hair = os.path.join(looks.OUT, 'hair')
        ne, newest_e = newest(os.path.join(ROOT, 'export')); dp = os.path.join(ROOT, 'data', 'players.csv')
        stale = ' (players.csv is newer than the last export)' if ne and os.path.exists(dp) and os.path.getmtime(dp) > newest_e else ''
        dirty = [t.name for t in tables._cache.values() if t.dirty]
        self.sub.config(text=f"body sheets built {ago(out)}  |  hair layers {ago(hair)}  |  exports: {ne} files{stale}" + (f"  |  UNSAVED: {', '.join(dirty)}" if dirty else ''))
