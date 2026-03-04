/**
 * AttachmentsComponent — reusable file upload/display widget.
 *
 * Usage:
 *   AttachmentsComponent.render(containerId, entityType, entityId, mode)
 *   // mode: "photos" | "photos+docs"
 *
 *   After calling render(), the widget appears inside the given container.
 *   To load existing attachments: await AttachmentsComponent.load(containerId, entityType, entityId)
 */

window.AttachmentsComponent = (function () {
    const MAX_SIZE_MB = 20;
    const MAX_SIZE = MAX_SIZE_MB * 1024 * 1024;

    const PHOTO_MIMES = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp']);
    const DOC_MIMES = new Set([
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain'
    ]);

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function fileIcon(mimeType) {
        if (PHOTO_MIMES.has(mimeType)) return '🖼️';
        if (mimeType === 'application/pdf') return '📕';
        if (mimeType.includes('word')) return '📄';
        if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
        return '📄';
    }

    function acceptAttr(mode) {
        if (mode === 'photos') return 'image/jpeg,image/png,image/gif,image/webp';
        return 'image/jpeg,image/png,image/gif,image/webp,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/plain';
    }

    function getContainer(containerId) {
        return document.getElementById(containerId);
    }

    function getListEl(containerId) {
        return document.getElementById(containerId + '-list');
    }

    function setLoading(containerId, loading) {
        const spinner = document.getElementById(containerId + '-spinner');
        if (spinner) spinner.style.display = loading ? 'flex' : 'none';
    }

    function renderAttachment(att, containerId, entityType, entityId) {
        const isPhoto = att.attachment_type === 'photo';
        const icon = fileIcon(att.mime_type);

        return `
        <div class="att-item" id="att-item-${att.id}" style="
            display:flex; align-items:center; gap:12px;
            padding:10px 14px;
            background:rgba(255,255,255,0.03);
            border:1px solid var(--c-border-subtle);
            border-radius:var(--radius-sm);
            margin-bottom:8px;
            transition:background 0.2s;
        ">
            ${isPhoto && att.url
                ? `<img src="${att.url}" alt="${att.file_name}" style="width:48px; height:48px; object-fit:cover; border-radius:6px; flex-shrink:0; border:1px solid var(--c-border);">`
                : `<span style="font-size:28px; flex-shrink:0;">${icon}</span>`
            }
            <div style="flex-grow:1; min-width:0;">
                <div style="font-size:13px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${att.file_name}">
                    ${att.file_name}
                </div>
                <div style="font-size:11px; color:var(--c-text-muted); margin-top:2px;">
                    ${formatSize(att.file_size)} &bull; ${att.attachment_type === 'photo' ? 'Фото' : 'Документ'}
                </div>
            </div>
            <button class="btn-icon" title="Удалить" style="flex-shrink:0; color:var(--c-danger);"
                onclick="AttachmentsComponent._delete(${att.id}, '${containerId}', '${entityType}', ${entityId})">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>
                    <path d="M9 6V4h6v2"/>
                </svg>
            </button>
        </div>`;
    }

    return {
        /**
         * Render the upload widget into the given container element.
         * @param {string} containerId - ID of the DOM element to inject into
         * @param {string} entityType - "topic" | "question"
         * @param {number|null} entityId - null if new entity (upload hidden)
         * @param {string} mode - "photos" | "photos+docs"
         */
        render(containerId, entityType, entityId, mode = 'photos') {
            const container = getContainer(containerId);
            if (!container) return;

            const accept = acceptAttr(mode);
            const modeLabel = mode === 'photos' ? 'Фотографии' : 'Фотографии и документы';
            const showUpload = entityId != null;

            container.innerHTML = `
            <div style="margin-top:20px;">
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
                    <label style="font-size:13px; font-weight:600; color:var(--c-text); display:flex; align-items:center; gap:8px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
                            <polyline points="21 15 16 10 5 21"/>
                        </svg>
                        ${modeLabel}
                    </label>
                    ${showUpload ? `
                    <div style="position:relative; overflow:hidden; display:inline-block;">
                        <button class="btn btn-secondary" style="font-size:12px; padding:6px 12px;" type="button">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right:4px;">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                            </svg>
                            Загрузить
                        </button>
                        <input type="file" multiple accept="${accept}"
                            style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; cursor:pointer;"
                            onchange="AttachmentsComponent._upload(event, '${containerId}', '${entityType}', ${entityId}, '${mode}')">
                    </div>
                    ` : `<span class="badge secondary" style="font-size:11px;">Доступно после сохранения</span>`}
                </div>

                ${showUpload ? `
                <div id="${containerId}-drop" style="
                    border:2px dashed var(--c-border);
                    border-radius:var(--radius-sm);
                    padding:24px;
                    text-align:center;
                    color:var(--c-text-muted);
                    font-size:13px;
                    transition:border-color 0.2s, background 0.2s;
                    position:relative;
                    cursor:pointer;
                    margin-bottom:12px;
                "
                ondragover="AttachmentsComponent._dragOver(event, '${containerId}')"
                ondragleave="AttachmentsComponent._dragLeave(event, '${containerId}')"
                ondrop="AttachmentsComponent._drop(event, '${containerId}', '${entityType}', ${entityId}, '${mode}')">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:8px; opacity:0.4; display:block; margin:0 auto 8px;">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    Перетащите файлы сюда или используйте кнопку выше
                    <input type="file" multiple accept="${accept}"
                        style="position:absolute; inset:0; width:100%; height:100%; opacity:0; cursor:pointer;"
                        onchange="AttachmentsComponent._upload(event, '${containerId}', '${entityType}', ${entityId}, '${mode}')">
                </div>` : ''}

                <div id="${containerId}-spinner" style="display:none; justify-content:center; padding:16px;">
                    <div style="width:20px; height:20px; border:2px solid var(--c-border); border-top-color:var(--c-primary); border-radius:50%; animation:spin 0.8s linear infinite;"></div>
                </div>

                <div id="${containerId}-list"></div>
                <div id="${containerId}-error" style="color:var(--c-danger); font-size:12px; margin-top:6px;"></div>
            </div>
            `;

            if (showUpload && entityId) {
                this.load(containerId, entityType, entityId);
            }
        },

        async load(containerId, entityType, entityId) {
            if (!entityId) return;
            const listEl = getListEl(containerId);
            if (!listEl) return;

            setLoading(containerId, true);
            try {
                const attachments = await API.get(`/attachments/${entityType}/${entityId}`);
                listEl.innerHTML = '';
                if (attachments.length === 0) {
                    listEl.innerHTML = `<p style="font-size:12px; color:var(--c-text-muted); text-align:center; padding:8px 0;">Нет прикреплённых файлов</p>`;
                } else {
                    attachments.forEach(att => {
                        listEl.insertAdjacentHTML('beforeend', renderAttachment(att, containerId, entityType, entityId));
                    });
                }
            } catch (e) {
                console.error('[AttachmentsComponent] load error', e);
            } finally {
                setLoading(containerId, false);
            }
        },

        async _upload(event, containerId, entityType, entityId, mode) {
            const files = Array.from(event.target.files || []);
            event.target.value = '';
            if (!files.length) return;
            await this._processFiles(files, containerId, entityType, entityId, mode);
        },

        async _processFiles(files, containerId, entityType, entityId, mode) {
            const errorEl = document.getElementById(containerId + '-error');
            if (errorEl) errorEl.textContent = '';

            const allowedMimes = mode === 'photos'
                ? PHOTO_MIMES
                : new Set([...PHOTO_MIMES, ...DOC_MIMES]);

            const errors = [];

            for (const file of files) {
                if (file.size > MAX_SIZE) {
                    errors.push(`${file.name}: превышает ${MAX_SIZE_MB} МБ`);
                    continue;
                }
                if (!allowedMimes.has(file.type)) {
                    errors.push(`${file.name}: неподдерживаемый тип файла (${file.type})`);
                    continue;
                }
            }

            if (errors.length) {
                if (errorEl) errorEl.textContent = errors.join('; ');
                if (errors.length === files.length) return;
            }

            const validFiles = files.filter(f => f.size <= MAX_SIZE && allowedMimes.has(f.type));
            if (!validFiles.length) return;

            setLoading(containerId, true);
            const formData = new FormData();
            validFiles.forEach(f => formData.append('files', f));

            try {
                // Use XMLHttpRequest for multipart upload (API.upload helper)
                const newAttachments = await API.upload(`/attachments/${entityType}/${entityId}/upload`, formData);
                const listEl = getListEl(containerId);
                if (listEl) {
                    // Remove "no files" placeholder
                    const placeholder = listEl.querySelector('p');
                    if (placeholder) placeholder.remove();

                    newAttachments.forEach(att => {
                        listEl.insertAdjacentHTML('beforeend', renderAttachment(att, containerId, entityType, entityId));
                    });
                }
                ui.toast(`Загружено файлов: ${newAttachments.length}`, 'success');
            } catch (e) {
                ui.toast('Ошибка загрузки файлов', 'error');
                console.error('[AttachmentsComponent] upload error', e);
            } finally {
                setLoading(containerId, false);
            }
        },

        async _delete(attachmentId, containerId, entityType, entityId) {
            if (!confirm('Удалить вложение?')) return;
            try {
                await API.delete(`/attachments/${attachmentId}`);
                const item = document.getElementById(`att-item-${attachmentId}`);
                if (item) item.remove();

                const listEl = getListEl(containerId);
                if (listEl && !listEl.querySelector('.att-item')) {
                    listEl.innerHTML = `<p style="font-size:12px; color:var(--c-text-muted); text-align:center; padding:8px 0;">Нет прикреплённых файлов</p>`;
                }

                ui.toast('Вложение удалено', 'success');
            } catch (e) {
                ui.toast('Ошибка удаления', 'error');
            }
        },

        _dragOver(event, containerId) {
            event.preventDefault();
            const drop = document.getElementById(containerId + '-drop');
            if (drop) {
                drop.style.borderColor = 'var(--c-primary)';
                drop.style.background = 'rgba(139,92,246,0.06)';
            }
        },

        _dragLeave(event, containerId) {
            const drop = document.getElementById(containerId + '-drop');
            if (drop) {
                drop.style.borderColor = 'var(--c-border)';
                drop.style.background = '';
            }
        },

        _drop(event, containerId, entityType, entityId, mode) {
            event.preventDefault();
            this._dragLeave(event, containerId);
            const files = Array.from(event.dataTransfer.files || []);
            if (files.length) {
                this._processFiles(files, containerId, entityType, entityId, mode);
            }
        }
    };
})();
