from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "InsightQuery FastAPI App"
    debug: bool = True

settings = Settings() 