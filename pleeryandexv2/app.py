from flask import Flask, render_template, jsonify, request, session, redirect, url_for, g
from yandex_music import Client
import sqlite3
import os
import json
from datetime import datetime, timedelta
import logging
import bcrypt
from functools import wraps
import time
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
import random
from PIL import Image
import uuid
from io import BytesIO

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'itired-super-secret-key-2025')
app.permanent_session_lifetime = timedelta(days=30)

# Конфигурация БД
DATABASE = 'itired.db'
UPLOAD_FOLDER = 'static/uploads/avatars'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Настройки email
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'itiredmp3@gmail.com',
    'password': 'ozbg ahqs jack lerf'
}

# Исправление для Python 3.12+ (datetime адаптер)
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(text):
    return datetime.fromisoformat(text.decode())

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("datetime", convert_datetime)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                yandex_token TEXT,
                avatar_url TEXT,
                bio TEXT,
                email_verified BOOLEAN DEFAULT FALSE,
                verification_code TEXT,
                verification_code_expires DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                theme TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'ru',
                auto_play BOOLEAN DEFAULT TRUE,
                show_explicit BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        db.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        return user
    return None

def get_yandex_client(user_id=None):
    try:
        db = get_db()
        cursor = db.cursor()
        if user_id:
            cursor.execute('SELECT yandex_token FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            token = user[0] if user else None
        else:
            current_user = get_current_user()
            token = current_user[5] if current_user else None
        
        if not token:
            return None
        
        client = Client(token).init()
        return client
    except Exception as e:
        logger.error(f"Error initializing Yandex Music client: {e}")
        return None

def send_verification_email(email, verification_code):
    """Отправка красивого email с кодом подтверждения в темных тонах"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"itired 🎵 <{EMAIL_CONFIG['email']}>"
        msg['To'] = email
        msg['Subject'] = '🎵 Ваш код подтверждения для itired'
        
        # Гифка из Pinterest (заменяем на прямую ссылку)
        gif_url = "https://i.pinimg.com/originals/2d/44/59/2d4459a3160b5a621ae2e32a73f1e3b1.gif"
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Подтверждение email - itired</title>
            <style>
                body {{
                    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                    margin: 0;
                    padding: 0;
                    color: #ffffff;
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: rgba(26, 26, 26, 0.95);
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
                    padding: 30px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}
                .logo {{
                    font-size: 2.5em;
                    font-weight: 800;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }}
                .tagline {{
                    font-size: 1.1em;
                    opacity: 0.9;
                    font-weight: 500;
                }}
                .content {{
                    padding: 40px;
                }}
                .welcome {{
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 1.5em;
                    font-weight: 600;
                    background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .gif-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .gif-container img {{
                    max-width: 100%;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }}
                .code-container {{
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                    padding: 30px;
                    text-align: center;
                    margin: 30px 0;
                    border: 2px solid rgba(255, 107, 107, 0.3);
                    position: relative;
                    overflow: hidden;
                }}
                .code-container::before {{
                    content: '';
                    position: absolute;
                    top: -50%;
                    left: -50%;
                    width: 200%;
                    height: 200%;
                    background: linear-gradient(45deg, transparent, rgba(255,107,107,0.1), transparent);
                    animation: shimmer 3s infinite;
                }}
                .code-label {{
                    font-size: 1.1em;
                    margin-bottom: 20px;
                    color: #a0a0a0;
                    font-weight: 500;
                }}
                .verification-code {{
                    font-size: 2.5em;
                    font-weight: 800;
                    font-family: 'Courier New', monospace;
                    background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    letter-spacing: 8px;
                    margin: 20px 0;
                    text-shadow: 0 0 20px rgba(255,107,107,0.3);
                    animation: pulse 2s infinite;
                }}
                .timer {{
                    background: rgba(255, 107, 107, 0.2);
                    color: #ff6b6b;
                    padding: 12px 24px;
                    border-radius: 25px;
                    display: inline-block;
                    font-size: 0.9em;
                    font-weight: 600;
                    margin-top: 15px;
                }}
                .security-note {{
                    background: rgba(255, 193, 7, 0.1);
                    border-left: 4px solid #ffc107;
                    padding: 20px;
                    margin: 30px 0;
                    border-radius: 12px;
                    font-size: 0.9em;
                    line-height: 1.6;
                }}
                .features {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 40px 0;
                }}
                .feature {{
                    background: rgba(255, 255, 255, 0.03);
                    padding: 20px;
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    transition: all 0.3s ease;
                    text-align: center;
                }}
                .feature:hover {{
                    background: rgba(255, 255, 255, 0.08);
                    transform: translateY(-5px);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .feature-icon {{
                    font-size: 2em;
                    margin-bottom: 15px;
                    background: linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .feature-title {{
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #ffffff;
                }}
                .feature-desc {{
                    color: #a0a0a0;
                    font-size: 0.9em;
                    line-height: 1.5;
                }}
                .footer {{
                    background: rgba(0, 0, 0, 0.3);
                    padding: 30px;
                    text-align: center;
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 0.9em;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }}
                .social-links {{
                    margin-top: 15px;
                }}
                .social-links a {{
                    color: #ff6b6b;
                    text-decoration: none;
                    margin: 0 10px;
                    transition: color 0.3s ease;
                }}
                .social-links a:hover {{
                    color: #4ecdc4;
                }}
                @keyframes pulse {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                    100% {{ transform: scale(1); }}
                }}
                @keyframes shimmer {{
                    0% {{ transform: translateX(-100%) translateY(-100%) rotate(45deg); }}
                    100% {{ transform: translateX(100%) translateY(100%) rotate(45deg); }}
                }}
                @keyframes float {{
                    0% {{ transform: translateY(0px); }}
                    50% {{ transform: translateY(-10px); }}
                    100% {{ transform: translateY(0px); }}
                }}
                .floating {{
                    animation: float 3s ease-in-out infinite;
                }}
                @media (max-width: 600px) {{
                    .content {{
                        padding: 20px;
                    }}
                    .verification-code {{
                        font-size: 2em;
                        letter-spacing: 6px;
                    }}
                    .features {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">itired</div>
                    <div class="tagline">Твоя музыкальная вселенная</div>
                </div>
                
                <div class="content">
                    <h2 class="welcome">Добро пожаловать в музыкальное сообщество! 🎶</h2>
                    
                    <div class="gif-container floating">
                        <img src="{gif_url}" alt="Музыкальная анимация" style="max-width: 300px;">
                    </div>
                    
                    <div class="code-container">
                        <div class="code-label">Твой код подтверждения:</div>
                        <div class="verification-code">{verification_code}</div>
                        <div class="timer">⏰ Действует 10 минут</div>
                    </div>
                    
                    <div class="security-note">
                        <strong>🔒 Важная информация:</strong> Никогда не сообщай этот код третьим лицам. 
                        Сотрудники itired никогда не запрашивают коды доступа. Если ты не регистрировался, 
                        просто проигнорируй это письмо.
                    </div>
                    
                    <div class="features">
                        <div class="feature">
                            <div class="feature-icon">🎵</div>
                            <div class="feature-title">Миллионы треков</div>
                            <div class="feature-desc">Доступ к огромной библиотеке музыки из любого уголка мира</div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">❤️</div>
                            <div class="feature-title">Персональные плейлисты</div>
                            <div class="feature-desc">Музыка, которая идеально подходит именно тебе</div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">👥</div>
                            <div class="feature-title">Музыкальные друзья</div>
                            <div class="feature-desc">Найди единомышленников и делитесь музыкой</div>
                        </div>
                        
                        <div class="feature">
                            <div class="feature-icon">📊</div>
                            <div class="feature-title">Умная статистика</div>
                            <div class="feature-desc">Отслеживай свои музыкальные предпочтения и открывай новое</div>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>© 2024 itired · Твой персональный музыкальный опыт</p>
                    <p>🎶 Служба поддержки: <a href="mailto:support@itired.com">support@itired.com</a></p>
                    <p>📧 Это письмо отправлено автоматически</p>
                    
                    <div class="social-links">
                        <a href="#">Instagram</a> • 
                        <a href="#">Telegram</a> • 
                        <a href="#">VK</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Текстовый вариант для почтовых клиентов, которые не поддерживают HTML
        text = f"""
        ДОБРО ПОЖАЛОВАТЬ В ITIRED! 🎵
        
        Твой код подтверждения: {verification_code}
        
        ⏰ Код действителен в течение 10 минут
        
        Введи этот код на сайте itired для завершения регистрации и погрузись в мир музыки!
        
        🔒 Безопасность: Никогда не сообщай этот код третьим лицам.
        
        Если ты не регистрировался на itired, проигнорируй это письмо.
        
        --
        itired · Твоя музыкальная вселенная
        🎶 Служба поддержки: support@itired.com
        📧 Письмо отправлено автоматически
        
        © 2024 itired
        """
        
        part1 = MIMEText(text, 'plain', 'utf-8')
        part2 = MIMEText(html, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Красивое письмо отправлено на {email}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки красивого письма на {email}: {e}")
        # Fallback на простое текстовое письмо
        return send_simple_verification_email(email, verification_code)

def send_simple_verification_email(email, verification_code):
    """Простая текстовая версия на случай ошибки"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = email
        msg['Subject'] = 'Код подтверждения для itired'
        
        text = f"""
        Ваш код подтверждения: {verification_code}
        Код действителен в течение 10 минут.
        
        Введите этот код на сайте itired для завершения регистрации.
        
        Если вы не регистрировались, проигнорируйте это письмо.
        """
        
        msg.attach(MIMEText(text, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Простое письмо отправлено на {email}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки простого письма на {email}: {e}")
        return False
def is_valid_image(file_data):
    """Проверяет, является ли файл валидным изображением"""
    try:
        image = Image.open(BytesIO(file_data))
        image.verify()
        return True
    except Exception as e:
        logger.warning(f"Invalid image file: {e}")
        return False

def get_image_format(file_data):
    """Определяет формат изображения"""
    try:
        image = Image.open(BytesIO(file_data))
        return image.format
    except Exception as e:
        logger.warning(f"Cannot determine image format: {e}")
        return None

def save_uploaded_file(file_data, filename):
    """Сохранение загруженного файла аватарки"""
    try:
        if not is_valid_image(file_data):
            logger.warning("Invalid image file uploaded")
            return None
        
        image_format = get_image_format(file_data)
        if not image_format:
            logger.warning("Cannot determine image format")
            return None
        
        supported_formats = ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP', 'JPG']
        if image_format.upper() not in supported_formats:
            logger.warning(f"Unsupported image format: {image_format}")
            return None
        
        # Конвертируем формат для расширения файла
        format_map = {
            'JPEG': 'jpg',
            'JPG': 'jpg',
            'PNG': 'png',
            'GIF': 'gif',
            'BMP': 'bmp',
            'WEBP': 'webp'
        }
        
        ext = format_map.get(image_format.upper(), 'jpg')
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Сохраняем изображение с оптимизацией
        image = Image.open(BytesIO(file_data))
        
        # Конвертируем в RGB если нужно
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (45, 45, 45))  # Темный фон
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Оптимизируем размер
        max_size = (400, 400)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Сохраняем с оптимизацией качества
        quality = 85
        if ext == 'png':
            image.save(filepath, 'PNG', optimize=True)
        else:
            image.save(filepath, 'JPEG', quality=quality, optimize=True)
        
        return f"/static/uploads/avatars/{unique_filename}"
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        return None
def save_uploaded_file(file_data, filename):
    """Сохранение загруженного файла аватарки"""
    try:
        if not is_valid_image(file_data):
            return None
        
        image_format = get_image_format(file_data)
        if not image_format:
            return None
        
        supported_formats = ['jpeg', 'png', 'gif', 'bmp', 'webp']
        if image_format not in supported_formats:
            return None
        
        ext = 'jpg' if image_format == 'jpeg' else image_format
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        return f"/static/uploads/avatars/{unique_filename}"
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return None

# Инициализация БД
init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        display_name = request.form.get('display_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        verification_code = request.form.get('verification_code', '').strip()
        
        if not all([username, email, password, confirm_password]):
            return render_template('auth.html', mode='register', error='Все поля обязательны для заполнения')
        
        if password != confirm_password:
            return render_template('auth.html', mode='register', error='Пароли не совпадают')
        
        if len(password) < 6:
            return render_template('auth.html', mode='register', error='Пароль должен содержать минимум 6 символов')
        
        db = get_db()
        cursor = db.cursor()
        
        # Проверка существующего пользователя только при первой регистрации
        if not verification_code:
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            existing_user = cursor.fetchone()
            
            if existing_user:
                return render_template('auth.html', mode='register', error='Пользователь с таким именем или email уже существует')
        
        if verification_code:
            cursor.execute(
                'SELECT * FROM users WHERE email = ? AND verification_code = ? AND verification_code_expires > datetime("now")',
                (email, verification_code)
            )
            user_to_verify = cursor.fetchone()
            
            if not user_to_verify:
                return render_template('auth.html', mode='register_verify', email=email, 
                                    error='Неверный или просроченный код подтверждения')
            
            cursor.execute(
                'UPDATE users SET email_verified = TRUE, verification_code = NULL, verification_code_expires = NULL WHERE id = ?',
                (user_to_verify[0],)
            )
            db.commit()
            
            session.permanent = True
            session['user_id'] = user_to_verify[0]
            session['username'] = user_to_verify[1]
            
            return redirect(url_for('index'))
        else:
            verification_code = str(uuid.uuid4())[:6].upper()
            code_expires = datetime.now() + timedelta(minutes=10)
            
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            try:
                cursor.execute(
                    'INSERT INTO users (username, display_name, email, password_hash, verification_code, verification_code_expires) VALUES (?, ?, ?, ?, ?, ?)',
                    (username, display_name or username, email, password_hash, verification_code, code_expires)
                )
                
                user_id = cursor.lastrowid
                cursor.execute('INSERT INTO user_settings (user_id) VALUES (?)', (user_id,))
                db.commit()
                
                if send_verification_email(email, verification_code):
                    return render_template('auth.html', mode='register_verify', email=email, 
                                        message='Код подтверждения отправлен на вашу почту')
                else:
                    return render_template('auth.html', mode='register', error='Ошибка отправки email. Попробуйте позже.')
            except sqlite3.IntegrityError:
                return render_template('auth.html', mode='register', error='Пользователь с таким именем или email уже существует')
    
    return render_template('auth.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('auth.html', mode='login', error='Введите имя пользователя и пароль')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, username))
        user = cursor.fetchone()
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user[4].encode('utf-8')):
            return render_template('auth.html', mode='login', error='Неверное имя пользователя или пароль')
        
        if not user[8]:
            return render_template('auth.html', mode='login', error='Email не подтвержден. Проверьте вашу почту')
        
        session.permanent = True
        session['user_id'] = user[0]
        session['username'] = user[1]
        
        return redirect(url_for('index'))
    
    return render_template('auth.html', mode='login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            data = request.get_json()
            display_name = data.get('display_name', '').strip()
            bio = data.get('bio', '').strip()
            yandex_token = data.get('yandex_token', '').strip()
            avatar_url = data.get('avatar_url', '').strip()
            avatar_file = data.get('avatar_file', '')
            
            user = get_current_user()
            db = get_db()
            cursor = db.cursor()
            
            update_fields = []
            update_values = []
            
            if display_name is not None:
                update_fields.append('display_name = ?')
                update_values.append(display_name)
            
            if bio is not None:
                update_fields.append('bio = ?')
                update_values.append(bio)
            
            final_avatar_url = user[6] if user[6] else ''
            if avatar_file and avatar_file.startswith('data:image/'):
                try:
                    header, encoded = avatar_file.split(',', 1)
                    file_data = base64.b64decode(encoded)
                    
                    saved_path = save_uploaded_file(file_data, 'avatar')
                    if saved_path:
                        final_avatar_url = saved_path
                        update_fields.append('avatar_url = ?')
                        update_values.append(saved_path)
                except Exception as e:
                    logger.error(f"Error processing avatar file: {e}")
            
            elif avatar_url and avatar_url.startswith(('http://', 'https://')):
                final_avatar_url = avatar_url
                update_fields.append('avatar_url = ?')
                update_values.append(avatar_url)
            
            if yandex_token:
                update_fields.append('yandex_token = ?')
                update_values.append(yandex_token)
            
            if update_fields:
                update_values.append(user[0])
                query = f'UPDATE users SET {", ".join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
                cursor.execute(query, update_values)
                db.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Профиль обновлен',
                'avatar_url': final_avatar_url
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500
    
    return render_template('profile.html')

@app.route('/api/profile')
@login_required
def get_profile_api():
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        
        yandex_profile = None
        if client:
            try:
                account = client.account_status()
                yandex_profile = {
                    'username': account.account.login,
                    'full_name': f"{getattr(account.account, 'first_name', '')} {getattr(account.account, 'last_name', '')}".strip(),
                    'email': getattr(account.account, 'email', ''),
                    'premium': getattr(account.account, 'premium', False),
                    'uid': getattr(account.account, 'uid', '')
                }
            except Exception as e:
                logger.warning(f"Yandex profile error: {e}")
        
        return jsonify({
            'local': {
                'username': user[1],
                'display_name': user[2] or user[1],
                'email': user[3],
                'bio': user[7],
                'avatar_url': user[6],
                'yandex_token_set': bool(user[5]),
                'created_at': user[11]
            },
            'yandex': yandex_profile
        })
    except Exception as e:
        logger.error(f"Profile API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_yandex_token')
@login_required
def check_yandex_token():
    try:
        user = get_current_user()
        if not user or not user[5]:
            return jsonify({'valid': False, 'message': 'Токен не настроен'})
        
        client = Client(user[5]).init()
        account = client.account_status()
        return jsonify({
            'valid': True,
            'message': 'Подключено к Яндекс.Музыке',
            'account': {
                'login': account.account.login,
                'name': f"{getattr(account.account, 'first_name', '')} {getattr(account.account, 'last_name', '')}".strip(),
                'premium': getattr(account.account, 'premium', False)
            }
        })
    except Exception as e:
        return jsonify({'valid': False, 'message': f'Ошибка подключения: {str(e)}'})

@app.route('/api/save_token', methods=['POST'])
@login_required
def save_token():
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'success': False, 'message': 'Токен не может быть пустым'})
        
        try:
            client = Client(token).init()
            account = client.account_status()
        except Exception as e:
            return jsonify({'success': False, 'message': f'Неверный токен: {str(e)}'})
        
        user = get_current_user()
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE users SET yandex_token = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (token, user[0])
        )
        db.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Токен успешно сохранен и проверен',
            'account': {
                'login': account.account.login,
                'name': f"{getattr(account.account, 'first_name', '')} {getattr(account.account, 'last_name', '')}".strip(),
                'premium': getattr(account.account, 'premium', False)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка сохранения: {str(e)}'})

@app.route('/api/recommendations')
@login_required
def get_recommendations():
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        if not client:
            return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
        
        result = []
        
        # Попробуем получить чарты
        try:
            chart = client.chart('world')
            if chart and hasattr(chart, 'chart') and chart.chart.tracks:
                for track in chart.chart.tracks[:6]:
                    cover_uri = None
                    if hasattr(track, 'cover_uri') and track.cover_uri:
                        cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
                    
                    result.append({
                        'id': track.id,
                        'title': track.title,
                        'type': 'track',
                        'artists': [artist.name for artist in track.artists],
                        'cover_uri': cover_uri,
                        'album': track.albums[0].title if track.albums else 'Unknown'
                    })
        except Exception as e:
            logger.warning(f"Chart error: {e}")
        
        # Попробуем получить плейлисты дня
        try:
            landing = client.landing()
            if landing and hasattr(landing, 'blocks'):
                for block in landing.blocks:
                    if hasattr(block, 'entities') and block.id == 'personal-playlists':
                        for entity in block.entities[:6-len(result)]:
                            if hasattr(entity, 'data'):
                                playlist = entity.data
                                cover_uri = None
                                if hasattr(playlist, 'cover_uri') and playlist.cover_uri:
                                    cover_uri = f"https://{playlist.cover_uri.replace('%%', '400x400')}"
                                
                                result.append({
                                    'id': getattr(playlist, 'kind', ''),
                                    'title': getattr(playlist, 'title', ''),
                                    'type': 'playlist',
                                    'track_count': getattr(playlist, 'track_count', 0),
                                    'cover_uri': cover_uri,
                                    'description': getattr(playlist, 'description', '') or ''
                                })
        except Exception as e:
            logger.warning(f"Landing error: {e}")
        
        return jsonify(result[:6])
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return jsonify([])

@app.route('/api/playlists')
@login_required
def get_playlists():
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        if not client:
            return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
        
        playlists = client.users_playlists_list()
        result = []
        
        for playlist in playlists:
            cover_uri = None
            if hasattr(playlist, 'cover_uri') and playlist.cover_uri:
                cover_uri = f"https://{playlist.cover_uri.replace('%%', '400x400')}"
            
            modified_date = None
            if hasattr(playlist, 'modified') and playlist.modified:
                if hasattr(playlist.modified, 'isoformat'):
                    modified_date = playlist.modified.isoformat()
                else:
                    modified_date = str(playlist.modified)
            
            result.append({
                'id': playlist.kind,
                'title': playlist.title,
                'track_count': playlist.track_count,
                'cover_uri': cover_uri,
                'modified': modified_date,
                'description': getattr(playlist, 'description', '') or '',
                'owner': getattr(playlist, 'owner', {}).get('login', '') if hasattr(playlist, 'owner') else ''
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Playlists error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/playlist/<int:playlist_id>')
@login_required
def get_playlist(playlist_id):
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        if not client:
            return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
        
        playlist = client.users_playlists(playlist_id)
        if not playlist:
            return jsonify({'error': 'Плейлист не найден'}), 404
        
        tracks = []
        for track_short in playlist.tracks:
            try:
                track = track_short.track
                cover_uri = None
                if hasattr(track, 'cover_uri') and track.cover_uri:
                    cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
                
                tracks.append({
                    'id': track.id,
                    'title': track.title,
                    'artists': [artist.name for artist in track.artists],
                    'album': track.albums[0].title if track.albums else 'Unknown Album',
                    'duration': track.duration_ms,
                    'cover_uri': cover_uri,
                    'year': track.albums[0].year if track.albums and track.albums[0].year else 'Unknown'
                })
            except Exception as e:
                logger.warning(f"Error processing track: {e}")
                continue
        
        cover_uri = None
        if hasattr(playlist, 'cover_uri') and playlist.cover_uri:
            cover_uri = f"https://{playlist.cover_uri.replace('%%', '400x400')}"
        
        return jsonify({
            'id': playlist.kind,
            'title': playlist.title,
            'track_count': playlist.track_count,
            'cover_uri': cover_uri,
            'description': getattr(playlist, 'description', '') or '',
            'owner': getattr(playlist, 'owner', {}).get('login', '') if hasattr(playlist, 'owner') else '',
            'tracks': tracks
        })
    except Exception as e:
        logger.error(f"Playlist error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/liked_tracks')
@login_required
def get_liked_tracks():
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        if not client:
            return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
        
        liked_tracks = client.users_likes_tracks()
        tracks = []
        
        for track_short in liked_tracks[:100]:
            try:
                track = track_short.fetch_track()
                cover_uri = None
                if hasattr(track, 'cover_uri') and track.cover_uri:
                    cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
                
                tracks.append({
                    'id': track.id,
                    'title': track.title,
                    'artists': [artist.name for artist in track.artists],
                    'album': track.albums[0].title if track.albums else 'Unknown Album',
                    'duration': track.duration_ms,
                    'cover_uri': cover_uri,
                    'year': track.albums[0].year if track.albums and track.albums[0].year else 'Unknown'
                })
            except Exception as e:
                continue
        
        return jsonify(tracks)
    except Exception as e:
        logger.error(f"Liked tracks error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
@login_required
def get_stats():
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        if not client:
            return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
        
        playlists = client.users_playlists_list()
        liked_tracks = client.users_likes_tracks()
        
        genre_stats = {}
        for track_short in liked_tracks[:50]:
            try:
                track = track_short.fetch_track()
                if track.albums and track.albums[0].genre:
                    genre = track.albums[0].genre
                    genre_stats[genre] = genre_stats.get(genre, 0) + 1
            except:
                continue
        
        stats = {
            'total_playlists': len(playlists),
            'total_liked_tracks': len(liked_tracks),
            'largest_playlist': max([p.track_count for p in playlists], default=0),
            'total_artists': len(set(artist.name for track_short in liked_tracks[:20] for artist in track_short.fetch_track().artists)),
            'genre_stats': genre_stats
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
@login_required
def search():
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        if not client:
            return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
        
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Введите запрос'}), 400
        
        search_result = client.search(query)
        result = {'tracks': [], 'albums': [], 'artists': [], 'playlists': []}
        
        if search_result.tracks:
            for track in search_result.tracks.results[:10]:
                cover_uri = None
                if hasattr(track, 'cover_uri') and track.cover_uri:
                    cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
                
                result['tracks'].append({
                    'id': track.id,
                    'title': track.title,
                    'artists': [artist.name for artist in track.artists],
                    'album': track.albums[0].title if track.albums else 'Unknown',
                    'duration': track.duration_ms,
                    'cover_uri': cover_uri
                })
        
        if search_result.albums:
            for album in search_result.albums.results[:5]:
                cover_uri = None
                if hasattr(album, 'cover_uri') and album.cover_uri:
                    cover_uri = f"https://{album.cover_uri.replace('%%', '300x300')}"
                
                result['albums'].append({
                    'id': album.id,
                    'title': album.title,
                    'artists': [artist.name for artist in album.artists],
                    'year': album.year,
                    'track_count': album.track_count,
                    'cover_uri': cover_uri
                })
        
        if search_result.artists:
            for artist in search_result.artists.results[:5]:
                result['artists'].append({
                    'id': artist.id,
                    'name': artist.name,
                    'genres': artist.genres or []
                })
        
        if search_result.playlists:
            for playlist in search_result.playlists.results[:5]:
                cover_uri = None
                if hasattr(playlist, 'cover_uri') and playlist.cover_uri:
                    cover_uri = f"https://{playlist.cover_uri.replace('%%', '300x300')}"
                
                result['playlists'].append({
                    'id': playlist.kind,
                    'title': playlist.title,
                    'track_count': playlist.track_count,
                    'cover_uri': cover_uri,
                    'description': getattr(playlist, 'description', '') or ''
                })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/play_track/<track_id>')
@login_required
def get_track_url(track_id):
    try:
        user = get_current_user()
        client = get_yandex_client(user[0])
        if not client:
            return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
        
        track = client.tracks(track_id)[0]
        download_info = track.get_download_info()
        
        if download_info:
            best_quality = max(download_info, key=lambda x: x.bitrate_in_kbps)
            download_url = best_quality.get_direct_link()
            
            return jsonify({
                'url': download_url,
                'title': track.title,
                'artists': [artist.name for artist in track.artists],
                'duration': track.duration_ms,
                'cover_uri': f"https://{track.cover_uri.replace('%%', '300x300')}" if track.cover_uri else None
            })
        
        return jsonify({'error': 'Не удалось получить ссылку на трек'}), 404
    except Exception as e:
        logger.error(f"Track URL error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    db = get_db()
    cursor = db.cursor()
    user = get_current_user()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user[0],))
        settings = cursor.fetchone()
        
        if settings:
            return jsonify({
                'theme': settings[1],
                'language': settings[2],
                'auto_play': bool(settings[3]),
                'show_explicit': bool(settings[4])
            })
        return jsonify({})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_settings 
            (user_id, theme, language, auto_play, show_explicit)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user[0],
            data.get('theme', 'dark'),
            data.get('language', 'ru'),
            data.get('auto_play', True),
            data.get('show_explicit', True)
        ))
        db.commit()
        
        return jsonify({'success': True})
    return jsonify({'error': 'Method not allowed'}), 405

@app.route('/api/notifications')
@login_required
def get_notifications():
    return jsonify([])

@app.route('/api/resend_verification', methods=['POST'])
def resend_verification():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email обязателен'})
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND email_verified = FALSE', (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден или уже подтвержден'})
        
        verification_code = str(uuid.uuid4())[:6].upper()
        code_expires = datetime.now() + timedelta(minutes=10)
        
        cursor.execute(
            'UPDATE users SET verification_code = ?, verification_code_expires = ? WHERE id = ?',
            (verification_code, code_expires, user[0])
        )
        db.commit()
        
        if send_verification_email(email, verification_code):
            return jsonify({'success': True, 'message': 'Код отправлен повторно'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка отправки email'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})
    
@app.route('/api/friends')
@login_required
def get_friends():
    try:
        user = get_current_user()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.display_name, u.avatar_url, 
                   f.status, f.taste_match, f.created_at,
                   CASE WHEN f.user_id = ? THEN 'outgoing' ELSE 'incoming' END as direction
            FROM friends f
            JOIN users u ON u.id = CASE 
                WHEN f.user_id = ? THEN f.friend_id 
                ELSE f.user_id 
            END
            WHERE (f.user_id = ? OR f.friend_id = ?) 
            AND f.status IN ('accepted', 'pending')
        ''', (user[0], user[0], user[0], user[0]))
        
        friends = []
        for row in cursor.fetchall():
            # Добавляем mock-активность для демонстрации
            current_activity = {
                'track': 'Bohemian Rhapsody',
                'artist': 'Queen',
                'timestamp': datetime.now().isoformat()
            } if random.random() > 0.5 else None
            
            friends.append({
                'id': row[0],
                'username': row[1],
                'display_name': row[2],
                'avatar_url': row[3],
                'status': row[4],
                'taste_match': row[5],
                'created_at': row[6],
                'direction': row[7],
                'current_activity': current_activity,
                'top_genres': ['Rock', 'Pop', 'Classic'],
                'is_online': random.random() > 0.3
            })
        
        return jsonify(friends)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/add/<int:friend_id>', methods=['POST'])
@login_required
def add_friend(friend_id):
    try:
        user = get_current_user()
        db = get_db()
        cursor = db.cursor()
        
        # Проверяем, не добавлен ли уже пользователь
        cursor.execute('''
            SELECT * FROM friends 
            WHERE (user_id = ? AND friend_id = ?) 
            OR (user_id = ? AND friend_id = ?)
        ''', (user[0], friend_id, friend_id, user[0]))
        
        existing = cursor.fetchone()
        if existing:
            return jsonify({'error': 'Уже есть запрос на дружбу'}), 400
        
        # Считаем совпадение музыкальных вкусов (упрощенно)
        taste_match = random.randint(50, 95)
        
        cursor.execute('''
            INSERT INTO friends (user_id, friend_id, taste_match, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user[0], friend_id, taste_match))
        
        db.commit()
        
        # Логируем активность
        cursor.execute('''
            INSERT INTO user_activity (user_id, activity_type, activity_data)
            VALUES (?, 'friend', ?)
        ''', (user[0], json.dumps({'friend_id': friend_id})))
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Запрос отправлен'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity')
@login_required
def get_activity():
    try:
        user = get_current_user()
        
        # Mock данные активности для демонстрации
        activities = [
            {
                'type': 'listen',
                'track': 'Bohemian Rhapsody',
                'artist': 'Queen',
                'track_id': 12345,
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat()
            },
            {
                'type': 'like', 
                'track': 'Hotel California',
                'artist': 'Eagles',
                'track_id': 67890,
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()
            },
            {
                'type': 'playlist',
                'playlist_name': 'Мое настроение',
                'timestamp': (datetime.now() - timedelta(hours=3)).isoformat()
            }
        ]
        
        return jsonify(activities)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)