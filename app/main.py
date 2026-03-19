import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.passes import router as passes_router
from app.core.config import get_settings
from app.core.exceptions import ApplicationError
from app.schemas.pass_submission import SubmitDataResponse, build_validation_message

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(passes_router)


@app.exception_handler(ApplicationError)
async def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
    payload = SubmitDataResponse(status=exc.status_code, message=exc.message, id=None)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = SubmitDataResponse(
        status=400,
        message=build_validation_message(exc.errors()),
        id=None,
    )
    return JSONResponse(status_code=400, content=payload.model_dump())


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
