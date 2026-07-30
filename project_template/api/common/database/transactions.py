from contextlib import _AsyncGeneratorContextManager  # noqa

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession


class Atomic(_AsyncGeneratorContextManager):
    """
    Context manager that allows writing transaction-oriented code.
    Enables making transactions and savepoint within transactions.
    SQL Alchemy session overlay.
    """

    def __init__(self, *args, session: AsyncSession, **kwargs):
        self._session: AsyncSession = session
        self._connection: AsyncConnection = self._session.bind
        super().__init__(self._transaction, args, kwargs)

    async def _transaction(self):
        """
        Needs to flush changes to database due to possible rollback in this transaction.
        Rollback will also clean up session, so if some entities were added to session before this transaction,
            they will also be "rolled back"
        """
        await self._session.commit()

        transaction_open_function = self._connection.begin  # BEGIN + COMMIT
        if self._connection.in_transaction():
            # If there is already opened transaction, open nested transaction (savepoint)
            transaction_open_function = (
                self._connection.begin_nested
            )  # SAVEPOINT + RELEASE

        async with transaction_open_function() as self._transaction:
            try:
                yield self
            except Exception:
                await self._transaction.rollback()
                raise
            else:
                if self._transaction.is_active:
                    await self._session.commit()  # Must be called
                    await self._transaction.commit()

    async def rollback(self):
        await self._session.rollback()
        if self._transaction.is_active:
            await self._transaction.rollback()


def atomic(*args, **kwargs):
    def decorator(function):
        async def wrapper(*f_args, **f_kwargs):
            async with Atomic(*args, **kwargs):
                return await function(*f_args, **f_kwargs)

        return wrapper

    return decorator
