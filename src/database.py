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

    return bookmarks


def fetch_bookmarks(kind: str) -> List[Dict[str, str]]:
    if not kind:
        query = "SELECT title, url, description, tags FROM bookmarks"
    if kind == "random":
        query = "SELECT title, url, description, tags FROM bookmarks ORDER BY RANDOM() LIMIT 1"
    elif kind == "untagged":
        query = "SELECT title, url, description, tags FROM bookmarks WHERE tags IS NULL OR tags = '[\"\"]'"
    return fetch_data(query)


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
