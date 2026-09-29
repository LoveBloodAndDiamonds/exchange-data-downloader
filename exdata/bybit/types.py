__all__ = ["MarketTypes", "PeriodTypes", "DataTypes"]

from typing import Literal

type MarketTypes = Literal[
    "futures",  # USDT, USDC (...PERP), инверсные USD и срочные контракты — всё в разделе trading/
    "spot",
]
"""Поддерживаемые Bybit типы рынков."""

type PeriodTypes = Literal[
    "daily",
    "monthly",  # доступно только для spot
]
"""Доступные типы периодов."""

type DataTypes = Literal["trades"]
"""Поддерживаемые типы датасетов."""
