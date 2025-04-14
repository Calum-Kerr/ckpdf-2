// Mega Menu JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const megaMenuToggle = document.getElementById('allToolsDropdown');
    const megaMenu = document.querySelector('.mega-menu');
    const navItem = document.querySelector('.nav-item.dropdown');

    // Only apply hover behavior on desktop
    function setupHoverBehavior() {
        if (window.innerWidth >= 992 && megaMenuToggle && megaMenu && navItem) {
            // Show menu on hover
            navItem.addEventListener('mouseenter', function() {
                const dropdownToggle = new bootstrap.Dropdown(megaMenuToggle);
                dropdownToggle.show();
            });

            // Hide menu when mouse leaves
            navItem.addEventListener('mouseleave', function() {
                const dropdownToggle = bootstrap.Dropdown.getInstance(megaMenuToggle);
                if (dropdownToggle) {
                    dropdownToggle.hide();
                }
            });
        }
    }

    // Setup hover behavior initially
    setupHoverBehavior();

    // Update on window resize
    window.addEventListener('resize', function() {
        setupHoverBehavior();
    });

    // Add placeholder for future icon insertion
    const dropdownItems = document.querySelectorAll('.mega-menu .dropdown-item');
    dropdownItems.forEach(item => {
        // Add a span for the icon before the text
        const text = item.textContent.trim();
        item.innerHTML = `<span class="tool-icon me-2"></span>${text}`;
    });

    // Position the mega menu correctly on mobile
    function adjustMegaMenuPosition() {
        if (window.innerWidth < 992 && megaMenu) {
            megaMenu.style.width = '100vw';
            megaMenu.style.left = '0';
            megaMenu.style.right = '0';
        } else if (megaMenu) {
            megaMenu.style.width = '';
            megaMenu.style.left = '';
            megaMenu.style.right = '';
        }
    }

    // Adjust position initially and on resize
    adjustMegaMenuPosition();
    window.addEventListener('resize', adjustMegaMenuPosition);
});
