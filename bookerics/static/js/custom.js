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
