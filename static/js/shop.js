let currentItems = [];
let selectedCategory = 'all';

async function loadShopItems() {
    try {
        showLoading();
        const response = await fetch('/api/shop/items');
        const items = await response.json();
        
        currentItems = items;
        displayItems(items);
        hideLoading();
        updateBalance();
    } catch (error) {
        console.error('Error loading shop items:', error);
        hideLoading();
    }
}

function displayItems(items) {
    const container = document.getElementById('shopItems');
    container.innerHTML = '';

    const filteredItems = selectedCategory === 'all' 
        ? items 
        : items.filter(item => item.category === selectedCategory);

    if (filteredItems.length === 0) {
        container.innerHTML = '<div class="no-items">Товары не найдены</div>';
        return;
    }

    filteredItems.forEach(item => {
        const itemElement = createItemElement(item);
        container.appendChild(itemElement);
    });
}

function createItemElement(item) {
    const div = document.createElement('div');
    div.className = 'shop-item';
    
    div.innerHTML = `
        <div class="item-header">
            <span class="item-rarity rarity-${item.rarity}">${getRarityName(item.rarity)}</span>
            ${item.owned ? '<span class="owned-badge">Куплено</span>' : ''}
        </div>
        
        <h3>${item.name}</h3>
        <p>${getCategoryName(item.category)}</p>
        
        <div class="item-price">
            ${item.price} <i class="fas fa-coins"></i>
        </div>
        
        <div class="item-actions">
            ${!item.owned ? `
                <button class="btn-primary" onclick="buyItem(${item.id})" 
                    ${getUserBalance() < item.price ? 'disabled' : ''}>
                    Купить
                </button>
            ` : `
                <button class="btn-primary" onclick="equipItem(${item.id})">
                    Надеть
                </button>
            `}
        </div>
    `;
    
    return div;
}

async function buyItem(itemId) {
    const item = currentItems.find(i => i.id === itemId);
    if (!item) return;

    document.getElementById('modalItemName').textContent = item.name;
    document.getElementById('modalItemPrice').textContent = item.price;
    document.getElementById('purchaseModal').style.display = 'block';
    
    window.confirmPurchase = async function() {
        try {
            const response = await fetch(`/api/shop/buy/${itemId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Покупка успешна!');
                closeModal();
                loadShopItems();
            } else {
                alert('Ошибка: ' + result.message);
            }
        } catch (error) {
            alert('Ошибка при покупке');
        }
    };
}

function closeModal() {
    document.getElementById('purchaseModal').style.display = 'none';
}

async function equipItem(itemId) {
    try {
        const response = await fetch(`/api/profile/equip/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Предмет надет!');
        } else {
            alert('Ошибка: ' + result.message);
        }
    } catch (error) {
        alert('Ошибка при надевании предмета');
    }
}

async function updateBalance() {
    try {
        const response = await fetch('/api/currency/balance');
        const data = await response.json();
        document.getElementById('userBalance').textContent = data.balance;
    } catch (error) {
        console.error('Error updating balance:', error);
    }
}

function getRarityName(rarity) {
    const names = {
        'common': 'Обычный',
        'rare': 'Редкий',
        'epic': 'Эпический',
        'legendary': 'Легендарный'
    };
    return names[rarity] || rarity;
}

function getCategoryName(category) {
    const names = {
        'themes': 'Тема',
        'avatars': 'Аватар',
        'banners': 'Баннер',
        'badges': 'Бейдж',
        'effects': 'Эффект',
        'animations': 'Анимация'
    };
    return names[category] || category;
}

function getUserBalance() {
    const balanceEl = document.getElementById('userBalance');
    return parseInt(balanceEl.textContent) || 0;
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}


document.addEventListener('DOMContentLoaded', function() {
    loadShopItems();
    

    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedCategory = this.dataset.category;
            displayItems(currentItems);
        });
    });
    

    document.getElementById('searchInput').addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const filtered = currentItems.filter(item => 
            item.name.toLowerCase().includes(searchTerm) ||
            item.category.toLowerCase().includes(searchTerm)
        );
        displayItems(filtered);
    });
});

let shopItems = [];
let userInventory = [];
let currentShopCategory = 'all';


async function loadShop() {
    try {
        showShopLoading();
        

        const [itemsResponse, inventoryResponse, balanceResponse] = await Promise.all([
            fetch('/api/shop/items'),
            fetch('/api/profile/inventory'),
            fetch('/api/currency/balance')
        ]);

        if (!itemsResponse.ok || !inventoryResponse.ok || !balanceResponse.ok) {
            throw new Error('Ошибка загрузки данных магазина');
        }

        shopItems = await itemsResponse.json();
        userInventory = await inventoryResponse.json();
        const balanceData = await balanceResponse.json();


        updateAllBalances(balanceData.balance);
        

        displayShopItems();
        displayInventory();
        
        hideShopLoading();
    } catch (error) {
        console.error('Error loading shop:', error);
        showError('Ошибка загрузки магазина');
        hideShopLoading();
    }
}


function displayShopItems() {
    const grid = document.getElementById('shopGrid');
    if (!grid) return;

    const filteredItems = filterShopItems();
    
    if (filteredItems.length === 0) {
        grid.innerHTML = '<div class="no-items">Товары не найдены</div>';
        return;
    }

    grid.innerHTML = filteredItems.map(item => createShopItemHTML(item)).join('');
}


function filterShopItems() {
    const searchTerm = document.getElementById('shopSearch')?.value.toLowerCase() || '';
    
    return shopItems.filter(item => {
        const matchesCategory = currentShopCategory === 'all' || item.category === currentShopCategory;
        const matchesSearch = item.name.toLowerCase().includes(searchTerm) || 
                             item.category.toLowerCase().includes(searchTerm);
        return matchesCategory && matchesSearch;
    });
}


function createShopItemHTML(item) {
    const isOwned = userInventory.some(invItem => invItem.id === item.id);
    const canAfford = getCurrentBalance() >= item.price;
    
    return `
        <div class="shop-item">
            <div class="item-header">
                <span class="item-rarity rarity-${item.rarity}">${getRarityName(item.rarity)}</span>
                ${isOwned ? '<span class="owned-badge">Куплено</span>' : ''}
            </div>
            
            <h4>${item.name}</h4>
            <p>${getCategoryName(item.category)}</p>
            
            <div class="item-price">
                ${item.price} <i class="fas fa-coins"></i>
            </div>
            
            <div class="item-actions">
                ${!isOwned ? `
                    <button class="btn-primary" onclick="openPurchaseModal(${item.id})" 
                        ${!canAfford ? 'disabled' : ''}>
                        Купить
                    </button>
                ` : `
                    <button class="btn-primary" onclick="equipItem(${item.id})">
                        Надеть
                    </button>
                `}
            </div>
        </div>
    `;
}

function openPurchaseModal(itemId) {
    const item = shopItems.find(i => i.id === itemId);
    if (!item) return;

    document.getElementById('purchaseItemName').textContent = item.name;
    document.getElementById('purchaseItemPrice').textContent = item.price;
    document.getElementById('purchaseBalance').textContent = getCurrentBalance();
    
    window.currentPurchaseItemId = itemId;
    openModal('purchaseModal');
}

async function confirmPurchase() {
    try {
        const response = await fetch(`/api/shop/buy/${window.currentPurchaseItemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        
        if (result.success) {
            showSuccess('Покупка успешна!');
            closeModal('purchaseModal');
            await loadShop();
        } else {
            showError(result.message || 'Ошибка при покупке');
        }
    } catch (error) {
        showError('Ошибка при покупке');
    }
}

async function equipItem(itemId) {
    try {
        const response = await fetch(`/api/profile/equip/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        
        if (result.success) {
            showSuccess('Предмет надет!');
            await loadShop();
        } else {
            showError(result.message || 'Ошибка');
        }
    } catch (error) {
        showError('Ошибка при надевании предмета');
    }
}


function displayInventory() {
    const grid = document.getElementById('inventoryGrid');
    if (!grid) return;

    if (userInventory.length === 0) {
        grid.innerHTML = '<div class="no-items">Инвентарь пуст</div>';
        return;
    }

    grid.innerHTML = userInventory.map(item => createInventoryItemHTML(item)).join('');
}

function createInventoryItemHTML(item) {
    return `
        <div class="inventory-item ${item.equipped ? 'equipped' : ''}">
            <h4>${item.name}</h4>
            <p>${getCategoryName(item.type)}</p>
            <p>Куплен: ${new Date(item.purchased_at).toLocaleDateString()}</p>
            ${item.equipped ? '<span class="owned-badge">Надет</span>' : ''}
        </div>
    `;
}

async function claimDailyReward() {
    try {
        const response = await fetch('/api/daily_reward', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        
        if (result.success) {
            document.getElementById('rewardAmount').textContent = result.amount;
            openModal('rewardModal');
            updateAllBalances(result.new_balance);
        } else {
            showError(result.message || 'Уже получали награду сегодня');
        }
    } catch (error) {
        showError('Ошибка при получении награды');
    }
}


function updateAllBalances(balance) {
    const balanceElements = [
        'headerBalance',
        'shopBalance',
        'welcomeCurrency',
        'purchaseBalance'
    ];
    
    balanceElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.textContent = balance;
    });
}

function getCurrentBalance() {
    return parseInt(document.getElementById('headerBalance')?.textContent || 0);
}


function getRarityName(rarity) {
    const names = {
        'common': 'Обычный',
        'rare': 'Редкий',
        'epic': 'Эпический',
        'legendary': 'Легендарный'
    };
    return names[rarity] || rarity;
}

function getCategoryName(category) {
    const names = {
        'theme': 'Тема',
        'avatar': 'Аватар',
        'banner': 'Баннер',
        'badge': 'Бейдж',
        'effect': 'Эффект',
        'animation': 'Анимация'
    };
    return names[category] || category;
}

function showShopLoading() {
    const grid = document.getElementById('shopGrid');
    if (grid) grid.innerHTML = '<div class="loading">Загрузка...</div>';
}

function hideShopLoading() {

}


function initShopTab() {
    loadShop();
    

    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentShopCategory = this.dataset.category;
            displayShopItems();
        });
    });
    

    const searchInput = document.getElementById('shopSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            displayShopItems();
        }, 300));
    }
}


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


document.addEventListener('DOMContentLoaded', function() {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function(tab) {
        originalSwitchTab(tab);
        if (tab === 'shop') {
            initShopTab();
        }
    };
});

async function initShopTab() {
    try {
        await loadShop();
        

        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentShopCategory = this.dataset.category;
                displayShopItems();
            });
        });
        

        const searchInput = document.getElementById('shopSearch');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(() => {
                displayShopItems();
            }, 300));
        }
    } catch (error) {
        console.error('Error initializing shop:', error);
    }
}

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