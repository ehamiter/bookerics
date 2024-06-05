from typing import override

from ludic.attrs import Attrs, GlobalAttrs
from ludic.base import NoChildren
from ludic.catalog.buttons import ButtonPrimary
from ludic.catalog.forms import InputField
from ludic.catalog.headers import H4
from ludic.catalog.layouts import Box, Cluster, Stack, Switcher
from ludic.catalog.typography import Link, Paragraph
from ludic.html import b, style
from ludic.types import Component, NoChildren


class NavMenu(Component[NoChildren, GlobalAttrs]):
    @override
    def render(self) -> Cluster:
        return Cluster(
            Link("newest", to="/"),
            Link("oldest", to="/oldest"),
            Link("random", to="/random"),
            Link("untagged", to="/untagged"),
        )


class BookmarkListAttrs(Attrs):
    bookmarks: list


class BookmarkList(Component[NoChildren, GlobalAttrs]):
    def render_tags(self, tags):
        return Cluster(
            *[ButtonPrimary(tag, classes=["info small"]) for tag in tags],
        )

    def render_bookmark(self, bookmark):
        return Box(
            H4(Link(bookmark["title"], to=bookmark["url"], target="_blank")),
            b(bookmark["url"]),
            Paragraph(bookmark["description"]) if bookmark.get("description") else "",
            Stack(
                self.render_tags(bookmark["tags"])
                if bookmark.get("tags")
                else Cluster(ButtonPrimary("none", classes=["warning small"]))
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
                "input": {
                    "background-color": theme.colors.light.lighten(1),
                    "border": f"1px solid {theme.colors.light.darken(5)}",
                    "color": theme.colors.dark,
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

    @override
    def render(self) -> InputField:
        return InputField(
            type="search",
            placeholder="Search bookerics",
            hx_get="/search",
            hx_trigger="input changed delay:500ms",
            hx_target="#search-results",
            hx_swap="innerHTML",
            name="query",
            **self.attrs,
        )
