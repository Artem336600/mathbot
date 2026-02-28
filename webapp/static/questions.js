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
                    <label class="text-muted mb-2" style="display:block; font-size:12px;">Выберите тему</label>
                    <div class="form-group" style="margin:0;">
                        <select id="questions-topic-select" class="form-control" onchange="modules.questions.onTopicChange()">
                            <option value="">Загрузка тем...</option>
                        </select>
                    </div>
                </div>
                
                <div style="display:flex; gap:12px;">
                    <button class="btn btn-secondary" onclick="modules.questions.openImportModal()">
                        <span class="icon-slot" data-icon="upload"></span> Импорт JSON
                    </button>
                    <button class="btn btn-primary" onclick="modules.questions.openModal()">
                        <span class="icon-slot" data-icon="plus"></span> Вопрос
                    </button>
                </div>
            </div>
            
            <div id="questions-list" style="display:flex; flex-direction:column; gap:16px;">
                 ${window.svgAnim ? window.svgAnim.emptyState("Выберите тему для отображения вопросов") : "<div class='text-center text-muted m-5'>Выберите тему</div>"}
            </div>
        `;
        ui.injectIcons(view);

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
        list.innerHTML = `<div class="text-center text-muted" style="padding:40px;">${window.svgAnim ? window.svgAnim.loader(40) : 'Загрузка...'}</div>`;

        try {
            this.data = await API.get(`/questions/?topic_id=${this.currentTopicId}`);
            this.renderQuestions();
        } catch (e) {
            list.innerHTML = window.svgAnim ? window.svgAnim.emptyState("Ошибка загрузки вопросов") : `<div class="text-center text-danger">Ошибка загрузки</div>`;
        }
    },

    renderQuestions: function () {
        const list = document.getElementById('questions-list');
        if (!this.data || this.data.length === 0) {
            list.innerHTML = window.svgAnim ? window.svgAnim.emptyState("В этой теме пока нет вопросов") : `<div class="text-center text-muted" style="padding: 40px; background:var(--c-bg-card); border-radius:var(--radius-md);">В этой теме пока нет вопросов.</div>`;
            return;
        }

        list.innerHTML = this.data.map(q => {
            const diffClass = q.difficulty === 1 ? 'success' : q.difficulty === 2 ? 'warning' : 'danger';
            const diffLabel = q.difficulty === 1 ? 'Уровень 1' : q.difficulty === 2 ? 'Уровень 2' : 'Уровень 3';

            // Just rendering the choices cleanly
            const renderOption = (letter, text, correctValue) => {
                const isCorrect = q.correct_option === correctValue;
                const activeStyle = isCorrect ? `background:rgba(16,185,129,0.1); border-color:var(--c-success);` : `background: rgba(255,255,255,0.02);`;
                return `<div style="padding:6px 12px; border-radius:6px; border:1px solid var(--c-border); ${activeStyle}">
                            <strong style="color:var(--c-text-muted); margin-right:4px;">${letter}:</strong> ${text}
                        </div>`;
            };

            return `
                <div class="stat-card" style="align-items:flex-start;">
                    <div style="flex-grow:1; width:100%;">
                        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
                            <span class="badge ${diffClass}">${diffLabel}</span>
                            <span class="text-muted" style="font-size:12px; font-family:'Space Grotesk',sans-serif;">ID: #${q.id}</span>
                        </div>
                        <h4 style="margin-bottom:16px; font-family:'Inter',sans-serif; font-weight:500;">${q.text}</h4>
                        
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
                            ${renderOption('A', q.option_a, 'a')}
                            ${renderOption('B', q.option_b, 'b')}
                            ${renderOption('C', q.option_c, 'c')}
                            ${renderOption('D', q.option_d, 'd')}
                        </div>
                        
                        ${q.explanation ? `<div class="text-muted" style="font-size:12px; margin-bottom:8px; display:flex; gap:6px; align-items:flex-start;"><span class="icon-slot text-primary" data-icon="info" data-size="14" style="margin-top:2px;"></span> <span>${q.explanation}</span></div>` : ''}
                        ${q.image_url ? `<div class="text-primary" style="font-size:12px; display:flex; gap:6px;"><span class="icon-slot" data-icon="search" data-size="14"></span> Вложение: ${q.image_url.split('/').pop()}</div>` : ''}
                    </div>
                    <div style="position:absolute; bottom:16px; right:16px;">
                        <button class="btn-icon" title="Редактировать" style="background:var(--c-bg-glass); border:1px solid var(--c-border-subtle);" onclick='modules.questions.openModal(${JSON.stringify(q).replace(/'/g, "&#39;")})'>
                            <span class="icon-slot" data-icon="edit"></span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        ui.injectIcons(list);
    },

    openModal: function (q = null) {
        if (!this.currentTopicId) {
            ui.toast("Сначала выберите тему", "error");
            return;
        }

        const isEdit = !!q;
        ui.modal(`
            <h3>${isEdit ? 'Редактировать вопрос' : 'Новый вопрос'}</h3>
            <form id="question-form" class="mt-4" onsubmit="event.preventDefault(); modules.questions.save(${q?.id || 'null'})">
                <div class="form-group">
                    <label>Текст вопроса</label>
                    <textarea id="q_text" class="form-control" rows="2" required>${q?.text || ''}</textarea>
                </div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="form-group mb-1"><label>А</label><input type="text" id="q_a" class="form-control" value="${q?.option_a || ''}" required></div>
                    <div class="form-group mb-1"><label>B</label><input type="text" id="q_b" class="form-control" value="${q?.option_b || ''}" required></div>
                    <div class="form-group mb-1"><label>C</label><input type="text" id="q_c" class="form-control" value="${q?.option_c || ''}" required></div>
                    <div class="form-group mb-1"><label>D</label><input type="text" id="q_d" class="form-control" value="${q?.option_d || ''}" required></div>
                </div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:12px;">
                    <div class="form-group">
                        <label>Правильный ответ</label>
                        <select id="q_correct" class="form-control" required style="cursor:pointer;">
                            <option value="a" ${q?.correct_option === 'a' ? 'selected' : ''}>A</option>
                            <option value="b" ${q?.correct_option === 'b' ? 'selected' : ''}>B</option>
                            <option value="c" ${q?.correct_option === 'c' ? 'selected' : ''}>C</option>
                            <option value="d" ${q?.correct_option === 'd' ? 'selected' : ''}>D</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Сложность</label>
                        <select id="q_diff" class="form-control" required style="cursor:pointer;">
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
                
                <div class="form-actions" style="display:flex; justify-content:flex-end; gap:12px; padding-top:12px; border-top:1px solid var(--c-border-subtle);">
                    ${isEdit ? `<button type="button" class="btn btn-danger mr-auto" onclick="modules.questions.delete(${q.id})" style="margin-right:auto"><span class="icon-slot" data-icon="trash"></span> Удалить</button>` : ''}
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

    openImportModal: function () {
        if (!this.currentTopicId) {
            ui.toast("Сначала выберите тему", "error");
            return;
        }

        const topicName = this.topics.find(t => t.id == this.currentTopicId)?.title || 'выбранную тему';

        ui.modal(`
            <h3>Импорт вопросов</h3>
            <p class="text-muted mt-2 mb-3">Загрузка JSON-файла в тему <strong>${topicName}</strong></p>
            
            <div style="background:var(--c-bg); padding:16px; border-radius:var(--radius-sm); border:1px solid var(--c-border); margin-bottom:16px;">
                <h4 style="font-size:14px; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                    <span class="icon-slot text-primary" data-icon="info" data-size="14"></span> Формат файла:
                </h4>
                <p class="text-muted" style="font-size:12px; margin-bottom:12px;">Файл должен содержать массив объектов со следующими полями:</p>
                <div style="background:#0d0d12; padding:12px; border-radius:6px; font-family:monospace; font-size:11px; color:#a855f7; overflow-x:auto;">
[
  {
    "text": "Текст вопроса?",
    "option_a": "Вариант А",
    "option_b": "Вариант B",
    "option_c": "Вариант C",
    "option_d": "Вариант D",
    "correct_option": "a", // a, b, c, d
    "difficulty": 1,       // 1-3
    "explanation": "Опц.",
    "image_url": "Опц."
  }
]
                </div>
            </div>
            
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
                <button class="btn btn-secondary" onclick="ui.closeModal()">Отмена</button>
                <div style="position:relative; overflow:hidden; display:inline-block;">
                    <button class="btn btn-primary">
                        <span class="icon-slot" data-icon="upload"></span> Выбрать файл
                    </button>
                    <input type="file" id="questions-import-file" accept=".json" style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; cursor:pointer;" onchange="modules.questions.importJson(event)">
                </div>
            </div>
        `);
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
        ui.closeModal();

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
