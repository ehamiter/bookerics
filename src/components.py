from typing import override

from ludic.attrs import Attrs, GlobalAttrs
from ludic.base import NoChildren
from ludic.catalog.buttons import ButtonLink, ButtonPrimary
from ludic.catalog.forms import InputField
from ludic.catalog.headers import H4
from ludic.catalog.layouts import Box, Cluster, Grid, Stack, Switcher
from ludic.catalog.typography import Link, Paragraph
from ludic.html import b, div, style
from ludic.types import Component, NoChildren


class NavMenu(Component[NoChildren, GlobalAttrs]):
    @override
    def render(self) -> Cluster:
        bookmark_count = f"{int(self.attrs['bookmark_count']):,}"

        return Cluster(
            Cluster(
                Link("newest", to="/"),
                Link("oldest", to="/oldest"),
                Link("random", to="/random"),
                Link("untagged", to="/untagged"),
            ),
            Cluster(Link("tags", to="/tags"), Paragraph(bookmark_count)),
            classes=["justify-space-between"],
        )


class BookmarkListAttrs(Attrs):
    bookmarks: list


class BookmarkList(Component[NoChildren, GlobalAttrs]):
    def render_tags(self, tags):
        return Cluster(
            *[
                ButtonLink(tag, to=f"/tags/{tag}", classes=["info small"])
                for tag in tags
            ],
        )

    def render_bookmark(self, bookmark):
        return Box(
            H4(Link(bookmark["title"], to=bookmark["url"], target="_blank")),
            b(bookmark["url"]),
            Paragraph(bookmark["description"]) if bookmark.get("description") else "",
            Box(
                Cluster(
                    self.render_tags(bookmark["tags"])
                    if bookmark.get("tags")
                    else Cluster(ButtonPrimary("none", classes=["warning small"])),
                ),
                classes=["no-border no-inline-padding"],
            ),
        )

    @override
    def render(self) -> Switcher:
        return Switcher(
            Paragraph(*[self.render_bookmark(bm) for bm in self.attrs["bookmarks"]])
        )


class SearchBar(Component[NoChildren, GlobalAttrs]):
    classes = ["search-bar"]
    styles = style.use(
        lambda theme: {
            ".search-bar": {
                "width": "100%",
                "input": {
                    "background-color": theme.colors.light.lighten(1),
                    "border": f"1px solid {theme.colors.light.darken(5)}",
                    "color": theme.colors.dark,
                    "max-inline-size": "none",
                },
                "input::placeholder": {
                    "color": theme.colors.dark.lighten(7),
                },
                "input:focus": {
                    "border-color": theme.colors.dark.lighten(5),
                    "outline": "none",
                },
            },
        }
    )

    def __init__(self, query="", **kwargs):
        super().__init__(**kwargs)
        self.query = query

    @override
    def render(self) -> InputField:
        return InputField(
            type="search",
            placeholder="Search bookerics",
            hx_get="/search",
            hx_trigger="input changed delay:500ms",
            hx_target="#results-container",
            hx_swap="innerHTML",
            name="query",
            id="query",
            value=self.query,
            **self.attrs,
        )


class TagCloud(Component[NoChildren, GlobalAttrs]):
    @override
    def render(self) -> div:
        tags = self.attrs.get("tags", [])
        return Cluster(
            *[Link(tag, to=f"/tags/{tag}", class_="tag") for tag in tags],
            class_="tag-cloud",
        )
