from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get(
    "/status",
    description="Get API status."
)
async def get_status():
    return PlainTextResponse(status_code=200, content="OK")
