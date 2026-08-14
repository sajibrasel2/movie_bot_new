/**
 * Universal Click Protection with Ad System
 * First click → Ad opens in new tab
 * Second click → Goes to actual link
 */

(function() {
    'use strict';
    
    // Track clicks per element
    const clickTracker = new WeakMap();
    
    // Ad links (fetched from database via PHP)
    let adLinks = [];
    
    // Initialize ad links
    function initAdLinks() {
        // This will be populated by PHP
        if (window.DIRECT_AD_LINKS && Array.isArray(window.DIRECT_AD_LINKS)) {
            adLinks = window.DIRECT_AD_LINKS;
        }
    }
    
    // Get random ad link
    function getRandomAdLink() {
        if (adLinks.length === 0) return null;
        const randomIndex = Math.floor(Math.random() * adLinks.length);
        return adLinks[randomIndex];
    }
    
    // Track ad click
    function trackAdClick(adId) {
        // Send tracking request
        fetch('/movie_bot_new/movies/track_ad_click.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ad_id: adId })
        }).catch(err => console.error('Tracking failed:', err));
    }
    
    // Handle click with ad protection
    function handleProtectedClick(element, event) {
        // Get click count for this element
        let clickCount = clickTracker.get(element) || 0;
        
        if (clickCount === 0) {
            // First click - show ad
            event.preventDefault();
            event.stopPropagation();
            
            const adLink = getRandomAdLink();
            if (adLink) {
                // Open ad in new tab
                window.open(adLink.url, '_blank');
                
                // Track click
                trackAdClick(adLink.id);
                
                // Visual feedback
                showClickFeedback(element, 'Click again to continue');
            }
            
            // Increment click count
            clickTracker.set(element, 1);
            
            // Reset after 10 seconds
            setTimeout(() => {
                clickTracker.set(element, 0);
            }, 10000);
            
            return false;
        } else {
            // Second click - allow normal action
            clickTracker.set(element, 0);
            return true;
        }
    }
    
    // Show visual feedback
    function showClickFeedback(element, message) {
        const originalText = element.textContent || element.value;
        const isButton = element.tagName === 'BUTTON' || element.tagName === 'INPUT';
        const isLink = element.tagName === 'A';
        
        if (isButton) {
            element.textContent = message;
            element.style.background = '#10b981';
            
            setTimeout(() => {
                element.textContent = originalText;
                element.style.background = '';
            }, 3000);
        } else if (isLink) {
            const badge = document.createElement('span');
            badge.textContent = ' ✓ Click again';
            badge.style.cssText = 'background: #10b981; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 5px;';
            element.appendChild(badge);
            
            setTimeout(() => {
                badge.remove();
            }, 3000);
        }
    }
    
    // Apply click protection to all clickable elements
    function applyClickProtection() {
        // Protect all links (except navigation)
        document.querySelectorAll('a').forEach(link => {
            // Skip navigation links, logo, etc.
            if (link.classList.contains('no-ad-protection') || 
                link.closest('nav') || 
                link.closest('.navbar') ||
                link.closest('.footer') ||
                link.href.includes('#')) {
                return;
            }
            
            link.addEventListener('click', function(e) {
                return handleProtectedClick(this, e);
            });
        });
        
        // Protect download buttons specifically
        document.querySelectorAll('.download-btn, .btn-primary').forEach(button => {
            button.addEventListener('click', function(e) {
                return handleProtectedClick(this, e);
            });
        });
        
        // Protect search form
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                const submitButton = this.querySelector('button[type="submit"]');
                const clickCount = clickTracker.get(this) || 0;
                
                if (clickCount === 0) {
                    e.preventDefault();
                    
                    const adLink = getRandomAdLink();
                    if (adLink) {
                        window.open(adLink.url, '_blank');
                        trackAdClick(adLink.id);
                        
                        if (submitButton) {
                            const originalHTML = submitButton.innerHTML;
                            submitButton.innerHTML = '<i class="fas fa-check"></i> Search Again';
                            submitButton.style.background = '#10b981';
                            
                            setTimeout(() => {
                                submitButton.innerHTML = originalHTML;
                                submitButton.style.background = '';
                            }, 3000);
                        }
                    }
                    
                    clickTracker.set(this, 1);
                    
                    setTimeout(() => {
                        clickTracker.set(this, 0);
                    }, 10000);
                    
                    return false;
                }
            });
        }
        
        // Protect movie cards
        document.querySelectorAll('.movie-card').forEach(card => {
            card.addEventListener('click', function(e) {
                // Don't interfere with child element clicks
                if (e.target !== this && !e.target.closest('.movie-card-poster')) {
                    return;
                }
                
                return handleProtectedClick(this, e);
            });
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initAdLinks();
            applyClickProtection();
        });
    } else {
        initAdLinks();
        applyClickProtection();
    }
    
    // Reapply protection when new content is added (for AJAX)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                applyClickProtection();
            }
        });
    });
    
    // Observe document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
})();
