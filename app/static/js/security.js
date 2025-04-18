/**
 * Security module for client-side protection.
 * This module provides functions to enhance security on the client side.
 */

(function() {
    'use strict';

    // Security namespace
    const Security = {
        /**
         * Initialize security features.
         */
        init: function() {
            // Add event listeners
            document.addEventListener('DOMContentLoaded', this.setupProtections.bind(this));
            
            // Initialize immediately if DOM is already loaded
            if (document.readyState === 'interactive' || document.readyState === 'complete') {
                this.setupProtections();
            }
        },

        /**
         * Set up security protections.
         */
        setupProtections: function() {
            this.protectForms();
            this.sanitizeInputs();
            this.preventClickjacking();
            this.disableDevTools();
            this.protectLinks();
            this.addCSPReporting();
        },

        /**
         * Protect forms from CSRF attacks.
         */
        protectForms: function() {
            const forms = document.querySelectorAll('form');
            
            forms.forEach(form => {
                // Skip forms that already have CSRF token
                if (form.querySelector('input[name="csrf_token"]')) {
                    return;
                }
                
                // Get CSRF token from meta tag
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
                
                if (csrfToken) {
                    // Create CSRF token input
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'csrf_token';
                    input.value = csrfToken;
                    
                    // Add to form
                    form.appendChild(input);
                }
            });
        },

        /**
         * Sanitize user inputs to prevent XSS attacks.
         */
        sanitizeInputs: function() {
            const inputs = document.querySelectorAll('input, textarea');
            
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    // Basic sanitization - replace < and > with entities
                    this.value = this.value.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                });
            });
        },

        /**
         * Prevent clickjacking attacks.
         */
        preventClickjacking: function() {
            // Check if page is in an iframe
            if (window !== window.top) {
                // Check if the parent is allowed
                const allowedParents = [
                    'https://revisepdf.com',
                    'https://www.revisepdf.com'
                ];
                
                let isAllowed = false;
                
                try {
                    const parentOrigin = window.parent.location.origin;
                    isAllowed = allowedParents.includes(parentOrigin);
                } catch (e) {
                    // If we can't access the parent origin, it's cross-origin and not allowed
                    isAllowed = false;
                }
                
                if (!isAllowed) {
                    // Redirect to the top-level page
                    window.top.location = window.location;
                }
            }
        },

        /**
         * Add basic protection against developer tools.
         * Note: This is not foolproof and can be bypassed, but adds a layer of difficulty.
         */
        disableDevTools: function() {
            // Disable right-click
            document.addEventListener('contextmenu', function(e) {
                // Allow right-click on specific elements if needed
                const allowedElements = ['A', 'BUTTON'];
                if (!allowedElements.includes(e.target.tagName)) {
                    e.preventDefault();
                }
            });
            
            // Disable keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Disable F12
                if (e.key === 'F12') {
                    e.preventDefault();
                }
                
                // Disable Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+Shift+C
                if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) {
                    e.preventDefault();
                }
                
                // Disable Ctrl+U (view source)
                if (e.ctrlKey && e.key === 'u') {
                    e.preventDefault();
                }
            });
            
            // Basic detection of dev tools opening
            let devToolsOpen = false;
            
            const detectDevTools = function() {
                const threshold = 160;
                const widthThreshold = window.outerWidth - window.innerWidth > threshold;
                const heightThreshold = window.outerHeight - window.innerHeight > threshold;
                
                if (widthThreshold || heightThreshold) {
                    if (!devToolsOpen) {
                        devToolsOpen = true;
                        console.clear();
                        console.log('%c⚠️ Security Alert', 'font-size:24px; color:red;');
                        console.log('%cThis is a security-sensitive application. Debugging and inspection are monitored.', 'font-size:16px;');
                    }
                } else {
                    devToolsOpen = false;
                }
            };
            
            setInterval(detectDevTools, 1000);
        },

        /**
         * Protect links to prevent open redirects.
         */
        protectLinks: function() {
            const links = document.querySelectorAll('a[href]');
            
            links.forEach(link => {
                // Skip internal links
                if (link.href.startsWith(window.location.origin) || link.href.startsWith('/')) {
                    return;
                }
                
                // Add rel="noopener noreferrer" to external links
                link.rel = 'noopener noreferrer';
                
                // Add target="_blank" to external links
                link.target = '_blank';
                
                // Add click handler to confirm external navigation
                link.addEventListener('click', function(e) {
                    const confirmed = confirm(`You are navigating to an external site: ${this.hostname}\n\nDo you want to continue?`);
                    
                    if (!confirmed) {
                        e.preventDefault();
                    }
                });
            });
        },

        /**
         * Add CSP violation reporting.
         */
        addCSPReporting: function() {
            // Listen for CSP violations
            document.addEventListener('securitypolicyviolation', function(e) {
                // Log CSP violations
                const violation = {
                    blockedURI: e.blockedURI,
                    violatedDirective: e.violatedDirective,
                    originalPolicy: e.originalPolicy,
                    disposition: e.disposition,
                    documentURI: e.documentURI,
                    referrer: e.referrer,
                    sample: e.sample
                };
                
                // Send violation report to server
                fetch('/api/security/csp-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(violation)
                }).catch(function(error) {
                    // Silently fail if reporting fails
                    console.error('Error reporting CSP violation:', error);
                });
            });
        }
    };

    // Initialize security features
    Security.init();

    // Export Security object to global scope (for debugging only)
    // window.Security = Security;
})();
