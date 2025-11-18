// Модуль для рендеринга UI
class UIRenderer {
    constructor() {
        this.weekDays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];
        this.timeSlots = [
            { start: '9:00', end: '10:30' },
            { start: '10:40', end: '12:10' },
            { start: '12:40', end: '14:10' },
            { start: '14:20', end: '15:50' }
        ];
    }

    // Рендеринг преподавателей
    renderTeachersList(container, teachers, onDelete) {
        if (!teachers.length) {
            container.innerHTML = '<div class="empty-state">Нет преподавателей</div>';
            return;
        }

        container.innerHTML = teachers.map(teacher => `
            <div class="teacher-item" data-id="${teacher.id}">
                <div class="teacher-info">
                    <strong>${teacher.name}</strong>
                    <div class="teacher-meta">ID: ${teacher.id}</div>
                </div>
                <button class="btn-danger btn-small" onclick="${onDelete}(${teacher.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    // Рендеринг предметов
    renderSubjectsList(container, subjects, onDelete) {
        if (!subjects.length) {
            container.innerHTML = '<div class="empty-state">Нет добавленных предметов</div>';
            return;
        }

        container.innerHTML = subjects.map(subject => {
            const consumedHours = subject.total_hours - subject.remaining_hours;
            const progressPercent = subject.total_hours > 0 ? (consumedHours / subject.total_hours) * 100 : 0;

            return `
                <div class="subject-item" data-id="${subject.id}">
                    <div class="subject-info">
                        <strong>${subject.subject_name}</strong>
                        <div class="teacher-name">${subject.teacher}</div>
                        <div class="hours-info">
                            <div class="hours-progress">${consumedHours} / ${subject.total_hours} часов</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${progressPercent}%"></div>
                            </div>
                            <div class="pairs-info">${subject.remaining_pairs} пар осталось</div>
                        </div>
                    </div>
                    <div class="subject-actions">
                        <div class="priority-badge">Приоритет: ${subject.priority}</div>
                        <button class="btn-danger btn-small" onclick="${onDelete}(${subject.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Рендеринг расписания
    renderSchedule(container, lessons) {
        let html = '';

        // Header
        html += '<div class="schedule-header"></div>';
        this.weekDays.forEach((day, index) => {
            const isWeekend = index >= 5;
            html += `<div class="schedule-header ${isWeekend ? 'weekend' : ''}">${day}</div>`;
        });

        // Time slots and lessons
        this.timeSlots.forEach((slot, slotIndex) => {
            html += `<div class="time-slot">${slot.start}<br>${slot.end}<div class="time-slot-number">${slotIndex + 1}</div></div>`;

            for (let day = 0; day < 7; day++) {
                const lesson = lessons.find(l => l.day === day && l.time_slot === slotIndex);
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

            // Lunch break
            if (slotIndex === 1) {
                html += `<div class="lunch-break" style="grid-column: 1 / span 8;">
                    <i class="fas fa-utensils"></i> Обеденный перерыв
                </div>`;
            }
        });

        container.innerHTML = html;
    }

    // Заполнение select элементов
    populateTeacherSelects(selects, teachers) {
        selects.forEach(select => {
            select.innerHTML = '<option value="">Выберите преподавателя</option>';
            teachers.forEach(teacher => {
                const option = document.createElement('option');
                option.value = teacher.name;
                option.textContent = teacher.name;
                select.appendChild(option);
            });
        });
    }
}