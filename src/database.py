import asyncio
import json
import os
import sqlite3
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List

import aioboto3
import aiohttp
import boto3
from PIL import Image

from src.constants import BOOKMARK_NAME, THUMBNAIL_API_KEY
from src.utils import log_warning_with_response, logger

# S3/DB setup
S3_BUCKET_NAME = f"{BOOKMARK_NAME}s"
S3_KEY = f"{BOOKMARK_NAME}s.db"
DB_PATH = f"./{BOOKMARK_NAME}s.db"


def download_file_from_s3(bucket_name, s3_key, local_path):
    s3 = boto3.client("s3")
    try:
        s3.download_file(bucket_name, s3_key, local_path)
        logger.info(f"Downloaded {s3_key} from bucket {bucket_name} to {local_path}")
    except Exception as e:
        logger.error(f"Error downloading file from S3: {e}")


def load_db_on_startup():
    logger.info("Bookerics starting up…")
    # Download the database file from S3
    if not os.path.exists(DB_PATH):
        download_file_from_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH)
    logger.info("Database loaded!")


def execute_query(query: str, params: tuple = ()) -> Any:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    last_row_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return result, last_row_id


def fetch_data(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
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
            logger.error(f"Unexpected row format: {row}")
    return bookmarks


def fetch_bookmark_by_id(id: str) -> List[Dict[str, Any]]:
    query = f"SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks WHERE id='{id}' LIMIT 1;"
    return fetch_data(query)


def fetch_bookmarks(kind: str) -> List[Dict[str, Any]]:
    queries = {
        "newest": "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks ORDER BY created_at DESC;",
        "oldest": "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks ORDER BY created_at ASC;",
        "random": "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks ORDER BY RANDOM();",
        "untagged": "SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at FROM bookmarks WHERE tags IS NULL OR tags = '[\"\"]' ORDER BY created_at DESC;",
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
    ORDER BY created_at DESC;
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
        ORDER BY bookmarks.created_at DESC;
        """
    rows, _ = execute_query(query)
    return [row[0] for row in rows]


def fetch_bookmarks_by_tag(tag: str) -> List[Dict[str, Any]]:
    query = """
    SELECT id, title, url, thumbnail_url, description, tags, created_at, updated_at
    FROM bookmarks
    WHERE ? IN (SELECT value FROM json_each(bookmarks.tags))
    ORDER BY created_at DESC;
    """
    return fetch_data(query, (tag,))


async def upload_file_to_s3(bucket_name, s3_key, local_path):
    session = aioboto3.Session()
    async with session.client("s3") as s3:
        try:
            await s3.upload_file(local_path, bucket_name, s3_key)
            logger.info(
                f"Uploaded {local_path} to bucket {bucket_name} with key {s3_key}"
            )
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")


def schedule_upload_to_s3():
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(upload_file_to_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH))
    else:
        asyncio.run(upload_file_to_s3(S3_BUCKET_NAME, S3_KEY, DB_PATH))


def schedule_thumbnail_fetch_and_save(bookmark):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(update_bookmarks_with_thumbnails(bookmark))
    else:
        asyncio.run(update_bookmarks_with_thumbnails(bookmark))


def create_bookmark(title: str, url: str, description: str, tags: List[str]) -> int:
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
    # breakpoint()
    schedule_upload_to_s3()
    bookmark = fetch_bookmark_by_id(bookmark_id)
    schedule_thumbnail_fetch_and_save(bookmark)
    return bookmark_id


def delete_bookmark_by_id(bookmark_id: int) -> None:
    try:
        query = "DELETE FROM bookmarks WHERE id = ?"
        execute_query(query, (bookmark_id,))
        logger.info(f"Deleted bookmark id: {bookmark_id}")
        schedule_upload_to_s3()
    except Exception as e:
        logger.error(f"Error deleting bookmark with id {bookmark_id}: {e}")
        raise e


# Fetch image preview thumbnails
async def update_bookmark_thumbnail_url(bookmark_id: int, img_url: str):
    query = """
    UPDATE bookmarks
    SET thumbnail_url = ?, updated_at = ?
    WHERE id = ?
    """
    current_timestamp = datetime.utcnow().isoformat()
    params = (img_url, current_timestamp, bookmark_id)
    await execute_query_async(query, params)


async def execute_query_async(query: str, params: tuple = ()):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, execute_query, query, params)


async def get_bookmark_thumbnail_image(bookmark: dict) -> str:
    img_url = bookmark.get("thumbnail_url")

    if img_url:
        logger.info(
            f"🎉 Found existing thumbnail URL for bookmark id {bookmark['id']}: {img_url}"
        )
        return img_url

    else:
        logger.info(
            f"🐕 Fetching thumbnail url from API for bookmark id {bookmark['id']}... "
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
                        f"🥳 Thumbnail for bookmark id # {bookmark["id"]} successfully uploaded to S3!"
                    )
                    return img_url
                else:
                    await log_warning_with_response(response)

    return img_url


async def update_bookmarks_with_thumbnails(bookmarks):
    logger.info("Starting update of bookmarks with thumbnails.")
    tasks = [get_bookmark_thumbnail_image(bm) for bm in bookmarks]
    thumbnails = await asyncio.gather(*tasks)
    for bm, thumbnail_url in zip(bookmarks, thumbnails):
        bm["thumbnail_url"] = thumbnail_url
    logger.info("Completed update of bookmarks with thumbnails.")
    return bookmarks


def verify_table_structure(table_name: str = "bookmarks"):
    """
    /table web endpoint
    """
    query = f"PRAGMA table_info({table_name})"
    rows, _ = execute_query(query)
    return rows
