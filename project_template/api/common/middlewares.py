from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class TrailingSlashRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware that normalizes incoming request URLs by removing trailing slashes.
    Redirects requests with trailing slashes to their non-slash equivalent while preserving query parameters.
    Ensures consistent URL formatting across the API and resolves problems with static files,
    if app.mount and StaticFiles are configured.
    """

    async def dispatch(self, request: Request, call_next):
        url_path = request.url.path
        if url_path != "/" and url_path.endswith("/"):
            new_path = url_path.rstrip("/")
            query_string = request.url.query
            if query_string:
                new_url = f"{new_path}?{query_string}"
            else:
                new_url = new_path
            return RedirectResponse(url=new_url)
        return await call_next(request)
