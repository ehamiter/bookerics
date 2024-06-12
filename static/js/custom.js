/* keyboard shortcuts */

document.addEventListener('keydown', function(event) {
    // Focus the search input on Command + K
    if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        // document.getElementById('query').focus();
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

document.querySelector('.hidden-link').addEventListener('click', function(event) {
    event.preventDefault();
    fetch('/update')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                location.reload();
            } else {
                alert('Failed to update: ' + data.message);
            }
        })
        .catch(error => console.error('Error:', error));
});
