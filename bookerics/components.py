import json # Uncommented
import requests # Uncommented

from fasthtml.common import Div, A, Input, P, Img, Pre, Code, Button, Form, Label, Textarea, Span
# For attributes, use dicts e.g. {'hx_get': '/search'}

from .constants import GIPHY_API_KEY # Keep
from .database import BOOKMARK_NAME # Keep


# class NavMenu(Component[NoChildren, GlobalAttrs]): # Ludic Component
#     @override
#     def render(self) -> Cluster:
def NavMenu(bookmark_count: int | bool = False, active: str = ""): # FastHTML functional component
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
    
    return Div( # Was Cluster
        link_display,
        Div( # Was Cluster
            A("newest", href="/", cls=nav_link_class("newest")), # Was Link
            A("oldest", href="/oldest", cls=nav_link_class("oldest")), # Was Link
            A("random", href="/random", cls=nav_link_class("random")), # Was Link
            A("untagged", href="/untagged", cls=nav_link_class("untagged")), # Was Link
            Span(" | ", cls="nav-separator"), # Pipe separator
            A("tags", href="#", id="tags-link", cls=nav_link_class("tags")), # Moved from separate div
        ),
        cls="nav-menu justify-space-between", # Added nav-menu class for styling
    )


# class SearchBar(Component[NoChildren, GlobalAttrs]): # Ludic Component
#     classes = ["search-bar"]
#     styles = style.use( # Ludic styles
#         lambda theme: {
#             ".search-bar": {
#                 "width": "100%",
#                 "input": {
#                     "background-color": theme.colors.light.lighten(1),
#                     "border": f"1px solid {theme.colors.light.darken(5)}",
#                     "color": theme.colors.dark,
#                     "max-inline-size": "none",
#                 },
#                 "input::placeholder": {
#                     "color": theme.colors.dark.lighten(7),
#                 },
#                 "input:focus": {
#                     "border-color": theme.colors.dark.lighten(5),
#                     "outline": "none",
#                 },
#             },
#         }
#     )

#     def __init__(self, query="", **kwargs): # Ludic __init__
#         super().__init__(**kwargs)
#         self.query = query

#     @override
#     def render(self) -> InputField: # Ludic render
def SearchBar(query: str = "", **attrs): # FastHTML functional component
    # Styles moved to .search-bar in components.css
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
        cls="search-bar-input", # Class for input styling
        **attrs # Pass through any other attributes
    )


# class HiddenLink(Component[str, LinkAttrs]): # Ludic Component
#     @override
#     def render(self) -> a:
def HiddenLink(*children, to: str, title: str, **attrs): # FastHTML functional component
    # Styles moved to .hidden-link in components.css
    return A(
        *children,
        href=to,
        title=title,
        cls="hidden-link", # Keep class for CSS
        **attrs
    )


# class BookericLink(Component[str, LinkAttrs]): # Ludic Component
#     @override
#     def render(self) -> a:
def BookericLink(*children, to: str, **attrs): # FastHTML functional component
    # Styles moved to .bookeric-link.external in components.css
    return A(
        *children,
        href=to,
        target="_blank",
        cls="bookeric-link external", # Keep class for CSS
        **attrs
    )

#
# --- Complex components commented out for now ---
#

# class TableStructure(Component[NoChildren, GlobalAttrs]): # Ludic Component
#     @override
#     def render(self) -> Center: # Ludic Center
#         structure = self.attrs.get("structure", [])
#         return Center( # Ludic Center
#             CodeBlock( # Ludic CodeBlock
#                 f"""
# [
#  {',\n '.join([str(col) for col in structure])}
# ]
# """
#             ),
#         )
def TableStructure(structure: list | None = None, **attrs): # FastHTML functional component
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


# class TagCloud(Component[NoChildren, GlobalAttrs]): # Ludic Component
#     styles = { # Ludic styles, moved to components.css
#         ".btn.tag": {
#             "border": "1px solid #4a4a4a4a;",
#             "font-size": "0.8em;",
#             "padding": "clamp(0.23rem, 0.23rem + 0vw, 0.28rem) clamp(0.47rem, 0.47rem + 0.1vw, 0.59rem);",
#         },
#         ".btn.tag:hover": {
#             "filter": "none;",
#             "border": "1px solid #4a4a4a77;",
#             "background-color": "#fff59b;",
#             "text-decoration": "none;",
#             "box-shadow": "rgba(0, 0, 0, 0.18) 0px 2px 4px;",
#         },
#     }
#
#     @override
#     def render(self) -> Cluster: # Ludic Cluster
#         tags = self.attrs.get("tags", [])
#         return Cluster( # Ludic Cluster
#             *[
#                 ButtonLink(tag, to=f"/tags/{tag}", classes="btn tag info") # Ludic ButtonLink
#                 for tag in tags
#             ]
#         )
def TagCloud(tags: list | None = None, **attrs): # FastHTML functional component
    if tags is None:
        tags = []
    # CSS class "tag-cloud" handles flex layout.
    # CSS classes "btn tag info" are for styling individual tags.
    return Div(
        *[
            A(tag, href=f"/tags/{tag}", cls="btn tag info") # Was ButtonLink
            for tag in tags
        ],
        cls="tag-cloud",
        **attrs
    )

#
# class Switcher(div): # Ludic specific layout component, styles moved to .switcher in CSS if needed
#     classes = ["switcher"]
#     styles = style.use(...)
# --- Ludic Switcher class definition removed ---

def _get_random_giphy_url(): # Helper function for PreviewImage
    _url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=waiting&rating=r"
    try:
        r = requests.get(_url, timeout=5) # Added timeout
        r.raise_for_status() # Raise an exception for bad status codes
        giphy_url = r.json()["data"]["images"]["original"]["url"]
        return giphy_url
    except requests.RequestException as e:
        print(f"Error fetching Giphy URL: {e}") # Or log this
        return "/static/images/placeholder.gif" # Fallback image
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing Giphy response: {e}") # Or log this
        return "/static/images/placeholder.gif" # Fallback image

# class PreviewImage(Component[img, ImgAttrs]): # Ludic Component
#     classes = ["image-placeholder"]
#     styles = { ... } # Moved to CSS
#     def get_random_giphy_url(self): ...
#     @override
#     def render(self) -> img: ...
def PreviewImage(src: str | None = None, **attrs): # FastHTML functional component
    placeholder_src = ""
    if not src:
        placeholder_src = _get_random_giphy_url() # Call helper
        src = placeholder_src # Use the random Giphy URL as src
        attrs['data_placeholder'] = "true" # Keep placeholder attribute if needed

    # Ensure all necessary attributes from original are passed or handled
    # Original attrs: src, height, width, id, hx_get, hx_target, hx_trigger, hx_swap
    return Img(src=src, cls="image-placeholder", **attrs)


# class ImageSwitcher(div): # Ludic Component
#     classes = ["image-switcher"]
#     styles = style.use(...) # Moved to CSS
def ImageSwitcher(*children, **attrs): # FastHTML functional component
    # Original Ludic component was a div with specific flex styles
    # These styles are now in components.css under .image-switcher
    return Div(*children, cls="image-switcher", **attrs)


# class BookmarkBox(div): # Ludic Component
#     classes = ["bookmark-box"]
#     styles = style.use(...) # Moved to CSS
def BookmarkBox(*children, **attrs): # FastHTML functional component
    # All styling and structure is handled by CSS via the 'bookmark-box' class and its modifiers.
    # Child elements like P, A, Div will be passed in *children.
    # Modifier classes like 'small', 'large', 'transparent', 'invert' should be part of attrs['cls']
    # e.g., BookmarkBox(P("Hello"), cls="bookmark-box small transparent")

    # The original Ludic component was a div.
    # We ensure 'bookmark-box' is always part of the class list.
    current_classes = attrs.pop('cls', "")
    final_classes = f"bookmark-box {current_classes}".strip()

    return Div(*children, cls=final_classes, **attrs)


# class HTMXDeleteButton(ComponentStrict[PrimitiveChildren, LinkAttrs]): # Ludic Component
#     classes = ["btn"]
#     @override
#     def render(self) -> a: ...
def HTMXDeleteButton(*children, to: str = "#", hx_target: str, hx_swap: str, hx_delete: str, cls: str = "", **attrs): # FastHTML
    # Original classes: ["btn"] + self.attrs.get("classes", [])
    # data-confirmed is a state managed by JS, but can be set initially
    final_cls = f"btn delete-btn {cls}".strip()
    # Store the delete URL in data attribute and remove hx_delete initially
    # JS will add hx_delete back when confirmed
    return A(*children, href=to, hx_target=hx_target, hx_swap=hx_swap,
             **{"data-delete-url": hx_delete, "data-confirmed": "false"},  # Use dict for hyphenated attributes
             cls=final_cls, **attrs)


# class ToggleImagePreviewButton(ComponentStrict[PrimitiveChildren, LinkAttrs]): # Ludic Component
#     classes = ["btn toggle-image-preview-btn"]
#     @override
#     def render(self) -> a: ...
def ToggleImagePreviewButton(*children, hx_get: str, hx_target: str, hx_swap: str, cls: str = "", **attrs): # FastHTML
    final_cls = f"btn toggle-image-preview-btn {cls}".strip()
    return A(*children, hx_get=hx_get, hx_target=hx_target, hx_swap=hx_swap, cls=final_cls, **attrs) # type: ignore


# class GetTagsForBookmarkButton(ComponentStrict[PrimitiveChildren, LinkAttrs]): # Ludic Component
#     classes = ["btn"]
#     @override
#     def render(self) -> a: ...
def GetTagsForBookmarkButton(*children, to: str = "#", hx_swap: str, hx_target: str, hx_get: str, cls: str = "", **attrs): # FastHTML
    final_cls = f"btn {cls}".strip() # General btn class, specific styling via parent or further classes
    return A(*children, href=to, hx_swap=hx_swap, hx_target=hx_target, hx_get=hx_get, cls=final_cls, **attrs) # type: ignore


# class UpdateBookmarkButton(ButtonLink): # Ludic ButtonLink
#     def __init__(self, text: str, **attrs):
#         super().__init__(text, to=attrs.pop("hx_get"), **attrs)
def UpdateBookmarkButton(text: str, hx_get: str, cls: str = "", hx_target: str = "", **attrs): # FastHTML
    # Original Ludic component was a ButtonLink, which is an A tag styled as a button
    # It used 'to' for the href, but hx_get for the actual action URL.
    final_cls = f"btn update-btn {cls}".strip() # Added 'update-btn' for specific styling
    attrs_dict = {"hx_get": hx_get, "cls": final_cls}
    if hx_target:
        attrs_dict["hx_target"] = hx_target
    attrs_dict.update(attrs)
    return A(text, **attrs_dict) # type: ignore


def _render_tags_html(tags: list[str] | str):
    """Renders a list of tags as A elements within a Div."""
    if isinstance(tags, str):
        # Handle case where tags might be passed as a string
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = tags.split() if tags else []
    
    if not tags:
        return Div(cls="tags-container")
    
    # Using 'btn tag info' for consistency with previous TagCloud, adjust if needed
    return Div(*[A(tag, href=f"/tags/{tag}", cls="btn tag info") for tag in tags], cls="tags-container")

def _render_created_at_html(created_at: str | None) -> Div:
    if created_at:
        # Assuming created_at is a string that can be parsed
        return Div(f"Created: {created_at}", cls="created-at-display")
    return Div("", cls="created-at-display")


def _render_bookmark_html(bookmark: dict, is_image_list: bool = False): # Helper for list components
    bookmark_id = bookmark.get("id")
    title = bookmark.get("title", "")
    url = bookmark.get("url", "")
    description = bookmark.get("description", "")
    tags = bookmark.get("tags", [])
    thumbnail_url = bookmark.get("thumbnail_url")
    created_at = bookmark.get("created_at")

    tags_html = _render_tags_html(tags)
    created_at_html = _render_created_at_html(created_at)

    toggle_btn_target_id = f"bmb-{bookmark_id}"

    # Prepare content list for BookmarkBox
    content = [
        BookericLink(title, to=url),
        created_at_html,
    ]

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

    return BookmarkBox(*content, id=toggle_btn_target_id)


# class BookmarkList(Component[NoChildren, GlobalAttrs]): # Ludic
#     def render_tags(self, tags) -> Cluster: ...
#     def render_bookmark(self, bookmark) -> BookmarkBox: ...
#     @override
#     def render(self) -> Switcher: ...
def BookmarkList(bookmarks: list, **attrs): # FastHTML
    # Assuming 'bookmarks' is a list of bookmark dictionaries
    # The 'attrs' can be used for top-level Div attributes if needed (e.g. id, class)
    # Replaces Ludic's Switcher with a Div styled by .bookmark-list-switcher
    return Div(
        *[_render_bookmark_html(bm, is_image_list=False) for bm in bookmarks],
        cls="bookmark-list-switcher",
        **attrs
    )


# class BookmarkImageList(Component[NoChildren, GlobalAttrs]): # Ludic
#     async def fetch_thumbnails(self): ...
#     def render_tags(self, tags) -> Cluster: ...
#     def render_bookmark(self, bookmark) -> BookmarkBox: ...
#     @override
#     def render(self) -> Switcher: ...
def BookmarkImageList(bookmarks: list, **attrs): # FastHTML
    # Removed asyncio.create_task(self.fetch_thumbnails())
    # Relies on PreviewImage's HTMX attributes for lazy loading thumbnails.
    # The update_bookmarks_with_thumbnails can be called in the route handler if needed pre-render.
    return Div(
        *[_render_bookmark_html(bm, is_image_list=True) for bm in bookmarks],
        cls="bookmark-image-list-switcher", # Or use "bookmark-list-switcher" if layout is identical
        **attrs
    )


# class BookmarkAttrs(Attrs): # Ludic Attrs, can be kept for reference or Pydantic model
#     title: Annotated[str, FieldMeta(label="Title")]
#     url: Annotated[str, FieldMeta(label="URL")]
#     description: Annotated[str, FieldMeta(label="Description")]
#     tags: Annotated[str, FieldMeta(label="Tags")]
# --- BookmarkAttrs class definition removed as it's not directly used by FastHTML form rendering ---

# class EditBookmarkForm(Component[NoChildren, BookmarkAttrs]): # Ludic Component
#     @override
#     def render(self) -> Form: ... # Ludic Form
def EditBookmarkForm(bookmark: dict, **attrs): # FastHTML functional component
    # 'bookmark' is a dictionary containing bookmark data
    # 'attrs' can include form attributes like 'action', 'method' (though method is POST by default here)

    tags_list = bookmark.get("tags", [])
    if isinstance(tags_list, str): # Handle if tags are passed as a JSON string
        try:
            tags_list = json.loads(tags_list)
        except json.JSONDecodeError:
            tags_list = [] # Or split the string, depending on expected format
    tags_str = " ".join(tags_list)

    form_method = attrs.pop('method', "POST") # Default to POST, allow override
    form_action = attrs.pop('action', f"/edit/{bookmark.get('id', '')}") # Example action

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


