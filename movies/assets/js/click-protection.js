/**
 * Download Button Click Protection with Ad System
 * First click  → Ad opens in new tab, button shows "Click again to download"
 * Second click → Goes to actual download link
 *
 * Config: set AD_URL below to your ad network popunder/direct link URL
 */

(function () {
    'use strict';

    // =====================================================
    // ▼▼▼ আপনার Ad Network URL এখানে দিন ▼▼▼
    // =====================================================
    var AD_URL = window.SITE_AD_URL || '';
    // উদাহরণ: 'https://www.profitableratecpm.com/xxxxxxxx'
    // অথবা যেকোনো PopAds / Adsterra direct link URL
    // =====================================================

    // Click state per element (WeakMap so no memory leak)
    var clickState = new WeakMap();

    // Track ad click via PHP (optional analytics)
    function trackAdClick() {
        try {
            fetch('/track_ad_click.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ context: 'download_btn' })
            });
        } catch (e) { /* silent */ }
    }

    // Show feedback on button after first click
    function showFeedback(btn) {
        var original = btn.innerHTML;
        var originalBg = btn.style.background;

        btn.innerHTML = '<i class="fas fa-redo"></i> আবার ক্লিক করুন';
        btn.style.background = '#10b981';
        btn.style.transition = 'background 0.3s';

        // Reset after 12 seconds (if user doesn't click again)
        setTimeout(function () {
            btn.innerHTML = original;
            btn.style.background = originalBg;
            clickState.set(btn, 0);
        }, 12000);
    }

    // Handle protected click on a download button
    function handleDownloadClick(e) {
        var btn = e.currentTarget;
        var count = clickState.get(btn) || 0;

        if (count === 0) {
            // ── First click ──
            e.preventDefault();
            e.stopImmediatePropagation();

            // Open ad in new tab (if AD_URL is set)
            if (AD_URL && AD_URL.length > 5) {
                window.open(AD_URL, '_blank', 'noopener,noreferrer');
                trackAdClick();
            }

            clickState.set(btn, 1);
            showFeedback(btn);

        } else {
            // ── Second click ── allow the original href to work normally
            clickState.set(btn, 0);
            // do nothing → browser follows the <a href>
        }
    }

    // Apply protection to all .download-btn elements
    function applyProtection() {
        document.querySelectorAll('a.download-btn').forEach(function (btn) {
            // Avoid double-binding
            if (btn.dataset.adProtected) return;
            btn.dataset.adProtected = '1';
            btn.addEventListener('click', handleDownloadClick, true);
        });
    }

    // Init on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyProtection);
    } else {
        applyProtection();
    }

    // Re-apply if new buttons are added dynamically
    new MutationObserver(function (mutations) {
        for (var m of mutations) {
            if (m.addedNodes.length) {
                applyProtection();
                break;
            }
        }
    }).observe(document.body, { childList: true, subtree: true });

})();
