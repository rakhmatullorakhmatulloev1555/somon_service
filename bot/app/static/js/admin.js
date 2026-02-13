
        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebar = document.querySelector('.sidebar');
        
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
        
        // Drag and drop functionality
        document.addEventListener('DOMContentLoaded', () => {
            const tasks = document.querySelectorAll('.task');
            const columns = document.querySelectorAll('.tasks');
            
            let draggedTask = null;
            
            tasks.forEach(task => {
                task.addEventListener('dragstart', () => {
                    draggedTask = task;
                    setTimeout(() => {
                        task.classList.add('dragging');
                    }, 0);
                });
                
                task.addEventListener('dragend', () => {
                    draggedTask = null;
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
                
                column.addEventListener('drop', () => {
                    if (draggedTask) {
                        column.appendChild(draggedTask);
                        column.classList.remove('drag-over');
                        // Update the backend with new task position
                        updateTaskPosition(draggedTask.dataset.id, column.id);
                    }
                });
            });
        });
