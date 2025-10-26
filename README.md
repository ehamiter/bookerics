# `bookerics`

> bookmarks, but for Erics

**`bookerics`** is a modern, self-hosted bookmark manager that combines simplicity with powerful features. Think of it as a personal alternative to [Pinboard](https://pinboard.in/) with intelligent tagging, automatic screenshots, RSS feeds, and cloud synchronization.

![Screenshot](bookerics/static/images/screenshot.webp)

## ✨ Features

### 📚 Core Functionality
- **Smart Bookmark Management** - Save, organize, and search your bookmarks with ease
- **Automatic Screenshots** - Visual previews of your bookmarks using website thumbnails
- **AI-Powered Tagging** - Intelligent tag suggestions using OpenAI's GPT models
- **Full-Text Search** - Search through titles, descriptions, and tags
- **RSS Feed Generation** - Automated RSS feeds for all bookmarks or specific tags
- **Archive.ph Integration** - Automatic archival of bookmarked URLs

### 🎨 User Experience
- **Keyboard Shortcuts** - Navigate and manage bookmarks without touching your mouse
- **Dark/Light Theme Toggle** - Comfortable viewing in any lighting condition
- **Infinite Scroll** - Seamless browsing through large bookmark collections
- **Responsive Design** - Works beautifully on desktop and mobile devices
- **Browser Extension** - One-click bookmark saving with pre-filled metadata

### 🔧 Technical Features
- **SFTP Integration** - Automatic screenshot storage and RSS feed distribution
- **Multiple View Modes** - Newest, oldest, untagged, and tag-filtered views
- **Customizable Branding** - Easily personalize for your name (booktoms, bookzendayas, etc.)

## 🏗️ Architecture & Tech Stack

### Backend
- **[FastHTML](https://fastht.ml/)** - Modern Python web framework (previously Ludic)
- **SQLite** - Lightweight, file-based database with thread-local connections
- **OpenAI API** - AI-powered tag generation and content analysis
- **shot-scraper** - Website screenshot generation using Playwright
- **asyncssh** - Async SFTP integration

### Frontend
- **[HTMX](https://htmx.org/)** - Dynamic frontend interactions without JavaScript complexity
- **Vanilla JavaScript** - Custom keyboard shortcuts and UI enhancements
- **Modern CSS** - Responsive design with dark/light theme support

### Infrastructure
- Cloud storage for screenshots and RSS feeds via SFTP
- Chrome/Firefox extensions for quick bookmark saving

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Web hosting account (optional, for cloud storage of screenshots and RSS feeds)
- OpenAI API key (optional, for AI tagging)

### Installation

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/ehamiter/bookerics.git
cd bookerics

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Install dependencies
uv sync

# Run the application
uv run bookerics
```

The application will be available at `http://localhost:50113`

### Environment Configuration

Create a `.env` file with your settings:

```env
# Basic Configuration
BOOKMARK_NAME=bookeric  # Customize your bookmark terminology

# RSS Feed Configuration
RSS_ID="https://bookyournames.com/"
RSS_TITLE="bookerics"
RSS_DESCRIPTION="bookmarks, but for Your Names"
RSS_AUTHOR_NAME="Your Name"
RSS_AUTHOR_EMAIL="yourname@bookyournames.com"
RSS_LINK="https://bookyournames.com"
RSS_LOGO="bookyournames.png"
RSS_LANGUAGE="en"

# Hosting (for screenshot and RSS feed storage)
BOOKERICS_SERVER=your-server.somehosting.com
BOOKERICS_USERNAME=your-username
BOOKERICS_PASSWORD=your-password

# OpenAI (for AI tagging)
BOOKERICS_OPENAI_KEY=your-openai-api-key

# Optional: Giphy (for placeholder images)
GIPHY_API_KEY=your-giphy-api-key

# Optional: Local backups
LOCAL_BACKUP_PATH=/path/to/backup/directory
```

## 📱 Browser Extension

`bookerics` includes browser extensions for Chrome and Firefox that enable one-click bookmark saving:

### Chrome Extension
```bash
cd tools/bookerics_browser_extension
# Load as unpacked extension in Chrome developer mode
```

### Firefox Extension
```bash
cd tools/bookerics_firefox_extension
# Load as temporary add-on in Firefox
```

**Usage**: Click the extension icon or press `Cmd+D` to open a bookmark modal pre-filled with the current page's title and description.

## ⌨️ Keyboard Shortcuts

### Navigation
- **J** - Navigate down to the next bookmark
- **K** - Navigate up to the previous bookmark

### Actions
- **V** - Open the selected bookmark's URL in a new browser tab
- **E** - Edit the selected bookmark (opens modal)
- **X** - Delete the selected bookmark (requires confirmation)

### Interface
- **Cmd+K** (Mac) / **Ctrl+K** (Windows/Linux) - Focus the search bar
- **Escape** - Unfocus search bar or close modals
- **Cmd+Shift+D** - Toggle between dark and light themes
- **?** - Show keyboard shortcuts help

## 📡 RSS Feeds

`bookerics` automatically generates RSS feeds for your bookmarks:

- **Main Feed**: `/feeds/rss.xml` - All bookmarks
- **Cloud Hosted**: Feeds are automatically uploaded to web hosting with SFTP for external access

RSS feeds include:
- Bookmark metadata (title, description, URL)
- Screenshot thumbnails as enclosures
- Tags as categories
- Proper RSS 2.0 formatting with XSL styling

## 🔄 Data Management

### Import Existing Bookmarks

Use the blazing fast 🔥 companion [bookerics-importer](https://github.com/ehamiter/bookerics-importer) tool to convert browser bookmarks:

```bash
git clone https://github.com/ehamiter/bookerics-importer.git
cd bookerics-importer
cargo build --release

# Convert bookmarks.html to bookerics.db
./target/release/bookerics_importer /path/to/bookmarks.html bookerics.db
```

### Backup & Sync

- **Automatic Sync**: Screenshots and RSS feeds automatically uploaded via SFTP
- **Manual Backup**: Click the bookmark count to trigger immediate backup and feed update
- **Local Backups**: Optional local backup path configuration (keeps 10 most recent backups)

## 🚀 Deployment

### Development
```bash
uv run bookerics
```

### Production (macOS with launchd)

Create `~/Library/LaunchAgents/com.bookerics.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bookerics</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/.local/bin/uv</string>
        <string>run</string>
        <string>bookerics</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/bookerics</string>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/bookerics.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/bookerics.error.log</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

**Service Management**:
```bash
# Load and start
launchctl load ~/Library/LaunchAgents/com.bookerics.plist

# Stop and unload  
launchctl unload ~/Library/LaunchAgents/com.bookerics.plist

# Check status
launchctl list | grep bookerics

# View logs
tail -f ~/Library/Logs/bookerics.log
tail -f ~/Library/Logs/bookerics.error.log
```

## 🤔 FAQ

**Q. What?**  
A: It's bookmarks, but for Erics. So, `bookerics`. Get it?

**Q: That seems like it's marketed to a very niche group.**  
A: That's not a question.

**Q: Can I use this if my name isn't Eric?**  
A: Sure. If you're not lucky enough to be named Eric, you can update the configuration to be booktoms, bookzendayas, bookvolodymyrs, 
etc. I suppose "bookmarks" works as well.
