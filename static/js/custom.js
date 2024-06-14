document.addEventListener('DOMContentLoaded', function() {
    // Code dependent on DOM content being fully loaded

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
