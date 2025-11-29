class ScheduleApp {
    constructor() {
        this.currentLesson = null;
        this.teachers = [];
        this.subjects = [];
        this.lessons = [];
        this.savedSchedules = [];
        this.filters = [];
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupThemeToggle();
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
            this.generateSchedule();
        });

        document.getElementById('clearAll').addEventListener('click', () => {
            this.clearAllData();
        });


        // Context menu
        document.addEventListener('contextmenu', (e) => {
            if (e.target.closest('.schedule-cell') && e.target.closest('.lesson-card')) {
                e.preventDefault();
                this.showContextMenu(e);
            }
        });

        document.addEventListener('click', () => {
            this.hideContextMenu();
        });

        // Modal events
        this.setupModalEvents();
    }

    setupModalEvents() {
        const replaceModal = document.getElementById('replaceModal');
        const closeBtn = replaceModal.querySelector('.close');
        const cancelBtn = document.getElementById('cancelReplace');
        const confirmBtn = document.getElementById('confirmReplace');

        [closeBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => {
                replaceModal.style.display = 'none';
            });
        });

        confirmBtn.addEventListener('click', () => {
            this.replaceLesson();
        });

        // Close modal on outside click
        replaceModal.addEventListener('click', (e) => {
            if (e.target === replaceModal) {
                replaceModal.style.display = 'none';
            }
        });
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
                this.loadTeachers(),
                this.loadSubjects(),
                this.loadLessons(),
                this.loadSavedSchedules(),
                this.loadFilters()  // Убедиться что эта строка есть
            ]);
        } catch (error) {
            console.error('⚠️ Предупреждение при загрузке данных:', error.message);
            this.showError('Ошибка загрузки данных: ' + error.message);
    }
}

    async loadTeachers() {
        try {
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

    async loadSubjects() {
    try {
        const response = await fetch('/api/subjects');
        if (response.ok) {
            this.subjects = await response.json();
            this.renderSubjectsList();
        } else {
            throw new Error('Failed to load subjects');
        }
    } catch (error) {
        console.error('Error loading subjects:', error);
        this.showError('Ошибка загрузки предметов: ' + error.message);
    }
}

    async loadLessons() {
        try {
            const response = await fetch('/api/lessons');
            if (response.ok) {
                this.lessons = await response.json();
                this.renderSchedule();
            }
        } catch (error) {
            console.error('Error loading lessons:', error);
        }
    }

    async loadSavedSchedules() {
        try {
            const response = await fetch('/api/schedules');
            if (response.ok) {
                this.savedSchedules = await response.json();
                this.renderSavedSchedulesList();
            }
        } catch (error) {
            console.error('Error loading saved schedules:', error);
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

    async deleteFilter(teacher) {
    if (!confirm(`Удалить ограничения для ${teacher}?`)) return;

    try {
        const response = await fetch(`/api/negative-filters/${encodeURIComponent(teacher)}`, {
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

    async loadFilters() {
    try {
        console.log("🔄 Загрузка ограничений...");
        const response = await fetch('/api/negative-filters');

        if (response.ok) {
            this.filters = await response.json();
            console.log("✅ Ограничения загружены:", this.filters);
            this.renderFiltersList();
        } else {
            console.error("❌ Ошибка загрузки ограничений:", response.status);
        }
    } catch (error) {
        console.error('Error loading filters:', error);
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

    renderSubjectsList() {
    const container = document.getElementById('subjectsList');
    if (!this.subjects || this.subjects.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет добавленных предметов</div>';
        return;
    }

    container.innerHTML = this.subjects.map(subject => {
        // Рассчитываем прогресс
        const consumedHours = subject.total_hours - subject.remaining_hours;
        const progressPercent = subject.total_hours > 0 ? (consumedHours / subject.total_hours) * 100 : 0;

        console.log(`Subject: ${subject.subject_name}, Total: ${subject.total_hours}, Remaining: ${subject.remaining_hours}, Progress: ${progressPercent}%`);

        return `
            <div class="subject-item" data-id="${subject.id}">
                <div class="subject-info">
                    <strong>${subject.subject_name}</strong>
                    <div class="teacher-name">${subject.teacher}</div>
                    <div class="hours-info">
                        <div class="hours-progress">
                            ${consumedHours} / ${subject.total_hours} часов
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progressPercent}%"></div>
                        </div>
                        <div class="pairs-info">
                            ${subject.remaining_pairs} пар осталось
                        </div>
                    </div>
                </div>
                <div class="subject-actions">
                    <div class="priority-badge">Приоритет: ${subject.priority}</div>
                    <button class="btn-danger btn-small" onclick="app.deleteSubject(${subject.id})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');
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
                <!-- ИСПРАВИТЬ ЭТУ КНОПКУ -->
                <button class="btn-danger btn-small" onclick="app.deleteSavedSchedule(${schedule.id})" title="Удалить">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `).join('');
}

    renderFiltersList() {
    const container = document.getElementById('filtersList');

    if (!this.filters || Object.keys(this.filters).length === 0) {
        container.innerHTML = '<div class="empty-state">Нет сохраненных ограничений</div>';
        return;
    }

    console.log("🎯 Рендерим ограничения:", this.filters);

    container.innerHTML = Object.entries(this.filters).map(([teacher, filter]) => {
        // Преобразуем дни в читаемый формат
        const daysMap = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт'};
        const daysText = filter.restricted_days && filter.restricted_days.length > 0
            ? filter.restricted_days.map(d => daysMap[d] || d).join(', ')
            : 'нет';

        // Преобразуем слоты в читаемый формат (1,2,3,4 вместо 0,1,2,3)
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

    // Header row
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

        // ⚠️ УБРАТЬ ЭТОТ БЛОК - обеденный перерыв
        // if (slotIndex === 1) {
        //     html += `<div class="lunch-break" style="grid-column: 1 / span 8;">
        //         <i class="fas fa-utensils"></i> Обеденный перерыв
        //     </div>`;
        // }
    });

    scheduleGrid.innerHTML = html;

    // Add click handlersfff
    scheduleGrid.querySelectorAll('.schedule-cell').forEach(cell => {
        cell.addEventListener('click', (e) => {
            if (e.target.closest('.lesson-card')) {
                this.handleLessonClick(cell);
            }
        });
    });
}

    handleLessonClick(cell) {
        // Можно добавить функциональность при клике на пару
        console.log('Lesson clicked:', cell.dataset.day, cell.dataset.slot);
    }

    showContextMenu(e) {
        const contextMenu = document.getElementById('contextMenu');
        const cell = e.target.closest('.schedule-cell');

        this.currentLesson = {
            day: parseInt(cell.dataset.day),
            time_slot: parseInt(cell.dataset.slot)
        };

        contextMenu.style.display = 'block';
        contextMenu.style.left = e.pageX + 'px';
        contextMenu.style.top = e.pageY + 'px';

        // Context menu actions
        contextMenu.querySelectorAll('.context-item').forEach(item => {
            item.onclick = () => {
                const action = item.dataset.action;
                this.handleContextAction(action);
            };
        });
    }

    hideContextMenu() {
        document.getElementById('contextMenu').style.display = 'none';
    }

    handleContextAction(action) {
        switch (action) {
            case 'delete':
                this.deleteLesson();
                break;
            case 'replace':
                this.showReplaceModal();
                break;
        }
        this.hideContextMenu();
    }

    async deleteLesson() {
        if (!this.currentLesson) return;

        if (!confirm('Удалить эту пару?')) return;

        try {
            const response = await fetch(`/api/lessons?day=${this.currentLesson.day}&time_slot=${this.currentLesson.time_slot}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Пара удалена');
                await this.loadLessons();
                await this.updateStatistics();
            } else {
                throw new Error(await response.text());
            }
        } catch (error) {
            this.showError('Ошибка удаления: ' + error.message);
        }
    }

    showReplaceModal() {
    const modal = document.getElementById('replaceModal');
    document.getElementById('replaceDay').value = this.currentLesson.day;
    document.getElementById('replaceTimeSlot').value = this.currentLesson.time_slot;

    // Заполняем выпадающий список предметами
    this.populateSubjectSelect();

    modal.style.display = 'block';
}

updateSelectedSubjectInfo(select) {
    const infoDiv = document.getElementById('selectedSubjectInfo');
    const selectedOption = select.options[select.selectedIndex];

    if (selectedOption.value) {
        document.getElementById('infoTeacher').textContent = selectedOption.dataset.teacher;
        document.getElementById('infoHours').textContent = selectedOption.dataset.totalHours;
        document.getElementById('infoRemainingPairs').textContent = selectedOption.dataset.remainingPairs;
        infoDiv.style.display = 'block';
    } else {
        infoDiv.style.display = 'none';
    }
}


populateSubjectSelect() {
    const select = document.getElementById('replaceSubjectSelect');
    select.innerHTML = '<option value="">Выберите предмет из списка</option>';

    this.subjects.forEach(subject => {
        if (subject.remaining_pairs > 0) { // Показываем только предметы с оставшимися парами
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




    async replaceLesson() {
    const form = document.getElementById('replaceForm');
    const subjectId = form.subject_id.value;

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
        day: parseInt(form.day.value),
        time_slot: parseInt(form.time_slot.value),
        new_teacher: selectedSubject.teacher,
        new_subject_name: selectedSubject.subject_name
    };

    this.showLoading();

    try {
        const response = await fetch('/api/lessons', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            this.showSuccess('Пара заменена');
            document.getElementById('replaceModal').style.display = 'none';
            form.reset();
            document.getElementById('selectedSubjectInfo').style.display = 'none';

            // Обновляем данные
            await this.refreshAllData();
        } else {
            const result = await response.json();
            throw new Error(result.detail || 'Ошибка замены пары');
        }
    } catch (error) {
        this.showError('Ошибка замены: ' + error.message);
    } finally {
        this.hideLoading();
    }
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
                this.showSuccess('Преподаватель добавлен');
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
    if (!confirm('Удалить этого преподавателя?')) return;

    this.showLoading();

    try {
        const response = await fetch(`/api/teachers/${teacherId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            this.showSuccess('Преподаватель удален');
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

    async addSubject() {
    const form = document.getElementById('addSubjectForm');
    const formData = new FormData(form);

    const data = {
        teacher: formData.get('teacher'),
        subject_name: formData.get('subject_name'),
        hours: parseInt(formData.get('hours')),
        priority: parseInt(formData.get('priority')) || 0,
        max_per_day: parseInt(formData.get('max_per_day')) || 2
    };

    // Валидация
    if (!data.teacher || !data.subject_name || !data.hours) {
        this.showError('Заполните все обязательные поля');
        return;
    }

    this.showLoading();

    try {
        const response = await fetch('/api/subjects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            this.showSuccess('Предмет добавлен');
            form.reset();
            // Автообновление статистики и предметов
            await this.loadSubjects();
            await this.updateStatistics(); // АВТООБНОВЛЕНИЕ
        } else {
            if (response.status === 409) {
                this.showError('Предмет с таким названием уже существует у этого преподавателя');
            } else {
                throw new Error(result.detail || result.error || 'Ошибка добавления предмета');
            }
        }
    } catch (error) {
        this.showError('Ошибка добавления предмета: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

async deleteSubject(subjectId) {
    if (!confirm('Удалить этот предмет?')) return;

    this.showLoading();

    try {
        const response = await fetch(`/api/subjects/${subjectId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            this.showSuccess('Предмет удален');
            // Автообновление статистики и предметов
            await this.loadSubjects();
            await this.updateStatistics(); // АВТООБНОВЛЕНИЕ
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

async generateSchedule() {
    this.showLoading();

    try {
        const response = await fetch('/api/schedule/generate', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            this.showSuccess(`Сгенерировано ${result.lessons.length} пар`);
            // Автообновление ВСЕХ данных
            await this.refreshAllData();
        } else {
            throw new Error(result.detail || 'Ошибка генерации');
        }
    } catch (error) {
        this.showError('Ошибка генерации: ' + error.message);
    } finally {
        this.hideLoading();
    }
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

    // Проверяем что выбраны ограничения
    if (restrictedDays.length === 0 && restrictedSlots.length === 0) {
        this.showError('Выберите хотя бы один день или пару для ограничения');
        return;
    }

    this.showLoading();

    try {
        const response = await fetch('/api/negative-filters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            this.showSuccess('Ограничения сохранены');
            form.reset();

            // Перезагружаем и автоматически раскрываем секцию ограничений
            await this.loadFilters();

            // Автоматически раскрываем секцию ограничений чтобы увидеть результат
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

    async saveSchedule() {
        const form = document.getElementById('saveScheduleForm');
        const formData = new FormData(form);
        const name = formData.get('name');

        if (!name) {
            this.showError('Введите название расписания');
            return;
        }

        try {
            const response = await fetch('/api/schedules/save', {
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
                this.showSuccess('Расписание сохранено');
                form.reset();
                await this.loadSavedSchedules();
            } else {
                throw new Error(await response.text());
            }
        } catch (error) {
            this.showError('Ошибка сохранения: ' + error.message);
        }
    }

    async loadSchedule(scheduleId) {
        try {
            const response = await fetch(`/api/schedules/${scheduleId}`);
            if (response.ok) {
                const schedule = await response.json();
                this.lessons = schedule.lessons;
                this.renderSchedule();
                this.showSuccess('Расписание загружено');
                await this.updateStatistics();
            } else {
                throw new Error(await response.text());
            }
        } catch (error) {
            this.showError('Ошибка загрузки расписания: ' + error.message);
        }
    }

    async deleteSubject(subjectId) {
    if (!confirm('Удалить этот предмет?')) return;

    this.showLoading();

    try {
        const response = await fetch(`/api/subjects/${subjectId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            this.showSuccess('Предмет удален');
            // Перезагружаем список предметов
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

    async generateSchedule() {
    this.showLoading();

    try {
        const response = await fetch('/api/schedule/generate', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            this.showSuccess(`Сгенерировано ${result.lessons.length} пар`);
            // Автоматически обновляем все данные
            await this.refreshAllData();
        } else {
            throw new Error(result.detail || 'Ошибка генерации');
        }
    } catch (error) {
        this.showError('Ошибка генерации: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

    async clearAllData() {
        if (!confirm('ВНИМАНИЕ! Это действие удалит все данные. Продолжить?')) return;

        try {
            const response = await fetch('/clear-all', {
                method: 'POST'
            });

            if (response.ok) {
                this.showSuccess('Все данные очищены');
                await this.loadInitialData();
                await this.updateStatistics();
            } else {
                throw new Error(await response.text());
            }
        } catch (error) {
            this.showError('Ошибка очистки: ' + error.message);
        }
    }

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

async exportCurrentSchedule() {
    this.showLoading();

    try {
        const response = await fetch('/api/export/current');

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'текущее_расписание.xlsx';

            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showSuccess('Текущее расписание экспортировано в Excel');
        } else {
            throw new Error('Ошибка экспорта текущего расписания');
        }
    } catch (error) {
        this.showError('Ошибка экспорта: ' + error.message);
    } finally {
        this.hideLoading();
    }
}

    async updateStatistics() {
    try {
        const response = await fetch('/api/statistics');
        if (response.ok) {
            const stats = await response.json();

            // Обновляем новые параметры
            document.getElementById('statSubjects').textContent = stats.total_subjects;
            document.getElementById('statTotalHours').textContent = stats.total_hours;
            document.getElementById('statRemainingHours').textContent = stats.remaining_hours;

            console.log(`📊 Статистика обновлена: ${stats.total_subjects} предметов, ${stats.total_hours}ч всего, ${stats.remaining_hours}ч осталось`);
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}
// Автообновление при любых изменениях
async refreshAllData() {
    try {
        await Promise.all([
            this.loadSubjects(),
            this.loadLessons(),
            this.updateStatistics() // Включаем обновление статистики
        ]);
        this.renderSchedule();
    } catch (error) {
        console.error('Error refreshing data:', error);
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