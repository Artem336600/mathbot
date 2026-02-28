/**
 * Users Module
 */

window.modules = window.modules || {};

window.modules.users = {
    data: [],
    page: 1,
    limit: 50,
    search: '',

    load: async function () {
        const view = document.getElementById('view-users');

        view.innerHTML = `
            <div class="header-actions mb-3" style="display:flex; justify-content:space-between; align-items:flex-end;">
                <div>
                    <h2 style="font-size:18px;">Пользователи бота</h2>
                    <p class="text-muted" style="margin-top:4px;">Управление пользователями и блокировки</p>
                </div>
            </div>
            
            <div class="mb-4" style="display:flex; gap:10px; max-width:400px;">
                <input type="text" id="users-search" class="form-control" placeholder="Поиск по нику, имени или ID..." value="${this.search}" onkeypress="if(event.key === 'Enter') modules.users.doSearch()">
                <button class="btn btn-primary" onclick="modules.users.doSearch()" style="padding: 12px 16px;">
                    <span class="icon-slot" data-icon="search"></span>
                </button>
            </div>
            
            <div id="users-content">
                <div class="text-center" style="padding:40px;">
                    ${window.svgAnim ? window.svgAnim.loader(40) : 'Загрузка...'}
                </div>
            </div>
            
            <div class="mt-4" style="display:flex; justify-content:space-between; align-items:center;">
                <button class="btn btn-secondary" onclick="modules.users.prevPage()" id="btn-prev-page" disabled>&larr; Назад</button>
                <span id="page-indicator" class="badge secondary" style="font-family:'Space Grotesk',sans-serif;">Страница ${this.page}</span>
                <button class="btn btn-secondary" onclick="modules.users.nextPage()" id="btn-next-page" disabled>Вперед &rarr;</button>
            </div>
        `;
        ui.injectIcons(view);

        await this.fetchData();
    },

    fetchData: async function () {
        const content = document.getElementById('users-content');
        document.getElementById('btn-prev-page').disabled = this.page <= 1;
        document.getElementById('page-indicator').innerText = `Страница ${this.page}`;

        try {
            const query = `?page=${this.page}&limit=${this.limit}${this.search ? '&search=' + encodeURIComponent(this.search) : ''}`;
            this.data = await API.get(`/users/${query}`);

            // Disable next if we got less than limit (end of results)
            document.getElementById('btn-next-page').disabled = this.data.length < this.limit;

            this.renderTable();
        } catch (e) {
            content.innerHTML = window.svgAnim ? window.svgAnim.emptyState("Ошибка загрузки данных") : `<p class="text-danger text-center">Ошибка загрузки</p>`;
        }
    },

    doSearch: function () {
        const val = document.getElementById('users-search').value.trim();
        this.search = val;
        this.page = 1;
        this.fetchData();
    },

    prevPage: function () {
        if (this.page > 1) {
            this.page--;
            this.fetchData();
        }
    },

    nextPage: function () {
        this.page++;
        this.fetchData();
    },

    renderTable: function () {
        const content = document.getElementById('users-content');
        if (!this.data || this.data.length === 0) {
            content.innerHTML = window.svgAnim ? window.svgAnim.emptyState("Пользователи не найдены") : `<p class="text-muted text-center">Пользователи не найдены</p>`;
            return;
        }

        const rows = this.data.map(u => {
            const statusBadge = u.is_banned
                ? `<span class="badge danger">Забанен</span>`
                : `<span class="badge success">Активен</span>`;

            return `
                <tr>
                    <td>
                        <div style="font-weight:500; font-family:'Inter',sans-serif;">${u.first_name || 'Неизвестно'}</div>
                        <div class="text-muted" style="font-size:11px; margin-top:2px;">${u.username ? '@' + u.username : 'ID: ' + u.id}</div>
                    </td>
                    <td>
                        <div style="font-family:'Space Grotesk',sans-serif;">XP: ${u.xp}</div>
                        <div class="text-primary" style="font-size:11px; margin-top:2px; font-weight:600;">${u.level || 'Новичок'}</div>
                    </td>
                    <td>
                        <div style="font-family:'Space Grotesk',sans-serif;">${Math.round(u.accuracy_rate * 100)}%</div>
                        <div class="text-warning" style="font-size:11px; margin-top:2px; display:flex; gap:4px; align-items:center;">
                            <span class="icon-slot" data-icon="arrow-up" data-size="10"></span> ${u.streak_days} дн.
                        </div>
                    </td>
                    <td>${statusBadge}</td>
                    <td class="text-right" style="display:flex; justify-content:flex-end; gap:6px;">
                        <button class="btn-icon" title="Написать сообщение" onclick="modules.users.openMessageModal(${u.id}, '${(u.first_name || '').replace(/'/g, "&#39;")}')">
                            <span class="icon-slot text-primary" data-icon="send"></span>
                        </button>
                        ${u.is_banned
                    ? `<button class="btn-icon text-success" title="Разбанить" onclick="modules.users.unban(${u.id})"><span class="icon-slot" data-icon="check"></span></button>`
                    : `<button class="btn-icon text-danger" title="Забанить" onclick="modules.users.ban(${u.id})"><span class="icon-slot" data-icon="ban"></span></button>`
                }
                    </td>
                </tr>
            `;
        }).join('');

        content.innerHTML = `
            <div class="table-container">
                <table class="table w-100" id="users-table">
                    <thead>
                        <tr>
                            <th>ID / User</th>
                            <th>Опыт / Уровень</th>
                            <th>Точность / Стрик</th>
                            <th>Статус</th>
                            <th class="text-right">Действия</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
        ui.injectIcons(content);
    },

    ban: async function (id) {
        if (!confirm("Заблокировать пользователя? Он не сможет пользоваться ботом.")) return;
        try {
            await API.post(`/users/${id}/ban`, {});
            ui.toast("Пользователь заблокирован", "success");
            this.fetchData();
        } catch (e) { }
    },

    unban: async function (id) {
        try {
            await API.post(`/users/${id}/unban`, {});
            ui.toast("Пользователь разблокирован", "success");
            this.fetchData();
        } catch (e) { }
    },

    openMessageModal: function (id, name) {
        ui.modal(`
            <h3>Сообщение для: ${name}</h3>
            <p class="text-muted mb-4" style="font-size:12px;">Уведомление будет отправлено ботом напрямую пользователю.</p>
            <form onsubmit="event.preventDefault(); modules.users.sendMessage(${id})">
                <div class="form-group">
                    <textarea id="msg_text" class="form-control" rows="4" required placeholder="Введите текст сообщения..."></textarea>
                </div>
                <div class="form-actions mt-4" style="display:flex; justify-content:flex-end; gap:12px;">
                    <button type="button" class="btn btn-secondary" onclick="ui.closeModal()">Отмена</button>
                    <button type="submit" class="btn btn-primary">
                        <span class="icon-slot" data-icon="send"></span> Отправить
                    </button>
                </div>
            </form>
        `);
    },

    sendMessage: async function (id) {
        const text = document.getElementById('msg_text').value;
        try {
            await API.post(`/users/${id}/message`, { text });
            ui.toast("Сообщение успешно отправлено", "success");
            ui.closeModal();
        } catch (e) { }
    }
};
