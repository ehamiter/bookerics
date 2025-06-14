function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        modalContainer.innerHTML = '';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed. Bookerics custom JS initializing.");
    
    // Initialize theme system
    initializeTheme();

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

    // Theme toggle button functionality with duplicate prevention
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn && !themeToggleBtn.hasAttribute('data-theme-listener')) {
        themeToggleBtn.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation(); // Prevent event bubbling
            toggleTheme();
        });
        themeToggleBtn.setAttribute('data-theme-listener', 'true');
        console.log('🎨 Theme toggle event listener attached');
    }

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



    // Enhanced keyboard shortcuts system
    let currentBookmarkIndex = -1;
    let bookmarkElements = [];
    let helpModalOpen = false;

    function updateBookmarkElements() {
        bookmarkElements = Array.from(document.querySelectorAll('.bookmark-box'));
        console.log('📋 Updated bookmark elements:', bookmarkElements.length);
    }

    function highlightBookmark(index) {
        // Remove highlight from all bookmarks
        bookmarkElements.forEach(el => el.classList.remove('keyboard-focused'));
        
        if (index >= 0 && index < bookmarkElements.length) {
            const bookmark = bookmarkElements[index];
            bookmark.classList.add('keyboard-focused');
            bookmark.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log('📋 Highlighted bookmark:', index, bookmark.id);
        }
    }

    function getCurrentBookmark() {
        if (currentBookmarkIndex >= 0 && currentBookmarkIndex < bookmarkElements.length) {
            return bookmarkElements[currentBookmarkIndex];
        }
        return null;
    }

    function getBookmarkUrl(bookmarkElement) {
        const link = bookmarkElement.querySelector('.bookeric-link.external');
        return link ? link.href : null;
    }

    function getBookmarkId(bookmarkElement) {
        const id = bookmarkElement.id;
        // Extract bookmark ID from element ID (format: bmb-{id})
        return id ? id.replace('bmb-', '') : null;
    }

    function triggerBookmarkEdit(bookmarkElement) {
        const bookmarkId = getBookmarkId(bookmarkElement);
        if (bookmarkId) {
            console.log('✒️ Triggering edit for bookmark:', bookmarkId);
            // Use HTMX to load the edit modal
            htmx.ajax('GET', `/edit/${bookmarkId}/modal`, {
                target: '#modal-container',
                swap: 'innerHTML'
            });
        }
    }

    function triggerBookmarkDelete(bookmarkElement) {
        const deleteBtn = bookmarkElement.querySelector('.delete-btn');
        if (deleteBtn) {
            console.log('🗑️ Triggering delete for bookmark:', getBookmarkId(bookmarkElement));
            // Simulate click on delete button to use existing delete logic
            deleteBtn.click();
        }
    }

    function showKeyboardShortcutsHelp() {
        if (helpModalOpen) {
            closeModal();
            return;
        }
        
        console.log('❓ Showing keyboard shortcuts help');
        htmx.ajax('GET', '/help/keyboard-shortcuts', {
            target: '#modal-container',
            swap: 'innerHTML'
        });
        helpModalOpen = true;
    }

    // Enhanced keyboard event handler
    document.addEventListener('keydown', function(event) {
        const modalContainer = document.getElementById('modal-container');
        const isModalOpen = modalContainer && modalContainer.innerHTML.trim() !== '';
        const isInputFocused = document.activeElement && 
                              (document.activeElement.tagName === 'INPUT' || 
                               document.activeElement.tagName === 'TEXTAREA');

        // Handle modal-specific shortcuts
        if (isModalOpen) {
            if (event.key === 'Escape') {
                event.preventDefault();
                closeModal();
                helpModalOpen = false;
                return;
            }
            // Don't process other shortcuts when modal is open
            return;
        }

        // Don't process navigation shortcuts when input is focused (except for escape)
        if (isInputFocused) {
            if (event.key === 'Escape') {
                event.preventDefault();
                document.activeElement.blur();
                // Clear current bookmark highlight when escaping from input
                bookmarkElements.forEach(el => el.classList.remove('keyboard-focused'));
                currentBookmarkIndex = -1;
            }
            return;
        }

        // Search shortcuts (Command/Ctrl + K)
        if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
            event.preventDefault();
            const queryInput = document.getElementById('query');
            if (queryInput) {
                queryInput.focus();
                if (queryInput.value) {
                    queryInput.select();
                }
            }
            return;
        }

        // Help modal (?)
        if (event.key === '?') {
            event.preventDefault();
            showKeyboardShortcutsHelp();
            return;
        }

        // Update bookmark elements list (in case new content was loaded)
        updateBookmarkElements();

        if (bookmarkElements.length === 0) {
            console.log('📋 No bookmark elements found');
            return;
        }

        // Navigation shortcuts
        if (event.key === 'j' || event.key === 'J') {
            event.preventDefault();
            if (currentBookmarkIndex < bookmarkElements.length - 1) {
                currentBookmarkIndex++;
                highlightBookmark(currentBookmarkIndex);
                console.log('📋 Navigate down to bookmark:', currentBookmarkIndex);
            } else {
                console.log('📋 Already at last bookmark, not wrapping');
            }
        }

        if (event.key === 'k' || event.key === 'K') {
            event.preventDefault();
            if (currentBookmarkIndex > 0) {
                currentBookmarkIndex--;
                highlightBookmark(currentBookmarkIndex);
                console.log('📋 Navigate up to bookmark:', currentBookmarkIndex);
            } else {
                console.log('📋 Already at first bookmark, not wrapping');
            }
        }

        // Action shortcuts (only if a bookmark is selected)
        const currentBookmark = getCurrentBookmark();
        if (!currentBookmark) {
            return;
        }

        // Open URL in new tab (V)
        if (event.key === 'v' || event.key === 'V') {
            event.preventDefault();
            console.log('🔗 V key pressed, current bookmark:', currentBookmark);
            console.log('🔗 Current bookmark index:', currentBookmarkIndex);
            const url = getBookmarkUrl(currentBookmark);
            console.log('🔗 Extracted URL:', url);
            if (url) {
                console.log('🔗 Opening URL in new tab:', url);
                window.open(url, '_blank');
            } else {
                console.log('🔗 No URL found for current bookmark');
            }
        }

        // Edit bookmark (E)
        if (event.key === 'e' || event.key === 'E') {
            event.preventDefault();
            triggerBookmarkEdit(currentBookmark);
        }

        // Delete bookmark (X)
        if (event.key === 'x' || event.key === 'X') {
            event.preventDefault();
            triggerBookmarkDelete(currentBookmark);
        }
    });

    // Update bookmark elements after HTMX content swaps
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        console.log('HTMX: Content swapped for target:', evt.detail.target.id);
        formatDates(); // Re-format dates in newly loaded content
        
        // Reset keyboard navigation state
        currentBookmarkIndex = -1;
        updateBookmarkElements();
        
        // Clear any existing highlights
        bookmarkElements.forEach(el => el.classList.remove('keyboard-focused'));
    });

    // Override the existing closeModal function to handle help modal state
    const originalCloseModal = window.closeModal;
    window.closeModal = function() {
        helpModalOpen = false;
        if (originalCloseModal) {
            originalCloseModal();
        } else {
            const modalContainer = document.getElementById('modal-container');
            if (modalContainer) {
                modalContainer.innerHTML = '';
            }
        }
    };

    // Initialize bookmark elements on page load
    updateBookmarkElements();

    // Format dates in user's local timezone
    function formatDates() {
        const timeElements = document.querySelectorAll('.created-at-time');
        timeElements.forEach(timeEl => {
            const isoDate = timeEl.getAttribute('datetime');
            if (isoDate) {
                try {
                    const date = new Date(isoDate);
                    const options = {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        hour12: true
                    };
                    const friendlyDate = date.toLocaleDateString('en-US', options);
                    timeEl.textContent = friendlyDate;
                } catch (e) {
                    console.error('Error formatting date:', e);
                }
            }
        });
    }

    // Format dates on initial load
    formatDates();

    // Also format dates after HTMX content swaps
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        console.log('HTMX: Content swapped for target:', evt.detail.target.id);
        formatDates(); // Re-format dates in newly loaded content
    });
});

// Theme Management Functions
function initializeTheme() {
    console.log('🎨 Initializing theme system...');
    
    // Always set up the keyboard shortcut, regardless of initialization path
    setupKeyboardShortcut();
    
    // Check if the blocking script already set the theme
    if (window.__THEME_SET__ && window.__INITIAL_COLOR_MODE__) {
        console.log('🎨 Theme already set by blocking script:', window.__INITIAL_COLOR_MODE__);
        
        // Just update the toggle button to match the theme that was already set
        updateThemeToggleIcon(window.__INITIAL_COLOR_MODE__);
        
        // Store it in localStorage if it's not already there (in case it came from system preference)
        if (!localStorage.getItem('bookerics-theme')) {
            localStorage.setItem('bookerics-theme', window.__INITIAL_COLOR_MODE__);
        }
        
        return;
    }
    
    // Fallback: if blocking script didn't run (shouldn't happen), do the normal detection
    console.log('🎨 Blocking script did not run, falling back to normal detection');
    const savedTheme = localStorage.getItem('bookerics-theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    console.log('🎨 Saved theme:', savedTheme);
    console.log('🎨 System prefers dark:', systemPrefersDark);
    
    // Apply theme based on saved preference or system preference
    if (savedTheme) {
        applyTheme(savedTheme);
    } else {
        // Honor system preference by default
        applyTheme(systemPrefersDark ? 'dark' : 'light');
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        console.log('🎨 System theme changed to:', e.matches ? 'dark' : 'light');
        // Only auto-switch if user hasn't manually set a preference
        if (!localStorage.getItem('bookerics-theme')) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
}

function setupKeyboardShortcut() {
    // Add keyboard shortcut for theme toggle (Cmd/Ctrl + Shift + D)
    document.addEventListener('keydown', function(event) {
        if ((event.metaKey || event.ctrlKey) && event.shiftKey && (event.key === 'D' || event.key === 'd')) {
            console.log('🎨 Theme toggle keyboard shortcut triggered!');
            event.preventDefault();
            toggleTheme();
        }
    });
}

function applyTheme(theme) {
    console.log('🎨 Applying theme:', theme);
    
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
    
    // Store the applied theme in localStorage
    localStorage.setItem('bookerics-theme', theme);
    
    // Also set a cookie so the server can detect the theme preference
    document.cookie = `bookerics-theme=${theme}; path=/; max-age=31536000; SameSite=Lax`;
    
    // Update theme toggle button icon
    updateThemeToggleIcon(theme);
    
    // Dispatch custom event for other components that might need to know
    document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
}

function updateThemeToggleIcon(theme) {
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn) {
        // Show sun icon in dark mode (to indicate switching to light)
        // Show moon icon in light mode (to indicate switching to dark)
        themeToggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
        themeToggleBtn.title = theme === 'dark' 
            ? 'Switch to light theme (Cmd+Shift+D)' 
            : 'Switch to dark theme (Cmd+Shift+D)';
    }
}

// Throttle to prevent rapid theme switching
let themeToggleTimeout = null;

function toggleTheme() {
    // Prevent rapid successive calls
    if (themeToggleTimeout) {
        return;
    }
    
    themeToggleTimeout = setTimeout(() => {
        themeToggleTimeout = null;
    }, 300); // 300ms throttle
    
    const currentTheme = localStorage.getItem('bookerics-theme') || 
                        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    console.log('🎨 Toggling theme from', currentTheme, 'to', newTheme);
    applyTheme(newTheme);
}

function getCurrentTheme() {
    return localStorage.getItem('bookerics-theme') || 
           (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
}
