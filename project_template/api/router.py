from fastapi import APIRouter

from project_template.api.v1.routers import api_v1_router

api_common_router = APIRouter(
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


api_common_router.include_router(api_v1_router)
