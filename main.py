"""
JAS — Just Automate Something
Modern Desktop Automation Agent Dashboard

UI redesigned without changing the core automation pipeline.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import threading
from datetime import datetime

from llm import generate_plan, verify_execution
from executor import execute_plan
from logger import Logger
from history import HistoryManager


# ============================================================
# THEME
# ============================================================

BG = "#05071A"
HEADER_BG = "#090B24"
PANEL = "#090D2B"
PANEL_ALT = "#0C1238"
CARD = "#0D143D"
CARD_HOVER = "#111B4D"

BORDER = "#26318C"
BORDER_DIM = "#18225F"

PURPLE = "#7C3AED"
PURPLE_LIGHT = "#A855F7"
BLUE = "#4F6BFF"

SUCCESS = "#19D98B"
WARNING = "#F5B942"
ERROR = "#FF5C7A"

TEXT = "#F3F5FF"
TEXT_MID = "#B6BCE0"
TEXT_DIM = "#737CA8"

FONT_UI = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI Semibold", 11)
FONT_HEADING = ("Segoe UI Semibold", 15)


# ============================================================
# UTILITY
# ============================================================

def shorten(text, length=38):
    if len(text) <= length:
        return text
    return text[:length] + "..."


# ============================================================
# MODERN BUTTON
# ============================================================

class ModernButton(tk.Label):

    def __init__(
        self,
        parent,
        text,
        command=None,
        bg=PURPLE,
        hover=PURPLE_LIGHT,
        fg="white",
        font=("Segoe UI Semibold", 10),
        padx=14,
        pady=8,
    ):
        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=font,
            padx=padx,
            pady=pady,
            cursor="hand2",
        )

        self.command = command
        self.normal_bg = bg
        self.hover_bg = hover

        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", self._click)

    def _enter(self, _):
        self.configure(bg=self.hover_bg)

    def _leave(self, _):
        self.configure(bg=self.normal_bg)

    def _click(self, _):
        if self.command:
            self.command()


# ============================================================
# EXECUTION STEP
# ============================================================

class StepCard(tk.Frame):

    STATUS = {
        "pending": (TEXT_DIM, "○"),
        "running": (BLUE, "◉"),
        "success": (SUCCESS, "✓"),
        "error": (ERROR, "✕"),
        "skipped": (WARNING, "−"),
    }

    def __init__(self, parent, index, step, **kwargs):

        super().__init__(
            parent,
            bg=PANEL_ALT,
            **kwargs
        )

        self.index = index
        self.step = step

        self.configure(
            padx=12,
            pady=7
        )

        # STATUS INDICATOR

        self.indicator = tk.Label(
            self,
            text="○",
            font=("Segoe UI Semibold", 12),
            fg=TEXT_DIM,
            bg=PANEL_ALT,
            width=2,
        )

        self.indicator.pack(side="left")

        # DESCRIPTION

        action = step.get("action", "step")

        description = self._describe(step)

        self.text_label = tk.Label(
            self,
            text=f"{action.title()} {description}",
            font=FONT_SMALL,
            fg=TEXT_MID,
            bg=PANEL_ALT,
            anchor="w",
        )

        self.text_label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(5, 0),
        )

    def _describe(self, step):

        action = step.get("action", "")

        if action == "press":
            return f'{step.get("key", "")}'

        if action == "hotkey":
            return " + ".join(step.get("keys", []))

        if action == "write":
            return f'"{shorten(step.get("text", ""), 35)}"'

        if action == "click":
            return f'at ({step.get("x", 0)}, {step.get("y", 0)})'

        if action == "move":
            return f'to ({step.get("x", 0)}, {step.get("y", 0)})'

        if action == "scroll":
            return f'{step.get("clicks", 3)} clicks'

        if action == "wait":
            return f'{step.get("seconds", 1)} seconds'

        if action == "screenshot":
            return "screen"

        return ""

    def set_status(self, status):

        color, icon = self.STATUS.get(
            status,
            (TEXT_DIM, "○")
        )

        self.indicator.configure(
            text=icon,
            fg=color
        )

        if status == "running":

            bg = "#101D4D"

        elif status == "success":

            bg = "#0B2B29"

        elif status == "error":

            bg = "#321426"

        else:

            bg = PANEL_ALT

        self.configure(bg=bg)

        self.indicator.configure(bg=bg)

        self.text_label.configure(bg=bg)


# ============================================================
# MAIN APPLICATION
# ============================================================

class JASApp(tk.Tk):

    def __init__(self):

        super().__init__()

        # WINDOW

        self.title("JAS")

        self.geometry("1180x720")

        self.minsize(980, 620)

        self.configure(bg=BG)

        # BACKEND

        self.logger = Logger()

        self.history = HistoryManager()

        self._busy = False

        self._step_cards = []

        self._current_command = ""

        # BUILD

        self._build_ui()

        self._load_history()


    # ========================================================
    # MAIN UI
    # ========================================================

    def _build_ui(self):

        # ROOT GRID

        self.grid_rowconfigure(
            1,
            weight=1
        )

        self.grid_columnconfigure(
            0,
            weight=1
        )


        # ====================================================
        # HEADER
        # ====================================================

        header = tk.Frame(
            self,
            bg=HEADER_BG,
            height=58
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        header.grid_propagate(False)


        # LOGO

        logo_box = tk.Frame(
            header,
            bg=HEADER_BG
        )

        logo_box.pack(
            side="left",
            padx=18
        )


        logo = tk.Label(
            logo_box,
            text="✦",
            font=("Segoe UI", 22),
            fg=PURPLE_LIGHT,
            bg=HEADER_BG
        )

        logo.pack(
            side="left"
        )


        tk.Label(
            logo_box,
            text="JAS",
            font=("Segoe UI Semibold", 17),
            fg=TEXT,
            bg=HEADER_BG
        ).pack(
            side="left",
            padx=(10, 0)
        )


        tk.Label(
            logo_box,
            text="JUST AUTOMATE SOMETHING",
            font=("Segoe UI", 8),
            fg=TEXT_DIM,
            bg=HEADER_BG
        ).pack(
            side="left",
            padx=(12, 0),
            pady=(6, 0)
        )


        # STATUS

        self.status_pill = tk.Label(
            header,
            text="●  Ready",
            font=FONT_SMALL,
            fg=SUCCESS,
            bg=HEADER_BG,
            padx=12
        )

        self.status_pill.pack(
            side="right",
            padx=18
        )


        # ====================================================
        # MAIN BODY
        # ====================================================

        body = tk.Frame(
            self,
            bg=BG
        )

        body.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=14,
            pady=14
        )

        body.grid_rowconfigure(
            0,
            weight=1
        )

        body.grid_columnconfigure(
            0,
            weight=4
        )

        body.grid_columnconfigure(
            1,
            weight=7
        )


        # ====================================================
        # LEFT PANEL
        # ====================================================

        left = tk.Frame(
            body,
            bg=PANEL,
            highlightthickness=1,
            highlightbackground=BORDER
        )

        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 7)
        )


        # ----------------------------------------------------
        # USER SECTION
        # ----------------------------------------------------

        user_section = tk.Frame(
            left,
            bg=PANEL
        )

        user_section.pack(
            fill="x",
            padx=18,
            pady=(18, 10)
        )


        avatar = tk.Label(
            user_section,
            text="●",
            font=("Segoe UI", 26),
            fg=PURPLE_LIGHT,
            bg=PANEL
        )

        avatar.pack(
            side="left"
        )


        user_text = tk.Frame(
            user_section,
            bg=PANEL
        )

        user_text.pack(
            side="left",
            padx=10
        )


        tk.Label(
            user_text,
            text="AUTOMATION COMMAND",
            font=("Segoe UI Semibold", 9),
            fg=TEXT,
            bg=PANEL
        ).pack(
            anchor="w"
        )


        tk.Label(
            user_text,
            text="Tell JAS what you want to automate",
            font=("Segoe UI", 8),
            fg=TEXT_DIM,
            bg=PANEL
        ).pack(
            anchor="w"
        )


        # ----------------------------------------------------
        # CURRENT COMMAND CARD
        # ----------------------------------------------------

        command_card = tk.Frame(
            left,
            bg=PANEL_ALT,
            highlightthickness=1,
            highlightbackground=BORDER_DIM
        )

        command_card.pack(
            fill="x",
            padx=18,
            pady=(8, 14)
        )


        self.current_command_label = tk.Label(
            command_card,
            text="Waiting for your command...",
            font=("Segoe UI", 11),
            fg=TEXT_MID,
            bg=PANEL_ALT,
            wraplength=330,
            justify="left",
            anchor="w",
            padx=14,
            pady=14
        )

        self.current_command_label.pack(
            fill="x"
        )


        # ----------------------------------------------------
        # JAS EXECUTION PANEL
        # ----------------------------------------------------

        agent_header = tk.Frame(
            left,
            bg=PANEL
        )

        agent_header.pack(
            fill="x",
            padx=18,
            pady=(4, 8)
        )


        tk.Label(
            agent_header,
            text="✦",
            font=("Segoe UI", 18),
            fg=PURPLE_LIGHT,
            bg=PANEL
        ).pack(
            side="left"
        )


        tk.Label(
            agent_header,
            text="JAS",
            font=("Segoe UI Semibold", 11),
            fg=TEXT,
            bg=PANEL
        ).pack(
            side="left",
            padx=8
        )


        self.step_count_lbl = tk.Label(
            agent_header,
            text="",
            font=("Segoe UI", 8),
            fg=TEXT_DIM,
            bg=PANEL
        )

        self.step_count_lbl.pack(
            side="right"
        )


        # ----------------------------------------------------
        # EXECUTION CANVAS
        # ----------------------------------------------------

        execution_outer = tk.Frame(
            left,
            bg=PANEL_ALT,
            highlightthickness=1,
            highlightbackground=BORDER_DIM
        )

        execution_outer.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 14)
        )


        self.viz_canvas = tk.Canvas(
            execution_outer,
            bg=PANEL_ALT,
            highlightthickness=0,
            bd=0
        )

        scrollbar = tk.Scrollbar(
            execution_outer,
            orient="vertical",
            command=self.viz_canvas.yview
        )


        self.viz_canvas.configure(
            yscrollcommand=scrollbar.set
        )


        scrollbar.pack(
            side="right",
            fill="y"
        )


        self.viz_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )


        self.viz_inner = tk.Frame(
            self.viz_canvas,
            bg=PANEL_ALT
        )


        self.viz_win = self.viz_canvas.create_window(
            (0, 0),
            window=self.viz_inner,
            anchor="nw"
        )


        self.viz_inner.bind(
            "<Configure>",
            self._on_viz_configure
        )


        self.viz_canvas.bind(
            "<Configure>",
            lambda event:
            self.viz_canvas.itemconfig(
                self.viz_win,
                width=event.width
            )
        )


        self.viz_empty = tk.Label(
            self.viz_inner,
            text=(
                "JAS is ready.\n\n"
                "Enter a natural language command\n"
                "to begin automation."
            ),
            font=FONT_UI,
            fg=TEXT_DIM,
            bg=PANEL_ALT,
            justify="center",
            pady=50
        )

        self.viz_empty.pack(
            fill="both",
            expand=True
        )


        # ====================================================
        # COMMAND INPUT
        # ====================================================

        command_input = tk.Frame(
            left,
            bg=CARD,
            highlightthickness=1,
            highlightbackground=BORDER
        )

        command_input.pack(
            fill="x",
            padx=18,
            pady=(0, 18)
        )


        tk.Label(
            command_input,
            text="🎙",
            font=("Segoe UI", 13),
            fg=TEXT_DIM,
            bg=CARD
        ).pack(
            side="left",
            padx=(12, 4)
        )


        self.cmd_entry = tk.Entry(
            command_input,
            bg=CARD,
            fg=TEXT,
            insertbackground=PURPLE_LIGHT,
            font=FONT_UI,
            relief="flat",
            bd=0
        )

        self.cmd_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=12,
            padx=5
        )


        self._placeholder = (
            "Type a task in natural language..."
        )

        self._show_placeholder()


        self.cmd_entry.bind(
            "<FocusIn>",
            self._hide_placeholder
        )

        self.cmd_entry.bind(
            "<FocusOut>",
            self._show_placeholder
        )

        self.cmd_entry.bind(
            "<Return>",
            self._on_enter
        )


        self.run_btn = ModernButton(
            command_input,
            text="➜",
            command=self._run,
            padx=15,
            pady=9
        )

        self.run_btn.pack(
            side="right",
            padx=5,
            pady=5
        )


        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right = tk.Frame(
            body,
            bg=PANEL,
            highlightthickness=1,
            highlightbackground=BORDER
        )

        right.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(7, 0)
        )


        # ----------------------------------------------------
        # WORKSPACE HEADER
        # ----------------------------------------------------

        workspace_header = tk.Frame(
            right,
            bg=PANEL_ALT,
            height=48
        )

        workspace_header.pack(
            fill="x"
        )

        workspace_header.pack_propagate(False)


        tk.Label(
            workspace_header,
            text="●",
            font=("Segoe UI", 13),
            fg=SUCCESS,
            bg=PANEL_ALT
        ).pack(
            side="left",
            padx=(16, 8)
        )


        tk.Label(
            workspace_header,
            text="AUTOMATION WORKSPACE",
            font=("Segoe UI Semibold", 10),
            fg=TEXT,
            bg=PANEL_ALT
        ).pack(
            side="left"
        )


        self.workspace_status = tk.Label(
            workspace_header,
            text="IDLE",
            font=("Segoe UI Semibold", 8),
            fg=TEXT_DIM,
            bg=PANEL_ALT
        )

        self.workspace_status.pack(
            side="right",
            padx=16
        )


        # ----------------------------------------------------
        # MAIN WORKSPACE
        # ----------------------------------------------------

        workspace = tk.Frame(
            right,
            bg=PANEL
        )

        workspace.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )


        # ----------------------------------------------------
        # AUTOMATION STATUS
        # ----------------------------------------------------

        status_card = tk.Frame(
            workspace,
            bg=PANEL_ALT,
            highlightthickness=1,
            highlightbackground=BORDER_DIM
        )

        status_card.pack(
            fill="x",
            pady=(0, 14)
        )


        tk.Label(
            status_card,
            text="CURRENT ACTIVITY",
            font=("Segoe UI Semibold", 8),
            fg=TEXT_DIM,
            bg=PANEL_ALT
        ).pack(
            anchor="w",
            padx=16,
            pady=(14, 6)
        )


        self.activity_label = tk.Label(
            status_card,
            text="Waiting for a task",
            font=("Segoe UI Semibold", 16),
            fg=TEXT,
            bg=PANEL_ALT
        )

        self.activity_label.pack(
            anchor="w",
            padx=16
        )


        self.activity_description = tk.Label(
            status_card,
            text=(
                "Enter a command and JAS will "
                "generate an execution plan."
            ),
            font=FONT_SMALL,
            fg=TEXT_DIM,
            bg=PANEL_ALT,
            wraplength=550,
            justify="left"
        )

        self.activity_description.pack(
            anchor="w",
            padx=16,
            pady=(5, 14)
        )


        # ----------------------------------------------------
        # ACTIVITY LOG HEADER
        # ----------------------------------------------------

        log_header = tk.Frame(
            workspace,
            bg=PANEL
        )

        log_header.pack(
            fill="x",
            pady=(4, 7)
        )


        tk.Label(
            log_header,
            text="ACTIVITY STREAM",
            font=("Segoe UI Semibold", 9),
            fg=TEXT_DIM,
            bg=PANEL
        ).pack(
            side="left"
        )


        ModernButton(
            log_header,
            text="Export",
            command=self._export_log,
            bg=CARD,
            hover=CARD_HOVER,
            fg=TEXT_DIM,
            font=("Segoe UI", 8),
            padx=10,
            pady=4
        ).pack(
            side="right"
        )


        # ----------------------------------------------------
        # LOG BOX
        # ----------------------------------------------------

        self.log_box = tk.Text(
            workspace,
            bg=BG,
            fg=TEXT_DIM,
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            state="disabled",
            wrap="word",
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground=BORDER_DIM
        )

        self.log_box.pack(
            fill="both",
            expand=True
        )


        # LOG COLORS

        for tag, color in [

            ("info", TEXT_DIM),

            ("success", SUCCESS),

            ("error", ERROR),

            ("warn", WARNING),

            ("accent", PURPLE_LIGHT),

            ("step", TEXT_MID),

        ]:

            self.log_box.tag_config(
                tag,
                foreground=color
            )


        # ----------------------------------------------------
        # BOTTOM CONTROLS
        # ----------------------------------------------------

        controls = tk.Frame(
            workspace,
            bg=PANEL
        )

        controls.pack(
            fill="x",
            pady=(12, 0)
        )


        self.auto_exec_var = tk.BooleanVar(
            value=False
        )

        tk.Checkbutton(
            controls,
            text="Auto Execute",
            font=FONT_SMALL,
            variable=self.auto_exec_var,
            fg=TEXT_DIM,
            bg=PANEL,
            selectcolor=CARD,
            activebackground=PANEL,
            activeforeground=TEXT
        ).pack(
            side="left"
        )


        self.retry_var = tk.BooleanVar(
            value=True
        )

        tk.Checkbutton(
            controls,
            text="Self-Healing",
            font=FONT_SMALL,
            variable=self.retry_var,
            fg=TEXT_DIM,
            bg=PANEL,
            selectcolor=CARD,
            activebackground=PANEL,
            activeforeground=TEXT
        ).pack(
            side="left",
            padx=14
        )


        ModernButton(
            controls,
            text="History",
            command=self._open_history,
            bg=CARD,
            hover=CARD_HOVER,
            fg=TEXT_MID,
            font=FONT_SMALL,
            padx=12,
            pady=5
        ).pack(
            side="right"
        )


    # ========================================================
    # PLACEHOLDER
    # ========================================================

    def _show_placeholder(self, *_):

        if not self.cmd_entry.get().strip():

            self.cmd_entry.insert(
                0,
                self._placeholder
            )

            self.cmd_entry.configure(
                fg=TEXT_DIM
            )


    def _hide_placeholder(self, *_):

        if self.cmd_entry.get() == self._placeholder:

            self.cmd_entry.delete(
                0,
                "end"
            )

            self.cmd_entry.configure(
                fg=TEXT
            )


    # ========================================================
    # ENTER KEY
    # ========================================================

    def _on_enter(self, _):

        self._run()

        return "break"


    # ========================================================
    # RUN
    # ========================================================

    def _run(self):

        if self._busy:

            return


        command = self.cmd_entry.get().strip()


        if (
            not command
            or command == self._placeholder
        ):

            self._log(
                "Enter a command first.",
                "warn"
            )

            return


        self._current_command = command

        self.current_command_label.configure(
            text=command,
            fg=TEXT
        )


        self._busy = True


        self._set_status(
            "thinking"
        )


        self._clear_viz()


        threading.Thread(

            target=self._worker,

            args=(command,),

            daemon=True

        ).start()


    # ========================================================
    # WORKER
    # ========================================================

    def _worker(self, cmd):

        self._log(
            f"\n▶  {cmd}",
            "accent"
        )

        try:

            # ------------------------------------------------
            # GENERATE PLAN
            # ------------------------------------------------

            self._update_activity(

                "Understanding request",

                "JAS is analyzing your command "
                "and generating an automation plan."
            )


            self._log(
                "Generating plan...",
                "info"
            )


            plan = generate_plan(cmd)


            steps = plan.get(
                "steps",
                []
            )


            if not steps:

                self._log(
                    "LLM returned empty plan.",
                    "error"
                )

                self._set_status(
                    "error"
                )

                return


            self.after(
                0,
                self._render_plan,
                steps
            )


            self._log(
                f"Plan ready — {len(steps)} step(s).",
                "success"
            )


            # ------------------------------------------------
            # CONFIRM
            # ------------------------------------------------

            if not self.auto_exec_var.get():

                proceed = self._ask_confirm(
                    len(steps)
                )


                if not proceed:

                    self._log(
                        "Execution cancelled.",
                        "warn"
                    )

                    self._set_status(
                        "ready"
                    )

                    return


            # ------------------------------------------------
            # EXECUTE
            # ------------------------------------------------

            self._set_status(
                "running"
            )


            self._update_activity(

                "Automating task",

                f"Executing {len(steps)} planned actions."
            )


            self._log(
                "Executing...",
                "info"
            )


            result = execute_plan(

                plan,

                step_callback=self._on_step_update

            )


            # ------------------------------------------------
            # SELF HEALING
            # ------------------------------------------------

            attempt = 1


            while (

                not result.success

                and self.retry_var.get()

                and attempt < 3

            ):

                self._log(

                    f"Step {result.failed_step + 1} failed: "
                    f"{result.error}\n"
                    f"Self-healing attempt "
                    f"{attempt + 1}/3...",

                    "warn"

                )


                self._update_activity(

                    "Self-healing",

                    "JAS detected an execution failure "
                    "and is generating a recovery plan."
                )


                healed_plan = generate_plan(

                    cmd,

                    error_context={

                        "failed_step":
                            result.failed_step,

                        "error":
                            result.error,

                        "original_plan":
                            plan,

                    }

                )


                self.after(

                    0,

                    self._render_plan,

                    healed_plan.get(
                        "steps",
                        []
                    )

                )


                result = execute_plan(

                    healed_plan,

                    step_callback=
                        self._on_step_update

                )


                plan = healed_plan

                attempt += 1


            # ------------------------------------------------
            # VERIFICATION
            # ------------------------------------------------

            if result.screenshot_path:

                self._update_activity(

                    "Verifying execution",

                    "Analyzing the final screenshot "
                    "to verify task completion."
                )


                self._log(

                    "Verifying result with screenshot...",

                    "info"

                )


                verdict = verify_execution(

                    cmd,

                    result.screenshot_path

                )


                if verdict.get("success"):

                    self._log(

                        f"✓ Verified: "
                        f"{verdict.get('note', '')}",

                        "success"

                    )

                else:

                    self._log(

                        f"Verification note: "
                        f"{verdict.get('note', '')}",

                        "warn"

                    )


            # ------------------------------------------------
            # COMPLETE
            # ------------------------------------------------

            if result.success:

                self._log(
                    "✓ Done.",
                    "success"
                )


                self._update_activity(

                    "Task completed",

                    "JAS successfully completed "
                    "the requested automation."
                )


                self._set_status(
                    "ready"
                )


                self.after(
                    0,
                    self.history.add,
                    cmd
                )


                self.after(
                    0,
                    self._load_history
                )


            else:

                self._log(

                    f"Failed after "
                    f"{attempt} attempt(s).",

                    "error"

                )


                self._update_activity(

                    "Execution failed",

                    "JAS could not complete the task "
                    "after multiple attempts."
                )


                self._set_status(
                    "error"
                )


        except Exception as error:

            self._log(
                f"✗ {error}",
                "error"
            )


            self._update_activity(

                "Unexpected error",

                str(error)
            )


            self._set_status(
                "error"
            )


        finally:

            self._busy = False


    # ========================================================
    # STEP CALLBACK
    # ========================================================

    def _on_step_update(
        self,
        index,
        status,
        detail=""
    ):

        def update():

            if index < len(
                self._step_cards
            ):

                self._step_cards[
                    index
                ].set_status(status)


            if status == "running":

                self.activity_label.configure(

                    text=(
                        f"Executing step "
                        f"{index + 1}"
                    )

                )


            if detail:

                tag = (

                    "error"

                    if status == "error"

                    else "step"

                )


                self._log(

                    f"[{index + 1}] "
                    f"{status}: {detail}",

                    tag

                )


        self.after(
            0,
            update
        )


    # ========================================================
    # CONFIRMATION
    # ========================================================

    def _ask_confirm(
        self,
        n_steps
    ):

        result = [False]

        event = threading.Event()


        def dialog():

            result[0] = (
                messagebox.askyesno(

                    "Execute Automation",

                    f"JAS generated "
                    f"{n_steps} actions.\n\n"
                    f"Start automation?",

                    parent=self

                )
            )

            event.set()


        self.after(
            0,
            dialog
        )


        event.wait()


        return result[0]


    # ========================================================
    # PLAN RENDERING
    # ========================================================

    def _render_plan(
        self,
        steps
    ):

        for widget in (
            self.viz_inner.winfo_children()
        ):

            widget.destroy()


        self._step_cards.clear()


        if not steps:

            return


        self.step_count_lbl.configure(

            text=f"{len(steps)} STEPS"
        )


        for index, step in enumerate(steps):

            card = StepCard(

                self.viz_inner,

                index,

                step

            )


            card.pack(

                fill="x",

                padx=6,

                pady=3

            )


            self._step_cards.append(
                card
            )


    # ========================================================
    # CLEAR VISUALIZER
    # ========================================================

    def _clear_viz(self):

        for widget in (
            self.viz_inner.winfo_children()
        ):

            widget.destroy()


        self._step_cards.clear()


        self.step_count_lbl.configure(
            text=""
        )


        tk.Label(

            self.viz_inner,

            text=(
                "✦\n\n"
                "JAS is generating "
                "an execution plan..."
            ),

            font=FONT_UI,

            fg=PURPLE_LIGHT,

            bg=PANEL_ALT,

            pady=50

        ).pack()


    # ========================================================
    # CANVAS CONFIG
    # ========================================================

    def _on_viz_configure(
        self,
        _
    ):

        self.viz_canvas.configure(

            scrollregion=
                self.viz_canvas.bbox("all")

        )


    # ========================================================
    # LOG
    # ========================================================

    def _log(
        self,
        msg,
        tag="info"
    ):

        timestamp = (
            datetime.now().strftime(
                "%H:%M:%S"
            )
        )


        line = (
            f"{timestamp}  {msg}\n"
        )


        self.logger.write(
            line
        )


        def append():

            self.log_box.configure(
                state="normal"
            )


            self.log_box.insert(

                "end",

                line,

                tag

            )


            self.log_box.see(
                "end"
            )


            self.log_box.configure(
                state="disabled"
            )


        self.after(
            0,
            append
        )


    # ========================================================
    # EXPORT LOG
    # ========================================================

    def _export_log(self):

        path = self.logger.export()

        self._log(

            f"Log exported → {path}",

            "success"

        )


    # ========================================================
    # STATUS
    # ========================================================

    def _set_status(
        self,
        state
    ):

        configs = {

            "ready":
                ("●  Ready", SUCCESS, "IDLE"),

            "thinking":
                ("◌  Thinking", PURPLE_LIGHT, "PLANNING"),

            "running":
                ("◉  Running", WARNING, "AUTOMATING"),

            "error":
                ("✕  Error", ERROR, "ERROR"),

        }


        text, color, workspace = (
            configs.get(

                state,

                ("●", TEXT_DIM, "IDLE")

            )
        )


        def update():

            self.status_pill.configure(

                text=text,

                fg=color

            )


            self.workspace_status.configure(

                text=workspace,

                fg=color

            )


        self.after(
            0,
            update
        )


    # ========================================================
    # ACTIVITY
    # ========================================================

    def _update_activity(
        self,
        title,
        description
    ):

        def update():

            self.activity_label.configure(
                text=title
            )


            self.activity_description.configure(
                text=description
            )


        self.after(
            0,
            update
        )


    # ========================================================
    # HISTORY
    # ========================================================

    def _load_history(self):

        # History remains managed by the existing backend.
        pass


    def _open_history(self):

        window = tk.Toplevel(self)

        window.title(
            "JAS History"
        )

        window.geometry(
            "500x420"
        )

        window.configure(
            bg=BG
        )


        tk.Label(

            window,

            text="Automation History",

            font=FONT_HEADING,

            fg=TEXT,

            bg=BG

        ).pack(

            anchor="w",

            padx=20,

            pady=(20, 12)

        )


        history_list = tk.Listbox(

            window,

            bg=PANEL,

            fg=TEXT_MID,

            selectbackground=PURPLE,

            selectforeground=TEXT,

            relief="flat",

            bd=0,

            font=FONT_UI,

            highlightthickness=1,

            highlightbackground=BORDER

        )


        history_list.pack(

            fill="both",

            expand=True,

            padx=20,

            pady=(0, 12)

        )


        items = list(
            reversed(
                self.history.get_all()
            )
        )


        for item in items:

            history_list.insert(
                "end",
                item
            )


        def use_command():

            selection = (
                history_list.curselection()
            )


            if not selection:

                return


            command = items[
                selection[0]
            ]


            self.cmd_entry.delete(
                0,
                "end"
            )


            self.cmd_entry.insert(
                0,
                command
            )


            self.cmd_entry.configure(
                fg=TEXT
            )


            window.destroy()


        buttons = tk.Frame(
            window,
            bg=BG
        )

        buttons.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )


        ModernButton(

            buttons,

            text="Use Command",

            command=use_command

        ).pack(
            side="left"
        )


        ModernButton(

            buttons,

            text="Clear History",

            command=lambda: (
                self.history.clear(),
                history_list.delete(
                    0,
                    "end"
                )
            ),

            bg=CARD,

            hover=CARD_HOVER,

            fg=TEXT_MID

        ).pack(
            side="right"
        )


    # ========================================================
    # OLD HISTORY CALLBACK COMPATIBILITY
    # ========================================================

    def _on_history_select(
        self,
        _
    ):

        pass


    def _clear_history(self):

        self.history.clear()


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    app = JASApp()

    app.mainloop()