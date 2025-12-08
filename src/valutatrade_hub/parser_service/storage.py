from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from .config import ParserConfig


class RatesStorage:
    """Хранилище для текущих курсов и истории измерений."""

    def __init__(self, config: ParserConfig) -> None:
        self._config = config
        self._rates_path: Path = config.RATES_FILE_PATH
        self._history_path: Path = config.HISTORY_FILE_PATH
        self._rates_path.parent.mkdir(parents=True, exist_ok=True)
        self._history_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _atomic_write(path: Path, data: Any) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(path)

    # --- история ---

    def load_history(self) -> List[Dict[str, Any]]:
        if not self._history_path.exists():
            return []
        with open(self._history_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def append_history_entries(self, entries: List[Dict[str, Any]]) -> None:
        history = self.load_history()
        history.extend(entries)
        self._atomic_write(self._history_path, history)

    # --- текущие курсы (кэш для Core Service) ---

    def load_current_rates(self) -> Dict[str, Any]:
        if not self._rates_path.exists():
            return {}
        with open(self._rates_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_current_rates(
        self,
        pairs: Dict[str, Dict[str, Any]],
        last_refresh: datetime,
    ) -> None:
        snapshot: Dict[str, Any] = {}
        for pair_key, info in pairs.items():
            snapshot[pair_key] = {
                "rate": float(info["rate"]),
                "updated_at": last_refresh.isoformat(),
                "source": info["source"],
            }
        snapshot["last_refresh"] = last_refresh.isoformat()
        self._atomic_write(self._rates_path, snapshot)
