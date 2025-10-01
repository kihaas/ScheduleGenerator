// app/static/js/main.js

// Переключение темы
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

// Восстановление темы при загрузке
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
});

// Контекстное меню для слотов
document.addEventListener('contextmenu', function(e) {
    const slot = e.target.closest('.schedule-cell');
    if (!slot) return;

    e.preventDefault();

    const day = slot.dataset.day;
    const timeSlot = slot.dataset.timeSlot;
    const weekStart = document.getElementById('weekStart')?.value || '2025-09-22'; // заглушка

    // Открыть модальное окно для редактирования
    openEditModal(day, timeSlot, weekStart);
});

function openEditModal(day, timeSlot, weekStart) {
    // Пока просто alert — позже заменим на модалку
    alert(`Редактирование слота: день=${day}, пара=${timeSlot}, неделя=${weekStart}`);
}

// Переключение недели
function changeWeek(dateStr) {
    // Пока просто перезагрузка — позже сделаем AJAX
    window.location.search = `?week=${dateStr}`;
}

// Обновление списка преподавателей
function updateTeacherSelect() {
    const select = document.getElementById('filter_teacher');
    if (!select) return;

    const subjects = JSON.parse(document.getElementById('subjects-data').textContent);
    const teachers = [...new Set(subjects.map(s => s.teacher))];

    select.innerHTML = '<option value="">Выберите преподавателя</option>';
    teachers.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        select.appendChild(opt);
    });
}

// Инициализация
document.addEventListener('DOMContentLoaded', updateTeacherSelect);