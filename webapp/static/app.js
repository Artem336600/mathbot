/**
 * MathTrainer Admin SPA Logic (Vanilla JS)
 */

const tg = window.Telegram.WebApp;

// ==== State & API ====
const state = {
    initData: tg.initData || '', // Fallback for local testing can be mocked
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
        // fetch handles multipart/form-data boundary automatically when body is FormData
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

        const icon = type === 'success' ? 'fa-check-circle text-success' :
            type === 'error' ? 'fa-circle-xmark text-danger' :
                type === 'warning' ? 'fa-triangle-exclamation text-warning' :
                    'fa-info-circle text-primary';

        el.innerHTML = `<i class="fa-solid ${icon}"></i><span>${msg}</span>`;
        container.appendChild(el);

        setTimeout(() => {
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 300);
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
        // Trigger reflow & show
        void backdrop.offsetWidth;
        backdrop.classList.add("show");
    },

    closeModal: () => {
        const backdrop = document.getElementById("modal-backdrop");
        if (backdrop) {
            backdrop.classList.remove("show");
            setTimeout(() => {
                if (!backdrop.classList.contains("show")) backdrop.remove();
            }, 200);
        }
    }
};

// ==== App Core (Router & Init) ====
const app = {
    init: () => {
        // Expand WebApp by default
        tg.expand();
        // Set Header Color
        tg.setHeaderColor("secondary_bg_color");

        // Setup user info
        document.getElementById("admin-name").innerText = state.user.first_name || "Admin";

        // Setup Router
        window.addEventListener('hashchange', app.onHashChange);

        // Setup UI bindings
        document.getElementById("btn-close").addEventListener("click", () => tg.close());

        const sbToggle = document.getElementById("sidebar-toggle");
        const sidebar = document.querySelector(".sidebar");
        sbToggle.addEventListener("click", () => sidebar.classList.toggle("open"));

        // Allow clicking outside sidebar to close on mobile
        document.querySelector(".views").addEventListener("click", () => {
            if (window.innerWidth <= 768) sidebar.classList.remove("open");
        });

        // Add theme toggle logic
        document.getElementById("theme-toggle").addEventListener("click", () => {
            const body = document.body;
            if (body.classList.contains("theme-dark")) {
                body.classList.replace("theme-dark", "theme-light");
            } else {
                body.classList.replace("theme-light", "theme-dark");
            }
        });

        // Hide loader, show app
        document.getElementById("app-loader").style.display = "none";
        document.getElementById("app-layout").style.display = "flex";

        // Initial route trigger
        if (!window.location.hash) {
            window.location.hash = "#dashboard";
        } else {
            app.onHashChange();
        }
    },

    onHashChange: () => {
        let hash = window.location.hash.replace('#', '');
        if (!hash) hash = 'dashboard';

        app.switchView(hash);
    },

    switchView: (viewName) => {
        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        // Deactivate all links
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

        // Try finding view
        const targetView = document.getElementById(`view-${viewName}`);
        const targetLink = document.querySelector(`.nav-link[data-target="${viewName}"]`);

        if (targetView) {
            targetView.classList.add('active');
            if (targetLink) targetLink.classList.add('active');
            document.getElementById('page-title').innerText = targetLink ? targetLink.innerText : viewName;

            // Load module logic dynamically if specified
            app.loadModule(viewName);
        } else {
            app.showError("404 Не найдено", "Страница не существует.");
        }

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            document.querySelector('.sidebar').classList.remove('open');
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
            // More to come...
        }
    }
};

window.modules = {}; // Namespace for page modules

// Boot
// Give it a tiny delay to ensure TG WebApp object is fully hydrated
setTimeout(() => app.init(), 100);
