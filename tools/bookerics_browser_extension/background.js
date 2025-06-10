chrome.action.onClicked.addListener((tab) => {
  console.log('Extension clicked on tab:', tab.url);
  
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: () => {
      console.log('Script executing on:', window.location.href);
      
      const title = encodeURIComponent(document.title);
      const metaDesc = document.querySelector("meta[name='description']") || 
                      document.querySelector("meta[property='og:description']");
      const description = metaDesc ? encodeURIComponent(metaDesc.content) : '';
      const url = encodeURIComponent(window.location.href);
      
      console.log('Captured URL:', window.location.href);
      
      const popupUrl = `http://localhost:50113/static/bookmarklet.html?title=${title}&description=${description}&url=${url}`;
      
      // Store the popup reference in window.bookericsPopup
      window.bookericsPopup = window.open(popupUrl, 'Save Bookeric', 'top=200,left=400,width=666,height=500');
      
      // Listen for the message from the popup
      window.addEventListener('message', function(e) {
        if (e.data === 'bookmark_saving' && window.bookericsPopup) {
          window.bookericsPopup.close();
        }
      }, false);
    }
  }).catch((error) => {
    console.error('Script execution failed:', error);
  });
});
