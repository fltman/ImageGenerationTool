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

    // Handle form submission with AJAX
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Always prevent default form submission
            
            const files = imageInput.files;
            const prompt = document.getElementById('prompt').value.trim();
            const numVariants = document.getElementById('num_variants').value;
            
            // Basic validation
            if (files.length === 0) {
                showAlert('Vänligen välj minst en bild.', 'danger');
                return;
            }
            
            if (!prompt) {
                showAlert('Vänligen ange en prompt.', 'danger');
                return;
            }
            
            // Create FormData for AJAX upload
            const formData = new FormData();
            for (let file of files) {
                formData.append('images', file);
            }
            formData.append('prompt', prompt);
            formData.append('num_variants', numVariants);
            
            // Show progress section
            showProgress();
            
            // Start AJAX upload
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    startProgressPolling(data.task_id);
                } else {
                    hideProgress();
                    showAlert(data.error, 'danger');
                }
            })
            .catch(error => {
                hideProgress();
                showAlert('Ett fel uppstod vid uppladdning: ' + error.message, 'danger');
                console.error('Upload error:', error);
            });
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

    function hideProgress() {
        if (progressSection) {
            progressSection.style.display = 'none';
            
            // Re-enable form elements
            const formElements = uploadForm.querySelectorAll('input, select, textarea, button');
            formElements.forEach(element => {
                element.disabled = false;
            });
            
            // Reset submit button
            submitBtn.innerHTML = `
                <i class="bi bi-magic me-2"></i>
                Generera Varianter
            `;
        }
    }

    function startProgressPolling(taskId) {
        const pollInterval = setInterval(() => {
            fetch(`/progress/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateProgress(data.data);
                        
                        if (data.data.status === 'completed') {
                            clearInterval(pollInterval);
                            window.location.href = `/results/${taskId}`;
                        } else if (data.data.status === 'error') {
                            clearInterval(pollInterval);
                            hideProgress();
                            showAlert('Fel vid bildgenerering: ' + data.data.error, 'danger');
                        }
                    }
                })
                .catch(error => {
                    clearInterval(pollInterval);
                    hideProgress();
                    showAlert('Fel vid statusuppdatering: ' + error.message, 'danger');
                    console.error('Progress polling error:', error);
                });
        }, 2000); // Poll every 2 seconds
    }

    function updateProgress(progressData) {
        // Update progress text and bar
        const progressText = progressSection.querySelector('h5');
        const progressBar = document.getElementById('progressBar');
        const progressDetails = document.getElementById('progressDetails');
        
        if (progressData.status === 'processing') {
            progressText.textContent = `Bearbetar: ${progressData.current_file}`;
            progressDetails.textContent = `${progressData.completed_files} av ${progressData.total_files} filer klara`;
            if (progressBar) {
                progressBar.style.width = `${progressData.progress}%`;
                progressBar.setAttribute('aria-valuenow', progressData.progress);
            }
        } else if (progressData.status === 'started') {
            progressText.textContent = 'Startar bildgenerering...';
            progressDetails.textContent = 'Förbereder filer för bearbetning...';
            if (progressBar) {
                progressBar.style.width = '10%';
                progressBar.setAttribute('aria-valuenow', 10);
            }
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
