/**
 * WYSIWYG PDF Editor JavaScript
 *
 * This file contains the JavaScript code for the WYSIWYG PDF editor.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Helper function to show error messages
    function showErrorMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        // Get nonce for the error icon
        const errorNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
        alertDiv.innerHTML = `<i class="fas fa-exclamation-circle me-2" ${errorNonce ? 'nonce="' + errorNonce + '"' : ''}></i>${message}`;

        const container = document.querySelector('.card-body');
        if (container) {
            container.prepend(alertDiv);
        } else {
            console.error(message);
        }
    }

    // Check if PDF.js is loaded
    if (typeof pdfjsLib === 'undefined') {
        console.error('PDF.js library not loaded. Please check your Content Security Policy settings.');

        // Load PDF.js dynamically
        const loadPdfJs = function() {
            return new Promise((resolve, reject) => {
                // First load the main library
                const script = document.createElement('script');
                script.src = '/static/js/lib/pdf.min.js';
                script.setAttribute('nonce', document.querySelector('script[nonce]')?.getAttribute('nonce') || '');

                script.onload = function() {
                    console.log('PDF.js loaded dynamically');

                    // Then load the worker
                    const workerScript = document.createElement('script');
                    workerScript.src = '/static/js/lib/pdf.worker.min.js';
                    workerScript.setAttribute('nonce', document.querySelector('script[nonce]')?.getAttribute('nonce') || '');

                    workerScript.onload = function() {
                        console.log('PDF.js worker loaded dynamically');

                        // Set worker path
                        if (typeof pdfjsLib !== 'undefined') {
                            pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/js/lib/pdf.worker.min.js';
                            resolve();
                        } else {
                            reject(new Error('PDF.js still not available after loading'));
                        }
                    };

                    workerScript.onerror = function() {
                        reject(new Error('Failed to load PDF.js worker'));
                    };

                    document.head.appendChild(workerScript);
                };

                script.onerror = function() {
                    reject(new Error('Failed to load PDF.js'));
                };

                document.head.appendChild(script);
            });
        };

        // Try to load PDF.js
        loadPdfJs()
            .then(() => {
                console.log('PDF.js loaded successfully, initializing editor');
                // Initialize the editor after a short delay
                setTimeout(initEditor, 500);
            })
            .catch(error => {
                showErrorMessage(`PDF.js library could not be loaded: ${error.message}. Please refresh the page or try a different browser.`);
            });

        return;
    }

    // Initialize the editor
    initEditor();

    // Initialize the editor
    function initEditor() {
        // Variables
        let pdfDoc = null;
        let pageNum = 1;
        let pageRendering = false;
        let pageNumPending = null;
        let scale = 1.5;
        let canvas = document.getElementById('pdf-canvas');
        let textEditing = false;
        let lastClickTime = 0;
        const doubleClickDelay = 300; // ms

        // Check if canvas exists
        if (!canvas) {
            console.log('PDF canvas not found. This is normal if no PDF is uploaded yet.');
            return;
        }

        let ctx = canvas.getContext('2d');
        let textLayer = document.getElementById('text-layer');
        let editLayer = document.getElementById('edit-layer');
        let pdfData = null;
        let selectedText = null;
        let textEditorModal = null;
        let editTextContent = document.getElementById('edit-text-content');
        let editFontSize = document.getElementById('edit-font-size');
        let applyTextEditBtn = document.getElementById('apply-text-edit');
        let currentEditingElement = null;

        // Initialize Bootstrap modal if it exists
        if (document.getElementById('textEditorModal')) {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                textEditorModal = new bootstrap.Modal(document.getElementById('textEditorModal'));
            } else {
                console.warn('Bootstrap Modal not available. Text editing modal will not work.');
            }
        }

        // Check if we have a PDF URL
        const pdfUrl = document.getElementById('pdf-url');
        if (pdfUrl && pdfUrl.value) {
            try {
                // PDF.js document loading
                const loadingTask = pdfjsLib.getDocument(pdfUrl.value);
                loadingTask.promise.then(function(pdf) {
                    pdfDoc = pdf;
                    const pageCountElement = document.getElementById('page-count');
                    if (pageCountElement) {
                        pageCountElement.textContent = pdf.numPages;
                    }

                    // Initial page rendering
                    renderPage(pageNum);

                    // Fetch the PDF data for editing
                    fetch(pdfUrl.value)
                        .then(response => response.arrayBuffer())
                        .then(data => {
                            pdfData = data;
                        })
                        .catch(function(error) {
                            console.error('Error fetching PDF data:', error);
                            showErrorMessage('Error loading PDF data. Please try uploading the file again.');
                        });
                }).catch(function(error) {
                    console.error('Error loading PDF:', error);
                    showErrorMessage('Error loading PDF. Please try uploading the file again or use a different PDF.');
                });
            } catch (error) {
                console.error('Error initializing PDF.js:', error);
                showErrorMessage('Error initializing PDF viewer. Please refresh the page or try a different browser.');
            }
        } else {
            // No PDF URL found, show upload form
            const uploadForm = document.querySelector('form');
            if (uploadForm) {
                uploadForm.style.display = 'block';
            }

            // Show a helpful message
            const container = document.querySelector('.card-body');
            if (container) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-info';
                // Get nonce for the info icon
                const infoNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                alertDiv.innerHTML = `
                    <i class="fas fa-info-circle me-2" ${infoNonce ? 'nonce="' + infoNonce + '"' : ''}></i>
                    Please upload a PDF file to start editing.
                `;
                container.prepend(alertDiv);
            }
        }

        // Render the page
        function renderPage(num) {
            if (!pdfDoc) {
                console.error('No PDF document loaded');
                return;
            }

            pageRendering = true;

            // Get page
            pdfDoc.getPage(num).then(function(page) {
                // Set scale
                const viewport = page.getViewport({ scale: scale });
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                // Render PDF page into canvas context
                const renderContext = {
                    canvasContext: ctx,
                    viewport: viewport
                };

                const renderTask = page.render(renderContext);

                // Clear previous text layer
                textLayer.innerHTML = '';

                // Update text layer dimensions
                textLayer.setAttribute('style', `width: ${viewport.width}px; height: ${viewport.height}px;`);

                // Ensure nonce is set
                const layerNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                if (layerNonce && !textLayer.hasAttribute('nonce')) {
                    textLayer.setAttribute('nonce', layerNonce);
                }

                // Get text content
                page.getTextContent().then(function(textContent) {
                    // Create text layer
                    const textLayerDiv = textLayer;

                    // Update text layer position and dimensions
                    let layerStyle = textLayerDiv.getAttribute('style') || '';
                    textLayerDiv.setAttribute('style', `${layerStyle}; left: ${canvas.offsetLeft}px; top: ${canvas.offsetTop}px; height: ${canvas.height}px; width: ${canvas.width}px;`);

                    // Ensure nonce is set
                    const layerNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                    if (layerNonce && !textLayerDiv.hasAttribute('nonce')) {
                        textLayerDiv.setAttribute('nonce', layerNonce);
                    }

                    // Create text elements
                    textContent.items.forEach(function(item, index) {
                        const tx = pdfjsLib.Util.transform(
                            viewport.transform,
                            item.transform
                        );

                        const style = textContent.styles[item.fontName];

                        // Calculate positions
                        const angle = Math.atan2(tx[1], tx[0]);
                        const fontHeight = Math.sqrt((tx[2] * tx[2]) + (tx[3] * tx[3]));
                        const fontAscent = fontHeight;

                        // Create text element
                        const textElement = document.createElement('div');
                        textElement.setAttribute('data-index', index);
                        textElement.setAttribute('data-text', item.str);
                        textElement.setAttribute('data-font-size', fontHeight);
                        textElement.setAttribute('data-font-name', item.fontName);
                        textElement.setAttribute('data-transform', item.transform.join(','));
                        textElement.setAttribute('data-page', num);

                        // Set text content
                        textElement.textContent = item.str;

                        // Set position and style using setAttribute to support nonce
                        const styleString = `left: ${tx[4]}px; top: ${tx[5] - fontAscent}px; font-size: ${fontHeight}px; font-family: ${style ? style.fontFamily : 'sans-serif'}; position: absolute; cursor: text; user-select: text; pointer-events: auto;`;
                        textElement.setAttribute('style', styleString);

                        // Get nonce from any existing script with nonce
                        const nonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                        if (nonce) {
                            textElement.setAttribute('nonce', nonce);
                        }

                        // Add click event for editing
                        textElement.addEventListener('click', function(e) {
                            e.stopPropagation();
                            handleTextElementClick(textElement, e);
                        });

                        // Add double-tap support for mobile
                        let touchTimeout;
                        textElement.addEventListener('touchstart', function(e) {
                            if (touchTimeout) {
                                // Double tap detected
                                clearTimeout(touchTimeout);
                                touchTimeout = null;
                                e.preventDefault();
                                makeElementEditable(textElement);
                            } else {
                                touchTimeout = setTimeout(function() {
                                    touchTimeout = null;
                                    // Single tap - just select
                                    selectTextElement(textElement);
                                }, 300);
                            }
                        });

                        // Add to text layer
                        textLayerDiv.appendChild(textElement);
                    });
                });

                // Wait for rendering to finish
                renderTask.promise.then(function() {
                    pageRendering = false;
                    if (pageNumPending !== null) {
                        // New page rendering is pending
                        renderPage(pageNumPending);
                        pageNumPending = null;
                    }
                });
            }).catch(function(error) {
                console.error('Error rendering page:', error);
                pageRendering = false;
                showErrorMessage(`Error rendering page ${num}: ${error.message}`);
            });

            // Update page counters
            const pageNumInput = document.getElementById('page-num');
            if (pageNumInput) {
                pageNumInput.value = num;
            }
        }

        // Select text element for editing
        function selectTextElement(element) {
            // Clear previous selection
            if (selectedText) {
                // Update style to remove background and border
                let currentStyle = selectedText.getAttribute('style') || '';
                currentStyle = currentStyle
                    .replace(/background-color:[^;]+;?/g, '')
                    .replace(/border:[^;]+;?/g, '');
                selectedText.setAttribute('style', currentStyle);

                // Ensure nonce is set
                const nonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                if (nonce && !selectedText.hasAttribute('nonce')) {
                    selectedText.setAttribute('nonce', nonce);
                }
            }

            // Set new selection
            selectedText = element;

            // Update style with background and border
            let currentStyle = selectedText.getAttribute('style') || '';
            selectedText.setAttribute('style', `${currentStyle}; background-color: rgba(35, 130, 135, 0.2); border: 1px solid #238287;`);

            // Ensure nonce is set
            const nonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
            if (nonce && !selectedText.hasAttribute('nonce')) {
                selectedText.setAttribute('nonce', nonce);
            }

            // Open editor modal if it exists
            if (textEditorModal) {
                currentEditingElement = element;
                editTextContent.value = element.textContent;

                // Get font size with fallback
                let fontSize = parseFloat(element.getAttribute('data-font-size'));
                if (isNaN(fontSize)) {
                    fontSize = parseFloat(window.getComputedStyle(element).fontSize) || 12;
                }

                editFontSize.value = Math.round(fontSize);

                // Show the modal
                textEditorModal.show();

                // Focus on the text content field
                setTimeout(() => {
                    editTextContent.focus();
                    editTextContent.select();
                }, 100);
            }
        }

        // Handle double-click for direct editing
        function handleTextElementClick(element, event) {
            const now = Date.now();
            if (now - lastClickTime < doubleClickDelay) {
                // Double click - enable direct editing
                event.stopPropagation();
                makeElementEditable(element);
            } else {
                // Single click - select for modal editing
                selectTextElement(element);
            }
            lastClickTime = now;
        }

        // Make an element directly editable
        function makeElementEditable(element) {
            // Store original content for cancel
            element.setAttribute('data-original-content', element.textContent);

            // Make editable
            element.contentEditable = true;

            // Update style for editing
            let currentStyle = element.getAttribute('style') || '';
            element.setAttribute('style', `${currentStyle}; background-color: rgba(255, 255, 255, 0.9); border: 1px dashed #238287; padding: 2px; outline: none;`);

            // Ensure nonce is set
            const nonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
            if (nonce && !element.hasAttribute('nonce')) {
                element.setAttribute('nonce', nonce);
            }

            // Focus and select all text
            element.focus();
            document.execCommand('selectAll', false, null);

            textEditing = true;
            currentEditingElement = element;

            // Add event listeners for saving/canceling
            element.addEventListener('blur', finishEditing);
            element.addEventListener('keydown', handleEditKeydown);
        }

        // Handle keydown events during direct editing
        function handleEditKeydown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                // Enter without shift - save changes
                event.preventDefault();
                finishEditing.call(this, event, true);
            } else if (event.key === 'Escape') {
                // Escape - cancel changes
                event.preventDefault();
                finishEditing.call(this, event, false);
            }
        }

        // Finish direct editing
        function finishEditing(event, save = true) {
            if (!textEditing || !currentEditingElement) return;

            const element = currentEditingElement;

            // Remove event listeners
            element.removeEventListener('blur', finishEditing);
            element.removeEventListener('keydown', handleEditKeydown);

            // Make non-editable
            element.contentEditable = false;

            // Update style to remove editing styles
            let currentStyle = element.getAttribute('style') || '';
            currentStyle = currentStyle
                .replace(/background-color:[^;]+;?/g, '')
                .replace(/border:[^;]+;?/g, '')
                .replace(/padding:[^;]+;?/g, '')
                .replace(/outline:[^;]+;?/g, '');
            element.setAttribute('style', currentStyle);

            // Ensure nonce is set
            const nonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
            if (nonce && !element.hasAttribute('nonce')) {
                element.setAttribute('nonce', nonce);
            }

            if (save) {
                // Save changes
                const newText = element.textContent;

                // Store the changes for saving
                element.setAttribute('data-modified', 'true');
                element.setAttribute('data-new-text', newText);

                // Visual feedback
                let feedbackStyle = element.getAttribute('style') || '';
                element.setAttribute('style', `${feedbackStyle}; background-color: rgba(35, 130, 135, 0.1);`);

                // Ensure nonce is set
                const nonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                if (nonce && !element.hasAttribute('nonce')) {
                    element.setAttribute('nonce', nonce);
                }

                setTimeout(() => {
                    let currentStyle = element.getAttribute('style') || '';
                    currentStyle = currentStyle.replace(/background-color:[^;]+;?/g, '');
                    element.setAttribute('style', currentStyle);
                }, 500);
            } else {
                // Restore original content
                element.textContent = element.getAttribute('data-original-content');
            }

            textEditing = false;
            currentEditingElement = null;
        }

        // Apply text edit from modal
        if (applyTextEditBtn) {
            applyTextEditBtn.addEventListener('click', function() {
                if (!currentEditingElement) return;

                // Update the text element
                const newText = editTextContent.value;
                const newFontSize = parseFloat(editFontSize.value);
                const originalFontSize = parseFloat(currentEditingElement.getAttribute('data-font-size')) ||
                    parseFloat(window.getComputedStyle(currentEditingElement).fontSize) || 12;
                const scaleFactor = newFontSize / originalFontSize;

                // Update the element
                currentEditingElement.textContent = newText;

                // Update style with new font size
                let currentStyle = currentEditingElement.getAttribute('style') || '';
                currentStyle = currentStyle.replace(/font-size:[^;]+;?/g, '');
                currentEditingElement.setAttribute('style', `${currentStyle}; font-size: ${newFontSize}px;`);

                // Ensure nonce is set
                const nonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                if (nonce && !currentEditingElement.hasAttribute('nonce')) {
                    currentEditingElement.setAttribute('nonce', nonce);
                }

                // Store the changes for saving
                currentEditingElement.setAttribute('data-modified', 'true');
                currentEditingElement.setAttribute('data-new-text', newText);
                currentEditingElement.setAttribute('data-new-font-size', newFontSize);

                // Visual feedback
                currentStyle = currentEditingElement.getAttribute('style') || '';
                currentEditingElement.setAttribute('style', `${currentStyle}; background-color: rgba(35, 130, 135, 0.1);`);

                setTimeout(() => {
                    let updatedStyle = currentEditingElement.getAttribute('style') || '';
                    updatedStyle = updatedStyle.replace(/background-color:[^;]+;?/g, '');
                    currentEditingElement.setAttribute('style', updatedStyle);
                }, 500);

                // Close the modal
                textEditorModal.hide();
            });
        }

        // Save changes to the PDF
        const saveChangesBtn = document.getElementById('save-changes');
        if (saveChangesBtn) {
            saveChangesBtn.addEventListener('click', async function() {
                try {
                    // Finish any ongoing direct editing
                    if (textEditing && currentEditingElement) {
                        finishEditing.call(currentEditingElement, null, true);
                    }

                    // Get all modified text elements
                    const modifiedElements = document.querySelectorAll('[data-modified="true"]');

                    if (modifiedElements.length === 0) {
                        // Show message in a more user-friendly way
                        const alertDiv = document.createElement('div');
                        alertDiv.className = 'alert alert-info alert-dismissible fade show';
                        // Get nonce for the info icon
                        const infoNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                        alertDiv.innerHTML = `
                            <i class="fas fa-info-circle me-2" ${infoNonce ? 'nonce="' + infoNonce + '"' : ''}></i>
                            No changes to save. Edit text by clicking on it.
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" ${infoNonce ? 'nonce="' + infoNonce + '"' : ''}></button>
                        `;

                        const container = document.querySelector('.card-body');
                        if (container) {
                            container.prepend(alertDiv);
                            // Auto-dismiss after 5 seconds
                            setTimeout(() => {
                                alertDiv.remove();
                            }, 5000);
                        } else {
                            alert('No changes to save.');
                        }
                        return;
                    }

                    // Show loading indicator
                    this.disabled = true;
                    // Get nonce from any existing script with nonce
                    const btnNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                    const spinnerHTML = `<i class="fas fa-spinner fa-spin me-2" ${btnNonce ? 'nonce="' + btnNonce + '"' : ''}></i> Saving...`;
                    this.innerHTML = spinnerHTML;

                    // Show progress message
                    const progressAlert = document.createElement('div');
                    progressAlert.className = 'alert alert-info';
                    progressAlert.id = 'save-progress-alert';
                    // Get nonce for the spinner
                    const alertNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                    progressAlert.innerHTML = `
                        <i class="fas fa-spinner fa-spin me-2" ${alertNonce ? 'nonce="' + alertNonce + '"' : ''}></i>
                        Saving ${modifiedElements.length} text modifications...
                    `;

                    const container = document.querySelector('.card-body');
                    if (container) {
                        container.prepend(progressAlert);
                    }

                    // Prepare data for server-side processing
                    const formData = new FormData();
                    const filenameElement = document.getElementById('pdf-filename');
                    if (!filenameElement || !filenameElement.value) {
                        throw new Error('No PDF filename found. Please upload a PDF file first.');
                    }

                    formData.append('filename', filenameElement.value);

                    // Add modified elements data
                    const modifications = [];
                    modifiedElements.forEach(element => {
                        // Get page number with fallback
                        const page = parseInt(element.getAttribute('data-page')) || pageNum;

                        // Get index with fallback
                        let index = parseInt(element.getAttribute('data-index'));
                        if (isNaN(index)) {
                            // Generate a unique index if not available
                            index = Array.from(textLayer.children).indexOf(element);
                        }

                        // Get original text with fallback
                        const originalText = element.getAttribute('data-text') ||
                                            element.getAttribute('data-original-content') ||
                                            '';

                        // Get new text
                        const newText = element.getAttribute('data-new-text') || element.textContent;

                        // Get transform with fallback
                        let transform;
                        try {
                            transform = element.getAttribute('data-transform').split(',').map(Number);
                        } catch (e) {
                            // Default transform if not available
                            transform = [1, 0, 0, 1,
                                        parseFloat(element.style.left) || 0,
                                        parseFloat(element.style.top) || 0];
                        }

                        // Get font name with fallback
                        const fontName = element.getAttribute('data-font-name') || 'helv';

                        // Get font sizes with fallbacks
                        let fontSize = parseFloat(element.getAttribute('data-font-size'));
                        if (isNaN(fontSize)) {
                            fontSize = parseFloat(window.getComputedStyle(element).fontSize) || 12;
                        }

                        let newFontSize = parseFloat(element.getAttribute('data-new-font-size'));
                        if (isNaN(newFontSize)) {
                            newFontSize = fontSize;
                        }

                        modifications.push({
                            page,
                            index,
                            originalText,
                            newText,
                            transform,
                            fontName,
                            fontSize,
                            newFontSize
                        });
                    });

                    formData.append('modifications', JSON.stringify(modifications));

                    // Send to server
                    const response = await fetch('/edit/save-wysiwyg-edits', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                    }

                    const result = await response.json();

                    if (result.error) {
                        throw new Error(result.error);
                    }

                    // Remove progress alert
                    const progressElement = document.getElementById('save-progress-alert');
                    if (progressElement) {
                        progressElement.remove();
                    }

                    // Show success message
                    const successAlert = document.createElement('div');
                    successAlert.className = 'alert alert-success alert-dismissible fade show';
                    // Get nonce for the success icon
                    const successNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                    successAlert.innerHTML = `
                        <i class="fas fa-check-circle me-2" ${successNonce ? 'nonce="' + successNonce + '"' : ''}></i>
                        Changes saved successfully! Applied ${result.modifications_applied} text modifications.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" ${successNonce ? 'nonce="' + successNonce + '"' : ''}></button>
                    `;

                    if (container) {
                        container.prepend(successAlert);
                        // Auto-dismiss after 5 seconds
                        setTimeout(() => {
                            successAlert.remove();
                        }, 5000);
                    }

                    // Reset modified flags
                    modifiedElements.forEach(element => {
                        element.removeAttribute('data-modified');
                        element.removeAttribute('data-new-text');
                        element.removeAttribute('data-new-font-size');
                        element.removeAttribute('data-original-content');
                    });

                    // Redirect to the same page with the output filename
                    const redirectUrl = new URL(window.location.href);
                    redirectUrl.searchParams.set('filename', filenameElement.value);
                    redirectUrl.searchParams.set('page', pageNum);
                    redirectUrl.searchParams.set('output', result.output_filename);

                    // Delay redirect slightly to show the success message
                    setTimeout(() => {
                        window.location.href = redirectUrl.toString();
                    }, 1000);

                } catch (error) {
                    console.error('Error saving changes:', error);

                    // Remove progress alert if it exists
                    const progressElement = document.getElementById('save-progress-alert');
                    if (progressElement) {
                        progressElement.remove();
                    }

                    // Show error message
                    const errorAlert = document.createElement('div');
                    errorAlert.className = 'alert alert-danger alert-dismissible fade show';
                    // Get nonce for the error icon
                    const errorNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                    errorAlert.innerHTML = `
                        <i class="fas fa-exclamation-circle me-2" ${errorNonce ? 'nonce="' + errorNonce + '"' : ''}></i>
                        Error saving changes: ${error.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" ${errorNonce ? 'nonce="' + errorNonce + '"' : ''}></button>
                    `;

                    const container = document.querySelector('.card-body');
                    if (container) {
                        container.prepend(errorAlert);
                    } else {
                        alert('Error saving changes: ' + error.message);
                    }

                    // Reset button
                    this.disabled = false;
                    // Get nonce for the save icon
                    const resetNonce = document.querySelector('script[nonce]')?.getAttribute('nonce');
                    this.innerHTML = `<i class="fas fa-save me-2" ${resetNonce ? 'nonce="' + resetNonce + '"' : ''}></i> Save Changes`;
                }
            });
        }

        // Download the edited PDF
        const downloadPdfBtn = document.getElementById('download-pdf');
        if (downloadPdfBtn) {
            downloadPdfBtn.addEventListener('click', function() {
                // Redirect to download URL
                const downloadUrl = '/edit/download-edited/' +
                    (document.getElementById('output-filename')?.value || document.getElementById('pdf-filename')?.value);

                if (!downloadUrl.endsWith('/')) {
                    window.location.href = downloadUrl;
                } else {
                    alert('Please save your changes first before downloading.');
                }
            });
        }

        // Previous page button
        const prevPageBtn = document.getElementById('prev-page');
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', function() {
                if (pageNum <= 1) {
                    return;
                }
                pageNum--;
                queueRenderPage(pageNum);
            });
        }

        // Next page button
        const nextPageBtn = document.getElementById('next-page');
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', function() {
                if (!pdfDoc || pageNum >= pdfDoc.numPages) {
                    return;
                }
                pageNum++;
                queueRenderPage(pageNum);
            });
        }

        // Page input
        const pageNumInput = document.getElementById('page-num');
        if (pageNumInput) {
            pageNumInput.addEventListener('change', function() {
                if (!pdfDoc) return;

                const num = parseInt(this.value);
                if (num >= 1 && num <= pdfDoc.numPages) {
                    pageNum = num;
                    queueRenderPage(pageNum);
                } else {
                    this.value = pageNum;
                }
            });
        }

        // Zoom in button
        const zoomInBtn = document.getElementById('zoom-in');
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', function() {
                scale *= 1.2;
                queueRenderPage(pageNum);
            });
        }

        // Zoom out button
        const zoomOutBtn = document.getElementById('zoom-out');
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', function() {
                scale /= 1.2;
                queueRenderPage(pageNum);
            });
        }

        // Queue rendering of a page
        function queueRenderPage(num) {
            if (pageRendering) {
                pageNumPending = num;
            } else {
                renderPage(num);
            }
        }
    }
});
