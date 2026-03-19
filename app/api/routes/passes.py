from fastapi import APIRouter, status

from app.core.database import database_manager
from app.schemas.pass_submission import PassSubmissionSchema, SubmitDataResponse
from app.services.pass_service import MountainPassSubmissionService


router = APIRouter(tags=["mountain-passes"])

service = MountainPassSubmissionService(database_manager=database_manager)


@router.post(
    "/submitData",
    response_model=SubmitDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Создать новую заявку на горный перевал",
    responses={
        200: {"description": "Заявка успешно создана"},
        400: {"description": "Ошибка валидации входных данных"},
        500: {"description": "Ошибка базы данных или внутренняя ошибка сервера"},
    },
)
def submit_data(payload: PassSubmissionSchema) -> SubmitDataResponse:
    record_id = service.submit(payload)
    return SubmitDataResponse(status=200, message=None, id=record_id)
