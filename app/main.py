import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.passes import router as passes_router
from app.core.config import get_settings
from app.core.exceptions import ApplicationError
from app.schemas.pass_submission import (
    ErrorMessageResponse,
    MountainPassUpdateResponse,
    SubmitDataResponse,
    build_validation_message,
)

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "REST API для приёма, просмотра и условного редактирования данных о горных перевалах. "
        "Документация доступна в Swagger UI по адресу /docs."
    ),
    contact={"name": "SputiPower", "email": "sputi0596@gmail.com"},
    openapi_tags=[
        {
            "name": "mountain-passes",
            "description": "Операции создания, чтения, редактирования и выборки заявок на перевалы.",
        }
    ],
)

app.include_router(passes_router)


@app.exception_handler(ApplicationError)
async def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_response())


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = build_validation_message(exc.errors())

    if request.method == "POST" and request.url.path == "/submitData":
        payload = SubmitDataResponse(status=400, message=message, id=None).model_dump()
    elif request.method == "PATCH" and request.url.path.startswith("/submitData/"):
        payload = MountainPassUpdateResponse(state=0, message=message).model_dump()
    else:
        payload = ErrorMessageResponse(message=message).model_dump()

    return JSONResponse(status_code=400, content=payload)


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    payload = SubmitDataResponse(
        status=500,
        message="Внутренняя ошибка сервера",
        id=None,
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
