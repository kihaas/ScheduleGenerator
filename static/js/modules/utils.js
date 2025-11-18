// Утилиты
class Utils {
    // Уведомления
    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i>
                <span>${message}</span>
            </div>
        `;

        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'success' ? '#10b981' : '#ef4444',
            color: 'white',
            padding: '12px 16px',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: '1003',
            animation: 'slideInRight 0.3s ease'
        });

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Loading spinner
    static showLoading() {
        document.getElementById('loadingSpinner').style.display = 'flex';
    }

    static hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
    }

    // Валидация
    static validateForm(data, requiredFields) {
        for (const field of requiredFields) {
            if (!data[field] || data[field].toString().trim().length === 0) {
                return `Поле "${field}" обязательно для заполнения`;
            }
        }
        return null;
    }
}