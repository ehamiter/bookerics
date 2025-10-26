#!/usr/bin/env python3
"""Migrate thumbnail URLs to bookerics.com."""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import from bookerics
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookerics.constants import FERAL_BASE_URL

DB_PATH = Path(__file__).parent.parent / "bookerics.db"


def migrate_urls():
    """Update all old thumbnail URLs to bookerics.com URLs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find all bookmarks with old URLs (S3 or FeralHosting)
    cursor.execute(
        """SELECT id, thumbnail_url FROM bookmarks 
           WHERE thumbnail_url LIKE '%bookerics.s3.amazonaws.com%' 
           OR thumbnail_url LIKE '%geryon.feralhosting.com%'"""
    )
    results = cursor.fetchall()

    print(f"Found {len(results)} bookmarks with old URLs")

    for bookmark_id, old_url in results:
        # Extract the filename from the old URL
        if "/thumbnails/" in old_url:
            filename = old_url.split("/thumbnails/")[1]
            new_url = f"{FERAL_BASE_URL}/thumbnails/{filename}"

            cursor.execute(
                "UPDATE bookmarks SET thumbnail_url = ? WHERE id = ?",
                (new_url, bookmark_id),
            )
            print(f"Updated bookmark {bookmark_id}: {filename}")

    conn.commit()
    conn.close()
    print(f"✅ Migration complete! Updated {len(results)} bookmarks")


if __name__ == "__main__":
    migrate_urls()
