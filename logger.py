"""
logger.py — File logger for JAS v1
"""

import os
from datetime import datetime
from pathlib import Path


class Logger:
    def __init__(self):
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = log_dir / f"jas_{stamp}.log"
        self._fh   = open(self._path, "a", encoding="utf-8")

    def write(self, line: str):
        self._fh.write(line)
        self._fh.flush()

    def export(self) -> str:
        return str(self._path)

    def __del__(self):
        try:
            self._fh.close()
        except Exception:
            pass
