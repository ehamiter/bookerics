// Listen for messages from the popup
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'saveBookmark') {
    console.log('Received saveBookmark message:', message.data);
    
    const { title, description, tags, url } = message.data;
    
    // Create the URL for the bookmarklet endpoint
    // Try both localhost and 127.0.0.1 versions
    const bookmarkletUrls = [
      `http://localhost:50667/static/bookmarklet.html`,
      `http://127.0.0.1:50667/static/bookmarklet.html`,
      `http://localhost:50667/api/bookmarks`,
      `http://127.0.0.1:50667/api/bookmarks`
    ];
    
    console.log('Attempting to save bookmark to:', bookmarkletUrls[0]);
    
    // We need to handle the Promise chain manually to avoid DataCloneError
    saveBookmarkToAnyEndpoint(bookmarkletUrls, title, description, tags, url)
      .then(() => {
        console.log('Bookmark saved successfully');
        sendResponse({ success: true });
      })
      .catch(error => {
        console.error('All requests failed:', error);
        sendResponse({ 
          success: false, 
          error: 'Failed to save bookmark. Server may be down or unreachable.' 
        });
      });
    
    // Return true to indicate that we will send a response asynchronously
    return true;
  }
});

// Listen for keyboard shortcut commands
browser.commands.onCommand.addListener((command) => {
  if (command === 'save-bookmark') {
    console.log('Keyboard shortcut triggered: save-bookmark');
    
    // Get the current tab
    browser.tabs.query({active: true, currentWindow: true}).then(tabs => {
      const tab = tabs[0];
      
      // Get metadata from the page
      browser.tabs.sendMessage(tab.id, {action: 'getMetadata'}).then(metadata => {
        // If we couldn't get metadata from the content script, use tab info
        const data = metadata || {
          title: tab.title,
          description: '',
          url: tab.url,
          tags: ''
        };
        
        // Save the bookmark
        const bookmarkletUrls = [
          `http://localhost:50667/static/bookmarklet.html`,
          `http://127.0.0.1:50667/static/bookmarklet.html`,
          `http://localhost:50667/api/bookmarks`,
          `http://127.0.0.1:50667/api/bookmarks`
        ];
        
        console.log('Keyboard shortcut: Quick saving bookmark for', data.url);
        
        saveBookmarkToAnyEndpoint(bookmarkletUrls, data.title, data.description, data.tags || '', data.url)
          .then(() => {
            console.log('Bookmark saved successfully via keyboard shortcut');
            // Show a notification
            browser.notifications.create({
              type: 'basic',
              iconUrl: 'icon-48.png',
              title: 'Bookerics',
              message: 'Bookmark saved successfully!'
            });
          })
          .catch(error => {
            console.error('Failed to save bookmark via keyboard shortcut:', error);
            // Show error notification
            browser.notifications.create({
              type: 'basic',
              iconUrl: 'icon-48.png',
              title: 'Bookerics',
              message: 'Failed to save bookmark. Server may be down or unreachable.'
            });
          });
      }).catch(error => {
        console.error('Error getting metadata:', error);
        // Fall back to using tab info directly
        const data = {
          title: tab.title,
          description: '',
          url: tab.url,
          tags: ''
        };
        
        // Save with basic info
        const bookmarkletUrls = [
          `http://localhost:50667/static/bookmarklet.html`,
          `http://127.0.0.1:50667/static/bookmarklet.html`
        ];
        
        saveBookmarkToAnyEndpoint(bookmarkletUrls, data.title, data.description, data.tags, data.url)
          .then(() => {
            console.log('Bookmark saved with basic info');
            browser.notifications.create({
              type: 'basic',
              iconUrl: 'icon-48.png',
              title: 'Bookerics',
              message: 'Bookmark saved successfully!'
            });
          })
          .catch(error => console.error('Failed to save bookmark with basic info:', error));
      });
    });
  }
});

// Try to save bookmark to any of the endpoints
async function saveBookmarkToAnyEndpoint(urls, title, description, tags, url) {
  let lastError = null;
  
  // Try each URL with both GET and POST
  for (const currentUrl of urls) {
    try {
      // Try GET first (since it worked in the logs)
      console.log(`Trying GET request to: ${currentUrl}`);
      await makeGetRequest(currentUrl, title, description, tags, url);
      console.log(`GET request to ${currentUrl} succeeded`);
      return true; // Success, exit the function
    } catch (getError) {
      console.log(`GET request to ${currentUrl} failed:`, getError);
      lastError = getError;
      
      try {
        // Try POST as fallback
        console.log(`Trying POST request to: ${currentUrl}`);
        await makePostRequest(currentUrl, title, description, tags, url);
        console.log(`POST request to ${currentUrl} succeeded`);
        return true; // Success, exit the function
      } catch (postError) {
        console.log(`POST request to ${currentUrl} failed:`, postError);
        lastError = postError;
        // Continue to the next URL
      }
    }
  }
  
  // If we get here, all requests failed
  throw lastError || new Error('All requests failed');
}

// Make a POST request
function makePostRequest(bookmarkletUrl, title, description, tags, url) {
  return new Promise((resolve, reject) => {
    const formData = new URLSearchParams();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('tags', tags);
    formData.append('url', url);
    
    fetch(bookmarkletUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString()
    })
    .then(response => {
      console.log('POST response status:', response.status);
      if (response.ok) {
        resolve(true);
      } else {
        reject(new Error(`Server returned ${response.status}: ${response.statusText}`));
      }
    })
    .catch(error => {
      console.error('POST fetch error:', error);
      reject(error);
    });
  });
}

// Make a GET request
function makeGetRequest(bookmarkletUrl, title, description, tags, url) {
  return new Promise((resolve, reject) => {
    // Create a new window to mimic the original Chrome extension behavior
    // This is important because the server might be expecting a window to send a message to
    const windowRef = window.open(
      `${bookmarkletUrl}?title=${encodeURIComponent(title)}&description=${encodeURIComponent(description)}&tags=${encodeURIComponent(tags)}&url=${encodeURIComponent(url)}`,
      'Save Bookeric',
      'top=200,left=400,width=666,height=444'
    );
    
    if (!windowRef) {
      // If window.open fails, fall back to XHR
      console.log('window.open failed, falling back to XHR');
      
      // First try to load the bookmarklet page
      const xhr = new XMLHttpRequest();
      const params = new URLSearchParams();
      params.append('title', title);
      params.append('description', description);
      params.append('tags', tags);
      params.append('url', url);
      
      const getUrl = `${bookmarkletUrl}?${params.toString()}`;
      
      xhr.open('GET', getUrl, true);
      
      xhr.onload = function() {
        console.log('GET response status:', xhr.status);
        if (xhr.status >= 200 && xhr.status < 300) {
          // Now directly submit to the /add endpoint
          const addUrl = bookmarkletUrl.replace('/static/bookmarklet.html', '/add');
          console.log('Directly submitting to:', addUrl);
          
          const postXhr = new XMLHttpRequest();
          postXhr.open('POST', addUrl, true);
          postXhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
          
          postXhr.onload = function() {
            console.log('POST response status:', postXhr.status);
            if (postXhr.status >= 200 && postXhr.status < 300) {
              console.log('Bookmark saved via direct POST');
              resolve(true);
            } else {
              console.error('POST request failed:', postXhr.statusText);
              reject(new Error(`Server returned ${postXhr.status}: ${postXhr.statusText}`));
            }
          };
          
          postXhr.onerror = function() {
            console.error('POST XHR error');
            reject(new Error('Network error occurred during POST'));
          };
          
          postXhr.send(params.toString());
        } else {
          reject(new Error(`Server returned ${xhr.status}: ${xhr.statusText}`));
        }
      };
      
      xhr.onerror = function() {
        console.error('GET XHR error');
        reject(new Error('Network error occurred'));
      };
      
      xhr.send();
      return;
    }
    
    // Listen for the message from the popup window
    const messageListener = function(e) {
      console.log('Received message from popup:', e.data);
      if (e.data === 'bookmark_saving') {
        console.log('Bookmark saving message received, closing popup');
        window.removeEventListener('message', messageListener);
        if (windowRef) windowRef.close();
        resolve(true);
      }
    };
    
    window.addEventListener('message', messageListener, false);
    
    // Set a timeout to close the window and resolve after 5 seconds
    // in case we don't receive the message
    setTimeout(() => {
      console.log('Timeout reached, assuming bookmark was saved');
      window.removeEventListener('message', messageListener);
      if (windowRef) windowRef.close();
      resolve(true);
    }, 5000);
  });
} 