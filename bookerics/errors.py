from fasthtml.common import H1, P

from .main import app
from .core import Page


@app.exception_handler(404)
async def not_found() -> Page:
    return Page(
        H1("Page Not Found"),
        P("The page you are looking for was not found."),
        title_str="404 - Page Not Found"
    )


@app.exception_handler(500)
async def server_error() -> Page:
    return Page(
        H1("Server Error"),
        P("Server encountered an error during processing."),
        title_str="500 - Server Error"
    )
