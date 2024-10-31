import secrets

from ludic.catalog.layouts import Stack
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from .ai import get_tags_and_description_from_bookmark_url
from .components import (
    BookmarkImageList,
    BookmarkList,
    NavMenu,
    SearchBar,
    TableStructure,
    TagCloud,
    EditBookmarkForm,
)
from .database import (
    backup_bookerics_db,
    create_bookmark,
    create_feed,
    delete_bookmark_by_id,
    fetch_bookmark_by_id,
    fetch_bookmark_by_url,
    fetch_bookmarks,
    fetch_bookmarks_by_tag,
    fetch_unique_tags,
    schedule_feed_creation,
    schedule_upload_to_s3,
    search_bookmarks,
    update_bookmark_description,
    update_bookmark_tags,
    update_bookmark_title,
    verify_table_structure,
)
from .main import app
from .pages import Page
from .utils import logger

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
    bookmarks = fetch_bookmarks(kind="newest")
    bookmark_count = len(bookmarks)
    bookmarks = [secrets.choice(bookmarks)]
    return Page(
        NavMenu(bookmark_count=bookmark_count),
        SearchBar(),
        BookmarkImageList(bookmarks=bookmarks),
    )


@app.get("/tags")
async def tags():
    bookmarks = fetch_bookmarks(kind="newest")
    bookmarks = [bm for bm in bookmarks if bm.get('source') == 'internal']
    tags = fetch_unique_tags(kind="frequency")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)), SearchBar(), TagCloud(tags=tags)
    )


@app.get("/tags/newest")
async def tags():
    bookmarks = fetch_bookmarks(kind="newest")
    bookmarks = [bm for bm in bookmarks if bm.get('source') == 'internal']
    tags = fetch_unique_tags(kind="newest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)), SearchBar(), TagCloud(tags=tags)
    )



@app.get("/tags/{tag}")
async def bookmarks_by_tag(tag: str):
    bookmarks = fetch_bookmarks_by_tag(tag)
    bookmarks = [bm for bm in bookmarks if bm.get('source') == 'internal']

    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )

@app.get("/tags/{tag}/feed")
async def create_feed_for_tag(tag: str):
    bookmarks = fetch_bookmarks_by_tag(tag)
    await create_feed(tag, bookmarks)

    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


@app.get("/untagged")
async def untagged_bookmarks():
    bookmarks = fetch_bookmarks(kind="untagged")
    bookmarks = [bm for bm in bookmarks if bm.get('source') == 'internal']
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
    )


# partials


@app.get("/id/{id}")
async def bookmark_by_id(id: str):
    bookmark = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return HTMLResponse("Bookmark not found", status_code=404)

    bookmarks = [bookmark]
    return BookmarkImageList(bookmarks=bookmarks)


@app.get("/id/c/{id}")
async def bookmark_by_id_compact(id: str):
    bookmark = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return HTMLResponse("Bookmark not found", status_code=404)

    bookmarks = [bookmark]
    return BookmarkList(bookmarks=bookmarks)

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
    tags, description = await get_tags_and_description_from_bookmark_url(
        bookmark["url"]
    )

    await update_bookmark_tags(bookmark["id"], tags)
    await update_bookmark_description(bookmark["id"], description)

    return BookmarkList().render_tags(tags)


@app.get("/get_thumbnail/{id}")
async def get_thumbnail(request: Request):
    bookmark_id = request.path_params["id"]
    headers = {"HX-Trigger": "loadThumbnail"}
    bookmark = await fetch_bookmark_by_id(bookmark_id)
    if bookmark:
        thumbnail_html = f'<img src="{bookmark["thumbnail_url"]}" height="270" width="480" id="thumbnail-{bookmark_id}" />'
        return HTMLResponse(thumbnail_html, headers=headers)

    logging.error(f"💥 Bookmark not found for id: {bookmark_id}")
    return HTMLResponse("<p>Bookmark not found</p>", status_code=404)


@app.get("/check")
async def check_if_bookmark_already_saved(request: Request):
    status = "not-exists"
    bookmark = {}
    url = request.query_params.get('url')
    if url:
        bookmark = await fetch_bookmark_by_url(url)
        if bookmark:
            status = "exists"

    return JSONResponse(
        {"status": status, "message": bookmark}
    )


@app.post("/add")
async def add_bookmark(request: Request):
    form = await request.form()
    title = form.get("title")
    url = form.get("url")
    description = form.get("description")
    tags = form.get("tags", "").split(" ")
    force_update = form.get("forceUpdate")

    if not title and url:
        return JSONResponse(
            {"status": "error", "message": "Title and URL are required!"}
        )

    # Does it already exist in our db?
    bookmark = await fetch_bookmark_by_url(url)
    if bookmark:
        # Update the existing bookmark with any new info.
        if force_update:
            await update_bookmark_description(bookmark["id"], description)
            await update_bookmark_tags(bookmark["id"], tags)
            await update_bookmark_title(bookmark["id"], title)
            logger.info(f"Bookmark updated!")
            return JSONResponse(
                {"status": "success", "message": "Bookmark updated!"}
            )
        else:
            return JSONResponse(
                {"status": "success", "message": "Bookmark not updated."}
            )

    bookmark = await create_bookmark(title, url, description, tags)
    return JSONResponse(
        {"status": "success", "message": "Bookmark saved!"}
    )



@app.get("/update")
async def update():
    try:
        # First get the bookmarks while we know the connection is good
        bookmarks = fetch_bookmarks(kind="newest")
        bookmarks = [bm for bm in bookmarks if bm.get('source') == 'internal']
        
        # Then do the backup operations
        backup_bookerics_db()
        await schedule_upload_to_s3()
        
        # Finally schedule feed creation
        await schedule_feed_creation(tag=None, bookmarks=bookmarks, publish=True)

        return JSONResponse(
            {"status": "success", "message": "File backed up locally and uploaded to S3. Feed created."}
        )
    except Exception as e:
        logger.error(f"Error in update route: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)}, status_code=500
        )


@app.get("/update_thumbnail/{id}")
async def update_thumbnail(request: Request):
    bookmark_id = request.path_params["id"]
    headers = {"HX-Trigger": "loadThumbnail"}
    logger.info(f"Sending HX-Trigger header for bookmark id: {bookmark_id}")
    return JSONResponse({"status": "thumbnail loaded"}, headers=headers)


@app.delete("/delete/{bookmark_id}")
async def delete_bookmark(bookmark_id: str):
    try:
        await delete_bookmark_by_id(int(bookmark_id))
        return HTMLResponse("")
    except Exception as e:
        logger.error(f"Error deleting bookmark: {e}")
        return HTMLResponse(f"Failed to delete: {str(e)}", status_code=500)


# misc


@app.get("/table")
async def table_structure():
    structure = verify_table_structure()
    bookmarks = fetch_bookmarks(kind="newest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        TableStructure(structure=structure),
    )


@app.get("/edit/{bookmark_id}")
async def edit_bookmark(bookmark_id: str):
    bookmark = await fetch_bookmark_by_id(id=bookmark_id)
    if not bookmark:
        return HTMLResponse("Bookmark not found", status_code=404)
    
    return Page(
        NavMenu(),
        EditBookmarkForm(bookmark=bookmark),
    )

@app.post("/edit/{bookmark_id}")
async def update_bookmark(bookmark_id: str, request: Request):
    form = await request.form()
    title = form.get("title")
    url = form.get("url")
    description = form.get("description")
    tags = form.get("tags", "").split(" ")
    
    await update_bookmark_title(bookmark_id, title)
    await update_bookmark_description(bookmark_id, description)
    await update_bookmark_tags(bookmark_id, tags)
    
    # Redirect to home page after saving
    return RedirectResponse(url="/", status_code=303)
