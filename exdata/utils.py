__all__ = ["generate_intervals"]

from datetime import date, timedelta

from .exceptions import InvalidParamsError


def generate_intervals(
    *,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    start_day: int | None = None,
    end_day: int | None = None,
) -> tuple[date, ...]:
    """Возвращает последовательность дат для обхода интервалов.

    Если переданы дни начала и конца, формируется ежедневный диапазон.
    Иначе функция возвращает первые числа месяцев в указанном промежутке.
    """
    if (start_day is None) ^ (end_day is None):  # XOR
        raise InvalidParamsError("Необходимо указать оба дня либо ни один.")

    if start_day is None:
        return _build_monthly_dates(start_year, start_month, end_year, end_month)

    return _build_daily_dates(
        start_year=start_year,
        start_month=start_month,
        start_day=start_day,
        end_year=end_year,
        end_month=end_month,
        end_day=end_day,  # type: ignore
    )


def _build_monthly_dates(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> tuple[date, ...]:
    """Возвращает кортеж дат-представителей месяцев включительно."""
    start = _make_date(start_year, start_month, 1)
    end = _make_date(end_year, end_month, 1)

    if start > end:
        raise InvalidParamsError("Дата начала не может быть больше даты окончания.")

    result: list[date] = []
    current = start

    while current <= end:
        result.append(current)
        # Переходим к первому числу следующего месяца
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        current = date(year, month, 1)

    return tuple(result)


def _build_daily_dates(
    *,
    start_year: int,
    start_month: int,
    start_day: int,
    end_year: int,
    end_month: int,
    end_day: int,
) -> tuple[date, ...]:
    """Возвращает кортеж дат между двумя точками времени включительно."""
    start = _make_date(start_year, start_month, start_day)
    end = _make_date(end_year, end_month, end_day)

    if start > end:
        raise InvalidParamsError("Дата начала не может быть больше даты окончания.")

    result: list[date] = []
    current = start

    while current <= end:
        result.append(current)
        current += timedelta(days=1)

    return tuple(result)


def _make_date(year: int, month: int, day: int) -> date:
    """Создаёт объект даты и валидирует входящие значения."""
    if year <= 0:
        raise InvalidParamsError("Год должен быть положительным целым числом.")

    if not 1 <= month <= 12:
        raise InvalidParamsError("Месяц должен быть в диапазоне от 1 до 12.")

    if not 1 <= day <= 31:
        raise InvalidParamsError("День должен быть в диапазоне от 1 до 31.")

    try:
        return date(year, month, day)
    except ValueError as exc:
        raise InvalidParamsError("Невозможно сформировать дату с переданными параметрами.") from exc
