// Основной модуль приложения
class ScheduleApp {
    constructor() {
        this.currentLesson = null;
        this.currentSlot = null; // Добавлено для пустых ячеек
        this.teachers = [];
        this.subjects = [];
        this.lessons = [];
        this.savedSchedules = [];
        this.filters = [];
        this.groups = [];
        this.currentGroupId = 1; // По умолчанию основная группа
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupThemeToggle();

        // Загружаем сохраненную группу
        const savedGroup = localStorage.getItem('currentGroup');
        if (savedGroup) {
            this.currentGroupId = parseInt(savedGroup);
        }

        await this.loadInitialData();
        this.renderSchedule();
        await this.refreshAllData();
        await this.updateStatistics();
    }

    setupEventListeners() {
        // Sidebar toggle
        document.getElementById('sidebarToggle').addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('active');
        });

        // Section headers
        document.querySelectorAll('.nav-section-header').forEach(header => {
            header.addEventListener('click', () => {
                const section = header.parentElement;
                section.classList.toggle('active');
            });
        });

        // Forms
        document.getElementById('addTeacherForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTeacher();
        });

        document.getElementById('addSubjectForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addSubject();
        });

        document.getElementById('addFilterForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addNegativeFilter();
        });

        document.getElementById('saveScheduleForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSchedule();
        });

        // Buttons
        document.getElementById('generateSchedule').addEventListener('click', () => {
            this.generateSchedule();
        });

        document.getElementById('fullGenerate').addEventListener('click', () => {
            app.generateSchedule();  // Теперь это будет использовать квоты если они заданы
        });

        document.getElementById('clearAll').addEventListener('click', () => {
            this.clearAllData();
        });

        // Context menu
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            const cell = e.target.closest('.schedule-cell');
            if (cell) {
                const hasLesson = cell.querySelector('.lesson-card');
                if (hasLesson) {
                    this.showLessonContextMenu(e, cell);
                } else {
                    this.showEmptyCellContextMenu(e, cell);
                }
            }
        });

        document.addEventListener('click', () => {
            this.hideContextMenu();
        });

        // Modal events
        this.setupModalEvents();

        // Group selector
        document.getElementById('groupSelector').addEventListener('change', (e) => {
            this.switchGroup(e.target.value);
        });
    }

    setupModalEvents() {
        const replaceModal = document.getElementById('replaceModal');
        const closeBtn = replaceModal.querySelector('.close');
        const cancelBtn = document.getElementById('cancelReplace');
        const confirmBtn = document.getElementById('confirmReplace');

        [closeBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => {
                replaceModal.style.display = 'none';
                this.resetReplaceModal();
            });
        });

        // Confirm button будет менять свою функцию динамически
        // Инициализация будет в showAddLessonModal

        // Close modal on outside click
        replaceModal.addEventListener('click', (e) => {
            if (e.target === replaceModal) {
                replaceModal.style.display = 'none';
                this.resetReplaceModal();
            }
        });
    }

    resetReplaceModal() {
        const form = document.getElementById('replaceForm');
        form.reset();
        document.getElementById('selectedSubjectInfo').style.display = 'none';
        this.currentLesson = null;
        this.currentSlot = null;
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        // Устанавливаем начальную тему
        if (prefersDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }

        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            if (currentTheme === 'dark') {
                document.documentElement.removeAttribute('data-theme');
                themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                localStorage.setItem('theme', 'dark');
            }
        });

        // Загружаем сохраненную тему
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadGroups(),
                this.loadTeachers(),
                this.loadSubjects(),
                this.loadLessons(),
                this.loadSavedSchedules(),
                this.loadFilters()
            ]);
        } catch (error) {
            console.error('⚠️ Предупреждение при загрузке данных:', error.message);
            this.showError('Ошибка загрузки данных: ' + error.message);
        }
    }

    // ========== ГРУППЫ ==========
    async loadGroups() {
        try {
            const response = await fetch('/api/groups');
            if (response.ok) {
                this.groups = await response.json();
                this.renderGroupSelector();
            }
        } catch (error) {
            console.error('Error loading groups:', error);
        }
    }

    renderGroupSelector() {
        const selector = document.getElementById('groupSelector');
        if (!this.groups || this.groups.length === 0) {
            selector.innerHTML = '<option value="">Нет групп</option>';
            return;
        }

        selector.innerHTML = this.groups.map(group =>
            `<option value="${group.id}" ${group.id == this.currentGroupId ? 'selected' : ''}>${group.name}</option>`
        ).join('');
    }

    async switchGroup(newGroupId) {
        if (!newGroupId || newGroupId == this.currentGroupId) return;

        this.showLoading();

        try {
            // Проверяем существование группы
            const response = await fetch(`/api/groups/${newGroupId}/exists`);
            const result = await response.json();

            if (result.exists) {
                this.currentGroupId = parseInt(newGroupId);
                localStorage.setItem('currentGroup', this.currentGroupId);

                // Перезагружаем все данные для новой группы
                await this.refreshAllData();
                this.showSuccess(`Переключено на группу: ${this.getCurrentGroupName()}`);
            } else {
                this.showError('Группа не найдена');
                await this.loadGroups(); // Перезагружаем список групп
            }
        } catch (error) {
            this.showError('Ошибка переключения группы: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    getCurrentGroupName() {
        const group = this.groups.find(g => g.id == this.currentGroupId);
        return group ? group.name : 'Неизвестная группа';
    }

    // Модалки для групп
    createGroup() {
        document.getElementById('createGroupModal').style.display = 'block';
        document.getElementById('newGroupName').value = '';
        document.getElementById('newGroupName').focus();
    }

    closeCreateGroupModal() {
        document.getElementById('createGroupModal').style.display = 'none';
    }

    async confirmCreateGroup() {
        const name = document.getElementById('newGroupName').value.trim();
        if (!name) {
            this.showError('Введите название группы');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/api/groups', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name })
            });

            if (response.ok) {
                const newGroup = await response.json();
                this.closeCreateGroupModal();
                this.showSuccess(`Группа "${name}" создана`);

                // Перезагружаем список групп и переключаемся на новую
                await this.loadGroups();
                await this.switchGroup(newGroup.id);
            } else {
                const result = await response.json();
                throw new Error(result.detail || 'Ошибка создания группы');
            }
        } catch (error) {
            this.showError('Ошибка создания группы: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    renameGroup() {
        if (this.currentGroupId === 1) {
            this.showError('Нельзя переименовать основную группу');
            return;
        }

        const currentGroup = this.groups.find(g => g.id == this.currentGroupId);
        if (!currentGroup) return;

        document.getElementById('renameGroupModal').style.display = 'block';
        document.getElementById('renameGroupName').value = currentGroup.name;
        document.getElementById('renameGroupName').focus();
    }

    closeRenameGroupModal() {
        document.getElementById('renameGroupModal').style.display = 'none';
    }

    async confirmRenameGroup() {
        const newName = document.getElementById('renameGroupName').value.trim();
        if (!newName) {
            this.showError('Введите новое название группы');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/api/groups/${this.currentGroupId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newName })
            });

            if (response.ok) {
                const updatedGroup = await response.json();
                this.closeRenameGroupModal();
                this.showSuccess(`Группа переименована в "${newName}"`);

                // Перезагружаем список групп
                await this.loadGroups();
            } else {
                const result = await response.json();
                throw new Error(result.detail || 'Ошибка переименования группы');
            }
        } catch (error) {
            this.showError('Ошибка переименования группы: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async deleteCurrentGroup() {
    if (this.currentGroupId === 1) {
        this.showError('Нельзя удалить основную группу');
        return;
    }

    const groupName = this.getCurrentGroupName();
    if (!confirm(`ВНИМАНИЕ! Удалить группу "${groupName}" и ВСЕ её данные (предметы, расписание, сохраненные расписания)?`)) return;

    this.showLoading();

    try {
        console.log(`🗑️ Удаление группы ${this.currentGroupId}: "${groupName}"`);

        const response = await fetch(`/api/groups/${this.currentGroupId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const result = await response.json();
            this.showSuccess(`Группа "${groupName}" удалена`);

            // Переключаемся на основную группу
            this.currentGroupId = 1;
            localStorage.setItem('currentGroup', 1);

            // ПЕРЕЗАГРУЖАЕМ ВСЕ ДАННЫЕ
            await this.loadGroups(); // ОБЯЗАТЕЛЬНО сначала группы
            await this.refreshAllData(); // Потом все остальное

            // Убедимся, что группа удалилась из списка
            console.log(`✅ Переключено на группу 1, обновляем интерфейс`);

        } else {
            const result = await response.json();
            throw new Error(result.detail || result.error || 'Ошибка удаления группы');
        }
    } catch (error) {
        console.error('❌ Ошибка удаления группы:', error);
        this.showError('Ошибка удаления группы: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

    // ========== ПРЕПОДАВАТЕЛИ (ГЛОБАЛЬНЫЕ) ==========
    async loadTeachers() {
        try {
            // Преподаватели глобальные - не зависит от группы
            const response = await fetch('/api/teachers');
            if (response.ok) {
                this.teachers = await response.json();
                this.populateTeacherSelects();
                this.renderTeachersList();
            }
        } catch (error) {
            console.error('Error loading teachers:', error);
        }
    }

    populateTeacherSelects() {
        const selects = document.querySelectorAll('select[name="teacher"], #teacherSelect, #filterTeacherSelect, #replaceTeacherSelect');
        selects.forEach(select => {
            select.innerHTML = '<option value="">Выберите преподавателя</option>';
            this.teachers.forEach(teacher => {
                const option = document.createElement('option');
                option.value = teacher.name;
                option.textContent = teacher.name;
                select.appendChild(option);
            });
        });
    }

    renderTeachersList() {
        const container = document.getElementById('teachersList');
        if (!this.teachers || this.teachers.length === 0) {
            container.innerHTML = '<div class="empty-state">Нет преподавателей</div>';
            return;
        }

        container.innerHTML = this.teachers.map(teacher => `
            <div class="teacher-item" data-id="${teacher.id}">
                <div class="teacher-info">
                    <strong>${teacher.name}</strong>
                    <div class="teacher-meta">ID: ${teacher.id}</div>
                </div>
                <button class="btn-danger btn-small" onclick="app.deleteTeacher(${teacher.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    async addTeacher() {
        const form = document.getElementById('addTeacherForm');
        const formData = new FormData(form);
        const name = formData.get('name');

        try {
            const response = await fetch('/api/teachers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name })
            });

            if (response.ok) {
                this.showSuccess('Преподаватель добавлен (глобально)');
                form.reset();
                await this.loadTeachers();
                await this.updateStatistics();
            } else {
                throw new Error(await response.text());
            }
        } catch (error) {
            this.showError('Ошибка добавления преподавателя: ' + error.message);
        }
    }

    async deleteTeacher(teacherId) {
        if (!confirm('Удалить этого преподавателя ИЗ ВСЕХ ГРУПП?')) return;

        this.showLoading();

        try {
            const response = await fetch(`/api/teachers/${teacherId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Преподаватель удален из всех групп');
                await this.loadTeachers();
                await this.loadSubjects(); // Перезагружаем предметы т.к. они связаны
                await this.updateStatistics();
            } else {
                const result = await response.json();
                throw new Error(result.detail || result.error || 'Ошибка удаления преподавателя');
            }
        } catch (error) {
            this.showError('Ошибка удаления преподавателя: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // ========== ПРЕДМЕТЫ (ЛОКАЛЬНЫЕ ДЛЯ ГРУППЫ) ==========
    async loadSubjects() {
        try {
            console.log(`📚 Загрузка предметов для группы ${this.currentGroupId}`);

            const response = await fetch(`/api/subjects?group_id=${this.currentGroupId}`);

            console.log(`📥 Ответ сервера: ${response.status} ${response.statusText}`);

            // ПРОМЕЖУТОЧНАЯ ОТЛАДКА
            const responseClone = response.clone(); // Клонируем ответ
            const text = await responseClone.text();
            console.log(`📥 Сырой ответ (первые 500 символов): ${text.substring(0, 500)}`);

            if (text.startsWith('<!DOCTYPE') || text.startsWith('<html')) {
                console.error('❌ Сервер вернул HTML вместо JSON!');
                throw new Error('Сервер вернул HTML страницу');
            }

            // Пробуем парсить
            this.subjects = JSON.parse(text);
            console.log(`✅ Загружено предметов: ${this.subjects.length}`);
            console.log('📊 Пример предмета:', this.subjects[0]);

            this.renderSubjectsList();

        } catch (error) {
            console.error('❌ Ошибка загрузки предметов:', error);
            this.showError('Ошибка загрузки предметов: ' + error.message);
            this.subjects = [];
            this.renderSubjectsList();
        }
    }

    renderSubjectsList() {
        const container = document.getElementById('subjectsList');

        if (!this.subjects || this.subjects.length === 0) {
            container.innerHTML = '<div class="empty-state">Нет добавленных предметов</div>';
            return;
        }

        console.log(`📊 Рендеринг ${this.subjects.length} предметов`);

        container.innerHTML = this.subjects.map(subject => {
            // Проверяем что все поля существуют
            const subjectName = subject.subject_name || 'Без названия';
            const teacherName = subject.teacher || 'Без преподавателя';
            const totalHours = subject.total_hours || 0;
            const remainingHours = subject.remaining_hours || 0;
            const consumedHours = totalHours - remainingHours;
            const progressPercent = totalHours > 0 ? (consumedHours / totalHours) * 100 : 0;

            const remainingPairs = subject.remaining_pairs || 0;
            const minPerWeek = subject.min_per_week || 0;
            const maxPerWeek = subject.max_per_week || 20;
            const maxPerDay = subject.max_per_day || 2;
            const priority = subject.priority || 0;

            // Отображаем квоты
            let quotaInfo = '';
            if (minPerWeek > 0) {
                quotaInfo = `📅 ${minPerWeek}-${maxPerWeek} пар/нед`;
            } else if (maxPerWeek < 20) {
                quotaInfo = `📅 до ${maxPerWeek} пар/нед`;
            } else {
                quotaInfo = `📅 без ограничений`;
            }

            return `
                <div class="subject-item" data-id="${subject.id}">
                    <div class="subject-info">
                        <strong>${subjectName}</strong>
                        <div class="teacher-name">${teacherName}</div>
                        <div class="hours-info">
                            <div class="hours-progress">
                                ${consumedHours} / ${totalHours} часов
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${progressPercent}%"></div>
                            </div>
                            <div class="pairs-info">
                                ${remainingPairs} пар осталось • 
                                ${quotaInfo} • 
                                ${maxPerDay} пар/день
                            </div>
                        </div>
                    </div>
                    <div class="subject-actions">
                        <div class="priority-badge">Приоритет: ${priority}</div>
                        <button class="btn-danger btn-small" onclick="app.deleteSubject(${subject.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    async addSubject() {
        const form = document.getElementById('addSubjectForm');
        const formData = new FormData(form);

        const data = {
            teacher: formData.get('teacher'),
            subject_name: formData.get('subject_name'),
            hours: parseInt(formData.get('hours')),
            priority: parseInt(formData.get('priority')) || 0,
            max_per_day: parseInt(formData.get('max_per_day')) || 2,
            min_per_week: parseInt(formData.get('min_per_week')) || 0,
            max_per_week: parseInt(formData.get('max_per_week')) || 20
        };

        // Валидация
        if (!data.teacher || !data.subject_name || !data.hours) {
            this.showError('Заполните все обязательные поля');
            return;
        }

        if (data.hours < 2 || data.hours % 2 !== 0) {
            this.showError('Часы должны быть положительным числом, кратным 2');
            return;
        }

        if (data.min_per_week > data.max_per_week) {
            this.showError('Минимум не может быть больше максимума');
            return;
        }

        if (data.max_per_day > 4) {
            this.showError('Максимум пар в день не может быть больше 4');
            return;
        }

        if (data.max_per_week > 20) {
            this.showError('Максимум пар в неделю не может быть больше 20');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/api/subjects?group_id=${this.currentGroupId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Предмет добавлен в группу ' + this.getCurrentGroupName());
                form.reset();
                await this.loadSubjects();
                await this.updateStatistics();
            } else {
                if (response.status === 409) {
                    this.showError('Предмет с таким названием уже существует у этого преподавателя в этой группе');
                } else if (response.status === 400) {
                    this.showError(result.error || 'Ошибка добавления предмета');
                } else {
                    throw new Error(result.detail || 'Ошибка добавления предмета');
                }
            }
        } catch (error) {
            this.showError('Ошибка добавления предмета: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async deleteSubject(subjectId) {
        if (!confirm('Удалить этот предмет из группы ' + this.getCurrentGroupName() + '?')) return;

        this.showLoading();

        try {
            const response = await fetch(`/api/subjects/${subjectId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Предмет удален из группы');
                await this.loadSubjects();
                await this.updateStatistics();
            } else {
                const result = await response.json();
                throw new Error(result.detail || result.error || 'Ошибка удаления предмета');
            }
        } catch (error) {
            this.showError('Ошибка удаления предмета: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // ========== РАСПИСАНИЕ ==========
    async loadLessons() {
        try {
            const response = await fetch(`/api/lessons?group_id=${this.currentGroupId}`);
            if (response.ok) {
                this.lessons = await response.json();
                this.renderSchedule();
            }
        } catch (error) {
            console.error('Error loading lessons:', error);
        }
    }

    renderSchedule() {
    const scheduleGrid = document.getElementById('scheduleGrid');
    const weekDays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];
    const timeSlots = [
        { start: '9:00', end: '10:30' },
        { start: '10:40', end: '12:10' },
        { start: '12:40', end: '14:10' },
        { start: '14:20', end: '15:50' }
    ];

    let html = '';

    // Header row - ТОЛЬКО полные названия дней
    html += '<div class="schedule-header"></div>';
    weekDays.forEach((day, index) => {
        const isWeekend = index >= 5;
        html += `<div class="schedule-header ${isWeekend ? 'weekend' : ''}">${day}</div>`;
    });

    // Time slots and lessons
    timeSlots.forEach((slot, slotIndex) => {
        html += `<div class="time-slot">${slot.start}<br>${slot.end}<div class="time-slot-number">${slotIndex + 1}</div></div>`;

        for (let day = 0; day < 7; day++) {
            const lesson = this.lessons.find(l => l.day === day && l.time_slot === slotIndex);
            const isWeekend = day >= 5;

            html += `<div class="schedule-cell ${isWeekend ? 'weekend' : ''}" data-day="${day}" data-slot="${slotIndex}">`;

            if (lesson) {
                html += `
                    <div class="lesson-card">
                        <div class="lesson-content">
                            <strong>${lesson.subject_name}</strong>
                            <div class="lesson-teacher">${lesson.teacher}</div>
                        </div>
                    </div>
                `;
            } else {
                html += `<div class="empty-slot"><i class="fas fa-plus"></i><span>Свободно</span></div>`;
            }

            html += '</div>';
        }
    });

    scheduleGrid.innerHTML = html;

    // ВАЖНО: Добавляем обработчик ПКМ на ВСЕ ячейки (и занятые, и свободные)
    scheduleGrid.querySelectorAll('.schedule-cell').forEach(cell => {
        cell.addEventListener('contextmenu', (e) => {
            e.preventDefault(); // Отменяем стандартное меню

            const day = parseInt(cell.dataset.day);
            const timeSlot = parseInt(cell.dataset.slot);
            const hasLesson = cell.querySelector('.lesson-card');

            console.log(`🖱️ ПКМ на ячейке: день=${day}, слот=${timeSlot}, есть урок=${hasLesson ? 'да' : 'нет'}`);

            if (hasLesson) {
                // ЗАНЯТАЯ ячейка - удаление/замена
                this.currentLesson = { day, timeSlot };
                this.currentSlot = { day, timeSlot };
                this.showOccupiedContextMenu(e, cell);
            } else {
                // СВОБОДНАЯ ячейка - добавление
                this.currentLesson = null;
                this.currentSlot = { day, timeSlot };
                this.showEmptyContextMenu(e, cell);
            }
        });

        // Левая кнопка мыши - для совместимости
        cell.addEventListener('click', (e) => {
            if (e.target.closest('.lesson-card')) {
                console.log('Левая кнопка на занятой ячейке');
                // Можно добавить что-то если нужно
            }
        });
    });
}

showEmptyContextMenu(e, cell) {
    const contextMenu = document.getElementById('contextMenu');

    contextMenu.innerHTML = `
        <div class="context-item" data-action="add_lesson">
            <i class="fas fa-plus"></i> Добавить пару
        </div>
    `;

    contextMenu.style.display = 'block';
    contextMenu.style.left = e.pageX + 'px';
    contextMenu.style.top = e.pageY + 'px';

    // Обработчики для свободной ячейки
    contextMenu.querySelectorAll('.context-item').forEach(item => {
        item.onclick = () => {
            const action = item.dataset.action;
            this.handleEmptyContextAction(action);
            this.hideContextMenu();
        };
    });
}


handleOccupiedContextAction(action) {
    switch (action) {
        case 'delete':
            this.deleteLesson();
            break;
        case 'replace':
            this.showReplaceModal();
            break;
    }
}

// ========== ОБРАБОТЧИКИ ДЕЙСТВИЙ ДЛЯ СВОБОДНЫХ ЯЧЕЕК ==========

handleEmptyContextAction(action) {
    switch (action) {
        case 'add_lesson':
            this.showAddLessonModal();
            break;
    }
}

// ========== НОВЫЕ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
async checkTeacherAvailability() {
    if (!this.currentLesson) return;

    // Получаем информацию о текущем уроке
    const lesson = this.lessons.find(l =>
        l.day === this.currentLesson.day &&
        l.time_slot === this.currentLesson.timeSlot
    );

    if (!lesson) {
        this.showError('Не удалось найти информацию об уроке');
        return;
    }

    this.showLoading();

    try {
        const response = await fetch(`/api/manual/check-availability?teacher=${encodeURIComponent(lesson.teacher)}&day=${this.currentLesson.day}&time_slot=${this.currentLesson.timeSlot}&group_id=${this.currentGroupId}`);

        if (response.ok) {
            const result = await response.json();
            if (result.available) {
                this.showSuccess(`Преподаватель ${lesson.teacher} доступен в это время`);
            } else {
                this.showError(`Преподаватель ${lesson.teacher} НЕ доступен: ${result.message}`);
            }
        } else {
            const errorText = await response.text();
            throw new Error(errorText);
        }
    } catch (error) {
        this.showError('Ошибка проверки: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

async checkSlotAvailability() {
    if (!this.currentSlot) return;

    this.showLoading();

    try {
        const response = await fetch(`/api/lessons/check-slot?day=${this.currentSlot.day}&time_slot=${this.currentSlot.timeSlot}&group_id=${this.currentGroupId}`);

        if (response.ok) {
            const result = await response.json();
            if (result.available) {
                this.showSuccess(`Слот свободен. Можно добавить пару.`);
            } else {
                this.showError(`Слот занят в текущей группе.`);
            }
        } else {
            const errorText = await response.text();
            throw new Error(errorText);
        }
    } catch (error) {
        this.showError('Ошибка проверки: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

showOccupiedContextMenu(e, cell) {
    const contextMenu = document.getElementById('contextMenu');

    contextMenu.innerHTML = `
        <div class="context-item" data-action="delete">
            <i class="fas fa-trash"></i> Удалить пару
        </div>
        <div class="context-item" data-action="replace">
            <i class="fas fa-exchange-alt"></i> Заменить предмет
        </div>
    `;

    contextMenu.style.display = 'block';
    contextMenu.style.left = e.pageX + 'px';
    contextMenu.style.top = e.pageY + 'px';

    // Обработчики для занятой ячейки
    contextMenu.querySelectorAll('.context-item').forEach(item => {
        item.onclick = () => {
            const action = item.dataset.action;
            this.handleOccupiedContextAction(action);
            this.hideContextMenu();
        };
    });
}

    async generateSchedule() {
        this.showLoading();

        try {
            console.log(`⚡ Генерация расписания для группы ${this.currentGroupId}`);

            const response = await fetch(`/api/schedule/generate?group_id=${this.currentGroupId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showSuccess(`Сгенерировано ${result.lessons.length} пар для группы ${this.getCurrentGroupName()}`);
                await this.refreshAllData();
            } else {
                throw new Error(result.detail || 'Ошибка генерации');
            }
        } catch (error) {
            console.error('❌ Ошибка генерации:', error);
            this.showError('Ошибка генерации: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // ========== ФИЛЬТРЫ ==========
    async loadFilters() {
        try {
            const response = await fetch(`/api/negative-filters?group_id=${this.currentGroupId}`);
            if (response.ok) {
                this.filters = await response.json();
                this.renderFiltersList();
            }
        } catch (error) {
            console.error('Error loading filters:', error);
        }
    }

    renderFiltersList() {
        const container = document.getElementById('filtersList');

        if (!this.filters || Object.keys(this.filters).length === 0) {
            container.innerHTML = '<div class="empty-state">Нет сохраненных ограничений</div>';
            return;
        }

        container.innerHTML = Object.entries(this.filters).map(([teacher, filter]) => {
            const daysMap = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт'};
            const daysText = filter.restricted_days && filter.restricted_days.length > 0
                ? filter.restricted_days.map(d => daysMap[d] || d).join(', ')
                : 'нет';

            const slotsText = filter.restricted_slots && filter.restricted_slots.length > 0
                ? filter.restricted_slots.map(s => parseInt(s) + 1).join(', ')
                : 'нет';

            return `
                <div class="filter-item">
                    <div class="filter-info">
                        <strong>${teacher}</strong>
                        <div class="filter-details">
                            <div><i class="fas fa-calendar-times"></i> Запрещенные дни: ${daysText}</div>
                            <div><i class="fas fa-clock"></i> Запрещенные пары: ${slotsText}</div>
                        </div>
                    </div>
                    <button class="btn-danger btn-small" onclick="app.deleteFilter('${teacher}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');
    }

    async addNegativeFilter() {
        const form = document.getElementById('addFilterForm');
        const formData = new FormData(form);

        // Собираем выбранные дни и слоты
        const restrictedDays = [];
        const restrictedSlots = [];

        // Собираем дни
        const dayCheckboxes = form.querySelectorAll('input[name="restricted_days"]:checked');
        dayCheckboxes.forEach(checkbox => {
            restrictedDays.push(parseInt(checkbox.value));
        });

        // Собираем слоты
        const slotCheckboxes = form.querySelectorAll('input[name="restricted_slots"]:checked');
        slotCheckboxes.forEach(checkbox => {
            restrictedSlots.push(parseInt(checkbox.value));
        });

        const data = {
            teacher: formData.get('teacher'),
            restricted_days: restrictedDays,
            restricted_slots: restrictedSlots
        };

        // Валидация
        if (!data.teacher) {
            this.showError('Выберите преподавателя');
            return;
        }

        if (restrictedDays.length === 0 && restrictedSlots.length === 0) {
            this.showError('Выберите хотя бы один день или пару для ограничения');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/api/negative-filters?group_id=${this.currentGroupId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.showSuccess('Ограничения сохранены для группы ' + this.getCurrentGroupName());
                form.reset();
                await this.loadFilters();

                // Автоматически раскрываем секцию ограничений
                const filtersSection = document.querySelector('[data-section="filters"]').parentElement;
                filtersSection.classList.add('active');

            } else {
                const result = await response.json();
                throw new Error(result.detail || 'Ошибка сохранения ограничений');
            }
        } catch (error) {
            this.showError('Ошибка сохранения ограничений: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async deleteFilter(teacher) {
        if (!confirm(`Удалить ограничения для ${teacher} в группе ${this.getCurrentGroupName()}?`)) return;

        try {
            const response = await fetch(`/api/negative-filters/${encodeURIComponent(teacher)}?group_id=${this.currentGroupId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Ограничения удалены');
                await this.loadFilters();
            } else {
                const result = await response.json();
                throw new Error(result.detail || 'Ошибка удаления ограничений');
            }
        } catch (error) {
            this.showError('Ошибка удаления ограничений: ' + error.message);
        }
    }

    // ========== СОХРАНЕННЫЕ РАСПИСАНИЯ ==========
    async loadSavedSchedules() {
        try {
            const response = await fetch(`/api/schedules?group_id=${this.currentGroupId}`);
            if (response.ok) {
                this.savedSchedules = await response.json();
                this.renderSavedSchedulesList();
            }
        } catch (error) {
            console.error('Error loading saved schedules:', error);
        }
    }

    renderSavedSchedulesList() {
        const container = document.getElementById('savedSchedulesList');
        if (!this.savedSchedules.length) {
            container.innerHTML = '<div class="empty-state">Нет сохраненных расписаний</div>';
            return;
        }

        container.innerHTML = this.savedSchedules.map(schedule => `
            <div class="saved-schedule-item" data-id="${schedule.id}">
                <div class="schedule-info">
                    <strong>${schedule.name}</strong>
                    <div class="schedule-meta">
                        ${new Date(schedule.created_at).toLocaleDateString()} • 
                        ${schedule.lesson_count} пар
                    </div>
                </div>
                <div class="schedule-actions">
                    <button class="btn-primary btn-small" onclick="app.exportSchedule(${schedule.id}, '${schedule.name.replace(/'/g, "\\'")}')" 
                            title="Скачать в Excel">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn-danger btn-small" onclick="app.deleteSavedSchedule(${schedule.id})" title="Удалить">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    async saveSchedule() {
        const form = document.getElementById('saveScheduleForm');
        const formData = new FormData(form);
        const name = formData.get('name');

        if (!name) {
            this.showError('Введите название расписания');
            return;
        }

        try {
            const response = await fetch(`/api/schedules/save?group_id=${this.currentGroupId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    lessons: this.lessons
                })
            });

            if (response.ok) {
                this.showSuccess('Расписание сохранено для группы ' + this.getCurrentGroupName());
                form.reset();
                await this.loadSavedSchedules();
            } else {
                throw new Error(await response.text());
            }
        } catch (error) {
            this.showError('Ошибка сохранения: ' + error.message);
        }
    }

    async deleteSavedSchedule(scheduleId) {
        if (!confirm('Удалить это сохраненное расписание?')) return;

        this.showLoading();

        try {
            const response = await fetch(`/api/schedules/${scheduleId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Сохраненное расписание удалено');
                await this.loadSavedSchedules();
            } else {
                const result = await response.json();
                throw new Error(result.detail || 'Ошибка удаления расписания');
            }
        } catch (error) {
            this.showError('Ошибка удаления расписания: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // ========== ЭКСПОРТ ==========
    async exportSchedule(scheduleId, scheduleName) {
        this.showLoading();

        try {
            console.log(`📤 Экспорт расписания ${scheduleId}: "${scheduleName}"`);

            const response = await fetch(`/api/export/schedule/${scheduleId}`);

            console.log(`📥 Ответ сервера: ${response.status} ${response.statusText}`);

            if (response.ok) {
                const blob = await response.blob();
                console.log(`📊 Размер файла: ${blob.size} bytes`);
                console.log(`📊 Тип файла: ${blob.type}`);

                if (blob.size === 0) {
                    throw new Error('Файл пустой');
                }

                // Создаем blob и скачиваем файл
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;

                // Формируем имя файла с названием расписания
                const filename = `${scheduleName.replace(/[<>:"/\\|?*]/g, '_')}.xlsx`;
                a.download = filename;

                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                this.showSuccess(`Файл "${scheduleName}.xlsx" успешно скачан`);
            } else {
                const errorText = await response.text();
                console.error(`❌ Ошибка сервера: ${errorText}`);
                throw new Error(`Ошибка сервера: ${response.status}`);
            }
        } catch (error) {
            console.error('💥 Ошибка экспорта:', error);
            this.showError('Ошибка экспорта: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    // ========== СТАТИСТИКА ==========
    async updateStatistics() {
        try {
            const response = await fetch(`/api/statistics?group_id=${this.currentGroupId}`);
            if (response.ok) {
                const stats = await response.json();

                // Обновляем все параметры
                document.getElementById('statSubjects').textContent = stats.total_subjects;
                document.getElementById('statTotalHours').textContent = stats.total_hours;
                document.getElementById('statRemainingHours').textContent = stats.remaining_hours;

                console.log(`📊 Статистика обновлена для группы ${this.currentGroupId}:`, stats);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    // ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========
    async refreshAllData() {
        try {
            await Promise.all([
                this.loadSubjects(),
                this.loadLessons(),
                this.loadFilters(),
                this.loadSavedSchedules(),
                this.updateStatistics()
            ]);
            this.renderSchedule();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }

    async fixHoursCalculation() {
        if (!confirm('Пересчитать и исправить все часы для текущей группы?')) return;

        this.showLoading();

        try {
            const response = await fetch(`/api/statistics/fix-hours?group_id=${this.currentGroupId}`, {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess(result.message);

                // Перезагружаем все данные
                await this.refreshAllData();
            } else {
                const result = await response.json();
                throw new Error(result.detail || 'Ошибка исправления часов');
            }
        } catch (error) {
            this.showError('Ошибка исправления часов: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async clearAllData() {
        if (!confirm('ВНИМАНИЕ! Это действие удалит все данные текущей группы. Продолжить?')) return;

        try {
            const response = await fetch(`/clear-all?group_id=${this.currentGroupId}`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showSuccess('Все данные группы очищены');
                await this.refreshAllData();
                await this.updateStatistics();
            } else {
                throw new Error(await response.text());
            }
        } catch (error) {
            this.showError('Ошибка очистки: ' + error.message);
        }
    }

    showLoading() {
        document.getElementById('loadingSpinner').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i>
                <span>${message}</span>
            </div>
        `;

        // Стили для уведомления
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1003;
            animation: slideInRight 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Автоматическое скрытие
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // ========== CONTEXT MENU ==========
    handleLessonClick(cell) {
    // Это уже есть, оставляем как есть
    console.log('Lesson clicked:', cell.dataset.day, cell.dataset.slot);
}

showContextMenu(e) {
    const contextMenu = document.getElementById('contextMenu');
    const cell = e.target.closest('.schedule-cell');
    const hasLesson = cell.querySelector('.lesson-card');

    const day = parseInt(cell.dataset.day);
    const timeSlot = parseInt(cell.dataset.slot);

    // Сохраняем информацию о текущей ячейке
    this.currentSlot = { day, timeSlot };

    if (hasLesson) {
        // Если есть урок - режим удаления/замены
        this.currentLesson = { day, timeSlot };
        contextMenu.innerHTML = `
            <div class="context-item" data-action="delete">
                <i class="fas fa-trash"></i> Удалить пару
            </div>
            <div class="context-item" data-action="replace">
                <i class="fas fa-exchange-alt"></i> Заменить предмет
            </div>
        `;
    } else {
        // Если пустая ячейка - режим добавления
        this.currentLesson = null; // Нет урока для удаления
        contextMenu.innerHTML = `
            <div class="context-item" data-action="add_lesson">
                <i class="fas fa-plus"></i> Добавить пару
            </div>
        `;
    }

    contextMenu.style.display = 'block';
    contextMenu.style.left = e.pageX + 'px';
    contextMenu.style.top = e.pageY + 'px';

    // Обработчики действий
    contextMenu.querySelectorAll('.context-item').forEach(item => {
        item.onclick = () => {
            const action = item.dataset.action;
            this.handleContextAction(action);
        };
    });
}

handleContextAction(action) {
    switch (action) {
        case 'delete':
            this.deleteLesson();
            break;
        case 'replace':
            this.showReplaceModal();
            break;
        case 'add_lesson':
            this.showAddLessonModal();
            break;
    }
    this.hideContextMenu();
}

    showEmptyCellContextMenu(e, cell) {
        const contextMenu = document.getElementById('contextMenu');
        const day = parseInt(cell.dataset.day);
        const timeSlot = parseInt(cell.dataset.slot);

        this.currentSlot = { day, timeSlot };
        this.currentLesson = null;  // Сбрасываем currentLesson для пустой ячейки

        // Меню для свободной ячейки
        contextMenu.innerHTML = `
            <div class="context-item" data-action="add_lesson">
                <i class="fas fa-plus"></i> Добавить пару
            </div>
        `;

        contextMenu.style.display = 'block';
        contextMenu.style.left = e.pageX + 'px';
        contextMenu.style.top = e.pageY + 'px';

        // Обработчик для свободной ячейки
        contextMenu.querySelector('.context-item').onclick = () => {
            this.showAddLessonModal(true);  // true = режим добавления в пустую ячейку
            this.hideContextMenu();
        };
    }

   hideContextMenu() {
    document.getElementById('contextMenu').style.display = 'none';
}

    showAddLessonModal() {
    const modal = document.getElementById('replaceModal');
    const modalTitle = modal.querySelector('h3');
    const confirmBtn = document.getElementById('confirmReplace');
    const cancelBtn = document.getElementById('cancelReplace');

    // Настраиваем модалку для добавления
    modalTitle.textContent = 'Добавить пару';
    confirmBtn.textContent = 'Добавить';

    // Устанавливаем день и время
    document.getElementById('replaceDay').value = this.currentSlot.day;
    document.getElementById('replaceTimeSlot').value = this.currentSlot.timeSlot;

    // Заполняем список предметов
    this.populateSubjectSelect();

    // Очищаем предыдущие обработчики
    confirmBtn.onclick = null;
    cancelBtn.onclick = null;

    // Новые обработчики
    confirmBtn.onclick = async () => {
        await this.addLessonToEmptySlot();
    };

    cancelBtn.onclick = () => {
        modal.style.display = 'none';
    };

    modal.style.display = 'block';
}

    // 1. Обновленный метод deleteLesson
    async deleteLesson() {
    if (!this.currentLesson) {
        this.showError('Не выбрана пара для удаления');
        return;
    }

    if (!confirm('Удалить эту пару?')) return;

    this.showLoading();

    try {
        const response = await fetch(`/api/lessons?day=${this.currentLesson.day}&time_slot=${this.currentLesson.timeSlot}&group_id=${this.currentGroupId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const result = await response.json();
            this.showSuccess(result.message || 'Пара удалена');

            // Очищаем текущий урок
            this.currentLesson = null;

            // Обновляем данные
            await this.refreshAllData();
        } else {
            const errorText = await response.text();
            throw new Error(errorText || 'Ошибка удаления');
        }
    } catch (error) {
        console.error('❌ Ошибка удаления:', error);
        this.showError('Ошибка удаления: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

showReplaceModal() {
    const modal = document.getElementById('replaceModal');
    const modalTitle = modal.querySelector('h3');
    const confirmBtn = document.getElementById('confirmReplace');
    const cancelBtn = document.getElementById('cancelReplace');

    // Настраиваем модалку для замены
    modalTitle.textContent = 'Заменить пару';
    confirmBtn.textContent = 'Заменить';

    // Устанавливаем день и время
    document.getElementById('replaceDay').value = this.currentLesson.day;
    document.getElementById('replaceTimeSlot').value = this.currentLesson.timeSlot;

    // Заполняем список предметов
    this.populateSubjectSelect();

    // Очищаем предыдущие обработчики
    confirmBtn.onclick = null;
    cancelBtn.onclick = null;

    // Новые обработчики
    confirmBtn.onclick = async () => {
        await this.replaceLesson();
    };

    cancelBtn.onclick = () => {
        modal.style.display = 'none';
    };

    modal.style.display = 'block';
}

    // 2. Обновленный метод replaceLesson
    async replaceLesson() {
    const subjectSelect = document.getElementById('replaceSubjectSelect');
    const subjectId = subjectSelect.value;

    if (!subjectId) {
        this.showError('Выберите предмет для замены');
        return;
    }

    // Находим выбранный предмет
    const selectedSubject = this.subjects.find(s => s.id == subjectId);
    if (!selectedSubject) {
        this.showError('Выбранный предмет не найден');
        return;
    }

    const data = {
        day: parseInt(document.getElementById('replaceDay').value),
        time_slot: parseInt(document.getElementById('replaceTimeSlot').value),
        new_teacher: selectedSubject.teacher,
        new_subject_name: selectedSubject.subject_name
    };

    console.log('📤 Данные для замены:', data);

    this.showLoading();

    try {
        const response = await fetch(`/api/manual/lessons?group_id=${this.currentGroupId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        console.log('📥 Ответ сервера:', response.status, response.statusText);

        if (response.ok) {
            const result = await response.json();
            this.showSuccess(result.message || 'Пара успешно заменена');

            // Закрываем модалку
            document.getElementById('replaceModal').style.display = 'none';
            subjectSelect.innerHTML = '<option value="">Выберите предмет из списка</option>';
            document.getElementById('selectedSubjectInfo').style.display = 'none';

            // Обновляем данные
            await this.refreshAllData();
        } else {
            const result = await response.json();
            console.error('❌ Ошибка от сервера:', result);
            throw new Error(result.detail || result.message || `Ошибка ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Ошибка замены:', error);
        this.showError('Ошибка замены: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

    // 3. Новый метод для добавления пары в пустую ячейку
    async addLessonToEmptySlot() {
    const form = document.getElementById('replaceForm');
    const subjectId = document.getElementById('replaceSubjectSelect').value;

    if (!subjectId) {
        this.showError('Выберите предмет для добавления');
        return;
    }

    // Находим выбранный предмет
    const selectedSubject = this.subjects.find(s => s.id == subjectId);
    if (!selectedSubject) {
        this.showError('Выбранный предмет не найден');
        return;
    }

    const data = {
        day: parseInt(document.getElementById('replaceDay').value),
        time_slot: parseInt(document.getElementById('replaceTimeSlot').value),
        teacher: selectedSubject.teacher,
        subject_name: selectedSubject.subject_name
    };

    this.showLoading();

    try {
        console.log('📤 Добавление пары:', data);

        const response = await fetch(`/api/manual/lessons?group_id=${this.currentGroupId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const result = await response.json();
            this.showSuccess(result.message || 'Пара добавлена');

            // Закрываем модалку
            document.getElementById('replaceModal').style.display = 'none';
            form.reset();
            document.getElementById('selectedSubjectInfo').style.display = 'none';

            // Обновляем данные
            await this.refreshAllData();
        } else {
            const result = await response.json();
            throw new Error(result.detail || result.message || 'Ошибка добавления');
        }
    } catch (error) {
        console.error('❌ Ошибка добавления:', error);
        this.showError('Ошибка добавления: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

    populateSubjectSelect() {
    const select = document.getElementById('replaceSubjectSelect');
    select.innerHTML = '<option value="">Выберите предмет из списка</option>';

    if (!this.subjects || this.subjects.length === 0) {
        console.warn('⚠️ Нет предметов для выбора');
        return;
    }

    this.subjects.forEach(subject => {
        if (subject.remaining_pairs > 0) {
            const option = document.createElement('option');
            option.value = subject.id;
            option.textContent = `${subject.teacher} - ${subject.subject_name} (${subject.remaining_pairs} пар осталось)`;
            option.dataset.teacher = subject.teacher;
            option.dataset.subjectName = subject.subject_name;
            option.dataset.remainingPairs = subject.remaining_pairs;
            option.dataset.totalHours = subject.total_hours;
            select.appendChild(option);
        }
    });

    // Добавляем обработчик изменения выбора
    select.addEventListener('change', (e) => {
        this.updateSelectedSubjectInfo(e.target);
    });
}

updateSelectedSubjectInfo(select) {
    const infoDiv = document.getElementById('selectedSubjectInfo');
    const selectedOption = select.options[select.selectedIndex];

    if (selectedOption.value && selectedOption.dataset.teacher) {
        document.getElementById('infoTeacher').textContent = selectedOption.dataset.teacher;
        document.getElementById('infoHours').textContent = selectedOption.dataset.totalHours;
        document.getElementById('infoRemainingPairs').textContent = selectedOption.dataset.remainingPairs;
        infoDiv.style.display = 'block';
    } else {
        infoDiv.style.display = 'none';
    }
}
}

// Добавляем CSS анимации для уведомлений
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 8px;
    }
`;
document.head.appendChild(style);

// Инициализация приложения
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ScheduleApp();
});