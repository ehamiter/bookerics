// This script is injected into the page by the browser_action
// It's primarily used to extract metadata from the page
// The actual bookmark saving is handled by the popup and background script

// Function to extract metadata from the page
function extractMetadata() {
  const title = document.title;
  const metaDesc = document.querySelector("meta[name='description']") || 
                  document.querySelector("meta[property='og:description']");
  const description = metaDesc ? metaDesc.content : '';
  const url = window.location.href;
  
  return {
    title,
    description,
    url
  };
}

// Make the metadata available to the extension
if (typeof browser !== 'undefined' && browser.runtime) {
  browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getMetadata') {
      sendResponse(extractMetadata());
    }
    return true;
  });
} 