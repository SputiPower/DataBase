class ApplicationError(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class DatabaseConnectionError(ApplicationError):
    def __init__(self, message: str = "Ошибка подключения к базе данных") -> None:
        super().__init__(message=message, status_code=500)


class PersistenceError(ApplicationError):
    def __init__(self, message: str = "Ошибка сохранения данных") -> None:
        super().__init__(message=message, status_code=500)
