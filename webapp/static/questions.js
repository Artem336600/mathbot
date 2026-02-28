/**
 * Questions Module
 */

window.modules = window.modules || {};

window.modules.questions = {
    topics: [],
    currentTopicId: null,
    data: [],

    load: async function () {
        const view = document.getElementById('view-questions');

        view.innerHTML = `
            <div class="header-actions mb-3" style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:10px;">
                <div style="flex-grow:1; max-width:300px;">
                    <label class="text-muted mb-1" style="display:block; font-size:12px;">Выберите тему</label>
                    <select id="questions-topic-select" class="form-control" onchange="modules.questions.onTopicChange()">
                        <option value="">Загрузка тем...</option>
                    </select>
                </div>
                
                <div style="display:flex; gap:10px;">
                    <div style="position:relative; overflow:hidden; display:inline-block;">
                        <button class="btn btn-secondary"><i class="fa-solid fa-file-import"></i> Импорт JSON</button>
                        <input type="file" id="questions-import-file" accept=".json" style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; cursor:pointer;" onchange="modules.questions.importJson(event)">
                    </div>
                    <button class="btn btn-primary" onclick="modules.questions.openModal()"><i class="fa-solid fa-plus"></i> Вопрос</button>
                </div>
            </div>
            
            <div id="questions-list" style="display:flex; flex-direction:column; gap:12px;">
                <div class="text-center text-muted py-5">Выберите тему для отображения вопросов</div>
            </div>
        `;

        await this.fetchTopics();
    },

    fetchTopics: async function () {
        try {
            this.topics = await API.get('/topics/');
            const sel = document.getElementById('questions-topic-select');

            if (this.topics.length === 0) {
                sel.innerHTML = `<option value="">Нет доступных тем</option>`;
                return;
            }

            sel.innerHTML = this.topics.map(t => `<option value="${t.id}">${t.title}</option>`).join('');

            // Auto Select first
            if (this.topics.length > 0) {
                this.currentTopicId = this.topics[0].id;
                this.fetchQuestions();
            }
        } catch (e) {
            console.error(e);
        }
    },

    onTopicChange: function () {
        const sel = document.getElementById('questions-topic-select');
        this.currentTopicId = sel.value;
        if (this.currentTopicId) {
            this.fetchQuestions();
        }
    },

    fetchQuestions: async function () {
        const list = document.getElementById('questions-list');
        list.innerHTML = `<div class="text-center text-muted"><div class="spinner mx-auto" style="margin: 0 auto"></div></div>`;

        try {
            this.data = await API.get(`/questions/?topic_id=${this.currentTopicId}`);
            this.renderQuestions();
        } catch (e) {
            list.innerHTML = `<div class="text-center text-danger">Ошибка загрузки</div>`;
        }
    },

    renderQuestions: function () {
        const list = document.getElementById('questions-list');
        if (!this.data || this.data.length === 0) {
            list.innerHTML = `<div class="text-center text-muted" style="padding: 40px; background:var(--c-bg-sec); border-radius:var(--radius-md);">В этой теме пока нет вопросов.</div>`;
            return;
        }

        list.innerHTML = this.data.map(q => {
            const diffColor = q.difficulty === 1 ? 'var(--c-success)' : q.difficulty === 2 ? 'var(--c-warning)' : 'var(--c-danger)';
            const diffLabel = q.difficulty === 1 ? 'Уровень 1' : q.difficulty === 2 ? 'Уровень 2' : 'Уровень 3';

            return `
                <div class="stat-card" style="align-items:flex-start;">
                    <div style="flex-grow:1;">
                        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
                            <span class="badge" style="background:transparent; border:1px solid ${diffColor}; color:${diffColor}">${diffLabel}</span>
                            <span class="text-muted">ID: #${q.id}</span>
                        </div>
                        <h4 style="margin-bottom:12px;">${q.text}</h4>
                        
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;">
                            <div style="padding:4px 8px; border-radius:4px; border:1px solid var(--c-border); ${q.correct_option === 'a' ? 'background:rgba(34,197,94,0.1); border-color:var(--c-success);' : ''}"><strong>A:</strong> ${q.option_a}</div>
                            <div style="padding:4px 8px; border-radius:4px; border:1px solid var(--c-border); ${q.correct_option === 'b' ? 'background:rgba(34,197,94,0.1); border-color:var(--c-success);' : ''}"><strong>B:</strong> ${q.option_b}</div>
                            <div style="padding:4px 8px; border-radius:4px; border:1px solid var(--c-border); ${q.correct_option === 'c' ? 'background:rgba(34,197,94,0.1); border-color:var(--c-success);' : ''}"><strong>C:</strong> ${q.option_c}</div>
                            <div style="padding:4px 8px; border-radius:4px; border:1px solid var(--c-border); ${q.correct_option === 'd' ? 'background:rgba(34,197,94,0.1); border-color:var(--c-success);' : ''}"><strong>D:</strong> ${q.option_d}</div>
                        </div>
                        
                        ${q.explanation ? `<div class="text-muted" style="font-size:12px; margin-bottom:8px;"><i class="fa-solid fa-circle-info"></i> ${q.explanation}</div>` : ''}
                        ${q.image_url ? `<div class="text-primary" style="font-size:12px;"><i class="fa-solid fa-image"></i> Вложение: ${q.image_url.split('/').pop()}</div>` : ''}
                    </div>
                    <div style="display:flex; flex-direction:column; gap:8px;">
                        <button class="btn-icon" title="Редактировать" onclick='modules.questions.openModal(${JSON.stringify(q).replace(/'/g, "&#39;")})'><i class="fa-solid fa-pen"></i></button>
                    </div>
                </div>
            `;
        }).join('');
    },

    openModal: function (q = null) {
        if (!this.currentTopicId) {
            ui.toast("Сначала выберите тему", "error");
            return;
        }

        const isEdit = !!q;
        ui.modal(`
            <h3>${isEdit ? 'Редактировать вопрос' : 'Новый вопрос'}</h3>
            <form id="question-form" class="mt-3" onsubmit="event.preventDefault(); modules.questions.save(${q?.id || 'null'})">
                <div class="form-group">
                    <label>Текст вопроса</label>
                    <textarea id="q_text" class="form-control" rows="2" required>${q?.text || ''}</textarea>
                </div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                    <div class="form-group mb-1"><label>А</label><input type="text" id="q_a" class="form-control" value="${q?.option_a || ''}" required></div>
                    <div class="form-group mb-1"><label>B</label><input type="text" id="q_b" class="form-control" value="${q?.option_b || ''}" required></div>
                    <div class="form-group mb-1"><label>C</label><input type="text" id="q_c" class="form-control" value="${q?.option_c || ''}" required></div>
                    <div class="form-group mb-1"><label>D</label><input type="text" id="q_d" class="form-control" value="${q?.option_d || ''}" required></div>
                </div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
                    <div class="form-group">
                        <label>Правильный ответ</label>
                        <select id="q_correct" class="form-control" required>
                            <option value="a" ${q?.correct_option === 'a' ? 'selected' : ''}>A</option>
                            <option value="b" ${q?.correct_option === 'b' ? 'selected' : ''}>B</option>
                            <option value="c" ${q?.correct_option === 'c' ? 'selected' : ''}>C</option>
                            <option value="d" ${q?.correct_option === 'd' ? 'selected' : ''}>D</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Сложность (1-3)</label>
                        <select id="q_diff" class="form-control" required>
                            <option value="1" ${q?.difficulty === 1 ? 'selected' : ''}>1 (Легкий)</option>
                            <option value="2" ${q?.difficulty === 2 ? 'selected' : ''}>2 (Средний)</option>
                            <option value="3" ${q?.difficulty === 3 ? 'selected' : ''}>3 (Сложный)</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group mt-2">
                    <label>Пояснение (опц.)</label>
                    <textarea id="q_exp" class="form-control" rows="2">${q?.explanation || ''}</textarea>
                </div>
                
                <div class="form-group mt-2 mb-4">
                    <label>URL картинки (опц.)</label>
                    <input type="text" id="q_img" class="form-control" value="${q?.image_url || ''}">
                </div>
                
                <div class="form-actions" style="display:flex; justify-content:flex-end; gap:10px;">
                    ${isEdit ? `<button type="button" class="btn btn-danger mr-auto" onclick="modules.questions.delete(${q.id})" style="margin-right:auto"><i class="fa-solid fa-trash"></i> Удалить</button>` : ''}
                    <button type="button" class="btn btn-secondary" onclick="ui.closeModal()">Отмена</button>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        `);
    },

    save: async function (id) {
        const payload = {
            topic_id: parseInt(this.currentTopicId),
            text: document.getElementById('q_text').value,
            option_a: document.getElementById('q_a').value,
            option_b: document.getElementById('q_b').value,
            option_c: document.getElementById('q_c').value,
            option_d: document.getElementById('q_d').value,
            correct_option: document.getElementById('q_correct').value,
            difficulty: parseInt(document.getElementById('q_diff').value),
            explanation: document.getElementById('q_exp').value || null,
            image_url: document.getElementById('q_img').value || null,
        };

        try {
            if (id) {
                // Topic ID is not modifiable in patch, just updating question data
                await API.patch(`/questions/${id}`, payload);
                ui.toast("Вопрос сохранен", "success");
            } else {
                await API.post(`/questions/`, payload);
                ui.toast("Вопрос создан", "success");
            }
            ui.closeModal();
            this.fetchQuestions();
        } catch (e) { }
    },

    delete: async function (id) {
        if (!confirm("Удалить этот вопрос? Действие необратимо.")) return;
        try {
            await API.delete(`/questions/${id}`);
            ui.toast("Вопрос удален", "success");
            ui.closeModal();
            this.fetchQuestions();
        } catch (e) { }
    },

    importJson: async function (e) {
        if (!this.currentTopicId) {
            ui.toast("Сначала выберите тему для импорта", "warning");
            e.target.value = '';
            return;
        }

        const file = e.target.files[0];
        if (!file) return;

        e.target.value = ''; // reset

        const formData = new FormData();
        formData.append("topic_id", this.currentTopicId);
        formData.append("file", file);

        ui.toast("Импортируем вопросы...", "info");

        try {
            const res = await API.upload('/questions/import', formData);
            if (res.status === 'success') {
                ui.toast(`Успешно импортировано: ${res.imported}`, "success");
            } else if (res.status === 'partial') {
                ui.toast(`Импортировано: ${res.imported}. Есть ошибки (${res.errors.length})`, "warning");
                console.warn("Import Errors:", res.errors);
            } else {
                ui.toast(`Ошибка: ${res.message || 'Не удалось импортировать'}`, "error");
            }
            this.fetchQuestions();
        } catch (err) {
            ui.toast("Сбой импорта файла", "error");
        }
    }
};
