import os
import shutil
import subprocess
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

from .ai import get_tags_and_description_from_bookmark_url
from .constants import (
    ADDITIONAL_DB_PATHS,
    BOOKMARK_NAME,
    LOCAL_BACKUP_PATH,
    RSS_FEED_CREATION_TAGS,
    RSS_METADATA,
    THUMBNAIL_API_KEY,
    FEEDS_DIR,
)

from .utils import log_warning_with_response, logger

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


def fetch_data(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
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


def fetch_bookmarks(kind: str) -> List[Dict[str, Any]]:
    bq = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM bookmarks "
    queries = {
        "newest": f"{bq} ORDER BY created_at DESC, updated_at DESC;",
        "oldest": f"{bq} ORDER BY created_at ASC, updated_at ASC;",
        "untagged": f"{bq} WHERE tags IS NULL OR tags = '[\"\"]' ORDER BY created_at DESC, updated_at DESC;",
    }
    query = queries.get(kind, queries["newest"])
    return fetch_data(query)


def search_bookmarks(query: str) -> List[Dict[str, Any]]:
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


def fetch_unique_tags(kind: str = "frequency") -> List[str]:
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
    return [row[0] for row in rows]


def fetch_bookmarks_by_tag(tag: str) -> List[Dict[str, Any]]:
    query = """
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source
    FROM bookmarks
    WHERE ? IN (SELECT value FROM json_each(bookmarks.tags))
    ORDER BY updated_at DESC, created_at DESC;
    """
    return fetch_data(query, (tag,))


async def delete_bookmark_by_id(bookmark_id: int) -> None:
    try:
        # Get the bookmark's tags before deletion
        bookmark = await fetch_bookmark_by_id(bookmark_id)
        if not bookmark:
            logger.warning(f"Bookmark {bookmark_id} not found for deletion")
            return

        # Delete the bookmark
        query = "DELETE FROM bookmarks WHERE id = ?"
        execute_query(query, (bookmark_id,))
        logger.info(f"☑️ Deleted bookmark id: {bookmark_id}")

        try:
            # Update RSS feeds with fresh bookmark list
            bookmarks = fetch_bookmarks(kind="newest")
            bookmarks = [bm for bm in bookmarks if bm and bm.get('source') == 'internal']
            if bookmarks:  # Only create feed if we have valid bookmarks
                asyncio.create_task(create_feed(tag=None, bookmarks=bookmarks, publish=True))
        except Exception as e:
            logger.error(f"Error scheduling RSS feed update: {e}")

        try:
            # Upload to S3
            asyncio.create_task(schedule_upload_to_s3())
        except Exception as e:
            logger.error(f"Error scheduling S3 upload: {e}")

    except Exception as e:
        logger.error(f"💥 Error in delete_bookmark_by_id: {e}")
        raise e


def backup_bookerics_db():
    src_path = S3_KEY
    today_str = datetime.now().strftime("%Y-%m-%d")
    dest_dir = LOCAL_BACKUP_PATH
    dest_path = os.path.join(dest_dir, f"{today_str}-{src_path}")

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    shutil.copy2(src_path, dest_path)
    logger.info(f"☑️ Backup created at {dest_path}")


async def schedule_upload_to_s3():
    """Schedule an S3 upload and return the task."""
    return await upload_file_to_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH)


async def schedule_feed_creation(tag, bookmarks, publish):
    """Schedule feed creation and return the task."""
    return await create_feed(tag=tag, bookmarks=bookmarks, publish=publish)


async def schedule_thumbnail_fetch_and_save(bookmark, schedule_s3_upload=True):
    """Schedule thumbnail fetching and return the task."""
    bookmarks = [bookmark]
    return await update_bookmarks_with_thumbnails(bookmarks, schedule_s3_upload=schedule_s3_upload)


def verify_table_structure(table_name: str = "bookmarks"):
    """
    /table web endpoint
    """
    query = f"PRAGMA table_info({table_name})"
    rows, _ = execute_query(query)
    return rows


# async
base_directory = os.path.dirname(os.path.abspath(__file__))
feeds_directory = os.path.join(base_directory, 'feeds')

async def get_file_size(url: str) -> int:
    async with aiohttp.ClientSession() as session:
        print(f"Requesting HEAD for URL: {url}")  # Debug print
        async with session.head(url) as response:
            file_size = response.headers.get('Content-Length')
            if file_size:
                return int(file_size)
            else:
                raise ValueError("Could not retrieve file size.")

async def push_changes_up(tag):
    local_repo_path = '/Users/eric/projects/bookerics-web-page'
    if tag:
        feed_source_path = os.path.join(feeds_directory, tag, 'rss.xml')
        feed_destination_path = os.path.join(local_repo_path, 'feeds', tag, 'rss.xml')
    else:
        feed_source_path = os.path.join(feeds_directory, 'rss.xml')
        feed_destination_path = os.path.join(local_repo_path, 'feeds', 'rss.xml')

    shutil.copy2(feed_source_path, feed_destination_path)

    os.chdir(local_repo_path)
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', 'Update RSS feed'])
    subprocess.run(['git', 'push', 'origin', 'main'])

DEFAULT_THUMBNAIL_URL = "https://bookerics.s3.amazonaws.com/thumbnails/1651.jpg"

async def create_feed(tag: Optional[str], bookmarks: List[Dict], publish: bool = False) -> None:
    """Create an RSS feed for the given tag (or main feed if tag is None)."""
    try:
        feed_path = os.path.join(FEEDS_DIR, 'rss.xml')
        
        # Create the feed content with updated XSL path
        feed = create_rss_feed(bookmarks, tag)
        
        # Save locally first
        with open(feed_path, 'w', encoding='utf-8') as f:
            f.write(feed)
        logger.info(f"Feed written successfully to {feed_path}")
        
        if publish:
            # Upload to S3 using aws cli
            process = await asyncio.create_subprocess_exec(
                'aws', 's3', 'cp',
                feed_path,
                f's3://{S3_BUCKET_NAME}/feeds/rss.xml',
                '--content-type', 'application/xml',
                '--cache-control', 'no-cache',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"RSS feed uploaded to S3: feeds/rss.xml")
            else:
                logger.error(f"Error uploading RSS feed to S3: {stderr.decode()}")
                raise Exception(stderr.decode())
            
    except Exception as e:
        logger.error(f"Error creating feed: {e}")
        raise e


async def execute_query_async(query: str, params: tuple = ()):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, execute_query, query, params)

async def fetch_bookmark_by_id(id: str) -> Dict[str, Any]:
    query = f"SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM bookmarks WHERE id='{id}' LIMIT 1;"
    results = fetch_data(query)
    bookmark = {} if not results else results[0]
    return bookmark

async def fetch_bookmark_by_url(url: str) -> Dict[str, Any]:
    query = f"SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at, 'internal' AS source FROM bookmarks WHERE url='{url}' LIMIT 1;"
    results = fetch_data(query)
    bookmark = {} if not results else results[0]
    bookmark = bookmark if bookmark.get('source') == 'internal' else {}
    return bookmark


async def upload_file_to_s3(bucket_name, s3_key, local_path):
    try:
        # Run AWS CLI command asynchronously
        process = await asyncio.create_subprocess_exec(
            'aws', 's3', 'cp',
            local_path,
            f's3://{bucket_name}/{s3_key}',
            '--content-type', 'application/xml',
            '--cache-control', 'no-cache',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info(f"☑️ Uploaded {local_path} to bucket {bucket_name}/{s3_key}")
        else:
            logger.error(f"💥 Error uploading to S3: {stderr.decode()}")
            
    except Exception as e:
        logger.error(f"💥 Error running aws command: {e}")


async def wait_for_thumbnail(bookmark_id: int, max_retries: int = 5) -> Optional[dict]:
    """Wait for thumbnail to be available with retries."""
    for attempt in range(max_retries):
        bookmark = await fetch_bookmark_by_id(bookmark_id)
        if bookmark and bookmark.get('thumbnail_url'):
            return bookmark
        await asyncio.sleep(1)  # Wait 1 second between attempts
    return None

async def create_bookmark(title: str, url: str, description: str, tags: List[str]) -> dict:
    try:
        # We get both from AI in the same call so if there's one missing, generate them both
        if tags == [""] or not description:
            try:
                _tags, _description = await get_tags_and_description_from_bookmark_url(url)
                # Only use AI-generated values if the user didn't provide them
                tags = _tags if tags == [""] else tags
                description = _description if not description else description
            except Exception as e:
                logger.error(f"Error generating AI tags/description: {e}")
                # Use defaults if AI generation fails
                tags = tags if tags != [""] else [""]
                description = description if description else url

        # Save the bookmark first
        tags_json = json.dumps(tags)
        current_timestamp = datetime.utcnow().isoformat()
        query = """
        INSERT INTO bookmarks (title, url, description, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        _, bookmark_id = execute_query(
            query,
            (title, url, description, tags_json, current_timestamp, current_timestamp),
        )
        bookmark = await fetch_bookmark_by_id(bookmark_id)

        try:
            # Generate and upload thumbnail
            await schedule_thumbnail_fetch_and_save(bookmark, schedule_s3_upload=True)
            
            # Wait for thumbnail to be ready
            updated_bookmark = await wait_for_thumbnail(bookmark_id)
            if not updated_bookmark:
                logger.warning(f"Thumbnail not ready after retries for bookmark {bookmark_id}")
                return bookmark
            
            # Now create and upload the RSS feed
            bookmarks = fetch_bookmarks(kind="newest")
            bookmarks = [bm for bm in bookmarks if bm.get('source') == 'internal']
            await create_feed(tag=None, bookmarks=bookmarks, publish=True)
            
            # Finally, upload the database
            await schedule_upload_to_s3()
            
            return updated_bookmark
            
        except Exception as e:
            logger.error(f"Error in background tasks: {e}")
            return bookmark
        
    except Exception as e:
        logger.error(f"Error in create_bookmark: {e}")
        raise e



async def update_bookmark_thumbnail_url(bookmark_id: int, img_url: str):
    query = """
    UPDATE bookmarks
    SET thumbnail_url = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.now(timezone.utc).isoformat()
    params = (img_url, current_timestamp, bookmark_id)
    await execute_query_async(query, params)


async def update_bookmark_description(bookmark_id: int, description: str):
    query = """
    UPDATE bookmarks
    SET description = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.now(timezone.utc).isoformat()
    params = (description, current_timestamp, bookmark_id)
    await execute_query_async(query, params)

async def update_bookmark_title(bookmark_id: int, title: str):
    query = """
    UPDATE bookmarks
    SET title = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.now(timezone.utc).isoformat()
    params = (title, current_timestamp, bookmark_id)
    await execute_query_async(query, params)


async def update_bookmark_tags(bookmark_id: int, tags: List[str]):
    # Filter out empty tags
    tags = [tag for tag in tags if tag.strip()]
    tags_json = json.dumps(tags)

    update_query = """
    UPDATE bookmarks
    SET tags = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.utcnow().isoformat()
    update_params = (tags_json, current_timestamp, bookmark_id)

    await execute_query_async(update_query, update_params)


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
                "--height", "800",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_output = stderr.decode()
                if "Executable doesn't exist" in error_output and "Please run the following command to download new browsers" in error_output:
                    logger.info("Installing Playwright browsers...")
                    await asyncio.create_subprocess_exec("playwright", "install", check=True)
                    
                    # Retry shot-scraper after installation
                    process = await asyncio.create_subprocess_exec(
                        "shot-scraper",
                        bookmark["url"],
                        "-o", local_path,
                        "--width", "480",
                        check=True
                    )
                    await process.communicate()
                else:
                    raise subprocess.CalledProcessError(process.returncode, "shot-scraper", stderr=error_output)

            # Upload to S3
            session = aioboto3.Session()
            async with session.client("s3") as s3:
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
    await schedule_upload_to_s3()
    return bookmarks

def create_rss_feed(bookmarks: List[Dict], tag: Optional[str] = None) -> str:
    """Create RSS feed content from bookmarks."""
    rss_items = []
    for bookmark in bookmarks:
        if not isinstance(bookmark, dict):
            logger.warning(f"Skipping invalid bookmark: {bookmark}")
            continue
            
        title = escape(str(bookmark.get('title', '')))
        link = escape(str(bookmark.get('url', '')))
        description = escape(str(bookmark.get('description', '')))
        pub_date = bookmark.get('created_at', '')
        
        # Handle None values for thumbnail_url more defensively
        thumbnail_url = bookmark.get('thumbnail_url')
        thumbnail = escape(str(thumbnail_url)) if thumbnail_url is not None else ''
        
        # Add thumbnail as media:content if available
        thumbnail_element = f'<media:content url="{thumbnail}" type="image/jpeg" />' if thumbnail else ''
        
        item = f"""
        <item>
            <title>{title}</title>
            <link>{link}</link>
            <description>{description}</description>
            <pubDate>{pub_date}</pubDate>
            <guid>{link}</guid>
            {thumbnail_element}
        </item>
        """
        rss_items.append(item)

    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <?xml-stylesheet type="text/xsl" href="rss.xsl"?>
    <rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
        <channel>
            <title>bookerics{f' - {tag}' if tag else ''}</title>
            <link>https://bookerics.s3.amazonaws.com/feeds/rss.xml</link>
            <description>bookmarks, but for Erics</description>
            <language>en-us</language>
            {''.join(rss_items)}
        </channel>
    </rss>
    """
    
    return rss_content
