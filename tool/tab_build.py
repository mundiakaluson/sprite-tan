import os, sys, subprocess, threading, queue, time, signal
import tkinter as tk
from tkinter import ttk
import tables

ROOT = tables.ROOT
JOBS = [
    ('Run self-test', 'tool/selftest.py', '.', 'headless checks, a few seconds'),
    ('Rebuild body sheets and skins', 'gen_uv.py', 'sprites', 'about 2 minutes'),
    ('Rebuild hair layers', 'export_hair.py', 'sprites', 'about 2 minutes'),
]


class BuildTab(ttk.Frame):
    """Buttons for the command-line steps (python3 tool/selftest.py, sprites/gen_uv.py, sprites/export_hair.py) with a live log."""

    def __init__(self, master):
        super().__init__(master)
        self.q = queue.Queue(); self.proc = None; self.t0 = 0; self.queue_left = []
        bar = ttk.Frame(self, padding=6); bar.pack(fill='x')
        self.btn = []
        for title, script, cwd, note in JOBS:
            f = ttk.Frame(bar); f.pack(side='left', padx=6)
            b = ttk.Button(f, text=title, command=lambda s=script, c=cwd, t=title: self.start([(t, s, c)])); b.pack(); self.btn.append(b)
            ttk.Label(f, text=note, foreground='#8a90a0').pack()
        f = ttk.Frame(bar); f.pack(side='left', padx=6)
        b = ttk.Button(f, text='Run all three', command=lambda: self.start([(t, s, c) for t, s, c, _ in JOBS])); b.pack(); self.btn.append(b)
        ttk.Label(f, text='one after the other', foreground='#8a90a0').pack()
        self.stop = ttk.Button(bar, text='Stop', command=self.cancel, state='disabled'); self.stop.pack(side='right', padx=6)
        self.state = ttk.Label(self, text='Idle', anchor='w'); self.state.pack(fill='x', padx=8)
        self.bar = ttk.Progressbar(self, mode='indeterminate'); self.bar.pack(fill='x', padx=8, pady=3)
        box = ttk.Frame(self); box.pack(fill='both', expand=True, padx=8, pady=4)
        self.log = tk.Text(box, wrap='none', bg='#12141c', fg='#d0d4e0', insertbackground='#d0d4e0', font=('TkFixedFont', 10), state='disabled')
        sy = ttk.Scrollbar(box, command=self.log.yview); self.log.config(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y'); self.log.pack(fill='both', expand=True)
        self.log.tag_configure('head', foreground='#7ec8ff'); self.log.tag_configure('bad', foreground='#ff7a7a'); self.log.tag_configure('good', foreground='#7ee08a')
        self.after(100, self.poll)

    def say(self, s, tag=None):
        self.log.config(state='normal'); self.log.insert('end', s if s.endswith('\n') else s + '\n', tag); self.log.see('end'); self.log.config(state='disabled')

    def busy(self, on):
        for b in self.btn: b.config(state='disabled' if on else 'normal')
        self.stop.config(state='normal' if on else 'disabled')
        if on: self.bar.start(15)
        else: self.bar.stop()

    def start(self, jobs):
        if self.proc is not None or self.queue_left: return
        self.queue_left = list(jobs); self.busy(True); self.next_job()

    def next_job(self):
        if not self.queue_left:
            self.busy(False); self.state.config(text='Idle'); return
        title, script, cwd = self.queue_left.pop(0)
        self.say(f'$ cd {cwd} && python3 {script}' if cwd != '.' else f'$ python3 {script}', 'head')
        self.name = title; self.t0 = time.time(); self.state.config(text=f'Running: {title} ...')
        cmd = [sys.executable, '-u', os.path.join(ROOT, script) if cwd == '.' else script]
        try:
            kw = dict(start_new_session=True) if os.name != 'nt' else dict(creationflags=getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0))
            self.proc = subprocess.Popen(cmd, cwd=os.path.join(ROOT, cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, **kw)
        except Exception as e:
            self.say(f'could not start: {e}', 'bad'); self.proc = None; self.queue_left = []; self.busy(False); return
        pr = self.proc

        def pump():
            for line in pr.stdout: self.q.put(('line', line))
            pr.wait(); self.q.put(('exit', pr.returncode))
        threading.Thread(target=pump, daemon=True).start()

    def cancel(self):
        self.queue_left = []
        if self.proc is not None:
            try:
                if os.name == 'nt': self.proc.terminate()
                else: os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except Exception: pass
            self.say('stopped by you', 'bad')

    def poll(self):
        try:
            while True:
                k, v = self.q.get_nowait()
                if k == 'line': self.say(v.rstrip('\n'))
                else:
                    secs = time.time() - self.t0; self.proc = None
                    ok = v == 0
                    self.say(f'{self.name}: {"done" if ok else "failed (exit %s)" % v} in {secs:.0f}s', 'good' if ok else 'bad')
                    if not ok: self.queue_left = []
                    self.next_job()
        except queue.Empty:
            pass
        if self.proc is not None: self.state.config(text=f'Running: {self.name} ... {time.time() - self.t0:.0f}s')
        self.after(100, self.poll)
