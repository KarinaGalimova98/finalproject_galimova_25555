from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from ..logging_config import configure_logging
from .config import ParserConfig
from .storage import RatesStorage
from .api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from ..core.exceptions import ApiRequestError


logger = configure_logging()


class RatesUpdater:
    """Координация обновления курсов с нескольких источников."""

    def __init__(self, config: ParserConfig) -> None:
        self._config = config
        self._storage = RatesStorage(config)
        self._clients: List[BaseApiClient] = [
            CoinGeckoClient(config),
            ExchangeRateApiClient(config),
        ]

    def run_update(self, source_filter: Optional[str] = None) -> Dict[str, Any]:
        """Основной сценарий обновления курсов.

        source_filter: "coingecko", "exchangerate" или None.
        """
        logger.info("Starting rates update...")
        all_pairs: Dict[str, Dict[str, Any]] = {}
        history_entries: List[Dict[str, Any]] = []
        errors: List[str] = []

        now = datetime.now(timezone.utc)

        for client in self._clients:
            name_lower = client.source_name.lower()
            if source_filter and source_filter not in name_lower:
                # пропускаем, если фильтр не совпадает
                continue

            logger.info(f"Fetching from {client.source_name}...")
            try:
                client_result = client.fetch_rates()
            except ApiRequestError as exc:
                msg = f"Failed to fetch from {client.source_name}: {exc}"
                logger.error(msg)
                errors.append(msg)
                continue

            logger.info(
                f"Fetching from {client.source_name} OK "
                f"({len(client_result)} rates)"
            )

            for pair_key, info in client_result.items():
                all_pairs[pair_key] = info
                from_code, to_code = pair_key.split("_", maxsplit=1)
                meta = info.get("meta", {})
                entry = {
                    "id": f"{from_code}_{to_code}_{now.isoformat()}",
                    "from_currency": from_code,
                    "to_currency": to_code,
                    "rate": float(info["rate"]),
                    "timestamp": now.isoformat(),
                    "source": info["source"],
                    "meta": meta,
                }
                history_entries.append(entry)

        if all_pairs:
            self._storage.save_current_rates(all_pairs, last_refresh=now)
            self._storage.append_history_entries(history_entries)
            logger.info(
                "Writing %d rates to %s",
                len(all_pairs),
                self._config.RATES_FILE_PATH,
            )
        else:
            logger.warning("No rates were updated.")

        result: Dict[str, Any] = {
            "total_rates": len(all_pairs),
            "last_refresh": now,
            "errors": errors,
        }
        if errors:
            logger.info("Update completed with errors.")
        else:
            logger.info("Update successful.")
        return result
