# Feature: File Attachments for Tasks and Theory

**Branch:** `feature/attachments`
**Created:** 2026-02-28
**Plan file:** `.ai-factory/plans/feature-attachments.md`

## Settings

| Setting  | Value   |
|----------|---------|
| Tests    | ✅ Yes  |
| Logging  | Verbose (DEBUG level throughout) |
| Docs     | ❌ No   |

## Scope

- **Задания (questions):** прикрепление нескольких фотографий
- **Теория (topics):** прикрепление нескольких фотографий + документов (PDF, DOCX, и др.)
- **Хранилище:** S3-совместимое (MinIO в Docker или AWS S3 в prod) через `aioboto3`
- **Таблица:** единая полиморфная таблица `attachments` с `entity_type` (`topic` / `question`) и `attachment_type` (`photo` / `document`)
- **Бот:** обновить хендлеры для отправки media group + документов пользователям
- **Админка:** UI-компонент загрузки файлов во всплывающих окнах тем и задач

## Architecture

```
Attachment (ORM)
  ├── entity_type: "topic" | "question"
  ├── entity_id: int (FK → topics.id или questions.id, без CASCADE через FK, удаление ручное)
  ├── attachment_type: "photo" | "document"
  ├── file_key: str (ключ в S3 bucket)
  ├── file_name: str (оригинальное имя файла)
  ├── file_size: int (байты)
  └── mime_type: str

StorageService (services/storage_service.py)
  ├── upload_file(bucket, key, data, content_type) → str (key)
  ├── delete_file(bucket, key) → bool
  └── get_presigned_url(bucket, key, expires=3600) → str

AttachmentRepository (repositories/attachment_repo.py)
  ├── get_for_entity(entity_type, entity_id) → list[Attachment]
  ├── create(entity_type, entity_id, type, key, name, size, mime) → Attachment
  └── delete(attachment_id) → bool

API: /api/attachments/
  POST /{entity_type}/{entity_id}/upload  — multipart, несколько файлов
  GET  /{entity_type}/{entity_id}         — список
  DELETE /{attachment_id}                 — удаление файла из S3 + DB
  GET  /{attachment_id}/url               — presigned URL для скачивания
```

---

## Tasks

### Phase 1 — Infrastructure & Storage

#### ✅ Task 1: Add aioboto3 dependency + S3 config

**Files:**
- `requirements.txt` — добавить `aioboto3>=12.0.0`, `aiosqlite>=0.20.0` (для тестов)
- `.env.example` — добавить `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_NAME`, `S3_PUBLIC_URL`
- `bot/config.py` — добавить S3-поля в Pydantic `Settings`
- `docker-compose.yml` — добавить сервис `minio` (image: `minio/minio:latest`), volume `minio_data`, healthcheck

**Logging:**
- `DEBUG [CONFIG] S3 endpoint={url} bucket={bucket}` при старте

**Details:**
MinIO будет запущен с переменными `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`.
Добавить `mc` (minio client) init container для создания bucket при первом запуске.

---

#### ✅ Task 2: Create StorageService

**Files:**
- `services/storage_service.py` (новый файл)

**API:**
```python
class StorageService:
    @staticmethod
    async def upload_file(file_key: str, data: bytes, content_type: str) -> str
    @staticmethod
    async def delete_file(file_key: str) -> bool
    @staticmethod
    async def get_presigned_url(file_key: str, expires: int = 3600) -> str
    @staticmethod
    def generate_key(entity_type: str, entity_id: int, filename: str) -> str
        # → f"{entity_type}/{entity_id}/{uuid4()}/{filename}"
```

**Logging:**
- `DEBUG [STORAGE] uploading key={key} size={size}B content_type={ct}`
- `INFO  [STORAGE] uploaded key={key}`
- `DEBUG [STORAGE] deleting key={key}`
- `INFO  [STORAGE] deleted key={key}`
- `ERROR [STORAGE] upload failed key={key}: {err}`

---

#### ✅ Task 3: DB Model + Alembic Migration

**Files:**
- `db/models.py` — добавить `Attachment` модель в конце файла
- Сгенерировать Alembic миграцию через `alembic revision --autogenerate -m "add_attachments"`

**Модель:**
```python
class Attachment(Base):
    __tablename__ = "attachments"

    id: int (PK, autoincrement)
    entity_type: str(16)      # "topic" | "question"
    entity_id: int            # ID темы или задачи (без FK constraint — полиморфизм)
    attachment_type: str(16)  # "photo" | "document"
    file_key: str(512)        # S3 ключ
    file_name: str(256)       # оригинальное имя
    file_size: int            # байты
    mime_type: str(128)
    created_at: datetime (server_default=now())
```

**Индексы:** составной индекс `(entity_type, entity_id)` для быстрой выборки.

**Logging:**
- `DEBUG [REPO:Attachment] created id={id} entity={entity_type}:{entity_id}`

---

#### ✅ Task 4: AttachmentRepository

**Files:**
- `repositories/attachment_repo.py` (новый файл)

**Methods:**
```python
class AttachmentRepository:
    get_for_entity(entity_type, entity_id, db) → list[Attachment]
    get_by_id(attachment_id, db) → Attachment | None
    create(entity_type, entity_id, attachment_type, file_key, file_name, file_size, mime_type, db) → Attachment
    delete(attachment_id, db) → Attachment | None  # возвращает объект для удаления из S3
    delete_all_for_entity(entity_type, entity_id, db) → list[str]  # возвращает list[file_key] для S3-удаления
```

**Logging:**
- `DEBUG [REPO:Attachment]` перед каждым запросом
- `INFO  [REPO:Attachment]` после успешного create/delete

---

### Phase 2 — API Endpoints

#### ✅ Task 5: Attachments FastAPI Router

**Files:**
- `webapp/routers/attachments.py` (новый файл)
- `webapp/schemas.py` — добавить `AttachmentResponse`
- `webapp/main.py` — зарегистрировать новый router

**Endpoints:**

```
POST /api/attachments/{entity_type}/{entity_id}/upload
    — multipart/form-data, поле files: List[UploadFile]
    — валидация entity_type ∈ {"topic", "question"}
    — для questions: разрешены только image/* (MIME)
    — для topics: разрешены image/* и document/* (pdf, docx, xlsx, ...)
    — загружает каждый файл в S3 через StorageService
    — создаёт запись в DB через AttachmentRepository
    — возвращает List[AttachmentResponse]

GET /api/attachments/{entity_type}/{entity_id}
    — возвращает List[AttachmentResponse] с presigned URLs

DELETE /api/attachments/{attachment_id}
    — удаляет из S3 + удаляет из DB
    — возвращает {"status": "deleted"}
```

**Валидация:**
- Максимальный размер файла: 20 МБ
- Допустимые MIME для фото: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- Допустимые MIME для документов: `application/pdf`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/plain`

**Logging:**
- `INFO  [WEBAPP:ATTACHMENTS] uploaded {N} files for {entity_type}:{entity_id} by admin={id}`
- `INFO  [WEBAPP:ATTACHMENTS] deleted attachment {id} file_key={key} by admin={id}`
- `ERROR [WEBAPP:ATTACHMENTS] upload failed: {err}`

**Schema:**
```python
class AttachmentResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    attachment_type: str
    file_name: str
    file_size: int
    mime_type: str
    url: str  # presigned URL
    created_at: str
```

---

#### ✅ Task 6: Cascade Deletion Integration

**Files:**
- `webapp/routers/topics.py` — в `delete_topic` вызвать `delete_all_for_entity("topic", topic_id)` и удалить из S3
- `webapp/routers/questions.py` — в `delete_question` вызвать `delete_all_for_entity("question", question_id)` и удалить из S3

**Logging:**
- `INFO  [WEBAPP] cascade deleted {N} attachments for deleted {entity_type}:{id}`

---

### Phase 3 — Admin WebApp UI

#### ✅ Task 7: Attachments UI Component (JS)

**Files:**
- `webapp/static/attachments.js` (новый файл) — переиспользуемый компонент

**Component API:**
```javascript
window.AttachmentsComponent = {
    render(entityType, entityId, allowedTypes),  // "photos" | "photos+docs"
    async load(entityType, entityId),
    async upload(entityType, entityId, inputEl),
    async delete(attachmentId, entityType, entityId),
}
```

**UX:**
- Drag-and-drop зона + кнопка "Выбрать файлы"
- Визуальные иконки: 🖼️ для фото, 📄 для документов
- Спиннер при загрузке
- Список загруженных файлов: имя + размер + кнопка удаления
- Для фото: превью `<img>` через presigned URL
- Сообщение об ошибке, если тип/размер не прошёл валидацию

---

#### ✅ Task 8: Integrate Component into Topics Modal

**Files:**
- `webapp/static/topics.js` — обновить `openModal()` и `save()`

**Changes:**
- В форме редактирования темы (только при `isEdit=true`) добавить секцию `AttachmentsComponent.render("topic", topic.id, "photos+docs")`
- После открытия модала вызвать `AttachmentsComponent.load("topic", topic.id)`
- Убрать поле "URL картинки" из UI (заменяется загрузчиком)
- При создании новой темы — секция вложений видна только после первого сохранения

---

#### ✅ Task 9: Integrate Component into Questions Modal

**Files:**
- `webapp/static/questions.js` — обновить `openModal()` и `save()`

**Changes:**
- В форме редактирования вопроса (только при `isEdit=true`) добавить секцию `AttachmentsComponent.render("question", q.id, "photos")`
- После открытия модала вызвать `AttachmentsComponent.load("question", q.id)`
- Убрать поле "URL картинки" из UI

---

#### ✅ Task 10: Load attachments.js in index.html

**Files:**
- `webapp/static/index.html` — добавить `<script src="/static/attachments.js">` перед `app.js`

---

### Phase 4 — Bot Integration

#### ✅ Task 11: Update topic_theory handler (send media group + documents)

**Files:**
- `bot/handlers/topics.py` — функция `topic_theory`

**Changes:**
1. Загрузить вложения через `AttachmentRepository.get_for_entity("topic", topic_id, db)`
2. Фотографии — отправить как `InputMediaPhoto` media group (Aiogram `answer_media_group`). Первое фото содержит caption с текстом теории.
3. Документы — отправить отдельными `answer_document()` после медиагруппы.
4. Если вложений нет — логика как прежде (только текст).
5. Если фото > 10 — отправлять несколькими группами (лимит Telegram).

**Logging:**
- `DEBUG [HANDLER:topics] sending theory topic={id}: photos={N} docs={M}`
- `INFO  [HANDLER:topics] theory sent with media group to user={uid}`
- `ERROR [HANDLER:topics] failed to send media group: {err}`

---

#### ✅ Task 12: Update solve_question + topic_next handlers (send photo attachments)

**Files:**
- `bot/handlers/topics.py` — функции `solve_question`, `topic_next`, `topic_answer`

**Changes:**
1. Загрузить вложения вопроса через `AttachmentRepository.get_for_entity("question", question_id, db)`
2. Если ≥2 фото — `answer_media_group`. Если 1 фото — `answer_photo` (для caption + reply_markup).
3. Если у вопроса media group, то feedback в `topic_answer` отправляется reply-сообщением, т.к. media group caption нельзя редактировать после ответа. Сохранять в Redis: `has_media_group: bool`.

**Logging:**
- `DEBUG [HANDLER:topics] question {id} has {N} photo attachments`
- `INFO  [HANDLER:topics] sent {N} photos for question {id} to user={uid}`

---

### Phase 5 — Tests

#### ✅ Task 13: Tests for Attachments API

**Files:**
- `tests/webapp/test_attachments.py` (новый файл)

**Test cases:**
```python
test_upload_photos_to_question           # POST upload 2x image/jpeg → 200, 2 записи в DB
test_upload_docs_to_topic                # POST upload PDF + DOCX → 200
test_upload_doc_to_question_fails        # POST upload PDF to question → 400
test_get_attachments_for_entity          # GET /api/attachments/question/{id} → список
test_delete_attachment                   # DELETE /api/attachments/{id} → 200
test_upload_oversized_file_fails         # >20MB → 400
test_invalid_entity_type                 # entity_type="foo" → 400
test_cascade_delete_on_topic_delete      # DELETE topic → attachments gone (mock S3)
```

**Mocking:**
- `StorageService.upload_file` и `delete_file` мокировать через `monkeypatch` / `pytest-mock`
- S3 реально не поднимается в тестах — возвращает фиктивный ключ

---

## Commit Plan

| Checkpoint | Tasks | Commit Message |
|------------|-------|----------------|
| ✅ Checkpoint 1 | 1–4 | `feat(storage): add S3 config, StorageService, Attachment model and repo` |
| ✅ Checkpoint 2 | 5–6 | `feat(api): add /api/attachments router with upload/list/delete` |
| ✅ Checkpoint 3 | 7–10 | `feat(webapp): add AttachmentsComponent UI, integrate into topics and questions modals` |
| ✅ Checkpoint 4 | 11–12 | `feat(bot): update topic theory and question handlers to send media groups` |
| ✅ Checkpoint 5 | 13 | `test(attachments): add API tests for attachments endpoints` |

---

## Key Decisions

1. **Полиморфная таблица без FK constraint** — `entity_id` не ссылается на конкретную таблицу через FOREIGN KEY. Каскадное удаление делается вручную в роутерах.
2. **S3 presigned URLs** — файлы не проксируются через FastAPI, ответ содержит временный presigned URL (1 час).
3. **MinIO в Docker** — в dev используется MinIO как S3-совместимое хранилище. В prod `.env` указывается реальный S3 endpoint.
4. **attachment_type по MIME** — проставляется сервером, не доверяя клиенту.
5. **Telegram media group лимит** — максимум 10 элементов. Если > 10 фото, шлём несколькими группами.
6. **Вложения только для существующих сущностей** — в create-форме секция вложений скрыта.
