from fastapi import FastAPI

from app.routes import api
from app.routes import auth


def setup_routes(app: FastAPI):
    """Each Router specified in routes/* must be referenced in setup_routes(),
    as a new app.include_router() call."""
    app.include_router(api.router, prefix="", tags=["api"])
    app.include_router(auth.router, prefix="", tags=["auth"])


TAGS_METADATA = [
    {"name": "api", "description": "General system endpoints for the API."},
    {"name": "auth", "description": "Authentication endpoints."},
]
