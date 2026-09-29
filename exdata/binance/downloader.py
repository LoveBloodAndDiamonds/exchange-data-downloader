__all__ = ["Downloader"]

import os
import zipfile

from exdata.base import BaseDownloader
from exdata.exceptions import InvalidParamsError

from .types import DataTypes, MarketTypes, PeriodTypes, Timeframes


class Downloader(BaseDownloader):
    """Класс содержит логику загрузки наборов данных с публичного ресурса data.binance.vision."""

    _base_url: str = "https://data.binance.vision/data/"  # базовый URL Binance Vision
    _archive_extension: str = ".zip"  # Binance отдаёт данные в ZIP-архивах

    def download(
        self,
        symbol: str,
        year: int,
        month: int,
        day: int | None = None,
        data_type: DataTypes = "klines",
        market_type: MarketTypes = "futures/um",
        timeframe: Timeframes | None = None,
        period_type: PeriodTypes = "monthly",
        unzip: bool = False,
    ) -> str:
        """Скачивает данные с data.binance.vision.com.

        :param symbol: Торговый инструмент, например "BTCUSDT".
        :param year: Год числом, например 2024.
        :param month: Месяц числом от 1 до 12.
        :param day: День числом от 1 до 31; используется только при period_type == "daily".
        :param timeframe: Таймфрейм, например "5m"; обязателен для kline-подобных типов данных.
        :param data_type: Тип данных, например "klines"; список см. в типе DataTypes.
        :param market_type: Тип рынка, например "futures/um"; список см. в типе MarketTypes.
        :param period_type: Тип периода, например "monthly"; список см. в типе PeriodTypes.
        :param unzip: Флаг, нужно ли распаковывать архив после скачивания.
        :return: Путь к ZIP-архиву либо к распакованному CSV-файлу, если unzip=True.
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
            timeframe=timeframe,
            market_type=market_type,
            period_type=period_type,
            data_type=data_type,
        )

        return self._download_endpoint(endpoint=endpoint, unzip=unzip)

    def _extract_archive(self, extract_from: str, extract_to: str) -> str:
        """Распаковывает данные из ZIP-архива и удаляет исходный файл."""
        with zipfile.ZipFile(extract_from, "r") as zip_ref:
            self._logger.debug(f"Extracting data from {extract_from} to {extract_to}")
            extracted_file_path = zip_ref.extract(
                zip_ref.namelist()[0], os.path.dirname(extract_to)
            )

        self._logger.debug(f"Removing tmp {extract_from} archive")
        os.remove(extract_from)

        return extracted_file_path

    def _compare_endpoint(
        self,
        symbol: str,
        year: str,
        month: str,
        day: str | None,
        timeframe: Timeframes | None,
        market_type: MarketTypes,
        period_type: PeriodTypes,
        data_type: DataTypes,
    ) -> str:
        """Формирует конечный путь на основе параметров, учитывая тип данных.

        :return: Структура пути внутри хранилища Binance.
        """
        common: tuple = (market_type, period_type, data_type, symbol.upper())

        if data_type in {"klines", "indexPriceKlines", "markPriceKlines", "premiumIndexKlines"}:
            if timeframe is None:
                raise InvalidParamsError(
                    "Для kline-подобных типов необходимо указать параметр 'timeframe'"
                )

            if period_type == "daily":
                if day is None:
                    raise InvalidParamsError(
                        "Для периодичности 'daily' необходимо передать параметр 'day'"
                    )
                filename = f"{symbol.upper()}-{timeframe}-{year}-{month}-{day}"
            else:
                filename = f"{symbol.upper()}-{timeframe}-{year}-{month}"

            return "/".join((*common, timeframe, filename))

        elif data_type in {"aggTrades", "bookTicker", "fundingRate", "trades"}:
            if period_type == "daily":
                if day is None:
                    raise InvalidParamsError(
                        "Для периодичности 'daily' необходимо передать параметр 'day'"
                    )
                filename = f"{symbol.upper()}-{data_type}-{year}-{month}-{day}"
            else:
                filename = f"{symbol.upper()}-{data_type}-{year}-{month}"

            return "/".join((*common, filename))

        raise InvalidParamsError(f"Wrong data type: {data_type}")
