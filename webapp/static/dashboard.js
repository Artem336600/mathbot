/**
 * Dashboard Module 
 */

window.modules = window.modules || {};

window.modules.dashboard = {
    load: async function () {
        const view = document.getElementById('view-dashboard');

        try {
            // Render skeleton
            view.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card skeleton"></div>
                    <div class="stat-card skeleton"></div>
                    <div class="stat-card skeleton"></div>
                    <div class="stat-card skeleton"></div>
                    <div class="stat-card skeleton"></div>
                    <div class="stat-card skeleton"></div>
                </div>
            `;

            // Fetch stats Data
            const data = await API.get('/stats/');

            // Render Real Data
            view.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon bg-primary"><i class="fa-solid fa-users"></i></div>
                        <div class="stat-info">
                            <h3>Пользователи</h3>
                            <div class="stat-value">${data.total_users}</div>
                            <small class="text-success">${data.active_users} активных</small>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon bg-danger"><i class="fa-solid fa-user-slash"></i></div>
                        <div class="stat-info">
                            <h3>Забанены</h3>
                            <div class="stat-value text-danger">${data.banned_users}</div>
                            <small class="text-muted">Всего заблокировано</small>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-success"><i class="fa-solid fa-layer-group"></i></div>
                        <div class="stat-info">
                            <h3>Темы</h3>
                            <div class="stat-value">${data.total_topics}</div>
                            <small class="text-muted">Разделы для изучения</small>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-warning"><i class="fa-solid fa-clipboard-question"></i></div>
                        <div class="stat-info">
                            <h3>Вопросы</h3>
                            <div class="stat-value">${data.total_questions}</div>
                            <small class="text-muted">В базе знаний</small>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-primary"><i class="fa-solid fa-check-double"></i></div>
                        <div class="stat-info">
                            <h3>Ответы (всего)</h3>
                            <div class="stat-value">${data.total_answers}</div>
                            <small class="text-muted">Решений задач</small>
                        </div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon bg-success"><i class="fa-solid fa-calendar-day"></i></div>
                        <div class="stat-info">
                            <h3>Ответы (сегодня)</h3>
                            <div class="stat-value">${data.answers_today}</div>
                            <small class="text-success">За последние 24ч</small>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            view.innerHTML = `<p class="text-danger">Ошибка загрузки дашборда</p>`;
        }
    }
};
