import json
from typing import override

from ludic.attrs import GlobalAttrs
from ludic.catalog.layouts import Center, Stack
from ludic.catalog.pages import Body, HtmlHeadAttrs, HtmlPage
from ludic.html import head, link, meta, style, title
from ludic.types import AnyChildren, BaseElement, Component


class CustomHead(Component[AnyChildren, HtmlHeadAttrs]):
    @override
    def render(self) -> head:
        elements: list[BaseElement] = [
            meta(charset="utf-8"),
            meta(
                name="viewport",
                content="width=device-width, initial-scale=1, shrink-to-fit=no",
            ),
            title(self.attrs.get("title", "Ludic App")),
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
                meta(charset="utf-8"),
                link(rel="icon", href="/static/favicon.png"),
                title="bookerics",
            ),
            Body(
                Center(
                    Stack(*self.children, **self.attrs),
                    style={
                        "padding-block": self.theme.sizes.xxl,
                    },
                ),
                htmx_version="latest",
            ),
        )
