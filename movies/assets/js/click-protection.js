/**
 * Download Button Click Protection with Ad System
 * ─────────────────────────────────────────────────
 * 1st click → opens a random ad URL in a new tab + shows "আবার ক্লিক করুন"
 * 2nd click → follows the real download href
 *
 * Ad URLs are fetched from /get_ad_links.php (populated via Dashboard → Direct Links)
 */

(function () {
    'use strict';

    // ── Ad pool (loaded async from database) ──
    var adPool = [];

    // Load ads from server
    function loadAdLinks() {
        fetch('/get_ad_links.php', { cache: 'no-store' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (Array.isArray(data) && data.length > 0) {
                    adPool = data;
                }
            })
            .catch(function () { /* silent */ });
    }

    // Pick a weighted-random ad from pool
    function pickAd() {
        if (adPool.length === 0) return null;
        // Simple random (priority weighting can be added later)
        return adPool[Math.floor(Math.random() * adPool.length)];
    }

    // Track click via PHP
    function trackClick(adId, context) {
        fetch('/track_ad_click.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ad_id: adId, context: context || 'download' })
        }).catch(function () { /* silent */ });
    }

    // ── Per-button click state ──
    var clickState = new WeakMap();

    // Visual feedback on button after 1st click
    function showFeedback(btn) {
        var orig     = btn.innerHTML;
        var origBg   = btn.style.background;

        btn.innerHTML = '<i class="fas fa-redo"></i>&nbsp; আবার ক্লিক করুন ↵';
        btn.style.background = '#10b981';

        var timer = setTimeout(function () {
            btn.innerHTML = orig;
            btn.style.background = origBg;
            clickState.set(btn, 0);
        }, 12000); // reset after 12 s if user doesn't click again

        // store timer so 2nd click can clear it
        btn._adTimer = timer;
    }

    // Main click handler (runs in capture phase to run before href)
    function handleClick(e) {
        var btn   = e.currentTarget;
        var count = clickState.get(btn) || 0;

        if (count === 0) {
            // ── FIRST CLICK: open ad, block navigation ──
            e.preventDefault();
            e.stopImmediatePropagation();

            var ad = pickAd();
            if (ad && ad.url) {
                window.open(ad.url, '_blank', 'noopener,noreferrer');
                trackClick(ad.id, btn.dataset.context || 'download');
            }

            clickState.set(btn, 1);
            showFeedback(btn);

        } else {
            // ── SECOND CLICK: allow normal href ──
            clearTimeout(btn._adTimer);
            clickState.set(btn, 0);
            // restore original text (if not already)
            // no preventDefault → browser follows the <a href>
        }
    }

    // Attach handler to all .download-btn links
    function applyProtection() {
        document.querySelectorAll('a.download-btn').forEach(function (btn) {
            if (btn.dataset.adProtected) return;
            btn.dataset.adProtected = '1';
            btn.addEventListener('click', handleClick, true); // capture
        });
    }

    // Init
    document.addEventListener('DOMContentLoaded', function () {
        loadAdLinks();
        applyProtection();
    });

    // Re-apply if buttons added dynamically (AJAX / SPA)
    new MutationObserver(function (mutations) {
        for (var i = 0; i < mutations.length; i++) {
            if (mutations[i].addedNodes.length) {
                applyProtection();
                break;
            }
        }
    }).observe(document.body, { childList: true, subtree: true });

})();
