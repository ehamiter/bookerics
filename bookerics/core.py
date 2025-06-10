from typing import Any
from fasthtml.common import Head, Meta, Link, Script, Body, Div, Html, Title

def Page(*children: Any, title_str: str = "bookerics") -> Html:
    """
    Constructs a basic HTML page structure using FastHTML components.
    """
    return Html(
        Head(
            Title(title_str),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1, shrink-to-fit=no"),
            Meta(name="description", content="Bookmarks, but for Erics"),
            Meta(name="keywords", content="bookmarks, eric hamiter, web, python, fasthtml, software"),
            Meta(name="author", content="Eric Hamiter"),
            Link(rel="icon", href="/static/favicon.png", type="image/png"),
            Link(rel="stylesheet", href="/static/css/main.css"),
            Link(rel="stylesheet", href="/static/css/components.css"),
            Script(src="/static/js/htmx.min.js", defer=True),
            Script(src="/static/js/custom.js", defer=True),
            Meta(name="htmx-config", content='{"defaultSwapStyle": "outerHTML"}')
        ),
        Body(
            Div(*children, id="results-container", cls="container mx-auto p-2"),
            # Modal container - empty div that will be populated by HTMX
            Div(id="modal-container")
        )
    )
