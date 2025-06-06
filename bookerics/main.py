import tracemalloc
tracemalloc.start()

import os
from collections.abc import AsyncIterator

# from ludic.html import style # Removed
# from ludic.styles import themes # Removed
# from ludic.styles.themes import Colors, Fonts # Removed
# from ludic.styles.types import Color # Removed
# from ludic.web import LudicApp # Removed
from starlette.routing import Mount
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fasthtml.common import fast_app
from contextlib import asynccontextmanager

from .database import load_db_on_startup


# @dataclass # Removed BookericsTheme
# class BookericsTheme(themes.Theme):
#     name: str = "bookerics-theme"
#
#     fonts: Fonts = field(
#         default_factory=lambda: Fonts(
#             plain="Helvetica Neue, Helvetica, Arial, sans-serif",
#             serif="Helvetica Neue, Helvetica, Arial, sans-serif",
#             mono="Edlo, Space Mono, Roboto Mono, monospace",
#         )
#     )
#
#     colors: Colors = field(
#         default_factory=lambda: Colors(
#             primary=Color("#0096ff"),
#             secondary=Color("#fefefe"),
#             success=Color("#c9ffad"),
#             info=Color("#fff080"),
#             warning=Color("#ffc280"),
#             danger=Color("#cc3333"),
#             light=Color("#f8f8f8"),
#             dark=Color("#414549"),
#         )
#     )

# bookerics_theme = BookericsTheme() # Removed
# themes.set_default_theme(bookerics_theme) # Removed


# @asynccontextmanager # Removed lifespan
# async def lifespan(_: LudicApp) -> AsyncIterator[None]:
#     load_db_on_startup() # TODO: Address this with FastHTML equivalent
#     style.load(cache=True) # TODO: Address this with FastHTML equivalent
#     yield


# Calculate the directory path
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
feeds_dir = os.path.join(base_dir, "feeds")

# Ensure the path exists
if not os.path.exists(static_dir):
    raise RuntimeError(f"Directory '{static_dir}' does not exist")

if not os.path.exists(feeds_dir):
    raise RuntimeError(f"Directory '{feeds_dir}' does not exist")

# TODO: style.load(cache=True) # Needs to be handled, Ludic specific styling

@asynccontextmanager
async def app_lifespan(app_instance) -> AsyncIterator[None]: # Renamed from 'lifespan' to avoid conflict if fast_app uses 'lifespan' internally
    load_db_on_startup()
    # style.load(cache=True) # Ludic specific, replacement TBD
    yield

app, rt = fast_app(debug=True, lifespan=app_lifespan) # Added debug and lifespan

# Add static file mounts
app.router.routes.append(
    Mount("/static", StaticFiles(directory=static_dir), name="static")
)
app.router.routes.append(
    Mount("/feeds", StaticFiles(directory=feeds_dir), name="feeds")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, restrict as needed
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# import bookerics.errors as _  # noqa # Commented out
import bookerics.routes as _  # noqa # Uncommented

def start():
    import uvicorn
    uvicorn.run(
        "bookerics.main:app",
        host="0.0.0.0",
        port=50667,  # ASCII sum of "bookerics" modulo 16384 + 49152
        reload=True
    )
