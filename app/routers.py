from fastapi import FastAPI

from app.routes import auth, api, expeditions, ws


def setup_routes(app: FastAPI):
    """Each Router specified in routes/* must be referenced in setup_routes(),
    as a new app.include_router() call."""
    app.include_router(api.router, prefix="", tags=["api"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(expeditions.router, prefix="/expeditions", tags=["expeditions"])
    app.include_router(ws.router, prefix="/ws", tags=["ws"])


TAGS_METADATA = [
    {"name": "api", "description": "General system endpoints for the API."},
    {"name": "auth", "description": "Authentication endpoints."},
    {"name": "expeditions", "description": "Expedition management endpoints."},
]
