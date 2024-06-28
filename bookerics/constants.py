import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8080"

# sqlite-web runs on a separate port
# poetry run sqlite_web bookerics.db -p 8888 -x
UPDATE_BASE_URL = "http://localhost:8888/bookmarks/update"

## Personalization
BOOKMARK_NAME = os.getenv("BOOKMARK_NAME", "bookeric")

### AWS
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

## Thumbnail API service
THUMBNAIL_API_KEY = os.getenv("THUMBNAIL_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

## OpenAI
BOOKERICS_OPENAI_KEY = os.getenv("BOOKERICS_OPENAI_KEY")
GPT_MODEL = "gpt-4o"

## Additional DBs
ADDITIONAL_DB_PATHS = os.getenv("ADDITIONAL_DB_PATHS", "").split(",")
ADDITIONAL_DB_PATHS = [path.strip() for path in ADDITIONAL_DB_PATHS if path.strip()]
