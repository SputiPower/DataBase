from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MountainPass, PassCoordinate, PassImage, PassLevel, User
from app.schemas.pass_submission import PassSubmissionSchema


class MountainPassRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_user(self, payload: PassSubmissionSchema) -> User:
        user = self.session.scalar(select(User).where(User.email == payload.user.email))
        if user:
            user.first_name = payload.user.name
            user.last_name = payload.user.fam
            user.middle_name = payload.user.otc
            user.phone = payload.user.phone
            self.session.flush()
            return user

        user = User(
            email=payload.user.email,
            first_name=payload.user.name,
            last_name=payload.user.fam,
            middle_name=payload.user.otc,
            phone=payload.user.phone,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def create_pass(self, payload: PassSubmissionSchema, user_id: int) -> MountainPass:
        mountain_pass = MountainPass(
            beauty_title=payload.beauty_title,
            title=payload.title,
            other_titles=payload.other_titles,
            connect=payload.connect,
            add_time=payload.add_time,
            user_id=user_id,
        )
        self.session.add(mountain_pass)
        self.session.flush()
        return mountain_pass

    def create_coordinates(self, payload: PassSubmissionSchema, mountain_pass_id: int) -> PassCoordinate:
        coordinates = PassCoordinate(
            mountain_pass_id=mountain_pass_id,
            latitude=payload.coords.latitude,
            longitude=payload.coords.longitude,
            height=payload.coords.height,
        )
        self.session.add(coordinates)
        self.session.flush()
        return coordinates

    def create_levels(self, payload: PassSubmissionSchema, mountain_pass_id: int) -> PassLevel:
        levels = PassLevel(
            mountain_pass_id=mountain_pass_id,
            winter=payload.level.winter,
            spring=payload.level.spring,
            summer=payload.level.summer,
            autumn=payload.level.autumn,
        )
        self.session.add(levels)
        self.session.flush()
        return levels

    def create_images(self, payload: PassSubmissionSchema, mountain_pass_id: int) -> list[PassImage]:
        images: list[PassImage] = []
        for position, image in enumerate(payload.images):
            entity = PassImage(
                mountain_pass_id=mountain_pass_id,
                title=image.title,
                image_data=image.decoded_bytes,
                content_type=image.content_type,
                position=position,
            )
            self.session.add(entity)
            images.append(entity)

        self.session.flush()
        return images
