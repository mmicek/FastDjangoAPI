import functools
from typing import Protocol

from project_template.api.common.context import (
    ContextSetContextManager,
    _request_action_context_var,
    _request_pk_context_var,
)
from project_template.api.common.database.session import get_request_session
from project_template.api.common.exceptions.exceptions import (
    IdValueMustBeIntegerException,
)


class RestMethod:
    GET = "get"
    POST = "post"
    DELETE = "delete"

    @classmethod
    def get_methods(cls) -> list[str]:
        return [cls.GET, cls.POST, cls.DELETE]


class ActionProtocol(Protocol):
    is_action: bool
    is_detail: bool
    method: str
    url_path: str


def action(url_path: str, method: RestMethod | str, detail: bool = False):
    """Mark a method as an action endpoint."""

    assert (
        method in RestMethod.get_methods()
    ), f"Invalid method name. Possible methods: {RestMethod.get_methods()}"

    def decorator(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = get_request_session()
            pk = request.path_params.get("pk")
            with ContextSetContextManager(_request_action_context_var, func.__name__):
                if pk is not None:
                    try:
                        pk = int(
                            pk
                        )  # REMOVE THIS CHECK IF YOU WANT PK TO BE ANY TYPE LIKE: str or uuid
                    except Exception:
                        raise IdValueMustBeIntegerException()
                    with ContextSetContextManager(_request_pk_context_var, pk):
                        result = await func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
            return result

        wrapper.is_action = True
        wrapper.is_detail = detail
        wrapper.method = method
        wrapper.url_path = url_path
        return wrapper

    return decorator
