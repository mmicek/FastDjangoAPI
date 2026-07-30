import pytest

from project_template.api.v1.library.models import Author, Book
from project_template.tests.factories.database import create_entity_factory


@pytest.fixture()
async def book(context_db, author):
    return await create_entity_factory(context_db, Book, author_id=author.id)


@pytest.fixture()
async def author(context_db):
    return await create_entity_factory(context_db, Author)
