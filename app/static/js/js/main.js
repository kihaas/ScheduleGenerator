// Главный файл приложения
class ScheduleApp {
    constructor() {
        this.api = new ApiService();
        this.ui = new UIRenderer();
        this.utils = Utils;

        this.currentLesson = null;
        this.teachers = [];
        this.subjects = [];
        this.lessons = [];
        this.savedSchedules = [];
        this.filters = [];
    }

    async init() {
        this.setupEventListeners();
        this.setupThemeToggle();
        await this.loadInitialData();
        await this.refreshAllData();
    }

    setupEventListeners() {
        // Sidebar
        document.getElementById('sidebarToggle').addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('active');
        });

        // Section headers
        document.querySelectorAll('.nav-section-header').forEach(header => {
            header.addEventListener('click', () => {
                header.parentElement.classList.toggle('active');
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

        // Buttons
        document.getElementById('generateSchedule').addEventListener('click', () => {
            this.generateSchedule();
        });

        document.getElementById('fullGenerate').addEventListener('click', () => {
            this.generateSchedule();
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
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('theme');

        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
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
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadTeachers(),
                this.loadSubjects(),
                this.loadLessons(),
                this.loadFilters()
            ]);
        } catch (error) {
            this.utils.showNotification('Ошибка загрузки данных: ' + error.message, 'error');
        }
    }

    async loadTeachers() {
        this.teachers = await this.api.getTeachers();
        this.ui.populateTeacherSelects(
            document.querySelectorAll('select[name="teacher"], #teacherSelect, #filterTeacherSelect'),
            this.teachers
        );
        this.ui.renderTeachersList(
            document.getElementById('teachersList'),
            this.teachers,
            'app.deleteTeacher'
        );
    }

    async loadSubjects() {
        this.subjects = await this.api.getSubjects();
        this.ui.renderSubjectsList(
            document.getElementById('subjectsList'),
            this.subjects,
            'app.deleteSubject'
        );
    }

    async loadLessons() {
        this.lessons = await this.api.getLessons();
        this.ui.renderSchedule(document.getElementById('scheduleGrid'), this.lessons);
    }

    async loadFilters() {
        this.filters = await this.api.getFilters();
        this.renderFiltersList();
    }

    async addTeacher() {
        const form = document.getElementById('addTeacherForm');
        const formData = new FormData(form);
        const name = formData.get('name').trim();

        const error = this.utils.validateForm({ name }, ['name']);
        if (error) {
            this.utils.showNotification(error, 'error');
            return;
        }

        this.utils.showLoading();
        try {
            await this.api.createTeacher(name);
            this.utils.showNotification('Преподаватель добавлен', 'success');
            form.reset();
            await this.loadTeachers();
            await this.updateStatistics();
        } catch (error) {
            this.utils.showNotification('Ошибка добавления преподавателя: ' + error.message, 'error');
        } finally {
            this.utils.hideLoading();
        }
    }

    async deleteTeacher(teacherId) {
        if (!confirm('Удалить этого преподавателя?')) return;

        this.utils.showLoading();
        try {
            await this.api.deleteTeacher(teacherId);
            this.utils.showNotification('Преподаватель удален', 'success');
            await this.loadTeachers();
            await this.loadSubjects();
            await this.updateStatistics();
        } catch (error) {
            this.utils.showNotification('Ошибка удаления преподавателя: ' + error.message, 'error');
        } finally {
            this.utils.hideLoading();
        }
    }

    async generateSchedule() {
        this.utils.showLoading();
        try {
            const result = await this.api.generateSchedule();
            this.utils.showNotification(`Сгенерировано ${result.lessons.length} пар`, 'success');
            await this.refreshAllData();
        } catch (error) {
            this.utils.showNotification('Ошибка генерации: ' + error.message, 'error');
        } finally {
            this.utils.hideLoading();
        }
    }

    async updateStatistics() {
        try {
            const stats = await this.api.getStatistics();
            document.getElementById('statSubjects').textContent = stats.total_subjects;
            document.getElementById('statTotalHours').textContent = stats.total_hours;
            document.getElementById('statRemainingHours').textContent = stats.remaining_hours;
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    async refreshAllData() {
        await Promise.all([
            this.loadSubjects(),
            this.loadLessons(),
            this.updateStatistics()
        ]);
    }

    // ... остальные методы (addSubject, deleteSubject, addNegativeFilter и т.д.)
    // будут аналогично переписаны с использованием модулей
}

// Инициализация приложения
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ScheduleApp();
});