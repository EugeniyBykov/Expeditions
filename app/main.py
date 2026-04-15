import uvicorn
from fastapi import FastAPI

from app.middlewares import request_handler
from app.routers import setup_routes
from app.routers import TAGS_METADATA
from app.settings import api_settings, api_docs_settings

app = FastAPI(
    title=api_docs_settings.title,
    version=api_docs_settings.version,
    openapi_tags=TAGS_METADATA
)
app.middleware("http")(request_handler)
setup_routes(app)


def run():
    """Run the API using Uvicorn"""
    uvicorn.run(
        app,
        host=api_settings.host,
        port=api_settings.port
    )
