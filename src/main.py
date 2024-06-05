from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from ludic.html import style
from ludic.styles import themes
from ludic.styles.themes import Colors, Fonts
from ludic.styles.types import Color
from ludic.web import LudicApp
from ludic.web.routing import Mount
from starlette.staticfiles import StaticFiles


@dataclass
class BookericsTheme(themes.LightTheme):
    name: str = "bookerics-theme"

    fonts: Fonts = field(
        default_factory=lambda: Fonts(
            plain="Helvetica Neue, Helvetica, Arial, sans-serif",
            serif="Helvetica Neue, Helvetica, Arial, sans-serif",
            mono="Edlo, Space Mono, Roboto Mono, monospace",
        )
    )

    colors: Colors = field(
        default_factory=lambda: Colors(
            primary=Color("#c2e7fd"),
            secondary=Color("#fefefe"),
            success=Color("#c9ffad"),
            info=Color("#fff080"),
            warning=Color("#ffc280"),
            danger=Color("#ffaca1"),
            light=Color("#f8f8f8"),
            dark=Color("#414549"),
        )
    )


bookerics_theme = BookericsTheme()
themes.set_default_theme(bookerics_theme)


@asynccontextmanager
async def lifespan(_: LudicApp) -> AsyncIterator[None]:
    style.load(cache=True)
    yield


app = LudicApp(
    debug=True,
    lifespan=lifespan,
    routes=[Mount("/static", StaticFiles(directory="static"), name="static")],
)


import src.endpoints.errors as _  # noqa
import src.endpoints.index as _  # noqa
