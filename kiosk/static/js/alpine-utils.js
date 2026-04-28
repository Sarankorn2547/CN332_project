/**
 * Shared Alpine.js utilities for Food Locker Kiosk
 * Loads BEFORE Alpine.js so it can register handlers on 'alpine:init' event
 */
document.addEventListener('alpine:init', () => {

  // ============================================================
  // STORE: toast — global notification popup
  // ============================================================
  Alpine.store('toast', {
    message: '',
    type: 'info',
    visible: false,
    _timeout: null,

    show(message, type = 'info', duration = 3000) {
      this.message = message;
      this.type = type;
      this.visible = true;
      if (this._timeout) clearTimeout(this._timeout);
      this._timeout = setTimeout(() => { this.visible = false; }, duration);
    },

    success(msg) { this.show(msg, 'success', 3000); },
    error(msg)   { this.show(msg, 'error', 5000); },
    warning(msg) { this.show(msg, 'warning', 4000); },
    info(msg)    { this.show(msg, 'info', 3000); },
  });

  // ============================================================
  // STORE: loading — global loading overlay
  // ============================================================
  Alpine.store('loading', {
    active: false,
    _count: 0,

    start() { this._count++; this.active = true; },
    stop()  {
      this._count = Math.max(0, this._count - 1);
      if (this._count === 0) this.active = false;
    },
    reset() { this._count = 0; this.active = false; },
  });

  // ============================================================
  // MAGIC: $csrf — get CSRF token from meta tag or cookie
  // ============================================================
  Alpine.magic('csrf', () => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  });

  // ============================================================
  // MAGIC: $api — fetch wrapper with auth + CSRF + loading state
  // ============================================================
  Alpine.magic('api', () => ({
    async request(method, url, data = null) {
      const csrfMeta = document.querySelector('meta[name="csrf-token"]');
      const csrfToken = csrfMeta ? csrfMeta.content :
        (document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '');

      const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest',
      };
      const token = sessionStorage.getItem('jwt');
      if (token) headers['Authorization'] = `Bearer ${token}`;

      Alpine.store('loading').start();
      try {
        const res = await fetch(url, {
          method,
          headers,
          body: data ? JSON.stringify(data) : null,
          credentials: 'same-origin',
        });

        // Token expired → kick to login
        if (res.status === 401) {
          sessionStorage.removeItem('jwt');
          Alpine.store('toast').error('เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่');
          setTimeout(() => { window.location.href = '/login/'; }, 1500);
          return null;
        }

        const payload = await res.json().catch(() => ({}));
        if (!res.ok) {
          const err = new Error(payload.detail || payload.message || `HTTP ${res.status}`);
          err.status = res.status;
          err.payload = payload;
          throw err;
        }
        return payload;
      } finally {
        Alpine.store('loading').stop();
      }
    },
    get(url)         { return this.request('GET', url); },
    post(url, data)  { return this.request('POST', url, data); },
    patch(url, data) { return this.request('PATCH', url, data); },
    delete(url)      { return this.request('DELETE', url); },
  }));

  // ============================================================
  // MAGIC: $formatThaiDate — format ISO date string for Thai users
  // ============================================================
  Alpine.magic('formatThaiDate', () => (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleString('th-TH', {
        year: 'numeric', month: 'long', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch { return isoString; }
  });

  // ============================================================
  // MAGIC: $debounce — prevent rapid-fire button clicks
  // ============================================================
  Alpine.magic('debounce', () => (fn, wait = 300) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), wait);
    };
  });
});