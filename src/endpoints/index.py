from src.components import BookmarkList, NavMenu, SearchBar
from src.database import fetch_bookmarks
from src.main import app
from src.pages import Page


@app.get("/")
async def index():
    bookmarks = fetch_bookmarks(kind=None)
    return Page(NavMenu(), SearchBar(), BookmarkList(bookmarks=[b for b in bookmarks]))


@app.get("/random")
async def random_bookmark():
    bookmark = fetch_bookmarks(kind="random")
    return Page(NavMenu(), SearchBar(), BookmarkList(bookmarks=bookmark))


@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_bookmarks(kind="untagged")
    return Page(NavMenu(), SearchBar(), BookmarkList(bookmarks=[b for b in bookmarks]))
