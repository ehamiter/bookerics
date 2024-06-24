import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8080"

# sqlite-web runs on a separate port
# poetry run sqlite_web bookerics.db -p 8888
UPDATE_BASE_URL = "http://localhost:8888/bookmarks/update/"

## Personalization
BOOKMARK_NAME = os.getenv("BOOKMARK_NAME", "bookeric")

### AWS
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_S3_BUCKET = "bookerics"

## Thumbnail API service
THUMBNAIL_API_KEY = os.getenv("THUMBNAIL_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
