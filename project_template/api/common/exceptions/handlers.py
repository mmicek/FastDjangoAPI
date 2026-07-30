import logging

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED

from project_template.api.common.exceptions.exceptions import (
    ApiAuthException,
    ApiBaseException,
    ApiException,
    ApiInternalServerException,
    ApiPydanticValidationException,
)

logger = logging.getLogger(__name__)
error_logger = logging.getLogger("errors")


def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    exc = ApiPydanticValidationException(details={"errors": exc.errors()})
    return JSONResponse(
        jsonable_encoder(exc.detail),
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Received unhandled exception: {exc}", exc_info=True)
    error_logger.error(f"Received unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder(ApiInternalServerException(error=str(exc)).detail),
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    headers = getattr(exc, "headers", None)
    if not isinstance(exc, ApiBaseException):
        exec_class = ApiException
        if exc.status_code == HTTP_401_UNAUTHORIZED:
            exec_class = ApiAuthException
        exc = exec_class(
            message=exc.detail if isinstance(exc.detail, str) else None,
            details=exc.detail if isinstance(exc.detail, dict) else None,
            status_code=exc.status_code,
            headers=headers,
        )
    return JSONResponse(
        jsonable_encoder(exc.detail), status_code=exc.status_code, headers=headers
    )
