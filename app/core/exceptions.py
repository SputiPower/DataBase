class ApplicationError(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int, payload: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_response(self) -> dict:
        return self.payload or {"message": self.message}


class ValidationError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=400,
            payload={"status": 400, "message": message, "id": None},
        )


class DatabaseConnectionError(ApplicationError):
    def __init__(self, message: str = "Ошибка подключения к базе данных") -> None:
        super().__init__(
            message=message,
            status_code=500,
            payload={"status": 500, "message": message, "id": None},
        )


class PersistenceError(ApplicationError):
    def __init__(self, message: str = "Ошибка сохранения данных") -> None:
        super().__init__(
            message=message,
            status_code=500,
            payload={"status": 500, "message": message, "id": None},
        )


class NotFoundError(ApplicationError):
    def __init__(self, message: str = "Запись не найдена") -> None:
        super().__init__(message=message, status_code=404, payload={"message": message})
