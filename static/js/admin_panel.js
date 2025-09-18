class AdminPanel {
    constructor() {
        this.init();
    }

    async init() {
        await this.loadStats();
        this.setupEventListeners();
    }

    async loadStats() {
        try {
            const response = await this.apiCall('admin/stats');
            this.updateStatsUI(response);
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showNotification('Ошибка загрузки статистики', 'error');
        }
    }

    setupEventListeners() {
        // Форма добавления товара
        document.getElementById('addItemForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addShopItem();
        });

        // Форма добавления валюты
        document.getElementById('addCurrencyForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addCurrency();
        });

        // Форма создания категории
        document.getElementById('addCategoryForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addCategory();
        });

        // Кнопка загрузки товаров
        document.getElementById('loadItemsBtn').addEventListener('click', () => {
            this.loadShopItems();
        });
    }

    async addShopItem() {
        const formData = new FormData(document.getElementById('addItemForm'));
        
        try {
            const response = await this.apiCall('admin/shop/add_item', {
                method: 'POST',
                body: JSON.stringify({
                    name: formData.get('name'),
                    type: formData.get('type'),
                    category: formData.get('category'),
                    price: parseInt(formData.get('price')),
                    rarity: formData.get('rarity'),
                    data: JSON.parse(formData.get('data') || '{}'),
                    is_active: formData.get('is_active') === 'true'
                })
            });

            if (response.success) {
                this.showNotification('Товар добавлен успешно!', 'success');
                document.getElementById('addItemForm').reset();
            } else {
                this.showNotification('Ошибка: ' + response.message, 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка сети', 'error');
        }
    }

    async addCurrency() {
        const formData = new FormData(document.getElementById('addCurrencyForm'));
        
        try {
            const response = await this.apiCall('admin/add_currency', {
                method: 'POST',
                body: JSON.stringify({
                    username: formData.get('username'),
                    amount: parseInt(formData.get('amount')),
                    reason: formData.get('reason') || 'admin_grant'
                })
            });

            if (response.success) {
                this.showNotification('Валюта добавлена успешно!', 'success');
                document.getElementById('addCurrencyForm').reset();
            } else {
                this.showNotification('Ошибка: ' + response.message, 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка сети', 'error');
        }
    }

    async addCategory() {
        const formData = new FormData(document.getElementById('addCategoryForm'));
        
        try {
            const response = await this.apiCall('admin/shop/categories', {
                method: 'POST',
                body: JSON.stringify({
                    name: formData.get('name'),
                    description: formData.get('description'),
                    icon: formData.get('icon')
                })
            });

            if (response.success) {
                this.showNotification('Категория создана успешно!', 'success');
                document.getElementById('addCategoryForm').reset();
            } else {
                this.showNotification('Ошибка: ' + response.message, 'error');
            }
        } catch (error) {
            this.showNotification('Ошибка сети', 'error');
        }
    }

    async loadShopItems() {
        try {
            const response = await this.apiCall('admin/shop/items');
            this.displayShopItems(response);
        } catch (error) {
            this.showNotification('Ошибка загрузки товаров', 'error');
        }
    }

    displayShopItems(items) {
        const container = document.getElementById('shopItemsList');
        if (!container) return;

        if (!items || items.length === 0) {
            container.innerHTML = '<div class="empty-state">Товаров нет</div>';
            return;
        }

        let html = items.map(item => `
            <div class="admin-item-card">
                <h4>${item.name}</h4>
                <p>Тип: ${item.type} | Цена: ${item.price} ₲</p>
                <p>Редкость: ${item.rarity} | Активен: ${item.is_active ? 'Да' : 'Нет'}</p>
                <button onclick="adminPanel.editItem(${item.id})">Редактировать</button>
                <button onclick="adminPanel.deleteItem(${item.id})">Удалить</button>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    updateStatsUI(stats) {
        document.getElementById('totalUsers').textContent = stats.total_users;
        document.getElementById('totalTransactions').textContent = stats.total_transactions;
        document.getElementById('totalItems').textContent = stats.total_items;
    }

    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch('/api/' + endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                credentials: 'include',
                ...options,
            });

            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            background: ${type === 'success' ? '#4ecdc4' : type === 'error' ? '#ff6b6b' : '#1976d2'};
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Инициализация при загрузке
let adminPanel;
document.addEventListener('DOMContentLoaded', function() {
    adminPanel = new AdminPanel();
});