/**
 * RevisePDF Main JavaScript
 * 
 * This file contains the main JavaScript functionality for the RevisePDF application.
 */

document.addEventListener('DOMContentLoaded', function() {
    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const wrapper = document.createElement('div');
        wrapper.className = 'file-upload-wrapper mb-3';
        
        const message = document.createElement('div');
        message.className = 'file-upload-message';
        message.innerHTML = `
            <i class="fas fa-cloud-upload-alt"></i>
            <p>Drag and drop your file here or click to browse</p>
            <p class="text-muted small">Maximum file size: 50MB</p>
        `;
        
        // Replace the input with the custom wrapper
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(message);
        wrapper.appendChild(input);
        
        // Update the message when a file is selected
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                const fileName = this.files[0].name;
                const fileSize = (this.files[0].size / 1024 / 1024).toFixed(2);
                
                message.innerHTML = `
                    <i class="fas fa-file-alt"></i>
                    <p>${fileName}</p>
                    <p class="text-muted small">${fileSize} MB</p>
                    <p class="text-primary">Click to change file</p>
                `;
            } else {
                message.innerHTML = `
                    <i class="fas fa-cloud-upload-alt"></i>
                    <p>Drag and drop your file here or click to browse</p>
                    <p class="text-muted small">Maximum file size: 50MB</p>
                `;
            }
        });
        
        // Handle drag and drop events
        wrapper.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('border-primary');
            this.classList.add('bg-primary-light');
        });
        
        wrapper.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('border-primary');
            this.classList.remove('bg-primary-light');
        });
        
        wrapper.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('border-primary');
            this.classList.remove('bg-primary-light');
            
            if (e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                
                // Trigger the change event
                const event = new Event('change');
                input.dispatchEvent(event);
            }
        });
    });
    
    // Form submission loading spinner
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Check if the form has files and they are valid
            const fileInputs = this.querySelectorAll('input[type="file"]');
            let hasFiles = false;
            
            fileInputs.forEach(input => {
                if (input.files.length > 0) {
                    hasFiles = true;
                }
            });
            
            if (hasFiles) {
                // Create and show the loading spinner
                const spinner = document.createElement('div');
                spinner.className = 'spinner-overlay';
                spinner.innerHTML = `
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                `;
                
                document.body.appendChild(spinner);
            }
        });
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Page range input validation for split and extract tools
    const pageRangeInputs = document.querySelectorAll('input[name="pages"], input[name="page_ranges"]');
    
    pageRangeInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Allow only numbers, commas, hyphens, and spaces
            this.value = this.value.replace(/[^0-9,\-\s]/g, '');
        });
    });
    
    // Dynamic form fields based on selection
    const splitMethodSelect = document.querySelector('select[name="split_method"]');
    
    if (splitMethodSelect) {
        const pageRangesField = document.querySelector('#page_ranges_field');
        const maxSizeField = document.querySelector('#max_size_field');
        
        splitMethodSelect.addEventListener('change', function() {
            if (this.value === 'range') {
                pageRangesField.classList.remove('d-none');
                maxSizeField.classList.add('d-none');
            } else if (this.value === 'size') {
                pageRangesField.classList.add('d-none');
                maxSizeField.classList.remove('d-none');
            } else {
                pageRangesField.classList.add('d-none');
                maxSizeField.classList.add('d-none');
            }
        });
        
        // Trigger the change event on page load
        splitMethodSelect.dispatchEvent(new Event('change'));
    }
    
    // Password strength meter for protect tool
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        const strengthMeter = document.createElement('div');
        strengthMeter.className = 'password-strength-meter mt-2';
        strengthMeter.innerHTML = `
            <div class="progress" style="height: 5px;">
                <div class="progress-bar" role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            <small class="text-muted">Password strength: <span class="strength-text">None</span></small>
        `;
        
        input.parentNode.appendChild(strengthMeter);
        
        input.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            let strengthText = 'None';
            
            if (password.length > 0) {
                // Length check
                if (password.length >= 8) {
                    strength += 25;
                }
                
                // Uppercase check
                if (/[A-Z]/.test(password)) {
                    strength += 25;
                }
                
                // Lowercase check
                if (/[a-z]/.test(password)) {
                    strength += 25;
                }
                
                // Number check
                if (/[0-9]/.test(password)) {
                    strength += 25;
                }
                
                // Special character check
                if (/[^A-Za-z0-9]/.test(password)) {
                    strength += 25;
                }
                
                // Cap at 100%
                strength = Math.min(strength, 100);
                
                // Set strength text
                if (strength < 25) {
                    strengthText = 'Very Weak';
                } else if (strength < 50) {
                    strengthText = 'Weak';
                } else if (strength < 75) {
                    strengthText = 'Moderate';
                } else if (strength < 100) {
                    strengthText = 'Strong';
                } else {
                    strengthText = 'Very Strong';
                }
            }
            
            // Update the strength meter
            const progressBar = strengthMeter.querySelector('.progress-bar');
            const strengthTextElement = strengthMeter.querySelector('.strength-text');
            
            progressBar.style.width = `${strength}%`;
            progressBar.setAttribute('aria-valuenow', strength);
            
            // Set the color based on strength
            if (strength < 25) {
                progressBar.className = 'progress-bar bg-danger';
            } else if (strength < 50) {
                progressBar.className = 'progress-bar bg-warning';
            } else if (strength < 75) {
                progressBar.className = 'progress-bar bg-info';
            } else {
                progressBar.className = 'progress-bar bg-success';
            }
            
            strengthTextElement.textContent = strengthText;
        });
    });
});
