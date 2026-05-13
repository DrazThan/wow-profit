from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tsm_api_key: str = ""
    tsm_auth_url: str = "https://auth.tradeskillmaster.com/oauth2/token"
    tsm_realm_api_url: str = "https://realm-api.tradeskillmaster.com"
    tsm_pricing_api_url: str = "https://pricing-api.tradeskillmaster.com"

    nexushub_base_url: str = "https://api.nexushub.co/wow-classic/v1"

    default_realm: str = "faerlina"
    default_faction: str = "horde"
    default_region: str = "us"

    database_url: str = "postgresql+asyncpg://ahtracker:ahtracker@localhost:5432/ah_tracker"
    redis_url: str = ""

    recipes_path: str = "/data/recipes.json"
    items_path: str = "/data/items.json"


settings = Settings()
