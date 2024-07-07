import json
from typing import override

from ludic.attrs import GlobalAttrs
from ludic.catalog.layouts import Center, Stack
from ludic.catalog.pages import Body, HtmlHeadAttrs, HtmlPage
from ludic.html import div, head, link, meta, script, style, title
from ludic.types import AnyChildren, BaseElement, Component

from .database import BOOKMARK_NAME


class CustomHead(Component[AnyChildren, HtmlHeadAttrs]):
    @override
    def render(self) -> head:
        elements: list[BaseElement] = [
            meta(charset="utf-8"),
            meta(
                name="viewport",
                content="width=device-width, initial-scale=1, shrink-to-fit=no",
            ),
            meta(name="description", content="Bookmarks, but for Erics."),
            meta(
                name="keywords",
                content="bookmarks, eric hamiter, web, python, ludic, software",
            ),
            meta(name="author", content="Eric Hamiter"),
            script(src="/static/js/htmx.min.js", defer=True),
            script(src="/static/js/custom.js", defer=True),
            title(self.attrs.get("title", "bookerics")),
            # Background photo originally by Jess Bailey on Unsplash:
            # https://unsplash.com/photos/close-shot-of-book-page-X5gDoysLbBc
            link(rel="icon", href="/static/favicon.ico", type="image/x-icon"),
            style(
                """html { background: url("/static/images/bg.png") no-repeat center center fixed; -webkit-background-size: cover; -moz-background-size: cover; -o-background-size: cover; background-size: cover;}"""
            ),  # no fmt
        ]

        if favicon := self.attrs.get("favicon"):
            elements.append(link(rel="icon", href=favicon, type="image/x-icon"))
        if config := self.attrs.get("htmx_config", {"defaultSwapStyle": "outerHTML"}):
            elements.append(meta(name="htmx-config", content=json.dumps(config)))
        if self.attrs.get("load_styles", True):
            elements.append(style.load(cache=True))

        return head(*elements, *self.children)


class Page(Component[AnyChildren, GlobalAttrs]):
    @override
    def render(self) -> HtmlPage:
        return HtmlPage(
            CustomHead(
                title=f"{BOOKMARK_NAME}s",
            ),
            Body(
                Center(
                    div(
                        Stack(*self.children, **self.attrs),
                        id="results-container",
                        style={"padding-block": self.theme.sizes.xs},
                    ),
                ),
            ),
        )
