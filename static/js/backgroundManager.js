class BackgroundManager {
    constructor() {
        this.backgroundTypes = ['static', 'gradient', 'animated', 'parallax'];
        this.init();
    }

    init() {
        this.loadBackgroundPreference();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('changeBackgroundBtn').addEventListener('click', () => {
            this.openBackgroundSelector();
        });
    }

    openBackgroundSelector() {
        // Здесь будет интерфейс выбора фона
        const modalContent = `
            <div class="background-selector">
                <h3>Выбор фона</h3>
                
                <div class="background-options">
                    <div class="bg-option" data-type="gradient">
                        <div class="gradient-preview"></div>
                        <span>Градиент</span>
                    </div>
                    
                    <div class="bg-option" data-type="animated">
                        <div class="animated-preview"></div>
                        <span>Анимация</span>
                    </div>
                    
                    <div class="bg-option" data-type="parallax">
                        <div class="parallax-preview"></div>
                        <span>Параллакс</span>
                    </div>
                    
                    <div class="bg-option" data-type="custom">
                        <input type="file" accept="image/gif,image/webp,video/mp4" id="bgUpload">
                        <label for="bgUpload">Загрузить</label>
                    </div>
                </div>
            </div>
        `;

        this.showCustomModal(modalContent);
    }

    async setBackground(type, config) {
        switch (type) {
            case 'gradient':
                this.applyGradientBackground(config);
                break;
            case 'animated':
                this.applyAnimatedBackground(config);
                break;
            case 'parallax':
                this.applyParallaxBackground(config);
                break;
            case 'custom':
                this.applyCustomBackground(config);
                break;
        }

        this.saveBackgroundPreference(type, config);
    }

    applyGradientBackground(config) {
        const gradient = `linear-gradient(${config.angle}deg, ${config.colors.join(', ')})`;
        document.body.style.backgroundImage = gradient;
        document.body.style.backgroundAttachment = 'fixed';
        document.body.style.backgroundSize = 'cover';
    }

    applyAnimatedBackground(config) {
        if (config.type === 'gif') {
            document.body.style.backgroundImage = `url('${config.url}')`;
            document.body.style.backgroundSize = 'cover';
        } else if (config.type === 'css') {
            this.applyCSSAnimation(config);
        }
    }

    applyCSSAnimation(config) {
        const styleId = 'animated-bg';
        let style = document.getElementById(styleId);
        
        if (!style) {
            style = document.createElement('style');
            style.id = styleId;
            document.head.appendChild(style);
        }

        style.textContent = `
            body {
                background: linear-gradient(-45deg, ${config.colors.join(', ')});
                background-size: 400% 400%;
                animation: gradientBG 15s ease infinite;
            }
            
            @keyframes gradientBG {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
        `;
    }

    applyParallaxBackground(config) {
        document.body.style.backgroundImage = `url('${config.imageUrl}')`;
        document.body.style.backgroundAttachment = 'fixed';
        document.body.style.backgroundSize = 'cover';
        document.body.style.backgroundPosition = 'center';

        // Добавляем эффект параллакса при скролле
        window.addEventListener('scroll', this.handleParallaxScroll);
    }

    handleParallaxScroll() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        document.body.style.backgroundPosition = `center ${rate}px`;
    }

    saveBackgroundPreference(type, config) {
        const preference = {
            type,
            config,
            timestamp: Date.now()
        };
        localStorage.setItem('backgroundPreference', JSON.stringify(preference));
    }

    loadBackgroundPreference() {
        const saved = localStorage.getItem('backgroundPreference');
        if (saved) {
            try {
                const preference = JSON.parse(saved);
                this.setBackground(preference.type, preference.config);
            } catch (e) {
                console.error('Error loading background preference:', e);
            }
        }
    }
}

// Инициализация
const backgroundManager = new BackgroundManager();