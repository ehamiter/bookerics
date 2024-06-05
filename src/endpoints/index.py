from dataclasses import dataclass, field
from typing import Optional, List

from ludic.catalog.buttons import ButtonPrimary
from ludic.catalog.headers import H1, H2, H3, H4, Anchor
from ludic.catalog.layouts import Box, Cluster, Stack, Switcher, Grid
from ludic.catalog.pages import HtmlPage, Head, Body
from ludic.catalog.typography import Paragraph, Link, Code
from ludic.html import div
from ludic.styles.themes import Fonts, Size, LightTheme, DarkTheme, set_default_theme, Colors, Theme
from ludic.styles.types import Color
from ludic.types import Attrs

from src.database import fetch_bookmarks, fetch_random_bookmark, fetch_untagged_bookmarks
from src.main import app
from src.pages import Page, SearchBar



def render_tags(tags):
    return Cluster(
        *[ButtonPrimary(tag, classes=["info small"]) for tag in tags],
    )

def render_bookmark(bookmark):
    return Box(
        H4(bookmark['title']),
        Link(bookmark['url'], to=bookmark['url'], target="_blank"),
        Paragraph(bookmark['description']) if bookmark.get('description') else "",
        Stack(render_tags(bookmark['tags']) if bookmark.get('tags') else Cluster(ButtonPrimary("none", classes=["warning small"])))
    )

@app.get("/")
async def index():
    bookmarks = fetch_bookmarks()
    return Page(
        Cluster(
            Link("bookerics", to="/"),
            Link("random", to="/random"),
            Link("untagged", to="/untagged")
        ),
        SearchBar(),
        Switcher(
            Paragraph(*[render_bookmark(bm) for bm in bookmarks])
        )
    )

@app.get("/random")
async def random_bookmark():
    bookmark = fetch_random_bookmark()
    return Page(
        Cluster(
            Link("bookerics", to="/"),
            Link("random", to="/random"),
            Link("untagged", to="/untagged")
        ),
        SearchBar(),
        Switcher(
            Paragraph(render_bookmark(bookmark))
        )
    )

@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_untagged_bookmarks()
    return Page(
        Cluster(
            Link("bookerics", to="/"),
            Link("random", to="/random"),
            Link("untagged", to="/untagged")
        ),
        SearchBar(),
        Switcher(
         Paragraph(*[render_bookmark(bm) for bm in bookmarks])
        )
    )
