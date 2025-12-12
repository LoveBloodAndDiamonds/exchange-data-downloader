__all__ = ["MarketTypes", "PeriodTypes", "DataTypes", "Timeframes"]

from typing import Literal

type MarketTypes = Literal[
    "futures/um",  # бессрочные USD-M фьючерсы
    "futures/cm",  # бессрочные COIN-M фьючерсы
    "spot",
    "option",
]
"""Поддерживаемые Binance типы рынков."""

type PeriodTypes = Literal[
    "monthly",
    "daily",
]
"""Доступные типы периодов."""

type DataTypes = Literal[
    "klines",
    "aggTrades",
    "bookTicker",
    "fundingRate",
    "indexPriceKlines",
    "markPriceKlines",
    "premiumIndexKlines",
    "trades",
]
"""Поддерживаемые типы датасетов."""

type Timeframes = Literal[
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1mo",
]
"""Поддерживаемые таймфреймы."""
