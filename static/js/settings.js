
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    setupSettingsListeners();
    setupThemeSelector();
});

function setupThemeSelector() {
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        themeSelect.addEventListener('change', function() {
            applyTheme(this.value);
            saveSettings();
        });
    }
}

async function loadSettings() {
    try {
        const response = await apiCall('settings');
        if (response) {
            updateSettingsUI(response);
            applyTheme(response.theme || 'dark');
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function updateSettingsUI(settings) {
    if (settings.theme) {
        document.getElementById('themeSelect').value = settings.theme;
    }
    if (settings.language) {
        document.getElementById('languageSelect').value = settings.language;
    }
    if (settings.auto_play !== undefined) {
        document.getElementById('autoPlayToggle').checked = settings.auto_play;
    }
}

function setupSettingsListeners() {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveSettings();
        });
    }
    
    document.querySelectorAll('#themeSelect, #languageSelect, #autoPlayToggle').forEach(element => {
        element.addEventListener('change', saveSettings);
    });
}

async function saveSettings() {
    try {
        const settings = {
            theme: document.getElementById('themeSelect').value,
            language: document.getElementById('languageSelect').value,
            auto_play: document.getElementById('autoPlayToggle').checked
        };
        
        const response = await apiCall('settings', {
            method: 'POST',
            body: JSON.stringify(settings)
        });
        
        if (response.success) {
            showNotification('Настройки сохранены', 'success');
        }
    } catch (error) {
        showNotification('Ошибка сохранения настроек', 'error');
    }
}

function applyTheme(theme) {
    if (theme === 'auto') {
        // Автоматическое определение темы системы
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.setAttribute('data-theme', 'dark');
        } else {
            document.body.setAttribute('data-theme', 'light');
        }
    } else {
        document.body.setAttribute('data-theme', theme);
    }
    localStorage.setItem('theme', theme);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        background: ${type === 'success' ? 'var(--success)' : 
                     type === 'error' ? 'var(--danger)' : 
                     type === 'warning' ? 'var(--warning)' : 'var(--accent)'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}