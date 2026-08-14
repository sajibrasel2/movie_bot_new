// =====================================================
// Movie Website JavaScript
// movies.techandclick.site
// =====================================================

document.addEventListener('DOMContentLoaded', function() {
    initNavbar();
    initSearch();
    initMovieCards();
    initScrollToTop();
    handleImageErrors();
});

// Navbar scroll effect
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

// Search functionality
function initSearch() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');

    if (!searchForm || !searchInput) return;

    // Create dropdown container
    const dropdown = document.createElement('div');
    dropdown.id = 'searchDropdown';
    dropdown.style.cssText = `
        position: absolute; top: 100%; left: 0; right: 0;
        background: #1a1a1a; border: 1px solid #333; border-top: none;
        border-radius: 0 0 8px 8px; z-index: 9999;
        max-height: 420px; overflow-y: auto; display: none;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
    `;
    searchForm.style.position = 'relative';
    searchForm.appendChild(dropdown);

    // Prevent form submit navigating away
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const q = searchInput.value.trim();
        if (q.length > 1) fetchResults(q);
    });

    let debounceTimer;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const q = this.value.trim();
        if (q.length < 2) { hideDropdown(); return; }
        debounceTimer = setTimeout(() => fetchResults(q), 280);
    });

    // Hide on click outside
    document.addEventListener('click', function(e) {
        if (!searchForm.contains(e.target)) hideDropdown();
    });

    function fetchResults(q) {
        fetch('/api/search.php?q=' + encodeURIComponent(q))
            .then(r => r.json())
            .then(results => renderDropdown(results, q))
            .catch(() => hideDropdown());
    }

    function renderDropdown(results, q) {
        if (!results || results.length === 0) {
            dropdown.innerHTML = `
                <div style="padding:16px;text-align:center;color:#888;font-size:0.9rem;">
                    No results for "<strong style="color:#fff">${escHtml(q)}</strong>"
                </div>`;
            showDropdown();
            return;
        }

        dropdown.innerHTML = results.map(m => {
            const qualities = (m.qualities || []).map(q =>
                `<span style="background:#E50914;color:#fff;font-size:0.65rem;font-weight:700;
                              padding:1px 6px;border-radius:3px;margin-left:4px;">${escHtml(q)}</span>`
            ).join('');

            const poster = m.poster_url
                ? `<img src="${escHtml(m.poster_url)}" style="width:36px;height:50px;object-fit:cover;border-radius:3px;flex-shrink:0;">`
                : `<div style="width:36px;height:50px;background:#333;border-radius:3px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🎬</div>`;

            return `
            <div onclick="window.location.href='/movie.php?slug=${escHtml(m.slug)}'"
                 style="display:flex;align-items:center;gap:12px;padding:10px 14px;
                        cursor:pointer;border-bottom:1px solid #2a2a2a;transition:background 0.15s;"
                 onmouseover="this.style.background='rgba(229,9,20,0.12)'"
                 onmouseout="this.style.background='transparent'">
                ${poster}
                <div style="flex:1;min-width:0;">
                    <div style="font-size:0.9rem;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        ${escHtml(m.movie_title)}
                    </div>
                    <div style="margin-top:3px;display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
                        ${m.year ? `<span style="font-size:0.75rem;color:#888;">${m.year}</span>` : ''}
                        ${qualities}
                    </div>
                </div>
                <i class="fas fa-chevron-right" style="color:#555;font-size:0.8rem;flex-shrink:0;"></i>
            </div>`;
        }).join('');

        showDropdown();
    }

    function showDropdown() { dropdown.style.display = 'block'; }
    function hideDropdown() { dropdown.style.display = 'none'; }

    function escHtml(str) {
        return String(str || '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
}

// Movie card interactions
function initMovieCards() {
    const movieCards = document.querySelectorAll('.movie-card');
    
    movieCards.forEach(card => {
        card.addEventListener('click', function() {
            const slug = this.dataset.slug;
            if (slug) {
                window.location.href = '/movie.php?slug=' + slug;
            }
        });
    });
}

// Copy download link
function copyDownloadLink(url, buttonElement) {
    navigator.clipboard.writeText(url).then(() => {
        const originalText = buttonElement.innerHTML;
        buttonElement.innerHTML = '<i class="fas fa-check"></i> Copied!';
        buttonElement.style.background = '#10b981';
        
        setTimeout(() => {
            buttonElement.innerHTML = originalText;
            buttonElement.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Track download click
function trackDownload(movieId, source) {
    fetch('/api/track_download.php', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            movie_id: movieId,
            source: source
        })
    }).catch(err => console.error('Tracking failed:', err));
}

// Lazy loading images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Show loading spinner
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.id = 'loadingSpinner';
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Time ago formatter
function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60,
        second: 1
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return interval + ' ' + unit + (interval > 1 ? 's' : '') + ' ago';
        }
    }
    
    return 'just now';
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLazyLoading);
} else {
    initLazyLoading();
}

// Scroll to top functionality
function initScrollToTop() {
    // Create button if doesn't exist
    let scrollBtn = document.getElementById('scrollToTop');
    if (!scrollBtn) {
        scrollBtn = document.createElement('button');
        scrollBtn.id = 'scrollToTop';
        scrollBtn.className = 'scroll-to-top';
        scrollBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
        scrollBtn.setAttribute('aria-label', 'Scroll to top');
        document.body.appendChild(scrollBtn);
    }
    
    // Show/hide on scroll
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollBtn.classList.add('show');
        } else {
            scrollBtn.classList.remove('show');
        }
    });
    
    // Scroll to top on click
    scrollBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Handle image loading errors
function handleImageErrors() {
    const images = document.querySelectorAll('.movie-card img');
    
    images.forEach(img => {
        img.addEventListener('error', function() {
            // Create placeholder
            const placeholder = document.createElement('div');
            placeholder.className = 'img-placeholder';
            placeholder.innerHTML = '🎬';
            placeholder.style.cssText = this.style.cssText;
            
            // Replace image with placeholder
            if (this.parentNode) {
                this.parentNode.replaceChild(placeholder, this);
            }
        });
        
        // Add loading class
        img.addEventListener('load', function() {
            this.style.opacity = '1';
        });
    });
}


// Quality tab switcher for multi-quality movies
function initQualityTabs() {
    const qualityTabs = document.querySelectorAll('.quality-tab');
    const qualityContents = document.querySelectorAll('.quality-content');
    
    if (qualityTabs.length === 0) return;
    
    qualityTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const quality = this.dataset.quality;
            
            // Remove active class from all tabs and contents
            qualityTabs.forEach(t => t.classList.remove('active'));
            qualityContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            this.classList.add('active');
            
            const activeContent = document.querySelector(`.quality-content[data-quality="${quality}"]`);
            if (activeContent) {
                activeContent.classList.add('active');
            }
            
            // Smooth scroll to download section
            const downloadSection = document.getElementById('download');
            if (downloadSection) {
                downloadSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    });
}

// Initialize quality tabs on movie page
document.addEventListener('DOMContentLoaded', function() {
    initQualityTabs();
});
