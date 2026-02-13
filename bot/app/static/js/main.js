// Main Application Module
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    if (!checkAuth()) {
        window.location.href = 'login.html';
        return;
    }
    
    // Load user data
    const currentUser = getCurrentUser();
    if (currentUser) {
        AppState.user = currentUser;
        document.getElementById('userAvatar').textContent = currentUser.avatar;
    }
    
    // Initialize data
    initializeData();
    
    // Initialize UI components
    initUIComponents();
    
    // Router will handle page loading
});

// Initialize UI Components
function initUIComponents() {
    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 992 && 
                !sidebar.contains(e.target) && 
                !sidebarToggle.contains(e.target) && 
                sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }
        });
    }

    // User menu toggle
    const userBtn = document.getElementById('userBtn');
    const userMenu = document.getElementById('userMenu');
    
    if (userBtn && userMenu) {
        userBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('active');
        });
        
        // Close user menu when clicking outside
        document.addEventListener('click', () => {
            userMenu.classList.remove('active');
        });
        
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                logout();
            });
        }
    }

    // Global search
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        const debouncedSearch = debounce(performSearch, 500);
        globalSearch.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
        });
    }
    
    // Notification button
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', showNotifications);
    }
}

// Search Function
function performSearch(query) {
    if (!query.trim()) return;
    
    // In a real app, you would search across all data
    // For now, just show a notification
    showNotification(`Поиск: "${query}"`, 'info');
}

// Notification System
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: white;
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
        box-shadow: var(--shadow-lg);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        min-width: 300px;
        max-width: 400px;
        z-index: 10000;
        border-left: 4px solid ${type === 'success' ? 'var(--secondary)' : type === 'error' ? 'var(--danger)' : 'var(--primary)'};
        animation: slideIn 0.3s ease-out;
    `;
    
    // Add close button event
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Add to body
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Show notifications modal
function showNotifications() {
    // In a real app, you would fetch notifications from server
    const notifications = [
        { id: 1, title: 'Новая заявка', message: 'Поступила новая заявка от Ивана Петрова', time: '5 мин назад', read: false },
        { id: 2, title: 'Заказ запчастей', message: 'Заказ запчастей доставлен на склад', time: '2 часа назад', read: false },
        { id: 3, title: 'Обновление системы', message: 'Запланировано обновление системы на 02:00', time: 'Сегодня', read: true }
    ];
    
    // Create notifications modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal" style="max-width: 500px;">
            <div class="modal-header">
                <h2 class="modal-title">Уведомления</h2>
                <button class="modal-close" id="closeNotifications">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="notifications-list">
                    ${notifications.map(notif => `
                        <div class="notification-item ${notif.read ? 'read' : 'unread'}" data-id="${notif.id}">
                            <div class="notification-icon">
                                <i class="fas ${notif.read ? 'fa-bell' : 'fa-bell'}"></i>
                            </div>
                            <div class="notification-content">
                                <div class="notification-title">${notif.title}</div>
                                <div class="notification-message">${notif.message}</div>
                                <div class="notification-time">${notif.time}</div>
                            </div>
                            ${!notif.read ? '<div class="notification-dot"></div>' : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" id="markAllReadBtn">
                    Отметить все как прочитанные
                </button>
                <button class="btn btn-primary" id="closeModalBtn">
                    Закрыть
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    const closeBtn = modal.querySelector('#closeNotifications');
    const closeModalBtn = modal.querySelector('#closeModalBtn');
    const markAllReadBtn = modal.querySelector('#markAllReadBtn');
    
    const closeModal = () => modal.remove();
    
    closeBtn.addEventListener('click', closeModal);
    closeModalBtn.addEventListener('click', closeModal);
    
    markAllReadBtn.addEventListener('click', () => {
        showNotification('Все уведомления отмечены как прочитанные', 'success');
        closeModal();
    });
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Add styles for notifications
    if (!document.querySelector('#notifications-styles')) {
        const style = document.createElement('style');
        style.id = 'notifications-styles';
        style.textContent = `
            .notifications-list {
                max-height: 400px;
                overflow-y: auto;
            }
            
            .notification-item {
                display: flex;
                align-items: flex-start;
                gap: 1rem;
                padding: 1rem;
                border-bottom: 1px solid var(--gray-200);
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .notification-item:hover {
                background-color: var(--gray-50);
            }
            
            .notification-item.unread {
                background-color: rgba(37, 99, 235, 0.05);
            }
            
            .notification-icon {
                width: 40px;
                height: 40px;
                background-color: var(--gray-100);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--gray-600);
            }
            
            .notification-content {
                flex: 1;
            }
            
            .notification-title {
                font-weight: 600;
                color: var(--gray-900);
                margin-bottom: 0.25rem;
            }
            
            .notification-message {
                font-size: 0.875rem;
                color: var(--gray-600);
                margin-bottom: 0.25rem;
            }
            
            .notification-time {
                font-size: 0.75rem;
                color: var(--gray-500);
            }
            
            .notification-dot {
                width: 8px;
                height: 8px;
                background-color: var(--primary);
                border-radius: 50%;
                margin-top: 0.5rem;
            }
        `;
        document.head.appendChild(style);
    }
}

// Helper function from utils
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Make functions available globally
window.showNotification = showNotification;