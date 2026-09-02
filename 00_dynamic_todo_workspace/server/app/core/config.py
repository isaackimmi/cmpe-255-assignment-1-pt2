from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Fieldnote Project 00 API"
    version: str = "1.1.0"
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:5173", "http://localhost:5173")


settings = Settings()
