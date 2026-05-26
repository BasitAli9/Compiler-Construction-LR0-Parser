#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import math
from collections import defaultdict

from grammar   import Grammar, FirstFollow
from automaton import LR0Automaton, LR0Table
from simulator import LR0Simulator
from ui_helpers import COLORS, setup_styles, make_card, scrollable_text


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LR(0) Parser Simulator ")
        self.geometry("1280x900")
        self.configure(bg=COLORS['bg'])
        self.resizable(True, True)

        self.grammar   = None
        self.ff        = None
        self.automaton = None
        self.table     = None

        setup_styles()
        self._build_header()
        self._build_body()

    # ------------------------------------------------------------------ #
    #  HEADER
    # ------------------------------------------------------------------ #
    def _build_header(self):
        bar = tk.Frame(self, bg=COLORS['header'], height=75)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        tk.Label(bar, text="LR(0) Parser Simulator By Basit Ali(54596) \nInstructor Tajamul Shahzad",
                 font=('Segoe UI', 15, 'bold'),
                 fg='#ffffff', bg=COLORS['header']
                 ).pack(side=tk.LEFT, padx=20, pady=10)

      

    # ------------------------------------------------------------------ #
    #  BODY  —  outer scrollable canvas
    # ------------------------------------------------------------------ #
    def _build_body(self):
        # outer frame holds the scrollable canvas + scrollbars
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.BOTH, expand=True)

        vsc = tk.Scrollbar(outer, orient=tk.VERTICAL)
        vsc.pack(side=tk.RIGHT, fill=tk.Y)

        hsc = tk.Scrollbar(outer, orient=tk.HORIZONTAL)
        hsc.pack(side=tk.BOTTOM, fill=tk.X)

        self.body_canvas = tk.Canvas(outer, bg=COLORS['bg'],
                                     highlightthickness=0,
                                     yscrollcommand=vsc.set,
                                     xscrollcommand=hsc.set)
        self.body_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsc.config(command=self.body_canvas.yview)
        hsc.config(command=self.body_canvas.xview)

        # inner frame — everything goes here
        self.inner = tk.Frame(self.body_canvas, bg=COLORS['bg'])
        self._win_id = self.body_canvas.create_window(
            (0, 0), window=self.inner, anchor='nw')

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.body_canvas.bind("<Configure>", self._on_canvas_configure)

        # mouse-wheel scroll
        self.body_canvas.bind_all("<MouseWheel>",
            lambda e: self.body_canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._build_sections()

    def _on_inner_configure(self, _event):
        self.body_canvas.configure(
            scrollregion=self.body_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # keep inner frame at least as wide as canvas
        self.body_canvas.itemconfig(self._win_id, width=event.width)

    # ------------------------------------------------------------------ #
    #  SECTIONS  (stacked top-to-bottom)
    # ------------------------------------------------------------------ #
    def _build_sections(self):
        p = self.inner

        # ── 1. Grammar + String input (centered top) ──────────────────
        self._build_input_section(p)

        # ── separator ─────────────────────────────────────────────────
        tk.Frame(p, bg=COLORS['border'], height=2).pack(
            fill=tk.X, padx=30, pady=(0, 0))

        # ── 2. DFA ────────────────────────────────────────────────────
        self._build_dfa_section(p)

        tk.Frame(p, bg=COLORS['border'], height=2).pack(
            fill=tk.X, padx=30, pady=(0, 0))

        # ── 3. FIRST / FOLLOW ─────────────────────────────────────────
        self._build_ff_section(p)

        tk.Frame(p, bg=COLORS['border'], height=2).pack(
            fill=tk.X, padx=30, pady=(0, 0))

        # ── 4. Parsing Table ──────────────────────────────────────────
        self._build_pt_section(p)

        tk.Frame(p, bg=COLORS['border'], height=2).pack(
            fill=tk.X, padx=30, pady=(0, 0))

        # ── 5. Trace Log ──────────────────────────────────────────────
        self._build_trace_section(p)

    # ── INPUT SECTION ──────────────────────────────────────────────────
    def _build_input_section(self, parent):
        sec = tk.Frame(parent, bg=COLORS['bg'])
        sec.pack(fill=tk.X, padx=30, pady=18)

        # Title
        tk.Label(sec, text="Grammar & Simulation Input",
                 font=('Segoe UI', 13, 'bold'),
                 fg=COLORS['header'], bg=COLORS['bg']
                 ).pack(pady=(0, 10))

        # Two-column row: [Grammar box]   [Productions + Parse-string ]
        row = tk.Frame(sec, bg=COLORS['bg'])
        row.pack(fill=tk.X)

        # ---- left: grammar text area ----
        left = tk.Frame(row, bg=COLORS['sidebar'],
                        highlightbackground=COLORS['border'],
                        highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        tk.Label(left, text="Grammar Input",
                 bg=COLORS['accent'], fg='#ffffff',
                 font=('Segoe UI', 9, 'bold'),
                 pady=5, padx=10, anchor='w').pack(fill=tk.X)

        tk.Label(left,
                 text="One rule per line:  A -> B C | D   "
                      "(epsilon → e or eps)",
                 bg=COLORS['sidebar'], fg=COLORS['muted'],
                 font=('Segoe UI', 8), justify='left'
                 ).pack(anchor='w', padx=10, pady=(4, 2))

        self.grammar_input = tk.Text(left, height=8,
                                     bg=COLORS['input_bg'], fg=COLORS['text'],
                                     font=('Consolas', 11), bd=1, relief='solid',
                                     padx=8, pady=6,
                                     insertbackground='black')
        self.grammar_input.pack(fill=tk.X, padx=10, pady=(0, 4))

        tk.Button(left, text="▶  Analyze Grammar",
                  bg=COLORS['accent'], fg='#ffffff',
                  font=('Segoe UI', 10, 'bold'),
                  relief='flat', cursor='hand2', padx=10, pady=6,
                  command=self.analyze
                  ).pack(fill=tk.X, padx=10, pady=(0, 10))

        # ---- right column: productions + simulate  ----
        right = tk.Frame(row, bg=COLORS['bg'], width=360)
        right.pack(side=tk.LEFT, fill=tk.Y)
        right.pack_propagate(False)

        # productions
        card_p = make_card(right, "Parsed Productions")
        card_p.pack(fill=tk.X, pady=(0, 8))
        _, self.productions_box = scrollable_text(card_p, height=4,
                                                   fg=COLORS['accent'])
        self.productions_box.master.pack(fill=tk.X, padx=10, pady=6)

        # simulate string
        card_s = make_card(right, "Parse a String")
        card_s.pack(fill=tk.X, pady=(0, 8))

        tk.Label(card_s, text="Tokens separated by spaces:",
                 bg=COLORS['sidebar'], fg=COLORS['muted'],
                 font=('Segoe UI', 8)
                 ).pack(anchor='w', padx=10, pady=(4, 0))

        self.token_entry = tk.Entry(card_s,
                                    bg=COLORS['input_bg'], fg=COLORS['text'],
                                    font=('Consolas', 11), bd=1, relief='solid',
                                    insertbackground='black')
        self.token_entry.pack(fill=tk.X, padx=10, pady=4)

        tk.Button(card_s, text="▶  Run Simulation",
                  bg=COLORS['accent2'], fg='#ffffff',
                  font=('Segoe UI', 10, 'bold'),
                  relief='flat', cursor='hand2', padx=10, pady=5,
                  command=self.simulate
                  ).pack(fill=tk.X, padx=10, pady=(0, 8))

      
    # ── DFA SECTION ────────────────────────────────────────────────────
    def _build_dfa_section(self, parent):
        sec = tk.Frame(parent, bg=COLORS['bg'])
        sec.pack(fill=tk.X, padx=30, pady=18)

        tk.Label(sec, text="LR(0) DFA",
                 font=('Segoe UI', 13, 'bold'),
                 fg=COLORS['header'], bg=COLORS['bg']
                 ).pack(anchor='w', pady=(0, 6))

        dfa_outer = tk.Frame(sec, bg=COLORS['canvas_bg'],
                             highlightbackground=COLORS['border'],
                             highlightthickness=1)
        dfa_outer.pack(fill=tk.X)

        dfa_inner = tk.Frame(dfa_outer, bg=COLORS['canvas_bg'])
        dfa_inner.pack(fill=tk.BOTH, expand=True)

        self.dfa_canvas = tk.Canvas(dfa_inner, bg=COLORS['canvas_bg'],
                                    height=480, highlightthickness=0)
        dfa_vsc = tk.Scrollbar(dfa_inner, orient=tk.VERTICAL,
                                command=self.dfa_canvas.yview)
        dfa_hsc = tk.Scrollbar(dfa_outer, orient=tk.HORIZONTAL,
                                command=self.dfa_canvas.xview)
        self.dfa_canvas.configure(yscrollcommand=dfa_vsc.set,
                                   xscrollcommand=dfa_hsc.set)
        dfa_vsc.pack(side=tk.RIGHT, fill=tk.Y)
        dfa_hsc.pack(side=tk.BOTTOM, fill=tk.X)
        self.dfa_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # ── FIRST / FOLLOW SECTION ─────────────────────────────────────────
    def _build_ff_section(self, parent):
        sec = tk.Frame(parent, bg=COLORS['bg'])
        sec.pack(fill=tk.X, padx=30, pady=18)

        tk.Label(sec, text="FIRST and FOLLOW Sets",
                 font=('Segoe UI', 13, 'bold'),
                 fg=COLORS['header'], bg=COLORS['bg']
                 ).pack(anchor='w', pady=(0, 6))

        wrapper = tk.Frame(sec, bg=COLORS['sidebar'],
                           highlightbackground=COLORS['border'],
                           highlightthickness=1)
        wrapper.pack(fill=tk.X)

        self.ff_text = tk.Text(wrapper, height=10,
                               bg=COLORS['input_bg'], fg=COLORS['text'],
                               font=('Consolas', 11), padx=20, pady=12,
                               state='disabled')
        ff_sb = tk.Scrollbar(wrapper, command=self.ff_text.yview)
        self.ff_text.configure(yscrollcommand=ff_sb.set)
        ff_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.ff_text.pack(fill=tk.BOTH, expand=True)

    # ── PARSING TABLE SECTION ──────────────────────────────────────────
    def _build_pt_section(self, parent):
        sec = tk.Frame(parent, bg=COLORS['bg'])
        sec.pack(fill=tk.X, padx=30, pady=18)

        tk.Label(sec, text="Parsing Table",
                 font=('Segoe UI', 13, 'bold'),
                 fg=COLORS['header'], bg=COLORS['bg']
                 ).pack(anchor='w', pady=(0, 6))

        pt_outer = tk.Frame(sec, bg=COLORS['bg'],
                            highlightbackground=COLORS['border'],
                            highlightthickness=1)
        pt_outer.pack(fill=tk.X)

        pt_inner = tk.Frame(pt_outer, bg=COLORS['bg'])
        pt_inner.pack(fill=tk.BOTH, expand=True)

        self.pt_canvas = tk.Canvas(pt_inner, bg=COLORS['bg'],
                                   height=320, highlightthickness=0)
        pt_vsc = ttk.Scrollbar(pt_inner, orient='vertical',
                                command=self.pt_canvas.yview)
        pt_hsc = ttk.Scrollbar(pt_outer, orient='horizontal',
                                command=self.pt_canvas.xview)

        self.pt_grid = tk.Frame(self.pt_canvas, bg=COLORS['bg'])
        self.pt_grid.bind("<Configure>",
                          lambda e: self.pt_canvas.configure(
                              scrollregion=self.pt_canvas.bbox("all")))
        self.pt_canvas.create_window((0, 0), window=self.pt_grid, anchor='nw')
        self.pt_canvas.configure(yscrollcommand=pt_vsc.set,
                                  xscrollcommand=pt_hsc.set)

        pt_hsc.pack(side='bottom', fill='x')
        pt_vsc.pack(side='right', fill='y')
        self.pt_canvas.pack(side='left', fill='both', expand=True)

    # ── TRACE LOG SECTION ──────────────────────────────────────────────
    def _build_trace_section(self, parent):
        sec = tk.Frame(parent, bg=COLORS['bg'])
        sec.pack(fill=tk.X, padx=30, pady=18)

        tk.Label(sec, text="Trace Log",
                 font=('Segoe UI', 13, 'bold'),
                 fg=COLORS['header'], bg=COLORS['bg']
                 ).pack(anchor='w', pady=(0, 6))

        wrapper = tk.Frame(sec, bg=COLORS['bg'],
                           highlightbackground=COLORS['border'],
                           highlightthickness=1)
        wrapper.pack(fill=tk.X)

        cols = ("Step", "State Stack", "Symbol Stack", "Input", "Action")
        self.trace_tree = ttk.Treeview(wrapper, show='headings',
                                        columns=cols, height=12)
        widths = [55, 200, 200, 210, 110]
        for col, w in zip(cols, widths):
            self.trace_tree.heading(col, text=col)
            self.trace_tree.column(col, width=w, anchor='center')

        trace_vsc = ttk.Scrollbar(wrapper, orient='vertical',
                                   command=self.trace_tree.yview)
        trace_hsc = ttk.Scrollbar(wrapper, orient='horizontal',
                                   command=self.trace_tree.xview)
        self.trace_tree.configure(yscrollcommand=trace_vsc.set,
                                   xscrollcommand=trace_hsc.set)
        trace_hsc.pack(side='bottom', fill='x')
        trace_vsc.pack(side='right', fill='y')
        self.trace_tree.pack(fill=tk.BOTH, expand=True)

        # colour tags
        self.trace_tree.tag_configure('shift',
            background=COLORS['shift_bg'], foreground=COLORS['shift_fg'])
        self.trace_tree.tag_configure('reduce',
            background=COLORS['reduce_bg'], foreground=COLORS['reduce_fg'])
        self.trace_tree.tag_configure('accept',
            background=COLORS['accept_bg'], foreground=COLORS['accept_fg'])
        self.trace_tree.tag_configure('reject',
            background='#fce4e4', foreground=COLORS['warn'])

    # ================================================================== #
    #  ANALYZE
    # ================================================================== #
    def analyze(self):
        text = self.grammar_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Empty Input", "Please enter a grammar first.")
            return

        try:
            self.grammar   = Grammar()
            self.grammar.load(text)
            self.ff        = FirstFollow(self.grammar)
            self.automaton = LR0Automaton(self.grammar)
            self.table     = LR0Table(self.grammar, self.automaton)
        except Exception as err:
            messagebox.showerror("Parse Error", str(err))
            self.status_lbl.config(text="Error", fg=COLORS['warn'])
            return

        self._show_productions()
        self._show_first_follow()
        self._draw_parse_table()
        self._draw_dfa()
        self._show_conflicts()

        self.status_lbl.config(text="Grammar analyzed ✔", fg='#00cec9')

    # ── productions ───────────────────────────────────────────────────
    def _show_productions(self):
        self.productions_box.config(state='normal')
        self.productions_box.delete('1.0', tk.END)
        for i, (lhs, rhs) in enumerate(self.grammar.productions):
            self.productions_box.insert(
                tk.END, f"  P{i}: {lhs} → {' '.join(rhs)}\n")
        self.productions_box.config(state='disabled')

    # ── FIRST / FOLLOW ────────────────────────────────────────────────
    def _show_first_follow(self):
        self.ff_text.config(state='normal')
        self.ff_text.delete('1.0', tk.END)
        self.ff_text.insert(tk.END, "FIRST and FOLLOW Sets\n")
        self.ff_text.insert(tk.END, "─" * 50 + "\n\n")

        for nt in sorted(self.grammar.non_terminals):
            if nt == self.grammar.aug_start:
                continue
            first_str  = "{ " + ", ".join(sorted(self.ff.first[nt]))  + " }"
            follow_str = "{ " + ", ".join(sorted(self.ff.follow[nt])) + " }"
            self.ff_text.insert(tk.END,
                f"  FIRST ({nt:<8}) = {first_str}\n"
                f"  FOLLOW({nt:<8}) = {follow_str}\n\n")

        self.ff_text.config(state='disabled')

    # ── PARSE TABLE ───────────────────────────────────────────────────
    def _draw_parse_table(self):
        for w in self.pt_grid.winfo_children():
            w.destroy()

        terms = sorted(self.grammar.terminals) + ['$']
        nts   = sorted(self.grammar.non_terminals - {self.grammar.aug_start})

        def cell(text, row, col, bg, fg, bold=False, width=8):
            font = ('Consolas', 9, 'bold') if bold else ('Consolas', 9)
            tk.Label(self.pt_grid,
                     text=text, bg=bg, fg=fg, font=font, width=width,
                     borderwidth=1, relief='solid', pady=5
                     ).grid(row=row, column=col, sticky='nsew')

        cell("State", 0, 0, COLORS['header'], '#ffffff', bold=True, width=6)
        tk.Label(self.pt_grid, text="ACTION",
                 bg='#154360', fg='#aed6f1',
                 font=('Consolas', 10, 'bold'),
                 borderwidth=1, relief='solid', pady=5
                 ).grid(row=0, column=1, columnspan=len(terms), sticky='nsew')
        tk.Label(self.pt_grid, text="GOTO",
                 bg='#145a32', fg='#a9dfbf',
                 font=('Consolas', 10, 'bold'),
                 borderwidth=1, relief='solid', pady=5
                 ).grid(row=0, column=1+len(terms), columnspan=len(nts),
                        sticky='nsew')

        cell("", 1, 0, COLORS['header'], '#ffffff', bold=True, width=6)
        for j, t in enumerate(terms):
            cell(t, 1, j+1, '#1b4f72', '#aed6f1', bold=True)
        for j, nt in enumerate(nts):
            cell(nt, 1, j+1+len(terms), '#1d4d27', '#a9dfbf', bold=True)

        for i in range(len(self.automaton.states)):
            row_bg = '#fdfefe' if i % 2 == 0 else '#f2f3f4'
            cell(str(i), i+2, 0, COLORS['header'], '#ffffff', bold=True, width=6)

            for j, t in enumerate(terms):
                val = self.table.action.get((i, t), "")
                if val.startswith('s'):
                    bg, fg = COLORS['shift_bg'], COLORS['shift_fg']
                elif val.startswith('r'):
                    bg, fg = COLORS['reduce_bg'], COLORS['reduce_fg']
                elif val == 'acc':
                    bg, fg = COLORS['accept_bg'], COLORS['accept_fg']
                else:
                    bg, fg = row_bg, COLORS['muted']
                cell(val, i+2, j+1, bg, fg)

            for j, nt in enumerate(nts):
                val = str(self.table.goto_table.get((i, nt), ""))
                fg  = COLORS['goto_fg'] if val else COLORS['muted']
                cell(val, i+2, j+1+len(terms), row_bg, fg)

    # ── DFA ───────────────────────────────────────────────────────────
    def _draw_dfa(self):
        self.dfa_canvas.delete("all")

        transitions = self.automaton.transitions
        num_states  = len(self.automaton.states)

        # BFS spanning tree for layout
        parent   = {0: None}
        children = defaultdict(list)
        edge_label = {}

        queue   = [0]
        visited = {0}
        while queue:
            src = queue.pop(0)
            for (s, sym), dst in sorted(transitions.items()):
                if s != src:
                    continue
                if dst not in visited:
                    visited.add(dst)
                    parent[dst] = src
                    children[src].append(dst)
                    queue.append(dst)
                if (src, dst) not in edge_label:
                    edge_label[(src, dst)] = sym

        for sid in range(num_states):
            if sid not in visited:
                children[0].append(sid)
                edge_label[(0, sid)] = "?"

        # node sizes
        node_size = {}
        for sid in range(num_states):
            items_text = "\n".join(str(it) for it in self.automaton.states[sid])
            lines = [f"I{sid}"] + items_text.split('\n')
            w = max(len(l) for l in lines) * 8 + 30
            h = len(lines) * 17 + 20
            node_size[sid] = (w / 2, h / 2)

        H_SPACING = 240
        V_SPACING = 200
        MARGIN_X  = 120
        MARGIN_Y  = 80

        depth = {0: 0}
        queue = [0]
        while queue:
            u = queue.pop(0)
            for c in children[u]:
                depth[c] = depth[u] + 1
                queue.append(c)

        x_pos = {}
        leaf_counter = [0]

        def assign_x(node):
            kids = children[node]
            if not kids:
                x_pos[node] = MARGIN_X + leaf_counter[0] * H_SPACING
                leaf_counter[0] += 1
            else:
                for k in kids:
                    assign_x(k)
                x_pos[node] = (x_pos[kids[0]] + x_pos[kids[-1]]) / 2

        assign_x(0)

        node_pos = {}
        for sid in range(num_states):
            cx = x_pos.get(sid, MARGIN_X)
            cy = MARGIN_Y + depth.get(sid, 0) * V_SPACING
            node_pos[sid] = (cx, cy)

        # draw nodes
        for sid in range(num_states):
            cx, cy = node_pos[sid]
            hw, hh = node_size[sid]
            items_text = "\n".join(str(it) for it in self.automaton.states[sid])
            fill = COLORS['node_start'] if sid == 0 else COLORS['node_fill']

            self.dfa_canvas.create_rectangle(
                cx-hw, cy-hh, cx+hw, cy+hh,
                fill=fill, outline='#ffffff', width=2)
            self.dfa_canvas.create_text(
                cx, cy-hh+11, text=f"I{sid}",
                fill='#f9ca24', font=('Consolas', 9, 'bold'))
            self.dfa_canvas.create_text(
                cx, cy+5, text=items_text,
                fill=COLORS['node_text'],
                font=('Consolas', 8), justify='center')

        # draw edges
        for (src_id, symbol), dst_id in transitions.items():
            if src_id not in node_pos or dst_id not in node_pos:
                continue
            x1, y1 = node_pos[src_id]
            x2, y2 = node_pos[dst_id]
            hw1, hh1 = node_size[src_id]
            hw2, hh2 = node_size[dst_id]

            dx, dy = x2-x1, y2-y1
            if dx == 0 and dy == 0:
                continue

            sx, sy = self._box_edge(x1, y1, dx, dy, hw1, hh1)
            ex, ey = self._box_edge(x2, y2, -dx, -dy, hw2, hh2)

            is_back   = (dy < 0)
            arrow_col = '#e17055' if is_back else COLORS['arrow']

            self.dfa_canvas.create_line(
                sx, sy, ex, ey,
                fill=arrow_col, arrow=tk.LAST,
                width=1.6, arrowshape=(10, 12, 4))
            mx, my = (sx+ex)/2, (sy+ey)/2
            self.dfa_canvas.create_text(
                mx, my-10, text=symbol,
                fill=COLORS['label'],
                font=('Consolas', 10, 'bold'))

        self.dfa_canvas.configure(
            scrollregion=self.dfa_canvas.bbox("all"))

    def _box_edge(self, cx, cy, dx, dy, half_w, half_h):
        t_values = []
        if dx != 0:
            t_values.append(half_w / abs(dx))
        if dy != 0:
            t_values.append(half_h / abs(dy))
        t = min(t_values) if t_values else 0
        return cx + dx*t, cy + dy*t

    # ================================================================== #
    #  SIMULATE
    # ================================================================== #
    def simulate(self):
        if self.table is None:
            messagebox.showwarning("Not Ready", "Please analyze a grammar first.")
            return

        raw = self.token_entry.get().strip()
        if not raw:
            messagebox.showwarning("Empty Input", "Please enter tokens to parse.")
            return

        tokens = raw.split() #['id', '+', 'id']
        sim    = LR0Simulator(self.grammar, self.table)
        trace, accepted = sim.simulate(tokens)

        for row in self.trace_tree.get_children():
            self.trace_tree.delete(row)

        for i, step in enumerate(trace):
            act = step['action']
            if act and act.startswith('s'):
                tag = ('shift',)
            elif act and act.startswith('r'):
                tag = ('reduce',)
            elif act == 'acc':
                tag = ('accept',)
            else:
                tag = ('reject',)

            self.trace_tree.insert('', tk.END, tags=tag, values=(
                i + 1,
                step['stack'],
                step['symbols'],
                step['input'],
                act
            ))

        # scroll to trace section
        self.body_canvas.yview_moveto(1.0)

        if accepted:
            messagebox.showinfo("Result", "✔  String ACCEPTED")
            self.status_lbl.config(text="Accepted ✔", fg='#00b894')
        else:
            messagebox.showinfo("Result", "✘  String REJECTED")
            self.status_lbl.config(text="Rejected ✘", fg=COLORS['warn'])


if __name__ == "__main__":
    App().mainloop()
