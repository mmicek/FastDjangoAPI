from enum import StrEnum

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings

DATABASE_SCHEMA = (
    "project_template"  # DO NOT CHANGE THIS VALUE, AS IT WILL DESTROY DATABASE
)


class Env(StrEnum):
    LOCAL = "local"
    DEV = "dev"
    DEMO = "demo"
    PROD = "prod"
    TEST = "test"

    @staticmethod
    def is_local(env: Env) -> bool:
        """Returns True if the environment is local or test (non-production - meaning not dev, demo or prod)"""

        return env == Env.LOCAL or env == Env.TEST


class Settings(BaseSettings):
    # Deployment
    ENV: str | None = Env.LOCAL
    SPRING_PROFILES_ACTIVE: str | None = "local"
    DEBUG_MODE: bool = False

    HOST: str = "0.0.0.0"  # noqa
    PORT: int = 80
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # SQL
    DATABASE_NAME: str = Field(
        default="database",
        validation_alias=AliasChoices("DATABASE_NAME"),
    )
    DATABASE_HOST: str = Field(
        default="localhost",
        validation_alias=AliasChoices("DATABASE_HOST"),
    )
    DATABASE_PORT: int = Field(
        default=5432,
        validation_alias=AliasChoices("DATABASE_PORT"),
    )
    DATABASE_USER: SecretStr = Field(
        default="postgres",
        validation_alias=AliasChoices("DATABASE_USER"),
    )
    DATABASE_PASSWORD: SecretStr = Field(
        default="postgres",
        validation_alias=AliasChoices("DATABASE_PASSWORD"),
    )
    DATABASE_DRIVER: str = "postgresql+asyncpg"

    @property
    def database_connection_string(self) -> str:
        connection_string = (
            f"{self.DATABASE_DRIVER}://{self.DATABASE_USER.get_secret_value()}:{self.DATABASE_PASSWORD.get_secret_value()}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )
        return connection_string


settings = Settings()
