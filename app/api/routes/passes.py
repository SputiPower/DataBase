from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import EmailStr

from app.core.database import database_manager
from app.schemas.pass_submission import (
    ErrorMessageResponse,
    MountainPassDetailResponse,
    MountainPassSummaryResponse,
    MountainPassUpdateResponse,
    PassSubmissionSchema,
    SubmitDataResponse,
)
from app.services.pass_service import MountainPassService


router = APIRouter(prefix="/submitData", tags=["mountain-passes"])

service = MountainPassService(database_manager=database_manager)


def get_mountain_pass_service() -> MountainPassService:
    return service


MountainPassServiceDep = Annotated[MountainPassService, Depends(get_mountain_pass_service)]
UserEmailQuery = Annotated[EmailStr, Query(alias="user__email", description="Email пользователя")]


@router.post(
    "",
    response_model=SubmitDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Создать новую заявку на горный перевал",
    description="Принимает полную структуру данных перевала и сохраняет её в базе данных со статусом new.",
    responses={
        200: {"description": "Заявка успешно создана"},
        400: {"description": "Ошибка валидации входных данных"},
        500: {"description": "Ошибка базы данных или внутренняя ошибка сервера"},
    },
)
def submit_data(payload: PassSubmissionSchema, service_dep: MountainPassServiceDep) -> SubmitDataResponse:
    record_id = service_dep.submit(payload)
    return SubmitDataResponse(status=200, message="Отправлено успешно", id=record_id)


@router.get(
    "/{mountain_pass_id}",
    response_model=MountainPassDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить полную информацию о перевале по id",
    description="Возвращает запись перевала вместе с пользователем, координатами, уровнями сложности, фотографиями и текущим статусом модерации.",
    responses={
        200: {"description": "Запись найдена"},
        404: {"model": ErrorMessageResponse, "description": "Запись не найдена"},
        400: {"model": ErrorMessageResponse, "description": "Ошибка валидации path-параметра"},
    },
)
def get_mountain_pass(mountain_pass_id: int, service_dep: MountainPassServiceDep) -> MountainPassDetailResponse:
    return service_dep.get_pereval_by_id(mountain_pass_id)


@router.patch(
    "/{mountain_pass_id}",
    response_model=MountainPassUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить запись перевала, если её статус new",
    description=(
        "Обновляет поля перевала, координаты, уровни сложности и изображения. "
        "Данные пользователя изменять нельзя: если в payload они отличаются, API вернёт ошибку."
    ),
    responses={
        200: {"description": "Запись успешно обновлена"},
        400: {"description": "Некорректный payload или попытка изменить данные пользователя"},
        404: {"description": "Запись не найдена"},
        409: {"description": "Редактирование запрещено из-за статуса записи"},
    },
)
def update_mountain_pass(
    mountain_pass_id: int,
    payload: PassSubmissionSchema,
    service_dep: MountainPassServiceDep,
) -> JSONResponse:
    response_model, response_status = service_dep.update_pereval(mountain_pass_id, payload)
    return JSONResponse(
        content=response_model.model_dump(),
        status_code=response_status,
    )


@router.get(
    "",
    response_model=list[MountainPassSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить все перевалы пользователя по email",
    description="Возвращает компактный список всех заявок, отправленных пользователем с указанным email.",
    responses={
        200: {"description": "Список записей пользователя"},
        400: {"model": ErrorMessageResponse, "description": "Некорректный email"},
    },
)
def get_mountain_passes_by_user_email(
    user_email: UserEmailQuery,
    service_dep: MountainPassServiceDep,
) -> list[MountainPassSummaryResponse]:
    return service_dep.get_perevals_by_user_email(str(user_email))
