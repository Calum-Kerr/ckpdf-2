/**
 * Mega Menu JavaScript
 *
 * This file contains the JavaScript functionality for the mega menu dropdown.
 */

document.addEventListener('DOMContentLoaded', function() {
    const toolsDropdown = document.getElementById('toolsDropdown');
    const megaMenuWrapper = document.getElementById('megaMenuWrapper');

    if (toolsDropdown && megaMenuWrapper) {
        // Toggle menu on click
        toolsDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            megaMenuWrapper.classList.toggle('show');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!toolsDropdown.contains(e.target) && !megaMenuWrapper.contains(e.target)) {
                megaMenuWrapper.classList.remove('show');
            }
        });

        // Prevent clicks inside the mega menu from closing it
        megaMenuWrapper.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
});
