# ⚡ JAS — Just Automate Something

> A natural language desktop automation agent. Tell it what you want done. It figures out the steps.

![Python](https://img.shields.io/badge/Python-3.11+-3B82F6?style=flat&logo=python&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Llama%203.1%208B-6366F1?style=flat)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat&logo=windows)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat)
![Version](https://img.shields.io/badge/Version-2.0-3B82F6?style=flat)

---

## What is JAS?

JAS turns plain English into desktop automation. You describe what you want — JAS generates a step-by-step plan using an LLM, shows you exactly what it's going to do, and executes it with your confirmation.

```
>>> Open Notepad and type a haiku about rain
```

That's it. No scripting. No learning hotkeys. Just describe the task.

---

## Features

| Feature | Description |
|---|---|
| 🧠 **LLM Planning** | Converts natural language to structured action plans via Llama 3.1 8B |
| 🖥️ **Modern GUI** | Built with CustomTkinter — native rounded UI with live step visualization |
| 🔁 **Self-Healing** | If a step fails, JAS automatically retries with error context (up to 3 attempts) |
| 📸 **Screenshot Verification** | After execution, JAS takes a screenshot and asks the LLM if the goal was achieved |
| 📋 **Command History** | Sidebar with persistent history — click any past command to re-run it |
| 📝 **Live Step Visualizer** | Watch each step light up as it executes in real time |
| 📁 **Log Export** | Full timestamped logs saved per session, exportable on demand |
| 🔐 **Secure Config** | API key stored in `.env`, never hardcoded |

---

## Supported Actions

| Action | What it does |
|---|---|
| `press` | Press a single key (enter, win, escape, F1–F12…) |
| `hotkey` | Key combinations (Ctrl+C, Alt+F4, Win+R…) |
| `write` | Type a string of text |
| `click` | Click at screen coordinates |
| `move` | Move the mouse to a position |
| `scroll` | Scroll up or down |
| `wait` | Pause for N seconds |
| `screenshot` | Capture the screen |

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/yourusername/jas.git
cd jas
pip install -r requirements.txt
```

### 2. Set up your API key

```bash
cp .env.example .env
# Edit .env and paste your NVIDIA API key
```

Get a free API key at [build.nvidia.com](https://build.nvidia.com).

### 3. Run

```bash
python main.py
```

---

## How it works

```
User types command
       ↓
   LLM generates JSON plan
   [{"action":"press","key":"win"}, ...]
       ↓
   GUI shows plan with step cards
       ↓
   User confirms (or auto-execute)
       ↓
   Executor runs each step live
       ↓
   If failure → self-healing retry with error context
       ↓
   Screenshot taken → LLM verifies result
```

---

## Example Plans

**"Open calculator"**
```json
{
  "steps": [
    {"action": "press", "key": "win"},
    {"action": "write", "text": "calculator"},
    {"action": "wait", "seconds": 1},
    {"action": "press", "key": "enter"}
  ]
}
```

**"Copy all text in the current window"**
```json
{
  "steps": [
    {"action": "hotkey", "keys": ["ctrl", "a"]},
    {"action": "hotkey", "keys": ["ctrl", "c"]},
    {"action": "screenshot"}
  ]
}
```

---

## Safety

- **Human-in-the-loop by default** — JAS asks for confirmation before executing any plan
- **Failsafe enabled** — move your mouse to the top-left corner to instantly abort
- **No web access** — JAS only controls your local desktop
- **Transparent** — the full plan is shown before anything runs

---

## Project Structure

```
jas/
├── main.py          # GUI application (tkinter)
├── llm.py           # LLM integration (NVIDIA / Llama 3.1)
├── executor.py      # Action executor (pyautogui)
├── logger.py        # Session logging
├── history.py       # Persistent command history
├── prompt.txt       # System prompt for the LLM
├── .env.example     # API key template
├── requirements.txt
└── logs/            # Auto-generated session logs
```

---

## Roadmap

- [ ] Voice input (speak your command)
- [ ] Macro recording & replay
- [ ] Multi-monitor support
- [ ] Plugin system for custom actions
- [ ] Local LLM support (Ollama)

---

## Changelog

### v2.0 — UI Overhaul

* Migrated from tkinter to CustomTkinter for a modern native UI
* Step cards now have rounded corners and animated color states
* Switches replaced checkboxes for Auto-execute and Self-healing
* History sidebar now uses scrollable button list
* Status pill redesigned as a proper rounded badge
* General spacing, padding, and typography improvements

### v1.0 — Initial Release

* Natural language → action plan via Llama 3.1 8B
* Live step visualizer
* Self-healing retry (up to 3 attempts)
* Screenshot verification via Llama 3.2 Vision
* Persistent command history
* Session logging with export
 
---

## License

MIT — do whatever you want with it.

---

*Built with Python, tkinter, pyautogui, and Llama 3.1 via NVIDIA NIM.*
