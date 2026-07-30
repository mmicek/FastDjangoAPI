import pydantic
from fastapi import HTTPException
from starlette import status

from project_template.api.common.enums import ApiErrorCode


class ExceptionResponse(pydantic.BaseModel):
    message: str
    details: dict
    error_code: int


class ApiBaseException(HTTPException):
    """
    Base exception class for API errors that standardizes HTTP error responses.
    Encapsulates error code, message, and structured details into a consistent response format.
    Just raise the exception and proper exception handler will return prepared json response.
    """

    error_code: int
    default_message: str | None
    status_code = 400

    def __init__(
        self,
        message: str = None,
        details: dict = None,
        status_code: int = None,
        headers: dict[str, str] = None,
        **kwargs,
    ):
        super().__init__(
            status_code=status_code or self.status_code,
            detail=ExceptionResponse(
                message=message or self.default_message,
                details=self._get_details(details, **kwargs),
                error_code=self.error_code,
            ).model_dump(),
            headers=headers,
        )

    @staticmethod
    def _get_details(details: dict, **kwargs) -> dict:
        if not details:
            return kwargs
        return details | kwargs


class ApiAuthException(ApiBaseException):
    error_code = ApiErrorCode.BASE_AUTHORIZATION_FAILED
    default_message = "Authorization failed."
    status_code = status.HTTP_401_UNAUTHORIZED


class ApiPermissionException(ApiBaseException):
    error_code = ApiErrorCode.PERMISSION_DENIED
    default_message = "Permission denied."
    status_code = status.HTTP_403_FORBIDDEN


class InvalidTokenException(ApiBaseException):
    error_code = ApiErrorCode.INVALID_TOKEN_EXCEPTION
    default_message = "Invalid token."
    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidTokenFormatException(ApiBaseException):
    error_code = ApiErrorCode.INVALID_TOKEN_FORMAT_EXCEPTION
    default_message = "Invalid token format. Should be 'Bearer <token>'"
    status_code = status.HTTP_401_UNAUTHORIZED


class ApiException(ApiBaseException):
    error_code = ApiErrorCode.BASE_API_EXCEPTION
    default_message = "Something went wrong. Check details for more information."


class ApiPydanticValidationException(ApiBaseException):
    default_message = "Validation exception."
    error_code = ApiErrorCode.PYDANTIC_VALIDATION_EXCEPTION
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


class ApiPydanticBadRequestException(ApiBaseException):
    default_message = "Bad request validation exception."
    error_code = ApiErrorCode.PYDANTIC_BAD_REQUEST_EXCEPTION
    status_code = status.HTTP_400_BAD_REQUEST


class IdValueMustBeIntegerException(ApiBaseException):
    error_code = ApiErrorCode.NUMERIC_ID_EXCEPTION
    default_message = "Id value must be an integer."


class ApiInternalServerException(ApiBaseException):
    error_code = ApiErrorCode.INTERNAL_SERVER_ERROR
    default_message = "Internal server error."
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ObjectDoesNotExistException(ApiBaseException):
    error_code = ApiErrorCode.OBJECT_DOES_NOT_EXIST_EXCEPTION
    default_message = "Object does not exist."
    status_code = status.HTTP_404_NOT_FOUND


class ForeignKeyViolationException(ApiBaseException):
    error_code = ApiErrorCode.FOREIGN_KEY_VIOLATION_EXCEPTION
    default_message = "Update or delete on table violates foreign key constraint. Please delete related objects and try again."
