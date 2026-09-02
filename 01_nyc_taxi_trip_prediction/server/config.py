from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    title: str = "Project 01 · NYC Taxi Trip Duration API"
    version: str = "1.0.0"
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")


settings = Settings()
