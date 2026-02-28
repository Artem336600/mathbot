/**
 * Broadcast Module
 */

window.modules = window.modules || {};

window.modules.broadcast = {
    pollInterval: null,

    load: async function () {
        const view = document.getElementById('view-broadcast');

        view.innerHTML = `
            <div class="header-actions mb-3">
                <h2 style="font-size:18px;">Массовая рассылка</h2>
                <p class="text-muted">Отправка сообщений всем пользователям бота</p>
            </div>
            
            <div style="display:grid; grid-template-columns:1fr; gap:20px;">
                <!-- Form Area -->
                <div class="stat-card" style="align-items:flex-start; display:block;">
                    <form onsubmit="event.preventDefault(); modules.broadcast.confirmSend()">
                        <div class="form-group mb-3">
                            <label>Текст сообщения (поддерживается HTML)</label>
                            <textarea id="broadcast-text" class="form-control" rows="8" required placeholder="<b>Внимание!</b> Новая тема доступна для изучения..."></textarea>
                            <small class="text-muted mt-2" style="display:block;">
                                Разрешенные теги: &lt;b&gt;, &lt;i&gt;, &lt;u&gt;, &lt;s&gt;, &lt;a href="..."&gt;, &lt;code&gt;, &lt;pre&gt;
                            </small>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <button type="button" class="btn btn-secondary" onclick="modules.broadcast.preview()"><i class="fa-solid fa-eye mr-2"></i> Предпросмотр</button>
                            <button type="submit" class="btn btn-primary" id="btn-broadcast-send"><i class="fa-solid fa-paper-plane mr-2"></i> Запустить рассылку</button>
                        </div>
                    </form>
                </div>
                
                <!-- Status Area -->
                <div class="stat-card" id="broadcast-status-card" style="display:none; flex-direction:column; align-items:flex-start;">
                    <h3 style="margin-bottom:16px;">Статус рассылки</h3>
                    
                    <div style="width:100%; margin-bottom:16px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                            <span id="broadcast-state" class="badge">Неизвестно</span>
                            <span id="broadcast-progress-text" class="text-muted">0 / 0</span>
                        </div>
                        <div style="width:100%; height:8px; background:var(--c-bg); border-radius:4px; overflow:hidden;">
                            <div id="broadcast-progress-bar" style="height:100%; width:0%; background:var(--c-primary); transition:width 0.3s;"></div>
                        </div>
                    </div>
                    
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; width:100%;">
                        <div style="background:var(--c-bg); padding:10px; border-radius:var(--radius-sm); border-left:3px solid var(--c-success);">
                            <div class="text-muted" style="font-size:11px;">Доставлено</div>
                            <div id="broadcast-sent" style="font-size:20px; font-weight:700;">0</div>
                        </div>
                        <div style="background:var(--c-bg); padding:10px; border-radius:var(--radius-sm); border-left:3px solid var(--c-danger);">
                            <div class="text-muted" style="font-size:11px;">Заблокировали бота (Failed)</div>
                            <div id="broadcast-failed" style="font-size:20px; font-weight:700;">0</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="broadcast-preview-container" class="mt-4" style="display:none;">
                <h3 class="mb-2">Предпросмотр:</h3>
                <div id="broadcast-preview-content" style="background:#fff; color:#000; padding:16px; border-radius:12px; max-width:400px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
                </div>
            </div>
        `;

        // Start polling if we switch to this view
        this.startPolling();
    },

    preview: async function () {
        const text = document.getElementById('broadcast-text').value;
        if (!text) return;

        try {
            const res = await API.post('/broadcast/preview', { text });
            document.getElementById('broadcast-preview-container').style.display = 'block';
            // Just inserting HTML as Telegram desktop roughly renders it.
            // XSS note: it's admin panel, so trust level is higher, but standard caveat applies.
            document.getElementById('broadcast-preview-content').innerHTML = res.html.replace(/\n/g, '<br>');
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
            stateEl.className = 'badge bg-warning text-dark';
            stateEl.innerText = 'В процессе';
            btn.disabled = true;
        } else if (data.status === 'completed') {
            stateEl.className = 'badge bg-success';
            stateEl.innerText = 'Завершено';
            btn.disabled = false;
        } else {
            stateEl.className = 'badge bg-danger';
            stateEl.innerText = 'Ошибка';
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
