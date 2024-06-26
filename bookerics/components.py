import asyncio
from textwrap import dedent
from typing import override

import aiohttp
import requests
from ludic.attrs import Attrs, GlobalAttrs, ImgAttrs
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
from ludic.html import a, b, div, h6, i, img
from ludic.html import script as Script
from ludic.html import small, style
from ludic.types import (AnyChildren, Component, ComponentStrict, JavaScript,
                         NoChildren, PrimitiveChildren)

from .constants import BASE_URL, GIPHY_API_KEY
from .database import BOOKMARK_NAME, update_bookmarks_with_thumbnails
from .utils import logger


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
            target="_blank",
            classes=["bookeric-link external"],
            style={
                "font-weight": "normal",
                "font-size": "1rem",
                "color": "#0086e5",
                "text-decoration": "none",
                "outline": "none",
            },
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


class PreviewImage(Component[img, ImgAttrs]):
    classes = ["image-placeholder"]
    styles = {
        ".image-placeholder": {
            "height": "auto",
            "width": "100%",
            "max-width": "480px",
            "margin-top": "1em",
            "box-shadow": "rgba(0, 0, 0, 0.4) 0px 2px 4px, rgba(0, 0, 0, 0.3) 0px 7px 13px -3px, rgba(0, 0, 0, 0.2) 0px -3px 0px inset;",
            "background": "#85acc934",
        }
    }

    def get_random_giphy_url(self):
        _url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=waiting&rating=r"
        r = requests.get(_url)
        giphy_url = r.json()["data"]["images"]["original"]["url"]
        return giphy_url

    @override
    def render(self) -> img:
        if not self.attrs.get("src"):
            self.attrs["src"] = self.get_random_giphy_url()
            self.attrs["placeholder"] = True
        return img(*self.children, **self.attrs)


class ImageSwitcher(div):
    classes = ["image-switcher"]
    styles = style.use(
        lambda theme: {
            ".image-switcher": {
                "display": "flex",
                "flex-direction": "column",
                "flex-wrap": "wrap",
                "gap": theme.sizes.xxxs,
                "justify-content": "center",  # Center the items horizontally
                "align-items": "center",
            },
            ".no-gap": {
                "gap": "0",
            },
            ".image-switcher > *": {
                "width": "100%",
                "text-align": "center",
            },
            (
                f".image-switcher > :nth-last-child(n+{theme.layouts.switcher.limit+1})",
                f".image-switcher > :nth-last-child(n+{theme.layouts.switcher.limit+1}) ~ *",
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
                "position": "relative",
                "padding": theme.sizes.m,
                "color": theme.colors.dark,
                "transition": "background-color 0.3s ease, box-shadow 0.3s ease",
            },
            ".bookmark-box.small": {
                "padding": theme.sizes.xs,
            },
            ".bookmark-box.large": {
                "padding": theme.sizes.l,
            },
            ".bookmark-box:not(.transparent)": {
                "border": ("1px solid #bababa"),
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
            ".box": {
                "padding": "1em 0 0 0",
            },
            ".bookmark-box p.url, .bookmark-box * p.url": {
                "margin": "0.75em 0",
                "font-size": "0.88em",
                "font-weight": "500",
                "color": "#5c744a",
            },
            ".bookmark-box p.description, .bookmark-box * p.description": {
                "color": "#10140d",
                "margin": "1em 0 0 0",
                "font-size": "1em",
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
            ".update-btn": {
                "position": "absolute",
                "bottom": "1rem;",
                "right": "2rem;",
                "background": "none",
                "border": "none",
                "cursor": "pointer",
                "font-size": "1rem",
                "opacity": "0.75",
            },
            ".update-bookmark": {
                "text-align": "center",
            },
            ".toggle-image-preview-btn": {
                "position": "absolute",
                "top": "1rem;",
                "right": "0.5rem;",
                "background": "none",
                "border": "none",
                "font-size": "1rem",
                "opacity": "0.25",
                "cursor": "pointer",
            },
            ".delete-btn": {
                "position": "absolute",
                "bottom": "1rem;",
                "right": "0.5rem;",
                "background": "none",
                "border": "none",
                "cursor": "not-allowed",
                "font-size": "1rem",
                "opacity": "0.75",
            },
            '.delete-btn[data-confirmed="true"]': {
                "cursor": "pointer",
            },
            ".btn.tag": {
                "border": "1px solid #4a4a4a4a;",
                "font-size": "0.8em;",
                "padding": "clamp(0.23rem, 0.23rem + 0vw, 0.28rem) clamp(0.47rem, 0.47rem + 0.1vw, 0.59rem);",
            },
            ".btn.tag:hover": {
                "filter": "none;",
                "border": "1px solid #4a4a4a77;",
                "background-color": "#fff59b;",
                "text-decoration": "none;",
                "box-shadow": "rgba(0, 0, 0, 0.18) 0px 2px 4px;",
            },
        }
    )


class HTMXDeleteButton(ComponentStrict[PrimitiveChildren, LinkAttrs]):
    classes = ["btn"]

    @override
    def render(self) -> a:
        attrs: HyperlinkAttrs = {
            "href": self.attrs.get("to", "#"),
            "hx-target": self.attrs.get("hx_target"),
            "hx-swap": self.attrs.get("hx_swap"),
            "class": " ".join(self.classes + self.attrs.get("classes", [])),
            "data-delete-url": self.attrs.get("hx_delete"),
            "data-confirmed": "false",
        }
        return a(self.children[0], **attrs)


class ToggleImagePreviewButton(ComponentStrict[PrimitiveChildren, LinkAttrs]):
    classes = ["btn toggle-image-preview-btn"]

    @override
    def render(self) -> a:
        attrs: HyperlinkAttrs = {
            "hx-get": self.attrs.get("hx_get"),
            "hx-target": self.attrs.get("hx_target"),
            "hx-swap": self.attrs.get("hx_swap"),
            "class": " ".join(self.classes + self.attrs.get("classes", [])),
        }
        return a(self.children[0], **attrs)


class UpdateBookmarkButton(ComponentStrict[PrimitiveChildren, LinkAttrs]):
    classes = ["btn update-btn"]

    @override
    def render(self) -> a:
        attrs = {
            "href": self.attrs.get("to", "#"),
            "hx-swap": "none",
            "hx-get": self.attrs.get("hx_get"),
            "class": " ".join(self.classes + self.attrs.get("classes", [])),
        }
        return a(self.children[0], **attrs)


class UpdatingBookmarkMessage(Component[NoChildren, GlobalAttrs]):
    @override
    def render(self) -> Switcher:
        bookmark_id = self.attrs.get("bookmark_id")
        return BookmarkBox(
            Paragraph(
                Link(
                    f"Updating {BOOKMARK_NAME} # {bookmark_id}, click here to return to {BOOKMARK_NAME}s…",
                    classes=["update-bookmark"],
                    to="/",
                    title="",
                ),
            ),
            id=f"bookmark-{bookmark_id}",
            classes=["update-bookmark"],
        )


class BookmarkList(Component[NoChildren, GlobalAttrs]):
    def render_tags(self, tags) -> Cluster:
        return Cluster(
            *[ButtonLink(tag, to=f"/tags/{tag}", classes=["tag info"]) for tag in tags],
        )

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
                        ButtonLink("none", to="/untagged", classes=["tag warning"])
                    ),
                ),
                classes=["no-border no-inline-padding"],
            ),
            ToggleImagePreviewButton(
                "➕",
                hx_get=f"/id/{bookmark['id']}",
                hx_target=f"#bookmark-{bookmark['id']}",
                hx_swap="outerHTML",
            ),
            UpdateBookmarkButton(
                "✒️",
                hx_get=f"/update/{bookmark['id']}",
            ),
            HTMXDeleteButton(
                "🗑️",
                to="#",
                classes=["delete-btn"],
                hx_target=f"#bookmark-{bookmark['id']}",
                hx_swap="outerHTML",
                hx_delete=f"/delete/{bookmark['id']}",
            ),
            id=f"bookmark-{bookmark['id']}",
            classes=["bookmark-box"],
        )

    @override
    def render(self) -> Switcher:
        return Switcher(*[self.render_bookmark(bm) for bm in self.attrs["bookmarks"]])


class BookmarkImageList(Component[NoChildren, GlobalAttrs]):
    """currently limited to fetching one entry"""

    def __init__(self, bookmarks):
        super().__init__()
        self.bookmarks = bookmarks[:1]
        # Schedule the async fetching of thumbnails
        asyncio.create_task(self.fetch_thumbnails())

    async def fetch_thumbnails(self):
        self.bookmarks = await update_bookmarks_with_thumbnails(self.bookmarks)

    def render_tags(self, tags) -> Cluster:
        return Cluster(
            *[ButtonLink(tag, to=f"/tags/{tag}", classes=["tag info"]) for tag in tags],
        )

    # Layout for showing image previews
    def render_bookmark(self, bookmark) -> BookmarkBox:
        return BookmarkBox(
            BookericLink(bookmark["title"], to=bookmark["url"]),
            ImageSwitcher(
                Link(
                    PreviewImage(
                        src=bookmark["thumbnail_url"],
                        height="270",
                        width="480",
                        id=f"thumbnail-{bookmark['id']}",
                        hx_get=f"/get_thumbnail/{bookmark['id']}",
                        hx_target=f"#thumbnail-{bookmark['id']}",
                        hx_trigger="loadThumbnail from:body",
                        hx_swap="outerHTML",
                    ),
                    to=bookmark["url"],
                ),
                Paragraph(bookmark["url"], classes=["image-url"]),
            ),
            Paragraph(bookmark["description"], classes=["image-description"])
            if bookmark.get("description")
            else Paragraph(i("Add a description… \n"), classes=["image-description"]),
            Box(
                Cluster(
                    self.render_tags(bookmark["tags"])
                    if bookmark.get("tags")
                    else Cluster(
                        ButtonLink("none", to="/untagged", classes=["tag warning"])
                    ),
                ),
                classes=["no-border no-inline-padding no-block-padding"],
            ),
            UpdateBookmarkButton(
                "✒️",
                hx_get=f"/update/{bookmark['id']}",
            ),
            ToggleImagePreviewButton(
                "➖",
                hx_get=f"/id/c/{bookmark['id']}",
                hx_target=f"#bmb-{bookmark['id']}",
                hx_swap="outerHTML",
            ),
            HTMXDeleteButton(
                "🗑️",
                to="#",
                classes=["delete-btn"],
                hx_target=f"#bmb-{bookmark['id']}",
                hx_swap="outerHTML",
                hx_delete=f"/delete/{bookmark['id']}",
            ),
            id=f"bmb-{bookmark['id']}",
            classes=["bookmark-box"],
        )

    @override
    def render(self) -> Switcher:
        return Switcher(*[self.render_bookmark(bm) for bm in self.bookmarks])
