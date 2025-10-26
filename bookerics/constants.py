import os

from dotenv import load_dotenv

load_dotenv()

## Personalization
BOOKMARK_NAME = os.getenv("BOOKMARK_NAME", "bookeric")

# RSS feed metadata
RSS_METADATA = {
    "id": os.getenv("RSS_ID", "https://localhost:50113/"),
    "title": os.getenv("RSS_TITLE", f"{BOOKMARK_NAME}s"),
    "description": os.getenv("RSS_DESCRIPTION", f"{BOOKMARK_NAME}s collection"),
    "author": {
        "name": os.getenv("RSS_AUTHOR_NAME", "Your Name"), 
        "email": os.getenv("RSS_AUTHOR_EMAIL", "your@email.com")
    },
    "link": os.getenv("RSS_LINK", "https://localhost:50113"),
    "logo": os.getenv("RSS_LOGO", f"{BOOKMARK_NAME}s.png"),
    "language": os.getenv("RSS_LANGUAGE", "en"),
}

### Local backups
LOCAL_BACKUP_PATH = os.getenv("LOCAL_BACKUP_PATH")

### Feral hosting info
FERAL_SERVER = os.getenv("FERAL_SERVER")
FERAL_USERNAME = os.getenv("FERAL_USERNAME")
FERAL_PASSWORD = os.getenv("FERAL_PASSWORD")
FERAL_BASE_URL = "https://geryon.feralhosting.com/eddielomax"
FERAL_FEEDS_PATH = "/media/sdc1/eddielomax/www/eddielomax.geryon/public_html/feeds"
FERAL_THUMBNAILS_PATH = "/media/sdc1/eddielomax/www/eddielomax.geryon/public_html/thumbnails"

## Giphy API service
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

## OpenAI
BOOKERICS_OPENAI_KEY = os.getenv("BOOKERICS_OPENAI_KEY")
GPT_MODEL = "gpt-4o"
TAG_GPT_MODEL = "gpt-3.5-turbo"

# Define the feeds directory relative to the project root
FEEDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'feeds')

# Create the directory if it doesn't exist
os.makedirs(FEEDS_DIR, exist_ok=True)
