__all__ = ["NotFoundError", "InvalidParamsError"]


class NotFoundError(Exception):
    """Исключение выбрасывается, если удалённый ресурс недоступен или не существует."""

    pass


class InvalidParamsError(ValueError):
    """Исключение выбрасывается при некорректных параметрах запроса к API."""

    pass
