from datetime import datetime
import json
import sqlite3
from typing import Dict, List

DB_PATH = "bookerics.db"


# GETs

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
            print(f"Unexpected row format: {row}")

    return bookmarks


def fetch_bookmarks(kind: str) -> List[Dict[str, str]]:
    if kind == "newest":
        query = "SELECT title, url, description, tags FROM bookmarks ORDER BY created_at DESC;"
    elif kind == "oldest":
        query = "SELECT title, url, description, tags FROM bookmarks ORDER BY created_at ASC;"
    elif kind == "random":
        query = "SELECT title, url, description, tags FROM bookmarks ORDER BY RANDOM() LIMIT 1;"
    elif kind == "untagged":
        query = "SELECT title, url, description, tags FROM bookmarks WHERE tags IS NULL OR tags = '[\"\"]';"
    else:
        query = "SELECT 0 FROM bookmarks;"
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


def fetch_unique_tags() -> List[str]:
    query = """
    SELECT DISTINCT json_each.value
    FROM bookmarks, json_each(bookmarks.tags)
    WHERE json_each.value IS NOT NULL
    AND json_each.value != ''
    AND json_each.value != '[""]';
    """
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
    WHERE ? IN (SELECT value FROM json_each(bookmarks.tags));
    """
    return fetch_data(query, (tag,))

# POSTs

def create_bookmark(title: str, url: str, description: str, tags: List[str]) -> None:
    tags_json = json.dumps(tags)
    current_timestamp = datetime.utcnow().isoformat()
    query = """
    INSERT INTO bookmarks (title, url, description, tags, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    execute_query(query, (title, url, description, tags_json, current_timestamp, current_timestamp))


# utils

def verify_table_structure(table_name: str):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    connection.close()
    return columns


if __name__ == "__main__":
    table_name = "bookmarks"
    structure = verify_table_structure(table_name)
    for column in structure:
        print(column)
