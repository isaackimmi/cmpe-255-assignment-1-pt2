"""ASGI entry point kept stable for ``uvicorn server.app:app``."""
from server.application import create_app

app = create_app()

__all__ = ["app", "create_app"]
