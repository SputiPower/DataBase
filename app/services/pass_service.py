from app.core.database import DatabaseManager
from app.core.exceptions import ValidationError
from app.repositories.pass_repository import MountainPassRepository
from app.schemas.pass_submission import PassSubmissionSchema


class MountainPassSubmissionService:
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
