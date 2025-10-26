import json
import httpx
from typing import Any, Union

from fasthtml.common import Div, A, Input, P, Img, Pre, Code, Button, Form, Label, Textarea, Span
# For attributes, use dicts e.g. {'hx_get': '/search'}

from .constants import GIPHY_API_KEY
from .database import BOOKMARK_NAME, Bookmark


AnyComponent = Any


def NavMenu(bookmark_count: Union[int, bool] = False, active: str = "") -> AnyComponent:
    if bookmark_count is not False and isinstance(bookmark_count, int):
        bookericz = BOOKMARK_NAME if bookmark_count == 1 else f"{BOOKMARK_NAME}s"
        bookmark_result = f"{bookmark_count:,} {bookericz}"
        link_display = HiddenLink(
            bookmark_result, to="/update", title="Backup / refresh feed on S3 now"
        )
    else:
        link_display = f"{BOOKMARK_NAME}s" # type: ignore

    # Helper function to add active class
    def nav_link_class(link_name):
        return "active" if active == link_name else ""
    
    return Div(
        link_display,
        Div(
            A("newest", href="/", cls=nav_link_class("newest")),
            A("oldest", href="/oldest", cls=nav_link_class("oldest")),
            A("random", href="/random", cls=nav_link_class("random")),
            A("untagged", href="/untagged", cls=nav_link_class("untagged")),
            Span(" | ", cls="nav-separator"),
            A("tags", href="#", id="tags-link", cls=nav_link_class("tags")),
            Span(" | ", cls="nav-separator"),
            A("🌙", href="#", id="theme-toggle", cls="theme-toggle-btn", title="Toggle dark/light theme (Cmd+Shift+D)"),
        ),
        cls="nav-menu justify-space-between",
    )


def SearchBar(query: str = "", **attrs: Any) -> AnyComponent:
    return Input(
        type="search",
        placeholder=f"Search {BOOKMARK_NAME}s",
        hx_get="/search",
        hx_trigger="input changed delay:500ms",
        hx_target="#results-container",
        hx_swap="innerHTML",
        name="query",
        id="query",
        value=query,
        cls="search-bar-input",
        **attrs
    )


def HiddenLink(*children: AnyComponent, to: str, title: str, **attrs: Any) -> AnyComponent:
    return A(
        *children,
        href=to,
        title=title,
        cls="hidden-link",
        **attrs
    )


def BookericLink(*children: AnyComponent, to: str, **attrs: Any) -> AnyComponent:
    return A(
        *children,
        href=to,
        target="_blank",
        cls="bookeric-link external",
        **attrs
    )

def TableStructure(structure: Union[list, None] = None, **attrs: Any) -> AnyComponent:
    if structure is None:
        structure = []

    formatted_structure = f"[\n {',\n '.join([str(col) for col in structure])}\n]"
    # CSS class "table-structure-wrapper" handles centering.
    # <pre><code>...</code></pre> is the equivalent of CodeBlock.
    return Div(
        Pre(Code(formatted_structure)),
        cls="table-structure-wrapper",
        **attrs
    )


def TagCloud(tags: Union[list, None] = None, **attrs: Any) -> AnyComponent:
    if tags is None:
        tags = []
    # CSS class "tag-cloud" handles flex layout.
    # CSS classes "btn tag info" are for styling individual tags.
    return Div(
        *[
            A(
                tag_item["tag"] if isinstance(tag_item, dict) else tag_item,
                href=f"/tags/{tag_item['tag'] if isinstance(tag_item, dict) else tag_item}",
                cls="btn tag info"
            ) # Was ButtonLink
            for tag_item in tags
        ],
        cls="tag-cloud",
        **attrs
    )

def _get_random_giphy_url() -> str:
    _url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=waiting&rating=r"
    try:
        r = httpx.get(_url, timeout=5)
        r.raise_for_status()
        giphy_url = r.json()["data"]["images"]["original"]["url"]
        return giphy_url
    except httpx.RequestError as e:
        print(f"Error fetching Giphy URL: {e}")
        return "/static/images/placeholder.gif"
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing Giphy response: {e}")
        return "/static/images/placeholder.gif"

def PreviewImage(src: Union[str, None] = None, **attrs: Any) -> AnyComponent:
    placeholder_src = ""
    if not src:
        placeholder_src = _get_random_giphy_url()
        src = placeholder_src # Use the random Giphy URL as src
        attrs['data_placeholder'] = "true"

    # Ensure all necessary attributes from original are passed or handled
    # Original attrs: src, height, width, id, hx_get, hx_target, hx_trigger, hx_swap
    return Img(src=src, cls="image-placeholder", **attrs)


def ImageSwitcher(*children: AnyComponent, **attrs: Any) -> AnyComponent:
    return Div(*children, cls="image-switcher", **attrs)


def BookmarkBox(*children: AnyComponent, **attrs: Any) -> AnyComponent:
    # All styling and structure is handled by CSS via the 'bookmark-box' class and its modifiers.
    # Child elements like P, A, Div will be passed in *children.
    # Modifier classes like 'small', 'large', 'transparent', 'invert' should be part of attrs['cls']
    # e.g., BookmarkBox(P("Hello"), cls="bookmark-box small transparent")

    # We ensure 'bookmark-box' is always part of the class list.
    current_classes = attrs.pop('cls', "")
    final_classes = f"bookmark-box {current_classes}".strip()

    return Div(*children, cls=final_classes, **attrs)


def HTMXDeleteButton(*children: AnyComponent, to: str = "#", hx_target: str, hx_swap: str, hx_delete: str, cls: str = "", **attrs: Any):
    # data-confirmed is a state managed by JS, but can be set initially
    final_cls = f"btn delete-btn {cls}".strip()
    # Store the delete URL in data attribute and remove hx_delete initially
    # JS will add hx_delete back when confirmed
    return A(*children, href=to, hx_target=hx_target, hx_swap=hx_swap,
             **{"data-delete-url": hx_delete, "data-confirmed": "false"},  # Use dict for hyphenated attributes
             cls=final_cls, **attrs)


def ToggleImagePreviewButton(*children: AnyComponent, hx_get: str, hx_target: str, hx_swap: str, cls: str = "", **attrs: Any):
    final_cls = f"btn toggle-image-preview-btn {cls}".strip()
    return A(*children, hx_get=hx_get, hx_target=hx_target, hx_swap=hx_swap, cls=final_cls, **attrs) # type: ignore


def GetTagsForBookmarkButton(*children: AnyComponent, to: str = "#", hx_swap: str, hx_target: str, hx_get: str, cls: str = "", **attrs: Any):
    final_cls = f"btn {cls}".strip() # General btn class, specific styling via parent or further classes
    return A(*children, href=to, hx_swap=hx_swap, hx_target=hx_target, hx_get=hx_get, cls=final_cls, **attrs) # type: ignore


def UpdateBookmarkButton(text: str, hx_get: str, cls: str = "", hx_target: str = "", **attrs: Any):
    final_cls = f"btn update-btn {cls}".strip()
    attrs_dict = {"hx_get": hx_get, "cls": final_cls}
    if hx_target:
        attrs_dict["hx_target"] = hx_target
    attrs_dict.update(attrs)
    return A(text, **attrs_dict) # type: ignore


def _render_tags_html(tags: Union[list[str], str]) -> AnyComponent:
    """Renders a list of tags as A elements within a Div."""
    if isinstance(tags, str):
        # Handle case where tags might be passed as a string
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = tags.split() if tags else []
    
    if not tags:
        return Div(cls="tags-container")

    return Div(*[A(tag_name, href=f"/tags/{tag_name}", cls="btn tag info") for tag_name in tags], cls="tags-container")

def _render_created_at_html(created_at: Union[str, None]) -> AnyComponent:
    if created_at:
        # Use HTML5 time element with datetime attribute for JavaScript formatting
        from fasthtml.common import Time
        return Div(
            Time(created_at, datetime=created_at, cls="created-at-time"),
            cls="created-at-display"
        )
    return Div("", cls="created-at-display")


def _render_bookmark_html(bookmark: Bookmark, is_image_list: bool = False) -> AnyComponent:
    bookmark_id = bookmark.get("id")
    title = bookmark.get("title", "")
    url = bookmark.get("url", "")
    description = bookmark.get("description", "")
    tags = bookmark.get("tags", [])
    thumbnail_url = bookmark.get("thumbnail_url")
    archive_url = bookmark.get("archive_url")
    created_at = bookmark.get("created_at")
    
    # Check if this is the last bookmark in the list for infinite scroll
    is_last = bookmark.get("is_last", False)
    next_page = bookmark.get("next_page", 2)
    kind = bookmark.get("kind", "newest")

    tags_html = _render_tags_html(tags)
    created_at_html = _render_created_at_html(created_at)

    toggle_btn_target_id = f"bmb-{bookmark_id}"

    # Prepare content list for BookmarkBox
    title_link = BookericLink(title, to=url)
    
    # Add archive link if available
    if archive_url:
        title_content = Div(
            title_link,
            A("🗄️", href=archive_url, target="_blank", cls="archive-link", title="View archived copy"),
            cls="title-with-archive"
        )
        content = [title_content, created_at_html]
    else:
        content = [title_link, created_at_html]

    if is_image_list and thumbnail_url:
        content.append(PreviewImage(src=thumbnail_url, id=f"thumbnail-{bookmark_id}"))

    if description:
        content.append(P(description))

    # Add tags display or 'get tags' button
    tags_container_id = f"tags-{bookmark_id}"
    if tags:
        tags_element = tags_html
    else:
        tags_element = GetTagsForBookmarkButton(
            "Get Tags",
            hx_get=f"/ai/{bookmark_id}",
            hx_target=f"#{tags_container_id}",
            hx_swap="outerHTML",
            cls="btn small",
        )
    content.append(Div(tags_element, id=tags_container_id))


    # Expand/Collapse button
    toggle_btn_text = "➖" if is_image_list else "➕"
    toggle_btn_hx_get = f"/id/c/{bookmark_id}" if is_image_list else f"/id/{bookmark_id}"

    content.append(
        Div(
            ToggleImagePreviewButton(
                toggle_btn_text, # type: ignore
                hx_get=toggle_btn_hx_get, hx_target=f"#{toggle_btn_target_id}", hx_swap="outerHTML"
            ),
            cls="expand-button"
        )
    )

    # Action buttons
    content.append(
        Div(
            UpdateBookmarkButton("✒️", hx_get=f"/edit/{bookmark_id}/modal", hx_target="#modal-container", hx_swap="innerHTML", cls="update-btn"), # type: ignore
            HTMXDeleteButton(
                "🗑️", to="#", hx_target=f"#{toggle_btn_target_id}", hx_swap="outerHTML", # type: ignore
                hx_delete=f"/delete/{bookmark_id}", cls="delete-btn"
            ),
            cls="action-buttons"
        )
    )

    # If this is the last bookmark, add infinite scroll attributes and loading indicator
    box_attrs = {"id": toggle_btn_target_id}
    if is_last:
        # Build the URL for infinite scroll
        query_param = bookmark.get("query", "")
        if kind == "search" and query_param:
            hx_get_url = f"/bookmarks?page={next_page}&kind={kind}&query={query_param}"
        else:
            hx_get_url = f"/bookmarks?page={next_page}&kind={kind}"
        
        box_attrs.update({
            "hx_get": hx_get_url,
            "hx_trigger": "revealed",
            "hx_swap": "afterend",
            "hx_indicator": f"#{toggle_btn_target_id}-loading"
        })
        
        # Add loading indicator after the bookmark box content
        content.append(
            Div(
                "Loading more bookerics...",
                id=f"{toggle_btn_target_id}-loading",
                cls="htmx-indicator loading-indicator",
                style="text-align: center; padding: 1rem; color: #666; font-style: italic;"
            )
        )

    return BookmarkBox(*content, **box_attrs)


def BookmarkList(bookmarks: list[Bookmark], **attrs: Any) -> AnyComponent:
    # Assuming 'bookmarks' is a list of bookmark dictionaries
    # The 'attrs' can be used for top-level Div attributes if needed (e.g. id, class)
    return Div(
        *[_render_bookmark_html(bm, is_image_list=False) for bm in bookmarks],
        cls="bookmark-list-switcher",
        **attrs
    )


def BookmarkImageList(bookmarks: list[Bookmark], **attrs: Any) -> AnyComponent:
    # Relies on PreviewImage's HTMX attributes for lazy loading thumbnails.
    # The update_bookmarks_with_thumbnails can be called in the route handler if needed pre-render.
    return Div(
        *[_render_bookmark_html(bm, is_image_list=True) for bm in bookmarks],
        cls="bookmark-image-list-switcher", # Or use "bookmark-list-switcher" if layout is identical
        **attrs
    )


def EditBookmarkForm(bookmark: Bookmark, **attrs: Any) -> AnyComponent:
    # 'bookmark' is a dictionary containing bookmark data
    # 'attrs' can include form attributes like 'action', 'method' (though method is POST by default here)

    tags_list = bookmark.get("tags", [])
    if isinstance(tags_list, str): # Handle if tags are passed as a JSON string
        try:
            tags_list = json.loads(tags_list)
        except json.JSONDecodeError:
            tags_list = [] # Or split the string, depending on expected format
    tags_str = " ".join(tags_list)

    form_method = attrs.pop('method', "POST")
    form_action = attrs.pop('action', f"/edit/{bookmark.get('id', '')}")

    # If this is for a modal, add HTMX attributes for inline submission
    form_attrs = {
        "method": form_method,
        "action": form_action,
        "cls": "edit-bookmark-form"
    }
    
    # Check if this is a modal form (has hx_target in attrs)
    if attrs.get("hx_target"):
        form_attrs["hx_post"] = form_action
        form_attrs["hx_target"] = attrs.get("hx_target")
        form_attrs["hx_swap"] = attrs.get("hx_swap", "innerHTML")
        # Remove action for HTMX form to prevent standard form submission
        del form_attrs["action"]
    
    form_attrs.update({k: v for k, v in attrs.items() if not k.startswith("hx_")})

    return Form(
        Div(
            Label("Title", for_="title"),
            Input(type="text", name="title", id="title", value=bookmark.get("title", "")),
        ),
        Div(
            Label("URL", for_="url"),
            Input(type="url", name="url", id="url", value=bookmark.get("url", "")),
        ),
        Div(
            Label("Description", for_="description"),
            Textarea(bookmark.get("description", ""), name="description", id="description")
        ),
        Div(
            Label("Tags (space-separated)", for_="tags"),
            Input(type="text", name="tags", id="tags", value=tags_str),
        ),
        Button("Save Changes", type="submit", cls="btn primary small"),
        **form_attrs
    )


def KeyboardShortcutsHelpModal(**attrs: Any) -> AnyComponent:
    """Modal showing all keyboard shortcuts"""
    return Div(
        Div(
            Div(
                Div(
                    "Keyboard Shortcuts",
                    Button("×", cls="modal-close-btn", onclick="closeModal()"),
                    cls="modal-header"
                ),
                Div(
                    Div(
                        "Navigation",
                        Div(
                            Div("J", cls="shortcut-key"),
                            Div("Navigate down to next bookmark", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        Div(
                            Div("K", cls="shortcut-key"),
                            Div("Navigate up to previous bookmark", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        cls="shortcut-section"
                    ),
                    Div(
                        "Actions",
                        Div(
                            Div("V", cls="shortcut-key"),
                            Div("Open bookmark URL in new tab", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        Div(
                            Div("E", cls="shortcut-key"),
                            Div("Edit selected bookmark", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        Div(
                            Div("X", cls="shortcut-key"),
                            Div("Delete selected bookmark (press twice)", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        cls="shortcut-section"
                    ),
                    Div(
                        "Search",
                        Div(
                            Div("Cmd+K", cls="shortcut-key"),
                            Div("Focus search bar", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        Div(
                            Div("Escape", cls="shortcut-key"),
                            Div("Unfocus search bar or close modal", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        cls="shortcut-section"
                    ),
                    Div(
                        "Other",
                        Div(
                            Div("Cmd+Shift+D", cls="shortcut-key"),
                            Div("Toggle dark/light theme", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        Div(
                            Div("?", cls="shortcut-key"),
                            Div("Show this help modal", cls="shortcut-desc"),
                            cls="shortcut-row"
                        ),
                        cls="shortcut-section"
                    ),
                    cls="shortcuts-content"
                ),
                cls="modal-content keyboard-shortcuts-modal"
            ),
            cls="modal-backdrop",
            onclick="closeModal()"
        ),
        cls="modal-container",
        id="modal-container",
        **attrs
    )
