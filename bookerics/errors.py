from fasthtml.common import H1, P, HTMLResponse
from starlette.requests import Request

from .main import app
from .core import Page


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> HTMLResponse:
    page_content = Page(
        H1("Page Not Found"),
        P("The page you are looking for was not found."),
        title_str="404 - Page Not Found"
    )
    return HTMLResponse(str(page_content), status_code=404)


@app.exception_handler(500)
async def server_error(request: Request, exc: Exception) -> HTMLResponse:
    page_content = Page(
        H1("Server Error"),
        P("Server encountered an error during processing."),
        title_str="500 - Server Error"
    )
    return HTMLResponse(str(page_content), status_code=500)
