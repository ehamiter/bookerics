import asyncio
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List

import aioboto3
import boto3

from src.utils import logger

BOOKMARK_NAME = "bookeric"  # change to your name for the ultimate in personalizatiom

# S3/DB setup
S3_BUCKET_NAME = f"{BOOKMARK_NAME}s"
S3_KEY = f"{BOOKMARK_NAME}s.db"
DB_PATH = f"/tmp/{BOOKMARK_NAME}s.db"


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


def execute_query(query: str, params: tuple = ()) -> None:
    # executes query and ends-- used for POSTing and no expected response
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    connection.commit()
    connection.close()


def fetch_data(query: str, params: tuple = ()) -> List[Dict[str, str]]:
    # executes query and fetches bookmarks-- used for retrieval
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()

    bookmarks = []
    for row in rows:
        if len(row) == 4:
            title, url, description, tags_json = row
            try:
                tags = json.loads(tags_json) if tags_json else []
                if tags == [""]:
                    tags = []
            except json.JSONDecodeError:
                tags = []
            bookmarks.append(
                {"title": title, "url": url, "description": description, "tags": tags}
            )
        else:
            logger.error(f"Unexpected row format: {row}")

    return bookmarks


def fetch_bookmarks(kind: str) -> List[Dict[str, str]]:
    queries = {
        "newest": "SELECT title, url, description, tags FROM bookmarks ORDER BY created_at DESC;",
        "oldest": "SELECT title, url, description, tags FROM bookmarks ORDER BY created_at ASC;",
        "random": "SELECT title, url, description, tags FROM bookmarks ORDER BY RANDOM();",
        "untagged": "SELECT title, url, description, tags FROM bookmarks WHERE tags IS NULL OR tags = '[\"\"]' ORDER BY created_at DESC;",
    }

    query = queries.get(kind, queries["newest"])

    return fetch_data(query)


def search_bookmarks(query: str) -> List[Dict[str, str]]:
    search_query = f"%{query}%"
    query = f"""
    SELECT title, url, description, tags
    FROM bookmarks
    WHERE title LIKE '{search_query}'
    OR url LIKE '{search_query}'
    OR description LIKE '{search_query}'
    OR tags LIKE '{search_query}';
    """
    return fetch_data(query)


def fetch_unique_tags(kind: str = "frequency") -> List[str]:
    # by tag frequency
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
    # by newness
    elif kind == "newest":
        query = """
        SELECT DISTINCT json_each.value
        FROM bookmarks, json_each(bookmarks.tags)
        WHERE json_each.value IS NOT NULL
          AND json_each.value != ''
          AND json_each.value != '[""]'
        ORDER BY bookmarks.created_at DESC;
        """

    # execute it
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    connection.close()
    return [row[0] for row in rows]


def fetch_bookmarks_by_tag(tag: str) -> List[Dict[str, str]]:
    query = """
    SELECT title, url, description, tags
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


def create_bookmark(title: str, url: str, description: str, tags: List[str]) -> None:
    tags_json = json.dumps(tags)
    current_timestamp = datetime.utcnow().isoformat()
    query = """
    INSERT INTO bookmarks (title, url, description, tags, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    execute_query(
        query,
        (title, url, description, tags_json, current_timestamp, current_timestamp),
    )

    # Schedule the upload of the database file to S3 asynchronously
    schedule_upload_to_s3()


def verify_table_structure(table_name: str = "bookmarks"):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    connection.close()
    return columns
