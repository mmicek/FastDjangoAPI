from enum import Enum, EnumType
from functools import lru_cache
from typing import Annotated, Any, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.fields import FieldInfo
from sqlalchemy import select

from project_template.api.common.database.models import BaseEntity, get_object_or_404
from project_template.api.common.fields import PrimaryKeyRelation


class BaseSerializer(BaseModel):
    """
    Base class for all model serializers. Supports PrimaryKeyRelation, ConvertableField
    and auto decimal round to 2 places.
    """

    model_config = ConfigDict(
        # to be able to serialize SqlAlchemy models directly
        from_attributes=True,
        # FastApi render pydantic models by aliases.
        # With populate_by_name set to true,
        # we are able to render SqlAlchemy instances using different attrs names than original ones.
        populate_by_name=True,
    )

    async def fetch_related(self):
        """
        Resolve all ``PrimaryKeyRelation`` fields.


        For each configured field, the referenced object is loaded
        and assigned to its destination attribute.
        """

        for field_name, relation in self._get_primary_related_fields():
            pk = getattr(self, field_name)
            if pk is None:
                continue

            model = relation.model
            lookup_field = relation.lookup_field
            obj = await get_object_or_404(
                select(model), getattr(model, lookup_field) == pk
            )
            source = relation.source
            if source is not None:
                object.__setattr__(self, source, obj)

    @classmethod
    def get_possible_values_for_enumerated_types(cls) -> dict[str, list[Any]]:
        """
        Return a dict mapping enumerated types to a list of possible values.
        """
        enum_fields = {}

        for field_name, field_info in cls.model_fields.items():
            type_annotation = None
            annotations = get_args(field_info.annotation)
            for annotation in annotations:
                if issubclass(annotation, Enum):
                    type_annotation = annotation
                    break

            if type_annotation:
                enum_fields[field_name] = type_annotation
            else:
                if field_info.annotation and type(field_info.annotation) is EnumType:
                    enum_fields[field_name] = field_info.annotation

        return enum_fields

    @classmethod
    def list_model_validate(cls, models: list[BaseModel]):
        return [cls.model_validate(model) for model in models]

    @model_validator(mode="before")
    @classmethod
    def _before_model_validation(cls, data: dict | BaseEntity):
        for field_name, conversion_mapping in cls._get_convertable_fields().items():
            try:
                if isinstance(data, dict):
                    data[field_name] = conversion_mapping[data[field_name]]
                else:
                    setattr(
                        data, field_name, conversion_mapping[getattr(data, field_name)]
                    )
            except KeyError:
                ...

        for field_name, sources in cls._get_multiple_source_fields().items():
            for source in sources:
                if cls._replace_field(data, field_name, source):
                    break
        return data

    @classmethod
    @lru_cache(maxsize=None)
    def _get_convertable_fields(cls) -> dict[str, dict]:
        result = {}
        for field_name, field_value in cls.model_fields.items():
            if field_info := cls.model_fields.get(field_name):
                if field_info.json_schema_extra:
                    if conversion_mapping := field_info.json_schema_extra.get(
                        "conversion_mapping"
                    ):
                        result[field_name] = conversion_mapping
        return result

    @classmethod
    @lru_cache(maxsize=None)
    def _get_multiple_source_fields(cls) -> dict[str, list[str]]:
        result = {}
        for field_name, field_value in cls.model_fields.items():
            if field_info := cls.model_fields.get(field_name):
                if field_info.json_schema_extra:
                    if sources := field_info.json_schema_extra.get("sources"):
                        result[field_name] = sources
        return result

    @classmethod
    @lru_cache(maxsize=None)
    def _get_primary_related_fields(cls) -> list[tuple[str, PrimaryKeyRelation]]:
        fields = []
        for field_name, field_info in cls.model_fields.items():
            relation: PrimaryKeyRelation | None = cls._extract_from_type(field_info)
            if relation is not None:
                fields.append((field_name, relation))
        return fields

    @classmethod
    def _extract_from_type(cls, field: Any):
        # Case 1: None | Annotated[int, PrimaryKeyRelation(...)]  -> This one will be generated by update_serializer from create_serializer
        if result := cls._handle_recursive_extract_from_type(field):
            return result

        annotated = None
        # Case 2: Annotated[int, PrimaryKeyRelation(...)] -> FieldInfo
        if isinstance(field, FieldInfo) and get_origin(field.annotation) is Annotated:
            annotated = field.annotation

        # Case 3: Annotated[int, PrimaryKeyRelation(...)] -> AnnotatedAlias
        if get_origin(field) is Annotated:
            annotated = field

        if annotated:
            return next(
                (m for m in get_args(annotated) if isinstance(m, PrimaryKeyRelation)),
                None,
            )

        # Case 4: FieldInfo(annotation=int, metadata=[PrimareyKeyRelation])
        if isinstance(field, FieldInfo) and any(
            (isinstance(o, PrimaryKeyRelation) for o in field.metadata)
        ):
            for o in field.metadata:
                if isinstance(o, PrimaryKeyRelation):
                    return o

        return None

    @classmethod
    def _handle_recursive_extract_from_type(cls, field: Any):
        if isinstance(field, FieldInfo) and isinstance(
            field.annotation, Union
        ):  # noqa Pycharm WTF (bug)
            for arg in get_args(field.annotation):
                result = cls._extract_from_type(arg)
                if result is not None:
                    return result

    @classmethod
    def _replace_field(cls, data: Any, field_name: str, source: str):
        """
        The order of the fields matter, so the first one is the most important.
        """
        if isinstance(data, dict):
            if source in data:
                data[field_name] = data[source]
                return True
        elif isinstance(data, BaseEntity):
            if hasattr(data, source):
                attr = getattr(data, source)
                if attr is not None:
                    setattr(data, field_name, attr)
                    return True
        else:
            raise NotImplementedError


class BaseModelSerializer(BaseSerializer):
    class Meta:
        model: type[BaseEntity]

    def __init_subclass__(cls, **kwargs):
        meta: BaseModelSerializer.Meta | None = getattr(cls, "Meta", None)
        assert (
            meta and meta.model
        ), "To use ModelSerializer please implement Meta.model."
        super().__init_subclass__(**kwargs)

    async def add_and_commit(
        self, commit: bool = True, ignore_fields: list[str] = None
    ):
        entity = self.get_entity(ignore_fields=ignore_fields)
        await entity.add_and_commit(commit=commit)
        return entity

    def get_entity(self, ignore_fields: list[str] = None) -> BaseEntity:
        ignore_fields = ignore_fields or []
        data = self.model_dump()
        for field in ignore_fields:
            del data[
                field
            ]  # Don't throw exception there. We do not want to override the exception.
        return self.Meta.model(**data)  # noqa model is not None


class SuccessResponse(BaseSerializer):
    success: bool = True
