from typing import Annotated

from pydantic import Field

from project_template.api.common.fields import PrimaryKeyRelation
from project_template.api.common.serializers import BaseModelSerializer
from project_template.api.v1.library.models import Author, Book, Chapter


class AuthorSerializer(BaseModelSerializer):
    id: int = None  # For CREATE endpoint do not insert id. It will be auto generated.
    first_name: str
    last_name: str

    class Meta:
        model = Author


class ChapterSerializer(BaseModelSerializer):
    id: int = None  # For CREATE endpoint do not insert id. It will be auto generated.
    name: str
    content: str
    author_id: Annotated[int, PrimaryKeyRelation(model=Author)]

    class Meta:
        model = Chapter


class ChapterDetailSerializer(ChapterSerializer):
    author: AuthorSerializer
    author_id: int = Field(exclude=True)  # Exclude from output - write only


class BookSerializer(BaseModelSerializer):
    id: int = None  # For CREATE endpoint do not insert id. It will be auto generated.
    title: str
    author_id: Annotated[int, PrimaryKeyRelation(model=Author)]

    class Meta:
        model = Book


class BookDetailSerializer(BookSerializer):
    author: AuthorSerializer
    author_id: int = Field(exclude=True)  # Exclude from output - write only


class BookWithChaptersSerializer(BookDetailSerializer):
    chapters: list[ChapterDetailSerializer]
