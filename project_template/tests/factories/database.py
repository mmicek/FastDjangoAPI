from typing import Any, Type, TypeVar

from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from project_template.api.common.database.models import BaseEntity

faker = Faker()
T = TypeVar("T")


def get_body_from_entity(entity: BaseEntity) -> dict:
    """Extracts a dict representation of a SQLAlchemy entity using its mapped column attributes."""
    return {
        attr.key: getattr(entity, attr.key)
        for attr in inspect(entity).mapper.column_attrs
        if attr.key != "id"
    }


def random_by_type(pytype: type) -> Any:
    if pytype is str:
        return faker.word()
    elif pytype is int:
        return faker.random_int(1, 1000)
    elif pytype is float:
        return faker.pyfloat(left_digits=2, right_digits=4, positive=True)
    elif pytype is bool:
        return faker.boolean()
    else:
        raise NotImplementedError


async def create_entity_factory(
    session: AsyncSession,
    entity_type: Type[BaseEntity] | Type[SQLAlchemyModelFactory],
    add_and_commit: bool = True,
    **overrides,
) -> T:
    """
    Factory utility for creating database entities or SQLAlchemy model factory instances.
    Automatically populates missing fields with fake data and optionally persists the instance.
    """
    if issubclass(entity_type, SQLAlchemyModelFactory):
        entity_type._meta.sqlalchemy_session = session
        instance = entity_type.build(**overrides)
        model_cls = entity_type._meta.model
    else:
        model_cls = entity_type
        instance = model_cls()

    current = {
        col.key: getattr(instance, col.key) for col in model_cls.__mapper__.column_attrs
    }

    for attribute in model_cls.__mapper__.column_attrs:
        name = attribute.key
        column = model_cls.__mapper__.columns[name]

        if current.get(name) is not None:
            continue

        if name in overrides:
            setattr(instance, name, overrides[name])
            continue

        if name in ["created_at", "updated_at", "deleted_at", "deleted_by"] or (
            (column.primary_key and column.autoincrement) or column.foreign_keys
        ):
            continue

        setattr(instance, name, random_by_type(column.type.python_type))

    if add_and_commit:
        session.add(instance)
        await session.commit()
    return instance
