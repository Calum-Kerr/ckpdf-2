/**
 * Password strength checker
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get password input elements
    const passwordInput = document.getElementById('password') || document.getElementById('new_password');
    const strengthIndicator = document.getElementById('password-strength');
    const strengthText = document.getElementById('strength-text');
    
    if (passwordInput && strengthIndicator && strengthText) {
        // Add input event listener to password field
        passwordInput.addEventListener('input', function() {
            const password = passwordInput.value;
            const strength = checkPasswordStrength(password);
            
            // Update strength indicator
            updateStrengthIndicator(strength);
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
     * Update the strength indicator
     * @param {number} strength - Strength score (0-4)
     */
    function updateStrengthIndicator(strength) {
        // Remove all classes
        strengthIndicator.className = 'progress-bar';
        
        // Set width based on strength
        const width = (strength * 25) + '%';
        strengthIndicator.style.width = width;
        
        // Set color and text based on strength
        let color, text;
        
        switch (strength) {
            case 0:
                color = 'bg-danger';
                text = 'None';
                break;
            case 1:
                color = 'bg-danger';
                text = 'Weak';
                break;
            case 2:
                color = 'bg-warning';
                text = 'Fair';
                break;
            case 3:
                color = 'bg-info';
                text = 'Good';
                break;
            case 4:
                color = 'bg-success';
                text = 'Strong';
                break;
        }
        
        strengthIndicator.classList.add(color);
        strengthText.textContent = text;
    }
});
