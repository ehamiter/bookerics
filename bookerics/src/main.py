import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from ludic.html import style
from ludic.styles import themes
from ludic.styles.themes import Colors, Fonts, Sizes, Switcher
from ludic.styles.types import Color, Size, SizeClamp
from ludic.web import LudicApp
from ludic.web.routing import Mount
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from .database import load_db_on_startup


@dataclass
class BookericsTheme(themes.Theme):
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
            primary=Color("#0096ff"),
            secondary=Color("#fefefe"),
            success=Color("#c9ffad"),
            info=Color("#fff080"),
            warning=Color("#ffc280"),
            danger=Color("#cc3333"),
            light=Color("#f8f8f8"),
            dark=Color("#414549"),
        )
    )


bookerics_theme = BookericsTheme()
themes.set_default_theme(bookerics_theme)


@asynccontextmanager
async def lifespan(_: LudicApp) -> AsyncIterator[None]:
    load_db_on_startup()
    style.load(cache=True)
    yield


# Calculate the directory path
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "..", "static")

# Ensure the path exists
if not os.path.exists(static_dir):
    raise RuntimeError(f"Directory '{static_dir}' does not exist")


app = LudicApp(
    debug=True,
    lifespan=lifespan,
    routes=[Mount("/static", StaticFiles(directory=static_dir), name="static")],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, restrict as needed
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

import bookerics.src.endpoints.errors as _  # noqa
import bookerics.src.endpoints.index as _  # noqa
