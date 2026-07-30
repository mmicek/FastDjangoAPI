from typing import TYPE_CHECKING

from sqlalchemy import UnaryExpression, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from project_template.api.common.database.session import get_request_db_session

if TYPE_CHECKING:
    from project_template.api.common.database.models import BaseEntity


class EntityQuery:
    def __init__(self, entity_query_manager: EntityQueryManager):
        self.entity_query_manager = entity_query_manager
        self.query = select(self.entity_query_manager.entity_class)

    def all(self):
        return self

    def filter(self, statement, *args):
        # TYPE THE INPUT PARAMETER
        self.query = self.query.where(statement, *args)
        return self

    def order_by(self, *order_clauses: list[UnaryExpression]):
        self.query = self.query.order_by(*order_clauses)
        return self

    async def fetch(
        self,
        session: AsyncSession = None,
        many: bool = True,
        raise_if_more_than_one: bool = False,
    ):
        session = session or get_request_db_session()
        if many:
            return (await session.scalars(self.query)).all()
        else:
            return await self.get(
                session, raise_if_more_than_one=raise_if_more_than_one
            )

    async def get(
        self, session: AsyncSession = None, raise_if_more_than_one: bool = False
    ):
        session = session or get_request_db_session()
        if raise_if_more_than_one:
            return (await session.execute(self.query)).scalar_one_or_none()
        else:
            return await session.scalar(self.query)

    async def count(self, session: AsyncSession = None):
        session = session or get_request_db_session()
        stmt = select(func.count()).select_from(self.query.subquery())
        return await session.scalar(stmt)


class EntityQueryManager:
    def __init__(self, entity_class: type[BaseEntity]):
        self.entity_class = entity_class

    def all(self):
        return EntityQuery(self).all()

    def filter(self, statement, *args):
        return EntityQuery(self).filter(statement, *args)

    async def get(
        self, session: AsyncSession = None, raise_if_more_than_one: bool = False
    ):
        return await EntityQuery(self).get(
            session, raise_if_more_than_one=raise_if_more_than_one
        )

    async def count(self, session: AsyncSession = None):
        return await EntityQuery(self).count(session)
