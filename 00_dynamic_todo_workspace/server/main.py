"""ASGI entry point kept intentionally thin for `uvicorn main:app`."""

from app.factory import create_app

app = create_app()
