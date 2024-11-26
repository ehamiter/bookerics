chrome.action.onClicked.addListener((tab) => {
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: () => {
      const title = encodeURIComponent(document.title);
      const metaDesc = document.querySelector("meta[name='description']") || 
                      document.querySelector("meta[property='og:description']");
      const description = metaDesc ? encodeURIComponent(metaDesc.content) : '';
      const url = encodeURIComponent(window.location.href);
      const popupUrl = `http://localhost:8080/static/bookmarklet.html?title=${title}&description=${description}&url=${url}`;
      
      // Store the popup reference in window.bookericsPopup
      window.bookericsPopup = window.open(popupUrl, 'Save Bookeric', 'top=200,left=400,width=666,height=444');
      
      // Listen for the message from the popup
      window.addEventListener('message', function(e) {
        if (e.data === 'bookmark_saving' && window.bookericsPopup) {
          window.bookericsPopup.close();
        }
      }, false);
    }
  });
});
