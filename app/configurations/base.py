from pydantic_settings import BaseSettings, SettingsConfigDict

from .utilities import get_env_file, get_env_type


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    ENV_TYPE: str
