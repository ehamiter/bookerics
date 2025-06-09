import tracemalloc
tracemalloc.start()

import os
from collections.abc import AsyncIterator

from starlette.routing import Mount
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fasthtml.common import fast_app
from contextlib import asynccontextmanager

from .database import load_db_on_startup


# Calculate the directory path
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
feeds_dir = os.path.join(base_dir, "feeds")

# Ensure the path exists
if not os.path.exists(static_dir):
    raise RuntimeError(f"Directory '{static_dir}' does not exist")

if not os.path.exists(feeds_dir):
    raise RuntimeError(f"Directory '{feeds_dir}' does not exist")

@asynccontextmanager
async def app_lifespan(app_instance) -> AsyncIterator[None]:
    load_db_on_startup()
    yield

app, rt = fast_app(debug=True, lifespan=app_lifespan, static_path=base_dir)

# Add feeds route manually since FastHTML doesn't handle this by default
app.router.routes.append(
    Mount("/feeds", StaticFiles(directory=feeds_dir), name="feeds")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, restrict as needed
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Import routes after app and rt are fully created to avoid circular import issues
import bookerics.errors as _  # noqa # Uncommented
import bookerics.routes as _  # noqa # Uncommented

def start():
    import uvicorn
    uvicorn.run(
        "bookerics.main:app",
        host="0.0.0.0",
        port=50113,  # ASCII sum of "bookerics" modulo 16384 + 49152
        reload=True
    )
