import contextlib
from typing import Any, AsyncIterator
from unittest import mock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.postgres import PostgresContainer

from project_template.api.common.context import ContextSetContextManager
from project_template.api.common.database.managers import DatabaseSessionManager
from project_template.api.common.database.models import BaseEntity
from project_template.api.common.database.session import database_session_context_var
from project_template.api.common.database.transactions import Atomic
from project_template.config import DATABASE_SCHEMA, settings


class TestDatabaseManager(DatabaseSessionManager):
    def __init__(self, url: str, engine_kwargs: dict[str, Any]):
        super().__init__(url, engine_kwargs)

    async def prepare_database(self):
        await self.create_models()

    async def create_models(self) -> None:
        async with self.engine.connect() as conn:
            await conn.execute(
                text(f"DROP SCHEMA IF EXISTS {DATABASE_SCHEMA} CASCADE;")
            )  # noqa F405
            await conn.execute(text(f"CREATE SCHEMA {DATABASE_SCHEMA};"))  # noqa F405
            await conn.run_sync(BaseEntity.metadata.create_all)
            await conn.commit()


@pytest.fixture(scope="function")
async def context_db(_context_session):
    """
    Wraps session within transaction, that always is rolled back,
    to clean up database after each test.




    Needs session to be already in context, to be able to use Atomic feature
    """
    database_session = _context_session
    async with Atomic(session=database_session) as transaction:
        yield _context_session
        await transaction.rollback()


@pytest.fixture(scope="session")
async def _test_database_manager():
    postgres = PostgresContainer(
        "postgres:17-alpine",
        dbname="project_template-test",
        username="postgres",
        password="postgres",
    )
    try:
        postgres.start()
        database_connection_string = postgres.get_connection_url().replace(
            "psycopg2", "psycopg"
        )

        settings.DATABASE_NAME = "project_template"
        yield TestDatabaseManager(
            database_connection_string,
            engine_kwargs={"pool_pre_ping": True},
        )
    finally:
        postgres.stop()


@pytest.fixture(scope="session")
async def _init_db(_test_database_manager):
    await _test_database_manager.prepare_database()
    yield


@pytest.fixture(scope="function")
async def _init_session(_test_database_manager, _init_db):
    async with _test_database_manager.session() as _session:

        @contextlib.asynccontextmanager
        async def _session_mock() -> AsyncIterator[AsyncSession]:
            yield _session

        with mock.patch.object(_test_database_manager, "session", _session_mock):
            yield _session


@pytest.fixture(scope="function")
def _context_session(_init_session):
    """
    Sets database session to context var - ContextVar("db_session")
    This must be as sync fixture as in async context will be set in different task.
    """
    with ContextSetContextManager(database_session_context_var, _init_session):
        yield _init_session
