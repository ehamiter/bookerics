from typing import override

from ludic.attrs import GlobalAttrs
from ludic.catalog.forms import InputField
from ludic.catalog.layouts import Center, Stack
from ludic.catalog.pages import Body, Head, HtmlPage
from ludic.html import meta, link, style
from ludic.types import Component, NoChildren, AnyChildren


class Page(Component[AnyChildren, GlobalAttrs]):
    @override
    def render(self) -> HtmlPage:
        return HtmlPage(
            Head(
                meta(charset="utf-8"),
                link(rel="icon", href="/static/favicon.png"),
                title="bookerics",
            ),
            Body(
                Center(
                    Stack(*self.children, **self.attrs),
                    style={
                        "padding-block": self.theme.sizes.xl
                    },
                ),
                htmx_version="latest",
            ),
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
            **self.attrs,
        )