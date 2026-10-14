"""CSV tables + an Excel-style editable grid. Files stay plain CSV so Excel and this tool can share them."""
import csv, os, sys, subprocess, tkinter as tk
from tkinter import ttk, messagebox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')


def read_csv(path):
    with open(path, 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    rd = csv.DictReader(text.splitlines())
    return list(rd.fieldnames or []), [dict(r) for r in rd], bom


def write_csv(path, cols, rows, bom=False):
    if os.path.exists(path):
        try:
            with open(path, 'rb') as a, open(path + '.bak', 'wb') as b:
                b.write(a.read())
        except OSError:
            pass
    with open(path, 'w', newline='', encoding='utf-8-sig' if bom else 'utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols})


def open_external(path):
    if sys.platform.startswith('win'):
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


class Table:
    """In-memory copy of one CSV with change tracking and a file-changed check."""

    def __init__(self, name):
        self.name = name
        self.path = os.path.join(DATA, name + '.csv')
        self.listeners = []
        self.load()

    def load(self):
        self.cols, self.rows, self.bom = read_csv(self.path)
        self.mtime = os.path.getmtime(self.path)
        self.dirty = False
        self.undo = []
        self.notify()

    def notify(self):
        for fn in list(self.listeners):
            try:
                fn()
            except tk.TclError:
                pass

    def snapshot(self):
        self.undo.append([dict(r) for r in self.rows])
        self.undo = self.undo[-50:]

    def do_undo(self):
        if self.undo:
            self.rows = self.undo.pop(); self.dirty = True; self.notify()

    def set(self, i, col, val, snap=True):
        if self.rows[i].get(col, '') == val:
            return
        if snap: self.snapshot()
        self.rows[i][col] = val; self.dirty = True; self.notify()

    def save(self):
        write_csv(self.path, self.cols, self.rows, self.bom)
        self.mtime = os.path.getmtime(self.path); self.dirty = False; self.notify()

    def changed_on_disk(self):
        try:
            return os.path.getmtime(self.path) != self.mtime
        except OSError:
            return False


_cache = {}


def table(name):
    if name not in _cache:
        _cache[name] = Table(name)
    return _cache[name]


def watch_all(root, ms=1500, status=None):
    """Poll every opened table: reload silently if clean, warn if there are unsaved edits."""
    def tick():
        for t in _cache.values():
            if t.changed_on_disk():
                if not t.dirty:
                    try:
                        t.load()
                        if status: status(f'{t.name}.csv changed on disk (Excel?) - reloaded')
                    except Exception as e:
                        if status: status(f'{t.name}.csv could not be read: {e}')
                else:
                    t.mtime = os.path.getmtime(t.path)
                    if status: status(f'{t.name}.csv changed on disk but you have unsaved edits - Save overwrites Excel changes, Reload discards yours')
        root.after(ms, tick)
    root.after(ms, tick)


class Grid(ttk.Frame):
    """Treeview grid bound to a Table. Double-click a cell to edit, header click sorts, filter box, add/duplicate/delete."""

    def __init__(self, master, tbl, choices=None, new_row=None, on_select=None, hide=(), width_for=None, extra_buttons=()):
        super().__init__(master)
        self.t = tbl; self.choices = choices or {}; self.new_row = new_row; self.on_select = on_select
        self.hide = set(hide); self.sort_col = None; self.sort_rev = False; self.edit = None; self.view = []
        bar = ttk.Frame(self); bar.pack(fill='x')
        ttk.Button(bar, text='Save', command=self.save).pack(side='left')
        ttk.Button(bar, text='Reload', command=self.reload).pack(side='left', padx=2)
        ttk.Button(bar, text='Undo', command=self.t.do_undo).pack(side='left')
        ttk.Button(bar, text='Open in Excel', command=lambda: open_external(self.t.path)).pack(side='left', padx=2)
        ttk.Separator(bar, orient='vertical').pack(side='left', fill='y', padx=4)
        ttk.Button(bar, text='+ Add', command=self.add).pack(side='left')
        ttk.Button(bar, text='Duplicate', command=self.dup).pack(side='left', padx=2)
        ttk.Button(bar, text='Delete', command=self.delete).pack(side='left')
        for txt, fn in extra_buttons:
            ttk.Button(bar, text=txt, command=lambda fn=fn: fn(self)).pack(side='left', padx=2)
        self.filter = tk.StringVar(); self.filter.trace_add('write', lambda *_: self.fill())
        ttk.Label(bar, text='  Filter').pack(side='left'); ttk.Entry(bar, textvariable=self.filter, width=18).pack(side='left')
        self.info = ttk.Label(bar, text=''); self.info.pack(side='right')
        box = ttk.Frame(self); box.pack(fill='both', expand=True)
        cols = [c for c in self.t.cols if c not in self.hide]
        self.tv = ttk.Treeview(box, columns=cols, show='headings', selectmode='extended')
        for c in cols:
            self.tv.heading(c, text=c, command=lambda c=c: self.sort(c))
            self.tv.column(c, width=(width_for or {}).get(c, 90 if len(c) < 9 else 130), minwidth=40, stretch=False)
        ys = ttk.Scrollbar(box, command=self.tv.yview); xs = ttk.Scrollbar(self, orient='horizontal', command=self.tv.xview)
        self.tv.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(side='right', fill='y'); self.tv.pack(fill='both', expand=True); xs.pack(fill='x')
        self.cols = cols
        self.tv.bind('<Double-1>', self.begin_edit); self.tv.bind('<<TreeviewSelect>>', self._sel)
        self.tv.bind('<Control-z>', lambda e: self.t.do_undo()); self.tv.bind('<Control-s>', lambda e: self.save())
        self.tv.bind('<Delete>', lambda e: self.delete())
        self.t.listeners.append(self.fill); self.fill()

    # --- data <-> view
    def fill(self):
        sel = self.selected_indices()
        q = self.filter.get().lower().strip()
        idx = [i for i, r in enumerate(self.t.rows) if not q or any(q in str(v).lower() for v in r.values())]
        if self.sort_col:
            def key(i):
                v = self.t.rows[i].get(self.sort_col, '')
                try: return (0, float(v))
                except ValueError: return (1, v.lower())
            idx.sort(key=key, reverse=self.sort_rev)
        self.view = idx
        self.tv.delete(*self.tv.get_children())
        for i in idx:
            self.tv.insert('', 'end', iid=str(i), values=[self.t.rows[i].get(c, '') for c in self.cols])
        keep = [str(i) for i in sel if i in idx]
        if keep: self.tv.selection_set(keep)
        self.info.config(text=f"{len(idx)}/{len(self.t.rows)} rows{'  *unsaved*' if self.t.dirty else ''}")

    def selected_indices(self):
        try: return [int(i) for i in self.tv.selection()]
        except tk.TclError: return []

    def _sel(self, _e=None):
        if self.on_select: self.on_select(self.selected_indices())

    def sort(self, c):
        self.sort_rev = (not self.sort_rev) if self.sort_col == c else False
        self.sort_col = c; self.fill()

    # --- editing
    def begin_edit(self, ev):
        if self.tv.identify_region(ev.x, ev.y) != 'cell': return
        iid = self.tv.identify_row(ev.y); col = self.tv.identify_column(ev.x)
        if not iid: return
        c = self.cols[int(col[1:]) - 1]; i = int(iid)
        x, y, w, h = self.tv.bbox(iid, col)
        if self.edit: self.edit.destroy()
        val = self.t.rows[i].get(c, '')
        if c in self.choices:
            e = ttk.Combobox(self.tv, values=self.choices[c], width=max(6, w // 8)); e.set(val)
        else:
            e = ttk.Entry(self.tv); e.insert(0, val)
        e.place(x=x, y=y, width=max(w, 70), height=h); e.focus_set(); self.edit = e

        def done(save=True):
            if self.edit is None: return
            v = e.get(); e.destroy(); self.edit = None
            if save: self.t.set(i, c, v)
        e.bind('<Return>', lambda _e: done()); e.bind('<Escape>', lambda _e: done(False)); e.bind('<FocusOut>', lambda _e: done())
        if c in self.choices: e.bind('<<ComboboxSelected>>', lambda _e: done())

    def add(self):
        self.t.snapshot()
        r = self.new_row(self.t) if self.new_row else {c: '' for c in self.t.cols}
        self.t.rows.append(r); self.t.dirty = True; self.t.notify()
        n = str(len(self.t.rows) - 1)
        if n in self.tv.get_children(): self.tv.selection_set(n); self.tv.see(n)

    def dup(self):
        sel = self.selected_indices()
        if not sel: return
        self.t.snapshot()
        for i in sel:
            r = dict(self.t.rows[i])
            if self.new_row:
                nr = self.new_row(self.t); r['id'] = nr.get('id', r.get('id', ''))
                if 'name' in r: r['name'] = r['name'] + ' copy'
            self.t.rows.append(r)
        self.t.dirty = True; self.t.notify()

    def delete(self):
        sel = self.selected_indices()
        if not sel or not messagebox.askyesno('Delete', f'Delete {len(sel)} row(s)?'): return
        self.t.snapshot()
        for i in sorted(sel, reverse=True): del self.t.rows[i]
        self.t.dirty = True; self.t.notify()

    def save(self):
        try:
            self.t.save()
        except PermissionError:
            messagebox.showerror('Save', f'{self.t.name}.csv is open in Excel. Close it there (or save from Excel and Reload).')

    def reload(self):
        if self.t.dirty and not messagebox.askyesno('Reload', 'Discard unsaved edits and reload from disk?'): return
        self.t.load()


class Split(ttk.Frame):
    """Main area on the left, fixed-width side panel on the right (the side keeps its natural width)."""

    def __init__(self, master, **kw):
        super().__init__(master)
        self.parts = []

    def add(self, w, weight=1):
        self.parts.append(w)
        if len(self.parts) == 2:
            self.parts[1].pack(side='right', fill='y')
            self.parts[0].pack(side='left', fill='both', expand=True)
