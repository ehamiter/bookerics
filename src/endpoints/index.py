from ludic.catalog.layouts import Box, Cluster, Stack, Switcher
from ludic.html import div
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.components import BookmarkList, NavMenu, SearchBar, TagCloud
from src.database import (schedule_upload_to_s3, fetch_bookmarks, fetch_bookmarks_by_tag,
                          fetch_unique_tags, search_bookmarks, create_bookmark)
from src.main import app
from src.pages import Page


@app.get("/")
async def index():
    bookmarks = fetch_bookmarks(kind="newest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


@app.get("/oldest")
async def oldest():
    bookmarks = fetch_bookmarks(kind="oldest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


@app.get("/random")
async def random_bookmark():
    bookmarks = fetch_bookmarks(kind="random")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_bookmarks(kind="untagged")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


@app.get("/tags")
async def tags():
    bookmarks = fetch_bookmarks(kind="all")
    tags = fetch_unique_tags()
    return Page(
        NavMenu(bookmark_count=len(bookmarks)), SearchBar(), TagCloud(tags=tags)
    )


@app.get("/tags/{tag}")
async def bookmarks_by_tag(tag: str):
    bookmarks = fetch_bookmarks_by_tag(tag)
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


@app.get("/search")
async def search(request: Request):
    query = request.query_params.get("query", "")
    bookmarks = search_bookmarks(query)
    return Stack(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(query=query),
        BookmarkList(bookmarks=bookmarks),
    )

@app.get("/update")
async def index():
    schedule_upload_to_s3()
    bookmarks = fetch_bookmarks(kind="newest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


@app.post("/add")
async def add_bookmark(request: Request):
    data = await request.json()
    title = data.get("title")
    url = data.get("url")
    description = data.get("description", "Add a description…")
    # TODO: suggest tags automatically
    tags = data.get("tags", [])

    if title and url:
        create_bookmark(title, url, description, tags)
        return JSONResponse({"status": "success", "message": "Bookmark saved!"}, status_code=201)
    return JSONResponse({"status": "error", "message": "Title and URL are required!"}, status_code=400)
