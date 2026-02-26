graph TD
    %% --- Styles ---
    classDef start fill:#f9f,stroke:#333,stroke-width:2px;
    classDef process fill:#e1f5fe,stroke:#0277bd,stroke-width:2px;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef screen fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,rx:5,ry:5;
    classDef admin fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef db fill:#e0f2f1,stroke:#00695c,stroke-width:2px,stroke-dasharray: 5 5;

    %% --- DATA LAYER ---
    subgraph DataLayer [Data Storage]
        direction LR
        PG[(PostgreSQL)]:::db
        RD[(Redis Cache)]:::db
    end

    %% --- Entry Points ---
    Start((Start / Login)):::start -->|"/start"| MainMenu
    Start -.->|Check/Create User| PG

    AdminCommand((/admin)):::admin -->|Admin Access Only| AdminMenu
    AdminCommand -.->|Check Role| PG

    %% --- Persistent Navigation (Reply Keyboard) ---
    subgraph PersistentNav [Reply Keyboard & Commands]
        direction TB
        ReplyProfile[👤 Профиль]:::process
        ReplyMenu[🏠 Меню]:::process
    end

    ReplyMenu --> MainMenu
    ReplyProfile --> ProfileScreen

    %% --- Main Menu ---
    MainMenu["🏠 Главное Меню<br>Выберите режим"]:::screen
    
    MainMenu -->|"🚀 Спринт"| SprintIntro
    MainMenu -->|"🏋️ Тренировка"| TrainingSetup
    MainMenu -->|"📚 Темы"| TopicList
    MainMenu -->|"❌ Мои ошибки"| MistakesMenu
    MainMenu -->|"👤 Профиль"| ProfileScreen

    %% --- 1. SPRINT MODE ---
    subgraph SprintFlow [US-002: Режим Спринт]
        direction TB
        SprintIntro["🏁 Описание Спринта<br>10-20 вопросов"]:::screen
        SprintIntro -->|"▶️ Поехали"| SprintInit
        SprintIntro -->|"🔙 Назад"| MainMenu

        SprintInit[Инициализация сессии]:::process
        SprintInit --> SprintQuestion
        SprintInit -.->|Create Session| RD
        SprintInit -.->|Fetch Questions| PG

        SprintQuestion{"❓ Вопрос N/20"}:::decision
        SprintQuestion -->|"Вариант ответа"| SprintCheck
        SprintQuestion -.->|Get Current State| RD
        
        SprintCheck{"Правильно?"}:::decision
        SprintCheck -->|"Да ✅"| SprintFeedback[Отлично!]:::process
        SprintCheck -->|"Нет ❌"| SprintError["Показать верный ответ<br>и решение"]:::process
        
        SprintFeedback --> SprintNextLogic
        SprintError --> SprintNextLogic
        
        SprintNextLogic{"Есть вопросы?"}:::decision
        SprintNextLogic -->|Да| SprintUpdate
        SprintNextLogic -->|Нет| SprintSave
        
        SprintUpdate[Обновить статус]:::process
        SprintUpdate --> SprintQuestion
        SprintUpdate -.->|Update State| RD

        SprintSave[Сохранить результат]:::process
        SprintSave --> SprintResult
        SprintSave -.->|Save Stats/History| PG
        SprintSave -.->|Clear Session| RD
        
        SprintResult["🏆 Результаты Спринта<br>Ваш счет: X/20"]:::screen
        SprintResult -->|"🏠 В меню"| MainMenu
        SprintResult -->|"🔄 Еще раз"| SprintIntro
    end

    %% --- 2. TRAINING MODE ---
    subgraph TrainingFlow [US-003: Режим Тренировка]
        direction TB
        TrainingSetup["⚙️ Настройка Тренировки<br>Выбор тем"]:::screen
        TrainingSetup -->|"✅ Выбрать Темы"| TrainingTopicSelect
        TrainingSetup -->|"▶️ Начать"| TrainingInit
        TrainingSetup -->|"🔙 Назад"| MainMenu

        TrainingTopicSelect["Список Тем (Чекбоксы)"]:::screen
        TrainingTopicSelect -->|Готово| TrainingSetup
        TrainingTopicSelect -.->|Fetch Topics| PG

        TrainingInit[Инициализация]:::process
        TrainingInit --> TrainingQuestion
        TrainingInit -.->|Create Endless Session| RD

        TrainingQuestion{"❓ Вопрос (Бесконечно)"}:::decision
        TrainingQuestion -->|"Вариант ответа"| TrainingCheck
        TrainingQuestion -.->|Get Adaptive Q| PG
        
        TrainingCheck{"Правильно?"}:::decision
        TrainingCheck -->|"Да ✅"| TrainingFeedback["Супер! Сложность ⬆️"]:::process
        TrainingCheck -->|"Нет ❌"| TrainingError["Разбор решения<br>Полное объяснение"]:::process
        
        TrainingFeedback --> TrainingNext[Следующий вопрос]:::process
        TrainingError --> TrainingNext
        
        TrainingNext --> TrainingQuestion
        TrainingNext -.->|Update Elo/State| PG
        
        TrainingQuestion -->|"🛑 Закончить"| TrainingSummary
        
        TrainingSummary[📊 Итоги сессии]:::screen
        TrainingSummary -->|"🏠 В меню"| MainMenu
    end

    %% --- 3. TOPICS & THEORY ---
    subgraph TopicsFlow [US-004: Каталог Тем]
        direction TB
        TopicList[📚 Список Тем]:::screen
        TopicList -->|Выбрать Тему| TopicCard
        TopicList -->|"🔙 Назад"| MainMenu
        TopicList -.->|Fetch Topics| PG

        TopicCard[📌 Карточка Темы]:::screen
        TopicCard -->|"📖 Теория"| TheoryView
        TopicCard -->|"📝 Решать задачи"| TaskList
        TopicCard -->|"🔙 Назад"| TopicList

        TheoryView[📄 Чтение Теории]:::screen
        TheoryView -->|"🔙 Назад"| TopicCard
        TheoryView -.->|Get Content| PG
        
        TaskList["📋 Список Задач (Сложность 1..N)"]:::screen
        TaskList -->|Выбрать задачу| TaskSolve
        TaskList -->|"🔙 Назад"| TopicCard
        TaskList -.->|Fetch Tasks| PG
        
        TaskSolve[✏️ Решение задачи]:::screen
        TaskSolve -->|Ответ| TaskFeedback
        TaskFeedback -->|"🔙 К списку"| TaskList
        TaskFeedback -->|Следующая| TaskSolve
        TaskFeedback -.->|Save Progress| PG
    end

    %% --- 4. MISTAKES ---
    subgraph MistakesFlow [US-006: Работа над ошибками]
        direction TB
        MistakesMenu["❌ Меню Ошибок<br>Всего: N"]:::screen
        MistakesMenu -->|"🎲 Все подряд"| MistakeSession
        MistakesMenu -->|"📂 По конкретной теме"| MistakeTopicSelect
        MistakesMenu -->|"🔙 Назад"| MainMenu
        MistakesMenu -.->|Count Mistakes| PG

        MistakeTopicSelect[Выбор Темы с ошибками]:::screen
        MistakeTopicSelect -->|Тема выбрана| MistakeSession
        MistakeTopicSelect -->|"🔙 Назад"| MistakesMenu

        MistakeSession{"❓ Вопрос (из ошибок)"}:::decision
        MistakeSession -->|Ответ| MistakeCheck
        MistakeSession -.->|Fetch Failed Task| PG

        MistakeCheck{"Исправил?"}:::decision
        MistakeCheck -->|"Да ✅"| MistakeFixed["Убрать из списка<br>+XP"]:::process
        MistakeCheck -->|"Нет ❌"| MistakeRetry["Показать решение<br>Оставить в списке"]:::process
        
        MistakeFixed --> MistakeNextLogic
        MistakeRetry --> MistakeNextLogic
        
        MistakeNextLogic{"Остались ошибки?"}:::decision
        MistakeNextLogic -->|Да| MistakeSession
        MistakeNextLogic -->|Нет| MistakeEmpty["🎉 Все исправлено!"]:::screen
        
        MistakeNextLogic -.->|Update Status| PG
        
        MistakeEmpty -->|"🏠 В меню"| MainMenu
    end

    %% --- 5. PROFILE ---
    subgraph ProfileFlow [US-007: Профиль]
        direction TB
        ProfileScreen["👤 Личный Кабинет<br>Статистика, Уровень, Streak"]:::screen
        ProfileScreen -->|"🔙 Назад"| MainMenu
        ProfileScreen -.->|Get User Stats| PG
    end

    %% --- 6. ADMIN PANEL ---
    subgraph AdminFlow [US-008, 009, 011: Админка]
        direction TB
        AdminMenu[🛠 Админ Панель]:::admin
        
        AdminMenu -->|"📚 Контент"| AdminContent
        AdminMenu -->|"👥 Пользователи"| AdminUsers
        AdminMenu -->|"📢 Рассылка"| AdminBroadcast
        AdminMenu -->|"🔙 Выход"| MainMenu

        AdminContent["Управление Темами/Задачами"]:::admin
        AdminContent -->|"➕ Добавить Тему"| AdminAddTopic
        AdminContent -->|"✏️ Редактировать"| AdminEditTopic
        AdminContent -->|"🔙 Назад"| AdminMenu
        
        AdminAddTopic[Ввод названия темы]:::admin
        AdminAddTopic -.->|INSERT Topic| PG
        
        AdminEditTopic[Список тем для ред.]:::admin
        AdminEditTopic -.->|UPDATE Topic| PG

        AdminUsers[Управление Юзерами]:::admin
        AdminUsers -->|"🔎 Поиск / Ban"| UserAction
        AdminUsers -->|"🔙 Назад"| AdminMenu
        
        UserAction[Действия с юзером]:::admin
        UserAction -.->|UPDATE User| PG

        AdminBroadcast[Создание Рассылки]:::admin
        AdminBroadcast -->|"📝 Ввод текста"| BroadcastPreview
        
        BroadcastPreview[Предпросмотр]:::admin
        BroadcastPreview -->|"✅ Отправить"| BroadcastDone
        BroadcastPreview -->|"🔙 Отмена"| AdminMenu
        
        BroadcastDone[Рассылка отправлена]:::admin
        BroadcastDone -.->|Save Log| PG
        BroadcastDone -.->|Queue Jobs| RD
    end