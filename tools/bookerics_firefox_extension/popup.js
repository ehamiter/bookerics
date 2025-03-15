document.addEventListener('DOMContentLoaded', function() {
  // Get the current tab's information
  browser.tabs.query({active: true, currentWindow: true}).then(tabs => {
    const tab = tabs[0];
    
    // Set the URL field
    document.getElementById('url').value = tab.url;
    
    // Set the title field
    document.getElementById('title').value = tab.title;
    
    // Get the description from the page (we need to execute a content script for this)
    browser.tabs.executeScript({
      code: `
        const metaDesc = document.querySelector("meta[name='description']") || 
                        document.querySelector("meta[property='og:description']");
        metaDesc ? metaDesc.content : '';
      `
    }).then(results => {
      if (results && results[0]) {
        document.getElementById('description').value = results[0];
      }
    }).catch(error => {
      console.error("Error getting description:", error);
    });
  });
  
  // Add event listener for the save button
  document.getElementById('save-button').addEventListener('click', function() {
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const tags = document.getElementById('tags').value;
    const url = document.getElementById('url').value;
    
    // Create the status element
    const statusElement = document.getElementById('status');
    
    // Disable the button while saving
    const saveButton = document.getElementById('save-button');
    saveButton.disabled = true;
    saveButton.textContent = 'Saving...';
    
    // Show a loading status
    statusElement.textContent = 'Saving bookmark...';
    statusElement.className = 'status';
    statusElement.style.display = 'block';
    
    // Send the data to the Bookerics server using the background script to avoid CORS issues
    browser.runtime.sendMessage({
      action: 'saveBookmark',
      data: {
        title: title,
        description: description,
        tags: tags,
        url: url
      }
    }).then(response => {
      if (response && response.success) {
        statusElement.textContent = 'Bookmark saved successfully!';
        statusElement.className = 'status success';
        
        // Close the popup after a short delay
        setTimeout(() => {
          window.close();
        }, 1500);
      } else {
        saveButton.disabled = false;
        saveButton.textContent = 'Save Bookmark';
        
        const errorMsg = response && response.error ? response.error : 'Unknown error occurred';
        statusElement.textContent = 'Error: ' + errorMsg;
        statusElement.className = 'status error';
      }
    }).catch(error => {
      console.error('Error in sendMessage:', error);
      
      saveButton.disabled = false;
      saveButton.textContent = 'Save Bookmark';
      
      statusElement.textContent = 'Error: ' + (error.message || 'Unknown error occurred');
      statusElement.className = 'status error';
    });
  });
}); 