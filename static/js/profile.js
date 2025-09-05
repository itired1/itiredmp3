let currentFriendsTab = 'all';
let friendsList = [];
let audioPlayer = null;

document.addEventListener('DOMContentLoaded', function() {
    loadProfileData();
    setupProfileForm();
    setupAvatarUpload();
    setupTokenValidation();
    initAudioPlayer();
    loadFriends();
    loadActivityFeed();
});

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

function setupAvatarUpload() {
    const avatarInput = document.getElementById('avatarInput');
    const avatarPreview = document.getElementById('avatarPreview');
    const avatarUrlInput = document.getElementById('avatar_url');
    
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
                    avatarUrlInput.value = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

function setupTokenValidation() {
    const yandexTokenInput = document.getElementById('yandex_token');
    const vkTokenInput = document.getElementById('vk_token');
    
    if (yandexTokenInput) {
        const validateBtn = document.createElement('button');
        validateBtn.type = 'button';
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Проверить';
        validateBtn.style.marginTop = '8px';
        validateBtn.className = 'validate-btn';
        validateBtn.onclick = () => validateAndSaveToken('yandex', yandexTokenInput.value);
        yandexTokenInput.parentNode.appendChild(validateBtn);
    }
    
    if (vkTokenInput) {
        const validateBtn = document.createElement('button');
        validateBtn.type = 'button';
        validateBtn.innerHTML = '<i class="fas fa-check"></i> Проверить';
        validateBtn.style.marginTop = '8px';
        validateBtn.className = 'validate-btn';
        validateBtn.onclick = () => validateAndSaveToken('vk', vkTokenInput.value);
        vkTokenInput.parentNode.appendChild(validateBtn);
    }
}

async function validateAndSaveToken(service, token) {
    if (!token) {
        showNotification('Введите токен для проверки', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/save_token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
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

function updateProfileForm(profile) {
    if (profile && profile.local) {
        document.getElementById('display_name').value = profile.local.display_name || '';
        document.getElementById('bio').value = profile.local.bio || '';
        document.getElementById('avatar_url').value = profile.local.avatar_url || '';
        document.getElementById('yandex_token').value = profile.local.yandex_token || '';
        document.getElementById('vk_token').value = profile.local.vk_token || '';
        
        document.getElementById('profileDisplayName').textContent = profile.local.display_name || profile.local.username;
        document.getElementById('profileUsername').textContent = '@' + profile.local.username;
        
        const avatarPreview = document.getElementById('avatarPreview');
        if (avatarPreview) {
            if (profile.local.avatar_url) {
                avatarPreview.innerHTML = `
                    <img src="${profile.local.avatar_url}" alt="${profile.local.display_name}" 
                         style="width:100%;height:100%;border-radius:50%;object-fit:cover">
                `;
            } else {
                avatarPreview.innerHTML = '<i class="fas fa-user"></i>';
            }
        }
        
        if (profile.local.created_at) {
            document.getElementById('joinDate').textContent = new Date(profile.local.created_at).toLocaleDateString('ru-RU');
        }
        
        updateTokenStatus(profile);
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
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const result = await response.json();
                showNotification(result.message, 'success');
                
                if (result.avatar_url) {
                    const avatarPreview = document.getElementById('avatarPreview');
                    if (avatarPreview) {
                        avatarPreview.innerHTML = `
                            <img src="${result.avatar_url}" alt="Аватар" 
                                 style="width:100%;height:100%;border-radius:50%;object-fit:cover">
                        `;
                    }
                }
                
                loadProfileData();
            } else {
                throw new Error('Ошибка сохранения');
            }
        } catch (error) {
            showNotification('Ошибка при сохранении профиля', 'error');
        }
    });
}

function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = e => reject(e);
        reader.readAsDataURL(file);
    });
}

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

async function loadActivityFeed() {
    try {
        const response = await fetch('/api/user/activity');
        if (response.ok) {
            const activity = await response.json();
            displayActivityFeed(activity);
        }
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

function updateFriendsCount(friends) {
    const acceptedFriends = friends.filter(f => f.status === 'accepted');
    document.getElementById('friendsCount').textContent = acceptedFriends.length;
    
    if (acceptedFriends.length > 0) {
        const avgMatch = acceptedFriends.reduce((sum, friend) => sum + friend.taste_match, 0) / acceptedFriends.length;
        document.getElementById('tastesMatch').textContent = Math.round(avgMatch) + '%';
    }
}

function openFriendsModal() {
    document.getElementById('friendsModal').style.display = 'block';
    showFriendsTab('all');
}

function showFriendsTab(tab) {
    currentFriendsTab = tab;
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.querySelector(`.tab-btn:nth-child(${['all', 'requests', 'suggestions'].indexOf(tab) + 1})`).classList.add('active');
    
    displayFriends(friendsList.filter(friend => {
        switch(tab) {
            case 'requests': return friend.status === 'pending' && friend.direction === 'incoming';
            case 'suggestions': return false;
            default: return friend.status === 'accepted' || friend.status === 'pending';
        }
    }));
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
                <img src="${friend.avatar_url || '/static/default-avatar.png'}" alt="${friend.username}">
            </div>
            <div class="friend-info">
                <h4>${friend.display_name || friend.username}</h4>
                <div class="taste-match">
                    <span>Совпадение: ${friend.taste_match}%</span>
                    <div class="taste-match-bar">
                        <div class="taste-match-fill" style="width: ${friend.taste_match}%"></div>
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
        showNotification('Функция принятия запроса в разработке', 'info');
    } catch (error) {
        showNotification('Ошибка принятия запроса', 'error');
    }
}

async function rejectFriend(friendId) {
    try {
        showNotification('Функция отклонения запроса в разработке', 'info');
    } catch (error) {
        showNotification('Ошибка отклонения запроса', 'error');
    }
}

function findMusicFriends() {
    showFriendsTab('suggestions');
    openFriendsModal();
}

function viewFriendProfile(friendId) {
    showNotification('Просмотр профиля друга в разработке', 'info');
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
        'share': 'share'
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
            return `Добавили в друзья`;
        default:
            return activity.message;
    }
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

function formatDuration(ms) {
    if (!ms) return '0:00';
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
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
            }
        }
    } catch (error) {
        showNotification('Ошибка воспроизведения', 'error');
    }
}

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