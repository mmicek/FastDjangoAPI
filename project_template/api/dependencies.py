from fastapi.security import HTTPBearer
from starlette.requests import Request

from project_template.api.common.context import ContextSetContextManager
from project_template.api.common.database.session import (
    database_session_context_var,
    request_session_context_var,
)

oauth2_scheme = HTTPBearer()


async def set_database_session_context(request: Request):
    async with request.app.session_manager.session() as database_session:
        with ContextSetContextManager(database_session_context_var, database_session):
            yield database_session


async def set_request_session_context(request: Request):
    with ContextSetContextManager(request_session_context_var, request):
        yield request
