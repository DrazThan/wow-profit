from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    default_realm: str = "faerlina"
    default_faction: str = "horde"

    database_url: str = "postgresql+asyncpg://ahtracker:ahtracker@localhost:5432/ah_tracker"
    redis_url: str = ""

    recipes_path: str = "/data/recipes.json"
    items_path: str = "/data/items.json"

    max_upload_size_mb: int = 50
    upload_dir: str = "/tmp/ah_uploads"


settings = Settings()
