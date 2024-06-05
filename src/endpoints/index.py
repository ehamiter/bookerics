from typing import Optional, List
from src.database import fetch_bookmarks, fetch_random_bookmark, fetch_untagged_bookmarks
from src.main import app

from ludic.catalog.buttons import ButtonPrimary
from ludic.catalog.headers import H1, H2, H3, Anchor
from ludic.catalog.pages import HtmlPage, Head, Body
from ludic.catalog.typography import Paragraph, Link
from ludic.catalog.layouts import Box, Cluster
from ludic.types import Attrs


class BookmarkAttrs(Attrs):
    title: str
    url: str
    description: Optional[str]
    tags: Optional[List[str]]
    created_at: str
    updated_at: str

def render_tags(tags):
    return Box(
        Cluster(*[ButtonPrimary(tag, classes=["small"]) for tag in tags]),
        classes=["justify-space-between"],
    )

def render_bookmark(bookmark):
    return Box(
        H3(Link(bookmark['title'], to=bookmark['url'], target="_blank")),
        Paragraph(bookmark['description']) if bookmark.get('description') else "",
        render_tags(bookmark['tags']) if bookmark.get('tags') else Box(Paragraph("None")),
        class_="card"
    )

@app.get("/")
async def index():
    bookmarks = fetch_bookmarks()
    return HtmlPage(
        Head(
            title="bookerics",
            load_styles=True
        ),
        Body(
            Cluster(
                Link("bookerics", to="/"),
                Link("random", to="/random"),
                Link("untagged", to="/untagged")
            ),
            Box(*[render_bookmark(bm) for bm in bookmarks])
        )
    )

@app.get("/random")
async def random_bookmark():
    bookmark = fetch_random_bookmark()
    return HtmlPage(
        Head(
            title="Random Bookmark",
            load_styles=True
        ),
        Body(
            Cluster(
                Link("bookerics", to="/"),
                Link("random", to="/random"),
                Link("untagged", to="/untagged")
            ),
            Box(render_bookmark(bookmark))
        )
    )

@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_untagged_bookmarks()
    return HtmlPage(
        Head(
            title="Untagged Bookmarks",
            load_styles=True
        ),
        Body(
            Cluster(
                Link("bookerics", to="/"),
                Link("random", to="/random"),
                Link("untagged", to="/untagged")
            ),
            Box(*[render_bookmark(bm) for bm in bookmarks])
        )
    )

if __name__ == "__main__":
    app.run()
