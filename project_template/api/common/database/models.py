from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import Integer, MetaData, Select, delete, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from project_template.api.common.database.queries import EntityQueryManager
from project_template.api.common.database.session import get_request_db_session
from project_template.api.common.exceptions.exceptions import (
    ObjectDoesNotExistException,
)
from project_template.config import DATABASE_SCHEMA

if TYPE_CHECKING:
    from project_template.api.common.serializers import BaseSerializer


class BaseEntity(DeclarativeBase):
    """
    Base SQLAlchemy declarative model used as the foundation for all database entities.
    Defines shared metadata configuration, naming conventions, and schema settings.
    Provides common helper methods for CRUD-like operations tied to the request session lifecycle.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    __table_args__ = {"extend_existing": True}
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
        schema=DATABASE_SCHEMA,
    )
    objects: EntityQueryManager

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.objects = EntityQueryManager(cls)

    async def add_and_commit(self, session: AsyncSession = None, commit: bool = True):
        self._get_session(session).add(self)
        if commit:
            await self._get_session(session).commit()

    async def refresh(self, session: AsyncSession = None):
        await self._get_session(session).refresh(self)

    async def delete_and_commit(self, pk_field="id", session: AsyncSession = None):
        await self._get_session(session).execute(
            delete(self.__class__).where(
                getattr(self.__class__, pk_field) == getattr(self, pk_field)
            )
        )
        await self._get_session(session).commit()

    def copy(
        self, pk_field="id", skip_fields: list[str] = None, session: AsyncSession = None
    ):
        skip_fields = skip_fields or []
        new_instance = type(self)()
        self._get_session(session).add(new_instance)
        for column in self.__table__.columns:
            if column.name != pk_field and column.name not in skip_fields:
                setattr(new_instance, column.name, getattr(self, column.name))
        return new_instance

    @cached_property
    def to_dict(self):
        """
        Includes also aliases so if there is id = Column(alias="object_id") the value will be object_id: 12
        """
        return {
            c_name: getattr(self, c_name)
            for c_name, column_property in self.model_fields().items()
        }

    @classmethod
    @lru_cache(maxsize=None)
    def database_columns(cls) -> dict[str, Any]:
        mapper = inspect(cls)
        return {c.key: c for c in mapper.columns}

    @classmethod
    @lru_cache(maxsize=None)
    def model_fields(cls) -> dict[str, Any]:
        mapper = inspect(cls)
        return {c.key: c for c in mapper.column_attrs}

    @staticmethod
    def _get_session(session: AsyncSession = None) -> AsyncSession:
        return session if session else get_request_db_session()


TBS = TypeVar("TBS", bound="BaseSerializer")
TE = TypeVar("TE", bound=BaseEntity)


async def get_object_or_404[TE](
    query: Select[tuple[TE]],
    statement,
    *args,
    for_update=False,
) -> TE:
    """
    Executes a SELECT query and returns a single entity instance.
    Raises a domain-specific exception if no matching object is found.
    Supports optional row-level locking via SELECT FOR UPDATE.
    """

    session = get_request_db_session()
    query = query.where(statement, *args)
    if for_update:
        query = query.with_for_update(of=statement.left.table)
    entity = await session.scalar(query)
    if not entity:
        message = (
            f"Object of '{statement.left.table.name}' with "
            f"provided {statement.left.name} equal {statement.right.value} does not exist."
        )
        raise ObjectDoesNotExistException(
            message=message,
        )
    return entity
