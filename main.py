"""
JAS - Just Automate Something
V1.0 | Desktop Automation Agent
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import time
from datetime import datetime
from llm import generate_plan, verify_execution
from executor import execute_plan, ExecutionResult
from logger import Logger
from history import HistoryManager

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#0F1117"
PANEL     = "#161B22"
CARD      = "#1C2333"
BORDER    = "#30363D"
ACCENT    = "#3B82F6"
ACCENT2   = "#6366F1"
SUCCESS   = "#22C55E"
WARNING   = "#F59E0B"
ERROR     = "#EF4444"
TEXT      = "#E6EDF3"
TEXT_DIM  = "#8B949E"
TEXT_MID  = "#C9D1D9"
FONT_MONO = ("JetBrains Mono", 10) if True else ("Courier New", 10)
FONT_UI   = ("Segoe UI", 10)
FONT_TITLE= ("Segoe UI Semibold", 11)


class StepCard(tk.Frame):
    """Single animated step card in the live visualizer."""

    STATUS_COLORS = {
        "pending":  (TEXT_DIM,  "○"),
        "running":  (ACCENT,    "◉"),
        "success":  (SUCCESS,   "✓"),
        "error":    (ERROR,     "✗"),
        "skipped":  (WARNING,   "–"),
    }

    def __init__(self, parent, index, step, **kw):
        super().__init__(parent, bg=CARD, **kw)
        self.index = index
        self.step  = step
        self._status = "pending"

        self.config(pady=6, padx=10, relief="flat")

        # indicator
        self.indicator = tk.Label(self, text="○", font=("Segoe UI", 13),
                                  fg=TEXT_DIM, bg=CARD, width=2)
        self.indicator.pack(side="left")

        # step label
        action = step.get("action", "?").upper()
        detail = self._describe(step)
        tk.Label(self, text=f"[{index+1}] {action}", font=("Segoe UI Semibold", 10),
                 fg=TEXT, bg=CARD).pack(side="left", padx=(4, 6))
        self.detail_lbl = tk.Label(self, text=detail, font=FONT_UI,
                                   fg=TEXT_DIM, bg=CARD)
        self.detail_lbl.pack(side="left")

        # separator line
        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x", side="bottom")

    def _describe(self, step):
        a = step.get("action", "")
        if a == "press":    return f'key: {step.get("key","")}'
        if a == "hotkey":   return f'keys: {" + ".join(step.get("keys", []))}'
        if a == "write":    return f'text: "{step.get("text","")}"'
        if a == "click":    return f'at ({step.get("x",0)}, {step.get("y",0)})'
        if a == "move":     return f'to ({step.get("x",0)}, {step.get("y",0)})'
        if a == "scroll":   return f'{step.get("clicks",3)} clicks'
        if a == "wait":     return f'{step.get("seconds",1)}s'
        if a == "screenshot": return "capture screen"
        return ""

    def set_status(self, status):
        self._status = status
        color, icon = self.STATUS_COLORS.get(status, (TEXT_DIM, "○"))
        self.indicator.config(text=icon, fg=color)
        if status == "running":
            self.config(bg="#1E2A3A")
            self.indicator.config(bg="#1E2A3A")
        elif status == "success":
            self.config(bg="#152A1E")
            self.indicator.config(bg="#152A1E")
        elif status == "error":
            self.config(bg="#2A1515")
            self.indicator.config(bg="#2A1515")


class JASApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JAS — Just Automate Something  v1.0")
        self.geometry("1080x700")
        self.minsize(860, 580)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.logger   = Logger()
        self.history  = HistoryManager()
        self._busy    = False
        self._step_cards = []

        self._build_ui()
        self._load_history()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Titlebar strip ─────────────────────────────────────────────────
        bar = tk.Frame(self, bg=PANEL, height=48)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        tk.Label(bar, text="⚡  JAS", font=("Segoe UI Semibold", 14),
                 fg=ACCENT, bg=PANEL).pack(side="left", padx=18, pady=10)
        tk.Label(bar, text="Just Automate Something", font=("Segoe UI", 10),
                 fg=TEXT_DIM, bg=PANEL).pack(side="left", pady=10)

        # status pill
        self.status_pill = tk.Label(bar, text="● Ready", font=("Segoe UI", 9),
                                    fg=SUCCESS, bg=PANEL, padx=10)
        self.status_pill.pack(side="right", padx=12)

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x")

        # ── Three-column body ───────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # Left: history sidebar
        sidebar = tk.Frame(body, bg=PANEL, width=220)
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="HISTORY", font=("Segoe UI Semibold", 9),
                 fg=TEXT_DIM, bg=PANEL).pack(anchor="w", padx=14, pady=(14, 6))

        self.hist_list = tk.Listbox(
            sidebar, bg=PANEL, fg=TEXT_MID, selectbackground=ACCENT,
            selectforeground=TEXT, relief="flat", bd=0,
            font=FONT_UI, activestyle="none", highlightthickness=0,
        )
        self.hist_list.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.hist_list.bind("<<ListboxSelect>>", self._on_history_select)

        tk.Button(sidebar, text="Clear History", font=("Segoe UI", 9),
                  bg=CARD, fg=TEXT_DIM, bd=0, relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT,
                  command=self._clear_history).pack(padx=10, pady=(0, 10), fill="x")

        vsep = tk.Frame(body, bg=BORDER, width=1)
        vsep.pack(fill="y", side="left")

        # Centre: main interaction
        centre = tk.Frame(body, bg=BG)
        centre.pack(fill="both", expand=True, side="left")

        # Input area
        input_frame = tk.Frame(centre, bg=PANEL)
        input_frame.pack(fill="x", padx=20, pady=18)

        tk.Label(input_frame, text="Command", font=FONT_TITLE,
                 fg=TEXT, bg=PANEL).pack(anchor="w", padx=14, pady=(12, 4))

        self.cmd_entry = tk.Text(
            input_frame, height=3, bg=CARD, fg=TEXT,
            insertbackground=ACCENT, font=FONT_UI,
            relief="flat", bd=0, padx=12, pady=10,
            wrap="word", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
        )
        self.cmd_entry.pack(fill="x", padx=14, pady=(0, 10))
        self.cmd_entry.bind("<Return>", self._on_enter)
        self.cmd_entry.bind("<Shift-Return>", lambda e: None)  # allow newline

        # placeholder
        self._placeholder = "e.g. Open Notepad and type Hello World"
        self._show_placeholder()
        self.cmd_entry.bind("<FocusIn>",  self._hide_placeholder)
        self.cmd_entry.bind("<FocusOut>", self._show_placeholder)

        btn_row = tk.Frame(input_frame, bg=PANEL)
        btn_row.pack(fill="x", padx=14, pady=(0, 14))

        self.run_btn = tk.Button(
            btn_row, text="▶  Run", font=("Segoe UI Semibold", 10),
            bg=ACCENT, fg="white", relief="flat", bd=0, padx=18, pady=7,
            cursor="hand2", activebackground=ACCENT2, activeforeground="white",
            command=self._run,
        )
        self.run_btn.pack(side="left")

        self.auto_exec_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            btn_row, text="Auto-execute (skip confirm)", font=("Segoe UI", 9),
            variable=self.auto_exec_var, fg=TEXT_DIM, bg=PANEL,
            selectcolor=CARD, activebackground=PANEL, activeforeground=TEXT,
        ).pack(side="left", padx=14)

        self.retry_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            btn_row, text="Self-healing retry", font=("Segoe UI", 9),
            variable=self.retry_var, fg=TEXT_DIM, bg=PANEL,
            selectcolor=CARD, activebackground=PANEL, activeforeground=TEXT,
        ).pack(side="left")

        # Live step visualizer
        viz_header = tk.Frame(centre, bg=BG)
        viz_header.pack(fill="x", padx=20, pady=(0, 6))
        tk.Label(viz_header, text="EXECUTION PLAN", font=("Segoe UI Semibold", 9),
                 fg=TEXT_DIM, bg=BG).pack(side="left")
        self.step_count_lbl = tk.Label(viz_header, text="", font=("Segoe UI", 9),
                                        fg=TEXT_DIM, bg=BG)
        self.step_count_lbl.pack(side="right")

        viz_outer = tk.Frame(centre, bg=CARD, relief="flat",
                             highlightthickness=1, highlightbackground=BORDER)
        viz_outer.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.viz_canvas = tk.Canvas(viz_outer, bg=CARD, bd=0,
                                    highlightthickness=0)
        viz_scroll = ttk.Scrollbar(viz_outer, orient="vertical",
                                   command=self.viz_canvas.yview)
        self.viz_canvas.configure(yscrollcommand=viz_scroll.set)
        viz_scroll.pack(side="right", fill="y")
        self.viz_canvas.pack(side="left", fill="both", expand=True)

        self.viz_inner = tk.Frame(self.viz_canvas, bg=CARD)
        self.viz_win = self.viz_canvas.create_window(
            (0, 0), window=self.viz_inner, anchor="nw")
        self.viz_inner.bind("<Configure>", self._on_viz_configure)
        self.viz_canvas.bind("<Configure>",
                             lambda e: self.viz_canvas.itemconfig(
                                 self.viz_win, width=e.width))

        # empty state
        self.viz_empty = tk.Label(
            self.viz_inner,
            text="No plan yet.\nType a command above and press Run.",
            font=FONT_UI, fg=TEXT_DIM, bg=CARD, pady=40,
        )
        self.viz_empty.pack()

        vsep2 = tk.Frame(body, bg=BORDER, width=1)
        vsep2.pack(fill="y", side="left")

        # Right: log panel
        right = tk.Frame(body, bg=PANEL, width=300)
        right.pack(fill="y", side="right")
        right.pack_propagate(False)

        tk.Label(right, text="LOG", font=("Segoe UI Semibold", 9),
                 fg=TEXT_DIM, bg=PANEL).pack(anchor="w", padx=14, pady=(14, 6))

        self.log_box = scrolledtext.ScrolledText(
            right, bg=BG, fg=TEXT_DIM, font=FONT_MONO,
            relief="flat", bd=0, state="disabled",
            wrap="word", padx=10, pady=8,
        )
        self.log_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # tag colours
        for tag, color in [("info", TEXT_DIM), ("success", SUCCESS),
                            ("error", ERROR), ("warn", WARNING),
                            ("accent", ACCENT), ("step", TEXT_MID)]:
            self.log_box.tag_config(tag, foreground=color)

        tk.Button(right, text="Export Log", font=("Segoe UI", 9),
                  bg=CARD, fg=TEXT_DIM, bd=0, relief="flat", cursor="hand2",
                  activebackground=BORDER, activeforeground=TEXT,
                  command=self._export_log).pack(padx=10, pady=(0, 10), fill="x")

    # ── Placeholder helpers ───────────────────────────────────────────────────

    def _show_placeholder(self, *_):
        if not self.cmd_entry.get("1.0", "end-1c").strip():
            self.cmd_entry.insert("1.0", self._placeholder)
            self.cmd_entry.config(fg=TEXT_DIM)

    def _hide_placeholder(self, *_):
        if self.cmd_entry.get("1.0", "end-1c") == self._placeholder:
            self.cmd_entry.delete("1.0", "end")
            self.cmd_entry.config(fg=TEXT)

    # ── Core Run Flow ─────────────────────────────────────────────────────────

    def _on_enter(self, event):
        if not event.state & 0x1:   # Shift not held
            self._run()
            return "break"

    def _run(self):
        if self._busy:
            return
        cmd = self.cmd_entry.get("1.0", "end-1c").strip()
        if not cmd or cmd == self._placeholder:
            self._log("⚠  Enter a command first.", "warn")
            return

        self._busy = True
        self._set_status("thinking")
        self._clear_viz()
        threading.Thread(target=self._worker, args=(cmd,), daemon=True).start()

    def _worker(self, cmd):
        self._log(f"\n▶  {cmd}", "accent")
        try:
            # ── 1. Generate plan ──────────────────────────────────────────
            self._log("Generating plan...", "info")
            plan = generate_plan(cmd)
            steps = plan.get("steps", [])

            if not steps:
                self._log("LLM returned empty plan.", "error")
                self._set_status("error")
                self._busy = False
                return

            self.after(0, self._render_plan, steps)
            self._log(f"Plan ready — {len(steps)} step(s).", "success")

            # ── 2. Confirm ────────────────────────────────────────────────
            if not self.auto_exec_var.get():
                proceed = self._ask_confirm(len(steps))
                if not proceed:
                    self._log("Execution cancelled.", "warn")
                    self._set_status("ready")
                    self._busy = False
                    return

            # ── 3. Execute ────────────────────────────────────────────────
            self._set_status("running")
            self._log("Executing...", "info")
            result = execute_plan(plan, step_callback=self._on_step_update)

            # ── 4. Self-healing retry ─────────────────────────────────────
            attempt = 1
            while (not result.success and self.retry_var.get()
                   and attempt < 3):
                self._log(
                    f"⚠  Step {result.failed_step+1} failed: {result.error}\n"
                    f"   Self-healing — attempt {attempt+1}/3...", "warn")
                healed_plan = generate_plan(
                    cmd,
                    error_context={
                        "failed_step": result.failed_step,
                        "error":       result.error,
                        "original_plan": plan,
                    }
                )
                self.after(0, self._render_plan, healed_plan.get("steps", []))
                result = execute_plan(healed_plan,
                                      step_callback=self._on_step_update)
                plan = healed_plan
                attempt += 1

            # ── 5. Screenshot verification ────────────────────────────────
            if result.screenshot_path:
                self._log("Verifying result with screenshot...", "info")
                verdict = verify_execution(cmd, result.screenshot_path)
                if verdict.get("success"):
                    self._log(f"✓  Verified: {verdict.get('note','')}", "success")
                else:
                    self._log(f"⚠  Verification note: {verdict.get('note','')}", "warn")

            # ── 6. Done ───────────────────────────────────────────────────
            if result.success:
                self._log("✓  Done.", "success")
                self._set_status("ready")
                self.after(0, self.history.add, cmd)
                self.after(0, self._load_history)
            else:
                self._log(f"✗  Failed after {attempt} attempt(s).", "error")
                self._set_status("error")

        except Exception as e:
            self._log(f"✗  {e}", "error")
            self._set_status("error")
        finally:
            self._busy = False

    # ── Step callback (called from executor thread) ───────────────────────────

    def _on_step_update(self, index, status, detail=""):
        def _update():
            if index < len(self._step_cards):
                self._step_cards[index].set_status(status)
            if detail:
                tag = "error" if status == "error" else "step"
                self._log(f"  [{index+1}] {status}: {detail}", tag)
        self.after(0, _update)

    # ── Confirmation dialog ───────────────────────────────────────────────────

    def _ask_confirm(self, n_steps):
        result = [False]
        ev = threading.Event()

        def _dialog():
            ans = messagebox.askyesno(
                "Execute Plan",
                f"Ready to run {n_steps} step(s).\n\nProceed?",
                parent=self,
            )
            result[0] = ans
            ev.set()

        self.after(0, _dialog)
        ev.wait()
        return result[0]

    # ── Visualizer rendering ──────────────────────────────────────────────────

    def _render_plan(self, steps):
        for w in self.viz_inner.winfo_children():
            w.destroy()
        self._step_cards.clear()

        if not steps:
            tk.Label(self.viz_inner, text="Empty plan.", font=FONT_UI,
                     fg=TEXT_DIM, bg=CARD, pady=30).pack()
            return

        self.step_count_lbl.config(text=f"{len(steps)} steps")

        for i, step in enumerate(steps):
            card = StepCard(self.viz_inner, i, step)
            card.pack(fill="x", padx=4, pady=2)
            self._step_cards.append(card)

    def _clear_viz(self):
        for w in self.viz_inner.winfo_children():
            w.destroy()
        self._step_cards.clear()
        self.step_count_lbl.config(text="")
        self.viz_empty = tk.Label(
            self.viz_inner,
            text="Generating plan...",
            font=FONT_UI, fg=TEXT_DIM, bg=CARD, pady=40,
        )
        self.viz_empty.pack()

    def _on_viz_configure(self, _):
        self.viz_canvas.configure(
            scrollregion=self.viz_canvas.bbox("all"))

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"{ts}  {msg}\n"
        self.logger.write(line)

        def _append():
            self.log_box.config(state="normal")
            self.log_box.insert("end", line, tag)
            self.log_box.see("end")
            self.log_box.config(state="disabled")

        self.after(0, _append)

    def _export_log(self):
        path = self.logger.export()
        self._log(f"Log exported → {path}", "success")

    # ── Status pill ───────────────────────────────────────────────────────────

    def _set_status(self, state):
        configs = {
            "ready":    ("● Ready",   SUCCESS),
            "thinking": ("◌ Thinking", ACCENT),
            "running":  ("◉ Running",  WARNING),
            "error":    ("✗ Error",    ERROR),
        }
        text, color = configs.get(state, ("●", TEXT_DIM))
        self.after(0, lambda: self.status_pill.config(text=text, fg=color))

    # ── History ───────────────────────────────────────────────────────────────

    def _load_history(self):
        self.hist_list.delete(0, "end")
        for item in reversed(self.history.get_all()):
            short = item[:28] + "…" if len(item) > 29 else item
            self.hist_list.insert("end", short)

    def _on_history_select(self, _):
        sel = self.hist_list.curselection()
        if not sel:
            return
        items = list(reversed(self.history.get_all()))
        cmd = items[sel[0]]
        self._hide_placeholder()
        self.cmd_entry.delete("1.0", "end")
        self.cmd_entry.insert("1.0", cmd)

    def _clear_history(self):
        self.history.clear()
        self._load_history()


if __name__ == "__main__":
    app = JASApp()
    app.mainloop()
