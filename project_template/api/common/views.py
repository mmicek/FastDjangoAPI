import inspect
from copy import deepcopy
from functools import lru_cache
from typing import Any, Callable, Dict, Generic, TypeVar, get_args, get_type_hints

from fastapi import APIRouter, Depends, Query
from fastapi_filter import FilterDepends
from psycopg.errors import ForeignKeyViolation
from pydantic import BaseModel, ConfigDict, Field, create_model
from sqlalchemy import Select, asc, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from project_template.api.common.context import (
    _request_action_context_var,
    _request_pk_context_var,
)
from project_template.api.common.database.models import BaseEntity, get_object_or_404
from project_template.api.common.database.session import get_request_db_session
from project_template.api.common.enums import ViewSetAction
from project_template.api.common.exceptions.exceptions import (
    ApiPydanticValidationException,
    ForeignKeyViolationException,
)
from project_template.api.common.filters import BaseFilter
from project_template.api.common.serializers import BaseSerializer

MODEL_TYPE = TypeVar("MODEL_TYPE", bound=BaseEntity)
E = TypeVar("E", bound=BaseEntity)
S = TypeVar("S", bound=BaseSerializer)
CustomActionName = TypeVar("CustomActionName", bound=str)


class PaginationParams(BaseModel):
    """
    Defines pagination and ordering parameters for list endpoints.
    Supports page-based pagination and Django-style ordering strings.
    """

    page: int | None = Query(None, ge=0)
    page_size: int | None = Query(None, ge=1, le=100)
    order_by: str | None = None


class GenericViewSet(Generic[MODEL_TYPE]):
    """
    Base class for building DRF-like viewsets on top of FastAPI and SQLAlchemy.
    Provides shared configuration for model, serializers, filters, and routing.
    Acts as a foundation for automatically registering CRUD endpoints via mixins.
    """

    url_prefix: str
    model: type[MODEL_TYPE]
    serializer_class: BaseSerializer

    filter_class: BaseFilter | None = None
    create_serializer_class: BaseSerializer | None = None
    # Needs to be here as for update you don't need to specify all fields, which is not allowed in FastAPI,
    # due to pre endpoint body validation.
    update_serializer_class: BaseSerializer | None = None

    def get_serializer_class(
        self, _action: ViewSetAction | CustomActionName | None = None
    ):
        # Cannot do self.action in this scope as it is invoked also when the ViewSet is registered.
        if _action == ViewSetAction.LIST or _action == ViewSetAction.RETRIEVE:
            return self.serializer_class
        elif _action == ViewSetAction.CREATE:
            return self.create_serializer_class
        elif _action == ViewSetAction.UPDATE:
            return self.update_serializer_class
        else:
            raise NotImplementedError

    def get_queryset(self) -> Select[MODEL_TYPE]:
        return select(self.model)

    async def get_object(
        self, pk: int = None, *, for_update: bool = False
    ) -> MODEL_TYPE:
        pk = pk or self.pk
        return await get_object_or_404(
            self.get_queryset(), self.model.id == pk, for_update=for_update
        )

    @staticmethod
    async def create_from_serializer(
        serializer: BaseSerializer,
        model_class: type[E],
        add_and_commit: bool = False,
        fetch_related: bool = False,
        session: AsyncSession = None,
        **serializer_kwargs,
    ) -> E:
        if fetch_related:
            await serializer.fetch_related()
        kwargs = serializer.model_dump()
        kwargs.update(**serializer_kwargs)
        obj = model_class(**kwargs)

        if add_and_commit:
            session = session or get_request_db_session()
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
        return obj

    @staticmethod
    def serialize_from_object(entity: BaseEntity, serializer_class: type[S]) -> S:
        return serializer_class.model_validate(entity, from_attributes=True)

    @property
    def action(self) -> ViewSetAction | CustomActionName:
        return _request_action_context_var.get()

    @property
    def pk(self) -> int:
        return _request_pk_context_var.get()

    @classmethod
    def register(cls, router: APIRouter):
        cls._allow_create_instance = True
        obj = cls(router)
        cls._allow_create_instance = False
        obj._register()
        return obj

    _router: APIRouter
    _allow_create_instance: bool = False
    _custom_actions: list[Callable]

    def __init__(self, router: APIRouter):
        assert (
            self._allow_create_instance
        ), "Do not create an instance manually. Please use GenericViewSet.register(router)."
        self._router = router

    def _register(self):
        self._register_actions()

        for register_view_func in [
            "register_list",
            "register_retrieve",
            "register_create",
            "register_destroy",
            "register_update",
        ]:
            if hasattr(self, register_view_func):
                getattr(self, register_view_func)()

    def _register_actions(self):
        """Register all @action methods from a class."""

        for _, function in inspect.getmembers(self.__class__, inspect.isfunction):
            if not getattr(function, "is_action", False):
                continue

            url = function.url_path
            if function.is_detail:
                url = self._join_urls("/{pk}", url)

            url = self._join_urls(self.url_prefix, url)
            self._router.add_api_route(
                url, getattr(self, function.__name__), methods=[function.method]
            )

    @staticmethod
    def _join_urls(*parts: str) -> str:
        return "/" + "/".join(p.strip("/") for p in parts if p)


class ListMixin:
    """
    Provides a list endpoint implementation for a viewset.
    Handles filtering, ordering, and pagination of querysets.
    Returns serialized collections of model instances.
    """

    def register_list(self: GenericViewSet):
        _self = self
        assert self.get_serializer_class(
            ViewSetAction.LIST
        ), "Attribute 'serializer_class' or get_serializer_class() for action 'list' must be provided for ListMixin."

        async def _list(
            filters: _self.filter_class | None, pagination: PaginationParams
        ):
            token = _request_action_context_var.set(ViewSetAction.LIST)
            try:
                if filters:
                    query = filters.filter(_self.get_queryset())
                else:
                    query = _self.get_queryset()

                query = _self._paginate_queryset(query, pagination)

                result = await get_request_db_session().execute(query)
                return [
                    _self.get_serializer_class(ViewSetAction.LIST).model_validate(
                        obj, from_attributes=True
                    )
                    for obj in result.scalars()
                ]
            finally:
                _request_action_context_var.reset(token)

        if _self.filter_class:

            @_self._router.get(f"/{_self.url_prefix}")
            async def list_view(
                pagination: PaginationParams = Depends(PaginationParams),
                filters: _self.filter_class = FilterDepends(_self.filter_class),
            ):
                return await _list(filters, pagination)

        else:

            @_self._router.get(f"/{_self.url_prefix}")
            async def list_view(
                pagination: PaginationParams = Depends(PaginationParams),
            ):
                return await _list(None, pagination)

    def _paginate_queryset(self, query, pagination):
        if pagination.order_by:
            order_clauses = []
            for field in pagination.order_by.split(","):
                field = field.strip()

                if field.startswith("-"):
                    if field := getattr(self.model, field[1:], None):
                        order_clauses.append(desc(field))
                else:
                    if field := getattr(self.model, field, None):
                        order_clauses.append(asc(field))
            query = query.order_by(*order_clauses)

        if pagination.page is not None and pagination.page_size is not None:
            offset = pagination.page * pagination.page_size
            query = query.offset(offset).limit(pagination.page_size)
        return query


class RetrieveMixin:
    """
    Provides a retrieve endpoint implementation for a viewset.
    Fetches a single object by primary key and returns its serialized representation.
    """

    def register_retrieve(self: GenericViewSet):
        _self = self
        assert self.get_serializer_class(
            ViewSetAction.RETRIEVE
        ), "Attribute 'serializer_class' or get_serializer_class() for action 'retrieve' must be provided for RetrieveMixin."

        @_self._router.get(
            f"/{_self.url_prefix}/{{pk}}",
            response_model=_self.get_serializer_class(ViewSetAction.RETRIEVE),
        )
        async def retrieve_view(pk: int):
            token = _request_action_context_var.set(ViewSetAction.RETRIEVE)
            try:
                obj = await _self.get_object(pk)
                return _self.get_serializer_class(
                    ViewSetAction.RETRIEVE
                ).model_validate(obj, from_attributes=True)
            finally:
                _request_action_context_var.reset(token)


class CreateMixin:
    """
    Provides a create endpoint implementation for a viewset.
    Validates input data, constructs a model instance, and persists it to the database.
    """

    def register_create(self: GenericViewSet):
        _self = self
        assert self.get_serializer_class(
            ViewSetAction.CREATE
        ), "Attribute 'create_serializer_class' or get_serializer_class() for action 'create' must be provided for CreateMixin."

        @_self._router.post(
            f"/{_self.url_prefix}",
            response_model=_self.get_serializer_class(ViewSetAction.LIST),
        )
        async def create_view(
            payload: _self.get_serializer_class(ViewSetAction.CREATE),
        ):
            token = _request_action_context_var.set(ViewSetAction.CREATE)
            try:
                db_session = get_request_db_session()
                await payload.fetch_related()
                obj = _self.model(**payload.model_dump())
                await _self.perform_create(obj, db_session)
                return _self.get_serializer_class(ViewSetAction.LIST).model_validate(
                    obj, from_attributes=True
                )
            finally:
                _request_action_context_var.reset(token)

    @staticmethod
    async def perform_create(obj: MODEL_TYPE, db_session: AsyncSession) -> None:
        db_session.add(obj)
        await db_session.commit()
        await db_session.refresh(obj)


class UpdateMixin:
    """
    Provides a partial update (PATCH-style) endpoint implementation for a viewset.
    Supports dynamic update serializers with optional fields and applies changes to existing database objects.
    """

    def register_update(self: GenericViewSet):
        _self = self
        assert self.get_serializer_class(
            ViewSetAction.UPDATE
        ) or self.get_serializer_class(
            ViewSetAction.CREATE
        ), "Attribute 'create_serializer_class' or 'update_serializer_class' must be provided for UpdateMixin."

        @_self._router.patch(
            f"/{_self.url_prefix}/{{pk}}",
            response_model=_self.get_serializer_class(ViewSetAction.RETRIEVE),
        )
        async def update_view(pk: int, payload: _self._get_update_serializer_class()):
            token = _request_action_context_var.set(ViewSetAction.UPDATE)
            try:
                _self._validate_against_create_serializer(
                    payload.model_dump(exclude_unset=True),
                    _self.get_serializer_class(ViewSetAction.CREATE),
                )
                await payload.fetch_related()

                obj = await _self.get_object(pk)

                for field, value in payload.model_dump(exclude_unset=True).items():
                    setattr(obj, field, value)

                db_session = get_request_db_session()
                await _self.perform_update(obj, db_session)
                return _self.get_serializer_class(
                    ViewSetAction.RETRIEVE
                ).model_validate(obj, from_attributes=True)
            finally:
                _request_action_context_var.reset(token)

    @staticmethod
    async def perform_update(obj: MODEL_TYPE, db_session: AsyncSession) -> None:
        db_session.add(obj)
        await db_session.commit()
        await db_session.refresh(obj)

    @lru_cache(maxsize=None)
    def _get_update_serializer_class(self: GenericViewSet) -> type | BaseSerializer:
        """
        Creates update serializer class from create serializer class.
        """
        if self.get_serializer_class(ViewSetAction.UPDATE):
            return self.get_serializer_class(ViewSetAction.UPDATE)

        assert (
            self.get_serializer_class(ViewSetAction.CREATE) is not None
        ), "To use UpdateMixin 'create_serializer_class' must be provided."
        source = self.get_serializer_class(ViewSetAction.CREATE)
        annotations = get_type_hints(source, include_extras=True)

        fields = {}
        for name, typ in annotations.items():
            if name.startswith("_"):
                continue

            src_field = source.model_fields.get(name)
            if src_field is not None:
                # Preserve all constraints/metadata from the creation serializer field.
                update_field = deepcopy(src_field)
                update_field.default = None
                update_field.default_factory = None
                fields[name] = (typ | None, update_field)
            else:
                fields[name] = (typ | None, Field(default=None))

        return create_model(
            f"Update{source.__name__}",
            __base__=BaseSerializer,
            __config__=ConfigDict(
                arbitrary_types_allowed=True,
                extra="forbid",
                from_attributes=True,  # From BaseSerializer as it overrides config
                populate_by_name=True,  # From BaseSerializer as it overrides config
            ),
            **fields,
        )

    def _validate_against_create_serializer(
        self,
        data: Dict[str, Any],
        create_serializer_cls: type,
        loc_prefix=("query", "payload"),
    ):
        """
        Checks that required fields from create_serializer_cls exist and are not None.
        """

        annotations = get_type_hints(create_serializer_cls, include_extras=True)
        errors = []
        for field_name, field_type in annotations.items():
            if field_name not in data:
                continue

            if self._is_required_field(field_type) and data[field_name] is None:
                errors.append(
                    {
                        "type": "missing",
                        "loc": list(loc_prefix + (field_name,)),
                        "msg": "Field required",
                        "input": None,
                    }
                )
        if errors:
            raise ApiPydanticValidationException(details={"detail": errors})

    @staticmethod
    def _is_required_field(field_type: Any) -> bool:
        return type(None) not in get_args(field_type)


class DestroyMixin:
    """
    Provides a delete endpoint implementation for a viewset.
    Removes an existing database object identified by its primary key.
    """

    def register_destroy(self: GenericViewSet):
        _self = self

        @_self._router.delete(f"/{_self.url_prefix}/{{pk}}", response_model=None)
        async def delete_view(pk: int):
            token = _request_action_context_var.set(ViewSetAction.DELETE)
            try:
                obj = await _self.get_object(pk)

                db_session = get_request_db_session()
                try:
                    await _self.perform_destroy(obj, db_session)
                except IntegrityError as e:
                    if isinstance(e.orig, ForeignKeyViolation):
                        raise ForeignKeyViolationException(
                            details={"errors": e.orig.args}
                        )
                    raise e
                return None
            finally:
                _request_action_context_var.reset(token)

    @staticmethod
    async def perform_destroy(obj: MODEL_TYPE, db_session: AsyncSession) -> None:
        await db_session.delete(obj)
        await db_session.commit()


class ModelViewSet(
    ListMixin,
    RetrieveMixin,
    CreateMixin,
    UpdateMixin,
    DestroyMixin,
    GenericViewSet[MODEL_TYPE],
    Generic[MODEL_TYPE],
):
    """
    Full-featured CRUD viewset combining list, retrieve, create, update, and delete operations.
    Designed to mirror Django REST Framework ModelViewSet behavior using FastAPI and SQLAlchemy.
    """

    ...
