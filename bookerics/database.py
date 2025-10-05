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
import subprocess
from xml.sax.saxutils import escape
from contextlib import contextmanager
import threading

from .constants import (
    BOOKMARK_NAME,
    LOCAL_BACKUP_PATH,
    RSS_METADATA,
    FEEDS_DIR,
    AWS_S3_BUCKET,
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
S3_BUCKET_NAME = AWS_S3_BUCKET or f"{BOOKMARK_NAME}s"
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






def execute_query(query: str, params: Tuple = ()) -> Any:
    with get_db_connection() as connection:
        cursor = connection.cursor()

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
    rows, _ = execute_query(query, params)
    bookmarks = []
    for row in rows:
        if len(row) == 8:
            (
                id,
                title,
                url,
                thumbnail_url,
                description,
                tags_json,
                created_at,
                updated_at,
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
                }
            )
        else:
            logger.error(f"💥 Unexpected row format: {row}")
    return bookmarks


def fetch_bookmarks(kind: str, page: int = 1, per_page: int = 25) -> List[Bookmark]:
    bq = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks "
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
    bq = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks "
    queries = {
        "newest": f"{bq} ORDER BY created_at DESC, updated_at DESC;",
        "oldest": f"{bq} ORDER BY created_at ASC, updated_at ASC;",
        "untagged": f"{bq} WHERE tags IS NULL OR tags = '[\"\"]' ORDER BY created_at DESC, updated_at DESC;",
    }
    query = queries.get(kind, queries["newest"])
    return fetch_data(query)


def search_bookmarks(query: str, page: int = 1, per_page: int = 25) -> List[Bookmark]:
    print(f"🔍 SEARCH_BOOKMARKS: Searching for query: '{query}', page: {page}, per_page: {per_page}")
    search_query = f"%{query}%"
    offset = (page - 1) * per_page
    sql_query = """
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at
    FROM bookmarks
    WHERE title LIKE ?
    OR url LIKE ?
    OR description LIKE ?
    OR tags LIKE ?
    ORDER BY created_at DESC, updated_at DESC
    LIMIT ? OFFSET ?;
    """
    print(f"🔍 SEARCH_BOOKMARKS: Executing SQL with search_query: '{search_query}', limit: {per_page}, offset: {offset}")
    results = fetch_data(sql_query, (search_query, search_query, search_query, search_query, per_page, offset))
    print(f"🔍 SEARCH_BOOKMARKS: Found {len(results)} bookmarks")
    return results


def search_bookmarks_all(query: str) -> List[Bookmark]:
    """Search all bookmarks without pagination - for compatibility and getting total count"""
    print(f"🔍 SEARCH_BOOKMARKS_ALL: Searching for query: '{query}' (no pagination)")
    search_query = f"%{query}%"
    sql_query = """
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at
    FROM bookmarks
    WHERE title LIKE ?
    OR url LIKE ?
    OR description LIKE ?
    OR tags LIKE ?
    ORDER BY created_at DESC, updated_at DESC;
    """
    print(f"🔍 SEARCH_BOOKMARKS_ALL: Executing SQL with search_query: '{search_query}'")
    results = fetch_data(sql_query, (search_query, search_query, search_query, search_query))
    print(f"🔍 SEARCH_BOOKMARKS_ALL: Found {len(results)} bookmarks")
    return results


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
    rows, _ = execute_query(query)
    if kind == "frequency":
        return [{"tag": row[0], "frequency": row[1]} for row in rows]
    else:
        return [{"tag": row[0]} for row in rows]


def fetch_bookmarks_by_tag(tag: str) -> List[Bookmark]:
    query = """
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at
    FROM bookmarks
    WHERE ? IN (SELECT value FROM json_each(bookmarks.tags))
    ORDER BY updated_at DESC, created_at DESC;
    """
    return fetch_data(query, (tag,))


async def delete_bookmark_by_id(bookmark_id: int) -> None:
    await execute_query_async("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
    try:
        # After deleting, we need to update feeds and S3
        # Fetch all bookmarks to regenerate the main feed
        all_bookmarks = fetch_bookmarks_all(kind="newest")

        if all_bookmarks:
            # Update the main RSS feed
            await create_feed(tag=None, bookmarks=all_bookmarks, publish=True)

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


async def update_main_rss_feed() -> None:
    """Update the main RSS feed with all bookmarks"""
    all_bookmarks = fetch_bookmarks_all(kind="newest")
    await create_feed(tag=None, bookmarks=all_bookmarks, publish=True)


async def create_feed(
    tag: Optional[str], bookmarks: List[Bookmark], publish: bool = False
) -> None:
    logger.info("🗂️ Creating main RSS feed")
    if FEEDS_DIR and not os.path.exists(FEEDS_DIR):
        os.makedirs(FEEDS_DIR)
    feed_content = create_rss_feed(bookmarks, tag)
    feed_filename = "rss.xml"
    if FEEDS_DIR:
        feed_path = os.path.join(FEEDS_DIR, feed_filename)
        async with aiofiles.open(feed_path, "w") as f:
            await f.write(feed_content)
        logger.info(f"✅ Main RSS feed created at {feed_path}")

        if publish:
            s3_feed_key = f"feeds/{feed_filename}"
            await upload_file_to_s3(S3_BUCKET_NAME, s3_feed_key, feed_path)
    return


async def execute_query_async(query: str, params: tuple = ()):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: execute_query(query, params))


async def fetch_bookmark_by_id(id: str) -> Optional[Bookmark]:
    query = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks WHERE id = ?"
    results = fetch_data(query, (id,))
    return results[0] if results else None


async def fetch_bookmark_by_url(url: str) -> Optional[Bookmark]:
    query = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks WHERE url = ?"
    results = fetch_data(query, (url,))
    return results[0] if results else None


async def upload_file_to_s3(bucket_name: str, s3_key: str, local_path: str):
    session = aioboto3.Session()
    async with session.client("s3") as s3:  # type: ignore
        try:
            # Determine content type based on file extension
            extra_args = {}
            if s3_key.endswith('.xml'):
                extra_args['ContentType'] = 'text/xml'
            elif s3_key.endswith('.xsl'):
                extra_args['ContentType'] = 'text/xsl'
            elif s3_key.endswith('.png'):
                extra_args['ContentType'] = 'image/png'
            elif s3_key.endswith('.jpg') or s3_key.endswith('.jpeg'):
                extra_args['ContentType'] = 'image/jpeg'
            elif s3_key.endswith('.db'):
                extra_args['ContentType'] = 'application/x-sqlite3'
            
            await s3.upload_file(local_path, bucket_name, s3_key, ExtraArgs=extra_args)
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
) -> Optional[int]:
    tags_json = json.dumps(tags)
    created_at = datetime.now(timezone.utc).isoformat()
    query = """
    INSERT INTO bookmarks (title, url, description, tags, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    try:
        _, last_row_id = execute_query(
            query,
            (title, url, description, tags_json, created_at, created_at),
        )

        if last_row_id is not None:
            bookmark_id = last_row_id
            logger.info(f"✅ Created bookmark with ID: {bookmark_id}")

            new_bookmark = await fetch_bookmark_by_id(str(bookmark_id))
            if new_bookmark:
                await schedule_thumbnail_fetch_and_save(new_bookmark)

            # Update the main RSS feed with all bookmarks
            await update_main_rss_feed()
            
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
    
    # Update the main RSS feed
    await update_main_rss_feed()


async def update_bookmark_title(id: str, title: str):
    query = """
    UPDATE bookmarks
    SET title = ?, updated_at = ?
    WHERE id = ?
    """
    updated_at = datetime.now(timezone.utc).isoformat()
    await execute_query_async(query, (title, updated_at, id))
    logger.info(f"✏️ Title updated for bookmark {id}")
    
    # Update the main RSS feed
    await update_main_rss_feed()


async def update_bookmark_tags(id: str, tags: List[str]):
    # Filter out empty tags
    tags = [tag for tag in tags if tag.strip()]
    tags_json = json.dumps(tags)

    query = "UPDATE bookmarks SET tags = ?, updated_at = ? WHERE id = ?"
    updated_at = datetime.now(timezone.utc).isoformat()
    await execute_query_async(query, (tags_json, updated_at, id))
    logger.info(f"🏷️ Tags updated for bookmark {id}")
    
    # Update the main RSS feed
    await update_main_rss_feed()


async def get_bookmark_thumbnail_image(bookmark: dict) -> str:
    if isinstance(bookmark, dict) and "thumbnail_url" in bookmark:
        img_url = bookmark["thumbnail_url"]
    else:
        logger.error(f"💥 Bookmark is not a valid dictionary: {bookmark}")
        return ""

    if img_url:
        logger.info(f"🎉 Found existing thumbnail URL for bookmark id {bookmark['id']}.")
        return img_url
    else:
        logger.info(f"🐕 Generating thumbnail for bookmark id {bookmark['id']}... ")
        
        s3_bucket = S3_BUCKET_NAME
        s3_key = f'thumbnails/{bookmark["id"]}.jpg'
        local_path = f'/tmp/{bookmark["id"]}.jpg'

        try:
            # Attempt to run shot-scraper
            process = await asyncio.create_subprocess_exec(
                "shot-scraper",
                bookmark["url"],
                "-o", local_path,
                "--width", "1280",
                "--height", "720",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_output = stderr.decode()
                if "Executable doesn't exist" in error_output and "Please run the following command to download new browsers" in error_output:
                    logger.info("Installing Playwright browsers...")
                    install_process = await asyncio.create_subprocess_exec("playwright", "install")
                    await install_process.communicate()
                    
                    # Retry shot-scraper after installation
                    process = await asyncio.create_subprocess_exec(
                        "shot-scraper",
                        bookmark["url"],
                        "-o", local_path,
                        "--width", "1280",
                        "--height", "720",
                    )
                    await process.communicate()
                else:
                    if process.returncode is not None:
                        raise subprocess.CalledProcessError(process.returncode, "shot-scraper", stderr=error_output)
                    else:
                        raise Exception(f"shot-scraper failed: {error_output}")

            # Upload to S3
            session = aioboto3.Session()
            async with session.client("s3") as s3:  # type: ignore
                with open(local_path, 'rb') as file_obj:
                    await s3.upload_fileobj(
                        file_obj,
                        s3_bucket,
                        s3_key,
                        ExtraArgs={"ContentType": "image/jpeg"},
                    )

            img_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"

            await update_bookmark_thumbnail_url(bookmark["id"], img_url)
            logger.info(f"🥳 Thumbnail for bookmark id # {bookmark['id']} successfully uploaded to S3!")
            
            # Clean up local file
            os.remove(local_path)
            
            return img_url
        except subprocess.CalledProcessError as e:
            logger.error(f"💥 Error generating thumbnail: {e}")
            return ""
        except Exception as e:
            logger.error(f"💥 Error uploading thumbnail to S3: {e}")
            return ""


async def update_bookmarks_with_thumbnails(bookmarks, schedule_s3_upload=True):
    tasks = []
    for bookmark in bookmarks:
        # Don't look up thumbnails for db entries we're just browsing
        source = bookmark.get("source")
        if source == "external":
            return bookmarks

        img_url = bookmark.get("thumbnail_url")
        if img_url in ('', None):
            if isinstance(bookmark, dict):
                task = asyncio.create_task(get_bookmark_thumbnail_image(bookmark))
                tasks.append(task)
            else:
                logger.error(f"💥 Bookmark is not a dictionary: {bookmark}")

    # Await all thumbnail fetching tasks
    thumbnails = await asyncio.gather(*tasks)

    for i, thumbnail_url in enumerate(thumbnails):
        if thumbnail_url:
            bookmarks[i]["thumbnail_url"] = thumbnail_url

    # Properly await the S3 upload
    if schedule_s3_upload:
        await schedule_upload_to_s3()
    return bookmarks

def create_rss_feed(
    bookmarks: List[Bookmark], tag: Optional[str] = None
) -> str:
    """Creates an RSS feed from a list of bookmarks."""
    try:
        sorted_bookmarks = sorted(
            [b for b in bookmarks if b],
            key=lambda x: x['created_at'],
            reverse=True
        )
        items = []
        for bookmark in sorted_bookmarks:
            if not bookmark:
                continue
                
            created_at = bookmark['created_at']
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            # Convert to local time and format as human-readable
            local_dt = dt.astimezone()
            hour = local_dt.hour
            minute = local_dt.minute
            am_pm = "am" if hour < 12 else "pm"
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12
            human_date = f"{local_dt.strftime('%A, %B %-d, %Y')} @ {display_hour}:{minute:02d}{am_pm}"
            # RFC 2822 format for standard RSS compatibility
            pub_date = local_dt.strftime('%a, %d %b %Y %H:%M:%S %z')

            title = bookmark.get('title', '').strip()
            title = clean_html(title) or "Untitled"

            description = bookmark.get('description', '').strip()
            description = clean_html(description)

            link = bookmark.get('url', '')
            link = safe_escape(link)

            thumbnail = bookmark.get('thumbnail_url', None)
            if thumbnail is None:
                thumbnail = "https://via.placeholder.com/200x200"
            
            # Generate category elements for tags
            tags = bookmark.get('tags', [])
            # Handle case where tags might be a string (shouldn't happen but just in case)
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags) if tags else []
                except (json.JSONDecodeError, TypeError):
                    tags = []
            # Ensure tags is a list and filter out empty tags
            if not isinstance(tags, list):
                tags = []
            tags = [tag.strip() for tag in tags if tag and str(tag).strip()]
            
            categories_xml = ""
            for tag in tags:
                # Escape XML special characters in tags
                escaped_tag = safe_escape(tag)
                categories_xml += f"<category>{escaped_tag}</category>\n                    "
            
            # Prepend human-readable date to description if description exists
            full_description = f"<p><em>{human_date}</em></p>{description}" if description else f"<p><em>{human_date}</em></p>"
            
            item = f"""
                <item>
                    <pubDate>{pub_date}</pubDate>
                    <title><![CDATA[{title}]]></title>
                    <link>{link}</link>
                    <description><![CDATA[{full_description}]]></description>
                    <enclosure url="{thumbnail}" type="image/jpeg" length="1000000" />
                    <guid isPermaLink="false">{link}</guid>
                    {categories_xml}
                </item>
            """
            items.append(item)

        channel_title = RSS_METADATA["title"]
        channel_link = RSS_METADATA.get("link", "")
        channel_description = RSS_METADATA.get("description", "")

        rss_items = []
        for item in items:
            rss_items.append(item)

        rss_items_str = "\n".join(rss_items)

        # Use RFC 2822 format for channel dates
        now = datetime.now().astimezone()
        rfc_date = now.strftime('%a, %d %b %Y %H:%M:%S %z')
        
        return f"""<?xml version="1.0" encoding="UTF-8" ?>
<?xml-stylesheet type="text/xsl" href="https://{S3_BUCKET_NAME}.s3.amazonaws.com/feeds/rss.xsl"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>{channel_title}</title>
    <link>{channel_link}</link>
    <description>{channel_description}</description>
    <language>en-us</language>
    <pubDate>{rfc_date}</pubDate>
    <lastBuildDate>{rfc_date}</lastBuildDate>
    <atom:link href="{RSS_METADATA.get('link', '')}/feeds/rss.xml" rel="self" type="text/xml" />
    <image>
        <url>https://{S3_BUCKET_NAME}.s3.amazonaws.com/{RSS_METADATA.get('logo', 'bookerics.png')}</url>
        <title>bookerics</title>
        <link>https://{S3_BUCKET_NAME}.s3.amazonaws.com/feeds/rss.xml</link>
        <width>128</width>
        <height>128</height>
    </image>
    {rss_items_str}
</channel>
</rss>
"""
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise e
