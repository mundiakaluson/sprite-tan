"""Progress window for the global EXPORT TO GAME button. The export runs on a worker thread (PIL only); Tk is only touched from after()."""
import queue, threading
import tkinter as tk
from tkinter import ttk
import export_game


def open_dialog(root, done_cb=None, only=None):
    w = tk.Toplevel(root); w.title('Export to game'); w.geometry('640x420'); w.transient(root)
    ttk.Label(w, text='Exporting to godot/', font=('TkDefaultFont', 12, 'bold')).pack(anchor='w', padx=12, pady=(12, 2))
    head = ttk.Label(w, text='starting...'); head.pack(anchor='w', padx=12)
    bar = ttk.Progressbar(w, maximum=1000); bar.pack(fill='x', padx=12, pady=6)
    box = tk.Text(w, height=14, font=('TkFixedFont', 9), bg='#14151f', fg='#cfd3e6'); box.pack(fill='both', expand=True, padx=12, pady=4)
    close = ttk.Button(w, text='Close', state='disabled', command=w.destroy); close.pack(pady=8)
    q = queue.Queue()

    def prog(i, n, title, d, t): q.put(('p', i, n, title, d, t))

    def work():
        try: res = export_game.run(log=lambda m: q.put(('l', m)), progress=prog, only=only)
        except Exception as e: res = (False, {}, [('export', str(e))]); q.put(('l', f'FAILED: {e}'))
        q.put(('end', res))

    def poll():
        try:
            while True:
                m = q.get_nowait()
                if m[0] == 'l': box.insert('end', m[1] + '\n'); box.see('end')
                elif m[0] == 'p':
                    _, i, n, title, d, t = m; head.config(text=f'{title}  ({i + 1}/{n})' if i < n else 'done'); bar['value'] = 1000 * (i + d / max(t, 1)) / n
                else:
                    ok = m[1][0]; bar['value'] = 1000; head.config(text='Export done' if ok else 'Export finished with problems - see the log'); close.config(state='normal')
                    if done_cb: done_cb()
                    return
        except queue.Empty: pass
        w.after(80, poll)
    threading.Thread(target=work, daemon=True).start(); poll()
    return w
