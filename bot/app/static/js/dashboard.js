// Dashboard Module
function initPage() {
    // Initialize dashboard page
    updateDashboardStats();
    loadKanbanBoard();
    loadRecentActivity();
    
    // Add event listeners
    document.getElementById('newOrderBtn').addEventListener('click', createNewOrder);
    document.getElementById('filterBtn').addEventListener('click', toggleFilters);
    document.getElementById('applyFilterBtn').addEventListener('click', applyFilters);
    document.getElementById('viewAllActivityBtn').addEventListener('click', viewAllActivity);
}

function updateDashboardStats() {
    const stats = getOrderStats();
    
    document.getElementById('newOrdersCount').textContent = stats.new;
    document.getElementById('repairOrdersCount').textContent = stats.repair;
    document.getElementById('doneOrdersCount').textContent = stats.done;
    document.getElementById('cancelledOrdersCount').textContent = stats.cancelled;
}

function loadKanbanBoard() {
    const board = document.getElementById('kanbanBoard');
    if (!board) return;
    
    const columns = {
        new: AppState.orders.filter(o => o.status === 'new'),
        repair: AppState.orders.filter(o => o.status === 'repair'),
        done: AppState.orders.filter(o => o.status === 'done'),
        cancelled: AppState.orders.filter(o => o.status === 'cancelled')
    };
    
    board.innerHTML = `
        <div class="column new" id="new-column">
            <div class="column-header">
                <div class="column-title">
                    <i class="fas fa-plus-circle"></i>
                    Новые
                    <span class="column-count">${columns.new.length}</span>
                </div>
                <i class="fas fa-ellipsis-h" style="color: var(--gray-400); cursor: pointer;"></i>
            </div>
            <div class="tasks" id="new-tasks">
                ${columns.new.length > 0 ? 
                    columns.new.map(order => renderTask(order)).join('') : 
                    '<div class="empty-column"><i class="fas fa-clipboard-list"></i><p>Нет новых заявок</p></div>'
                }
            </div>
        </div>
        
        <div class="column repair" id="repair-column">
            <div class="column-header">
                <div class="column-title">
                    <i class="fas fa-tools"></i>
                    В ремонте
                    <span class="column-count">${columns.repair.length}</span>
                </div>
                <i class="fas fa-ellipsis-h" style="color: var(--gray-400); cursor: pointer;"></i>
            </div>
            <div class="tasks" id="repair-tasks">
                ${columns.repair.length > 0 ? 
                    columns.repair.map(order => renderTask(order)).join('') : 
                    '<div class="empty-column"><i class="fas fa-clipboard-list"></i><p>Нет заявок в ремонте</p></div>'
                }
            </div>
        </div>
        
        <div class="column done" id="done-column">
            <div class="column-header">
                <div class="column-title">
                    <i class="fas fa-check-circle"></i>
                    Готово
                    <span class="column-count">${columns.done.length}</span>
                </div>
                <i class="fas fa-ellipsis-h" style="color: var(--gray-400); cursor: pointer;"></i>
            </div>
            <div class="tasks" id="done-tasks">
                ${columns.done.length > 0 ? 
                    columns.done.map(order => renderTask(order)).join('') : 
                    '<div class="empty-column"><i class="fas fa-clipboard-list"></i><p>Нет готовых заявок</p></div>'
                }
            </div>
        </div>
    `;
    
    // Add event listeners to tasks
    document.querySelectorAll('.task').forEach(task => {
        task.addEventListener('click', (e) => {
            if (!e.target.closest('.task-action')) {
                const taskId = task.getAttribute('data-id');
                showTaskDetails(taskId);
            }
        });
    });
    
    // Initialize drag and drop
    initDragAndDrop();
}

function renderTask(order) {
    const priorityClass = order.priority || 'medium';
    const statusClass = order.status === 'repair' ? 'repair' : order.status === 'done' ? 'done' : '';
    const initials = getInitials(order.client);
    
    return `
        <div class="task ${statusClass}" draggable="true" data-id="${order.id}">
            <div class="task-header">
                <div class="task-id">#${order.number}</div>
                <div class="task-priority ${priorityClass}">${getPriorityText(order.priority)}</div>
            </div>
            <div class="task-device">${order.device}</div>
            <div class="task-problem">${order.problem}</div>
            <div class="task-client">
                <div class="client-avatar">${initials}</div>
                <div class="client-name">${order.client}</div>
            </div>
            <div class="task-footer">
                <div class="task-date">
                    <i class="far fa-clock"></i>
                    ${formatDate(order.date)}
                </div>
                <div class="task-actions">
                    <button class="task-action edit" onclick="editTask(${order.id})">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                    <button class="task-action view" onclick="showTaskDetails(${order.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

function initDragAndDrop() {
    const tasks = document.querySelectorAll('.task');
    const columns = document.querySelectorAll('.tasks');
    
    tasks.forEach(task => {
        task.addEventListener('dragstart', () => {
            task.classList.add('dragging');
        });
        
        task.addEventListener('dragend', () => {
            task.classList.remove('dragging');
        });
    });
    
    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
            column.classList.add('drag-over');
        });
        
        column.addEventListener('dragleave', () => {
            column.classList.remove('drag-over');
        });
        
        column.addEventListener('drop', (e) => {
            e.preventDefault();
            column.classList.remove('drag-over');
            
            const taskId = document.querySelector('.dragging')?.getAttribute('data-id');
            const columnId = column.parentElement.id;
            
            if (!taskId) return;
            
            let newStatus = 'new';
            if (columnId.includes('repair')) newStatus = 'repair';
            if (columnId.includes('done')) newStatus = 'done';
            if (columnId.includes('cancelled')) newStatus = 'cancelled';
            
            // Update order status
            const orderIndex = AppState.orders.findIndex(o => o.id == taskId);
            if (orderIndex !== -1) {
                AppState.orders[orderIndex].status = newStatus;
                
                showNotification(`Статус заявки #${AppState.orders[orderIndex].number} изменен`, 'success');
                
                // Update stats and reload board
                updateDashboardStats();
                loadKanbanBoard();
            }
        });
    });
}

function loadRecentActivity() {
    const tbody = document.getElementById('activityTableBody');
    if (!tbody) return;
    
    // Generate recent activity from orders
    const activities = [];
    
    AppState.orders.forEach(order => {
        activities.push({
            time: order.date,
            event: `Создана заявка #${order.number}`,
            order: order.number,
            user: 'Система'
        });
        
        if (order.master) {
            activities.push({
                time: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
                event: `Назначен мастер: ${order.master}`,
                order: order.number,
                user: 'Администратор'
            });
        }
    });
    
    // Sort by time (newest first) and take first 5
    activities.sort((a, b) => new Date(b.time) - new Date(a.time));
    const recentActivities = activities.slice(0, 5);
    
    tbody.innerHTML = recentActivities.map(activity => `
        <tr>
            <td>${formatDate(activity.time)}</td>
            <td>${activity.event}</td>
            <td>#${activity.order}</td>
            <td>${activity.user}</td>
        </tr>
    `).join('');
}

function toggleFilters() {
    const filters = document.getElementById('dashboardFilters');
    filters.style.display = filters.style.display === 'none' ? 'flex' : 'none';
}

function applyFilters() {
    const priority = document.getElementById('priorityFilter').value;
    const master = document.getElementById('masterFilter').value;
    
    // Apply filters to kanban board
    showNotification('Фильтры применены', 'success');
    toggleFilters();
}

function createNewOrder() {
    // Navigate to orders page with new order form
    Router.navigate('/orders?action=create');
}

function viewAllActivity() {
    // Navigate to activity log page
    showNotification('Функция в разработке', 'info');
}

function editTask(taskId) {
    showTaskDetails(taskId);
}

function showTaskDetails(taskId) {
    const order = AppState.orders.find(o => o.id == taskId);
    if (!order) return;
    
    // Create modal for task details
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal" style="max-width: 600px;">
            <div class="modal-header">
                <h2 class="modal-title">Заявка #${order.number}</h2>
                <button class="modal-close" id="closeTaskModal">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">Устройство</label>
                    <div class="form-control-static">${order.device}</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Проблема</label>
                    <div class="form-control-static">${order.problem}</div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Клиент</label>
                        <div class="form-control-static">${order.client}</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Приоритет</label>
                        <div class="form-control-static">${getPriorityText(order.priority)}</div>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Статус</label>
                        <select class="form-control" id="taskStatus">
                            <option value="new" ${order.status === 'new' ? 'selected' : ''}>Новая</option>
                            <option value="repair" ${order.status === 'repair' ? 'selected' : ''}>В ремонте</option>
                            <option value="done" ${order.status === 'done' ? 'selected' : ''}>Готово</option>
                            <option value="cancelled" ${order.status === 'cancelled' ? 'selected' : ''}>Отменено</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Мастер</label>
                        <select class="form-control" id="taskMaster">
                            <option value="">Не назначен</option>
                            ${AppState.masters.map(m => `<option value="${m.name}" ${order.master === m.name ? 'selected' : ''}>${m.name}</option>`).join('')}
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Комментарий</label>
                    <textarea class="form-control" id="taskComment" rows="3">${order.comment || ''}</textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" id="cancelTaskBtn">Закрыть</button>
                <button class="btn btn-primary" id="saveTaskBtn">Сохранить</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    const closeBtn = modal.querySelector('#closeTaskModal');
    const cancelBtn = modal.querySelector('#cancelTaskBtn');
    const saveBtn = modal.querySelector('#saveTaskBtn');
    
    const closeModal = () => modal.remove();
    
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    
    saveBtn.addEventListener('click', () => {
        const orderIndex = AppState.orders.findIndex(o => o.id == taskId);
        if (orderIndex !== -1) {
            AppState.orders[orderIndex].status = modal.querySelector('#taskStatus').value;
            AppState.orders[orderIndex].master = modal.querySelector('#taskMaster').value;
            AppState.orders[orderIndex].comment = modal.querySelector('#taskComment').value;
            
            showNotification('Заявка обновлена', 'success');
            
            // Update dashboard
            updateDashboardStats();
            loadKanbanBoard();
            
            closeModal();
        }
    });
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// Make functions available globally
window.initPage = initPage;
window.editTask = editTask;
window.showTaskDetails = showTaskDetails;