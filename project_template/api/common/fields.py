from pydantic import Field

from project_template.api.common.database.models import BaseEntity


def ConvertableField(*args, conversion_mapping: dict = None, **kwargs):  # noqa
    """
    Custom Pydantic Field wrapper that attaches value conversion metadata.


    Stores a conversion mapping inside JSON schema metadata so that external
    processing layers can transform input values before or after validation.


    Intended for use in serializer fields that require pre-processing rules
    such as normalization or type coercion beyond standard Pydantic behavior.


    Example:
    rotate_90_degree: bool | None = ConvertableField(
        ...,
        conversion_mapping={None: False}
    )


    In the example above, a conversion layer may interpret ``None`` as
    ``False`` before the value is processed further.
    """

    json_schema_extra = kwargs.pop("json_schema_extra", {})
    json_schema_extra["conversion_mapping"] = (
        conversion_mapping if conversion_mapping is not None else {}
    )

    return Field(
        *args,
        json_schema_extra=json_schema_extra,
        **kwargs,
    )


def MultipleSourceField(*args, sources: list[str] = None, **kwargs):  # noqa
    """
    Custom Pydantic Field wrapper that allows to insert attribute from different properties.
    """
    json_schema_extra = kwargs.pop("json_schema_extra", {})
    json_schema_extra["sources"] = sources if sources is not None else {}

    return Field(
        *args,
        json_schema_extra=json_schema_extra,
        **kwargs,
    )


class PrimaryKeyRelation:
    """
    Custom Pydantic annotated relation representing a foreign-key relationship resolved via a primary key.


    This relation extends a standard integer input with additional metadata describing how the
    referenced object should be resolved from a database or repository layer. It separates
    relationship resolution from validation logic, enabling explicit loading of related
    entities outside the core validation step.


    It is intended for serializer patterns where relationship hydration is performed as a
    separate step (e.g. `fetch_related()`), rather than during model validation.


    Example:
        class BookCreate(RelatedBaseModel):
            author_id:  Annotated[int, PrimaryKeyRelation(model=Project, source="author")]


        book = BookCreate(author_id=1)
        await book.fetch_related()  # Must be called explicitly; handled automatically in GenericViewSet
        book.author  # -> User instance resolved from foreign key


    Attribute name 'source' is where the resolved object will be assigned. If not provided,
    the field will only validate existence of the related object without attaching
    it to the serializer instance.


    """

    def __init__(
        self, model: type[BaseEntity], lookup_field: str = "id", source: str = None
    ):
        self.model = model
        self.lookup_field = lookup_field
        self.source = source
