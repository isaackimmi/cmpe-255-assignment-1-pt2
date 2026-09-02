"""Service configuration with an explicit local-only CORS policy."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    title: str = "Basket Signals API"
    version: str = "2.0.0"
    data_source: str = "data/transactions.csv"
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")


settings = Settings()
