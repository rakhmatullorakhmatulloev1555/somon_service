// Router Module
const Router = {
    routes: {},
    currentRoute: null,
    
    init: function() {
        // Define routes
        this.routes = {
            '/dashboard': { 
                title: 'Панель управления', 
                file: 'pages/dashboard.html',
                script: 'js/dashboard.js'
            },
            '/orders': { 
                title: 'Заявки', 
                file: 'pages/orders.html',
                script: 'js/orders.js'
            },
            '/clients': { 
                title: 'Клиенты', 
                file: 'pages/clients.html',
                script: 'js/clients.js'
            },
            '/masters': { 
                title: 'Мастера', 
                file: 'pages/masters.html',
                script: 'js/masters.js'
            },
            '/parts': { 
                title: 'Запчасти', 
                file: 'pages/parts.html',
                script: 'js/parts.js'
            },
            '/services': { 
                title: 'Услуги', 
                file: 'pages/services.html',
                script: 'js/services.js'
            },
            '/analytics': { 
                title: 'Аналитика', 
                file: 'pages/analytics.html',
                script: 'js/analytics.js'
            },
            '/settings': { 
                title: 'Настройки', 
                file: 'pages/settings.html',
                script: 'js/settings.js'
            },
            '/telegram': { 
                title: 'Telegram Бот', 
                file: 'pages/telegram.html',
                script: 'js/telegram.js'
            },
            '/help': { 
                title: 'Помощь', 
                file: 'pages/help.html',
                script: 'js/help.js'
            },
            '/profile': { 
                title: 'Мой профиль', 
                file: 'pages/profile.html',
                script: 'js/profile.js'
            }
        };
        
        // Handle hash changes
        window.addEventListener('hashchange', () => this.handleRoute());
        
        // Handle initial route
        this.handleRoute();
    },
    
    handleRoute: function() {
        let hash = window.location.hash || '#/dashboard';
        
        // Remove leading #
        if (hash.startsWith('#')) {
            hash = hash.substring(1);
        }
        
        // Ensure starts with /
        if (!hash.startsWith('/')) {
            hash = '/' + hash;
        }
        
        // Find matching route
        let route = this.routes[hash];
        
        // Default to dashboard if route not found
        if (!route) {
            route = this.routes['/dashboard'];
            window.location.hash = '#/dashboard';
        }
        
        // Update current route
        this.currentRoute = hash;
        
        // Load page
        this.loadPage(route);
        
        // Update active nav link
        this.updateNavActiveState(hash);
    },
    
    loadPage: function(route) {
        const pageContent = document.getElementById('pageContent');
        const pageTitle = document.getElementById('pageTitle');
        
        // Show loading state
        pageContent.innerHTML = `
            <div class="loading">
                <div class="loading-spinner"></div>
                <p>Загрузка...</p>
            </div>
        `;
        
        // Update page title
        pageTitle.textContent = route.title;
        
        // Load HTML content
        fetch(route.file)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Страница не найдена');
                }
                return response.text();
            })
            .then(html => {
                pageContent.innerHTML = html;
                
                // Load page-specific script
                if (route.script) {
                    this.loadScript(route.script);
                }
                
                // Initialize page
                if (typeof window.initPage === 'function') {
                    window.initPage();
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки страницы:', error);
                pageContent.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Ошибка загрузки</h3>
                        <p>Не удалось загрузить страницу. Пожалуйста, попробуйте еще раз.</p>
                        <button class="btn btn-primary mt-3" onclick="location.reload()">
                            Обновить страницу
                        </button>
                    </div>
                `;
            });
    },
    
    loadScript: function(src) {
        // Remove existing script if any
        const existingScript = document.querySelector(`script[src="${src}"]`);
        if (existingScript) {
            existingScript.remove();
        }
        
        // Create new script element
        const script = document.createElement('script');
        script.src = src;
        script.defer = true;
        
        // Handle script load
        script.onload = () => {
            console.log(`Script loaded: ${src}`);
        };
        
        script.onerror = () => {
            console.error(`Error loading script: ${src}`);
        };
        
        // Add to document
        document.body.appendChild(script);
    },
    
    updateNavActiveState: function(route) {
        // Remove active class from all nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to current route link
        const navLink = document.querySelector(`.nav-link[href="#${route}"]`);
        if (navLink) {
            navLink.classList.add('active');
        }
    },
    
    navigate: function(path) {
        window.location.hash = path;
    },
    
    getCurrentRoute: function() {
        return this.currentRoute;
    }
};

// Initialize router when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    Router.init();
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Router;
}