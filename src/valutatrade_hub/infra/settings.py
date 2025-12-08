from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..core import constants


@dataclass(frozen=True)
class SettingsData:
    data_dir: str
    users_file: str
    portfolios_file: str
    rates_file: str
    logs_dir: str
    log_file: str
    log_level: str
    log_max_bytes: int
    log_backup_count: int
    rates_ttl_seconds: int
    default_base_currency: str


class SettingsLoader:
    """Singleton для конфигурации приложения.

    Реализован через __new__ для простоты и читабельности.
    """

    _instance: "SettingsLoader | None" = None

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self) -> None:
        self._settings = SettingsData(
            data_dir=str(constants.DATA_DIR),
            users_file=str(constants.USERS_FILE),
            portfolios_file=str(constants.PORTFOLIOS_FILE),
            rates_file=str(constants.RATES_FILE),
            logs_dir=str(constants.LOG_DIR),
            log_file=str(constants.LOG_FILE),
            log_level=constants.LOG_LEVEL,
            log_max_bytes=constants.LOG_MAX_BYTES,
            log_backup_count=constants.LOG_BACKUP_COUNT,
            rates_ttl_seconds=constants.RATE_FRESHNESS_SECONDS,
            default_base_currency=constants.DEFAULT_BASE_CURRENCY,
        )

    def get(self, key: str, default: Any | None = None) -> Any:
        return getattr(self._settings, key, default)

    def as_dict(self) -> Dict[str, Any]:
        return self._settings.__dict__.copy()
