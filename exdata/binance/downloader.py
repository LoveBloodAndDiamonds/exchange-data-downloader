__all__ = ["Downloader"]

import os.path
import urllib.error
import urllib.request
import zipfile
from logging import Logger as LoggingLogger

from loguru import _Logger as LoguruLogger  # type: ignore
from loguru import logger

from exdata.exceptions import InvalidParamsError, NotFoundError

from .types import DataTypes, MarketTypes, PeriodTypes, Timeframes


class Downloader:
    """Класс содержит логику загрузки наборов данных с публичного ресурса data.binance.vision."""

    _base_url: str = "https://data.binance.vision/data/"  # базовый URL Binance Vision

    def __init__(
        self,
        data_folder_path: str = "data/",
        logger_instance: LoguruLogger | LoggingLogger | None = None,
    ) -> None:
        """Принимает путь к каталогу данных и конфигурирует логгер."""
        self._data_folder_path: str = (
            data_folder_path if data_folder_path.endswith("/") else data_folder_path + "/"
        )
        self._logger: LoguruLogger | LoggingLogger = logger_instance or logger

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

        # Проверяем, есть ли уже готовый файл (архив или CSV в зависимости от флага)
        target_extension = ".csv" if unzip else ".zip"
        target_filename: str = self._data_folder_path + endpoint + target_extension
        if os.path.exists(target_filename):
            self._logger.debug(f"File {target_filename} already exists.")
            return target_filename

        # Создаём директорию для будущего файла вместе с родительскими каталогами
        os.makedirs(os.path.dirname(target_filename), exist_ok=True)
        self._logger.debug(f"Created necessary directories for {target_filename}")

        # Скачиваем ZIP-архив с данными
        archive_filename: str = self._retrieve_archive(endpoint=endpoint)
        self._logger.debug(f"Archive downloaded to {archive_filename}")

        if not unzip:
            self._logger.debug("Skipping archive extraction per unzip=False")
            return archive_filename

        # Распаковываем архив и удаляем его
        data_filename: str = self._extract_archive(
            extract_from=archive_filename, extract_to=target_filename
        )
        self._logger.debug(f"Data extracted to {data_filename}")

        return data_filename

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

    @staticmethod
    def _normalize_year(year: int) -> str:
        """Преобразует численный год в строку формата YYYY и проверяет диапазон."""
        if year <= 0:
            raise InvalidParamsError("Год должен быть положительным целым числом.")

        return f"{year:04d}"

    @staticmethod
    def _normalize_month(month: int) -> str:
        """Преобразует численный месяц в строку формата MM и проверяет диапазон."""
        if not 1 <= month <= 12:
            raise InvalidParamsError("Месяц должен быть в диапазоне от 1 до 12.")

        return f"{month:02d}"

    @staticmethod
    def _normalize_day(day: int | None) -> str | None:
        """Приводит день месяца к строке DD либо возвращает None."""
        if day is None:
            return None

        if not 1 <= day <= 31:
            raise InvalidParamsError("День должен быть в диапазоне от 1 до 31.")

        return f"{day:02d}"

    def _retrieve_archive(self, endpoint: str) -> str:
        """Скачивает ZIP-архив по построенному URL и возвращает путь до файла.

        :param endpoint: Конечная часть URL.
        :return: Путь к загруженному ZIP-файлу.
        """
        try:
            self._logger.debug(f"Downloading archive from endpoint: {endpoint}")
            return urllib.request.urlretrieve(
                url=self._base_url + endpoint + ".zip",
                filename=self._data_folder_path + endpoint + ".zip",
            )[0]
        except urllib.error.URLError as e:
            raise NotFoundError(f"Failed to download archive: {e.reason}") from e

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
