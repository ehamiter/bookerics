# Bookerics Firefox Extension

A Firefox extension for saving bookmarks to your Bookerics service.

## Installation

1. Open Firefox and navigate to `about:debugging`
2. Click on "This Firefox" in the left sidebar
3. Click on "Load Temporary Add-on..."
4. Navigate to the `bookerics_firefox_extension` folder and select the `manifest.json` file
5. The extension should now be loaded and visible in your toolbar

## Usage

1. Navigate to a webpage you want to bookmark
2. Click on the Bookerics icon in the toolbar
3. A popup will appear with the page title, description, URL, and a field for tags
4. Add comma-separated tags if desired
5. Click "Save Bookmark" to save to your Bookerics service
6. The popup will close automatically after saving

## Development

This extension is built using the Firefox WebExtensions API. The main components are:

- `manifest.json`: Extension configuration
- `background.js`: Background script that handles communication with the Bookerics server
- `popup.html` and `popup.js`: UI for the extension popup
- `content-script.js`: Script that extracts metadata from the current page

## Troubleshooting

If you encounter issues with the extension:

1. **Check the Firefox Console**:
   - Press F12 to open Developer Tools
   - Go to the Console tab
   - Look for any error messages related to the extension

2. **CORS Issues**:
   - The extension uses the background script to make requests to avoid CORS restrictions
   - Both fetch and XMLHttpRequest methods are implemented as fallbacks
   - The extension tries multiple endpoints and both localhost and 127.0.0.1 addresses

3. **Server Connection**:
   - Make sure your Bookerics server is running at `http://localhost:50667`
   - The extension will try both `localhost` and `127.0.0.1` addresses
   - It will attempt to use both `/static/bookmarklet.html` and `/api/bookmarks` endpoints

4. **Popup Windows**:
   - The extension now tries to mimic the original Chrome extension by opening a popup window
   - This is important because the server might be expecting a window to send a message to
   - If the popup window is blocked, the extension will fall back to using XMLHttpRequest
   - You may need to allow popups from the extension in Firefox settings

5. **Debugging**:
   - The background script includes extensive logging
   - Check the browser console for detailed information about request attempts
   - If you see "TypeError: s is undefined" or "DataCloneError", these have been fixed in the latest version

6. **Server API Compatibility**:
   - The extension now sends tags as part of the bookmark data
   - Make sure your server can handle the tags parameter
   - The extension uses URLSearchParams for proper parameter encoding

## Notes

- The extension expects the Bookerics service to be running at `http://localhost:50667`
- This approach uses both the extension's built-in popup system and a separate popup window for server communication
- The extension will try multiple methods to save bookmarks, increasing the chances of success
- The extension now prioritizes GET requests since they were successful in testing 