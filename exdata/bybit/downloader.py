__all__ = ["Downloader"]

import gzip
import os
import shutil

from exdata.base import BaseDownloader
from exdata.exceptions import InvalidParamsError

from .types import DataTypes, MarketTypes, PeriodTypes


class Downloader(BaseDownloader):
    """Класс содержит логику загрузки наборов данных с публичного ресурса public.bybit.com."""

    _base_url: str = "https://public.bybit.com/"  # базовый URL публичных данных Bybit
    _archive_extension: str = ".csv.gz"  # Bybit отдаёт данные в gzip-сжатых CSV

    def download(
        self,
        symbol: str,
        year: int,
        month: int,
        day: int | None = None,
        data_type: DataTypes = "trades",
        market_type: MarketTypes = "futures",
        period_type: PeriodTypes = "daily",
        unzip: bool = False,
    ) -> str:
        """Скачивает данные с public.bybit.com.

        :param symbol: Торговый инструмент, например "BTCUSDT".
        :param year: Год числом, например 2024.
        :param month: Месяц числом от 1 до 12.
        :param day: День числом от 1 до 31; используется только при period_type == "daily".
        :param data_type: Тип данных; сейчас поддерживается только "trades".
        :param market_type: Тип рынка: "futures" или "spot".
        :param period_type: Тип периода: "daily" или "monthly" (monthly есть только у spot).
        :param unzip: Флаг, нужно ли распаковывать архив после скачивания.
        :return: Путь к .csv.gz-архиву либо к распакованному CSV-файлу, если unzip=True.
        """
        # Нормализуем числовые значения в строковые представления для эндпоинта
        year_str = self._normalize_year(year)
        month_str = self._normalize_month(month)
        day_str = self._normalize_day(day)

        # Строим конечную точку, соответствующую параметрам запроса
        endpoint: str = self._compare_endpoint(
            symbol=symbol,
            year=year_str,
            month=month_str,
            day=day_str,
            data_type=data_type,
            market_type=market_type,
            period_type=period_type,
        )

        return self._download_endpoint(endpoint=endpoint, unzip=unzip)

    def _extract_archive(self, extract_from: str, extract_to: str) -> str:
        """Распаковывает gzip-архив в CSV-файл и удаляет исходный архив."""
        self._logger.debug(f"Extracting data from {extract_from} to {extract_to}")
        with gzip.open(extract_from, "rb") as source, open(extract_to, "wb") as target:
            # Копируем потоково, чтобы не держать весь файл (бывает >100 МБ) в памяти
            shutil.copyfileobj(source, target)

        self._logger.debug(f"Removing tmp {extract_from} archive")
        os.remove(extract_from)

        return extract_to

    def _compare_endpoint(
        self,
        symbol: str,
        year: str,
        month: str,
        day: str | None,
        data_type: DataTypes,
        market_type: MarketTypes,
        period_type: PeriodTypes,
    ) -> str:
        """Формирует путь к файлу на public.bybit.com без расширения.

        Форматы имён файлов на Bybit:
        - futures daily: trading/BTCUSDT/BTCUSDT2026-09-28
        - spot daily:    spot/BTCUSDT/BTCUSDT_2026-09-28
        - spot monthly:  spot/BTCUSDT/BTCUSDT-2026-08
        """
        if data_type != "trades":
            raise InvalidParamsError(f"Wrong data type: {data_type}")

        symbol = symbol.upper()

        # Дата в имени файла: для daily с днём, для monthly только год и месяц
        if period_type == "daily":
            if day is None:
                raise InvalidParamsError("Parameter 'day' is required for 'daily' period")
            date_part = f"{year}-{month}-{day}"
        elif period_type == "monthly":
            date_part = f"{year}-{month}"
        else:
            raise InvalidParamsError(f"Wrong period type: {period_type}")

        if market_type == "futures":
            if period_type == "monthly":
                raise InvalidParamsError("Bybit provides futures trades only for 'daily' period")
            return f"trading/{symbol}/{symbol}{date_part}"

        if market_type == "spot":
            # У спота разделитель между символом и датой зависит от периода
            separator = "_" if period_type == "daily" else "-"
            return f"spot/{symbol}/{symbol}{separator}{date_part}"

        raise InvalidParamsError(f"Wrong market type: {market_type}")
