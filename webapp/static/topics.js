/**
 * Topics Module
 */

window.modules = window.modules || {};

window.modules.topics = {
    data: [],

    load: async function () {
        const view = document.getElementById('view-topics');

        view.innerHTML = `
            <div class="header-actions mb-3" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="font-size:18px;">Управление темами</h2>
                    <p class="text-muted" style="margin-top:4px;">Темы, доступные для изучения</p>
                </div>
                <button class="btn btn-primary" onclick="modules.topics.openModal()">
                    <span class="icon-slot" data-icon="plus"></span> Создать тему
                </button>
            </div>
            
            <div id="topics-content">
                <div class="text-center" style="padding:40px;">
                    ${window.svgAnim ? window.svgAnim.loader(40) : 'Загрузка...'}
                </div>
            </div>
        `;
        ui.injectIcons(view);

        await this.fetchData();
    },

    fetchData: async function () {
        const content = document.getElementById('topics-content');
        try {
            this.data = await API.get('/topics/');
            this.renderTable();
        } catch (e) {
            content.innerHTML = window.svgAnim ? window.svgAnim.emptyState("Ошибка загрузки данных") : `<p class="text-danger text-center">Ошибка загрузки</p>`;
        }
    },

    renderTable: function () {
        const content = document.getElementById('topics-content');
        if (!this.data || this.data.length === 0) {
            content.innerHTML = window.svgAnim ? window.svgAnim.emptyState("Нет добавленных тем") : `<p class="text-center">Нет тем</p>`;
            return;
        }

        const rows = this.data.map(t => {
            const statusBadge = t.is_active
                ? `<span class="badge success" style="cursor:pointer;" onclick="modules.topics.toggle(${t.id})">Активна</span>`
                : `<span class="badge secondary" style="cursor:pointer;" onclick="modules.topics.toggle(${t.id})">Скрыта</span>`;

            return `
                <tr>
                    <td style="color:var(--c-text-muted);">#${t.id}</td>
                    <td><strong>${t.title}</strong></td>
                    <td style="font-family:'Space Grotesk',sans-serif;">${t.questions_count}</td>
                    <td>${statusBadge}</td>
                    <td class="text-right">
                        <button class="btn-icon" onclick='modules.topics.openModal(${JSON.stringify(t).replace(/'/g, "&#39;")})'>
                            <span class="icon-slot" data-icon="edit"></span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        content.innerHTML = `
            <div class="table-container">
                <table class="table w-100" id="topics-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Название</th>
                            <th>Вопросов</th>
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

    toggle: async function (id) {
        try {
            await API.patch(`/topics/${id}/toggle`);
            ui.toast("Статус темы изменен", "success");
            this.fetchData();
        } catch (e) { }
    },

    openModal: function (topic = null) {
        const isEdit = !!topic;
        const title = isEdit ? `Редактирование: ${topic.title}` : "Новая тема";

        ui.modal(`
            <h3>${title}</h3>
            <form id="topic-form" class="mt-3" onsubmit="event.preventDefault(); modules.topics.save(${topic?.id || 'null'})">
                <div class="form-group">
                    <label>Название темы</label>
                    <input type="text" id="topic_title" class="form-control" required value="${topic?.title || ''}" placeholder="Дроби и проценты">
                </div>
                <div class="form-group mt-2">
                    <label>Теория (опционально)</label>
                    <textarea id="topic_theory" class="form-control" rows="4">${topic?.theory_text || ''}</textarea>
                </div>
                <div class="form-group mt-2 mb-3">
                    <label>URL картинки (опционально)</label>
                    <input type="text" id="topic_image_url" class="form-control" value="${topic?.image_url || ''}">
                </div>
                
                <div class="form-actions" style="display:flex; justify-content:flex-end; gap:12px; margin-top:24px;">
                    ${isEdit ? `<button type="button" class="btn btn-danger mr-auto" onclick="modules.topics.delete(${topic.id})" style="margin-right:auto"><span class="icon-slot" data-icon="trash"></span> Удалить</button>` : ''}
                    <button type="button" class="btn btn-secondary" onclick="ui.closeModal()">Отмена</button>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        `);
    },

    save: async function (id) {
        const payload = {
            title: document.getElementById('topic_title').value,
            theory_text: document.getElementById('topic_theory').value || null,
            image_url: document.getElementById('topic_image_url').value || null,
        };

        try {
            if (id) {
                await API.patch(`/topics/${id}`, payload);
                ui.toast("Тема сохранена", "success");
            } else {
                await API.post(`/topics/`, payload);
                ui.toast("Тема создана", "success");
            }
            ui.closeModal();
            this.fetchData();
        } catch (e) { }
    },

    delete: async function (id) {
        if (!confirm("Удалить тему? Все вопросы в ней могут стать недоступны.")) return;
        try {
            await API.delete(`/topics/${id}`);
            ui.toast("Тема удалена", "success");
            ui.closeModal();
            this.fetchData();
        } catch (e) { }
    }
};
