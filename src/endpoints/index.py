from src.database import fetch_bookmarks, fetch_random_bookmark, fetch_untagged_bookmarks
from src.main import app
from src.pages import Page
from src.components import SearchBar, BookmarkList, NavMenu


@app.get("/")
async def index():
    bookmarks = fetch_bookmarks()
    return Page(
        NavMenu(),
        SearchBar(),
        BookmarkList(bookmarks=[b for b in bookmarks])
    )

@app.get("/random")
async def random_bookmark():
    bookmark = fetch_random_bookmark()
    return Page(
        NavMenu(),
        SearchBar(),
        BookmarkList(bookmarks=[bookmark])
    )

@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_untagged_bookmarks()
    return Page(
        NavMenu(),
        SearchBar(),
        BookmarkList(bookmarks=[b for b in bookmarks])
    )
