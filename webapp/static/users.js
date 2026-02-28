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
            <div class="header-actions mb-3" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="font-size:18px;">Пользователи бота</h2>
                    <p class="text-muted">Управление пользователями и блокировки</p>
                </div>
            </div>
            
            <div class="mb-3" style="display:flex; gap:10px;">
                <input type="text" id="users-search" class="form-control" placeholder="Поиск по нику, имени или ID..." value="${this.search}" onkeypress="if(event.key === 'Enter') modules.users.doSearch()">
                <button class="btn btn-primary" onclick="modules.users.doSearch()"><i class="fa-solid fa-magnifying-glass"></i></button>
            </div>
            
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
                    <tbody>
                        <tr><td colspan="5" class="text-center text-muted">Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="mt-3" style="display:flex; justify-content:space-between; align-items:center;">
                <button class="btn btn-secondary" onclick="modules.users.prevPage()" id="btn-prev-page"><i class="fa-solid fa-chevron-left"></i> Назад</button>
                <span id="page-indicator" class="text-muted">Страница ${this.page}</span>
                <button class="btn btn-secondary" onclick="modules.users.nextPage()" id="btn-next-page">Вперед <i class="fa-solid fa-chevron-right"></i></button>
            </div>
        `;

        await this.fetchData();
    },

    fetchData: async function () {
        const tbody = document.querySelector('#users-table tbody');
        document.getElementById('btn-prev-page').disabled = this.page <= 1;
        document.getElementById('page-indicator').innerText = `Страница ${this.page}`;

        try {
            const query = `?page=${this.page}&limit=${this.limit}${this.search ? '&search=' + encodeURIComponent(this.search) : ''}`;
            this.data = await API.get(`/users/${query}`);

            // Disable next if we got less than limit (end of results)
            document.getElementById('btn-next-page').disabled = this.data.length < this.limit;

            this.renderTable();
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Ошибка загрузки</td></tr>`;
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
        const tbody = document.querySelector('#users-table tbody');
        if (!this.data || this.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Пользователи не найдены</td></tr>`;
            return;
        }

        tbody.innerHTML = this.data.map(u => {
            const statusBadge = u.is_banned
                ? `<span class="badge bg-danger" style="color:white;">Забанен</span>`
                : `<span class="badge bg-success" style="color:white;">Активен</span>`;

            return `
                <tr>
                    <td>
                        <div style="font-weight:600">${u.first_name}</div>
                        <div class="text-muted" style="font-size:11px;">${u.username ? '@' + u.username : 'ID: ' + u.id}</div>
                    </td>
                    <td>
                        <div>XP: ${u.xp}</div>
                        <div class="text-primary" style="font-size:11px;">${u.level}</div>
                    </td>
                    <td>
                        <div>${Math.round(u.accuracy_rate * 100)}%</div>
                        <div class="text-warning" style="font-size:11px;"><i class="fa-solid fa-fire"></i> ${u.streak_days} дн.</div>
                    </td>
                    <td>${statusBadge}</td>
                    <td class="text-right">
                        <button class="btn-icon" title="Написать сообщение" onclick="modules.users.openMessageModal(${u.id}, '${u.first_name}')"><i class="fa-solid fa-paper-plane"></i></button>
                        ${u.is_banned
                    ? `<button class="btn-icon text-success" title="Разбанить" onclick="modules.users.unban(${u.id})"><i class="fa-solid fa-unlock"></i></button>`
                    : `<button class="btn-icon text-danger" title="Забанить" onclick="modules.users.ban(${u.id})"><i class="fa-solid fa-ban"></i></button>`
                }
                    </td>
                </tr>
            `;
        }).join('');
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
            <p class="text-muted mb-3" style="font-size:12px;">Уведомление будет отправлено ботом напрямую пользователю.</p>
            <form onsubmit="event.preventDefault(); modules.users.sendMessage(${id})">
                <div class="form-group">
                    <textarea id="msg_text" class="form-control" rows="4" required placeholder="Введите текст сообщения..."></textarea>
                </div>
                <div class="form-actions mt-3" style="display:flex; justify-content:flex-end; gap:10px;">
                    <button type="button" class="btn btn-secondary" onclick="ui.closeModal()">Отмена</button>
                    <button type="submit" class="btn btn-primary"><i class="fa-solid fa-paper-plane mr-2"></i> Отправить</button>
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
