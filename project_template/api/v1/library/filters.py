from fastapi_filter.contrib.sqlalchemy import Filter

from project_template.api.common.filters import BaseModelFilter
from project_template.api.v1.library.models import Book


class BookFilter(BaseModelFilter):
    # You can also define all filters introduced by fastapi_filter library

    class Constants(Filter.Constants):
        model = Book
        fields = ["id", "title"]
