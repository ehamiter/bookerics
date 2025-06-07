from fasthtml.common import Head, Meta, Link, Script, Body, Div, Html, Title

def Page(*children, title_str: str = "bookerics"):
    """
    Constructs a basic HTML page structure using FastHTML components.
    """
    return Html(
        Head(
            Title(title_str),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1, shrink-to-fit=no"),
            Meta(name="description", content="Bookmarks, but for Erics."),
            Meta(name="keywords", content="bookmarks, eric hamiter, web, python, fasthtml, software"),
            Meta(name="author", content="Eric Hamiter"),
            Link(rel="icon", href="/static/favicon.png", type="image/png"),
            Link(rel="stylesheet", href="/static/css/main.css"),
            Link(rel="stylesheet", href="/static/css/components.css"), # Added link for component styles
            # Assuming PicoCSS or similar will be added for utility classes like .container, .mx-auto, .p-2
            # Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@latest/css/pico.min.css"),
            Script(src="/static/js/htmx.min.js", defer=True),
            Script(src="/static/js/custom.js", defer=True),
            Meta(name="htmx-config", content='{"defaultSwapStyle": "outerHTML"}')
        ),
        Body(
            Div(*children, id="results-container", cls="container mx-auto p-2"),
            # Modal container - empty div that will be populated by HTMX
            Div(id="modal-container")
            # The class "container mx-auto p-2" assumes a CSS framework like PicoCSS or Tailwind/Bootstrap.
            # For PicoCSS, just "container" might be enough for centering.
            # Padding "p-2" is a utility class example.
        )
    )

# Example of how Title() would be used if not using Titled()
# def PageSimple(*children, title_str: str = "bookerics"):
#     return Html(
#         Head(
#             Title(title_str), # Title needs to be directly in Head usually
#             Meta(charset="utf-8"),
#             Meta(name="viewport", content="width=device-width, initial-scale=1, shrink-to-fit=no"),
#             Link(rel="stylesheet", href="/static/css/main.css"),
#             Script(src="/static/js/htmx.min.js", defer=True),
#         ),
#         Body(
#             Div(*children, id="results-container")
#         )
#     )
