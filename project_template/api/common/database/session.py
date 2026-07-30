from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

database_session_context_var: ContextVar[AsyncSession] = ContextVar(
    "database_session_context_var"
)
request_session_context_var: ContextVar[Request] = ContextVar(
    "request_session_context_var"
)


def get_request_db_session() -> AsyncSession:
    return database_session_context_var.get()


def get_request_session() -> Request:
    return request_session_context_var.get()
