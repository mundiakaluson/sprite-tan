"""Tab strip that wraps onto new rows (ttk.Notebook cannot). Drop-in for the parts of Notebook the tool uses:
add(widget, text=), select(widget=None), nametowidget via Tk, bind('<<NotebookTabChanged>>'). Tab pages are children of this frame; the button bar lives in `bar`."""
import tkinter as tk
from tkinter import ttk


class WrapTabs(ttk.Frame):
    def __init__(self, master, bar_parent=None):
        super().__init__(master)
        self.bar = ttk.Frame(bar_parent if bar_parent is not None else self)
        if bar_parent is None: self.bar.pack(fill='x')
        self.pages, self.buttons, self.cur = [], {}, None
        self.var = tk.StringVar()
        st = ttk.Style(); st.configure('Tab.Toolbutton', padding=(10, 4))
        self.bar.bind('<Configure>', lambda e: self._layout())
        self.body = ttk.Frame(self); self.body.pack(fill='both', expand=True)

    def add(self, w, text=''):
        b = ttk.Radiobutton(self.bar, text=text, value=str(w), variable=self.var, style='Toolbutton', command=lambda: self.select(w))
        self.pages.append(w); self.buttons[w] = b; self._layout()

    def _layout(self):
        W = max(self.bar.winfo_width(), 200); x = y = 0; row_h = 0
        for w in self.pages:
            b = self.buttons[w]; b.update_idletasks()
            bw, bh = b.winfo_reqwidth() + 2, b.winfo_reqheight() + 2
            if x and x + bw > W: x = 0; y += row_h; row_h = 0
            b.place(x=x, y=y); x += bw; row_h = max(row_h, bh)
        self.bar.configure(height=y + row_h)

    def select(self, w=None):
        if w is None: return str(self.cur) if self.cur is not None else ''
        if isinstance(w, str): w = self.nametowidget(w)
        if w is self.cur: return
        if self.cur is not None: self.cur.pack_forget()
        self.cur = w; w.pack(in_=self.body, fill='both', expand=True); self.var.set(str(w))
        self.event_generate('<<NotebookTabChanged>>')
