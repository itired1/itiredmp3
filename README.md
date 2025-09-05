# itiredmp3
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Music Player - VK & Yandex Music Integration</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e6e6e6;
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 30px;
            background: rgba(30, 30, 50, 0.7);
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        h1 {
            font-size: 2.8rem;
            margin-bottom: 15px;
            background: linear-gradient(45deg, #4cc9f0, #4361ee, #7209b7);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }
        
        .subtitle {
            font-size: 1.2rem;
            color: #a3a3c2;
            margin-bottom: 25px;
        }
        
        .logo {
            font-size: 3rem;
            margin-bottom: 20px;
            text-shadow: 0 0 15px rgba(76, 201, 240, 0.5);
        }
        
        .language-tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }
        
        .tab {
            padding: 12px 25px;
            background: rgba(40, 40, 70, 0.7);
            border: none;
            color: #a3a3c2;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border-radius: 5px;
            margin: 0 10px;
        }
        
        .tab.active {
            background: linear-gradient(45deg, #4361ee, #7209b7);
            color: white;
            box-shadow: 0 0 15px rgba(76, 201, 240, 0.5);
        }
        
        .content-section {
            margin-bottom: 40px;
        }
        
        h2 {
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #4cc9f0;
            border-left: 4px solid #7209b7;
            padding-left: 15px;
        }
        
        p {
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .feature {
            background: rgba(40, 40, 70, 0.5);
            padding: 20px;
            border-radius: 10px;
            transition: transform 0.3s ease;
        }
        
        .feature:hover {
            transform: translateY(-5px);
            background: rgba(40, 40, 70, 0.8);
        }
        
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 15px;
            color: #4361ee;
        }
        
        .disclaimer {
            background: rgba(179, 0, 0, 0.2);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ff3860;
            margin: 30px 0;
        }
        
        .disclaimer h2 {
            color: #ff3860;
        }
        
        .tech-stack {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin: 30px 0;
        }
        
        .tech {
            text-align: center;
            padding: 15px;
            background: rgba(40, 40, 70, 0.5);
            border-radius: 10px;
            margin: 10px;
            min-width: 120px;
            transition: all 0.3s ease;
        }
        
        .tech:hover {
            background: rgba(40, 40, 70, 0.8);
            transform: scale(1.05);
        }
        
        .future-plans {
            background: rgba(40, 70, 40, 0.2);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #38ff7a;
            margin: 30px 0;
        }
        
        .future-plans h2 {
            color: #38ff7a;
        }
        
        footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #a3a3c2;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2.2rem;
            }
            
            .features {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🎵</div>
            <h1>Music Player / Музыкальный Плеер</h1>
            <p class="subtitle">Веб-приложение с интеграцией VK и Яндекс.Музыки</p>
            
            <div class="language-tabs">
                <button class="tab active" onclick="showLanguage('ru')">Русский</button>
                <button class="tab" onclick="showLanguage('en')">English</button>
            </div>
        </header>
        
        <section id="ru-content" class="content-section">
            <h2>О проекте</h2>
            <p>Современный веб-плеер с интеграцией сервисов VK и Яндекс.Музыки. Проект сочетает в себе элегантный дизайн и функциональные возможности воспроизведения музыки.</p>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🔌</div>
                    <h3>Двойная интеграция</h3>
                    <p>Подключение к сервисам VK и Яндекс.Музыки через официальные API</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">📱</div>
                    <h3>Адаптивный дизайн</h3>
                    <p>Красивый интерфейс для desktop и мобильных устройств</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔐</div>
                    <h3>Токенная аутентификация</h3>
                    <p>Безопасный вход с использованием токенов сервисов</p>
                </div>
            </div>
            
            <div class="future-plans">
                <h2>Планы по развитию</h2>
                <p>Это активный развивающийся проект с планами на:</p>
                <ul>
                    <li>Улучшенные профили пользователей и настройки</li>
                    <li>Расширенное создание и обмен плейлистами</li>
                    <li>Социальные функции и рекомендации музыки</li>
                    <li>Улучшенная производительность и оффлайн-режим</li>
                    <li>Интеграция дополнительных музыкальных сервисов</li>
                </ul>
            </div>
            
            <div class="disclaimer">
                <h2>Важная информация</h2>
                <p><strong>Внимание</strong>: В проекте используются демо-данные для тестирования и разработки. Вся личная информация, email-адреса и данные аккаунтов внутри приложения являются вымышленными и используются исключительно в демонстрационных целях.</p>
            </div>
            
            <h2>Технологии</h2>
            <div class="tech-stack">
                <div class="tech">HTML5</div>
                <div class="tech">CSS3</div>
                <div class="tech">JavaScript</div>
                <div class="tech">Python</div>
                <div class="tech">VK API</div>
                <div class="tech">Yandex API</div>
            </div>
        </section>
        
        <section id="en-content" class="content-section" style="display: none;">
            <h2>About Project</h2>
            <p>A modern web-based music player with integration for VK and Yandex Music services. This project combines sleek design with functional music playback capabilities.</p>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🔌</div>
                    <h3>Dual Integration</h3>
                    <p>Connect with both VK and Yandex Music services through official APIs</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">📱</div>
                    <h3>Responsive Design</h3>
                    <p>Beautiful UI that works on desktop and mobile devices</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔐</div>
                    <h3>Token Authentication</h3>
                    <p>Secure login using service tokens</p>
                </div>
            </div>
            
            <div class="future-plans">
                <h2>Future Development</h2>
                <p>This is an active development project with plans for:</p>
                <ul>
                    <li>Enhanced user profiles and preferences</li>
                    <li>Advanced playlist creation and sharing</li>
                    <li>Social features and music discovery</li>
                    <li>Improved performance and offline capabilities</li>
                    <li>Additional music service integrations</li>
                </ul>
            </div>
            
            <div class="disclaimer">
                <h2>Disclaimer</h2>
                <p><strong>Note</strong>: This project uses demo/sample data for testing and development purposes. All personal information, email addresses, and account details within this application are fictional and used solely for demonstration.</p>
            </div>
            
            <h2>Technology Stack</h2>
            <div class="tech-stack">
                <div class="tech">HTML5</div>
                <div class="tech">CSS3</div>
                <div class="tech">JavaScript</div>
                <div class="tech">Python</div>
                <div class="tech">VK API</div>
                <div class="tech">Yandex API</div>
            </div>
        </section>
        
        <footer>
            <p>© 2025 Music Player Project | Статус: Активная разработка / Active Development</p>
        </footer>
    </div>

    <script>
        function showLanguage(lang) {
            if (lang === 'ru') {
                document.getElementById('ru-content').style.display = 'block';
                document.getElementById('en-content').style.display = 'none';
                document.querySelectorAll('.tab')[0].classList.add('active');
                document.querySelectorAll('.tab')[1].classList.remove('active');
            } else {
                document.getElementById('ru-content').style.display = 'none';
                document.getElementById('en-content').style.display = 'block';
                document.querySelectorAll('.tab')[0].classList.remove('active');
                document.querySelectorAll('.tab')[1].classList.add('active');
            }
        }
    </script>
</body>
</html>
