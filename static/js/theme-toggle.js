/**
 * NextReel — theme-toggle.js
 * Handles: theme switching, nav scroll effect, mobile menu, toast auto-dismiss
 */

(function () {
  'use strict';

  /* ============================================================
     CSRF TOKEN HELPER
     ============================================================ */

  /**
   * Read a cookie value by name.
   * @param {string} name
   * @returns {string|null}
   */
  function getCookie(name) {
    if (!document.cookie) return null;
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }


  /* ============================================================
     THEME MANAGEMENT
     ============================================================ */

  const STORAGE_KEY    = 'nextreel-theme';
  const DARK_THEME     = 'dark';
  const WARM_THEME     = 'warm';
  const ICON_DARK      = '🌙';   // shown when current theme is dark  (click → go warm)
  const ICON_WARM      = '☀️';   // shown when current theme is warm  (click → go dark)

  /**
   * Apply a theme to the root element and update the toggle button icon.
   * @param {'dark'|'warm'} theme
   */
  function applyTheme(theme) {
    if (theme === WARM_THEME) {
      document.documentElement.dataset.theme = WARM_THEME;
    } else {
      // Dark is the default — no data-theme attribute needed
      delete document.documentElement.dataset.theme;
    }
    updateToggleIcon(theme);
  }

  /**
   * Update the visible icon on every theme-toggle button on the page.
   * @param {'dark'|'warm'} currentTheme
   */
  function updateToggleIcon(currentTheme) {
    document.querySelectorAll('.theme-toggle, #theme-toggle').forEach(function (btn) {
      // When it's dark, show the ☀️ icon (clicking takes you to warm)
      // When it's warm, show the 🌙 icon (clicking takes you to dark)
      btn.textContent  = currentTheme === DARK_THEME ? ICON_WARM : ICON_DARK;
      btn.setAttribute('aria-label',
        currentTheme === DARK_THEME ? 'Switch to warm theme' : 'Switch to dark theme'
      );
      btn.setAttribute('title',
        currentTheme === DARK_THEME ? 'Switch to warm theme' : 'Switch to dark theme'
      );
    });
  }

  /**
   * Persist the current theme preference and optionally sync with the server.
   * @param {'dark'|'warm'} theme
   * @param {HTMLElement} btn  — the button that was clicked (to read data-attributes)
   */
  function saveTheme(theme, btn) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) { /* storage may be blocked */ }

    // Server sync — only when the user is authenticated
    if (btn && btn.dataset.authenticated === 'true') {
      const csrfToken = getCookie('csrftoken');
      if (!csrfToken) return;

      fetch('/users/set-theme/', {
        method:  'POST',
        headers: {
          'Content-Type':     'application/json',
          'X-CSRFToken':      csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
        body: JSON.stringify({ theme: theme }),
      }).catch(function (err) {
        // Non-critical — silently ignore network errors
        console.debug('[NextReel] theme sync failed:', err);
      });
    }
  }

  /**
   * Read the stored theme from localStorage (or fall back to dark).
   * @returns {'dark'|'warm'}
   */
  function loadStoredTheme() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === WARM_THEME) return WARM_THEME;
    } catch (_) { /* ignore */ }
    return DARK_THEME;
  }

  /**
   * Wire up click handlers on all theme-toggle buttons.
   */
  function initThemeToggle() {
    // Apply saved preference immediately (before DOM is fully painted)
    const current = loadStoredTheme();
    applyTheme(current);

    // Attach listeners (document-level delegation handles dynamically added buttons)
    document.addEventListener('click', function (e) {
      const btn = e.target.closest('.theme-toggle, #theme-toggle');
      if (!btn) return;

      // Determine the current theme from the DOM
      const isDark   = document.documentElement.dataset.theme !== WARM_THEME;
      const nextTheme = isDark ? WARM_THEME : DARK_THEME;

      applyTheme(nextTheme);
      saveTheme(nextTheme, btn);

      // Brief scale animation for tactile feedback
      btn.style.transform = 'rotate(180deg) scale(0.9)';
      setTimeout(function () {
        btn.style.transform = '';
      }, 300);
    });
  }


  /* ============================================================
     NAVBAR SCROLL EFFECT
     ============================================================ */

  function initNavScroll() {
    const nav = document.querySelector('.nav');
    if (!nav) return;

    function onScroll() {
      if (window.scrollY > 20) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    }

    // Use passive listener for performance
    window.addEventListener('scroll', onScroll, { passive: true });

    // Run immediately in case the page loads mid-scroll
    onScroll();
  }


  /* ============================================================
     MOBILE MENU TOGGLE
     ============================================================ */

  function initMobileMenu() {
    // Support both the CSS-only hamburger label and an explicit JS toggle
    const hamburgerLabel = document.querySelector('.nav__hamburger-label');
    const navLinks       = document.querySelector('.nav__links');

    if (!hamburgerLabel || !navLinks) return;

    hamburgerLabel.addEventListener('click', function () {
      const isOpen = navLinks.classList.toggle('nav__links--open');
      hamburgerLabel.setAttribute('aria-expanded', isOpen.toString());

      // Animate the three hamburger lines into an X
      const spans = hamburgerLabel.querySelectorAll('span');
      if (isOpen && spans.length >= 3) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity   = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
      } else if (spans.length >= 3) {
        spans[0].style.transform = '';
        spans[1].style.opacity   = '';
        spans[2].style.transform = '';
      }
    });

    // Close menu when a nav link is clicked
    navLinks.addEventListener('click', function (e) {
      if (e.target.closest('.nav__link')) {
        navLinks.classList.remove('nav__links--open');
        hamburgerLabel.setAttribute('aria-expanded', 'false');
        const spans = hamburgerLabel.querySelectorAll('span');
        spans.forEach(function (s) {
          s.style.transform = '';
          s.style.opacity   = '';
        });
      }
    });

    // Close menu when clicking outside
    document.addEventListener('click', function (e) {
      if (
        navLinks.classList.contains('nav__links--open') &&
        !navLinks.contains(e.target) &&
        !hamburgerLabel.contains(e.target)
      ) {
        navLinks.classList.remove('nav__links--open');
        hamburgerLabel.setAttribute('aria-expanded', 'false');
        const spans = hamburgerLabel.querySelectorAll('span');
        spans.forEach(function (s) {
          s.style.transform = '';
          s.style.opacity   = '';
        });
      }
    });
  }


  /* ============================================================
     TOAST AUTO-DISMISS
     ============================================================ */

  /**
   * Schedule auto-removal of a toast element.
   * @param {HTMLElement} toast
   * @param {number} [delay=4000] ms before removal starts
   */
  function scheduleToastDismiss(toast, delay) {
    delay = delay !== undefined ? delay : 4000;

    setTimeout(function () {
      toast.style.animation = 'toastOut 0.35s ease forwards';
      setTimeout(function () {
        toast.remove();
      }, 350);
    }, delay);
  }

  /**
   * Dismiss a toast when its close button is clicked.
   */
  function initToastCloseButtons() {
    document.addEventListener('click', function (e) {
      const closeBtn = e.target.closest('.toast__close');
      if (!closeBtn) return;
      const toast = closeBtn.closest('.toast');
      if (!toast) return;
      toast.style.animation = 'toastOut 0.35s ease forwards';
      setTimeout(function () { toast.remove(); }, 350);
    });
  }

  /**
   * Set up auto-dismiss for all toasts currently in the DOM,
   * and observe for new ones added dynamically.
   */
  function initToasts() {
    initToastCloseButtons();

    // Handle toasts already in the DOM
    document.querySelectorAll('.toast').forEach(function (toast) {
      scheduleToastDismiss(toast, 4000);
    });

    // Handle toasts added after page load (e.g., AJAX feedback)
    const messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) return;

    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1 && node.classList.contains('toast')) {
            scheduleToastDismiss(node, 4000);
          }
        });
      });
    });

    observer.observe(messagesContainer, { childList: true });
  }


  /* ============================================================
     STAR RATING INTERACTIVE HINTS
     ============================================================ */

  /**
   * Add accessible keyboard support and ARIA labels to star rating inputs.
   */
  function initStarRatings() {
    document.querySelectorAll('.star-rating--input').forEach(function (widget) {
      const labels = widget.querySelectorAll('label');
      labels.forEach(function (label, index) {
        // The row is reversed (flex-direction: row-reverse) so index 0 = 5 stars
        const stars = labels.length - index;
        label.setAttribute('title', stars + ' star' + (stars !== 1 ? 's' : ''));
        label.setAttribute('aria-label', stars + ' star' + (stars !== 1 ? 's' : ''));
      });
    });
  }


  /* ============================================================
     SMOOTH ACTIVE NAV LINK
     ============================================================ */

  /**
   * Mark the current nav link as active based on the URL path.
   */
  function highlightActiveNavLink() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav__link').forEach(function (link) {
      const href = link.getAttribute('href');
      if (!href) return;
      // Exact match or sub-path (but don't mark '/' active for everything)
      const isActive = href === path || (href !== '/' && path.startsWith(href));
      link.classList.toggle('nav__link--active', isActive);
    });
  }


  /* ============================================================
     LAZY IMAGE FALLBACK
     ============================================================ */

  /**
   * Swap broken poster images to the default SVG placeholder.
   */
  function initImageFallbacks() {
    const DEFAULT_POSTER = '/static/images/default_poster.svg';
    const DEFAULT_AVATAR = '/static/images/default_avatar.svg';

    document.addEventListener('error', function (e) {
      const img = e.target;
      if (img.tagName !== 'IMG') return;

      if (img.classList.contains('movie-card__poster') || img.closest('.movie-card__poster')) {
        if (img.src !== DEFAULT_POSTER) img.src = DEFAULT_POSTER;
      } else if (img.classList.contains('review-card__avatar') || img.closest('.review-card__avatar') ||
                 img.classList.contains('profile-avatar')       || img.closest('.profile-avatar') ||
                 img.classList.contains('nav__avatar')          || img.closest('.nav__avatar')) {
        if (img.src !== DEFAULT_AVATAR) img.src = DEFAULT_AVATAR;
      }
    }, true /* capture phase to catch all image errors */);
  }


  /* ============================================================
     SCROLL-TO-TOP BUTTON
     ============================================================ */

  function initScrollToTop() {
    // Inject a scroll-to-top button if one doesn't already exist
    if (document.querySelector('.scroll-top')) return;

    const btn = document.createElement('button');
    btn.className    = 'scroll-top';
    btn.innerHTML    = '↑';
    btn.setAttribute('aria-label', 'Scroll to top');
    btn.setAttribute('title',      'Scroll to top');

    Object.assign(btn.style, {
      position:     'fixed',
      bottom:       '2rem',
      right:        '1.5rem',
      width:        '44px',
      height:       '44px',
      borderRadius: '50%',
      border:       '1px solid var(--border)',
      background:   'var(--surface)',
      color:        'var(--text-muted)',
      fontSize:     '1.1rem',
      cursor:       'pointer',
      display:      'none',
      alignItems:   'center',
      justifyContent: 'center',
      zIndex:       '500',
      boxShadow:    '0 4px 16px var(--shadow)',
      transition:   'opacity 0.2s, transform 0.2s',
      backdropFilter: 'blur(8px)',
    });

    document.body.appendChild(btn);

    window.addEventListener('scroll', function () {
      if (window.scrollY > 400) {
        btn.style.display = 'flex';
        btn.style.opacity = '1';
      } else {
        btn.style.opacity = '0';
        setTimeout(function () {
          if (btn.style.opacity === '0') btn.style.display = 'none';
        }, 200);
      }
    }, { passive: true });

    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    btn.addEventListener('mouseenter', function () {
      btn.style.borderColor = 'var(--accent)';
      btn.style.color       = 'var(--accent)';
      btn.style.transform   = 'translateY(-3px)';
    });

    btn.addEventListener('mouseleave', function () {
      btn.style.borderColor = 'var(--border)';
      btn.style.color       = 'var(--text-muted)';
      btn.style.transform   = '';
    });
  }


  /* ============================================================
     INTERSECTION OBSERVER — animate cards into view
     ============================================================ */

  function initScrollAnimations() {
    if (!window.IntersectionObserver) return;

    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = 'running';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    // Pause animations until elements are visible
    document.querySelectorAll('.animate-fade-up, .stagger-children > *').forEach(function (el) {
      el.style.animationPlayState = 'paused';
      observer.observe(el);
    });
  }


  /* ============================================================
     PUBLIC API
     ============================================================ */

  /**
   * Programmatically show a toast notification.
   * @param {string} message  - The message text.
   * @param {'success'|'error'|'info'|'warning'} [type='info']
   * @param {number} [duration=4000]  - ms before auto-dismiss.
   */
  window.NextReelToast = function (message, type, duration) {
    type     = type     || 'info';
    duration = duration !== undefined ? duration : 4000;

    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };

    let container = document.querySelector('.messages');
    if (!container) {
      container = document.createElement('div');
      container.className = 'messages';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.innerHTML =
      '<span class="toast__icon">' + (icons[type] || icons.info) + '</span>' +
      '<span class="toast__text">' + message + '</span>' +
      '<button class="toast__close" aria-label="Dismiss">&times;</button>';

    container.appendChild(toast);
    scheduleToastDismiss(toast, duration);
  };


  /* ============================================================
     INIT — run when DOM is ready
     ============================================================ */

  function init() {
    initThemeToggle();
    initNavScroll();
    initMobileMenu();
    initToasts();
    initStarRatings();
    highlightActiveNavLink();
    initImageFallbacks();
    initScrollToTop();
    initScrollAnimations();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM already ready (script loaded with defer/async or at bottom of body)
    init();
  }

}());
