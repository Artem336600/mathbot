/**
 * Dashboard Module 
 * Bento Grid Layout with SVG Icons and Count-Up Animation
 */

window.modules = window.modules || {};

window.modules.dashboard = {
    load: async function () {
        const view = document.getElementById('view-dashboard');

        try {
            // Render Shimmer Skeleton inside Bento Grid
            view.innerHTML = `
                <div class="bento-grid">
                    <div class="stat-card skeleton col-2" style="min-height: 180px;"></div>
                    <div class="stat-card skeleton"></div>
                    <div class="stat-card skeleton"></div>
                    <div class="stat-card skeleton col-2" style="min-height: 140px;"></div>
                    <div class="stat-card skeleton col-2" style="min-height: 140px;"></div>
                </div>
            `;

            // Fetch Real Data
            const data = await API.get('/stats/');

            // Build Real UI
            view.innerHTML = `
                <div class="bento-grid">
                    <!-- Big Card: Total Users -->
                    <div class="stat-card col-2">
                        <div class="stat-header">
                            <div class="stat-info">
                                <h3>Пользователи</h3>
                                <div class="stat-value count-up" data-val="${data.total_users}">0</div>
                            </div>
                            <div class="stat-icon primary">
                                <span class="icon-slot" data-icon="users" data-size="24"></span>
                            </div>
                        </div>
                        <div class="stat-meta text-success">
                            <span class="icon-slot" data-icon="arrow-up" data-size="14"></span>
                            <span>${data.active_users} активных</span>
                        </div>
                    </div>
                    
                    <!-- Standard Card: Topics -->
                    <div class="stat-card">
                        <div class="stat-header">
                            <div class="stat-info">
                                <h3>Темы</h3>
                                <div class="stat-value count-up" data-val="${data.total_topics}">0</div>
                            </div>
                            <div class="stat-icon" style="background: rgba(255,255,255,0.05);">
                                <span class="icon-slot" data-icon="layers" data-size="24"></span>
                            </div>
                        </div>
                        <div class="stat-meta text-muted">Разделы для изучения</div>
                    </div>

                    <!-- Standard Card: Questions -->
                    <div class="stat-card">
                        <div class="stat-header">
                            <div class="stat-info">
                                <h3>Вопросы</h3>
                                <div class="stat-value count-up" data-val="${data.total_questions}">0</div>
                            </div>
                            <div class="stat-icon" style="background: rgba(255,255,255,0.05);">
                                <span class="icon-slot" data-icon="clipboard-question" data-size="24"></span>
                            </div>
                        </div>
                        <div class="stat-meta text-muted">В базе знаний</div>
                    </div>

                    <!-- Wide Card: Banned Users -->
                    <div class="stat-card" style="grid-column: span 4;">
                        <div class="stat-header">
                            <div class="stat-info">
                                <h3>Забанены</h3>
                                <div class="stat-value text-danger count-up" data-val="${data.banned_users}">0</div>
                            </div>
                            <div class="stat-icon danger">
                                <span class="icon-slot" data-icon="ban" data-size="24"></span>
                            </div>
                        </div>
                        <div class="stat-meta text-danger">
                            <span class="icon-slot" data-icon="alert-triangle" data-size="14"></span>
                            <span>Заблокированные аккаунты</span>
                        </div>
                    </div>
                </div>
            `;

            ui.injectIcons(view);
            this.animateCountUp();

        } catch (e) {
            if (window.svgAnim) {
                view.innerHTML = window.svgAnim.emptyState("Ошибка загрузки дашборда");
            } else {
                view.innerHTML = `<p class="text-danger">Ошибка загрузки дашборда</p>`;
            }
        }
    },

    animateCountUp: function () {
        const elements = document.querySelectorAll('.count-up');
        const duration = 1200; // ms

        elements.forEach(el => {
            const target = parseInt(el.getAttribute('data-val'), 10);
            if (isNaN(target)) return;

            if (target === 0) {
                el.innerText = "0";
                return;
            }

            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                // easeOutQuad
                const easeOut = progress * (2 - progress);

                el.innerText = Math.floor(easeOut * target).toLocaleString('ru-RU');

                if (progress < 1) {
                    window.requestAnimationFrame(step);
                } else {
                    el.innerText = target.toLocaleString('ru-RU');
                }
            };
            window.requestAnimationFrame(step);
        });
    }
};
