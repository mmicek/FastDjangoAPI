from enum import IntEnum, StrEnum

from sqlalchemy import Enum as SAEnum


class StringEnum(StrEnum):
    """
    Allows to put two values: database_value, human_readable_value like:


    PROGRAMMATIC_VALUE = "database_value", "human_readable_value"
    """

    def __new__(cls, db_value, description):
        obj = str.__new__(cls, db_value)
        obj._value_ = db_value
        obj.description = description
        return obj

    def __str__(self):
        return self.value

    @classmethod
    def _missing_(cls, value):
        """
        Due to the fact, that Excel file is assuming the type of the column by values so,
         it might put integer type if enum values are strings that looks like numeric value: "45"
        """
        if isinstance(value, int) or isinstance(value, float):
            return cls(str(value))
        return None


def StringEnumType(enum_cls, **kwargs):  # noqa
    """
    Uses member value not member name for StringEnum enums for sqlalchemy enum.


    If you define:
      PP = "pp", "parent pipe"
    and generate alembic migration from this, you will get "PP" as an enum. You need to use this class to get "pp".
    """
    return SAEnum(
        enum_cls, values_callable=lambda e: [str(item) for item in e], **kwargs
    )


class ViewSetAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    RETRIEVE = "retrieve"


class ApiErrorCode(IntEnum):
    # 1xxxxx Authorization
    BASE_AUTHORIZATION_FAILED = 100000
    INVALID_TOKEN_FORMAT_EXCEPTION = 100001
    INVALID_TOKEN_EXCEPTION = 100002
    PERMISSION_DENIED = 100003

    # 4xxxxx Bad request
    BASE_API_EXCEPTION = 400000
    PYDANTIC_VALIDATION_EXCEPTION = 400001
    PYDANTIC_BAD_REQUEST_EXCEPTION = 400002
    NUMERIC_ID_EXCEPTION = 400003
    OBJECT_DOES_NOT_EXIST_EXCEPTION = 400004
    FOREIGN_KEY_VIOLATION_EXCEPTION = 400005

    # 9xxxxx Internal
    INTERNAL_SERVER_ERROR = 999990
