/**
 * Password strength checker
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get password input elements
    const currentPasswordInput = document.getElementById('current_password');
    const newPasswordInput = document.getElementById('new_password') || document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');

    // Get strength text elements
    const currentStrengthText = document.getElementById('current-strength-text');
    const newStrengthText = document.getElementById('new-strength-text') || document.getElementById('strength-text');
    const confirmStrengthText = document.getElementById('confirm-strength-text');
    const passwordMatchText = document.getElementById('password-match-text');

    // Get strength indicators for all password fields
    const currentStrengthIndicator = document.getElementById('current-password-strength');
    const newStrengthIndicator = document.getElementById('new-password-strength') || document.getElementById('password-strength');
    const confirmStrengthIndicator = document.getElementById('confirm-password-strength');

    // Setup event listeners for all password fields
    if (currentPasswordInput && currentStrengthText) {
        currentPasswordInput.addEventListener('input', function() {
            const strength = checkPasswordStrength(currentPasswordInput.value);
            updateStrengthText(currentStrengthText, strength);

            // Update progress bar if it exists
            if (currentStrengthIndicator) {
                updateStrengthIndicator(currentStrengthIndicator, strength);
            }
        });
    }

    if (newPasswordInput && newStrengthText) {
        newPasswordInput.addEventListener('input', function() {
            const strength = checkPasswordStrength(newPasswordInput.value);
            updateStrengthText(newStrengthText, strength);

            // Update progress bar if it exists
            if (newStrengthIndicator) {
                updateStrengthIndicator(newStrengthIndicator, strength);
            }

            // Check if passwords match
            if (confirmPasswordInput && passwordMatchText) {
                checkPasswordsMatch(newPasswordInput.value, confirmPasswordInput.value, passwordMatchText);
            }
        });
    }

    if (confirmPasswordInput && confirmStrengthText) {
        confirmPasswordInput.addEventListener('input', function() {
            const strength = checkPasswordStrength(confirmPasswordInput.value);
            updateStrengthText(confirmStrengthText, strength);

            // Update progress bar if it exists
            if (confirmStrengthIndicator) {
                updateStrengthIndicator(confirmStrengthIndicator, strength);
            }

            // Check if passwords match
            if (newPasswordInput && passwordMatchText) {
                checkPasswordsMatch(newPasswordInput.value, confirmPasswordInput.value, passwordMatchText);
            }
        });
    }

    /**
     * Check password strength
     * @param {string} password - The password to check
     * @returns {number} - Strength score (0-4)
     */
    function checkPasswordStrength(password) {
        if (!password) {
            return 0; // Empty password
        }

        let score = 0;

        // Length check
        if (password.length >= 8) {
            score += 1;
        }
        if (password.length >= 12) {
            score += 1;
        }

        // Character variety checks
        if (/[A-Z]/.test(password)) { // Has uppercase
            score += 1;
        }
        if (/[a-z]/.test(password)) { // Has lowercase
            score += 1;
        }
        if (/[0-9]/.test(password)) { // Has number
            score += 1;
        }
        if (/[^A-Za-z0-9]/.test(password)) { // Has special character
            score += 1;
        }

        // Normalize score to 0-4 range
        return Math.min(4, Math.floor(score / 1.5));
    }

    /**
     * Update the strength text
     * @param {HTMLElement} element - The text element to update
     * @param {number} strength - Strength score (0-4)
     */
    function updateStrengthText(element, strength) {
        let text;

        switch (strength) {
            case 0:
                text = 'None';
                break;
            case 1:
                text = 'Weak';
                break;
            case 2:
                text = 'Fair';
                break;
            case 3:
                text = 'Good';
                break;
            case 4:
                text = 'Strong';
                break;
        }

        element.textContent = 'Password strength: ' + text;
    }

    /**
     * Update the strength indicator
     * @param {HTMLElement} indicator - The progress bar element
     * @param {number} strength - Strength score (0-4)
     */
    function updateStrengthIndicator(indicator, strength) {
        // Remove all classes except progress-bar
        indicator.className = 'progress-bar';

        // Set color based on strength
        let color;
        let width = (strength / 4) * 100; // Convert strength to percentage

        switch (strength) {
            case 0:
                color = 'bg-secondary';
                break;
            case 1:
                color = 'bg-danger';
                break;
            case 2:
                color = 'bg-warning';
                break;
            case 3:
                color = 'bg-info';
                break;
            case 4:
                color = 'bg-success';
                break;
        }

        indicator.classList.add(color);
        indicator.style.width = width + '%';
        indicator.setAttribute('aria-valuenow', width);
    }

    /**
     * Check if passwords match and update the match text
     * @param {string} password1 - The first password
     * @param {string} password2 - The second password
     * @param {HTMLElement} matchText - The element to update with match status
     */
    function checkPasswordsMatch(password1, password2, matchText) {
        if (!password1 || !password2) {
            matchText.textContent = '';
            matchText.className = 'text-muted';
            return;
        }

        if (password1 === password2) {
            matchText.textContent = 'Passwords match ✓';
            matchText.className = 'text-success';
        } else {
            matchText.textContent = 'Passwords do not match ✗';
            matchText.className = 'text-danger';
        }
    }
});
