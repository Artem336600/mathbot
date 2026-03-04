/**
 * Broadcast Module
 */

window.modules = window.modules || {};

window.modules.broadcast = {
    pollInterval: null,

    load: async function () {
        const view = document.getElementById('view-broadcast');

        view.innerHTML = `
            <div class="header-actions mb-4">
                <h2 style="font-size:18px;">Массовая рассылка</h2>
                <p class="text-muted" style="margin-top:4px;">Отправка сообщений всем пользователям бота</p>
            </div>
            
            <div style="display:grid; grid-template-columns:1fr; gap:24px;">
                <!-- Form Area -->
                <div class="stat-card" style="align-items:flex-start; display:block;">
                    <form onsubmit="event.preventDefault(); modules.broadcast.confirmSend()">
                        <div class="form-group mb-4">
                            <label>Текст сообщения (поддерживается HTML)</label>
                            <textarea id="broadcast-text" class="form-control" rows="8" required placeholder="<b>Внимание!</b> Новая тема доступна для изучения..."></textarea>
                            <small class="text-muted mt-2" style="display:block;">
                                Разрешенные теги: &lt;b&gt;, &lt;i&gt;, &lt;u&gt;, &lt;s&gt;, &lt;a href="..."&gt;, &lt;code&gt;, &lt;pre&gt;
                            </small>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                            <button type="button" class="btn btn-secondary" onclick="modules.broadcast.preview()">
                                <span class="icon-slot" data-icon="search"></span> Предпросмотр
                            </button>
                            <button type="submit" class="btn btn-primary" id="btn-broadcast-send">
                                <span class="icon-slot" data-icon="broadcast"></span> Запустить рассылку
                            </button>
                        </div>
                    </form>
                </div>
                
                <div id="broadcast-preview-container" style="display:none; margin-top:-8px;">
                    <h4 class="mb-2" style="font-size:14px; color:var(--c-text-muted);">Предпросмотр:</h4>
                    <div id="broadcast-preview-content" style="background:#fff; color:#000; padding:16px 20px; border-radius:var(--radius-md); max-width:400px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; box-shadow:var(--shadow-card);">
                    </div>
                </div>

                <!-- Status Area -->
                <div class="stat-card" id="broadcast-status-card" style="display:none; flex-direction:column; align-items:flex-start; margin-top:8px;">
                    <h3 style="margin-bottom:20px; font-size:15px;">Статус рассылки</h3>
                    
                    <div style="width:100%; margin-bottom:24px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                            <span id="broadcast-state" class="badge">Неизвестно</span>
                            <span id="broadcast-progress-text" class="text-muted" style="font-family:'Space Grotesk',sans-serif;">0 / 0</span>
                        </div>
                        <div style="width:100%; height:12px; background:rgba(255,255,255,0.05); border-radius:6px; overflow:hidden; border:1px solid var(--c-border-subtle);">
                            <div id="broadcast-progress-bar" style="height:100%; width:0%; background:var(--c-accent-gradient); box-shadow:var(--glow-accent); transition:width 0.5s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                        </div>
                    </div>
                    
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; width:100%;">
                        <div style="background:var(--c-bg); padding:16px; border-radius:var(--radius-sm); border:1px solid rgba(16,185,129,0.2); position:relative; overflow:hidden;">
                            <div style="position:absolute; left:0; top:0; bottom:0; width:3px; background:var(--c-success);"></div>
                            <div class="text-muted" style="font-size:12px; margin-bottom:4px;">Доставлено</div>
                            <div id="broadcast-sent" style="font-size:24px; font-weight:700; font-family:'Space Grotesk',sans-serif;">0</div>
                        </div>
                        <div style="background:var(--c-bg); padding:16px; border-radius:var(--radius-sm); border:1px solid rgba(244,63,94,0.2); position:relative; overflow:hidden;">
                            <div style="position:absolute; left:0; top:0; bottom:0; width:3px; background:var(--c-danger);"></div>
                            <div class="text-muted" style="font-size:12px; margin-bottom:4px;">Ошибки (Отписки)</div>
                            <div id="broadcast-failed" style="font-size:24px; font-weight:700; font-family:'Space Grotesk',sans-serif;">0</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        ui.injectIcons(view);

        // Start polling if we switch to this view
        this.startPolling();
    },

    preview: async function () {
        const text = document.getElementById('broadcast-text').value;
        if (!text) return;

        try {
            const res = await API.post('/broadcast/preview', { text });
            document.getElementById('broadcast-preview-container').style.display = 'block';
            const previewEl = document.getElementById('broadcast-preview-content');
            previewEl.textContent = res.text || '';
            previewEl.style.whiteSpace = 'pre-wrap';
        } catch (e) { }
    },

    confirmSend: async function () {
        const text = document.getElementById('broadcast-text').value;
        if (!text) return;

        if (!confirm("Запустить массовую рассылку? Это действие нельзя отменить.")) return;

        try {
            await API.post('/broadcast/send', { text });
            ui.toast("Рассылка запущена", "success");
            document.getElementById('broadcast-text').value = '';
            document.getElementById('broadcast-preview-container').style.display = 'none';
            this.pollStatus(); // force immediate poll
        } catch (e) {
            ui.toast(e.message || "Ошибка запуска", "error");
        }
    },

    startPolling: function () {
        this.stopPolling();
        this.pollStatus(); // initial
        this.pollInterval = setInterval(() => this.pollStatus(), 2000);
    },

    stopPolling: function () {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    },

    pollStatus: async function () {
        // Only poll if we are on the broadcast view
        if (window.location.hash !== '#broadcast') {
            this.stopPolling();
            return;
        }

        try {
            const data = await API.get('/broadcast/status');
            this.renderStatus(data);
        } catch (e) {
            console.error("Poll failed");
        }
    },

    renderStatus: function (data) {
        const card = document.getElementById('broadcast-status-card');
        const btn = document.getElementById('btn-broadcast-send');

        if (!data || data.status === 'idle') {
            card.style.display = 'none';
            btn.disabled = false;
            return;
        }

        card.style.display = 'flex';

        const stateEl = document.getElementById('broadcast-state');
        const progBar = document.getElementById('broadcast-progress-bar');

        if (data.status === 'in_progress') {
            stateEl.className = 'badge warning text-dark';
            stateEl.innerText = 'В процессе';
            btn.disabled = true;
        } else if (data.status === 'completed') {
            stateEl.className = 'badge success';
            stateEl.innerText = 'Завершено';
            btn.disabled = false;
        } else {
            stateEl.className = 'badge danger';
            stateEl.innerText = 'Ошибка / Отмена';
            btn.disabled = false;
        }

        const processed = data.sent + data.failed;
        const total = data.total || 1; // prevent div by 0
        const pct = Math.round((processed / total) * 100);

        document.getElementById('broadcast-progress-text').innerText = `${processed} / ${data.total}`;
        progBar.style.width = `${pct}%`;

        document.getElementById('broadcast-sent').innerText = data.sent;
        document.getElementById('broadcast-failed').innerText = data.failed;
    }
};

// Override hash change to clean up polling
const originalHash = app.onHashChange;
app.onHashChange = function () {
    if (window.modules?.broadcast) {
        window.modules.broadcast.stopPolling();
    }
    originalHash.apply(app, arguments);
};
