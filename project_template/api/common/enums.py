from enum import IntEnum, StrEnum

from pydantic_core import core_schema


class _Unset:
    @staticmethod
    def __get_pydantic_core_schema__(source_type, handler):
        return core_schema.any_schema()


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

    # APPS EXCEPTIONS
    """
    6xxxxx - Dataset exceptions
    601xxx - General dataset exceptions
 
    7xxxxx - Other exceptions
    """
    PIPE_ALREADY_HAS_LINER_EXCEPTION = 601001

    DATA_IMPORT_VALIDATION_EXCEPTION = 701000
    NOT_UNIQUE_PRIMARY_KEY_EXCEPTION = 701001
    FK_RELATION_DOES_NOT_EXIST_EXCEPTION = 701002
    DATASET_CREATE_RECORD_VALIDATION_EXCEPTION = 701003
    DATASET_FRONT_SHEET_VALIDATION_EXCEPTION = 701004
    PIPE_DOES_NOT_EXIST_EXCEPTION = 701005
