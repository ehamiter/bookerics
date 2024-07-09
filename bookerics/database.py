import asyncio
import json
import os
import shutil
import sqlite3
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Tuple

import aioboto3
import aiohttp
import boto3
from PIL import Image

from .ai import get_tags_and_description_from_bookmark_url
from .constants import (
    ADDITIONAL_DB_PATHS,
    BOOKMARK_NAME,
    LOCAL_BACKUP_PATH,
    THUMBNAIL_API_KEY,
)
from .utils import log_warning_with_response, logger

# S3/DB setup
S3_BUCKET_NAME = f"{BOOKMARK_NAME}s"
S3_KEY = f"{BOOKMARK_NAME}s.db"
DB_PATH = f"./{BOOKMARK_NAME}s.db"


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
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    if allow_external_db:
        # params are passed in to fetch thumbnails, so do not attach additional dbs if that is the case
        if not params and ADDITIONAL_DB_PATHS:
            query = enter_the_multiverse(query, cursor, table_name)

    try:
        cursor.execute(query, params)
        result = cursor.fetchall()
        last_row_id = cursor.lastrowid
        connection.commit()
    except Exception as e:
        logger.error(
            f"💥 Error executing query: {query}\nParams: {params}\nException: {e}"
        )
        raise
    finally:
        connection.close()

    return result, last_row_id


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
    bq = "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks "
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
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at
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
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at
    FROM bookmarks
    WHERE ? IN (SELECT value FROM json_each(bookmarks.tags))
    ORDER BY updated_at DESC, created_at DESC;
    """
    return fetch_data(query, (tag,))


def delete_bookmark_by_id(bookmark_id: int) -> None:
    try:
        query = "DELETE FROM bookmarks WHERE id = ?"
        execute_query(query, (bookmark_id,))
        logger.info(f"☑️ Deleted bookmark id: {bookmark_id}")
        schedule_upload_to_s3()
    except Exception as e:
        logger.error(f"💥 Error deleting bookmark with id {bookmark_id}: {e}")
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


def schedule_upload_to_s3():
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(upload_file_to_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH))
    else:
        asyncio.run(upload_file_to_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH))


def schedule_thumbnail_fetch_and_save(bookmark):
    bookmarks = [bookmark]
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(update_bookmarks_with_thumbnails(bookmarks))
    else:
        asyncio.run(update_bookmarks_with_thumbnails(bookmarks))


def verify_table_structure(table_name: str = "bookmarks"):
    """
    /table web endpoint
    """
    query = f"PRAGMA table_info({table_name})"
    rows, _ = execute_query(query)
    return rows


# async

async def execute_query_async(query: str, params: tuple = ()):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, execute_query, query, params)

async def fetch_bookmark_by_id(id: str) -> Dict[str, Any]:
    query = f"SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks WHERE id='{id}' LIMIT 1;"
    results = fetch_data(query)
    bookmark = {} if not results else results[0]
    return bookmark

async def fetch_bookmark_by_url(url: str) -> Dict[str, Any]:
    query = f"SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks WHERE url='{url}' LIMIT 1;"
    results = fetch_data(query)
    bookmark = {} if not results else results[0]
    bookmark = bookmark if bookmark.get('source') == 'internal' else {}
    return bookmark


async def upload_file_to_s3(bucket_name, s3_key, local_path):
    session = aioboto3.Session()
    async with session.client("s3") as s3:
        try:
            await s3.upload_file(local_path, bucket_name, s3_key)
            logger.info(
                f"☑️ Uploaded {local_path} to bucket {bucket_name} with key {s3_key}"
            )
        except Exception as e:
            logger.error(f"💥 Error uploading file to S3: {e}")


async def create_bookmark(
    title: str, url: str, description: str, tags: List[str]
) -> dict:

    # We get both from AI in the same call so if there's one missing, generate them both
    if tags == [""] or not description:
        _tags, _description = await get_tags_and_description_from_bookmark_url(url)

    tags = _tags if tags == [""] else tags
    description = _description if not description else description

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

    schedule_thumbnail_fetch_and_save(bookmark)
    schedule_upload_to_s3()
    return bookmark



async def update_bookmark_thumbnail_url(bookmark_id: int, img_url: str):
    query = """
    UPDATE bookmarks
    SET thumbnail_url = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.utcnow().isoformat()
    params = (img_url, current_timestamp, bookmark_id)
    await execute_query_async(query, params)


async def update_bookmark_description(bookmark_id: int, description: str):
    query = """
    UPDATE bookmarks
    SET description = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.utcnow().isoformat()
    params = (description, current_timestamp, bookmark_id)
    await execute_query_async(query, params)

async def update_bookmark_title(bookmark_id: int, title: str):
    query = """
    UPDATE bookmarks
    SET title = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.utcnow().isoformat()
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
        # Handle cases where bookmark is not as expected (log, raise error, etc.)
        logger.error(f"💥 Bookmark is not a valid dictionary: {bookmark}")
        return ""

    if img_url:
        logger.info(
            f"🎉 Found existing thumbnail URL for bookmark id {bookmark['id']}."
        )
        return img_url
    else:
        logger.info(
            f"🐕 Fetching thumbnail URL from API for bookmark id {bookmark['id']}... "
        )
        api_root = f"https://api.thumbnail.ws/api/{THUMBNAIL_API_KEY}/thumbnail/get"
        api_img_url = f'{api_root}?width=480&url={bookmark["url"]}'

        async with aiohttp.ClientSession() as session:
            async with session.get(api_img_url) as response:
                if response.status == 200:
                    logger.info(
                        f"🤝 Thumbnail API handshake successful for bookmark id {bookmark['id']}!"
                    )
                    img_bytes = await response.read()
                    img = Image.open(BytesIO(img_bytes))

                    # Save the image to a BytesIO object
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format="JPEG")
                    img_byte_arr.seek(0)

                    # Upload to S3
                    session = aioboto3.Session()
                    async with session.client("s3") as s3:
                        s3_bucket = S3_BUCKET_NAME
                        s3_key = f'thumbnails/{bookmark["id"]}.jpg'
                        await s3.upload_fileobj(
                            img_byte_arr,
                            s3_bucket,
                            s3_key,
                            ExtraArgs={"ContentType": "image/jpeg"},
                        )

                        img_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"

                    await update_bookmark_thumbnail_url(bookmark["id"], img_url)
                    logger.info(
                        f"🥳 Thumbnail for bookmark id # {bookmark['id']} successfully uploaded to S3!"
                    )
                    return img_url
                else:
                    await log_warning_with_response(response)

    return img_url


async def update_bookmarks_with_thumbnails(bookmarks):
    tasks = []
    for bookmark in bookmarks:
        # Don't look up thumbnails for db entries we're just browsing
        source = bookmark.get("source")
        if source == "external":
            return bookmarks

        img_url = bookmark.get("thumbnail_url")
        if img_url is None:
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

    return bookmarks
