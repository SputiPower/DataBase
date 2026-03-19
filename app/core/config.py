from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DataBase"
    app_version: str = "1.0.0"

    db_host: str = Field(alias="FSTR_DB_HOST")
    db_port: int = Field(default=5432, alias="FSTR_DB_PORT")
    db_login: str = Field(alias="FSTR_DB_LOGIN")
    db_pass: str = Field(alias="FSTR_DB_PASS")
    db_name: str = Field(default="database", alias="FSTR_DB_NAME")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_login}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
