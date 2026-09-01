"""ASGI entry point kept intentionally small for `uvicorn server.main:app`."""
from .app import create_app

app = create_app()
