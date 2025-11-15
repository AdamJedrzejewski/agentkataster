"""Configuration management for AgentKataster."""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # Database
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="agentkataster", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="postgres", alias="DB_PASSWORD")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    # Geoportal
    uldk_wfs_url: str = Field(
        default="https://uldk.gugik.gov.pl/service.svc/get",
        alias="ULDK_WFS_URL"
    )
    geoportal_base_url: str = Field(
        default="https://polska.geoportal2.pl",
        alias="GEOPORTAL_BASE_URL"
    )

    # Scraper
    concurrent_requests: int = Field(default=5, alias="CONCURRENT_REQUESTS")
    request_delay: float = Field(default=1.0, alias="REQUEST_DELAY")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/scraper.log", alias="LOG_FILE")

    @property
    def database_url(self) -> str:
        """Get SQLAlchemy database URL."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
