import base64
import webbrowser

from ludic.catalog.layouts import Stack
from starlette.requests import Request
from starlette.responses import (FileResponse, HTMLResponse, JSONResponse)

from .components import (BookmarkImageList, BookmarkList, NavMenu, SearchBar,
                         TableStructure, TagCloud)
from .constants import UPDATE_BASE_URL
from .database import (backup_bookerics_db, create_bookmark,
                       delete_bookmark_by_id, fetch_bookmark_by_id,
                       fetch_bookmarks, fetch_bookmarks_by_tag,
                       fetch_unique_tags, schedule_upload_to_s3,
                       search_bookmarks, verify_table_structure, update_bookmark_tags, update_bookmark_description)
from .main import app
from .pages import Page
from .utils import logger
from .ai import get_tags_and_description_from_bookmark_url


# main routes


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


@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_bookmarks(kind="untagged")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


# partials


@app.get("/id/{id}")
async def bookmark_by_id(id: str):
    bookmarks = await fetch_bookmark_by_id(id=id)
    if not bookmarks:
        return HTMLResponse("Bookmark not found", status_code=404)

    return BookmarkImageList(bookmarks=bookmarks)


@app.get("/id/c/{id}")
async def bookmark_by_id_compact(id: str):
    bookmarks = await fetch_bookmark_by_id(id=id)
    if not bookmarks:
        return HTMLResponse("Bookmark not found", status_code=404)

    return BookmarkList(bookmarks=bookmarks)


@app.get("/update/{bookmark_id}")
def update_bookmark_by_id(bookmark_id: str):
    pk_b64_id = base64.b64encode(bookmark_id.encode()).decode("utf8")
    update_url = f"{UPDATE_BASE_URL}/{pk_b64_id}/"
    webbrowser.open_new_tab(update_url)


@app.get("/search")
async def search(request: Request):
    query = request.query_params.get("query", "")
    bookmarks = search_bookmarks(query)
    return Stack(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(query=query),
        BookmarkList(bookmarks=bookmarks),
    )


# utils

@app.get("/ai/{id}")
async def get_ai_info_for_bookmark_by_id(id: str):
    bookmark = await fetch_bookmark_by_id(id=id)
    tags, description = await get_tags_and_description_from_bookmark_url(bookmark[0]["url"])

    await update_bookmark_tags(bookmark[0]['id'], tags)
    await update_bookmark_description(bookmark[0]['id'], description)
    # return JSONResponse(
    #         {"status": "success", "tags": tags}, status_code=201
    #     )
    return BookmarkList().render_tags(tags)

@app.get("/get_thumbnail/{id}")
async def get_thumbnail(request: Request):
    bookmark_id = request.path_params["id"]
    headers = {"HX-Trigger": "loadThumbnail"}
    bookmark = await fetch_bookmark_by_id(bookmark_id)
    if bookmark:
        logger.info(f"Found bookmark # {bookmark_id}!")
        bookmark = bookmark[
            0
        ]  # fetch_bookmark_by_id returns a list, so take the first item
        thumbnail_html = f'<img src="{bookmark["thumbnail_url"]}" height="270" width="480" id="thumbnail-{bookmark_id}" />'
        logger.info(f"Returning HTML for thumbnail id: {bookmark_id}")
        return HTMLResponse(thumbnail_html, headers=headers)
    logging.info(f"Bookmark not found for id: {bookmark_id}")
    return HTMLResponse("<p>Bookmark not found</p>", status_code=404)


@app.post("/add")
async def add_bookmark(request: Request):
    form = await request.form()
    title = form.get("title")
    url = form.get("url")
    description = form.get("description", "Add a description…")
    tags = form.get("tags", "").split(" ")

    if title and url:
        bookmark_id = await create_bookmark(title, url, description, tags)

        return JSONResponse(
            {"status": "success", "message": "Bookmark saved!"}, status_code=201
        )

    return JSONResponse(
        {"status": "error", "message": "Title and URL are required!"}, status_code=400
    )


@app.get("/update")
async def update():
    backup_bookerics_db()
    schedule_upload_to_s3()
    return JSONResponse(
        {"status": "success", "message": "File backed up locally and uploaded to S3"}
    )


@app.get("/update_thumbnail/{id}")
async def update_thumbnail(request: Request):
    bookmark_id = request.path_params["id"]
    headers = {"HX-Trigger": "loadThumbnail"}
    logger.info(f"Sending HX-Trigger header for bookmark id: {bookmark_id}")
    return JSONResponse({"status": "thumbnail loaded"}, headers=headers)


@app.delete("/delete/{bookmark_id}")
async def delete_bookmark(request: Request):
    bookmark_id = request.path_params["bookmark_id"]
    try:
        delete_bookmark_by_id(bookmark_id)
        # Return a minimal response to trigger the swap
        return HTMLResponse("", status_code=200)
    except Exception as e:
        # Log the error for debugging purposes
        logger.error(f"Error deleting bookmark: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# misc


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/table")
async def table_structure():
    structure = verify_table_structure()
    bookmarks = fetch_bookmarks(kind="newest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        TableStructure(structure=structure),
    )
