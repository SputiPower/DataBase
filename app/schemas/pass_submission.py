import base64
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.exceptions import ValidationError


PHONE_REGEX = re.compile(r"^[0-9+\-\s()]{5,32}$")
DATA_URI_REGEX = re.compile(r"^data:(?P<content_type>[\w./+-]+);base64,(?P<data>.+)$", re.IGNORECASE)
REQUIRED_FIELD_ERROR_PREFIX = "Отсутствует обязательное поле"


def empty_str_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class UserSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    fam: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    otc: str | None = Field(default=None, max_length=100)
    phone: str = Field(min_length=5, max_length=32)

    @field_validator("otc", mode="before")
    @classmethod
    def normalize_middle_name(cls, value: str | None) -> str | None:
        return empty_str_to_none(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not PHONE_REGEX.fullmatch(value):
            raise ValueError("Некорректный номер телефона")
        return value


class CoordinatesSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    latitude: Decimal
    longitude: Decimal
    height: int

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: Decimal) -> Decimal:
        if value < Decimal("-90") or value > Decimal("90"):
            raise ValueError("Широта должна быть в диапазоне от -90 до 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: Decimal) -> Decimal:
        if value < Decimal("-180") or value > Decimal("180"):
            raise ValueError("Долгота должна быть в диапазоне от -180 до 180")
        return value

    @field_validator("height")
    @classmethod
    def validate_height(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Высота должна быть неотрицательной")
        return value


class LevelSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    winter: str | None = Field(default=None, max_length=16)
    spring: str | None = Field(default=None, max_length=16)
    summer: str | None = Field(default=None, max_length=16)
    autumn: str | None = Field(default=None, max_length=16)

    @field_validator("winter", "spring", "summer", "autumn", mode="before")
    @classmethod
    def normalize_optional_level(cls, value: str | None) -> str | None:
        return empty_str_to_none(value)


class ImageSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    data: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=255)

    @property
    def decoded_bytes(self) -> bytes:
        raw_data = self.data
        match = DATA_URI_REGEX.match(raw_data)
        if match:
            raw_data = match.group("data")
        try:
            return base64.b64decode(raw_data, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValidationError("Некорректные данные изображения: ожидается base64") from exc

    @property
    def content_type(self) -> str | None:
        match = DATA_URI_REGEX.match(self.data)
        return match.group("content_type") if match else None


class PassSubmissionSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    beauty_title: str | None = Field(default=None, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    other_titles: str | None = Field(default=None, max_length=255)
    connect: str | None = None
    add_time: datetime
    user: UserSchema
    coords: CoordinatesSchema
    level: LevelSchema
    images: list[ImageSchema] = Field(min_length=1)

    @field_validator("beauty_title", "other_titles", "connect", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return empty_str_to_none(value)

    @field_validator("add_time", mode="before")
    @classmethod
    def parse_add_time(cls, value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Некорректный формат add_time. Ожидается YYYY-MM-DD HH:MM:SS") from exc

    @model_validator(mode="before")
    @classmethod
    def validate_required_sections(cls, data: object) -> object:
        if not isinstance(data, dict):
            raise ValueError("Тело запроса должно быть JSON-объектом")
        for field_name in ("user", "coords", "level", "images", "title", "add_time"):
            if field_name not in data or data[field_name] in (None, ""):
                raise ValueError(f"Отсутствует обязательное поле {field_name}")
        return data


class SubmitDataResponse(BaseModel):
    status: int
    message: str | None
    id: int | None


def build_validation_message(errors: list[dict]) -> str:
    first_error = errors[0]
    location = [str(item) for item in first_error.get("loc", []) if item != "body"]
    message = first_error.get("msg", "Некорректные входные данные")
    error_type = first_error.get("type")

    if error_type == "missing" and location:
        return f"{REQUIRED_FIELD_ERROR_PREFIX} {'.'.join(location)}"

    if error_type == "json_invalid":
        return "Некорректный JSON"

    if location:
        return f"{'.'.join(location)}: {message}"
    return message


def coerce_decimal(value: str | float | int | Decimal) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError("Некорректное числовое значение координат") from exc
