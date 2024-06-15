from ludic.catalog.layouts import Box, Cluster, Stack, Switcher
from ludic.catalog.typography import CodeBlock
from ludic.html import div
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, HTMLResponse

from src.components import (BookmarkList, BookmarkImageList, NavMenu, SearchBar, TableStructure,
                            TagCloud)
from src.database import (create_bookmark, fetch_bookmarks,
                          fetch_bookmarks_by_tag, delete_bookmark_by_id, fetch_unique_tags,
                          schedule_upload_to_s3, search_bookmarks,
                          verify_table_structure)
from src.main import app
from src.pages import Page
from src.utils import logger


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
        BookmarkImageList(bookmarks=bookmarks),
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
    bookmarks = fetch_bookmarks(kind="newest")
    tags = fetch_unique_tags(kind="frequency")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)), SearchBar(), TagCloud(tags=tags)
    )


@app.get("/tags/newest")
async def tags():
    bookmarks = fetch_bookmarks(kind="newest")
    tags = fetch_unique_tags(kind="newest")
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
async def update():
    schedule_upload_to_s3()
    return JSONResponse({"status": "success", "message": "File uploaded to S3"})


@app.post("/add")
async def add_bookmark(request: Request):
    form = await request.form()
    title = form.get("title")
    url = form.get("url")
    description = form.get("description", "Add a description…")
    # TODO: suggest tags automatically
    tags = form.get("tags", "").split(" ")

    if title and url:
        create_bookmark(title, url, description, tags)
        return JSONResponse(
            {"status": "success", "message": "Bookmark saved!"}, status_code=201
        )
    return JSONResponse(
        {"status": "error", "message": "Title and URL are required!"}, status_code=400
    )


@app.delete("/delete/{bookmark_id}")
async def delete_bookmark(request: Request):
    bookmark_id = request.path_params['bookmark_id']
    try:
        delete_bookmark_by_id(bookmark_id)
        # Return a minimal response to trigger the swap
        return HTMLResponse('', status_code=200)
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error deleting bookmark: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.png")


@app.get("/table")
async def table_structure():
    structure = verify_table_structure()
    bookmarks = fetch_bookmarks(kind="newest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        TableStructure(structure=structure),
    )
