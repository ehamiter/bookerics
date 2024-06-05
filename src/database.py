import sqlite3
import json
from typing import List, Dict

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
        bookmarks.append({
            "title": title,
            "url": url,
            "description": description,
            "tags": tags
        })

    return bookmarks

def fetch_bookmarks() -> List[Dict[str, str]]:
    query = "SELECT title, url, description, tags FROM bookmarks"
    return fetch_data(query)

def fetch_random_bookmark() -> Dict[str, str]:
    query = "SELECT title, url, description, tags FROM bookmarks ORDER BY RANDOM() LIMIT 1"
    bookmarks = fetch_data(query)
    return bookmarks[0] if bookmarks else {}

def fetch_untagged_bookmarks() -> List[Dict[str, str]]:
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
