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
            // Only respect a saved theme cookie when the user manually chose it.
            // Auto-detected themes (from system preference) do not set the manual flag,
            // so stale cookies from a previous system-light visit don't override system-dark.
            const cookies = document.cookie.split(';');
            let savedTheme = null;
            let isManual = false;
            for (let cookie of cookies) {
                const trimmed = cookie.trim();
                const eqIdx = trimmed.indexOf('=');
                if (eqIdx === -1) continue;
                const name = trimmed.slice(0, eqIdx);
                const value = trimmed.slice(eqIdx + 1);
                if (name === 'bookerics-theme') savedTheme = value;
                if (name === 'bookerics-theme-manual') isManual = (value === 'true');
            }
            if (savedTheme && isManual) {
                return savedTheme;
            }

            // No manual preference — always follow system
            const mql = window.matchMedia('(prefers-color-scheme: dark)');
            if (typeof mql.matches === 'boolean') {
                return mql.matches ? 'dark' : 'light';
            }

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
