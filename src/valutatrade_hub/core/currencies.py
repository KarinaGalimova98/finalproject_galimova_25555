from __future__ import annotations

from abc import ABC, abstractmethod

from .constants import CURRENCY_REGISTRY, CurrencyConfig
from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный класс валюты."""

    def __init__(self, name: str, code: str) -> None:
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым.")
        code = code.strip().upper()
        if not (2 <= len(code) <= 5) or " " in code:
            raise ValueError("Код валюты должен быть 2–5 символов, без пробелов.")
        self.name = name.strip()
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:  # pragma: no cover - просто формат
        """Строковое представление для UI/логов."""


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name=name, code=code)
        if not issuing_country or not issuing_country.strip():
            raise ValueError("Страна эмиссии не может быть пустой.")
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


class CryptoCurrency(Currency):
    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        super().__init__(name=name, code=code)
        if not algorithm or not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым.")
        if market_cap < 0:
            raise ValueError("Капитализация не может быть отрицательной.")
        self.algorithm = algorithm.strip()
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


def get_currency(code: str) -> Currency:
    """Фабрика валют по коду.

    Если код неизвестен — CurrencyNotFoundError.
    """
    normalized = code.strip().upper()
    config: CurrencyConfig | None = CURRENCY_REGISTRY.get(normalized)  # type: ignore[assignment]

    if config is None:
        raise CurrencyNotFoundError(normalized)

    if config["kind"] == "fiat":
        return FiatCurrency(
            name=config["name"],
            code=normalized,
            issuing_country=config["issuing_country"],
        )

    if config["kind"] == "crypto":
        return CryptoCurrency(
            name=config["name"],
            code=normalized,
            algorithm=config["algorithm"],
            market_cap=config["market_cap"],
        )

    # На случай неправильной конфигурации
    raise CurrencyNotFoundError(normalized)
