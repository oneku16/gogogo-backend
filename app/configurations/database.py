from urllib.parse import quote_plus

from .base import Settings


class PostgresSettings(Settings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    @property
    def dsn(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def dns_alembic(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD)
        host = self.POSTGRES_HOST
        if self.ENV_TYPE == "dev":
            host = "localhost"
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}" 


postgres_settings = PostgresSettings()  # type: ignore[call-arg]


__all__ = [
    "postgres_settings",
]
