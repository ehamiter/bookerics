from typing import Any
from fasthtml.common import Head, Meta, Link, Script, Body, Div, Html, Title, FT


def Page(*children: Any, title_str: str = "bookerics", theme: str = "light") -> FT:
    """
    Constructs a basic HTML page structure using FastHTML components.
    """
    # Blocking script to prevent theme flash - runs before any content is painted
    # Based on Josh Comeau's technique: https://www.joshwcomeau.com/react/dark-mode/
    theme_prevention_script = """
    (function() {
        function getInitialColorMode() {
            // Check if user has explicitly chosen a theme via cookie
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'bookerics-theme') {
                    return value;
                }
            }
            
            // Check user's system preference
            const mql = window.matchMedia('(prefers-color-scheme: dark)');
            const hasMediaQueryPreference = typeof mql.matches === 'boolean';
            if (hasMediaQueryPreference) {
                return mql.matches ? 'dark' : 'light';
            }
            
            // Default to light theme
            return 'light';
        }
        
        const colorMode = getInitialColorMode();
        
        // Set the data-theme attribute immediately
        document.documentElement.setAttribute('data-theme', colorMode);
        
        // Also set a flag so our JS knows the theme was already set
        window.__THEME_SET__ = true;
        window.__INITIAL_COLOR_MODE__ = colorMode;
    })();
    """

    return Html(
        Head(
            Title(title_str),
            Meta(charset="utf-8"),
            Meta(
                name="viewport",
                content="width=device-width, initial-scale=1, shrink-to-fit=no",
            ),
            Meta(name="description", content="Bookmarks, but for Erics"),
            Meta(
                name="keywords",
                content="bookmarks, eric hamiter, web, python, fasthtml, software",
            ),
            Meta(name="author", content="Eric Hamiter"),
            Link(rel="icon", href="/static/favicon.png", type="image/png"),
            Script(
                theme_prevention_script
            ),  # Critical: runs before CSS to prevent flash
            Link(rel="stylesheet", href="/static/css/main.css"),
            Link(rel="stylesheet", href="/static/css/components.css"),
            Script(src="/static/js/htmx.min.js", defer=True),
            Script(src="/static/js/custom.js", defer=True),
            Meta(name="htmx-config", content='{"defaultSwapStyle": "outerHTML"}'),
        ),
        Body(
            Div(*children, id="results-container", cls="container mx-auto p-2"),
            # Modal container - empty div that will be populated by HTMX
            Div(id="modal-container"),
        ),
    )
