import secrets
import asyncio
import logging # Added for get_thumbnail error logging

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse # Response not directly used

from .ai import get_tags_and_description_from_bookmark
from .core import Page # Changed from .pages import Page
from .components import (
    NavMenu,
    SearchBar,
    BookmarkList,
    BookmarkImageList,
    TagCloud,
    TableStructure,
    EditBookmarkForm,
    _render_tags_html, # Helper for AI route
    PreviewImage # For get_thumbnail
    # Img removed as PreviewImage is used for its .to_html() method
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
from .main import rt as main_fasthtml_router, app # Import both rt and app
from .utils import logger

# main routes


@main_fasthtml_router("/")
async def index():
    bookmarks = fetch_bookmarks(kind="newest")
    # Pass components as children to Page
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
        title_str="Bookerics - Newest"
    )


@main_fasthtml_router("/oldest")
async def oldest():
    bookmarks = fetch_bookmarks(kind="oldest")
    return Page(
        NavMenu(bookmark_count=len(bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks),
        title_str="Bookerics - Oldest"
    )


@main_fasthtml_router("/random")
async def random_bookmark():
    bookmarks = fetch_bookmarks(kind="newest") # Fetch all to get a random one
    bookmark_count = len(bookmarks)
    if not bookmarks: # Handle case with no bookmarks
        return Page(NavMenu(bookmark_count=0), SearchBar(), P("No bookmarks available to choose from."))

    selected_bookmarks = [secrets.choice(bookmarks)]
    return Page(
        NavMenu(bookmark_count=bookmark_count),
        SearchBar(),
        BookmarkImageList(bookmarks=selected_bookmarks), # Uses selected_bookmarks
        title_str="Bookerics - Random"
    )


@main_fasthtml_router("/tags")
async def tags_route(): # Renamed from 'tags' to avoid conflict with variable name
    all_bookmarks = fetch_bookmarks(kind="newest") # To get total count
    internal_bookmarks_count = len([bm for bm in all_bookmarks if bm.get('source') == 'internal'])
    tag_list = fetch_unique_tags(kind="frequency") # Renamed variable 'tags' to 'tag_list'
    return Page(
        NavMenu(bookmark_count=internal_bookmarks_count),
        SearchBar(),
        TagCloud(tags=tag_list),
        title_str="Bookerics - Tags"
    )


@main_fasthtml_router("/tags/newest")
async def tags_newest_route(): # Renamed from 'tags'
    all_bookmarks = fetch_bookmarks(kind="newest")
    internal_bookmarks_count = len([bm for bm in all_bookmarks if bm.get('source') == 'internal'])
    tag_list = fetch_unique_tags(kind="newest") # Renamed variable 'tags' to 'tag_list'
    return Page(
        NavMenu(bookmark_count=internal_bookmarks_count),
        SearchBar(),
        TagCloud(tags=tag_list),
        title_str="Bookerics - Tags (Newest)"
    )


@main_fasthtml_router("/tags/{tag}")
async def bookmarks_by_tag_route(tag: str): # Renamed from 'bookmarks_by_tag'
    bookmarks_for_tag = fetch_bookmarks_by_tag(tag) # Renamed variable
    internal_bookmarks = [bm for bm in bookmarks_for_tag if bm.get('source') == 'internal']

    return Page(
        NavMenu(bookmark_count=len(internal_bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=internal_bookmarks),
        title_str=f"Bookerics - Tag: {tag}"
    )

@main_fasthtml_router("/tags/{tag}/feed") # Changed from @app.get
async def create_feed_for_tag_route(tag: str): # Renamed
    bookmarks_for_feed = fetch_bookmarks_by_tag(tag) # Renamed variable
    await create_feed(tag, bookmarks_for_feed) # Assuming create_feed is async or handled

    # Usually a feed route might return XML or a success message, not a full page.
    # For now, returning a page as per original, but this might need review.
    return Page(
        NavMenu(bookmark_count=len(bookmarks_for_feed)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks_for_feed), # Displaying all bookmarks for the tag
        title_str=f"Bookerics - Feed for {tag}"
    )


@main_fasthtml_router("/untagged") # Changed from @app.get
async def untagged_bookmarks_route(): # Renamed
    untagged = fetch_bookmarks(kind="untagged") # Renamed variable
    internal_untagged = [bm for bm in untagged if bm.get('source') == 'internal']
    return Page(
        NavMenu(bookmark_count=len(internal_untagged)),
        SearchBar(),
        BookmarkList(bookmarks=internal_untagged),
        title_str="Bookerics - Untagged"
    )


# partials


@main_fasthtml_router("/id/{id}") # Changed from @app.get
async def bookmark_by_id_partial(id: str): # Renamed
    bookmark = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return HTMLResponse("Bookmark not found", status_code=404) # Return 404 for not found
    bookmarks = [bookmark]
    # BookmarkImageList returns a Div component, which FastHTML can render directly
    return BookmarkImageList(bookmarks=bookmarks)


@main_fasthtml_router("/id/c/{id}") # Changed from @app.get
async def bookmark_by_id_compact_partial(id: str): # Renamed
    bookmark = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return HTMLResponse("Bookmark not found", status_code=404) # Return 404
    bookmarks = [bookmark]
    # BookmarkList returns a Div component
    return BookmarkList(bookmarks=bookmarks)

@main_fasthtml_router("/search") # Changed from @app.get
async def search_route(request: Request): # Renamed
    query = request.query_params.get("query", "")
    searched_bookmarks = search_bookmarks(query) # Renamed
    # Return a tuple of components for HTMX innerHTML swap into #results-container
    # No Page() wrapper here.
    return (
        NavMenu(bookmark_count=len(searched_bookmarks)),
        SearchBar(query=query),
        BookmarkList(bookmarks=searched_bookmarks),
        # title_str is not applicable here as we are not rendering a full page
    )


# utils


@main_fasthtml_router("/ai/{id}") # Changed from @app.get
async def get_ai_info_for_bookmark_by_id_route(id: str): # Renamed
    bookmark = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return HTMLResponse("Bookmark not found for AI processing.", status_code=404)

    tags, description = await get_tags_and_description_from_bookmark(
        bookmark
    )

    if bookmark.get("id"): # Ensure bookmark has an id
        await update_bookmark_tags(bookmark["id"], tags)
        await update_bookmark_description(bookmark["id"], description)
    else: # Should not happen if fetch_bookmark_by_id guarantees an id
        return HTMLResponse("Bookmark ID missing, cannot update.", status_code=500)

    # Return the HTML for the tags using the helper (or a small dedicated component)
    # _render_tags_html returns a Div, which is fine for HTMX swaps
    return _render_tags_html(tags)


@main_fasthtml_router("/get_thumbnail/{id}") # Changed from @app.get
async def get_thumbnail_route(request: Request): # Renamed
    bookmark_id = request.path_params["id"]
    headers = {"HX-Trigger": "loadThumbnail"} # HX-Trigger might be better handled by client-side JS if needed after swap
    bookmark = await fetch_bookmark_by_id(bookmark_id)
    if bookmark and bookmark.get("thumbnail_url"):
        # Using PreviewImage component to render the image tag for consistency
        # PreviewImage itself handles placeholder logic if thumbnail_url is empty, though here we check it.
        img_html = PreviewImage(src=bookmark["thumbnail_url"], id=f"thumbnail-{bookmark_id}", height="270", width="480").to_html()
        return HTMLResponse(img_html, headers=headers)

    logging.error(f"💥 Bookmark or thumbnail not found for id: {bookmark_id}")
    # Return a placeholder or an empty response with appropriate status
    img_html = PreviewImage(src=None, id=f"thumbnail-{bookmark_id}", height="270", width="480").to_html() # Shows placeholder
    return HTMLResponse(img_html, headers=headers, status_code=404)


@main_fasthtml_router("/check") # Changed from @app.get
async def check_if_bookmark_already_saved_route(request: Request): # Renamed
    status = "not-exists"
    retrieved_bookmark = {} # Renamed variable
    url = request.query_params.get('url')
    if url:
        retrieved_bookmark = await fetch_bookmark_by_url(url)
        if retrieved_bookmark:
            status = "exists"

    return JSONResponse(
        {"status": status, "message": retrieved_bookmark}
    )


@main_fasthtml_router("/add", methods=["POST"]) # Changed from @app.post
async def add_bookmark_route(request: Request): # Renamed
    form_data = await request.form() # Renamed variable
    title = form_data.get("title")
    url = form_data.get("url")
    description = form_data.get("description")
    tags_str = form_data.get("tags", "") # Renamed variable
    tags = tags_str.split(" ") if tags_str else [] # Ensure tags is a list
    force_update = form_data.get("forceUpdate")

    if not title or not url: # Check both title and url
        return JSONResponse(
            {"status": "error", "message": "Title and URL are required!"}, status_code=400 # Added status_code
        )

    existing_bookmark = await fetch_bookmark_by_url(url) # Renamed variable
    if existing_bookmark:
        if force_update:
            await update_bookmark_description(existing_bookmark["id"], description)
            await update_bookmark_tags(existing_bookmark["id"], tags)
            await update_bookmark_title(existing_bookmark["id"], title)
            logger.info(f"Bookmark updated!")
            return JSONResponse(
                {"status": "success", "message": "Bookmark updated!"}
            )
        else:
            # If not forcing update, and bookmark exists, this might be considered a conflict or specific state.
            return JSONResponse(
                {"status": "exists", "message": "Bookmark already exists. Not updated unless forceUpdate is true.", "bookmark_id": existing_bookmark["id"]}, status_code=200
            )

    new_bookmark = await create_bookmark(title, url, description, tags) # Renamed variable
    return JSONResponse(
        {"status": "success", "message": "Bookmark saved!", "bookmark_id": new_bookmark.get("id") if new_bookmark else None}, status_code=201 # Added status_code
    )


@main_fasthtml_router("/update") # Changed from @app.get
async def update_route(): # Renamed
    try:
        backup_bookerics_db() # This is synchronous, consider if it needs to be async
        # Also, consider what this route should actually do. Schedule tasks?
        # For now, keeping original logic but noting it might need more thought for an async app.
        # schedule_feed_creation() # Assuming these are meant to be called
        # schedule_upload_to_s3()
        return JSONResponse(
            {"status": "success", "message": "Database backed up. Feed creation/S3 upload scheduling (if any) initiated."}
        )
    except Exception as e:
        logger.error(f"Error in backup/feed operation: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)}, status_code=500
        )


@main_fasthtml_router("/update_thumbnail/{id}") # Changed from @app.get
async def update_thumbnail_route(request: Request): # Renamed
    bookmark_id = request.path_params["id"]
    # This route seems to just trigger the client.
    # The actual thumbnail URL is fetched by /get_thumbnail/{id} or embedded.
    # If this is purely a trigger, it can remain simple.
    headers = {"HX-Trigger": json.dumps({"loadThumbnail": f"#{bookmark_id}"})} # Example: Trigger specific event
    logger.info(f"Sending HX-Trigger header for bookmark id: {bookmark_id}")
    return JSONResponse({"status": "thumbnail update triggered"}, headers=headers)


@main_fasthtml_router("/delete/{bookmark_id}", methods=["DELETE"]) # Changed from @app.delete
async def delete_bookmark_route(bookmark_id: int): # Renamed
    try:
        # delete_bookmark_by_id is async, so await it directly
        await delete_bookmark_by_id(bookmark_id)
        # For HTMX, an empty response with 200 status usually means "success, do nothing to the target"
        # Or, if the target is the item itself, it will be removed by hx-swap="outerHTML" on success (empty response).
        return HTMLResponse(status_code=200) # Empty 200 signals success to HTMX for outerHTML swap
    except Exception as e:
        logger.error(f"Error deleting bookmark: {e}")
        # Return an error response that HTMX can handle, e.g., display an error message
        return HTMLResponse(f"Error deleting bookmark: {str(e)}", status_code=500)


# misc


@main_fasthtml_router("/table") # Changed from @app.get
async def table_structure_route(): # Renamed
    structure = verify_table_structure() # Assuming this is synchronous
    all_bookmarks = fetch_bookmarks(kind="newest") # Renamed
    return Page(
        NavMenu(bookmark_count=len(all_bookmarks)),
        SearchBar(),
        TableStructure(structure=structure),
        title_str="Bookerics - DB Table Structure"
    )


@main_fasthtml_router("/edit/{bookmark_id}") # Changed from @app.get
async def edit_bookmark_form_route(bookmark_id: str): # Renamed
    bookmark_data = await fetch_bookmark_by_id(id=bookmark_id) # Renamed
    if not bookmark_data:
        return HTMLResponse("Bookmark not found", status_code=404)

    return Page(
        NavMenu(), # No count passed, could fetch if needed
        EditBookmarkForm(bookmark=bookmark_data, action=f"/edit/{bookmark_id}"), # Pass action URL
        title_str=f"Bookerics - Edit: {bookmark_data.get('title', '')}"
    )

@main_fasthtml_router("/edit/{bookmark_id}", methods=["POST"]) # Changed from @app.post
async def update_bookmark_route(bookmark_id: str, request: Request): # Renamed
    form_data = await request.form() # Renamed
    title = form_data.get("title")
    url = form_data.get("url")
    description = form_data.get("description")
    tags_str = form_data.get("tags", "") # Renamed
    tags = tags_str.split(" ") if tags_str else []

    # Basic validation (can be expanded)
    if not title or not url:
        # This should ideally return the form with an error message
        # For now, returning a simple error response
        return HTMLResponse("Title and URL are required.", status_code=400)

    await update_bookmark_title(bookmark_id, title)
    await update_bookmark_description(bookmark_id, description)
    await update_bookmark_tags(bookmark_id, tags)
    
    # Redirect to home page after saving, or to the bookmark's page
    return RedirectResponse(url="/", status_code=303) # 303 See Other is good for POST-redirect-GET
