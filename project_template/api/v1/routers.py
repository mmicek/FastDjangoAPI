from fastapi import APIRouter, Depends

from project_template.api.dependencies import (
    set_database_session_context,
    set_request_session_context,
)
from project_template.api.v1.library.api import router as library_router

api_v1_router = APIRouter(
    prefix="/api/v1",
    dependencies=[
        Depends(set_database_session_context),
        Depends(set_request_session_context),
    ],
    responses={404: {"description": "Not found"}, 403: {"description": "Forbidden"}},
)


api_v1_router.include_router(library_router)
