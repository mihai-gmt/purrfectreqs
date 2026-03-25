"""
Application configuration.

All environment variables are loaded and validated here at startup.
The rest of the application imports `settings` from this module.
Never call os.getenv() directly in application code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Pydantic-settings reads from the .env file and validates types.
    If a required variable is missing, the app fails at startup with
    a clear error listing which variables are absent.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Project name

    project_name: str = "Purrfectreqs"
    project_description: str = "AI-powered requirements management system"
    project_version: str = "0.1.0"

    # Database
    database_url: str

    # Redis
    redis_url: str

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwtf_refresh_token_expire_days: int = 7

    # OLLAMA
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "mistral:7b-instruct-v0.3-q4_K_M"
    ollama_timeout_seconds: int = 60

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-V2"

    # Application
    app_env: str = "development"
    app_debug: bool = False
    log_level: str = "info"

    # File Uploads

    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 10
    allowed_file_types: str = ".txt, .md, .docx, .doc"

    @property
    def allowed_file_types_list(self) -> list[str]:
        """Return allowed file types as a list."""
        return [t.strip() for t in self.allowed_file_types(",")]

    @property
    def is_development(self) -> bool:
        """True when running in development environment."""
        return self.app_env == "development"


# Single instance used throughout the application.
# Import with: from app.core.config import settings
settings = Settings()
