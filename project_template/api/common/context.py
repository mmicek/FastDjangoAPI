import typing
from contextvars import ContextVar
from typing import Any

from project_template.api.common.enums import ViewSetAction

if typing.TYPE_CHECKING:
    from project_template.api.common.views import CustomActionName


_request_action_context_var: ContextVar[ViewSetAction | CustomActionName] = ContextVar(
    "request_action_context_var"
)
_request_pk_context_var: ContextVar[int] = ContextVar("request_pk_context_var")


class ContextSetContextManager:
    """
    Context manager that allows to set a context variable for each request.
    """

    def __init__(self, context_var: ContextVar, context: Any):
        self.context_var = context_var
        self.context = context
        self.token = None

    def __enter__(self):
        self.token = self.context_var.set(self.context)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context_var.reset(self.token)
