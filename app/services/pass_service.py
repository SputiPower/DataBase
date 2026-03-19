from fastapi import status

from app.core.database import DatabaseManager
from app.core.exceptions import NotFoundError, ValidationError
from app.db.enums import PassStatus
from app.db.models import MountainPass, User
from app.repositories.pass_repository import MountainPassRepository
from app.schemas.pass_submission import (
    CoordinatesSchema,
    LevelSchema,
    MountainPassDetailResponse,
    MountainPassImageResponse,
    MountainPassSummaryResponse,
    MountainPassUpdateResponse,
    PassSubmissionSchema,
    UserSchema,
    encode_image_data,
)


class MountainPassService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self.database_manager = database_manager

    def submit(self, payload: PassSubmissionSchema) -> int:
        if not payload.images:
            raise ValidationError("Отсутствует обязательное поле images")

        with self.database_manager.session_scope() as session:
            repository = MountainPassRepository(session)
            user = repository.get_or_create_user(payload)
            mountain_pass = repository.create_pass(payload, user.id)
            repository.create_coordinates(payload, mountain_pass.id)
            repository.create_levels(payload, mountain_pass.id)
            repository.create_images(payload, mountain_pass.id)
            return mountain_pass.id

    def get_pereval_by_id(self, mountain_pass_id: int) -> MountainPassDetailResponse:
        with self.database_manager.session_scope() as session:
            repository = MountainPassRepository(session)
            mountain_pass = repository.get_pereval_by_id(mountain_pass_id)
            if mountain_pass is None:
                raise NotFoundError("Запись перевала не найдена")
            return self._build_detail_response(mountain_pass)

    def update_pereval(self, mountain_pass_id: int, payload: PassSubmissionSchema) -> tuple[MountainPassUpdateResponse, int]:
        with self.database_manager.session_scope() as session:
            repository = MountainPassRepository(session)
            mountain_pass = repository.get_pereval_by_id(mountain_pass_id)

            if mountain_pass is None:
                return (
                    MountainPassUpdateResponse(state=0, message="Запись перевала не найдена"),
                    status.HTTP_404_NOT_FOUND,
                )

            if mountain_pass.status != PassStatus.NEW:
                return (
                    MountainPassUpdateResponse(
                        state=0,
                        message="Редактирование запрещено, так как статус записи не new",
                    ),
                    status.HTTP_409_CONFLICT,
                )

            if self._has_user_changes(mountain_pass.user, payload):
                return (
                    MountainPassUpdateResponse(
                        state=0,
                        message="Редактирование данных пользователя запрещено",
                    ),
                    status.HTTP_400_BAD_REQUEST,
                )

            repository.update_pereval_if_new(mountain_pass, payload)
            return MountainPassUpdateResponse(state=1, message=None), status.HTTP_200_OK

    def get_perevals_by_user_email(self, email: str) -> list[MountainPassSummaryResponse]:
        with self.database_manager.session_scope() as session:
            repository = MountainPassRepository(session)
            mountain_passes = repository.get_perevals_by_user_email(email)
            return [
                MountainPassSummaryResponse(
                    id=mountain_pass.id,
                    title=mountain_pass.title,
                    beauty_title=mountain_pass.beauty_title,
                    other_titles=mountain_pass.other_titles,
                    status=mountain_pass.status,
                    add_time=mountain_pass.add_time,
                    created_at=mountain_pass.created_at,
                    updated_at=mountain_pass.updated_at,
                )
                for mountain_pass in mountain_passes
            ]

    @staticmethod
    def _has_user_changes(user: User, payload: PassSubmissionSchema) -> bool:
        return any(
            (
                user.email != payload.user.email,
                user.last_name != payload.user.fam,
                user.first_name != payload.user.name,
                user.middle_name != payload.user.otc,
                user.phone != payload.user.phone,
            )
        )

    @staticmethod
    def _build_detail_response(mountain_pass: MountainPass) -> MountainPassDetailResponse:
        return MountainPassDetailResponse(
            beauty_title=mountain_pass.beauty_title,
            title=mountain_pass.title,
            other_titles=mountain_pass.other_titles,
            connect=mountain_pass.connect,
            add_time=mountain_pass.add_time,
            user=UserSchema(
                email=mountain_pass.user.email,
                fam=mountain_pass.user.last_name,
                name=mountain_pass.user.first_name,
                otc=mountain_pass.user.middle_name,
                phone=mountain_pass.user.phone,
            ),
            coords=CoordinatesSchema(
                latitude=mountain_pass.coordinates.latitude,
                longitude=mountain_pass.coordinates.longitude,
                height=mountain_pass.coordinates.height,
            ),
            level=LevelSchema(
                winter=mountain_pass.levels.winter,
                spring=mountain_pass.levels.spring,
                summer=mountain_pass.levels.summer,
                autumn=mountain_pass.levels.autumn,
            ),
            images=[
                MountainPassImageResponse(
                    data=encode_image_data(image.image_data, image.content_type),
                    title=image.title,
                )
                for image in mountain_pass.images
            ],
            status=mountain_pass.status,
            created_at=mountain_pass.created_at,
            updated_at=mountain_pass.updated_at,
        )


MountainPassSubmissionService = MountainPassService
