/* keyboard shortcuts */

document.addEventListener('keydown', function(event) {
    // Focus the search input on Command + K
    if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        document.getElementById('query').focus();
    }
    // Unfocus the search input on Escape
    if (event.key === 'Escape') {
        event.preventDefault();
        document.getElementById('query').blur();
    }
});
