from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project_template.api.common.database.models import BaseEntity


class Author(BaseEntity):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)


class Chapter(BaseEntity):
    __tablename__ = "chapter"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"), nullable=False)

    book: Mapped["Book"] = relationship("Book", back_populates="chapters")
    author: Mapped[Author] = relationship("Author")


class Book(BaseEntity):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"), nullable=False)

    chapters: Mapped[list[Chapter]] = relationship("Chapter", back_populates="book")
    author: Mapped[Author] = relationship("Author")
