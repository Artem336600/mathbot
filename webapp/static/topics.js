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

                ${isEdit ? `<div id="topic-attachments-wrap"></div>` : `
                <div class="form-group mt-2" style="padding:12px; background:rgba(255,255,255,0.03); border-radius:var(--radius-sm); border:1px dashed var(--c-border-subtle);">
                    <p class="text-muted" style="font-size:12px; margin:0;">💡 После сохранения темы здесь появится загрузчик фотографий и документов</p>
                </div>`}

                <div class="form-actions" style="display:flex; justify-content:flex-end; gap:12px; margin-top:24px;">
                    ${isEdit ? `<button type="button" class="btn btn-danger mr-auto" onclick="modules.topics.delete(${topic.id})" style="margin-right:auto"><span class="icon-slot" data-icon="trash"></span> Удалить</button>` : ''}
                    <button type="button" class="btn btn-secondary" onclick="ui.closeModal()">Отмена</button>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        `);

        if (isEdit && topic.id) {
            if (topic.image_url) {
                const wrap = document.getElementById('topic-attachments-wrap');
                if (wrap) {
                    wrap.insertAdjacentHTML('beforeend', `
                        <div style="margin-top:16px;">
                            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                                <label style="font-size:13px; font-weight:600; color:var(--c-text); display:flex; align-items:center; gap:8px;">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
                                    </svg>
                                    Изображение (URL)
                                </label>
                                <span class="badge secondary" style="font-size:10px;">Из JSON-импорта</span>
                            </div>
                            <div style="display:flex; align-items:flex-start; gap:12px; padding:10px 14px;
                                background:rgba(255,255,255,0.03); border:1px solid var(--c-border-subtle); border-radius:var(--radius-sm);" data-legacy-img="1">
                                <img src="${topic.image_url.replace(/"/g, '&quot;')}" 
                                    style="width:64px; height:64px; object-fit:cover; border-radius:6px; flex-shrink:0; border:1px solid var(--c-border);"
                                    onerror="this.style.display='none'">
                                <div style="flex-grow:1; min-width:0;">
                                    <div style="font-size:12px; color:var(--c-text-muted); word-break:break-all;">${topic.image_url}</div>
                                    <div style="margin-top:8px; display:flex; align-items:center; gap:8px;">
                                        <input type="text" id="t_img_url" class="form-control" value="${topic.image_url.replace(/"/g, '&quot;')}" 
                                            style="font-size:12px; flex:1;" placeholder="URL изображения">
                                        <button type="button" class="btn btn-secondary" style="font-size:11px; padding:5px 10px; white-space:nowrap;"
                                            onclick="document.getElementById('t_img_url').value=''; this.closest('div[data-legacy-img]').remove();">
                                            Очистить
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="topic-attachments-inner"></div>
                    `);
                }
            } else {
                const wrap = document.getElementById('topic-attachments-wrap');
                if (wrap) wrap.insertAdjacentHTML('beforeend', `
                    <input type="hidden" id="t_img_url" value="">
                    <div id="topic-attachments-inner"></div>
                `);
            }
            AttachmentsComponent.render('topic-attachments-inner', 'topic', topic.id, 'photos+docs');
        }
    },

    save: async function (id) {
        let imageUrl = null;
        if (id) {
            const imgInput = document.getElementById('t_img_url');
            if (imgInput) {
                imageUrl = imgInput.value.trim() || null;
            }
        }

        const payload = {
            title: document.getElementById('topic_title').value,
            theory_text: document.getElementById('topic_theory').value || null,
            image_url: imageUrl,
        };

        try {
            if (id) {
                await API.patch(`/topics/${id}`, payload);
                ui.toast("Тема сохранена", "success");
                ui.closeModal();
            } else {
                const created = await API.post(`/topics/`, payload);
                ui.toast("Тема создана. Теперь откройте её для добавления вложений.", "success");
                ui.closeModal();
            }
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
