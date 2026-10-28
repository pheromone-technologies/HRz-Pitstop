/* =============================================
   HRz PITSTOP – Auth Module
   Demo Google Login + Login Popup Gate
   + Admin PIN gate (see Admin PIN section below)

   HONEST SECURITY NOTE — READ BEFORE RELYING ON THIS:
   This is a static site with no backend, so the admin PIN gate in
   this file is a DETERRENT, not real security. The PIN is stored
   only as a SHA-256 hash in this browser's localStorage, and the
   "unlocked" flag lives in sessionStorage. Anyone with access to
   this browser (DevTools -> Application -> Local Storage) can read
   or delete those keys and bypass the gate entirely. Never treat
   this as protection for sensitive data, and never hardcode a
   default PIN or password anywhere in this file.
   ============================================= */

window.HRz = window.HRz || {};

const AUTH_KEY = "hrz_auth_user_v1";
// Admin PIN: only a hash is stored, never the PIN itself, and never
// a default value. First admin visit (no hash stored) sets the PIN;
// later visits must match it. See Admin PIN section below.
const ADMIN_PIN_HASH_KEY = "hrz_admin_pin_hash_v1";
const ADMIN_UNLOCK_KEY = "hrz_admin_unlocked_v1";

const DEMO_GOOGLE_ACCOUNTS = [
  { id: "g_001", name: "Rahul Sharma", email: "rahul.sharma@gmail.com", avatar: "RS" },
  { id: "g_002", name: "Priya Mehra",  email: "priya.mehra@gmail.com",  avatar: "PM" },
  { id: "g_003", name: "Arun Verma",   email: "arun.verma@gmail.com",   avatar: "AV" },
];

class AuthService {

  static getUser() {
    try {
      const raw = sessionStorage.getItem(AUTH_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  static setUser(user) {
    try { sessionStorage.setItem(AUTH_KEY, JSON.stringify(user)); } catch {}
  }

  static isLoggedIn() { return !!this.getUser(); }

  static logout() {
    sessionStorage.removeItem(AUTH_KEY);
    sessionStorage.removeItem(ADMIN_UNLOCK_KEY);
    this._refreshHeaderAvatar();
    window.HRz.Utils.showToast("Signed out successfully", "info");
  }

  /* ------ Admin PIN gate (client-side deterrent only — see header) ------
     Used ONLY by js/admin.js. The customer login popup and "Continue
     as Guest" flow below are untouched: guest sign-in deliberately
     does NOT satisfy the admin gate (isLoggedIn() stays false for
     guests), so a guest can never open #admin through this path. */
  static hasAdminPin() {
    try { return !!localStorage.getItem(ADMIN_PIN_HASH_KEY); } catch { return false; }
  }

  static isAdminUnlocked() {
    try { return sessionStorage.getItem(ADMIN_UNLOCK_KEY) === "1"; } catch { return false; }
  }

  static lockAdmin() {
    try { sessionStorage.removeItem(ADMIN_UNLOCK_KEY); } catch {}
  }

  static _hashPin(pin) {
    // SHA-256 when available (secure contexts). Fallback is a plain
    // non-cryptographic hash used only as obfuscation — it does not
    // make the gate secure; see the header note.
    const subtle = (window.crypto && window.crypto.subtle)
      || (typeof crypto !== "undefined" && crypto.subtle);
    if (subtle && subtle.digest) {
      const data = new TextEncoder().encode("hrz-admin-pin:" + pin);
      return subtle.digest("SHA-256", data).then(buf =>
        Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("")
      );
    }
    let h = 2166136261;
    const s = "hrz-admin-pin:" + pin;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return Promise.resolve("weak-" + (h >>> 0).toString(16));
  }

  static _isValidPinFormat(pin) { return /^\d{4,8}$/.test(pin || ""); }

  // Sets the PIN on first admin visit. Returns { ok, error }.
  static setAdminPin(pin, confirmPin) {
    if (!this._isValidPinFormat(pin)) {
      return Promise.resolve({ ok: false, error: "PIN must be 4–8 digits." });
    }
    if (pin !== confirmPin) {
      return Promise.resolve({ ok: false, error: "PINs do not match." });
    }
    if (this.hasAdminPin()) {
      return Promise.resolve({ ok: false, error: "An admin PIN is already set. Enter it instead." });
    }
    return this._hashPin(pin).then(hash => {
      try {
        localStorage.setItem(ADMIN_PIN_HASH_KEY, hash);
        sessionStorage.setItem(ADMIN_UNLOCK_KEY, "1");
      } catch { return { ok: false, error: "Could not save the PIN in this browser." }; }
      return { ok: true };
    });
  }

  // Verifies a PIN on later visits. Returns a Promise<boolean>.
  // A wrong PIN never unlocks and never renders any admin UI.
  static verifyAdminPin(pin) {
    if (!this._isValidPinFormat(pin)) return Promise.resolve(false);
    let stored = null;
    try { stored = localStorage.getItem(ADMIN_PIN_HASH_KEY); } catch {}
    if (!stored) return Promise.resolve(false);
    return this._hashPin(pin).then(hash => {
      if (hash === stored) {
        try { sessionStorage.setItem(ADMIN_UNLOCK_KEY, "1"); } catch {}
        return true;
      }
      return false;
    });
  }

  /* ------ Login Popup ------ */
  static showLoginPopup(onSuccess, onCancel) {
    const existing = document.getElementById("hrzLoginPopup");
    if (existing) existing.remove();

    const popup = document.createElement("div");
    popup.id = "hrzLoginPopup";
    popup.innerHTML = `
      <div class="login-popup-backdrop" id="loginPopupBackdrop"></div>
      <div class="login-popup-card" role="dialog" aria-modal="true">
        <button class="login-popup-close" id="loginPopupClose" aria-label="Close">&#x2715;</button>

        <div class="login-popup-logo">
          <img src="images/HRZ_BIKE_LOGO_page-0001-removebg-preview (3)_20250705_182254_0000.webp" alt="HRz Logo" style="height: 38px; width: auto; object-fit: contain;" />
          <span>HRz Pitstop</span>
        </div>

        <h2 class="login-popup-title">Sign in to proceed</h2>
        <p class="login-popup-sub">Access your cart, wishlist &amp; verified bike fitments.</p>

        <button class="login-google-btn" id="loginGoogleBtn">
          <svg width="20" height="20" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          </svg>
          Continue with Google
        </button>

        <button class="login-guest-btn" id="loginGuestBtn">
          Continue as Guest
        </button>

        <p class="login-popup-legal">By continuing you agree to our <a href="#help">Terms</a> &amp; <a href="#help">Privacy Policy</a>.</p>
      </div>
    `;
    document.body.appendChild(popup);

    requestAnimationFrame(() => popup.classList.add("active"));

    const close = (wasSuccess = false) => {
      popup.classList.remove("active");
      setTimeout(() => popup.remove(), 320);
      if (wasSuccess) {
        if (typeof onSuccess === "function") onSuccess();
      } else {
        if (typeof onCancel === "function") onCancel();
      }
    };

    popup.querySelector("#loginPopupClose").onclick = () => close(false);
    popup.querySelector("#loginPopupBackdrop").onclick = () => close(false);
    popup.querySelector("#loginGuestBtn").onclick = () => close(true);

    popup.querySelector("#loginGoogleBtn").onclick = () => {
      this._login(DEMO_GOOGLE_ACCOUNTS[0], popup, onSuccess);
    };

    const onKey = (e) => {
      if (e.key === "Escape") { close(false); document.removeEventListener("keydown", onKey); }
    };
    document.addEventListener("keydown", onKey);
  }

  static _login(account, popup, onSuccess) {
    popup.classList.remove("active");
    setTimeout(() => popup.remove(), 320);
    this.setUser(account);
    this._refreshHeaderAvatar();
    window.HRz.Utils.showToast("Welcome, " + account.name + "!", "success");
    if (typeof onSuccess === "function") onSuccess(account);
  }

  /* ------ Header Avatar ------ */
  static _refreshHeaderAvatar() {
    const user = this.getUser();
    let btn = document.getElementById("hrzHeaderAvatar");

    if (user) {
      if (!btn) {
        btn = document.createElement("button");
        btn.id = "hrzHeaderAvatar";
        btn.className = "hrz-user-avatar-btn";
        btn.onclick = () => this._showUserMenu();
        const navActions = document.querySelector(".nav-actions");
        if (navActions) navActions.prepend(btn);
      }
      btn.textContent = user.avatar;
      btn.title = user.name;
    } else {
      if (btn) btn.remove();
    }
  }

  static _showUserMenu() {
    const user = this.getUser();
    if (!user) return;

    const existing = document.getElementById("hrzUserMenu");
    if (existing) { existing.remove(); return; }

    const menu = document.createElement("div");
    menu.id = "hrzUserMenu";
    menu.className = "hrz-user-menu";
    menu.innerHTML = `
      <div class="user-menu-header">
        <span class="user-menu-avatar">${user.avatar}</span>
        <div>
          <strong>${user.name}</strong>
          <small>${user.email}</small>
        </div>
      </div>
      <hr class="user-menu-divider"/>
      <a href="#tracking" class="user-menu-item">My Orders</a>
      <a href="#wishlist" class="user-menu-item">Wishlist</a>
      <a href="#garage" class="user-menu-item">My Garage</a>
      <hr class="user-menu-divider"/>
      <button class="user-menu-item user-menu-signout" id="umSignout">Sign Out</button>
    `;
    document.body.appendChild(menu);

    menu.querySelector("#umSignout").onclick = () => { menu.remove(); this.logout(); };
    menu.querySelectorAll("a.user-menu-item").forEach(a => a.addEventListener("click", () => menu.remove()));

    const outside = (e) => {
      if (!menu.contains(e.target) && e.target.id !== "hrzHeaderAvatar") {
        menu.remove();
        document.removeEventListener("click", outside);
      }
    };
    setTimeout(() => document.addEventListener("click", outside), 50);
  }

  static init() { this._refreshHeaderAvatar(); }
}

window.HRz.Auth = AuthService;

