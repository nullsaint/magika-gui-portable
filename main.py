import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from magika import Magika, PredictionMode
from pathlib import Path
import time
from collections import Counter
import json
import gc

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use("Agg")  # Prevent matplotlib from holding display resources

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "1.0.0"


# ============================================================
# ANALYSIS WINDOW — LEFT/RIGHT split layout
# ============================================================
class AnalysisWindow(tk.Toplevel):

    BG       = "#1a1a2e"
    BG_CARD  = "#16213e"
    BG_CHART = "#0f3460"

    def __init__(self, parent, results):
        super().__init__(parent)
        self.title("Magika Analysis Report")
        self.configure(bg=self.BG)
        self.results = results
        self._canvas_refs = []
        self._figures = []  # Track figures for cleanup

        # Proper close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Maximise & focus
        self.after(50, lambda: self.state("zoomed"))
        self.after(150, self.focus_force)

        # ── Header bar ──
        bar = tk.Frame(self, bg=self.BG)
        bar.pack(fill="x", padx=20, pady=(15, 8))
        tk.Label(bar, text="MAGIKA ANALYSIS", font=("Segoe UI", 22, "bold"),
                 bg=self.BG, fg="white").pack(side="left")
        tk.Button(bar, text="EXPORT JSON", font=("Segoe UI", 10, "bold"),
                  bg="#34495e", fg="white", relief="flat", padx=14, pady=5,
                  activebackground="#2c3e50", activeforeground="white",
                  command=self._export_json).pack(side="right")

        # ── Main horizontal split ──
        body = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=self.BG,
                              sashwidth=6, sashrelief="flat")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # ===================== LEFT PANEL =====================
        left = tk.Frame(body, bg=self.BG)
        body.add(left, width=520, stretch="always")

        # Stats cards
        stats_row = tk.Frame(left, bg=self.BG)
        stats_row.pack(fill="x", pady=(0, 8))
        total  = len(results)
        unique = len(set(r.output.label for r in results))
        avg    = sum(r.score for r in results) / total if total else 0
        for val, lbl in [(str(total), "Total Files"),
                         (str(unique), "Unique Types"),
                         (f"{avg:.2%}", "Avg Confidence")]:
            card = tk.Frame(stats_row, bg=self.BG_CARD, padx=14, pady=8)
            card.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(card, text=val, font=("Segoe UI", 20, "bold"),
                     bg=self.BG_CARD, fg="white").pack()
            tk.Label(card, text=lbl, font=("Segoe UI", 9),
                     bg=self.BG_CARD, fg="#999").pack()

        # Pie chart slot
        self._pie_frame = tk.Frame(left, bg=self.BG_CHART)
        self._pie_frame.pack(fill="both", expand=True, pady=(0, 4))

        # Histogram slot
        self._hist_frame = tk.Frame(left, bg=self.BG_CHART)
        self._hist_frame.pack(fill="both", expand=True, pady=(4, 0))

        # ===================== RIGHT PANEL ====================
        right = tk.Frame(body, bg="#111")
        body.add(right, width=500, stretch="always")

        tk.Label(right, text="FILE INSPECTOR", font=("Segoe UI", 14, "bold"),
                 bg="#111", fg="white").pack(anchor="w", padx=12, pady=(10, 6))

        # Toolbar
        tb = tk.Frame(right, bg="#222", pady=6)
        tb.pack(fill="x", padx=8)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._apply_filters)
        tk.Entry(tb, textvariable=self._search_var,
                 font=("Segoe UI", 10), bg="#333", fg="white",
                 insertbackground="white", relief="flat", width=22).pack(side="left", padx=6)

        tk.Label(tb, text="Type:", font=("Segoe UI", 9),
                 bg="#222", fg="#aaa").pack(side="left", padx=(8, 2))
        all_types = sorted(set(r.output.label for r in results))
        self._type_var = tk.StringVar(value="All")
        cb = ttk.Combobox(tb, textvariable=self._type_var,
                          values=["All"] + all_types,
                          state="readonly", width=14, font=("Segoe UI", 9))
        cb.pack(side="left", padx=2)
        cb.bind("<<ComboboxSelected>>", self._apply_filters)

        tk.Button(tb, text="Reset", font=("Segoe UI", 8),
                  bg="#e74c3c", fg="white", relief="flat", padx=8,
                  command=self._clear_filters).pack(side="right", padx=6)

        self._status_lbl = tk.Label(tb, text=f"{total} files",
                                    font=("Segoe UI", 9), bg="#222", fg="#888")
        self._status_lbl.pack(side="right", padx=8)

        # Treeview
        self._build_tree(right)
        self._populate(results)

        # Draw charts after window is fully rendered
        self.update_idletasks()
        self.update()
        self.after(400, self._draw_pie)
        self.after(500, self._draw_hist)

    # ----------------------------------------------------------
    def _on_close(self):
        """Properly clean up matplotlib figures and memory."""
        for canvas in self._canvas_refs:
            try:
                canvas.get_tk_widget().destroy()
            except Exception:
                pass
        for fig in self._figures:
            try:
                fig.clf()
                matplotlib.pyplot.close(fig) if hasattr(matplotlib, 'pyplot') else None
            except Exception:
                pass
        self._canvas_refs.clear()
        self._figures.clear()
        self.results = None
        gc.collect()
        self.destroy()

    # ----------------------------------------------------------
    def _build_tree(self, parent):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Dark.Treeview",
                        background="#1a1a1a", foreground="white",
                        fieldbackground="#1a1a1a", borderwidth=0,
                        rowheight=22, font=("Segoe UI", 9))
        style.map("Dark.Treeview", background=[("selected", "#3498db")])
        style.configure("Dark.Treeview.Heading",
                        background="#2b2b2b", foreground="white",
                        relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Dark.Treeview.Heading", background=[("active", "#34495e")])

        tree_wrap = tk.Frame(parent, bg="#111")
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical")
        vsb.pack(side="right", fill="y")

        self._tree = ttk.Treeview(
            tree_wrap, style="Dark.Treeview",
            columns=("label", "score", "path", "raw_score"), show="headings",
            yscrollcommand=vsb.set)
        vsb.config(command=self._tree.yview)

        self._sort_state = {}

        self._tree.heading("label", text="LABEL",
                           command=lambda: self._sort_column("label", False))
        self._tree.heading("score", text="SCORE",
                           command=lambda: self._sort_column("score", True))
        self._tree.heading("path",  text="FILE PATH")
        self._tree.column("label", width=100, anchor="center")
        self._tree.column("score", width=70, anchor="center")
        self._tree.column("path",  width=350, anchor="w")
        self._tree.column("raw_score", width=0, stretch=False)
        self._tree["displaycolumns"] = ("label", "score", "path")
        self._tree.pack(fill="both", expand=True)

    # ----------------------------------------------------------
    def _draw_pie(self):
        try:
            bg = self.BG_CHART
            counts = Counter(r.output.label for r in self.results)
            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top = dict(sorted_items[:8])
            if len(sorted_items) > 8:
                top["Others"] = sum(v for _, v in sorted_items[8:])

            fig = Figure(figsize=(5, 3), dpi=100, facecolor=bg)
            self._figures.append(fig)
            ax = fig.add_subplot(111)
            ax.set_facecolor(bg)
            palette = ["#3498db", "#9b59b6", "#2ecc71", "#f1c40f",
                        "#e67e22", "#e74c3c", "#1abc9c", "#34495e", "#95a5a6"]
            wedges, texts, autotexts = ax.pie(
                list(top.values()), labels=list(top.keys()), autopct="%1.1f%%",
                startangle=140, colors=palette[:len(top)],
                textprops={"color": "white", "fontsize": 8})
            ax.set_title("File Type Distribution", color="white", fontsize=11, pad=10)
            fig.tight_layout()

            c = FigureCanvasTkAgg(fig, master=self._pie_frame)
            c.draw()
            c.get_tk_widget().pack(fill="both", expand=True)
            self._canvas_refs.append(c)
        except Exception as e:
            tk.Label(self._pie_frame, text=f"Chart error: {e}",
                     bg=self.BG_CHART, fg="red").pack(expand=True)

    def _draw_hist(self):
        try:
            bg = self.BG_CHART
            scores = [r.score for r in self.results]
            fig = Figure(figsize=(5, 3), dpi=100, facecolor=bg)
            self._figures.append(fig)
            ax = fig.add_subplot(111)
            ax.set_facecolor(bg)
            ax.hist(scores, bins=10, color="#9b59b6", edgecolor="white", alpha=0.8)
            ax.set_title("Confidence Distribution", color="white", fontsize=11, pad=10)
            ax.set_xlabel("Score", color="#ccc", fontsize=9)
            ax.set_ylabel("Count", color="#ccc", fontsize=9)
            ax.tick_params(colors="white", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#444")
            fig.tight_layout()

            c = FigureCanvasTkAgg(fig, master=self._hist_frame)
            c.draw()
            c.get_tk_widget().pack(fill="both", expand=True)
            self._canvas_refs.append(c)
        except Exception as e:
            tk.Label(self._hist_frame, text=f"Chart error: {e}",
                     bg=self.BG_CHART, fg="red").pack(expand=True)

    # ----------------------------------------------------------
    def _sort_column(self, col, numeric):
        ascending = not self._sort_state.get(col, False)
        self._sort_state[col] = ascending

        items = [(self._tree.set(iid, col), iid) for iid in self._tree.get_children()]

        if numeric:
            items = [(self._tree.set(iid, "raw_score"), iid)
                     for iid in self._tree.get_children()]
            items.sort(key=lambda x: float(x[0]), reverse=not ascending)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=not ascending)

        for idx, (_, iid) in enumerate(items):
            self._tree.move(iid, "", idx)

        arrow = " ▲" if ascending else " ▼"
        base_names = {"label": "LABEL", "score": "SCORE"}
        for c, name in base_names.items():
            self._tree.heading(c, text=name)
        self._tree.heading(col, text=base_names[col] + arrow)

    # ----------------------------------------------------------
    def _populate(self, data):
        self._tree.delete(*self._tree.get_children())
        self._sort_state = {}
        self._tree.heading("label", text="LABEL")
        self._tree.heading("score", text="SCORE")
        for r in data:
            self._tree.insert("", "end",
                              values=(r.output.label, f"{r.score:.2%}",
                                      str(r.path), f"{r.score:.6f}"))
        self._status_lbl.config(text=f"{len(data)} / {len(self.results)} files")

    def _apply_filters(self, *_):
        filtered = list(self.results)
        t = self._type_var.get()
        if t != "All":
            filtered = [r for r in filtered if r.output.label == t]
        q = self._search_var.get().lower()
        if q:
            filtered = [r for r in filtered if q in Path(r.path).name.lower()]
        self._populate(filtered)

    def _clear_filters(self):
        self._search_var.set("")
        self._type_var.set("All")
        self._populate(self.results)

    def _export_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            data = [{"file": Path(r.path).name, "label": r.output.label,
                     "mime": r.output.mime_type, "score": float(r.score)}
                    for r in self.results]
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Export", f"Saved {len(data)} entries.")


# ============================================================
# MAIN SCANNER WINDOW
# ============================================================
class MagikaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Magika by Google — Portable File Inspector")
        self.geometry("950x700")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Proper exit handler
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

        self.magika = Magika(prediction_mode=PredictionMode.HIGH_CONFIDENCE)
        self.results = []
        self._analysis_windows = []

        # ── Sidebar ──
        self.side = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.side.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.side, text="MAGIKA",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(25, 2))
        ctk.CTkLabel(self.side, text="by Google",
                     font=ctk.CTkFont(size=12), text_color="#888").pack(pady=(0, 5))
        ctk.CTkLabel(self.side, text=f"v{APP_VERSION}",
                     font=ctk.CTkFont(size=10), text_color="#555").pack(pady=(0, 20))

        ctk.CTkLabel(self.side, text="Prediction Mode:").pack(pady=(20, 0))
        ctk.CTkOptionMenu(
            self.side,
            values=["High Confidence", "Medium Confidence", "Best Guess"],
            command=self.set_mode,
        ).pack(pady=10)

        # ── Main area ──
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.center = ctk.CTkFrame(self.main, corner_radius=20)
        self.center.grid(row=1, column=0, sticky="nsew", pady=20)
        self.center.grid_columnconfigure(0, weight=1)
        self.center.grid_rowconfigure(1, weight=1)

        input_f = ctk.CTkFrame(self.center, fg_color="transparent")
        input_f.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.path_var = ctk.StringVar(value="Select folder...")
        ctk.CTkEntry(input_f, textvariable=self.path_var).pack(
            side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(input_f, text="Browse", command=self.browse).pack(side="right")

        self.term = ctk.CTkTextbox(
            self.center, font=ctk.CTkFont(family="Consolas"),
            fg_color="#0a0a0a", text_color="#00FF41")
        self.term.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.term.configure(state="disabled")

        btns = ctk.CTkFrame(self.main, fg_color="transparent")
        btns.grid(row=2, column=0, sticky="ew")
        self.run_btn = ctk.CTkButton(
            btns, text="START SCAN", height=45,
            fg_color="#2ecc71", hover_color="#27ae60",
            font=ctk.CTkFont(weight="bold"), command=self.start)
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.ana_btn = ctk.CTkButton(
            btns, text="ANALYSIS", height=45, width=140,
            state="disabled", fg_color="#8e44ad", hover_color="#7d3c98",
            font=ctk.CTkFont(weight="bold"), command=self.show)
        self.ana_btn.pack(side="left", padx=(0, 10))

        ctk.CTkButton(btns, text="CLEAR", height=45, width=100,
                       fg_color="#e74c3c", hover_color="#c0392b",
                       command=self.clear).pack(side="right")

    # ── Proper shutdown ──
    def _on_exit(self):
        """Clean exit: close all analysis windows, free memory, terminate."""
        for win in self._analysis_windows:
            try:
                win._on_close()
            except Exception:
                pass
        self._analysis_windows.clear()
        self.results = []
        gc.collect()
        self.destroy()
        sys.exit(0)

    # ── callbacks ──
    def set_mode(self, mod):
        m = {"High Confidence": PredictionMode.HIGH_CONFIDENCE,
             "Medium Confidence": PredictionMode.MEDIUM_CONFIDENCE,
             "Best Guess": PredictionMode.BEST_GUESS}[mod]
        self.magika = Magika(prediction_mode=m)
        self.log(f"Mode → {mod}")

    def browse(self):
        f = filedialog.askdirectory()
        if f:
            self.path_var.set(f)

    def log(self, m):
        self.term.configure(state="normal")
        self.term.insert("end", f"[{time.strftime('%H:%M:%S')}] {m}\n")
        self.term.see("end")
        self.term.configure(state="disabled")

    def clear(self):
        self.term.configure(state="normal")
        self.term.delete("1.0", "end")
        self.term.configure(state="disabled")
        self.results = []
        self.ana_btn.configure(state="disabled")

    def start(self):
        p = self.path_var.get()
        if not os.path.isdir(p):
            return
        self.results = []
        self.run_btn.configure(state="disabled", text="SCANNING...")
        threading.Thread(target=self._scan, args=(p,), daemon=True).start()

    def _scan(self, p):
        files = [Path(r) / f for r, _, fs in os.walk(p) for f in fs]
        self.log(f"Found {len(files)} files. Scanning...")
        for fp in files:
            try:
                res = self.magika.identify_path(fp)
                if res.ok:
                    self.log(f"{fp.name}: {res.output.label} [{res.score:.2f}]")
                    self.results.append(res)
            except Exception as e:
                self.log(f"ERR {fp.name}: {e}")
        self.log(f"Done — {len(self.results)} files identified.")
        self.run_btn.configure(state="normal", text="START SCAN")
        self.ana_btn.configure(state="normal")

    def show(self):
        if self.results:
            win = AnalysisWindow(self, self.results)
            self._analysis_windows.append(win)


if __name__ == "__main__":
    app = MagikaGUI()
    app.mainloop()
