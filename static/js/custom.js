document.addEventListener('DOMContentLoaded', function() {

    document.body.addEventListener('click', function(event) {
        const button = event.target;
        if (button.classList.contains('delete-btn')) {
            if (button.dataset.confirmed === 'false') {
                event.preventDefault();
                button.dataset.confirmed = 'true';
                button.textContent = '✅';
                button.classList.add('enabled');
                setTimeout(() => {
                    button.dataset.confirmed = 'false';
                    button.textContent = '🗑️';
                    button.classList.remove('enabled');
                }, 3000);  // Reset after 3 seconds
            } else if (button.dataset.confirmed === 'true') {
                event.preventDefault();
                button.setAttribute('hx-delete', button.dataset.deleteUrl);
                console.log('Confirmed delete URL:', button.dataset.deleteUrl);
                console.log('Setting hx-delete:', button.getAttribute('hx-delete'));

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

        // Unfocus the search input on Escape
        if (event.key === 'Escape') {
            event.preventDefault();
            document.getElementById('query').blur();
        }
    });
});
