// profile.js - полный рабочий код с поддержкой GIF баннеров

// ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
let currentFriendsTab = 'all';
let friendsList = [];
let audioPlayer = null;
let currentItems = [];
let selectedCategory = 'all';
let currentPurchaseItem = null;

// ========== КОНСТАНТЫ ==========
const standardBadges = [
    { icon: 'music', text: 'Музыкант', color: '#007bff' },
    { icon: 'heart', text: 'Любитель музыки', color: '#e83e8c' },
    { icon: 'star', text: 'Активный слушатель', color: '#ffc107' }
];

// ========== ИНИЦИАЛИЗАЦИЯ ==========
document.addEventListener('DOMContentLoaded', function() {
    loadProfileData();
    setupProfileForm();
    setupAvatarUpload();
    setupTokenValidation();
    initAudioPlayer();
    loadFriends();
    loadActivityFeed();
    updateBalance();
    initShopEventListeners();
    loadUserSettings();
    loadEquippedItems();
    
    // Добавляем контейнер для бейджей в баннер
    const bannerOverlay = document.querySelector('.banner-overlay');
    if (bannerOverlay && !document.getElementById('userBadges')) {
        const badgesContainer = document.createElement('div');
        badgesContainer.id = 'userBadges';
        badgesContainer.className = 'user-badges';
        bannerOverlay.appendChild(badgesContainer);
    }
});

// ========== ОСНОВНЫЕ ФУНКЦИИ ПРОФИЛЯ ==========
function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.profile-tab').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(`tab-${tabName}`).classList.add('active');
    const tabIndex = ['main', 'shop', 'activity', 'inventory'].indexOf(tabName);
    document.querySelectorAll('.profile-tab')[tabIndex].classList.add('active');
    
    if (tabName === 'shop') loadShopItems();
    else if (tabName === 'inventory') loadUserInventory();
}

async function loadProfileData() {
    try {
        const response = await fetch('/api/profile');
        if (response.ok) {
            const profile = await response.json();
            updateProfileForm(profile);
            loadUserStats();
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        showNotification('Ошибка загрузки профиля', 'error');
    }
}

function updateProfileForm(profile) {
    if (profile && profile.local) {
        document.getElementById('display_name').value = profile.local.display_name || '';
        document.getElementById('bio').value = profile.local.bio || '';
        document.getElementById('avatar_url').value = profile.local.avatar_url || '';
        document.getElementById('yandex_token').value = profile.local.yandex_token || '';
        document.getElementById('vk_token').value = profile.local.vk_token || '';
        
        document.getElementById('profileDisplayName').textContent = profile.local.display_name || profile.local.username;
        document.getElementById('profileUsername').textContent = '@' + profile.local.username;
        document.getElementById('bannerUsername').textContent = profile.local.display_name || profile.local.username;
        document.getElementById('sidebarUsername').textContent = profile.local.display_name || profile.local.username;
        
        if (profile.local.bio) {
            document.getElementById('bannerBio').textContent = profile.local.bio;
        }
        
        const avatarPreview = document.getElementById('avatarPreview');
        if (avatarPreview && profile.local.avatar_url) {
            avatarPreview.innerHTML = `<img src="${profile.local.avatar_url}" alt="Avatar" style="width:100%;height:100%;border-radius:50%;object-fit:cover">`;
        }
        
        if (profile.local.created_at) {
            document.getElementById('joinDate').textContent = new Date(profile.local.created_at).toLocaleDateString('ru-RU');
        }
        
        updateTokenStatus(profile);
    }
}

function setupProfileForm() {
    const form = document.getElementById('profileForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            display_name: formData.get('display_name'),
            bio: formData.get('bio'),
            avatar_url: formData.get('avatar_url'),
            yandex_token: formData.get('yandex_token'),
            vk_token: formData.get('vk_token')
        };
        
        const avatarInput = document.getElementById('avatarInput');
        if (avatarInput && avatarInput.files[0]) {
            data.avatar_file = await readFileAsDataURL(avatarInput.files[0]);
        }
        
        try {
            const response = await fetch('/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const result = await response.json();
                showNotification(result.message, 'success');
                loadProfileData();
            } else {
                throw new Error('Ошибка сохранения');
            }
        } catch (error) {
            showNotification('Ошибка при сохранении профиля', 'error');
        }
    });
}

function setupAvatarUpload() {
    const avatarInput = document.getElementById('avatarInput');
    const avatarPreview = document.getElementById('avatarPreview');
    
    if (avatarInput && avatarPreview) {
        avatarInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (!file.type.startsWith('image/')) {
                    showNotification('Выберите файл изображения', 'error');
                    return;
                }
                
                if (file.size > 5 * 1024 * 1024) {
                    showNotification('Файл слишком большой (макс. 5MB)', 'error');
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    avatarPreview.innerHTML = `
                        <img src="${e.target.result}" alt="Аватар" 
                             style="width:100%;height:100%;border-radius:50%;object-fit:cover">
                    `;
                    document.getElementById('avatar_url').value = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

function setupTokenValidation() {
    const yandexTokenInput = document.getElementById('yandex_token');
    const vkTokenInput = document.getElementById('vk_token');
    
    [yandexTokenInput, vkTokenInput].forEach((input, index) => {
        if (input) {
            const service = index === 0 ? 'yandex' : 'vk';
            const validateBtn = document.createElement('button');
            validateBtn.type = 'button';
            validateBtn.innerHTML = '<i class="fas fa-check"></i> Проверить';
            validateBtn.className = 'validate-btn';
            validateBtn.onclick = () => validateAndSaveToken(service, input.value);
            input.parentNode.appendChild(validateBtn);
        }
    });
}

async function validateAndSaveToken(service, token) {
    if (!token) {
        showNotification('Введите токен для проверки', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/save_token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token, service: service })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            loadProfileData();
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Ошибка при проверке токена', 'error');
    }
}

function updateTokenStatus(profile) {
    const yandexStatus = document.getElementById('yandexStatus');
    const vkStatus = document.getElementById('vkStatus');
    
    if (yandexStatus) {
        if (profile.yandex) {
            yandexStatus.innerHTML = `
                <div class="status-connected">
                    <i class="fas fa-check-circle" style="color:var(--success)"></i>
                    <span>Подключено к Яндекс.Музыке</span>
                    <div style="font-size:0.8em;margin-top:4px;color:var(--text-secondary)">
                        ${profile.yandex.name} • ${profile.yandex.premium ? 'Premium' : 'Бесплатный'}
                    </div>
                </div>
            `;
        } else if (profile.local.yandex_token_set) {
            yandexStatus.innerHTML = `
                <div class="status-error">
                    <i class="fas fa-exclamation-triangle" style="color:var(--warning)"></i>
                    <span>Ошибка подключения. Проверьте токен.</span>
                </div>
            `;
        } else {
            yandexStatus.innerHTML = `
                <div class="status-disconnected">
                    <i class="fas fa-plug" style="color:var(--text-secondary)"></i>
                    <span>Не подключено к Яндекс.Музыке</span>
                </div>
            `;
        }
    }
    
    if (vkStatus) {
        if (profile.vk) {
            vkStatus.innerHTML = `
                <div class="status-connected">
                    <i class="fas fa-check-circle" style="color:var(--success)"></i>
                    <span>Подключено к VK Музыке</span>
                    <div style="font-size:0.8em;margin-top:4px;color:var(--text-secondary)">
                        ${profile.vk.full_name}
                    </div>
                </div>
            `;
        } else if (profile.local.vk_token_set) {
            vkStatus.innerHTML = `
                <div class="status-error">
                    <i class="fas fa-exclamation-triangle" style="color:var(--warning)"></i>
                    <span>Ошибка подключения. Проверьте токен.</span>
                </div>
            `;
        } else {
            vkStatus.innerHTML = `
                <div class="status-disconnected">
                    <i class="fas fa-plug" style="color:var(--text-secondary)"></i>
                    <span>Не подключено к VK Музыке</span>
                </div>
            `;
        }
    }
}

async function loadUserStats() {
    try {
        const response = await fetch('/api/stats');
        if (response.ok) {
            const stats = await response.json();
            updateUserStats(stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateUserStats(stats) {
    if (stats.total_liked_tracks) {
        document.getElementById('totalTracks').textContent = stats.total_liked_tracks;
    }
    
    if (stats.top_genre) {
        document.getElementById('topGenre').textContent = stats.top_genre;
    }
    
    if (stats.top_artist) {
        document.getElementById('topArtist').textContent = stats.top_artist;
    }
}

// ========== ФУНКЦИИ МАГАЗИНА ==========
async function loadShopItems() {
    try {
        showLoading('shopItems', 'Загрузка товаров...');
        const response = await fetch('/api/shop/items');
        if (response.ok) {
            currentItems = await response.json();
            displayItems(currentItems);
        }
    } catch (error) {
        console.error('Error loading shop items:', error);
        showNotification('Ошибка загрузки магазина', 'error');
    }
}

function displayItems(items) {
    const container = document.getElementById('shopItems');
    const filtered = selectedCategory === 'all' 
        ? items 
        : items.filter(item => item.category === selectedCategory);
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="empty-state">Товары не найдены</div>';
        return;
    }
    
    let html = '';
    filtered.forEach(item => {
        html += `
        <div class="shop-item">
            <div class="item-header">
                <span class="item-rarity rarity-${item.rarity}">${item.rarity}</span>
                ${item.owned ? '<span class="owned-badge">Куплено</span>' : ''}
            </div>
            <h3>${item.name}</h3>
            <p>${getItemTypeName(item.type)}</p>
            ${item.data && item.data.animation ? '<span class="gif-badge">GIF</span>' : ''}
            <div class="item-price">${item.price} <i class="fas fa-coins"></i></div>
            <div class="item-actions">
                ${item.owned ? 
                    `<button class="btn-secondary" disabled>Уже куплено</button>` :
                    `<button class="btn-primary" onclick="openPurchaseModal(${item.id})" 
                     ${getUserBalance() < item.price ? 'disabled' : ''}>
                        Купить
                    </button>`
                }
            </div>
        </div>`;
    });
    
    container.innerHTML = html;
}

function initShopEventListeners() {
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedCategory = this.dataset.category;
            displayItems(currentItems);
        });
    });
}

function openPurchaseModal(itemId) {
    const item = currentItems.find(i => i.id === itemId);
    if (!item) return;
    
    currentPurchaseItem = item;
    document.getElementById('modalItemName').textContent = item.name;
    document.getElementById('modalItemPrice').textContent = item.price;
    document.getElementById('purchaseBalance').textContent = getUserBalance();
    
    openModal('purchaseModal');
}

async function confirmPurchase() {
    if (!currentPurchaseItem) return;
    
    try {
        const response = await fetch(`/api/shop/buy/${currentPurchaseItem.id}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message, 'success');
            closeModal('purchaseModal');
            updateBalance();
            loadShopItems();
            loadUserInventory();
            
            // Перезагружаем экипированные предметы
            loadEquippedItems();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Ошибка покупки', 'error');
        }
    } catch (error) {
        showNotification('Ошибка покупки', 'error');
    }
}

// ========== ФУНКЦИИ ИНВЕНТАРЯ ==========
async function loadUserInventory() {
    try {
        showLoading('inventoryGrid', 'Загрузка инвентаря...');
        const response = await fetch('/api/profile/inventory');
        if (response.ok) {
            const inventory = await response.json();
            displayInventory(inventory);
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
        showNotification('Ошибка загрузки инвентаря', 'error');
    }
}

function displayInventory(items) {
    const container = document.getElementById('inventoryGrid');
    
    if (!items || items.length === 0) {
        container.innerHTML = '<div class="empty-state">Инвентарь пуст</div>';
        return;
    }
    
    let html = '';
    items.forEach(item => {
        html += `
        <div class="inventory-item ${item.equipped ? 'equipped' : ''}">
            <div class="item-icon">
                <i class="fas fa-${getItemIcon(item.type)}"></i>
            </div>
            <div class="item-info">
                <h4>${item.name} ${item.equipped ? '<span class="equipped-badge">(Надето)</span>' : ''}</h4>
                <p>${getItemTypeName(item.type)} • ${formatDate(item.purchased_at)}</p>
                ${item.data && item.data.description ? `<p class="item-description">${item.data.description}</p>` : ''}
                ${item.data && item.data.animation ? '<span class="gif-label">GIF анимация</span>' : ''}
            </div>
            <div class="item-actions">
                ${item.equipped ? 
                    '<span class="equipped-badge">Надето</span>' : 
                    `<button class="equip-btn" onclick="equipItem(${item.id})">Надеть</button>`
                }
            </div>
        </div>`;
    });
    
    container.innerHTML = html;
}

async function equipItem(itemId) {
    try {
        const response = await fetch(`/api/profile/equip/${itemId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Предмет применен', 'success');
            loadUserInventory();
            loadEquippedItems();
        } else {
            showNotification('Ошибка применения предмета', 'error');
        }
    } catch (error) {
        showNotification('Ошибка применения предмета', 'error');
    }
}

// ========== ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ ЭКИПИРОВАННЫХ ПРЕДМЕТОВ ==========
async function loadEquippedItems() {
    try {
        const response = await fetch('/api/profile/equipped');
        if (response.ok) {
            const equippedItems = await response.json();
            updateProfileAppearance(equippedItems);
            updateEquippedBadges(equippedItems);
        }
    } catch (error) {
        console.error('Error loading equipped items:', error);
    }
}

function updateProfileAppearance(equippedItems) {
    console.log('Equipped items:', equippedItems);
    
    // Обновляем баннер
    const banner = document.getElementById('profileBanner');
    if (banner) {
        // Сохраняем исходный HTML баннера
        const originalHtml = banner.innerHTML;
        
        if (equippedItems.profile_banner && equippedItems.profile_banner.data) {
            const bannerData = equippedItems.profile_banner.data;
            const bannerUrl = bannerData.image_url;
            console.log('Setting banner URL:', bannerUrl);
            
            if (bannerUrl) {
                // Проверяем, является ли баннер GIF
                const isGif = bannerUrl.toLowerCase().endsWith('.gif') || 
                              (bannerData.animation && bannerData.animation === 'gif');
                
                if (isGif) {
                    // Для GIF создаем элемент img вместо background-image
                    banner.innerHTML = `
                        <img src="${bannerUrl}" alt="Баннер профиля" 
                             onerror="handleImageError(this, '/static/default-banner.jpg')"
                             style="width:100%;height:100%;object-fit:cover;border-radius:12px;">
                        <div class="banner-overlay">
                            <h2 id="bannerUsername">${document.getElementById('bannerUsername').textContent}</h2>
                            <p id="bannerBio">${document.getElementById('bannerBio').textContent}</p>
                            <div class="user-badges" id="userBadges"></div>
                        </div>
                        <button class="banner-edit-btn" onclick="openBannerShop()">
                            <i class="fas fa-camera"></i> Сменить баннер
                        </button>
                    `;
                } else {
                    // Для обычных изображений используем background
                    banner.style.backgroundImage = `url('${bannerUrl}')`;
                    banner.style.backgroundSize = 'cover';
                    banner.style.backgroundPosition = 'center';
                    banner.style.backgroundRepeat = 'no-repeat';
                    
                    // Восстанавливаем оверлей и кнопку
                    const overlay = banner.querySelector('.banner-overlay');
                    const editBtn = banner.querySelector('.banner-edit-btn');
                    if (!overlay) {
                        const overlayDiv = document.createElement('div');
                        overlayDiv.className = 'banner-overlay';
                        overlayDiv.innerHTML = `
                            <h2 id="bannerUsername">${document.getElementById('bannerUsername').textContent}</h2>
                            <p id="bannerBio">${document.getElementById('bannerBio').textContent}</p>
                            <div class="user-badges" id="userBadges"></div>
                        `;
                        banner.appendChild(overlayDiv);
                    }
                    if (!editBtn) {
                        const btn = document.createElement('button');
                        btn.className = 'banner-edit-btn';
                        btn.onclick = openBannerShop;
                        btn.innerHTML = '<i class="fas fa-camera"></i> Сменить баннер';
                        banner.appendChild(btn);
                    }
                }
            }
        } else {
            // Стандартный градиент если баннер не установлен
            banner.style.backgroundImage = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            banner.style.backgroundSize = 'cover';
            banner.style.backgroundPosition = 'center';
            
            // Восстанавливаем исходный HTML если он был потерян
            if (!banner.querySelector('.banner-overlay')) {
                banner.innerHTML = originalHtml;
            }
        }
    }

    // Обновляем аватар
    if (equippedItems.avatar && equippedItems.avatar.data && equippedItems.avatar.data.image_url) {
        const avatarPreview = document.getElementById('avatarPreview');
        if (avatarPreview) {
            const isGifAvatar = equippedItems.avatar.data.image_url.toLowerCase().endsWith('.gif');
            avatarPreview.innerHTML = `
                <img src="${equippedItems.avatar.data.image_url}" alt="Аватар" 
                     onerror="handleImageError(this, '/static/default-avatar.png')"
                     style="width:100%;height:100%;border-radius:50%;object-fit:cover;
                     ${isGifAvatar ? 'animation: none;' : ''}">
            `;
        }
    }
}

function updateEquippedBadges(equippedItems) {
    const badgesContainer = document.getElementById('userBadges');
    if (!badgesContainer) return;

    badgesContainer.innerHTML = '';

    // Добавляем экипированные бейджи
    if (equippedItems.badge && equippedItems.badge.data) {
        const badge = createBadgeElement(equippedItems.badge);
        badgesContainer.appendChild(badge);
    }

    // Добавляем стандартные бейджи (только если у пользователя есть достижения)
    const totalTracks = parseInt(document.getElementById('totalTracks').textContent) || 0;
    
    if (totalTracks > 100) {
        const musicLoverBadge = document.createElement('div');
        musicLoverBadge.className = 'user-badge';
        musicLoverBadge.style.backgroundColor = '#e83e8c';
        musicLoverBadge.innerHTML = '<i class="fas fa-heart"></i> Любитель музыки';
        badgesContainer.appendChild(musicLoverBadge);
    }

    if (totalTracks > 500) {
        const superFanBadge = document.createElement('div');
        superFanBadge.className = 'user-badge';
        superFanBadge.style.backgroundColor = '#ffc107';
        superFanBadge.innerHTML = '<i class="fas fa-star"></i> Суперфанат';
        badgesContainer.appendChild(superFanBadge);
    }
}

function createBadgeElement(badgeItem) {
    const badge = document.createElement('div');
    badge.className = `user-badge badge-${badgeItem.data.rarity || 'common'}`;
    
    if (badgeItem.data.animation) {
        badge.style.animation = `${badgeItem.data.animation} 2s infinite alternate`;
    }
    
    if (badgeItem.data.color) {
        badge.style.backgroundColor = badgeItem.data.color;
    }

    badge.innerHTML = `
        <i class="fas fa-${getBadgeIcon(badgeItem.data)}"></i>
        ${badgeItem.data.text || badgeItem.name || 'Бейдж'}
    `;
    
    return badge;
}

function getBadgeIcon(badgeData) {
    const iconMap = {
        'vip': 'crown',
        'premium': 'gem',
        'winner': 'trophy',
        'music': 'music',
        'star': 'star',
        'medal': 'medal',
        'gif': 'film',
        'animation': 'film'
    };
    return iconMap[badgeData.icon] || 'certificate';
}

function handleImageError(imgElement, fallbackUrl) {
    imgElement.onerror = null;
    imgElement.src = fallbackUrl;
}

// ========== ФУНКЦИИ МАГАЗИНА БАННЕРОВ ==========
function openBannerShop() {
    showTab('shop');
    // Автоматически выбираем категорию баннеров
    setTimeout(() => {
        const bannerCategory = document.querySelector('[data-category="banners"]');
        if (bannerCategory) {
            bannerCategory.click();
        }
    }, 100);
}

// ========== ФУНКЦИИ ДРУЗЕЙ ==========
async function loadFriends() {
    try {
        const response = await fetch('/api/friends');
        if (response.ok) {
            friendsList = await response.json();
            updateFriendsCount(friendsList);
        }
    } catch (error) {
        console.error('Error loading friends:', error);
    }
}

function updateFriendsCount(friends) {
    const acceptedFriends = friends.filter(f => f.status === 'accepted');
    document.getElementById('friendsCount').textContent = acceptedFriends.length;
    
    if (acceptedFriends.length > 0) {
        const avgMatch = acceptedFriends.reduce((sum, friend) => sum + (friend.taste_match || 0), 0) / acceptedFriends.length;
        document.getElementById('tastesMatch').textContent = Math.round(avgMatch) + '%';
    }
}

function openFriendsModal() {
    openModal('friendsModal');
    showFriendsTab('all');
}

function showFriendsTab(tab) {
    currentFriendsTab = tab;
    
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    const filteredFriends = friendsList.filter(friend => {
        switch(tab) {
            case 'requests': return friend.status === 'pending' && friend.direction === 'incoming';
            case 'suggestions': return friend.status === 'suggested';
            default: return friend.status === 'accepted' || friend.status === 'pending';
        }
    });
    
    displayFriends(filteredFriends);
}

function displayFriends(friends) {
    const container = document.getElementById('friendsList');
    
    if (!friends || friends.length === 0) {
        let message = '';
        switch(currentFriendsTab) {
            case 'requests': message = 'Нет входящих запросов'; break;
            case 'suggestions': message = 'Нет предложений друзей'; break;
            default: message = 'Нет друзей';
        }
        container.innerHTML = `<div class="empty-state">${message}</div>`;
        return;
    }
    
    let html = '';
    friends.forEach(friend => {
        const actions = friend.status === 'pending' && friend.direction === 'incoming' ? `
            <div class="friend-actions">
                <button class="action-btn success" onclick="acceptFriend(${friend.id})">
                    <i class="fas fa-check"></i>
                </button>
                <button class="action-btn danger" onclick="rejectFriend(${friend.id})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        ` : friend.status === 'pending' ? `
            <div class="friend-actions">
                <span style="color:var(--text-secondary);font-size:0.8em;">Ожидание</span>
            </div>
        ` : friend.status === 'suggested' ? `
            <div class="friend-actions">
                <button class="action-btn success" onclick="addFriend(${friend.id})">
                    <i class="fas fa-user-plus"></i> Добавить
                </button>
            </div>
        ` : `
            <div class="friend-actions">
                <button class="action-btn" onclick="viewFriendProfile(${friend.id})">
                    <i class="fas fa-eye"></i>
                </button>
            </div>
        `;
        
        html += `
        <div class="friend-item">
            <div class="friend-avatar">
                <img src="${friend.avatar_url || '/static/default-avatar.png'}" alt="${friend.username}" onerror="handleImageError(this, '/static/default-avatar.png')">
            </div>
            <div class="friend-info">
                <h4>${friend.display_name || friend.username}</h4>
                <div class="taste-match">
                    <span>Совпадение: ${friend.taste_match || 0}%</span>
                    <div class="taste-match-bar">
                        <div class="taste-match-fill" style="width: ${friend.taste_match || 0}%"></div>
                    </div>
                </div>
            </div>
            ${actions}
        </div>`;
    });
    
    container.innerHTML = html;
}

function searchFriends() {
    const searchTerm = document.getElementById('friendsSearch').value.toLowerCase();
    const filteredFriends = friendsList.filter(friend => 
        (friend.display_name || friend.username).toLowerCase().includes(searchTerm)
    );
    displayFriends(filteredFriends);
}

async function addFriend(userId) {
    try {
        const response = await fetch(`/api/friends/add/${userId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Запрос в друзья отправлен', 'success');
            loadFriends();
        } else {
            showNotification('Ошибка отправки запроса', 'error');
        }
    } catch (error) {
        showNotification('Ошибка отправки запроса', 'error');
    }
}

async function acceptFriend(friendId) {
    try {
        const response = await fetch(`/api/friends/accept/${friendId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Запрос в друзья принят', 'success');
            loadFriends();
        } else {
            showNotification('Ошибка принятия запроса', 'error');
        }
    } catch (error) {
        showNotification('Ошибка принятия запроса', 'error');
    }
}

async function rejectFriend(friendId) {
    try {
        const response = await fetch(`/api/friends/reject/${friendId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Запрос в друзья отклонен', 'success');
            loadFriends();
        } else {
            showNotification('Ошибка отклонения запроса', 'error');
        }
    } catch (error) {
        showNotification('Ошибка отклонения запроса', 'error');
    }
}

async function findMusicFriends() {
    try {
        const response = await fetch('/api/friends/suggestions');
        if (response.ok) {
            const suggestions = await response.json();
            friendsList = friendsList.concat(suggestions);
            showFriendsTab('suggestions');
            openFriendsModal();
        }
    } catch (error) {
        console.error('Error loading friend suggestions:', error);
        showNotification('Ошибка загрузки предложений друзей', 'error');
    }
}

function viewFriendProfile(friendId) {
    window.location.href = `/profile/${friendId}`;
}

// ========== ФУНКЦИИ АКТИВНОСТИ ==========
async function loadActivityFeed() {
    try {
        showLoading('activityFeed', 'Загрузка активности...');
        const response = await fetch('/api/user/activity');
        if (response.ok) {
            const activity = await response.json();
            displayActivityFeed(activity);
        }
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

function displayActivityFeed(activities) {
    const container = document.getElementById('activityFeed');
    
    if (!activities || activities.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет активности</div>';
        return;
    }
    
    let html = '';
    activities.forEach(activity => {
        html += `
        <div class="activity-item">
            <div class="activity-icon">
                <i class="fas fa-${getActivityIcon(activity.type)}"></i>
            </div>
            <div class="activity-content">
                <p>${getActivityText(activity)}</p>
                <span class="activity-time">${formatTime(activity.timestamp)}</span>
            </div>
            ${activity.track_id ? `
            <button class="activity-action" onclick="playTrack('${activity.track_id}')">
                <i class="fas fa-play"></i>
            </button>
            ` : ''}
        </div>`;
    });
    
    container.innerHTML = html;
}

function getActivityIcon(type) {
    const icons = {
        'listen': 'music',
        'like': 'heart',
        'playlist': 'list',
        'friend': 'user-plus',
        'share': 'share',
        'purchase': 'shopping-cart'
    };
    return icons[type] || 'music';
}

function getActivityText(activity) {
    switch(activity.type) {
        case 'listen':
            return `Слушали: <strong>${activity.track}</strong> - ${activity.artist}`;
        case 'like':
            return `Понравился: <strong>${activity.track}</strong> - ${activity.artist}`;
        case 'playlist':
            return `Создали плейлист: <strong>${activity.playlist_name}</strong>`;
        case 'friend':
            return `Добавили в друзья: <strong>${activity.friend_name}</strong>`;
        case 'purchase':
            return `Купили предмет: <strong>${activity.item_name}</strong>`;
        default:
            return activity.message || 'Неизвестное действие';
    }
}

// ========== ФУНКЦИИ АУДИОПЛЕЕРА ==========
function initAudioPlayer() {
    audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer) {
        audioPlayer = document.createElement('audio');
        audioPlayer.id = 'audioPlayer';
        audioPlayer.hidden = true;
        document.body.appendChild(audioPlayer);
    }

    audioPlayer.addEventListener('timeupdate', updateProgress);
    audioPlayer.addEventListener('ended', handleTrackEnd);
    audioPlayer.addEventListener('pause', updatePlayButton);
    audioPlayer.addEventListener('play', updatePlayButton);
}

function togglePlay() {
    if (audioPlayer.paused) {
        audioPlayer.play().catch(console.error);
    } else {
        audioPlayer.pause();
    }
    updatePlayButton();
}

function updatePlayButton() {
    const playIcon = document.getElementById('playIcon');
    if (playIcon) {
        playIcon.className = audioPlayer.paused ? 'fas fa-play' : 'fas fa-pause';
    }
}

function updateProgress() {
    const progressFill = document.getElementById('progressFill');
    const currentTime = document.getElementById('currentTime');
    
    if (progressFill && currentTime) {
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progressFill.style.width = progress + '%';
        currentTime.textContent = formatDuration(audioPlayer.currentTime * 1000);
    }
}

function handleTrackEnd() {
    audioPlayer.currentTime = 0;
    audioPlayer.pause();
    updatePlayButton();
}

function seekTrack(event) {
    const progressBar = event.currentTarget;
    const rect = progressBar.getBoundingClientRect();
    const seekPosition = (event.clientX - rect.left) / rect.width;
    audioPlayer.currentTime = audioPlayer.duration * seekPosition;
}

function changeVolume(volume) {
    audioPlayer.volume = volume / 100;
}

async function playTrack(trackId) {
    try {
        const response = await fetch(`/api/play_track/${trackId}`);
        if (response.ok) {
            const trackData = await response.json();
            if (trackData.url) {
                audioPlayer.src = trackData.url;
                audioPlayer.play();
                
                document.getElementById('currentTrack').textContent = trackData.title;
                document.getElementById('currentArtist').textContent = trackData.artists.join(', ');
                document.getElementById('totalTime').textContent = formatDuration(trackData.duration);
                
                const playerCover = document.getElementById('playerCover');
                if (trackData.cover_uri) {
                    playerCover.innerHTML = `<img src="${trackData.cover_uri}" alt="${trackData.title}" 
                        style="width:100%;height:100%;border-radius:6px;object-fit:cover">`;
                }
                
                updatePlayButton();
            }
        }
    } catch (error) {
        showNotification('Ошибка воспроизведения', 'error');
    }
}

// ========== ФУНКЦИИ НАСТРОЕК ==========
async function loadUserSettings() {
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const settings = await response.json();
            updateSettingsForm(settings);
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function updateSettingsForm(settings) {
    if (settings) {
        document.getElementById('themeSelect').value = settings.theme || 'dark';
        document.getElementById('languageSelect').value = settings.language || 'ru';
        document.getElementById('musicService').value = settings.music_service || 'yandex';
        document.getElementById('autoPlayToggle').checked = settings.auto_play !== false;
        document.getElementById('showExplicitToggle').checked = settings.show_explicit !== false;
    }
}

function setupSettingsForm() {
    const form = document.getElementById('settingsForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            theme: formData.get('theme'),
            language: formData.get('language'),
            music_service: formData.get('music_service'),
            auto_play: formData.get('auto_play') === 'on',
            show_explicit: formData.get('show_explicit') === 'on'
        };
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                showNotification('Настройки сохранены', 'success');
                closeModal('settingsModal');
                // Применяем тему сразу
                if (data.theme) {
                    document.documentElement.setAttribute('data-theme', data.theme);
                }
            }
        } catch (error) {
            showNotification('Ошибка сохранения настроек', 'error');
        }
    });
}

// ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
function getItemIcon(type) {
    const icons = {
        'theme': 'palette',
        'avatar': 'user',
        'profile_banner': 'image',
        'badge': 'medal',
        'effect': 'magic',
        'animation': 'film',
        'gif': 'film'
    };
    return icons[type] || 'box';
}

function getItemTypeName(type) {
    const names = {
        'theme': 'Тема',
        'avatar': 'Аватар',
        'profile_banner': 'Баннер',
        'badge': 'Бейдж',
        'effect': 'Эффект',
        'animation': 'Анимация',
        'gif': 'GIF баннер'
    };
    return names[type] || 'Предмет';
}

function getUserBalance() {
    return parseInt(document.getElementById('headerBalance').textContent) || 0;
}

async function updateBalance() {
    try {
        const response = await fetch('/api/currency/balance');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('headerBalance').textContent = data.balance;
            document.getElementById('userBalance').textContent = data.balance;
            document.getElementById('profileBalance').textContent = data.balance + ' монет';
        }
    } catch (error) {
        console.error('Error updating balance:', error);
    }
}

async function claimDailyReward() {
    try {
        const response = await fetch('/api/daily_reward', { method: 'POST' });
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                showNotification(`Получено ${result.amount} монет!`, 'success');
                updateBalance();
            } else {
                showNotification(result.message, 'warning');
            }
        }
    } catch (error) {
        showNotification('Ошибка получения награды', 'error');
    }
}

function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = e => reject(e);
        reader.readAsDataURL(file);
    });
}

function formatDuration(ms) {
    if (!ms) return '0:00';
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
}

function formatTime(timestamp) {
    const now = new Date();
    const activityTime = new Date(timestamp);
    const diff = now - activityTime;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 60) return `${minutes} мин назад`;
    if (hours < 24) return `${hours} ч назад`;
    if (days < 7) return `${days} д назад`;
    
    return activityTime.toLocaleDateString('ru-RU');
}

function formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('ru-RU');
}

function showLoading(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `<div class="loading"><i class="fas fa-spinner fa-spin"></i> ${message}</div>`;
    }
}

// ========== УТИЛИТЫ ==========
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function logout() {
    fetch('/logout').then(() => window.location.href = '/login');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation' : 'info'}-circle"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function shareProfile() {
    if (navigator.share) {
        navigator.share({
            title: 'Мой музыкальный профиль',
            text: 'Посмотри мой музыкальный профиль на itired!',
            url: window.location.href
        });
    } else {
        navigator.clipboard.writeText(window.location.href);
        showNotification('Ссылка скопирована в буфер', 'success');
    }
}

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('active');
}

function switchTab(tabName) {
    window.location.href = `/${tabName}`;
}

// Инициализация форм
setupSettingsForm();