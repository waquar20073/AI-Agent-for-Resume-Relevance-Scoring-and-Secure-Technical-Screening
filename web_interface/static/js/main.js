// Main JavaScript file for AI Recruitment Agent

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        var target = $(this.getAttribute('href'));
        if (target.length) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 70
            }, 1000);
        }
    });

    // Form validation enhancements
    $('form').on('submit', function(e) {
        var form = $(this);
        var submitBtn = form.find('button[type="submit"]');
        
        // Add loading state to submit button
        if (submitBtn.length && !submitBtn.prop('disabled')) {
            submitBtn.prop('disabled', true);
            submitBtn.html('<i class="fas fa-spinner fa-spin me-2"></i>Processing...');
            
            // Re-enable button after 10 seconds (fallback)
            setTimeout(function() {
                submitBtn.prop('disabled', false);
                submitBtn.html(submitBtn.data('original-text') || 'Submit');
            }, 10000);
        }
    });

    // Store original button text
    $('button[type="submit"]').each(function() {
        $(this).data('original-text', $(this).html());
    });

    // File upload preview
    $('input[type="file"]').on('change', function() {
        var input = $(this);
        var file = input[0].files[0];
        
        if (file) {
            var fileSize = (file.size / 1024 / 1024).toFixed(2); // Convert to MB
            
            // Show file info
            var fileInfo = '<div class="alert alert-info mt-2">' +
                '<i class="fas fa-file me-2"></i>' +
                '<strong>Selected file:</strong> ' + file.name +
                ' <strong>(' + fileSize + ' MB)</strong>' +
                '</div>';
            
            // Remove previous file info
            input.siblings('.alert').remove();
            input.after(fileInfo);
        }
    });

    // Character counter for textareas
    $('textarea[maxlength]').each(function() {
        var textarea = $(this);
        var maxLength = parseInt(textarea.attr('maxlength'));
        
        // Add character counter
        var counter = $('<div class="text-muted small mt-1">' +
            '<span class="char-count">0</span> / ' + maxLength + ' characters' +
            '</div>');
        
        textarea.after(counter);
        
        // Update counter on input
        textarea.on('input', function() {
            var currentLength = $(this).val().length;
            counter.find('.char-count').text(currentLength);
            
            if (currentLength >= maxLength * 0.9) {
                counter.addClass('text-warning');
            } else {
                counter.removeClass('text-warning');
            }
        });
    });

    // Auto-resize textareas
    $('textarea').each(function() {
        var textarea = $(this);
        
        textarea.on('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Initial resize
        textarea.trigger('input');
    });

    // Copy to clipboard functionality
    $('.copy-btn').on('click', function() {
        var textToCopy = $(this).data('copy-text');
        var button = $(this);
        
        if (navigator.clipboard) {
            navigator.clipboard.writeText(textToCopy).then(function() {
                showCopySuccess(button);
            }).catch(function() {
                fallbackCopyText(textToCopy, button);
            });
        } else {
            fallbackCopyText(textToCopy, button);
        }
    });

    function showCopySuccess(button) {
        var originalHtml = button.html();
        button.html('<i class="fas fa-check me-1"></i>Copied!');
        button.removeClass('btn-outline-secondary').addClass('btn-success');
        
        setTimeout(function() {
            button.html(originalHtml);
            button.removeClass('btn-success').addClass('btn-outline-secondary');
        }, 2000);
    }

    function fallbackCopyText(text, button) {
        var textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showCopySuccess(button);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
        
        document.body.removeChild(textArea);
    }

    // Print functionality
    $('.print-btn').on('click', function() {
        window.print();
        return false;
    });

    // Confirm dangerous actions
    $('.confirm-action').on('click', function(e) {
        var message = $(this).data('confirm-message') || 'Are you sure you want to proceed?';
        
        if (!confirm(message)) {
            e.preventDefault();
            return false;
        }
    });

    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        let imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    let image = entry.target;
                    image.src = image.dataset.src;
                    image.classList.remove('lazy');
                    imageObserver.unobserve(image);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Network status indicator
    function updateNetworkStatus() {
        var isOnline = navigator.onLine;
        var statusIndicator = $('#network-status');
        
        if (statusIndicator.length === 0) {
            statusIndicator = $('<div id="network-status" class="network-status">' +
                '<i class="fas fa-wifi me-1"></i>' +
                '<span class="status-text">Online</span>' +
                '</div>');
            $('body').append(statusIndicator);
        }
        
        if (isOnline) {
            statusIndicator.removeClass('offline').addClass('online');
            statusIndicator.find('.status-text').text('Online');
            statusIndicator.find('i').removeClass('fa-wifi-slash').addClass('fa-wifi');
        } else {
            statusIndicator.removeClass('online').addClass('offline');
            statusIndicator.find('.status-text').text('Offline');
            statusIndicator.find('i').removeClass('fa-wifi').addClass('fa-wifi-slash');
        }
    }

    // Check network status on load and change
    updateNetworkStatus();
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);

    // Auto-save functionality for forms
    var autoSaveInterval;
    
    $('form[data-auto-save]').each(function() {
        var form = $(this);
        var saveUrl = form.data('auto-save');
        var saveKey = form.data('save-key') || 'form-' + form.attr('id');
        
        // Load saved data
        var savedData = localStorage.getItem(saveKey);
        if (savedData) {
            try {
                var data = JSON.parse(savedData);
                form.find('input, textarea, select').each(function() {
                    var field = $(this);
                    var name = field.attr('name');
                    if (name && data[name]) {
                        field.val(data[name]);
                    }
                });
            } catch (e) {
                console.error('Error loading saved form data:', e);
            }
        }
        
        // Auto-save on input
        form.on('input', function() {
            clearTimeout(autoSaveInterval);
            autoSaveInterval = setTimeout(function() {
                var formData = {};
                form.find('input, textarea, select').each(function() {
                    var field = $(this);
                    var name = field.attr('name');
                    if (name) {
                        formData[name] = field.val();
                    }
                });
                
                localStorage.setItem(saveKey, JSON.stringify(formData));
                
                // Optional: Send to server
                if (saveUrl) {
                    $.ajax({
                        url: saveUrl,
                        method: 'POST',
                        data: formData,
                        success: function() {
                            console.log('Form auto-saved successfully');
                        },
                        error: function() {
                            console.log('Failed to auto-save form');
                        }
                    });
                }
            }, 2000);
        });
        
        // Clear saved data on successful submission
        form.on('submit', function() {
            localStorage.removeItem(saveKey);
        });
    });

    // Keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl/Cmd + S to save forms
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            $('form:visible').first().submit();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            $('.modal.show').modal('hide');
        }
    });

    // Performance monitoring
    function logPerformance() {
        if ('performance' in window) {
            var loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            console.log('Page load time:', loadTime + 'ms');
        }
    }
    
    // Log performance after page load
    window.addEventListener('load', logPerformance);

    // Error handling
    window.addEventListener('error', function(e) {
        console.error('JavaScript error:', e.error);
        
        // Show user-friendly error message
        if (typeof showErrorMessage === 'function') {
            showErrorMessage('An unexpected error occurred. Please refresh the page and try again.');
        }
    });

    // Success message function
    window.showSuccessMessage = function(message) {
        var alert = $('<div class="alert alert-success alert-dismissible fade show" role="alert">' +
            '<i class="fas fa-check-circle me-2"></i>' + message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
            '</div>');
        
        $('.container').prepend(alert);
        
        setTimeout(function() {
            alert.fadeOut('slow', function() {
                $(this).remove();
            });
        }, 5000);
    };

    // Error message function
    window.showErrorMessage = function(message) {
        var alert = $('<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
            '<i class="fas fa-exclamation-triangle me-2"></i>' + message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
            '</div>');
        
        $('.container').prepend(alert);
        
        setTimeout(function() {
            alert.fadeOut('slow', function() {
                $(this).remove();
            });
        }, 5000);
    };

    // Loading indicator
    window.showLoading = function(message) {
        message = message || 'Loading...';
        
        var loading = $('<div class="loading-overlay">' +
            '<div class="loading-spinner">' +
            '<div class="spinner-border text-primary" role="status">' +
            '<span class="visually-hidden">Loading...</span>' +
            '</div>' +
            '<div class="loading-text">' + message + '</div>' +
            '</div>' +
            '</div>');
        
        $('body').append(loading);
    };

    window.hideLoading = function() {
        $('.loading-overlay').fadeOut('fast', function() {
            $(this).remove();
        });
    };

    console.log('AI Recruitment Agent - JavaScript initialized');
});
