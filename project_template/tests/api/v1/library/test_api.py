import pytest

from project_template.api.v1.library.api import BookViewSet
from project_template.api.v1.library.models import Author, Book, Chapter
from project_template.tests.factories.database import create_entity_factory
from project_template.tests.helpers.assertions import assert_status
from project_template.tests.helpers.crud import crud_view_set_test


@pytest.mark.asyncio
async def test_api(client, context_db, book):
    crud_view_set_test(client, book, "/api/v1/library/", BookViewSet)


class TestAuthorViewSet:
    async def test_crud(self, client, context_db):

        # CREATE
        body = {
            "first_name": "Joe",
            "last_name": "Doe",
        }
        response = client.post("/api/v1/library/authors/", json=body)
        assert_status(response)
        data = response.json()
        assert data["first_name"] == body["first_name"]
        assert data["last_name"] == body["last_name"]
        author_id = data["id"]

        assert await Author.objects.count() == 1
        update_body = {
            "first_name": "New name",
        }
        response = client.patch(
            f"/api/v1/library/authors/{author_id}/", json=update_body
        )
        assert_status(response)
        author = await Author.objects.get(raise_if_more_than_one=True)
        assert author.first_name == update_body["first_name"]

        # LIST
        response = client.get("/api/v1/library/authors/")
        assert_status(response)
        assert len(response.json()) == 1

        # RETRIEVE
        response = client.get(f"/api/v1/library/authors/{author_id}/")
        assert_status(response)
        assert response.json()["last_name"] == body["last_name"]
        assert response.json()["first_name"] == update_body["first_name"]

        # DELETE
        response = client.delete(f"/api/v1/library/authors/{author_id}/")
        assert_status(response)
        assert (await Author.objects.get()) is None


class TestBookViewSet:
    @pytest.mark.asyncio
    async def test_crud(self, client, context_db, book: Book, author: Author):
        # ADD-CHAPTER
        body = {
            "name": "Chapter 1",
            "content": "This is content of the first chapter",
            "author_id": author.id,
        }
        response = client.post(
            f"/api/v1/library/books/{book.id}/add-chapter/", json=body
        )
        assert_status(response)

        chapter = await Chapter.objects.get()
        assert chapter.name == body["name"]
        assert chapter.content == body["content"]
        assert chapter.author_id == author.id

        # ADD-CHAPTER Invalid author
        body = {
            "name": "Chapter 1",
            "content": "This is content of the first chapter",
            "author_id": -1,
        }
        response = client.post(
            f"/api/v1/library/books/{book.id}/add-chapter/", json=body
        )
        assert_status(response, 404)

        # CREATE
        new_book_author = await create_entity_factory(context_db, Author)
        body = {
            "title": "Dev Ops Guide",
            "author_id": new_book_author.id,
        }
        response = client.post("/api/v1/library/books/", json=body)
        assert_status(response, 200)
        data = response.json()
        assert data["author_id"] == new_book_author.id
        assert data["title"] == "Dev Ops Guide"
        assert data["id"]
        new_book_id = data["id"]

        # RETRIEVE
        response = client.get(f"/api/v1/library/books/{new_book_id}/")
        assert_status(response, 200)
        data = response.json()
        assert data["title"] == "Dev Ops Guide"
        assert data["id"]
        assert data["author"]["first_name"] == new_book_author.first_name
        assert data["author"]["last_name"] == new_book_author.last_name

        # LIST
        response = client.get("/api/v1/library/books/")
        assert_status(response, 200)
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == book.title
        assert data[1]["title"] == body["title"]
        assert data[0]["author_id"] == author.id
        assert data[1]["author_id"] == new_book_author.id
        # For list, we do not want to serialize all objects# For list we do not want to serialize all objects
        assert data[0].get("author") is None
        assert data[1].get("author") is None
        assert data[0].get("chapters") is None
        assert data[1].get("chapters") is None

        # DELETE
        response = client.delete(f"/api/v1/library/books/{new_book_id}/")
        assert_status(response, 200)

        # UPDATE
        update_body = {"title": "New Title"}
        response = client.patch(f"/api/v1/library/books/{book.id}/", json=update_body)
        assert_status(response)
        assert response.json()["title"] == update_body["title"]
        await book.refresh(context_db)
        assert book.title == update_body["title"]

        # CHAPTERS
        response = client.get(f"/api/v1/library/books/{book.id}/chapters-with-authors/")
        assert_status(response, 200)
        data = response.json()
        assert data["title"] == book.title
        assert (
            data.get("author_id") is None
        )  # Remove author_id from output as we serialize whole author entity
        assert data["author"]["first_name"] == author.first_name
        assert len(data["chapters"]) == 1
        assert data["chapters"][0]["name"] == chapter.name
        assert data["chapters"][0]["content"] == chapter.content
        assert (
            data["chapters"][0].get("author_id") is None
        )  # Remove author_id from output as we serialize whole author entity
        assert data["chapters"][0]["author"]["first_name"] == author.first_name
        assert data["chapters"][0]["author"]["last_name"] == author.last_name
