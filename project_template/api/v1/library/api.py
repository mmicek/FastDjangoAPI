from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from project_template.api.common.actions import action
from project_template.api.common.enums import ViewSetAction
from project_template.api.common.views import ModelViewSet
from project_template.api.v1.library.filters import BookFilter
from project_template.api.v1.library.models import Author, Book, Chapter
from project_template.api.v1.library.serializers import (
    AuthorSerializer,
    BookDetailSerializer,
    BookSerializer,
    BookWithChaptersSerializer,
    ChapterDetailSerializer,
    ChapterSerializer,
)

router = APIRouter(prefix="/library")


class AuthorViewSet(ModelViewSet):
    url_prefix = "authors"
    model = Author
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    create_serializer_class = AuthorSerializer


class BookViewSet(ModelViewSet):
    url_prefix = "books"
    model = Book
    filter_class = BookFilter
    create_serializer_class = BookSerializer

    def get_queryset(self):
        qs = select(self.model)
        if self.action == "get_chapters_with_authors":
            qs = qs.options(selectinload(Book.chapters).selectinload(Chapter.author))
        return qs.order_by(Book.id.asc())

    def get_serializer_class(self, _action=None):
        if _action == ViewSetAction.LIST:
            return BookSerializer  # We do not want to serialize whole author for list -> too big output
        elif _action == ViewSetAction.RETRIEVE:
            return BookDetailSerializer  # Serialize also author entity
        return super().get_serializer_class(_action)

    @action(method="post", detail=True, url_path="add-chapter/")
    async def add_chapter(self, body: ChapterSerializer):
        book = await self.get_object()
        page = await self.create_from_serializer(
            body, Chapter, fetch_related=True, add_and_commit=True, book_id=book.id
        )
        # Attribute 'fetch_related' will check if the author provided by id exists. If not, it will raise 404.
        return self.serialize_from_object(page, ChapterDetailSerializer)

    @action(method="get", detail=True, url_path="chapters-with-authors/")
    async def get_chapters_with_authors(self):
        book = await self.get_object()
        return self.serialize_from_object(book, BookWithChaptersSerializer)


BookViewSet.register(router)
AuthorViewSet.register(router)
