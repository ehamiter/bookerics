import os
import re
import shutil
import boto3
import aioboto3
import aiohttp
import aiofiles
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional
import asyncio
import json
import sqlite3
from io import BytesIO
from xml.sax.saxutils import escape
from contextlib import contextmanager
import threading

from PIL import Image

from .constants import (
    ADDITIONAL_DB_PATHS,
    BOOKMARK_NAME,
    LOCAL_BACKUP_PATH,
    RSS_FEED_CREATION_TAGS,
    RSS_METADATA,
    THUMBNAIL_API_KEY,
    FEEDS_DIR,
)

from .utils import logger


Bookmark = Dict[str, Any]


def clean_html(raw_html):
    return re.sub(r'<.*?>', '', raw_html)

def safe_escape(text):
    return escape(clean_html(text), {
        '"': "&quot;",
        "'": "&apos;"
    })


# S3/DB setup
S3_BUCKET_NAME = f"{BOOKMARK_NAME}s"
S3_KEY = f"{BOOKMARK_NAME}s.db"
DB_PATH = f"./{BOOKMARK_NAME}s.db"

# Global connection storage per thread
_connection = threading.local()

@contextmanager
def get_db_connection():
    """Get a database connection for the current thread."""
    if not hasattr(_connection, 'db'):
        _connection.db = sqlite3.connect(DB_PATH)
        _connection.db.row_factory = sqlite3.Row
    
    try:
        yield _connection.db
    except Exception as e:
        _connection.db.rollback()
        raise e

def download_file_from_s3(bucket_name, s3_key, local_path):
    s3 = boto3.client("s3")
    try:
        s3.download_file(bucket_name, s3_key, local_path)
        logger.info(f"💾 Downloaded {s3_key} from bucket {bucket_name} to {local_path}")
    except Exception as e:
        logger.error(f"💥 Error downloading file from S3: {e}")


def load_db_on_startup():
    logger.info("🔖 Bookerics starting up…")
    if not os.path.exists(DB_PATH):
        download_file_from_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH)
    
    # Test the connection
    with get_db_connection() as conn:
        conn.execute("SELECT 1")
    
    logger.info("☑️ Database loaded!")


def get_max_id(cursor, table_name: str = "bookmarks"):
    cursor.execute(f'SELECT MAX(id) FROM {table_name}')
    return cursor.fetchone()[0] or 0

def extract_order_by_clause(query):
    if 'ORDER BY' in query:
        return query.split('ORDER BY')[-1]
    return ''

def enter_the_multiverse(query, cursor, table_name):
    # Attach additional databases if they exist
    for idx, _db_path in enumerate(ADDITIONAL_DB_PATHS):
        try:
            cursor.execute(f'ATTACH DATABASE "{_db_path}" AS db_{idx};')
            logger.info(f"💽 {_db_path} > db_{idx}")
        except sqlite3.OperationalError as e:
            logger.error(f"❌ Failed to attach {_db_path}: {e}")
            raise

    # Get the maximum ID from the main database
    max_id_main = get_max_id(cursor, table_name)

    # Extract the ORDER BY clause from the original query
    order_by_clause = extract_order_by_clause(query) or "created_at DESC, updated_at DESC"

    # Remove the ORDER BY clause from the original query
    base_query = query.strip().split("ORDER BY")[0].strip().rstrip(";")

    # Modify query to include data from attached databases
    union_queries = [f"SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM ({base_query})"]
    for idx in range(len(ADDITIONAL_DB_PATHS)):
        attach_query = base_query.replace(table_name, f"db_{idx}.{table_name}")
        offset = (max_id_main + 1 + idx * 1000000)
        union_queries.append(
            f"SELECT id + {offset} AS id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'external' AS source FROM ({attach_query})"
        )

    combined_query = " UNION ALL ".join(union_queries)

    # Append the ORDER BY clause to the combined query
    final_query = f"SELECT * FROM ({combined_query}) ORDER BY {order_by_clause}"
    return final_query

def execute_query(query: str, params: Tuple = (), table_name: str = "bookmarks", allow_external_db: bool = True) -> Any:
    with get_db_connection() as connection:
        cursor = connection.cursor()

        if allow_external_db:
            if not params and ADDITIONAL_DB_PATHS:
                query = enter_the_multiverse(query, cursor, table_name)

        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            last_row_id = cursor.lastrowid
            connection.commit()
            return result, last_row_id
        except Exception as e:
            logger.error(
                f"💥 Error executing query: {query}\nParams: {params}\nException: {e}"
            )
            raise


def fetch_data(query: str, params: tuple = ()) -> List[Bookmark]:
    # source (internal / external) gets added as an attribute here
    rows, _ = execute_query(query, params)
    bookmarks = []
    for row in rows:
        if len(row) == 9:
            (
                id,
                title,
                url,
                thumbnail_url,
                description,
                tags_json,
                created_at,
                updated_at,
                source
            ) = row
            try:
                tags = json.loads(tags_json) if tags_json else []
                if tags == [""]:
                    tags = []
            except json.JSONDecodeError:
                tags = []
            bookmarks.append(
                {
                    "id": id,
                    "title": title,
                    "url": url,
                    "thumbnail_url": thumbnail_url,
                    "description": description,
                    "tags": tags,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "source": source
                }
            )
        else:
            logger.error(f"💥 Unexpected row format: {row}")
    return bookmarks


def fetch_bookmarks(kind: str, page: int = 1, per_page: int = 50) -> List[Bookmark]:
    bq = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM bookmarks "
    offset = (page - 1) * per_page
    
    queries = {
        "newest": f"{bq} ORDER BY created_at DESC, updated_at DESC LIMIT {per_page} OFFSET {offset};",
        "oldest": f"{bq} ORDER BY created_at ASC, updated_at ASC LIMIT {per_page} OFFSET {offset};",
        "untagged": f"{bq} WHERE tags IS NULL OR tags = '[\"\"]' ORDER BY created_at DESC, updated_at DESC LIMIT {per_page} OFFSET {offset};",
    }
    query = queries.get(kind, queries["newest"])
    return fetch_data(query)

def fetch_bookmarks_all(kind: str) -> List[Bookmark]:
    """Fetch all bookmarks without pagination - for compatibility with existing code that needs all bookmarks"""
    bq = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM bookmarks "
    queries = {
        "newest": f"{bq} ORDER BY created_at DESC, updated_at DESC;",
        "oldest": f"{bq} ORDER BY created_at ASC, updated_at ASC;",
        "untagged": f"{bq} WHERE tags IS NULL OR tags = '[\"\"]' ORDER BY created_at DESC, updated_at DESC;",
    }
    query = queries.get(kind, queries["newest"])
    return fetch_data(query)


def search_bookmarks(query: str) -> List[Bookmark]:
    search_query = f"%{query}%"
    query = f"""
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source
    FROM bookmarks
    WHERE title LIKE '{search_query}'
    OR url LIKE '{search_query}'
    OR description LIKE '{search_query}'
    OR tags LIKE '{search_query}'
    ORDER BY created_at DESC, updated_at DESC;
    """
    return fetch_data(query)


def fetch_unique_tags(kind: str = "frequency") -> List[Dict[str, Any]]:
    query = ""
    if kind == "frequency":
        query = """
        SELECT json_each.value, COUNT(*) as frequency
        FROM bookmarks, json_each(bookmarks.tags)
        WHERE json_each.value IS NOT NULL
          AND json_each.value != ''
          AND json_each.value != '[""]'
        GROUP BY json_each.value
        ORDER BY frequency DESC;
        """
    elif kind == "newest":
        query = """
        SELECT DISTINCT json_each.value
        FROM bookmarks, json_each(bookmarks.tags)
        WHERE json_each.value IS NOT NULL
          AND json_each.value != ''
          AND json_each.value != '[""]'
        ORDER BY bookmarks.updated_at DESC, bookmarks.created_at DESC;
        """
    rows, _ = execute_query(query, allow_external_db=False)
    if kind == "frequency":
        return [{"tag": row[0], "frequency": row[1]} for row in rows]
    else:
        return [{"tag": row[0]} for row in rows]


def fetch_bookmarks_by_tag(tag: str) -> List[Bookmark]:
    query = """
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source
    FROM bookmarks
    WHERE ? IN (SELECT value FROM json_each(bookmarks.tags))
    ORDER BY updated_at DESC, created_at DESC;
    """
    return fetch_data(query, (tag,))


async def delete_bookmark_by_id(bookmark_id: int) -> None:
    await execute_query_async("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
    try:
        # After deleting, we need to update feeds and S3
        # Fetch all internal bookmarks to regenerate the main feed
        all_bookmarks = fetch_bookmarks_all(kind="newest")
        internal_bookmarks = [
            bm for bm in all_bookmarks if bm.get("source") == "internal"
        ]

        if internal_bookmarks:
            # Update the main RSS feed
            await create_feed(tag=None, bookmarks=internal_bookmarks, publish=True)

        # Also update S3
        await schedule_upload_to_s3()

    except Exception as e:
        logger.error(f"Error during post-deletion tasks: {e}")


def backup_bookerics_db():
    if LOCAL_BACKUP_PATH and not os.path.exists(LOCAL_BACKUP_PATH):
        os.makedirs(LOCAL_BACKUP_PATH)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if LOCAL_BACKUP_PATH:
        backup_file_path = os.path.join(
            LOCAL_BACKUP_PATH, f"{BOOKMARK_NAME}s_backup_{timestamp}.db"
        )
        if os.path.exists(DB_PATH):
            shutil.copy(DB_PATH, backup_file_path)
            logger.info(f"✅ Backup successful: {backup_file_path}")

            # Prune old backups, keeping the 10 most recent
            backups = sorted(
                [
                    os.path.join(LOCAL_BACKUP_PATH, f)
                    for f in os.listdir(LOCAL_BACKUP_PATH)
                    if f.endswith(".db")
                ],
                key=os.path.getmtime,
                reverse=True,
            )
            for old_backup in backups[10:]:
                os.remove(old_backup)
                logger.info(f"🗑️ Pruned old backup: {old_backup}")


async def schedule_upload_to_s3():
    logger.info("🚀 Scheduling S3 upload...")
    try:
        await upload_file_to_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH)
        if FEEDS_DIR and os.path.exists(FEEDS_DIR):
            for feed_file in os.listdir(FEEDS_DIR):
                if feed_file.endswith(".xml"):
                    feed_path = os.path.join(FEEDS_DIR, feed_file)
                    s3_feed_key = f"feeds/{feed_file}"
                    await upload_file_to_s3(S3_BUCKET_NAME, s3_feed_key, feed_path)
        logger.info("✅ S3 upload complete.")
    except Exception as e:
        logger.error(f"💥 S3 upload failed: {e}")


async def schedule_feed_creation(
    tag: Optional[str], bookmarks: List[Bookmark], publish: bool
):
    await create_feed(tag, bookmarks, publish)


async def schedule_thumbnail_fetch_and_save(
    bookmark: Bookmark, schedule_s3_upload: bool = True
):
    await get_bookmark_thumbnail_image(bookmark)
    if schedule_s3_upload:
        await schedule_upload_to_s3()


def verify_table_structure(table_name: str = "bookmarks") -> List[Dict[str, Any]]:
    query = f"PRAGMA table_info({table_name})"
    rows, _ = execute_query(query)
    return [{"name": row[1], "type": row[2]} for row in rows]


async def get_file_size(url: str) -> int:
    try:
        async with aiohttp.ClientSession() as session:
            print(f"Requesting HEAD for URL: {url}")  # Debug print
            async with session.head(url) as response:
                file_size = response.headers.get('Content-Length')
                if file_size:
                    return int(file_size)
                else:
                    raise ValueError("Could not retrieve file size.")
    except Exception as e:
        logger.error(f"Error getting file size for {url}: {e}")
        return -1


async def push_changes_up(tag: str) -> None:
    if tag in RSS_FEED_CREATION_TAGS:
        bookmarks = fetch_bookmarks_by_tag(tag)
        await create_feed(tag, bookmarks, publish=True)
        await schedule_upload_to_s3()


async def create_feed(
    tag: Optional[str], bookmarks: List[Bookmark], publish: bool = False
) -> None:
    logger.info(f"🗂️ Creating feed for tag: {tag}")
    if FEEDS_DIR and not os.path.exists(FEEDS_DIR):
        os.makedirs(FEEDS_DIR)
    feed_content = create_rss_feed(bookmarks, tag)
    feed_filename = f"{tag}.xml" if tag else "all.xml"
    if FEEDS_DIR:
        feed_path = os.path.join(FEEDS_DIR, feed_filename)
        async with aiofiles.open(feed_path, "w") as f:
            await f.write(feed_content)
        logger.info(f"✅ Feed created at {feed_path}")

        if publish:
            s3_feed_key = f"feeds/{feed_filename}"
            await upload_file_to_s3(S3_BUCKET_NAME, s3_feed_key, feed_path)
    return


async def execute_query_async(query: str, params: tuple = ()):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: execute_query(query, params))


async def fetch_bookmark_by_id(id: str) -> Optional[Bookmark]:
    query = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM bookmarks WHERE id = ?"
    results = fetch_data(query, (id,))
    return results[0] if results else None


async def fetch_bookmark_by_url(url: str) -> Optional[Bookmark]:
    query = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM bookmarks WHERE url = ?"
    results = fetch_data(query, (url,))
    return results[0] if results else None


async def upload_file_to_s3(bucket_name: str, s3_key: str, local_path: str):
    session = aioboto3.Session()
    async with session.client("s3") as s3:  # type: ignore
        try:
            await s3.upload_file(local_path, bucket_name, s3_key)
            logger.info(f"⬆️ Uploaded {local_path} to s3://{bucket_name}/{s3_key}")
        except Exception as e:
            logger.error(f"💥 Error uploading {local_path} to S3: {e}")


async def wait_for_thumbnail(
    bookmark_id: int, max_retries: int = 5
) -> Optional[Bookmark]:
    for i in range(max_retries):
        bookmark = await fetch_bookmark_by_id(str(bookmark_id))
        if bookmark and bookmark.get("thumbnail_url"):
            return bookmark
        await asyncio.sleep(1)  # Wait 1 second between attempts
    return None


async def create_bookmark(
    title: str,
    url: str,
    description: str,
    tags: List[str],
    source: str = "internal",
) -> Optional[int]:
    tags_json = json.dumps(tags)
    created_at = datetime.now(timezone.utc).isoformat()
    query = """
    INSERT INTO bookmarks (title, url, description, tags, created_at, updated_at, source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    try:
        _, last_row_id = execute_query(
            query,
            (title, url, description, tags_json, created_at, created_at, source),
            allow_external_db=False,
        )

        if last_row_id is not None:
            bookmark_id = last_row_id
            logger.info(f"✅ Created bookmark with ID: {bookmark_id}")

            new_bookmark = await fetch_bookmark_by_id(str(bookmark_id))
            if new_bookmark:
                await schedule_thumbnail_fetch_and_save(new_bookmark)

            # Check if any of the tags require a feed to be created/updated
            for tag in tags:
                if tag in RSS_FEED_CREATION_TAGS:
                    await push_changes_up(tag)
            return bookmark_id
        else:
            logger.error("💥 Failed to retrieve last inserted ID.")
            return None
    except Exception as e:
        logger.error(f"💥 Error creating bookmark: {e}")
        return None


async def update_bookmark_thumbnail_url(bookmark_id: int, img_url: str):
    query = """
    UPDATE bookmarks
    SET thumbnail_url = ?, updated_at = ?
    WHERE id = ?
    """
    updated_at = datetime.now(timezone.utc).isoformat()
    await execute_query_async(query, (img_url, updated_at, bookmark_id))
    logger.info(f"🖼️ Thumbnail URL updated for bookmark {bookmark_id}")


async def update_bookmark_description(id: str, description: str):
    query = """
    UPDATE bookmarks
    SET description = ?, updated_at = ?
    WHERE id = ?
    """
    updated_at = datetime.now(timezone.utc).isoformat()
    await execute_query_async(query, (description, updated_at, id))
    logger.info(f"📝 Description updated for bookmark {id}")


async def update_bookmark_title(id: str, title: str):
    query = """
    UPDATE bookmarks
    SET title = ?, updated_at = ?
    WHERE id = ?
    """
    updated_at = datetime.now(timezone.utc).isoformat()
    await execute_query_async(query, (title, updated_at, id))
    logger.info(f"✏️ Title updated for bookmark {id}")


async def update_bookmark_tags(id: str, tags: List[str]):
    # Filter out empty tags
    tags = [tag for tag in tags if tag.strip()]
    tags_json = json.dumps(tags)

    query = "UPDATE bookmarks SET tags = ?, updated_at = ? WHERE id = ?"
    updated_at = datetime.now(timezone.utc).isoformat()
    await execute_query_async(query, (tags_json, updated_at, id))
    logger.info(f"🏷️ Tags updated for bookmark {id}")


async def get_bookmark_thumbnail_image(bookmark: Bookmark) -> str:
    url = bookmark.get("url")
    bookmark_id = bookmark.get("id")

    if not url or not bookmark_id:
        return ""

    logger.info(f"🖼️ Getting thumbnail for {url}")
    thumbnail_api_url = f"https://api.microlink.io/?url={url}&screenshot=true&meta=false&embed=screenshot.url"
    headers = (
        {"x-api-key": THUMBNAIL_API_KEY} if THUMBNAIL_API_KEY else {}
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_api_url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                img_url = data.get("data", {}).get("screenshot", {}).get("url")

                if img_url:
                    async with session.get(img_url) as img_response:
                        img_response.raise_for_status()
                        image_data = await img_response.read()

                        # Create a local path for the image
                        local_img_dir = f"./{S3_BUCKET_NAME}"
                        os.makedirs(local_img_dir, exist_ok=True)
                        local_img_path = os.path.join(
                            local_img_dir, f"{bookmark_id}.png"
                        )

                        # Save the original image
                        async with aiofiles.open(local_img_path, "wb") as f:
                            await f.write(image_data)
                        logger.info(f"✅ Saved original thumbnail to {local_img_path}")

                        # Create a thumbnail
                        img = Image.open(BytesIO(image_data))
                        img.thumbnail((200, 200))
                        thumb_path = local_img_path.replace(".png", "_thumb.png")
                        img.save(thumb_path, "PNG")
                        logger.info(f"✅ Created thumbnail at {thumb_path}")

                        # Upload original to S3
                        s3_key = f"{bookmark_id}.png"
                        await upload_file_to_s3(
                            S3_BUCKET_NAME, s3_key, local_img_path
                        )

                        # Update the bookmark with the S3 URL
                        s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
                        await update_bookmark_thumbnail_url(bookmark_id, s3_url)

                        return s3_url
                return ""
    except Exception as e:
        logger.error(f"💥 Error getting thumbnail for {url}: {e}")
        return ""


async def update_bookmarks_with_thumbnails(
    bookmarks: List[Bookmark], schedule_s3_upload=True
):
    tasks = [
        get_bookmark_thumbnail_image(bookmark)
        for bookmark in bookmarks
        if not bookmark.get("thumbnail_url")
    ]
    if tasks:
        await asyncio.gather(*tasks)
    if schedule_s3_upload:
        await schedule_upload_to_s3()

def create_rss_feed(
    bookmarks: List[Bookmark], tag: Optional[str] = None
) -> str:
    """Creates an RSS feed from a list of bookmarks."""
    try:
        sorted_bookmarks = sorted(
            [b for b in bookmarks if b],
            key=lambda x: x['created_at'],
            reverse=True
        )[:25]
        items = []
        for bookmark in sorted_bookmarks:
            if not bookmark:
                continue
                
            created_at = bookmark['created_at']
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            pub_date = dt.strftime('%a, %d %b %Y %H:%M:%S %z')

            title = bookmark.get('title', '').strip()
            title = clean_html(title) or "Untitled"

            description = bookmark.get('description', '').strip()
            description = clean_html(description)

            link = bookmark.get('url', '')
            link = safe_escape(link)

            thumbnail = bookmark.get('thumbnail_url', None)
            if thumbnail is None:
                thumbnail = "https://via.placeholder.com/200x200"
            
            item = f"""
                <item>
                    <pubDate>{pub_date}</pubDate>
                    <title><![CDATA[{title}]]></title>
                    <link>{link}</link>
                    <description><![CDATA[{description}]]></description>
                    <enclosure url="{thumbnail}" type="image/jpeg" length="1000000" />
                    <guid isPermaLink="false">{link}</guid>
                </item>
            """
            items.append(item)

        channel_title = (
            f"{RSS_METADATA['title']} - Tag: {tag}"
            if tag
            else RSS_METADATA["title"]
        )
        if RSS_METADATA.get("link"):
            channel_link = (
                f"{RSS_METADATA['link']}/tags/{tag}" if tag else RSS_METADATA["link"]
            )
        else:
            channel_link = ""

        channel_description = (
            f"Bookmarks tagged with '{tag}'"
            if tag
            else RSS_METADATA.get("description", "")
        )

        rss_items = []
        for item in items:
            rss_items.append(item)

        rss_items_str = "\n".join(rss_items)

        return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>{channel_title}</title>
    <link>{channel_link}</link>
    <description>{channel_description}</description>
    <language>en-us</language>
    <pubDate>{datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
    <lastBuildDate>{datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
    <atom:link href="{RSS_METADATA.get('link', '')}/feeds/{tag or 'all'}.xml" rel="self" type="application/rss+xml" />
    {rss_items_str}
</channel>
</rss>
"""
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise e
