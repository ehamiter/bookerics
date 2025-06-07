function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        modalContainer.innerHTML = '';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed. Bookerics custom JS initializing.");

    // General HTMX event logging
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        console.log('HTMX: Making a request to:', evt.detail.requestConfig.path);
        console.log('HTMX: Target element is:', evt.detail.requestConfig.target);
    });

    document.body.addEventListener('htmx:afterSwap', function(evt) {
        console.log('HTMX: Content swapped for target:', evt.detail.target.id);
    });

    document.body.addEventListener('htmx:afterRequest', function(evt) {
        console.log('HTMX: Request completed. Status:', evt.detail.xhr.status);
        console.log('HTMX: Response headers:', evt.detail.xhr.getAllResponseHeaders());
        if (evt.detail.xhr.getResponseHeader('HX-Trigger')) {
            console.log('HTMX: HX-Trigger header found:', evt.detail.xhr.getResponseHeader('HX-Trigger'));
        }
    });

    document.body.addEventListener('htmx:targetError', function(evt) {
        console.error("HTMX Target Error:", evt.detail.error);
        console.error("Attempted to target:", evt.detail.target);
    });

    // Listen for direct closeModal events from HX-Trigger headers
    document.body.addEventListener('closeModal', function(e) {
        console.log('closeModal event received from HX-Trigger, closing modal...');
        closeModal();
    });

    // Listen for custom event to open modal and log it
    document.body.addEventListener('openModal', function(e) {
        console.log('Modal event triggered. Content will be loaded into #modal-container.');
    });

    // Close modal on Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modalContainer = document.getElementById('modal-container');
            if (modalContainer && modalContainer.innerHTML.trim() !== '') {
                event.preventDefault();
                closeModal();
            }
        }
    });

    /* Deleting bookmarks  */
    document.body.addEventListener('click', function(event) {
        const button = event.target;
        if (button.classList.contains('delete-btn')) {
            console.log('🔥 Delete button clicked:', button.dataset);
            console.log('🔥 Confirmed status:', button.dataset.confirmed);
            console.log('🔥 Delete URL:', button.dataset.deleteUrl);
            
            if (button.dataset.confirmed === 'false') {
                event.preventDefault();
                button.dataset.confirmed = 'true';
                button.textContent = '✅';
                button.classList.add('enabled');
                console.log('🔥 Delete button now confirmed, waiting for second click');
                setTimeout(() => {
                    button.dataset.confirmed = 'false';
                    button.textContent = '🗑️';
                    button.classList.remove('enabled');
                    console.log('🔥 Delete button confirmation timeout, reset to unconfirmed');
                }, 3000);  // Reset after 3 seconds
            } else if (button.dataset.confirmed === 'true') {
                event.preventDefault();
                console.log('🔥 Executing delete for URL:', button.dataset.deleteUrl);
                
                // Manually create an HTMX request to handle the delete
                htmx.ajax('DELETE', button.dataset.deleteUrl, {
                    target: button.getAttribute('hx-target'),
                    swap: 'outerHTML'
                });
            }
        }
    });

    // Tags link toggle functionality
    const tagsLink = document.getElementById('tags-link');
    const currentPath = window.location.pathname;

    // Set the initial title based on the current path
    if (currentPath === '/tags') {
        tagsLink.title = 'Click to see sorted by newest';
    } else if (currentPath === '/tags/newest') {
        tagsLink.title = 'Click to see sorted by frequency';
    }

    tagsLink.addEventListener('click', function(event) {
        event.preventDefault();
        if (currentPath === '/tags') {
            window.location.href = '/tags/newest';
            tagsLink.title = 'Click to see sorted by frequency';
        } else if (currentPath === '/tags/newest') {
            window.location.href = '/tags';
            tagsLink.title = 'Click to see sorted by newest';
        } else {
            window.location.href = '/tags';
        }
    });

    // Hidden link click functionality
    document.querySelector('.hidden-link').addEventListener('click', function(event) {
        event.preventDefault();
        fetch('/update')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    location.reload();
                    console.log('Successfully backed up bookmarks to S3!');
                } else {
                    alert('Failed to update: ' + data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Focus the search input on Command + K
        if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
            event.preventDefault();
            const queryInput = document.getElementById('query');
            queryInput.focus();

            if (queryInput.value) {
                queryInput.select();
            }
        }

        // Unfocus the search input on Escape (only if no modal is open)
        if (event.key === 'Escape') {
            const modalContainer = document.getElementById('modal-container');
            if (!modalContainer || modalContainer.innerHTML.trim() === '') {
                event.preventDefault();
                document.getElementById('query').blur();
            }
        }
    });
});
