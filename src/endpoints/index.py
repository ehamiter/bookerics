from src.components import BookmarkList, NavMenu, SearchBar
from src.database import fetch_bookmarks, search_bookmarks
from src.main import app
from src.pages import Page
from ludic.catalog.layouts import Box, Cluster, Stack, Switcher
from starlette.requests import Request
from ludic.html import div


@app.get("/")
async def index():
    bookmarks = fetch_bookmarks(kind="all")
    return Page(NavMenu(bookmark_count=len(bookmarks)), SearchBar(), BookmarkList(bookmarks=bookmarks))

@app.get("/oldest")
async def oldest():
    bookmarks = fetch_bookmarks(kind="oldest")
    return Page(NavMenu(bookmark_count=len(bookmarks)), SearchBar(), BookmarkList(bookmarks=bookmarks))

@app.get("/random")
async def random_bookmark():
    bookmarks = fetch_bookmarks(kind="random")
    return Page(NavMenu(bookmark_count=len(bookmarks)), SearchBar(), BookmarkList(bookmarks=bookmarks))

@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_bookmarks(kind="untagged")
    return Page(NavMenu(bookmark_count=len(bookmarks)), SearchBar(), BookmarkList(bookmarks=bookmarks))

@app.get("/search")
async def search(request: Request):
    query = request.query_params.get("query", "")
    bookmarks = search_bookmarks(query)
    return Stack(NavMenu(bookmark_count=len(bookmarks)), SearchBar(), BookmarkList(bookmarks=bookmarks))
