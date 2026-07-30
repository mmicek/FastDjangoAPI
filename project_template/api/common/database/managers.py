import contextlib
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine


class DatabaseSessionManager:
    """
    Manages the lifecycle of SQLAlchemy async engine, connections, and sessions.
    Provides context-managed access to database sessions and connections with automatic cleanup.
    Ensures safe acquisition and disposal of database resources in asynchronous environments.
    """

    def __init__(self, url: str, engine_kwargs: dict[str, Any]):
        self.engine = create_async_engine(url, **engine_kwargs)

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self.engine is None:
            raise RuntimeError("DatabaseSessionManager has been closed.")

        async with self.engine.connect() as connection:
            session = self._get_async_session(connection)
            try:
                yield session
            finally:
                await session.close()
                await connection.close()
                # Clean up all existing connections (do not return it to the engine pool)
                await self.engine.dispose()

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """
        Create an AsyncConnection that automatically rolls back the transaction on exception or commits it
         on successful execution.
        """
        if self.engine is None:
            raise RuntimeError("DatabaseSessionManager has been closed.")

        async with self.engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise
            finally:
                await connection.close()
                # Clean up all existing connections (do not return it to the engine pool)
                await self.engine.dispose()

    async def close(self):
        if self.engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized.")
        await self.engine.dispose()
        self.engine = None

    @staticmethod
    def _get_async_session(connection) -> AsyncSession:
        return AsyncSession(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            close_resets_only=False,
            bind=connection,
        )
