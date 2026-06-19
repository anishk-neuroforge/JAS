"""
history.py — Persistent command history for JAS v1
"""

import json
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "history.json"
MAX_ENTRIES  = 50


class HistoryManager:
    def __init__(self):
        self._entries: list[str] = []
        self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            try:
                self._entries = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                self._entries = []

    def _save(self):
        HISTORY_FILE.write_text(
            json.dumps(self._entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, command: str):
        if command in self._entries:
            self._entries.remove(command)
        self._entries.append(command)
        if len(self._entries) > MAX_ENTRIES:
            self._entries = self._entries[-MAX_ENTRIES:]
        self._save()

    def get_all(self) -> list[str]:
        return list(self._entries)

    def clear(self):
        self._entries = []
        self._save()
