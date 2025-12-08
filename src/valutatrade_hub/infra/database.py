from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Dict

from ..core.constants import DATA_DIR, USERS_FILE, PORTFOLIOS_FILE, RATES_FILE
from ..core.models import User, Portfolio
from .settings import SettingsLoader


class DatabaseManager:
    """Singleton-обёртка над JSON-хранилищем."""

    _instance: "DatabaseManager | None" = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_paths()
        return cls._instance

    def _init_paths(self) -> None:
        settings = SettingsLoader()
        self.data_dir = Path(settings.get("data_dir"))
        self.users_file = Path(settings.get("users_file"))
        self.portfolios_file = Path(settings.get("portfolios_file"))
        self.rates_file = Path(settings.get("rates_file"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # --- низкоуровневые операции ---

    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default

    def _save_json(self, path: Path, data: Any) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- пользователи ---

    def load_users(self) -> List[User]:
        raw = self._load_json(self.users_file, [])
        return [User.from_dict(item) for item in raw]

    def save_users(self, users: List[User]) -> None:
        data = [user.to_dict() for user in users]
        self._save_json(self.users_file, data)

    # --- портфели ---

    def load_portfolios_raw(self) -> List[Dict]:
        return self._load_json(self.portfolios_file, [])

    def save_portfolios_raw(self, data: List[Dict]) -> None:
        self._save_json(self.portfolios_file, data)

    # --- курсы ---

    def load_rates_raw(self) -> Dict[str, Any]:
        return self._load_json(self.rates_file, {})

    def save_rates_raw(self, data: Dict[str, Any]) -> None:
        self._save_json(self.rates_file, data)
