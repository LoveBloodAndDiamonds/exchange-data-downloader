__all__ = ["BaseDownloader"]

import os.path
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from logging import Logger as LoggingLogger

from loguru import _Logger as LoguruLogger  # type: ignore
from loguru import logger

from .exceptions import InvalidParamsError, NotFoundError


class BaseDownloader(ABC):
    """Общая логика загрузчиков: кэш, создание каталогов, скачивание и распаковка архивов.

    Наследник обязан задать атрибуты `_base_url` и `_archive_extension`,
    а также реализовать `_extract_archive` под свой формат архива.
    """

    _base_url: str  # базовый URL источника данных, задаётся в наследнике
    _archive_extension: str  # расширение скачиваемого архива, например ".zip" или ".csv.gz"

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

    @abstractmethod
    def _extract_archive(self, extract_from: str, extract_to: str) -> str:
        """Распаковывает архив, удаляет его и возвращает путь к распакованному CSV-файлу."""

    def _download_endpoint(self, endpoint: str, unzip: bool) -> str:
        """Скачивает файл по endpoint с учётом кэша и при необходимости распаковывает его.

        :param endpoint: Путь к файлу относительно `_base_url`, без расширения.
        :param unzip: Флаг, нужно ли распаковывать архив после скачивания.
        :return: Путь к архиву либо к распакованному CSV-файлу, если unzip=True.
        """
        # Проверяем, есть ли уже готовый файл (архив или CSV в зависимости от флага)
        target_extension = ".csv" if unzip else self._archive_extension
        target_filename: str = self._data_folder_path + endpoint + target_extension
        if os.path.exists(target_filename):
            self._logger.debug(f"File {target_filename} already exists.")
            return target_filename

        # Создаём директорию для будущего файла вместе с родительскими каталогами
        os.makedirs(os.path.dirname(target_filename), exist_ok=True)
        self._logger.debug(f"Created necessary directories for {target_filename}")

        # Скачиваем архив с данными
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

    def _retrieve_archive(self, endpoint: str) -> str:
        """Скачивает архив по построенному URL и возвращает путь до файла.

        :param endpoint: Конечная часть URL.
        :return: Путь к загруженному архиву.
        """
        try:
            self._logger.debug(f"Downloading archive from endpoint: {endpoint}")
            return urllib.request.urlretrieve(
                url=self._base_url + endpoint + self._archive_extension,
                filename=self._data_folder_path + endpoint + self._archive_extension,
            )[0]
        except urllib.error.URLError as e:
            raise NotFoundError(f"Failed to download archive: {e.reason}") from e

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
