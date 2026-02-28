/**
 * MathTrainer Admin SPA Logic (Vanilla JS)
 */

const tg = window.Telegram.WebApp;

// ==== State & API ====
const state = {
    initData: tg.initData || '',
    user: tg.initDataUnsafe?.user || { first_name: "Local Admin", id: 0 },
    currentView: 'dashboard'
};

const API = {
    _fetch: async (path, options = {}) => {
        const url = `/api${path}`;
        const headers = {
            'X-Init-Data': state.initData,
            ...options.headers
        };

        try {
            const res = await fetch(url, { ...options, headers });

            if (res.status === 401 || res.status === 403) {
                app.showError("Доступ запрещен", "Вы не являетесь администратором или ваша сессия истекла.");
                throw new Error("Unauthorized");
            }

            const data = await res.json().catch(() => null);
            if (!res.ok) {
                const msg = data?.detail || `HTTP Error ${res.status}`;
                ui.toast(msg, "error");
                throw new Error(msg);
            }
            return data;
        } catch (e) {
            console.error(`API Error (${path}):`, e);
            throw e;
        }
    },

    get: (path) => API._fetch(path, { method: 'GET' }),
    post: (path, body) => API._fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    patch: (path, body) => API._fetch(path, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    }),
    delete: (path) => API._fetch(path, { method: 'DELETE' }),
    upload: (path, formData) => {
        return API._fetch(path, {
            method: 'POST',
            body: formData
        });
    }
};

// ==== UI Utils ====
const ui = {
    toast: (msg, type = "info") => {
        const container = document.getElementById("toast-container");
        const el = document.createElement("div");
        el.className = `toast ${type}`;

        const iconName = type === 'success' ? 'check-circle' :
            type === 'error' ? 'x-circle' :
                type === 'warning' ? 'alert-triangle' :
                    'info';

        const iconSvg = window.icon(iconName, 20);

        el.innerHTML = `${iconSvg}<span>${msg}</span>`;
        container.appendChild(el);

        setTimeout(() => {
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 400);
        }, 3000);
    },

    modal: (htmlContent) => {
        let backdrop = document.getElementById("modal-backdrop");
        if (!backdrop) {
            backdrop = document.createElement("div");
            backdrop.id = "modal-backdrop";
            backdrop.className = "modal-backdrop";
            backdrop.innerHTML = `<div class="modal-dialog" id="modal-content"></div>`;
            document.body.appendChild(backdrop);

            // Close on click outside
            backdrop.addEventListener("click", (e) => {
                if (e.target === backdrop) ui.closeModal();
            });
        }

        document.getElementById("modal-content").innerHTML = htmlContent;
        void backdrop.offsetWidth; // Trigger reflow
        backdrop.classList.add("show");
        ui.injectIcons(backdrop);
    },

    closeModal: () => {
        const backdrop = document.getElementById("modal-backdrop");
        if (backdrop) {
            backdrop.classList.remove("show");
            setTimeout(() => {
                if (!backdrop.classList.contains("show")) backdrop.remove();
            }, 300);
        }
    },

    /**
     * Replaces <span class="icon-slot" data-icon="name"> with real SVG icon
     */
    injectIcons: (root = document) => {
        const slots = root.querySelectorAll('.icon-slot');
        slots.forEach(slot => {
            const name = slot.getAttribute('data-icon');
            const size = slot.getAttribute('data-size') || 18;
            if (name && window.icon) {
                const svg = window.icon(name, parseInt(size));
                if (svg) {
                    slot.innerHTML = svg;
                    slot.classList.remove('icon-slot');
                    // carry over classes
                    const cls = slot.getAttribute('class');
                    if (cls) slot.firstChild.setAttribute('class', cls);
                    slot.replaceWith(slot.firstChild);
                }
            }
        });
    }
};

// ==== App Core (Router & Init) ====
const app = {
    init: () => {
        tg.expand();
        // Force secondary background color header for a seamless look
        try { tg.setHeaderColor("#13131a"); } catch (e) { }
        try { tg.setBackgroundColor("#0d0d12"); } catch (e) { }

        // Set User Name
        document.getElementById("admin-name").innerText = state.user.first_name || "Admin";

        // Inject App Loader SVG
        const loaderContainer = document.getElementById("app-loader");
        if (loaderContainer && window.svgAnim) {
            loaderContainer.insertAdjacentHTML('afterbegin', window.svgAnim.loader(64));
        }

        // Inject SVG Logo
        const appLogo = document.getElementById("app-logo");
        if (appLogo && window.svgAnim) {
            appLogo.innerHTML = window.svgAnim.logo(28);
        }

        // Set User initial on Avatar
        const avatarSvg = document.getElementById("avatar-svg");
        if (avatarSvg) {
            avatarSvg.innerHTML = window.icon('user-tie', 20);
        }

        // Inject All Initial Icons
        ui.injectIcons();

        // Setup Router
        window.addEventListener('hashchange', app.onHashChange);

        // Setup UI bindings
        const sbToggle = document.getElementById("sidebar-toggle");
        const sidebar = document.querySelector(".sidebar");
        const overlay = document.getElementById("sidebar-overlay");

        sbToggle.addEventListener("click", () => {
            sidebar.classList.toggle("open");
            overlay.classList.toggle("show");
        });

        // Click outside sidebar on mobile
        overlay.addEventListener("click", () => {
            sidebar.classList.remove("open");
            overlay.classList.remove("show");
        });

        // Hide loader, show app
        setTimeout(() => {
            document.getElementById("app-loader").style.display = "none";
            document.getElementById("app-layout").style.display = "flex";

            // Initial route trigger
            if (!window.location.hash || window.location.hash.startsWith('#tgWebApp')) {
                window.location.hash = "#dashboard";
            } else {
                app.onHashChange();
            }
        }, 800);
    },

    onHashChange: () => {
        let hash = window.location.hash.replace('#', '');

        if (!hash || hash.startsWith('tgWebApp')) {
            window.location.hash = '#dashboard';
            return;
        }

        app.switchView(hash);
    },

    switchView: (viewName) => {
        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        // Deactivate all links
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

        const targetView = document.getElementById(`view-${viewName}`);
        const targetLink = document.querySelector(`.nav-link[data-target="${viewName}"]`);

        if (targetView) {
            targetView.classList.add('active');
            if (targetLink) targetLink.classList.add('active');
            document.getElementById('page-title').innerText = targetLink ? targetLink.innerText : viewName;

            // Load module logic dynamically
            app.loadModule(viewName);
        } else {
            app.showError("404 Не найдено", "Страница не существует.");
        }

        // Close sidebar on mobile if open
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.getElementById("sidebar-overlay");
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        }
    },

    showError: (title, message) => {
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        const errView = document.getElementById('view-error');
        errView.classList.add('active');
        document.getElementById('error-title').innerText = title;
        document.getElementById('error-message').innerText = message;
    },

    loadModule: (name) => {
        switch (name) {
            case 'dashboard':
                if (window.modules?.dashboard) window.modules.dashboard.load();
                break;
            case 'topics':
                if (window.modules?.topics) window.modules.topics.load();
                break;
            case 'questions':
                if (window.modules?.questions) window.modules.questions.load();
                break;
            case 'users':
                if (window.modules?.users) window.modules.users.load();
                break;
            case 'broadcast':
                if (window.modules?.broadcast) window.modules.broadcast.load();
                break;
        }
    }
};

window.modules = {};

// Boot
// Let DOM and TG WebApp initialize properly
setTimeout(() => app.init(), 100);
