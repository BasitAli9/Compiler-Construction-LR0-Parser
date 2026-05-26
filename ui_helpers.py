import tkinter as tk
from tkinter import ttk

# Color theme — light academic style (different from the original dark theme)
COLORS = {
    'bg'        : '#f5f6fa',
    'sidebar'   : '#ffffff',
    'header'    : '#2d3436',
    'accent'    : '#0984e3',
    'accent2'   : '#00b894',
    'warn'      : '#d63031',
    'card'      : '#dfe6e9',
    'text'      : '#2d3436',
    'muted'     : '#636e72',
    'border'    : '#b2bec3',
    'input_bg'  : '#ffffff',
    'shift_bg'  : '#d4efdf',
    'shift_fg'  : '#1e8449',
    'reduce_bg' : '#fadbd8',
    'reduce_fg' : '#922b21',
    'accept_bg' : '#fdebd0',
    'accept_fg' : '#784212',
    'goto_fg'   : '#1a5276',
    'canvas_bg' : '#eaf4fb',
    'node_fill' : '#2980b9',
    'node_start': '#e74c3c',
    'node_text' : '#ffffff',
    'arrow'     : '#2c3e50',
    'label'     : '#8e44ad',
}


def setup_styles():
    s = ttk.Style()
    s.theme_use('clam')

    s.configure("TNotebook",
                 background=COLORS['bg'],
                 borderwidth=0)

    s.configure("TNotebook.Tab",
                 background=COLORS['card'],
                 foreground=COLORS['text'],
                 padding=[14, 6],
                 font=('Segoe UI', 10))

    s.map("TNotebook.Tab",
          background=[("selected", COLORS['accent'])],
          foreground=[("selected", "#ffffff")])

    s.configure("Treeview",
                 background=COLORS['input_bg'],
                 foreground=COLORS['text'],
                 fieldbackground=COLORS['input_bg'],
                 rowheight=26)

    s.configure("Treeview.Heading",
                 background=COLORS['header'],
                 foreground='#ffffff',
                 font=('Segoe UI', 10, 'bold'))

    s.configure("Vertical.TScrollbar",
                 background=COLORS['card'])


def make_card(parent, title):
    """A titled card frame used throughout the left panel."""
    frame = tk.Frame(parent, bg=COLORS['sidebar'],
                     highlightbackground=COLORS['border'],
                     highlightthickness=1)

    tk.Label(frame, text=title,
             bg=COLORS['accent'], fg='#ffffff',
             font=('Segoe UI', 9, 'bold'),
             pady=5, padx=10, anchor='w').pack(fill=tk.X)

    return frame


def scrollable_text(parent, height, fg=None, font=None):
    """A read-only Text widget with a vertical scrollbar."""
    fg   = fg   or COLORS['text']
    font = font or ('Consolas', 10)

    frame = tk.Frame(parent, bg=COLORS['sidebar'])
    sb = tk.Scrollbar(frame)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    txt = tk.Text(frame, height=height,
                  bg=COLORS['input_bg'], fg=fg,
                  font=font, bd=0, padx=8, pady=6,
                  state='disabled', wrap='none',
                  yscrollcommand=sb.set)
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.config(command=txt.yview)
    return frame, txt
