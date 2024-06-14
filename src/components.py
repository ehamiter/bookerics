from textwrap import dedent
from typing import override

from ludic.attrs import Attrs, GlobalAttrs
from ludic.base import NoChildren
from ludic.catalog.buttons import ButtonLink, ButtonPrimary
from ludic.catalog.forms import InputField
from ludic.catalog.headers import H1, H2, H3, H4, WithAnchor, WithAnchorAttrs
from ludic.catalog.layouts import (Box, Center, Cluster, Cover, Grid, Stack,
                                   Switcher)
from ludic.catalog.messages import (MessageDanger, MessageInfo, MessageSuccess,
                                    MessageWarning)
from ludic.catalog.typography import (Code, CodeBlock, Link, LinkAttrs,
                                      Paragraph)
from ludic.html import a, b, div, h6, i, img, small, style
from ludic.types import Component, ComponentStrict, NoChildren

from src.database import BOOKMARK_NAME


class NavMenu(Component[NoChildren, GlobalAttrs]):
    @override
    def render(self) -> Cluster:
        if self.attrs.get("bookmark_count", False):
            bookmark_count = int(self.attrs["bookmark_count"])
            bookericz = BOOKMARK_NAME if bookmark_count == 1 else f"{BOOKMARK_NAME}s"
            bookmark_result = f"{bookmark_count:,} {bookericz}"
            link_display = HiddenLink(
                bookmark_result, to="/update", title="Backup on S3 now"
            )
        else:
            link_display = f"{BOOKMARK_NAME}s"

        return Cluster(
            link_display,
            Cluster(
                Link("newest", to="/"),
                Link("oldest", to="/oldest"),
                Link("random", to="/random"),
                Link("untagged", to="/untagged"),
            ),
            Cluster(a("tags", href="#", id="tags-link")),
            classes=["justify-space-between"],
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
            placeholder=f"Search {BOOKMARK_NAME}s",
            hx_get="/search",
            hx_trigger="input changed delay:500ms",
            hx_target="#results-container",
            hx_swap="innerHTML",
            name="query",
            id="query",
            value=self.query,
            **self.attrs,
        )


class HiddenLink(Component[str, LinkAttrs]):
    @override
    def render(self) -> a:
        return a(
            *self.children,
            href=self.attrs["to"],
            title=self.attrs["title"],
            classes=["hidden-link"],
            style={
                "color": "inherit",
                "text-decoration": "none",
                "cursor": "alias",
                "outline": "none",
            },
        )


class BookericLink(Component[str, LinkAttrs]):
    @override
    def render(self) -> a:
        return a(
            *self.children,
            href=self.attrs["to"],
            classes=["bookeric-link external"],
            style={
                "font-weight": "normal",
                "font-size": "1rem",
                "color": "#0086e5",
                "text-decoration": "none",
                "outline": "none",
            },
        )


class ImagePlaceholder(img):
    void_element = True
    html_name = "img"
    classes = ["image-placeholder"]
    styles = style.use(
        lambda theme: {
            ".image-placeholder": {
                "margin-top": "1em",
                "border": "1px groove #a3d3f641",
                "border-radius": "4px",
                "box-shadow": "0 1px 2px rgba(0, 0, 0, 0.1)",
                "background": "#85acc934",
            }
        }
    )


class TableStructure(Component[NoChildren, GlobalAttrs]):
    @override
    def render(self) -> Center:
        structure = self.attrs.get("structure", [])
        return Center(
            CodeBlock(
                f"""
[
 {',\n '.join([str(col) for col in structure])}
]
"""
            ),
        )


class TagCloud(Component[NoChildren, GlobalAttrs]):
    @override
    def render(self) -> Cluster:
        tags = self.attrs.get("tags", [])
        return Cluster(
            *[ButtonLink(tag, to=f"/tags/{tag}", classes="info small") for tag in tags]
        )


class Switcher(div):
    classes = ["switcher"]
    styles = style.use(
        lambda theme: {
            ".switcher": {
                "display": "flex",
                "flex-wrap": "wrap",
                "gap": theme.sizes.xl,
            },
            ".no-gap": {
                "gap": "0",
            },
            ".switcher > *": {
                "flex-grow": 1,
                "flex-basis": (
                    f"calc(({theme.layouts.switcher.threshold} - 100%) * 999)"
                ),
            },
            (
                f".switcher > :nth-last-child(n+{theme.layouts.switcher.limit+1})",
                f".switcher > :nth-last-child(n+{theme.layouts.switcher.limit+1}) ~ *",
            ): {
                "flex-basis": "100%",
            },
        }
    )


class BookmarkBox(div):
    classes = ["bookmark-box"]
    styles = style.use(
        lambda theme: {
            ".bookmark-box": {
                "padding": theme.sizes.m,
                "color": theme.colors.dark,
                "transition": "background-color 0.3s ease, box-shadow 0.3s ease",
            },
            ".bookmark-box.small": {
                "padding": theme.sizes.xs,
            },
            ".bookmark-box.large": {
                "padding": theme.sizes.xl,
            },
            ".bookmark-box:not(.transparent)": {
                "border": (
                    f"{theme.borders.thin} solid {theme.colors.light.darken(1)}"
                ),
                "border-radius": theme.rounding.more,
                "background-color": theme.colors.light,
            },
            ".bookmark-box:not(.transparent) *": {
                "color": "inherit",
            },
            ".bookmark-box.invert": {
                "color": theme.colors.light,
                "background-color": theme.colors.dark,
                "border": f"{theme.borders.thin} solid {theme.colors.dark}",
                "border-radius": theme.rounding.more,
            },
            ".bookmark-box:hover": {
                "background-color": theme.colors.light.lighten(1),
                "box-shadow": "rgba(149, 157, 165, 0.2) 0px 8px 24px;",
            },
            ".bookmark-box .bookeric-link.external:hover": {
                "text-decoration": "underline !important",
            },
            ".bookmark-box p.url, .bookmark-box * p.url": {
                "margin": "0.75em 0",
                "font-size": "0.88em",
                "color": "#5c744a",
            },
            ".bookmark-box p.description, .bookmark-box * p.description": {
                "margin": "1em 0 0 0",
                "font-size": "1em",
                "color": "#10140d",
            },
            ".bookmark-box p.image-url, .bookmark-box * p.image-url": {
                "text-align": "center",
                "font-size": "14px",
                "margin": "2px auto",
                "color": "#5c744a",
                "font-style": "italic",
            },
            ".bookmark-box p.image-description, .bookmark-box * p.image-description": {
                "color": "#10140d",
                "margin": "1em .25em",
                "font-size": "1em",
            },
        }
    )


class BookmarkList(Component[NoChildren, GlobalAttrs]):
    def render_tags(self, tags) -> Cluster:
        return Cluster(
            *[
                ButtonLink(tag, to=f"/tags/{tag}", classes=["info small"])
                for tag in tags
            ],
        )

    # Layout for not showing image previews
    def render_bookmark(self, bookmark) -> BookmarkBox:
        return BookmarkBox(
            BookericLink(bookmark["title"], to=bookmark["url"]),
            Paragraph(bookmark["url"], classes=["url"]),
            Paragraph(bookmark["description"], classes=["description"])
            if bookmark.get("description")
            else Paragraph(i("Add a description… \n", classes=["description"])),
            Box(
                Cluster(
                    self.render_tags(bookmark["tags"])
                    if bookmark.get("tags")
                    else Cluster(
                        ButtonLink("none", to="/untagged", classes=["warning small"])
                    ),
                ),
                classes=["no-border no-inline-padding"],
            ),
        )

    @override
    def render(self) -> Switcher:
        return Switcher(*[self.render_bookmark(bm) for bm in self.attrs["bookmarks"]])

    # Layout for showing image previews
    # def render_bookmark(self, bookmark) -> BookmarkBox:
    #     thumbnail_api_url = 'https://api.thumbnail.ws/api/ab2247020d254828b275c75ada9230473674b395d748/thumbnail/get'
    #     return BookmarkBox(
    #         BookericLink(bookmark["title"], to=bookmark["url"]),
    #         Switcher(
    #             Link(ImagePlaceholder(src=f'{thumbnail_api_url}?url={bookmark["url"]}&width=480'),to=bookmark["url"]),
    #             Paragraph(bookmark["url"], classes=["image-url"]),
    #             classes=["no-gap"],
    #         ),
    #         Paragraph(bookmark["description"], classes=["image-description"])
    #         if bookmark.get("description")
    #         else Paragraph(i("Add a description… \n", classes=["image-description"])),
    #         Box(
    #             Cluster(
    #                 self.render_tags(bookmark["tags"])
    #                 if bookmark.get("tags")
    #                 else Cluster(ButtonLink("none", to="/untagged", classes=["warning small"])),
    #             ),
    #             classes=["no-border no-inline-padding no-block-padding"],
    #         ),
    #     )

    # @override
    # def render(self) -> Switcher:
    #     return Switcher(*[self.render_bookmark(bm) for bm in self.attrs["bookmarks"]][:3])
