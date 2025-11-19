// Модуль для работы с API
class ApiService {
    constructor() {
        this.baseUrl = '';
    }

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'API Error');
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Teachers
    async getTeachers() {
        return this.request('/api/teachers');
    }

    async createTeacher(name) {
        return this.request('/api/teachers', {
            method: 'POST',
            body: JSON.stringify({ name })
        });
    }

    async deleteTeacher(id) {
        return this.request(`/api/teachers/${id}`, {
            method: 'DELETE'
        });
    }

    // Subjects
    async getSubjects() {
        return this.request('/api/subjects');
    }

    async createSubject(data) {
        return this.request('/api/subjects', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async deleteSubject(id) {
        return this.request(`/api/subjects/${id}`, {
            method: 'DELETE'
        });
    }

    // Lessons
    async getLessons() {
        return this.request('/api/lessons');
    }

    async deleteLesson(day, timeSlot) {
        return this.request(`/api/lessons?day=${day}&time_slot=${timeSlot}`, {
            method: 'DELETE'
        });
    }

    async updateLesson(data) {
        return this.request('/api/lessons', {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    // Filters
    async getFilters() {
        return this.request('/api/negative-filters');
    }

    async createFilter(data) {
        return this.request('/api/negative-filters', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async deleteFilter(teacher) {
        return this.request(`/api/negative-filters/${encodeURIComponent(teacher)}`, {
            method: 'DELETE'
        });
    }

    // Schedule
    async generateSchedule() {
        return this.request('/api/schedule/generate', {
            method: 'POST'
        });
    }

    async getStatistics() {
        return this.request('/api/statistics');
    }
}