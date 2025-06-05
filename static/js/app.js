document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('images');
    const previewSection = document.getElementById('imagePreview');
    const previewContainer = document.getElementById('previewContainer');
    const uploadForm = document.getElementById('uploadForm');
    const progressSection = document.getElementById('progressSection');
    const submitBtn = document.getElementById('submitBtn');

    // Handle file input change for preview
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            previewContainer.innerHTML = '';
            
            if (files.length > 0) {
                previewSection.style.display = 'block';
                
                files.forEach((file, index) => {
                    if (file.type.startsWith('image/')) {
                        const reader = new FileReader();
                        
                        reader.onload = function(e) {
                            const previewDiv = document.createElement('div');
                            previewDiv.className = 'position-relative';
                            previewDiv.innerHTML = `
                                <img src="${e.target.result}" 
                                     class="img-thumbnail preview-image" 
                                     style="width: 150px; height: 150px; object-fit: cover;" 
                                     alt="Förhandsvisning ${index + 1}">
                                <div class="position-absolute top-0 start-0">
                                    <span class="badge bg-primary">${index + 1}</span>
                                </div>
                                <div class="text-center mt-1">
                                    <small class="text-muted">${file.name}</small>
                                </div>
                            `;
                            previewContainer.appendChild(previewDiv);
                        };
                        
                        reader.readAsDataURL(file);
                    }
                });
            } else {
                previewSection.style.display = 'none';
            }
        });
    }

    // Handle form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            console.log('Form submitted');
            console.log('Files:', imageInput.files);
            console.log('Files length:', imageInput.files.length);
            
            const files = imageInput.files;
            const prompt = document.getElementById('prompt').value.trim();
            
            console.log('Prompt:', prompt);
            
            // Only validate prompt, let server handle file validation
            if (!prompt) {
                e.preventDefault();
                showAlert('Vänligen ange en prompt.', 'danger');
                return;
            }
            
            // Show progress
            showProgress();
        });
    }

    function showProgress() {
        if (progressSection) {
            progressSection.style.display = 'block';
            
            // Disable form elements
            const formElements = uploadForm.querySelectorAll('input, select, textarea, button');
            formElements.forEach(element => {
                element.disabled = true;
            });
            
            // Update submit button
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Genererar...
            `;
            
            // Scroll to progress section
            progressSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    function showAlert(message, type) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.container .col-lg-8');
        const firstCard = container.querySelector('.card');
        container.insertBefore(alertDiv, firstCard);
        
        // Scroll to alert
        alertDiv.scrollIntoView({ behavior: 'smooth' });
    }

    // Add tooltips to info icons
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add smooth scrolling for better UX
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Global function for handling image clicks in results page
function enlargeImage(imgSrc) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    
    if (modal && modalImage) {
        modalImage.src = imgSrc;
        new bootstrap.Modal(modal).show();
    }
}

// Add loading states for download buttons
document.addEventListener('click', function(e) {
    if (e.target.matches('a[href*="/download/"]') || e.target.closest('a[href*="/download/"]')) {
        const button = e.target.matches('a') ? e.target : e.target.closest('a');
        const originalContent = button.innerHTML;
        
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-1" role="status"></span>
            Laddar ner...
        `;
        
        // Reset button after 3 seconds
        setTimeout(() => {
            button.innerHTML = originalContent;
        }, 3000);
    }
});
