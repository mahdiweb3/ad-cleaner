// ponytail: YouTube ads die by seeking the ad to its end; that keeps the player
// and the real video intact (no fake player, no stream rewriting). If YouTube
// ever serves ads without the .ad-showing class this needs a new hook.
(() => {
  const AD = '.ad-showing, .ad-interrupting';
  const JUNK = [
    'ytd-enforcement-message-view-model',      // "ad blocker detected" wall
    'ytd-popup-container tp-yt-paper-dialog:has(ytd-enforcement-message-view-model)',
    '.ytp-ad-overlay-slot', '.ytp-ad-image-overlay', '.ytp-ad-text-overlay',
    '.ytp-ad-survey', '.ytp-ad-progress-list',
    '#masthead-ad', 'ytd-display-ad-renderer', 'ytd-ad-slot-renderer',
    'ytd-promoted-sparkles-web-renderer', 'ytd-in-feed-ad-layout-renderer',
    'ytd-banner-promo-renderer', 'ytd-statement-banner-renderer',
    'ytm-companion-slot', 'ytd-companion-slot-renderer'
  ].join(',');

  const killDom = (root) => {
    let n = 0;
    try {
      root.querySelectorAll(JUNK).forEach(el => {
        const holder = el.closest('tp-yt-paper-dialog') || el.closest('#movie_player');
        if (el.matches('ytd-enforcement-message-view-model')) {
          const dlg = el.closest('tp-yt-paper-dialog') || el.parentElement;
          if (dlg) { dlg.remove(); n++; }
        } else el.remove();
        if (holder && holder.id === 'movie_player') holder.classList.remove('ad-interrupting');
      });
    } catch (e) { /* :has() unsupported -> ignore */ }
    return n;
  };

  const skipAd = () => {
    const player = document.getElementById('movie_player');
    const video = player && player.querySelector('video');
    if (!video || !document.querySelector(AD)) return;

    // Kill the ad slot first so the player stops requesting more.
    player.querySelectorAll('.ytp-ad-module, .video-ads').forEach(el => el.replaceChildren());

    if (isFinite(video.duration) && video.duration > 0) {
      const target = video.duration - 0.1;
      if (video.currentTime < target) video.currentTime = target;
    } else if (video.currentTime > 0) {
      video.currentTime = 1e5; // live/unknown duration ad: jump past it
    }
    if (video.paused) video.play().catch(() => {});
  };

  const tick = () => { killDom(document); skipAd(); };

  // Ads start inside the first second of a navigation; run before anything else.
  tick();
  document.addEventListener('DOMContentLoaded', tick, { once: true });
  document.addEventListener('yt-navigate-finish', () => setTimeout(tick, 50), true);

  let queued = false;
  new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; tick(); });
  }).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });

  // Video element survives SPA navigations, so bind once per player.
  setInterval(() => {
    const v = document.querySelector('#movie_player video');
    if (v && !v.dataset.adclean) {
      v.dataset.adclean = '1';
      v.addEventListener('loadedmetadata', tick);
      v.addEventListener('durationchange', tick);
    }
  }, 1000);
})();
