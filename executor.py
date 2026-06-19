"""
executor.py — Action executor for JAS v1
Supports: press, hotkey, write, click, move, scroll, wait, screenshot
"""

import time
import pyautogui
import tempfile
import os
from dataclasses import dataclass, field
from typing import Callable, Optional

pyautogui.FAILSAFE = True   # move mouse to top-left corner to abort
pyautogui.PAUSE    = 0.05   # small pause between actions


@dataclass
class ExecutionResult:
    success:         bool
    failed_step:     int               = -1
    error:           str               = ""
    screenshot_path: Optional[str]     = None
    logs:            list[str]         = field(default_factory=list)


def _do_action(step: dict) -> str:
    """Execute one step dict. Returns a human-readable description."""
    action = step.get("action", "").lower()

    if action == "press":
        key = step["key"]
        pyautogui.press(key)
        return f'Pressed "{key}"'

    elif action == "hotkey":
        keys = step["keys"]          # e.g. ["ctrl", "c"]
        pyautogui.hotkey(*keys)
        return f'Hotkey: {" + ".join(keys)}'

    elif action == "write":
        text     = step["text"]
        interval = float(step.get("interval", 0.03))
        pyautogui.write(text, interval=interval)
        return f'Typed "{text[:40]}{"…" if len(text)>40 else ""}"'

    elif action == "click":
        x, y   = int(step["x"]), int(step["y"])
        button = step.get("button", "left")
        clicks = int(step.get("clicks", 1))
        pyautogui.click(x, y, button=button, clicks=clicks)
        return f'Clicked ({x},{y}) [{button}×{clicks}]'

    elif action == "move":
        x, y      = int(step["x"]), int(step["y"])
        duration  = float(step.get("duration", 0.2))
        pyautogui.moveTo(x, y, duration=duration)
        return f'Moved to ({x},{y})'

    elif action == "scroll":
        x       = int(step.get("x", pyautogui.position().x))
        y       = int(step.get("y", pyautogui.position().y))
        clicks  = int(step.get("clicks", 3))
        pyautogui.scroll(clicks, x=x, y=y)
        return f'Scrolled {clicks} at ({x},{y})'

    elif action == "wait":
        secs = float(step.get("seconds", 1))
        time.sleep(secs)
        return f'Waited {secs}s'

    elif action == "screenshot":
        path = step.get("path") or os.path.join(
            tempfile.gettempdir(), f"jas_screen_{int(time.time())}.png")
        pyautogui.screenshot(path)
        return f'Screenshot → {path}'

    else:
        raise ValueError(f'Unknown action: "{action}"')


def execute_plan(
    plan: dict,
    step_callback: Optional[Callable[[int, str, str], None]] = None,
) -> ExecutionResult:
    """
    Execute every step in *plan["steps"]*.

    *step_callback(index, status, detail)* is called before and after each step:
        status ∈ {"running", "success", "error", "skipped"}
    """
    steps = plan.get("steps", [])
    screenshot_path = None
    logs = []

    for i, step in enumerate(steps):
        if step_callback:
            step_callback(i, "running", "")

        try:
            detail = _do_action(step)
            logs.append(f"[{i+1}] OK  {detail}")

            # Track screenshot path for the verification loop
            if step.get("action") == "screenshot":
                p = step.get("path") or ""
                if os.path.exists(p):
                    screenshot_path = p

            if step_callback:
                step_callback(i, "success", detail)

        except Exception as e:
            msg = str(e)
            logs.append(f"[{i+1}] ERR {msg}")
            if step_callback:
                step_callback(i, "error", msg)

            # Mark remaining steps as skipped
            for j in range(i + 1, len(steps)):
                if step_callback:
                    step_callback(j, "skipped", "")

            return ExecutionResult(
                success=False,
                failed_step=i,
                error=msg,
                screenshot_path=screenshot_path,
                logs=logs,
            )

    # Auto-screenshot at the end for verification
    if not screenshot_path:
        try:
            auto_path = os.path.join(
                tempfile.gettempdir(), f"jas_verify_{int(time.time())}.png")
            pyautogui.screenshot(auto_path)
            screenshot_path = auto_path
        except Exception:
            pass

    return ExecutionResult(
        success=True,
        screenshot_path=screenshot_path,
        logs=logs,
    )
