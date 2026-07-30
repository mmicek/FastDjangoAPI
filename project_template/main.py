import asyncio
import logging.config
import sys
from contextlib import asynccontextmanager
from typing import Callable

import uvicorn
from cachetools import TTLCache
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from project_template.api.common.database.managers import DatabaseSessionManager
from project_template.api.common.exceptions.handlers import (
    http_exception_handler,
    internal_server_error_handler,
    request_validation_exception_handler,
)
from project_template.api.common.middlewares import TrailingSlashRedirectMiddleware
from project_template.api.router import api_common_router
from project_template.api.v1.routers import api_v1_router
from project_template.config import settings
from project_template.logger import configure_logging


class HiveApp(FastAPI):
    session_manager: DatabaseSessionManager


@asynccontextmanager
async def lifespan(h_app: HiveApp):
    configure_logging()
    h_app.session_manager = DatabaseSessionManager(
        settings.database_connection_string,
        engine_kwargs={
            "pool_pre_ping": True,
            "pool_size": 25,
            "max_overflow": 25,
        },
    )
    yield


def create_app(life_span: Callable) -> HiveApp:
    hive_app = HiveApp(
        title="Hive API",
        description="API for Hive application",
        version="1.0.0",
        lifespan=life_span,
    )
    hive_app.cache = TTLCache(
        maxsize=10_000,
        ttl=60 * 60 * 24 * 3,  # 3 days
    )
    hive_app.add_middleware(TrailingSlashRedirectMiddleware)
    hive_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.DEBUG_MODE:
        hive_app.add_exception_handler(500, internal_server_error_handler)
    hive_app.add_exception_handler(HTTPException, http_exception_handler)
    hive_app.add_exception_handler(
        RequestValidationError, request_validation_exception_handler
    )
    hive_app.include_router(api_v1_router)
    hive_app.include_router(api_common_router)
    return hive_app


def get_app():
    return create_app(life_span=lifespan)


if __name__ == "__main__":
    import warnings

    warnings.simplefilter("ignore")
    try:
        app = get_app()
        if sys.platform == "win32":
            from asyncio import WindowsSelectorEventLoopPolicy

            # Sqlalchemy.exc.InterfaceError: (psycopg.InterfaceError) Psycopg cannot use the 'ProactorEventLoop'
            # to run in async mode. Please use a compatible event loop, for instance by running
            # 'asyncio.run(..., loop_factory=asyncio.SelectorEventLoop(selectors.SelectSelector()))'
            asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            ws_ping_interval=3600.0,  # 1 minute
            ws_ping_timeout=3600.0,  # 1 minute
        )
    except Exception as exc:
        logging.getLogger("errors").error(
            f"Received unhandled exception: {exc}", exc_info=True
        )
        raise exc
