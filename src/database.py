import json
import sqlite3
from typing import Dict, List

DB_PATH = "bookerics.db"

def fetch_data(query: str, params: tuple = ()) -> List[Dict[str, str]]:
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
    if kind == "all":
        query = "SELECT title, url, description, tags FROM bookmarks;"
    elif kind == "random":
        query = "SELECT title, url, description, tags FROM bookmarks ORDER BY RANDOM() LIMIT 1;"
    elif kind == "untagged":
        query = "SELECT title, url, description, tags FROM bookmarks WHERE tags IS NULL OR tags = '[\"\"]';"
    elif kind == "oldest":
        query = "SELECT title, url, description, tags FROM bookmarks ORDER BY created_at ASC;"
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
    query = "SELECT DISTINCT json_each.value FROM bookmarks, json_each(bookmarks.tags);"
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
