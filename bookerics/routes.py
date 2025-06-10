import secrets
import logging
import json
from typing import Any, Dict, List, Optional, Union

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from fasthtml.common import to_xml, Html
from .ai import get_tags_and_description_from_bookmark
from .core import Page
from .components import (
    Div,
    NavMenu,
    SearchBar,
    BookmarkList,
    BookmarkImageList,
    TagCloud,
    TableStructure,
    EditBookmarkForm,
    _render_tags_html,
    PreviewImage,
    AnyComponent,
)
from .database import (
    backup_bookerics_db,
    create_bookmark,
    create_feed,
    delete_bookmark_by_id,
    fetch_bookmark_by_id,
    fetch_bookmark_by_url,
    fetch_bookmarks,
    fetch_bookmarks_all,
    fetch_bookmarks_by_tag,
    fetch_unique_tags,
    search_bookmarks,
    update_bookmark_description,
    update_bookmark_tags,
    update_bookmark_title,
    verify_table_structure,
    Bookmark,
)
from .main import rt as main_fasthtml_router
from .utils import logger

# Alias for consistency with existing code
FastHTMLResponse = HTMLResponse

# main routes

@main_fasthtml_router("/")
async def index():
    print("🏠 INDEX ROUTE: Loading first page of bookmarks")
    bookmarks: List[Bookmark] = fetch_bookmarks(kind="newest", page=1, per_page=50)
    all_bookmarks: List[Bookmark] = fetch_bookmarks_all(kind="newest")  # For count
    print(f"🏠 INDEX ROUTE: Loaded {len(bookmarks)} bookmarks from page 1, total: {len(all_bookmarks)}")
    
    # Add infinite scroll trigger to the last bookmark if we have bookmarks
    if bookmarks:
        # Add HTMX attributes to the last bookmark for infinite scroll
        last_bookmark = bookmarks[-1]
        last_bookmark['is_last'] = True
        last_bookmark['next_page'] = 2
        last_bookmark['kind'] = "newest"
    
    # Pass components as children to Page
    return Page(
        NavMenu(bookmark_count=len(all_bookmarks), active="newest"),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks)
    )

@main_fasthtml_router("/bookmarks")
async def bookmarks_page(request: Request) -> HTMLResponse:
    """HTMX endpoint for infinite scroll pagination"""
    page: int = int(request.query_params.get("page", 2))
    kind: str = request.query_params.get("kind", "newest") or "newest"
    
    print(f"📄 BOOKMARKS_PAGE: Loading page {page} for kind {kind}")
    bookmarks: List[Bookmark] = fetch_bookmarks(kind=kind, page=page, per_page=50)
    print(f"📄 BOOKMARKS_PAGE: Loaded {len(bookmarks)} bookmarks for page {page}")
    
    # If no bookmarks, return empty response
    if not bookmarks:
        print(f"📄 BOOKMARKS_PAGE: No more bookmarks found for page {page}")
        return HTMLResponse("", status_code=200)
    
    # Add infinite scroll trigger to the last bookmark
    last_bookmark = bookmarks[-1]
    last_bookmark['is_last'] = True
    last_bookmark['next_page'] = page + 1
    last_bookmark['kind'] = kind
    
    # Create individual bookmark HTML elements and join them
    from bookerics.components import _render_bookmark_html
    bookmark_elements = [_render_bookmark_html(bm, is_image_list=False) for bm in bookmarks]
    
    # Convert to HTML strings and join them
    html_parts: List[str] = [to_xml(element) for element in bookmark_elements]
    combined_html: str = "\n".join(html_parts)
    
    print(f"📄 BOOKMARKS_PAGE: Returning {len(bookmark_elements)} bookmark elements as HTML")
    return HTMLResponse(combined_html, status_code=200)


@main_fasthtml_router("/oldest")
async def oldest():
    print("📅 OLDEST ROUTE: Loading first page of oldest bookmarks")
    bookmarks: List[Bookmark] = fetch_bookmarks(kind="oldest", page=1, per_page=50)
    all_bookmarks: List[Bookmark] = fetch_bookmarks_all(kind="oldest")  # For count
    print(f"📅 OLDEST ROUTE: Loaded {len(bookmarks)} bookmarks from page 1, total: {len(all_bookmarks)}")
    
    # Add infinite scroll trigger to the last bookmark if we have bookmarks
    if bookmarks:
        last_bookmark = bookmarks[-1]
        last_bookmark['is_last'] = True
        last_bookmark['next_page'] = 2
        last_bookmark['kind'] = "oldest"
    
    return Page(
        NavMenu(bookmark_count=len(all_bookmarks), active="oldest"),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks)
    )


@main_fasthtml_router("/random")
async def random_bookmark():
    bookmarks: List[Bookmark] = fetch_bookmarks_all(kind="newest")
    bookmark_count: int = len(bookmarks)
    if not bookmarks:
        return Page(NavMenu(bookmark_count=0, active="random"), SearchBar(), "No bookmarks available to choose from.")

    selected_bookmarks: List[Bookmark] = [secrets.choice(bookmarks)]
    return Page(
        NavMenu(bookmark_count=bookmark_count, active="random"),
        SearchBar(),
        BookmarkImageList(bookmarks=selected_bookmarks)
    )


@main_fasthtml_router("/tags")
async def tags_route():
    all_bookmarks: List[Bookmark] = fetch_bookmarks_all(kind="newest")
    internal_bookmarks_count: int = len([bm for bm in all_bookmarks if bm.get('source') == 'internal'])
    tag_list: List[Dict[str, Any]] = fetch_unique_tags(kind="frequency")
    return Page(
        NavMenu(bookmark_count=internal_bookmarks_count, active="tags"),
        SearchBar(),
        TagCloud(tags=tag_list)
    )


@main_fasthtml_router("/tags/newest")
async def tags_newest_route():
    all_bookmarks: List[Bookmark] = fetch_bookmarks_all(kind="newest")
    internal_bookmarks_count: int = len([bm for bm in all_bookmarks if bm.get('source') == 'internal'])
    tag_list: List[Dict[str, Any]] = fetch_unique_tags(kind="newest")
    return Page(
        NavMenu(bookmark_count=internal_bookmarks_count),
        SearchBar(),
        TagCloud(tags=tag_list),
        title_str="Bookerics - Tags (Newest)"
    )


@main_fasthtml_router("/tags/{tag}")
async def bookmarks_by_tag_route(tag: str):
    bookmarks_for_tag: List[Bookmark] = fetch_bookmarks_by_tag(tag)
    internal_bookmarks: List[Bookmark] = [bm for bm in bookmarks_for_tag if bm.get('source') == 'internal']

    return Page(
        NavMenu(bookmark_count=len(internal_bookmarks)),
        SearchBar(),
        BookmarkList(bookmarks=internal_bookmarks),
        title_str=f"Bookerics - Tag: {tag}"
    )

@main_fasthtml_router("/tags/{tag}/feed")
async def create_feed_for_tag_route(tag: str):
    bookmarks_for_feed: List[Bookmark] = fetch_bookmarks_by_tag(tag)
    await create_feed(tag, bookmarks_for_feed)

    # Usually a feed route might return XML or a success message, not a full page.
    # For now, returning a page as per original, but this might need review.
    return Page(
        NavMenu(bookmark_count=len(bookmarks_for_feed)),
        SearchBar(),
        BookmarkList(bookmarks=bookmarks_for_feed),
        title_str=f"Bookerics - Feed for {tag}"
    )


@main_fasthtml_router("/untagged")
async def untagged_bookmarks_route():
    print("🏷️ UNTAGGED ROUTE: Loading first page of untagged bookmarks")
    untagged: List[Bookmark] = fetch_bookmarks(kind="untagged", page=1, per_page=50)
    all_untagged: List[Bookmark] = fetch_bookmarks_all(kind="untagged")
    internal_untagged: List[Bookmark] = [bm for bm in untagged if bm.get('source') == 'internal']
    all_internal_untagged: List[Bookmark] = [bm for bm in all_untagged if bm.get('source') == 'internal']
    print(f"🏷️ UNTAGGED ROUTE: Loaded {len(internal_untagged)} bookmarks from page 1, total: {len(all_internal_untagged)}")
    
    # Add infinite scroll trigger to the last bookmark if we have bookmarks
    if internal_untagged:
        last_bookmark = internal_untagged[-1]
        last_bookmark['is_last'] = True
        last_bookmark['next_page'] = 2
        last_bookmark['kind'] = "untagged"
    
    return Page(
        NavMenu(bookmark_count=len(all_internal_untagged), active="untagged"),
        SearchBar(),
        BookmarkList(bookmarks=internal_untagged)
    )


# partials

@main_fasthtml_router("/id/{id}")
async def bookmark_by_id_partial(id: str) -> Union[AnyComponent, HTMLResponse]:
    bookmark: Optional[Bookmark] = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return HTMLResponse("Bookmark not found", status_code=404)
    bookmarks: List[Bookmark] = [bookmark]
    # BookmarkImageList returns a Div component, which FastHTML can render directly
    return BookmarkImageList(bookmarks=bookmarks)


@main_fasthtml_router("/id/c/{id}") # Changed from @app.get
async def bookmark_by_id_compact_partial(id: str) -> Union[AnyComponent, HTMLResponse]:
    bookmark: Optional[Bookmark] = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return HTMLResponse("Bookmark not found", status_code=404) # Return 404
    bookmarks: List[Bookmark] = [bookmark]
    # BookmarkList returns a Div component
    return BookmarkList(bookmarks=bookmarks)

@main_fasthtml_router("/search") # Changed from @app.get
async def search_route(request: Request) -> HTMLResponse:
    query: str = request.query_params.get("query", "")
    searched_bookmarks: List[Bookmark] = search_bookmarks(query)
    # Return components wrapped in a Div for HTMX innerHTML swap into #results-container
    components = Div(
        NavMenu(bookmark_count=len(searched_bookmarks)),
        SearchBar(query=query),
        BookmarkList(bookmarks=searched_bookmarks)
    )
    return HTMLResponse(to_xml(components))


# utils

@main_fasthtml_router("/ai/{id}")
async def get_ai_info_for_bookmark_by_id_route(id: str) -> FastHTMLResponse:
    bookmark: Optional[Bookmark] = await fetch_bookmark_by_id(id=id)
    if not bookmark:
        return FastHTMLResponse("Bookmark not found for AI processing.", status_code=404)

    try:
        ai_tags, ai_description = await get_tags_and_description_from_bookmark(bookmark)
        if ai_tags:
            await update_bookmark_tags(id=id, tags=ai_tags)
        if ai_description:
            await update_bookmark_description(id=id, description=ai_description)

        updated_bookmark = await fetch_bookmark_by_id(id=id)
        if not updated_bookmark:
            return HTMLResponse("Bookmark not found after update", status_code=404)

        return HTMLResponse(
            to_xml(_render_tags_html(updated_bookmark.get("tags", []))),
            headers={"HX-Trigger": json.dumps({"showToast": "AI update complete."})},
        )
    except Exception as e:
        logger.error(f"Error getting AI info for bookmark {id}: {e}")
        return FastHTMLResponse(f"Error: {e}", status_code=500)


@main_fasthtml_router("/get_thumbnail/{id}")
async def get_thumbnail_route(request: Request) -> HTMLResponse:
    bookmark_id: str = request.path_params["id"]
    headers = {"HX-Trigger": "loadThumbnail"}
    bookmark: Optional[Bookmark] = await fetch_bookmark_by_id(bookmark_id)
    if bookmark and bookmark.get("thumbnail_url"):
        # Using PreviewImage component to render the image tag for consistency
        # PreviewImage itself handles placeholder logic if thumbnail_url is empty, though here we check it.
        img_component = PreviewImage(src=bookmark["thumbnail_url"], id=f"thumbnail-{bookmark_id}")
        img_html = to_xml(img_component)
        return HTMLResponse(img_html, headers=headers)

    logging.error(f"💥 Bookmark or thumbnail not found for id: {bookmark_id}")
    # Return a placeholder or an empty response with appropriate status
    img_component = PreviewImage(src=None, id=f"thumbnail-{bookmark_id}") # Shows placeholder
    img_html = to_xml(img_component)
    return HTMLResponse(img_html, headers=headers, status_code=404)


@main_fasthtml_router("/check")
async def check_if_bookmark_already_saved_route(request: Request) -> HTMLResponse:
    url: Union[str, None] = request.query_params.get("url", "")
    if not url:
        return HTMLResponse("URL is required.", status_code=400)

    bookmark: Optional[Bookmark] = await fetch_bookmark_by_url(url)
    if bookmark:
        return HTMLResponse("Bookmark exists.", status_code=200)
    else:
        return HTMLResponse("Bookmark does not exist.", status_code=404)


@main_fasthtml_router("/add", methods=["POST"])
async def add_bookmark_route(request: Request) -> HTMLResponse:
    form_data = await request.form()
    title: str = str(form_data.get("title", ""))
    url: str = str(form_data.get("url", ""))
    description: str = str(form_data.get("description", ""))
    tags_str: str = str(form_data.get("tags", ""))
    tags: List[str] = tags_str.split(" ") if tags_str else []
    force_update = form_data.get("forceUpdate")
    source: str = form_data.get("source", "internal")

    if not url or not title:
        return HTMLResponse("URL and Title are required.", status_code=400)

    existing_bookmark = await fetch_bookmark_by_url(url)
    if existing_bookmark:
        if force_update:
            await update_bookmark_description(existing_bookmark["id"], description)
            await update_bookmark_tags(existing_bookmark["id"], tags)
            await update_bookmark_title(existing_bookmark["id"], title)
            logger.info("Bookmark updated!")
            return HTMLResponse(
                "Bookmark updated successfully.", status_code=200
            )
        else:
            # If not forcing update, and bookmark exists, this might be considered a conflict or specific state.
            return HTMLResponse(
                "Bookmark already exists. Not updated unless forceUpdate is true.", status_code=409
            )

    bookmark_id: Optional[int] = await create_bookmark(
        url=url,
        title=title,
        description=description,
        tags=tags,
        source=source,
    )
    if not bookmark_id:
        return HTMLResponse("Failed to create bookmark.", status_code=500)

    new_bookmark = await fetch_bookmark_by_id(str(bookmark_id))
    if not new_bookmark:
        return HTMLResponse("Failed to fetch new bookmark.", status_code=500)

    if not tags:
        try:
            ai_tags, ai_description = await get_tags_and_description_from_bookmark(
                new_bookmark
            )
            if ai_tags:
                await update_bookmark_tags(id=str(bookmark_id), tags=ai_tags)
            if ai_description:
                await update_bookmark_description(
                    id=str(bookmark_id), description=ai_description
                )
        except Exception as e:
            logger.error(f"Error getting AI info for new bookmark {bookmark_id}: {e}")

    headers = {
        "HX-Trigger": json.dumps({"showToast": f"New bookmark added: {title}"})
    }
    return HTMLResponse("Bookmark added successfully.", headers=headers)


@main_fasthtml_router("/update") # Changed from @app.get
async def update_route():
    try:
        backup_bookerics_db()
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
async def update_thumbnail_route(request: Request) -> FastHTMLResponse:
    bookmark_id: str = request.path_params["id"]
    # The actual thumbnail URL is fetched by /get_thumbnail/{id} or embedded.
    headers = {"HX-Trigger": json.dumps({"loadThumbnail": f"#{bookmark_id}"})}
    logger.info(f"Sending HX-Trigger header for bookmark id: {bookmark_id}")
    return JSONResponse({"status": "thumbnail update triggered"}, headers=headers)


@main_fasthtml_router("/delete/{bookmark_id}", methods=["DELETE"])
async def delete_bookmark_route(bookmark_id: int, request: Request) -> FastHTMLResponse:
    try:
        print(f"🔥 DELETE_BOOKMARK_ROUTE CALLED: bookmark_id={bookmark_id}")
        
        # delete_bookmark_by_id is async, so await it directly
        await delete_bookmark_by_id(bookmark_id)
        print(f"🔥 DELETE_BOOKMARK_ROUTE: Successfully deleted bookmark {bookmark_id}")
        
        # Check if the request came from the random page by checking the Referer header
        referer = request.headers.get("referer", "")
        print(f"🔥 DELETE_BOOKMARK_ROUTE: Referer header: {referer}")
        
        if "/random" in referer:
            print("🔥 DELETE_BOOKMARK_ROUTE: Request came from random page, returning new random bookmark")
            # If deleting from the random page, return a new random bookmark
            bookmarks = fetch_bookmarks_all(kind="newest")
            if bookmarks: # Make sure we have bookmarks left
                selected_bookmarks = [secrets.choice(bookmarks)]
                print(f"🔥 DELETE_BOOKMARK_ROUTE: Selected new random bookmark: {selected_bookmarks[0].get('title', 'N/A')}")
                # Convert the BookmarkImageList component to HTML for HTMX swap
                component = BookmarkImageList(bookmarks=selected_bookmarks)
                return HTMLResponse(to_xml(component))
            else:
                print("🔥 DELETE_BOOKMARK_ROUTE: No bookmarks left to show")
                # No bookmarks left
                return HTMLResponse("No more bookmarks available to choose from.", status_code=200)
        
        # For HTMX, an empty response with 200 status usually means "success, do nothing to the target"
        # Or, if the target is the item itself, it will be removed by hx-swap="outerHTML" on success (empty response).
        print("🔥 DELETE_BOOKMARK_ROUTE: Normal delete, returning empty response")
        return HTMLResponse(status_code=200)
    except Exception as e:
        logger.error(f"Error deleting bookmark: {e}")
        print(f"🔥 DELETE_BOOKMARK_ROUTE: Exception occurred: {str(e)}")
        return HTMLResponse(f"Error deleting bookmark: {str(e)}", status_code=500)


# misc

@main_fasthtml_router("/table")
async def table_structure_route():
    structure = verify_table_structure()
    all_bookmarks = fetch_bookmarks_all(kind="newest")
    return Page(
        NavMenu(bookmark_count=len(all_bookmarks)),
        SearchBar(),
        TableStructure(structure=structure),
        title_str="Bookerics - DB Table Structure"
    )


@main_fasthtml_router("/edit/{bookmark_id}")
async def edit_bookmark_form_route(bookmark_id: str) -> Union[Html, HTMLResponse]:
    bookmark_data = await fetch_bookmark_by_id(id=bookmark_id)
    if not bookmark_data:
        return HTMLResponse("Bookmark not found", status_code=404)

    return Page(
        NavMenu(), # No count passed, could fetch if needed
        EditBookmarkForm(bookmark=bookmark_data, action=f"/edit/{bookmark_id}")
    )

@main_fasthtml_router("/edit/{bookmark_id}/modal") # Modal version for HTMX
async def edit_bookmark_modal_route(bookmark_id: str) -> Union[AnyComponent, Div, HTMLResponse]:
    bookmark_data = await fetch_bookmark_by_id(id=bookmark_id)
    if not bookmark_data:
        return HTMLResponse("Bookmark not found", status_code=404)

    # Import Button and H2 for the modal structure
    from fasthtml.common import Button, H2
    
    # Return complete modal structure using our CSS
    return Div(
        Div(
            Div(
                H2(f"Edit {bookmark_data.get('title', 'Bookmark')}"),
                Button("×", cls="modal-close", onclick="closeModal()"),
                cls="modal-header"
            ),
            Div(
                EditBookmarkForm(
                    bookmark=bookmark_data,
                    action=f"/edit-test/{bookmark_id}",
                    hx_post=f"/edit-test/{bookmark_id}",
                    hx_target=f"#bmb-{bookmark_id}",
                    hx_swap="outerHTML",
                ),
                cls="modal-body"
            ),
            cls="modal-content",
            onclick="event.stopPropagation()"
        ),
        cls="modal-backdrop",
        onclick="closeModal()"
    )

@main_fasthtml_router("/edit-test/{bookmark_id}", methods=["POST"])
async def update_bookmark_route(bookmark_id: str, request: Request) -> FastHTMLResponse:
    print(f"🔥 UPDATE_BOOKMARK_ROUTE CALLED: bookmark_id={bookmark_id}")
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info(f"UPDATE_BOOKMARK_ROUTE: Starting update for bookmark {bookmark_id}")
    
    form_data = await request.form()
    print(f"🔥 FORM DATA: {dict(form_data)}")
    logging.info(f"UPDATE_BOOKMARK_ROUTE: Form data received: {dict(form_data)}")
    
    title: str = str(form_data.get("title", ""))
    url: str = str(form_data.get("url", ""))
    description: str = str(form_data.get("description", ""))
    tags_str: str = str(form_data.get("tags", ""))
    tags: List[str] = tags_str.split(" ") if tags_str else []
    
    logging.info(f"UPDATE_BOOKMARK_ROUTE: Parsed data - title: {title}, url: {url}, description: {description}, tags: {tags}")

    # Basic validation (can be expanded)
    if not title or not url:
        logging.error(f"UPDATE_BOOKMARK_ROUTE: Validation failed - title: {title}, url: {url}")
        # This should ideally return the form with an error message
        # For now, returning a simple error response
        return HTMLResponse("Title and URL are required.", status_code=400)

    try:
        bookmark_id_int = int(bookmark_id)
        logging.info(f"UPDATE_BOOKMARK_ROUTE: Starting database updates for bookmark {bookmark_id_int}")
        
        await update_bookmark_title(bookmark_id_int, title)
        await update_bookmark_description(bookmark_id_int, description)
        await update_bookmark_tags(bookmark_id_int, tags)
        
        logging.info(f"UPDATE_BOOKMARK_ROUTE: Database updates completed for bookmark {bookmark_id_int}")
        
        updated_bookmark = await fetch_bookmark_by_id(id=bookmark_id)
        logging.info(f"UPDATE_BOOKMARK_ROUTE: Fetched updated bookmark: {updated_bookmark is not None}")
        
        if not updated_bookmark:
            logging.warning(f"UPDATE_BOOKMARK_ROUTE: Updated bookmark not found for id {bookmark_id}")
            return HTMLResponse(
                status_code=200, headers={"HX-Reswap": "none", "HX-Trigger": "closeModal"}
            )

        logging.info("UPDATE_BOOKMARK_ROUTE: Rendering bookmark HTML")
        # Use the full bookmark rendering function to maintain all interactive elements
        from bookerics.components import _render_bookmark_html
        component = _render_bookmark_html(updated_bookmark, is_image_list=False)
        
        print(f"🔥 COMPONENT TYPE: {type(component)}")
        print(f"🔥 COMPONENT: {component}")
        print(f"🔥 HAS to_html: {hasattr(component, 'to_html')}")
        print(f"🔥 HAS __html__: {hasattr(component, '__html__')}")
        print(f"🔥 AVAILABLE METHODS: {[m for m in dir(component) if not m.startswith('_')]}")
        if hasattr(component, 'to_html'):
            print(f"🔥 to_html TYPE: {type(component.to_html)}")
        
        # Set headers properly following the pattern from other routes
        headers = {"HX-Trigger": "closeModal"}
        logging.info(f"UPDATE_BOOKMARK_ROUTE: Setting HX-Trigger header for bookmark id: {bookmark_id}")
        logging.info(f"UPDATE_BOOKMARK_ROUTE: Headers being set: {headers}")
        
        # Convert the component to HTML using fasthtml's to_xml function
        print("🔥 CONVERTING: Component to HTML using to_xml")
        html_content = to_xml(component)
        print(f"🔥 CONVERSION SUCCESS: {html_content[:100]}...")
        response = HTMLResponse(html_content, headers=headers)
        logging.info("UPDATE_BOOKMARK_ROUTE: Response created using to_xml(), returning to client")
        return response
        
    except Exception as e:
        logging.error(f"UPDATE_BOOKMARK_ROUTE: Exception occurred: {str(e)}")
        logging.error(f"UPDATE_BOOKMARK_ROUTE: Exception type: {type(e).__name__}")
        import traceback
        logging.error(f"UPDATE_BOOKMARK_ROUTE: Traceback: {traceback.format_exc()}")
        return HTMLResponse(f"Error updating bookmark: {str(e)}", status_code=500)

# Handle Chrome DevTools requests to prevent 404 logs
@main_fasthtml_router("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_handler() -> JSONResponse:
    return JSONResponse({}, status_code=404)

# Close modal route - returns empty content to clear the modal
@main_fasthtml_router("/close-modal")
async def close_modal() -> FastHTMLResponse:
    return FastHTMLResponse("", status_code=200)
