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
from PIL import Image
from io import BytesIO
import requests
import vk_api
import re
import secrets
import random
from collections import Counter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from models import db, User, UserCurrency, ShopCategory, ShopItem, UserInventory, CurrencyTransaction


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=30)


limiter = Limiter(app)
limiter.key_func = get_remote_address
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///itired.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Инициализация базы данных
def init_database():
    try:
        with app.app_context():

            db.create_all()
            
            init_db() 
            
            init_shop_data()
            create_admin_user()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
def init_shop_data():
    """Инициализация магазина начальными данными"""
    try:

        categories = [
            ('themes', 'Темы оформления', 'fas fa-palette'),
            ('avatars', 'Аватары', 'fas fa-user'),
            ('banners', 'Баннеры профиля', 'fas fa-image'),
            ('badges', 'Бейджи', 'fas fa-medal'),
            ('effects', 'Эффекты плеера', 'fas fa-magic'),
            ('animations', 'Анимации', 'fas fa-film')
        ]
        
        for cat_name, cat_desc, cat_icon in categories:
            category = ShopCategory.query.filter_by(name=cat_name).first()
            if not category:
                category = ShopCategory(
                    name=cat_name,
                    description=cat_desc,
                    icon=cat_icon
                )
                db.session.add(category)
        
        db.session.commit()
        

        shop_items = [
            ('Темная тема Premium', 'theme', 'themes', 50, 
             '{"styles": {"--bg-primary": "#0a0a0a", "--bg-secondary": "#141414", "--accent": "#ff6b6b", "--text-primary": "#ffffff"}}', 'rare'),
            
            ('Синяя тема Ocean', 'theme', 'themes', 40,
             '{"styles": {"--bg-primary": "#0a1929", "--bg-secondary": "#132f4c", "--accent": "#1976d2", "--text-primary": "#e3f2fd"}}', 'common'),
            
            ('Аватар "Звезда"', 'avatar', 'avatars', 20,
             '{"image_url": "/static/shop/avatars/star.png", "unlockable": true}', 'common'),
            
            ('Аватар "Лунный свет"', 'avatar', 'avatars', 25,
             '{"image_url": "/static/shop/avatars/moon.png", "unlockable": true}', 'common'),
            
            ('Баннер "Г"', 'profile_banner', 'banners', 40,
             '{"image_url": "/static/shop/banners/xz2.jpg", "preview": "/static/shop/banners/xz2.jpg"}', 'common'),
            ('Баннер "Огненный дракон"', 'profile_banner', 'banners', 120,
             '{"image_url": "/static/shop/banners/kruto.gif", "preview": "/static/shop/banners/kruto.gif", "animation": "gif"}', 'legendary'),
            ('Баннер "zxc"', 'profile_banner', 'banners', 120,
             '{"image_url": "/static/shop/banners/kruto1.gif", "preview": "/static/shop/banners/kruto1.gif", "animation": "gif"}', 'legendary'),
            ('Баннер "вас крутой"', 'profile_banner', 'banners', 120,
             '{"image_url": "/static/shop/banners/kruto2.gif", "preview": "/static/shop/banners/kruto2.gif", "animation": "gif"}', 'legendary'),
            ('Баннер "крутой вас"', 'profile_banner', 'banners', 120,
             '{"image_url": "/static/shop/banners/kruto3.gif", "preview": "/static/shop/banners/kruto3.gif", "animation": "gif"}', 'legendary'),
            ('Баннер "крутой"', 'profile_banner', 'banners', 120,
             '{"image_url": "/static/shop/banners/kruto.gif", "preview": "/static/shop/banners/kruto.gif", "animation": "gif"}', 'legendary'),

            ('Баннер "К"', 'profile_banner', 'banners', 45,
             '{"image_url": "/static/shop/banners/xz1.jpg", "preview": "/static/shop/banners/xz1.jpg"}', 'rare'),

            ('Баннер "Г"', 'profile_banner', 'banners', 35,
             '{"image_url": "/static/shop/banners/xz.jpg", "preview": "/static/shop/banners/xz.jpg"}', 'common'),
            
            ('Бейдж "Меломан"', 'badge', 'badges', 15,
             '{"text": "🎵 Меломан", "color": "#ff6b6b", "animation": "pulse"}', 'common'),
            
            ('Бейдж "VIP"', 'badge', 'badges', 30,
             '{"text": "⭐ VIP", "color": "#ffd700", "animation": "glow"}', 'rare'),
            
            ('Эффект "Неоновое сияние"', 'effect', 'effects', 75,
             '{"css": ".player { filter: drop-shadow(0 0 10px #ff00ff); }", "duration": 30000}', 'epic'),
            
            ('Анимация "Вращение"', 'animation', 'animations', 45,
             '{"css": "@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }", "element": ".album-cover"}', 'rare')
        ]
        
        for name, item_type, category_name, price, data, rarity in shop_items:
            category = ShopCategory.query.filter_by(name=category_name).first()
            if category:
                item = ShopItem.query.filter_by(name=name).first()
                if not item:
                    item = ShopItem(
                        name=name,
                        type=item_type,
                        category_id=category.id,
                        price=price,
                        data=data,
                        rarity=rarity
                    )
                    db.session.add(item)
        
        db.session.commit()
        logger.info("Shop data initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing shop data: {e}")

def get_user_currency_balance(user_id):
    currency = UserCurrency.query.filter_by(user_id=user_id).first()
    return currency.balance if currency else 0

def can_afford_item(user_id, item_price):
    balance = get_user_currency_balance(user_id)
    return balance >= item_price

def get_equipped_items(user_id):
    inventory = UserInventory.query.filter_by(
        user_id=user_id, equipped=True
    ).all()
    
    equipped_items = {}
    for inv_item in inventory:
        equipped_items[inv_item.item.type] = {
            'item_id': inv_item.item_id,
            'data': json.loads(inv_item.item.data) if inv_item.item.data else {}
        }
    
    return equipped_items

def create_admin_user():
    try:
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@itired.com',
                password_hash=bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Admin user created: admin / admin123")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user[10]: 
            return jsonify({'error': 'Требуются права администратора'}), 403
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def add_currency(user_id, amount, reason):
    try:
        currency = UserCurrency.query.filter_by(user_id=user_id).first()
        
        if currency:
            currency.balance += amount
        else:
            currency = UserCurrency(user_id=user_id, balance=amount)
            db.session.add(currency)
        
        transaction = CurrencyTransaction(
            user_id=user_id,
            amount=amount,
            reason=reason
        )
        db.session.add(transaction)
        db.session.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error adding currency: {e}")
        db.session.rollback()
        return False

DATABASE = 'itired.db'
UPLOAD_FOLDER = 'static/uploads/avatars'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'itiredmp3@gmail.com',
    'password': 'ozbg ahqs jack lerf'
}

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
                vk_token TEXT,
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
                music_service TEXT DEFAULT 'yandex',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица активности пользователя
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT NOT NULL,
                activity_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица друзей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                friend_id INTEGER,
                status TEXT DEFAULT 'pending',
                taste_match INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (friend_id) REFERENCES users (id),
                UNIQUE(user_id, friend_id)
            )
        ''')
        
        # Таблица для хранения истории прослушивания
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listening_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                track_id TEXT,
                track_data TEXT,
                played_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                colors TEXT NOT NULL,
                background_url TEXT,
                is_default BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        
        db.commit()

def get_current_user():
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        return user
    return None

def get_current_user_id():
    user = get_current_user()
    return user[0] if user else None

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

def get_vk_client(user_id=None):
    try:
        db = get_db()
        cursor = db.cursor()
        if user_id:
            cursor.execute('SELECT vk_token FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            token = user[0] if user else None
        else:
            current_user = get_current_user()
            token = current_user[6] if current_user else None
        
        if not token:
            return None
        
        if 'access_token=' in token:
            match = re.search(r'access_token=([^&]+)', token)
            if match:
                token = match.group(1)
        
        session = vk_api.VkApi(token=token)
        return session.get_api()
    except Exception as e:
        logger.error(f"Error initializing VK client: {e}")
        return None

def get_current_music_service(user_id=None):
    db = get_db()
    cursor = db.cursor()
    if not user_id:
        user_id = get_current_user_id()
    
    cursor.execute('SELECT music_service FROM user_settings WHERE user_id = ?', (user_id,))
    setting = cursor.fetchone()
    return setting[0] if setting else 'yandex'

def send_verification_email(email, verification_code):
    try:
        msg = MIMEText(f'Ваш код подтверждения: {verification_code}\nДействует 10 минут.', 'plain', 'utf-8')
        msg['From'] = f"itired 🎵 <{EMAIL_CONFIG['email']}>"
        msg['To'] = email
        msg['Subject'] = '🎵 Ваш код подтверждения для itired'
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Письмо отправлено на {email}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки письма: {e}")
        return False

def is_valid_image(file_data):
    try:
        image = Image.open(BytesIO(file_data))
        image.verify()
        return True
    except Exception as e:
        logger.warning(f"Invalid image file: {e}")
        return False

def save_uploaded_file(file_data, filename):
    try:
        if not is_valid_image(file_data):
            return None
        
        image = Image.open(BytesIO(file_data))
        
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (45, 45, 45))
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        max_size = (400, 400)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        unique_filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        image.save(filepath, 'JPEG', quality=85, optimize=True)
        
        return f"/static/uploads/avatars/{unique_filename}"
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        return None

class EnhancedRecommender:
    def __init__(self):
        pass
    
    def get_enhanced_recommendations(self, user_id, service='yandex'):
        """Получение рекомендаций из нескольких источников"""
        recommendations = []
        
        try:
            if service == 'yandex':
                client = get_yandex_client(user_id)
                if client:
                    history_recs = self._get_history_based_recommendations(user_id, client)
                    recommendations.extend(history_recs)
                    
                    liked_recs = self._get_liked_based_recommendations(user_id, client)
                    recommendations.extend(liked_recs)
                    
                    if not recommendations:
                        fallback_recs = self._get_fallback_recommendations(client)
                        recommendations.extend(fallback_recs)
            
            elif service == 'vk':
                vk_client = get_vk_client(user_id)
                if vk_client:
                    vk_recs = self._get_vk_recommendations(vk_client)
                    recommendations.extend(vk_recs)
            
            return self._deduplicate_and_shuffle(recommendations)
            
        except Exception as e:
            logger.error(f"Enhanced recommendations error: {e}")
            return []
    
    def _get_history_based_recommendations(self, user_id, client):
        try:
            # Получаем историю прослушивания из базы
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                SELECT track_data FROM listening_history 
                WHERE user_id = ? 
                ORDER BY played_at DESC 
                LIMIT 20
            ''', (user_id,))
            
            history_tracks = []
            for row in cursor.fetchall():
                try:
                    track_data = json.loads(row[0])
                    history_tracks.append(track_data)
                except:
                    continue
            
            if not history_tracks:
                return []
            
            recommendations = []
            
            genres = self._extract_genres_from_history(history_tracks)
            if genres:
                for genre in genres[:2]: 
                    try:
                        search_results = client.search(f"жанр:{genre}", type_='track')
                        if search_results and search_results.tracks:
                            for track in search_results.tracks.results[:2]:
                                recommendations.append(self._format_track(track, 'history_genre'))
                    except:
                        continue
            
            artists = self._extract_artists_from_history(history_tracks)
            if artists:
                for artist in artists[:2]:
                    try:
                        search_results = client.search(artist, type_='track')
                        if search_results and search_results.tracks:
                            for track in search_results.tracks.results[:2]:
                                if not any(t['id'] == f"yandex_{track.id}" for t in recommendations):
                                    recommendations.append(self._format_track(track, 'history_artist'))
                    except:
                        continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"History based recommendations error: {e}")
            return []
    
    def _get_liked_based_recommendations(self, user_id, client):
        try:
            liked_tracks = client.users_likes_tracks()
            if not liked_tracks:
                return []
            
            recommendations = []
            
            # Берем 3 случайных лайкнутых трека
            sample_tracks = random.sample(list(liked_tracks[:10]), min(3, len(liked_tracks)))
            
            for track_short in sample_tracks:
                try:
                    track = track_short.fetch_track()
                    
                    # Ищем похожие треки
                    search_query = f"{track.title} {track.artists[0].name if track.artists else ''}"
                    similar_tracks = client.search(search_query, type_='track')
                    
                    if similar_tracks and similar_tracks.tracks:
                        for similar in similar_tracks.tracks.results[:2]:
                            if similar.id != track.id:
                                recommendations.append(self._format_track(similar, 'liked_similar'))
                
                except Exception as e:
                    logger.warning(f"Error processing liked track: {e}")
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Liked based recommendations error: {e}")
            return []
    
    def _get_fallback_recommendations(self, client):
        recommendations = []
        
        try:
            new_releases = client.new_releases()
            if new_releases and hasattr(new_releases, 'new_releases'):
                for album in new_releases.new_releases[:3]:
                    recommendations.append({
                        'id': f"yandex_{album.id}",
                        'title': album.title,
                        'type': 'album',
                        'artists': [artist.name for artist in album.artists],
                        'cover_uri': f"https://{album.cover_uri.replace('%%', '300x300')}" if hasattr(album, 'cover_uri') and album.cover_uri else None,
                        'source': 'new_releases'
                    })
            chart = client.chart('world')
            if chart and hasattr(chart, 'chart') and chart.chart.tracks:
                for track in chart.chart.tracks[:3]:
                    recommendations.append(self._format_track(track, 'chart'))
                    
        except Exception as e:
            logger.error(f"Fallback recommendations error: {e}")
        
        return recommendations
    
    def _get_vk_recommendations(self, vk_client):
        try:
            recommendations = []
            vk_recs = vk_client.audio.getRecommendations(count=6)
            
            if 'items' in vk_recs:
                for track in vk_recs['items']:
                    recommendations.append({
                        'id': f"vk_{track['id']}",
                        'title': track['title'],
                        'type': 'track',
                        'artists': [track['artist']],
                        'cover_uri': track.get('album', {}).get('thumb', {}).get('photo_300') if track.get('album') else None,
                        'duration': track['duration'] * 1000,
                        'source': 'vk_recommendations'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"VK recommendations error: {e}")
            return []
    
    def _extract_genres_from_history(self, history_tracks):
        genres = []
        for track in history_tracks:
            if 'genre' in track:
                genres.append(track['genre'])
        return [genre for genre, count in Counter(genres).most_common() if genre]
    
    def _extract_artists_from_history(self, history_tracks):
        artists = []
        for track in history_tracks:
            if 'artists' in track and track['artists']:
                artists.extend(track['artists'])
        return [artist for artist, count in Counter(artists).most_common(5)]
    
    def _format_track(self, track, source):
        cover_uri = None
        if hasattr(track, 'cover_uri') and track.cover_uri:
            cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
        
        return {
            'id': f"yandex_{track.id}",
            'title': track.title,
            'type': 'track',
            'artists': [artist.name for artist in track.artists] if hasattr(track, 'artists') else [],
            'cover_uri': cover_uri,
            'album': track.albums[0].title if track.albums else 'Unknown Album',
            'duration': getattr(track, 'duration_ms', 0),
            'source': source
        }
    
    def _deduplicate_and_shuffle(self, recommendations):
        seen_ids = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec['id'] not in seen_ids:
                seen_ids.add(rec['id'])
                unique_recommendations.append(rec)
        
        random.shuffle(unique_recommendations)
        return unique_recommendations[:8]  

recommender = EnhancedRecommender()

init_db()
init_database()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute", error_message='Слишком много попыток регистрации')
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
                cursor.execute(
                    'SELECT verification_code_expires FROM users WHERE email = ?',
                    (email,)
                )
                expired_user = cursor.fetchone()
                
                error_msg = 'Неверный или просроченный код подтверждения'
                if expired_user and expired_user[0]:
                    expired_time = datetime.fromisoformat(expired_user[0]) if isinstance(expired_user[0], str) else expired_user[0]
                    if expired_time < datetime.now():
                        error_msg = f'Код истек {expired_time.strftime("%H:%M")}. Запросите новый код.'
                
                return render_template('auth.html', mode='register_verify', email=email, 
                                    error=error_msg)
            
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
@limiter.limit("5 per minute", error_message='Слишком много попыток входа')
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
        
        if not user[9]:
            cursor.execute('SELECT verification_code_expires FROM users WHERE id = ?', (user[0],))
            expiry = cursor.fetchone()
            
            if expiry and expiry[0]:
                expiry_time = expiry[0] if isinstance(expiry[0], datetime) else datetime.fromisoformat(expiry[0])
                if expiry_time < datetime.now():
                    return render_template('auth.html', mode='login', 
                                        error='Код подтверждения истек. Используйте форму ниже для отправки нового кода.',
                                        show_resend=True, email=user[3])
            
            return render_template('auth.html', mode='login', 
                                error='Email не подтвержден. Проверьте вашу почту',
                                show_resend=True, email=user[3])
        
        session.permanent = True
        session['user_id'] = user[0]
        session['username'] = user[1]
        
        return redirect(url_for('index'))
    
    return render_template('auth.html', mode='login')


@app.route('/api/currency/balance')
@login_required
def get_currency_balance():
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
            
        currency = UserCurrency.query.filter_by(user_id=user_id).first()
        balance = currency.balance if currency else 0
        return jsonify({'balance': balance})
    except Exception as e:
        logger.error(f"Currency balance error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/items')
@login_required
def get_shop_items():
    try:
        user = User.get_current()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        items = ShopItem.query.all()
        
        user_items = user.get_inventory()
        owned_item_ids = [ui.item_id for ui in user_items]
        
        result = []
        for item in items:
            result.append({
                'id': item.id,
                'name': item.name,
                'type': item.type,
                'category': item.category.name if item.category else 'unknown',
                'price': item.price,
                'data': item.get_data_dict(),
                'rarity': item.rarity,
                'owned': item.id in owned_item_ids
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Shop items error: {e}")
        return jsonify({'error': str(e)}), 500
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Shop items error: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/shop/buy/<int:item_id>', methods=['POST'])
@login_required
def buy_shop_item(item_id):
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
            
        item = ShopItem.query.get_or_404(item_id)
        
        if not item.is_active:
            return jsonify({'success': False, 'message': 'Товар недоступен'}), 400
        
        currency = UserCurrency.query.filter_by(user_id=user_id).first()
        balance = currency.balance if currency else 0
        
        if balance < item.price:
            return jsonify({'success': False, 'message': 'Недостаточно средств'}), 400
        
        existing_inventory = UserInventory.query.filter_by(
            user_id=user_id, item_id=item_id
        ).first()
        
        if existing_inventory:
            return jsonify({'success': False, 'message': 'Товар уже куплен'}), 400
        
        if currency:
            currency.balance -= item.price
        else:
            currency = UserCurrency(user_id=user_id, balance=-item.price)
            db.session.add(currency)
        
        transaction = CurrencyTransaction(
            user_id=user_id,
            amount=-item.price,
            reason=f'purchase_{item.name}'
        )
        db.session.add(transaction)
        
        inventory = UserInventory(
            user_id=user_id,
            item_id=item_id
        )
        db.session.add(inventory)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Покупка совершена успешно',
            'new_balance': currency.balance
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Buy item error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profile/equip/<int:item_id>', methods=['POST'])
@login_required
def equip_item(item_id):
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        inventory_item = UserInventory.query.filter_by(
            user_id=user_id, item_id=item_id
        ).first()
        
        if not inventory_item:
            return jsonify({'success': False, 'message': 'Товар не куплен'}), 400
        
        item = ShopItem.query.get_or_404(item_id)
        
        same_type_items = db.session.query(UserInventory).join(
            ShopItem, UserInventory.item_id == ShopItem.id
        ).filter(
            UserInventory.user_id == user_id,
            ShopItem.type == item.type
        ).all()
        
        for inv_item in same_type_items:
            inv_item.equipped = False
        
        inventory_item.equipped = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Предмет применен'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Equip item error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/profile/inventory')
@login_required
def get_user_inventory():
    try:
        user = User.get_current()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        inventory = user.get_inventory()
        
        result = []
        for inv in inventory:
            result.append({
                'id': inv.item.id,
                'name': inv.item.name,
                'type': inv.item.type,
                'price': inv.item.price,
                'data': inv.item.get_data_dict(),
                'equipped': inv.equipped,
                'purchased_at': inv.purchased_at.isoformat() if inv.purchased_at else None
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Inventory error: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/admin/add_currency', methods=['POST'])
@login_required
@admin_required
def admin_add_currency():
    try:
        data = request.get_json()
        username = data.get('username')
        amount = data.get('amount', 0)
        reason = data.get('reason', 'admin_grant')
        
        if not username or amount <= 0:
            return jsonify({'success': False, 'message': 'Неверные параметры'}), 400
        
        target_user = User.query.filter_by(username=username).first()
        if not target_user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'}), 404
        
        currency = UserCurrency.query.filter_by(user_id=target_user.id).first()
        if currency:
            currency.balance += amount
        else:
            currency = UserCurrency(user_id=target_user.id, balance=amount)
            db.session.add(currency)
        
        transaction = CurrencyTransaction(
            user_id=target_user.id,
            amount=amount,
            reason=reason
        )
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Добавлено {amount} валюты пользователю {username}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/shop/add_item', methods=['POST'])
@login_required
@admin_required
def admin_add_shop_item():
    try:
        data = request.get_json()
        
        required_fields = ['name', 'type', 'category', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Отсутствует поле: {field}'}), 400
        
        category = ShopCategory.query.filter_by(name=data['category']).first()
        if not category:
            return jsonify({'success': False, 'message': 'Категория не найдена'}), 404
        
        new_item = ShopItem(
            name=data['name'],
            type=data['type'],
            category_id=category.id,
            price=data['price'],
            data=json.dumps(data.get('data', {})),
            rarity=data.get('rarity', 'common'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Товар добавлен',
            'item_id': new_item.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/shop/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_shop_categories():
    try:
        if request.method == 'GET':
            categories = ShopCategory.query.filter_by(is_active=True).all()
            return jsonify([{
                'id': cat.id,
                'name': cat.name,
                'description': cat.description,
                'icon': cat.icon
            } for cat in categories])
        
        elif request.method == 'POST':
            data = request.get_json()
            
            new_category = ShopCategory(
                name=data['name'],
                description=data.get('description', ''),
                icon=data.get('icon', 'fas fa-box'),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(new_category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Категория создана',
                'category_id': new_category.id
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin')
@login_required
def admin_panel():
    user = get_current_user()
    if not user or not user[10]: 
        return redirect(url_for('index'))
    return render_template('admin_panel.html')

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
            vk_token = data.get('vk_token', '').strip()
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
            
            final_avatar_url = user[7] if user[7] else ''
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
            
            if vk_token:
                update_fields.append('vk_token = ?')
                update_values.append(vk_token)
            
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
        vk_client = get_vk_client(user[0])
        
        yandex_profile = None
        vk_profile = None
        
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
        
        if vk_client:
            try:
                vk_user = vk_client.users.get()[0]
                vk_profile = {
                    'first_name': vk_user['first_name'],
                    'last_name': vk_user['last_name'],
                    'full_name': f"{vk_user['first_name']} {vk_user['last_name']}",
                    'uid': vk_user['id']
                }
            except Exception as e:
                logger.warning(f"VK profile error: {e}")
        
        return jsonify({
            'local': {
                'username': user[1],
                'display_name': user[2] or user[1],
                'email': user[3],
                'bio': user[8],
                'avatar_url': user[7],
                'yandex_token_set': bool(user[5]),
                'vk_token_set': bool(user[6]),
                'created_at': user[12]
            },
            'yandex': yandex_profile,
            'vk': vk_profile
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

@app.route('/api/check_vk_token')
@login_required
def check_vk_token():
    try:
        user = get_current_user()
        if not user or not user[6]:
            return jsonify({'valid': False, 'message': 'Токен не настроен'})
        
        vk_client = get_vk_client(user[0])
        if not vk_client:
            return jsonify({'valid': False, 'message': 'Ошибка инициализации VK клиента'})
        
        vk_user = vk_client.users.get()[0]
        return jsonify({
            'valid': True,
            'message': 'Подключено к VK Музыке',
            'account': {
                'name': f"{vk_user['first_name']} {vk_user['last_name']}",
                'uid': vk_user['id']
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
        service = data.get('service', 'yandex')
        
        if not token:
            return jsonify({'success': False, 'message': 'Токен не может быть пустым'})
        
        user = get_current_user()
        db = get_db()
        cursor = db.cursor()
        
        if service == 'yandex':
            try:
                client = Client(token).init()
                account = client.account_status()
            except Exception as e:
                return jsonify({'success': False, 'message': f'Неверный токен: {str(e)}'})
            
            cursor.execute(
                'UPDATE users SET yandex_token = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (token, user[0])
            )
            db.commit()
            
            cache.delete(f'recommendations_{user[0]}')
            cache.delete(f'playlists_{user[0]}')
            cache.delete(f'stats_{user[0]}')
            
            return jsonify({
                'success': True, 
                'message': 'Токен успешно сохранен и проверен',
                'account': {
                    'login': account.account.login,
                    'name': f"{getattr(account.account, 'first_name', '')} {getattr(account.account, 'last_name', '')}".strip(),
                    'premium': getattr(account.account, 'premium', False)
                }
            })
        
        elif service == 'vk':
            try:
                if 'access_token=' in token:
                    match = re.search(r'access_token=([^&]+)', token)
                    if match:
                        token = match.group(1)
                
                vk_session = vk_api.VkApi(token=token)
                vk_client = vk_session.get_api()
                vk_user = vk_client.users.get()[0]
            except Exception as e:
                return jsonify({'success': False, 'message': f'Неверный токен: {str(e)}'})
            
            cursor.execute(
                'UPDATE users SET vk_token = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (token, user[0])
            )
            db.commit()
            
            cache.delete(f'recommendations_{user[0]}')
            cache.delete(f'playlists_{user[0]}')
            cache.delete(f'stats_{user[0]}')
            
            return jsonify({
                'success': True, 
                'message': 'Токен успешно сохранен и проверен',
                'account': {
                    'name': f"{vk_user['first_name']} {vk_user['last_name']}",
                    'uid': vk_user['id']
                }
            })
        
        return jsonify({'success': False, 'message': 'Неизвестный сервис'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка сохранения: {str(e)}'})

@app.route('/api/recommendations')
@login_required
def get_recommendations():
    try:
        user_id = get_current_user_id()
        service = get_current_music_service(user_id)
        
        recommendations = recommender.get_enhanced_recommendations(user_id, service)
        
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return jsonify([])

@app.route('/api/playlists')
@login_required
def get_playlists():
    try:
        user_id = get_current_user_id()
        service = get_current_music_service(user_id)
        
        result = []
        
        if service == 'yandex':
            client = get_yandex_client(user_id)
            if not client:
                return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
            
            playlists = client.users_playlists_list()
            
            for playlist in playlists:
                if hasattr(playlist, 'collective') and playlist.collective:
                    continue
                    
                cover_uri = None
                if hasattr(playlist, 'cover') and playlist.cover:
                    if hasattr(playlist.cover, 'uri') and playlist.cover.uri:
                        cover_uri = f"https://{playlist.cover.uri.replace('%%', '400x400')}"
                
                modified_date = None
                if hasattr(playlist, 'modified') and playlist.modified:
                    if hasattr(playlist.modified, 'isoformat'):
                        modified_date = playlist.modified.isoformat()
                    else:
                        modified_date = str(playlist.modified)
                
                result.append({
                    'id': f"yandex_{playlist.kind}",
                    'title': playlist.title,
                    'track_count': playlist.track_count,
                    'cover_uri': cover_uri,
                    'modified': modified_date,
                    'description': getattr(playlist, 'description', '') or '',
                    'owner': getattr(playlist.owner, 'login', '') if hasattr(playlist, 'owner') else '',
                    'service': 'yandex'
                })
        
        elif service == 'vk':
            vk_client = get_vk_client(user_id)
            if not vk_client:
                return jsonify({'error': 'Токен VK не настроен'}), 400
            
            try:
                playlists = vk_client.audio.getPlaylists()
                if 'items' in playlists:
                    for playlist in playlists['items']:
                        if playlist.get('is_following') or playlist.get('owner_id') != user_id:
                            continue
                            
                        result.append({
                            'id': f"vk_{playlist['id']}",
                            'title': playlist['title'],
                            'track_count': playlist['count'],
                            'cover_uri': playlist['photo']['photo_300'] if playlist.get('photo') else None,
                            'modified': playlist['update_time'],
                            'description': playlist.get('description', ''),
                            'owner': f"id{playlist['owner_id']}",
                            'service': 'vk'
                        })
            except Exception as e:
                logger.warning(f"VK playlists error: {e}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Playlists error: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/playlist/<service>_<int:playlist_id>')
@login_required
def get_playlist(service, playlist_id):
    try:
        user_id = get_current_user_id()
        
        if service == 'yandex':
            client = get_yandex_client(user_id)
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
                        'id': f"yandex_{track.id}",
                        'title': track.title,
                        'artists': [artist.name for artist in track.artists],
                        'album': track.albums[0].title if track.albums else 'Unknown Album',
                        'duration': track.duration_ms,
                        'cover_uri': cover_uri,
                        'year': track.albums[0].year if track.albums and track.albums[0].year else 'Unknown',
                        'service': 'yandex'
                    })
                except Exception as e:
                    logger.warning(f"Error processing track: {e}")
                    continue
            
            cover_uri = None
            if hasattr(playlist, 'cover_uri') and playlist.cover_uri:
                cover_uri = f"https://{playlist.cover_uri.replace('%%', '400x400')}"
            
            return jsonify({
                'id': f"yandex_{playlist.kind}",
                'title': playlist.title,
                'track_count': playlist.track_count,
                'cover_uri': cover_uri,
                'description': getattr(playlist, 'description', '') or '',
                'owner': getattr(playlist, 'owner', {}).get('login', '') if hasattr(playlist, 'owner') else '',
                'tracks': tracks,
                'service': 'yandex'
            })
        
        elif service == 'vk':
            vk_client = get_vk_client(user_id)
            if not vk_client:
                return jsonify({'error': 'Токен VK не настроен'}), 400
            
            try:
                playlist = vk_client.audio.getPlaylistById(playlist_id=playlist_id)
                tracks = vk_client.audio.get(playlist_id=playlist_id)
                
                track_list = []
                if 'items' in tracks:
                    for track in tracks['items']:
                        track_list.append({
                            'id': f"vk_{track['id']}",
                            'title': track['title'],
                            'artists': [track['artist']],
                            'album': track.get('album', {}).get('title', 'Unknown Album'),
                            'duration': track['duration'] * 1000,
                            'cover_uri': track.get('album', {}).get('thumb', {}).get('photo_300') if track.get('album') else None,
                            'year': track.get('year', 'Unknown'),
                            'service': 'vk'
                        })
                
                return jsonify({
                    'id': f"vk_{playlist['id']}",
                    'title': playlist['title'],
                    'track_count': playlist['count'],
                    'cover_uri': playlist['photo']['photo_300'] if playlist.get('photo') else None,
                    'description': playlist.get('description', ''),
                    'owner': f"id{playlist['owner_id']}",
                    'tracks': track_list,
                    'service': 'vk'
                })
            except Exception as e:
                logger.error(f"VK playlist error: {e}")
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Неизвестный сервис'}), 400
        
    except Exception as e:
        logger.error(f"Playlist error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/liked_tracks')
@login_required
def get_liked_tracks():
    try:
        user_id = get_current_user_id()
        service = get_current_music_service(user_id)
        
        tracks = []
        
        if service == 'yandex':
            client = get_yandex_client(user_id)
            if not client:
                return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
            
            liked_tracks = client.users_likes_tracks()
            
            for track_short in liked_tracks[:100]:
                try:
                    track = track_short.fetch_track()
                    cover_uri = None
                    if hasattr(track, 'cover_uri') and track.cover_uri:
                        cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
                    
                    tracks.append({
                        'id': f"yandex_{track.id}",
                        'title': track.title,
                        'artists': [artist.name for artist in track.artists],
                        'album': track.albums[0].title if track.albums else 'Unknown Album',
                        'duration': track.duration_ms,
                        'cover_uri': cover_uri,
                        'year': track.albums[0].year if track.albums and track.albums[0].year else 'Unknown',
                        'service': 'yandex'
                    })
                except Exception as e:
                    continue
        
        elif service == 'vk':
            vk_client = get_vk_client(user_id)
            if not vk_client:
                return jsonify({'error': 'Токен VK не настроен'}), 400
            
            try:
                liked_tracks = vk_client.audio.get(count=100)
                if 'items' in liked_tracks:
                    for track in liked_tracks['items']:
                        tracks.append({
                            'id': f"vk_{track['id']}",
                            'title': track['title'],
                            'artists': [track['artist']],
                            'album': track.get('album', {}).get('title', 'Unknown Album'),
                            'duration': track['duration'] * 1000,
                            'cover_uri': track.get('album', {}).get('thumb', {}).get('photo_300') if track.get('album') else None,
                            'year': track.get('year', 'Unknown'),
                            'service': 'vk'
                        })
            except Exception as e:
                logger.error(f"VK liked tracks error: {e}")
                return jsonify({'error': str(e)}), 500
        
        return jsonify(tracks)
    except Exception as e:
        logger.error(f"Liked tracks error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
@login_required
#@cache.cached(timeout=1800, key_prefix=lambda: f'stats_{session["user_id"]}')
def get_stats():
    try:
        user_id = get_current_user_id()
        service = get_current_music_service(user_id)
        
        if service == 'yandex':
            client = get_yandex_client(user_id)
            if not client:
                return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
            
            playlists = client.users_playlists_list()
            liked_tracks = client.users_likes_tracks()
            
            genre_stats = {}
            artist_stats = {}
            
            for track_short in liked_tracks[:50]:
                try:
                    track = track_short.fetch_track()
                    
                    if track.albums and track.albums[0].genre:
                        genre = track.albums[0].genre
                        genre_stats[genre] = genre_stats.get(genre, 0) + 1
                    
                    for artist in track.artists:
                        artist_name = artist.name
                        artist_stats[artist_name] = artist_stats.get(artist_name, 0) + 1
                        
                except:
                    continue
            
            top_artist = max(artist_stats.items(), key=lambda x: x[1], default=('Неизвестно', 0))
            top_genre = max(genre_stats.items(), key=lambda x: x[1], default=('Неизвестно', 0))
            
            stats = {
                'total_playlists': len(playlists),
                'total_liked_tracks': len(liked_tracks),
                'largest_playlist': max([p.track_count for p in playlists], default=0),
                'total_artists': len(artist_stats),
                'top_artist': top_artist[0],
                'top_genre': top_genre[0],
                'genre_stats': genre_stats,
                'artist_stats': dict(sorted(artist_stats.items(), key=lambda x: x[1], reverse=True)[:5])
            }
            
            return jsonify(stats)
        
        elif service == 'vk':
            vk_client = get_vk_client(user_id)
            if not vk_client:
                return jsonify({'error': 'Токен VK не настроен'}), 400
            
            try:
                liked_tracks = vk_client.audio.get(count=50)
                playlists = vk_client.audio.getPlaylists()
                
                if 'items' not in liked_tracks or 'items' not in playlists:
                    return jsonify({'error': 'Invalid VK response'}), 500
                
                genre_stats = {}
                artist_stats = {}
                
                for track in liked_tracks['items']:
                    artist = track['artist']
                    artist_stats[artist] = artist_stats.get(artist, 0) + 1
                
                top_artist = max(artist_stats.items(), key=lambda x: x[1], default=('Неизвестно', 0))
                
                stats = {
                    'total_playlists': playlists.get('count', 0),
                    'total_liked_tracks': liked_tracks.get('count', 0),
                    'largest_playlist': max([p['count'] for p in playlists['items']], default=0) if playlists['items'] else 0,
                    'total_artists': len(artist_stats),
                    'top_artist': top_artist[0],
                    'top_genre': 'Неизвестно',
                    'genre_stats': {},
                    'artist_stats': dict(sorted(artist_stats.items(), key=lambda x: x[1], reverse=True)[:5])
                }
                
                return jsonify(stats)
            except Exception as e:
                logger.error(f"VK stats error: {e}")
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Неизвестный сервис'}), 400
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/profile/equipped')
@login_required
def get_equipped_items():
    try:
        user = User.get_current()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        inventory = UserInventory.query.filter_by(
            user_id=user.id, equipped=True
        ).all()
        
        equipped_items = {}
        for inv_item in inventory:
            equipped_items[inv_item.item.type] = {
                'item_id': inv_item.item_id,
                'name': inv_item.item.name,
                'type': inv_item.item.type,
                'data': inv_item.item.get_data_dict(),
                'purchased_at': inv_item.purchased_at.isoformat() if inv_item.purchased_at else None
            }
        
        return jsonify(equipped_items)
    except Exception as e:
        logger.error(f"Equipped items error: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/search')
@login_required
def search():
    try:
        user_id = get_current_user_id()
        service = get_current_music_service(user_id)
        query = request.args.get('q', '')
        
        if not query:
            return jsonify({'error': 'Введите запрос'}), 400
        
        result = {'tracks': [], 'albums': [], 'artists': [], 'playlists': []}
        
        if service == 'yandex':
            client = get_yandex_client(user_id)
            if not client:
                return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
            
            search_result = client.search(query)
            
            if search_result.tracks:
                for track in search_result.tracks.results[:10]:
                    cover_uri = None
                    if hasattr(track, 'cover_uri') and track.cover_uri:
                        cover_uri = f"https://{track.cover_uri.replace('%%', '300x300')}"
                    
                    result['tracks'].append({
                        'id': f"yandex_{track.id}",
                        'title': track.title,
                        'artists': [artist.name for artist in track.artists],
                        'album': track.albums[0].title if track.albums else 'Unknown',
                        'duration': track.duration_ms,
                        'cover_uri': cover_uri,
                        'service': 'yandex'
                    })
            
            if search_result.albums:
                for album in search_result.albums.results[:5]:
                    cover_uri = None
                    if hasattr(album, 'cover_uri') and album.cover_uri:
                        cover_uri = f"https://{album.cover_uri.replace('%%', '300x300')}"
                    
                    result['albums'].append({
                        'id': f"yandex_{album.id}",
                        'title': album.title,
                        'artists': [artist.name for artist in album.artists],
                        'year': album.year,
                        'track_count': album.track_count,
                        'cover_uri': cover_uri,
                        'service': 'yandex'
                    })
            
            if search_result.artists:
                for artist in search_result.artists.results[:5]:
                    result['artists'].append({
                        'id': f"yandex_{artist.id}",
                        'name': artist.name,
                        'genres': artist.genres or [],
                        'service': 'yandex'
                    })
            
            if search_result.playlists:
                for playlist in search_result.playlists.results[:5]:
                    cover_uri = None
                    if hasattr(playlist, 'cover_uri') and playlist.cover_uri:
                        cover_uri = f"https://{playlist.cover_uri.replace('%%', '300x300')}"
                    
                    result['playlists'].append({
                        'id': f"yandex_{playlist.kind}",
                        'title': playlist.title,
                        'track_count': playlist.track_count,
                        'cover_uri': cover_uri,
                        'description': getattr(playlist, 'description', '') or '',
                        'service': 'yandex'
                    })
        
        elif service == 'vk':
            vk_client = get_vk_client(user_id)
            if not vk_client:
                return jsonify({'error': 'Токен VK не настроен'}), 400
            
            try:
                search_result = vk_client.audio.search(q=query, count=10)
                
                if 'items' in search_result:
                    for track in search_result['items']:
                        result['tracks'].append({
                            'id': f"vk_{track['id']}",
                            'title': track['title'],
                            'artists': [track['artist']],
                            'album': track.get('album', {}).get('title', 'Unknown'),
                            'duration': track['duration'] * 1000,
                            'cover_uri': track.get('album', {}).get('thumb', {}).get('photo_300') if track.get('album') else None,
                            'service': 'vk'
                        })
                
            except Exception as e:
                logger.error(f"VK search error: {e}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/play_track/<service>_<track_id>')
@login_required
def get_track_url(service, track_id):
    try:
        user_id = get_current_user_id()
        
        if service == 'yandex':
            client = get_yandex_client(user_id)
            if not client:
                return jsonify({'error': 'Токен Яндекс.Музыки не настроен'}), 400
            
            track = client.tracks(track_id)[0]
            
            download_info = track.get_download_info()
            
            if not download_info:
                return jsonify({'error': 'Не удалось получить информацию для скачивания'}), 404
            
            best_quality = max(download_info, key=lambda x: x.bitrate_in_kbps)
            download_url = best_quality.get_direct_link()
            
            track_data = {
                'title': track.title,
                'artists': [artist.name for artist in track.artists],
                'album': track.albums[0].title if track.albums else 'Unknown Album',
                'genre': track.albums[0].genre if track.albums and track.albums[0].genre else 'Unknown',
                'duration': track.duration_ms,
                'cover_uri': f"https://{track.cover_uri.replace('%%', '300x300')}" if track.cover_uri else None
            }
            
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute(
                'INSERT INTO listening_history (user_id, track_id, track_data) VALUES (?, ?, ?)',
                (user_id, f"yandex_{track_id}", json.dumps(track_data))
            )
            
            activity_data = json.dumps({
                'track': track.title,
                'artist': ', '.join([artist.name for artist in track.artists]),
                'track_id': f"yandex_{track_id}",
                'service': 'yandex'
            })
            cursor.execute(
                'INSERT INTO user_activity (user_id, activity_type, activity_data) VALUES (?, ?, ?)',
                (user_id, 'listen', activity_data)
            )
            
            db.commit()
            add_currency(user_id, 1, 'listen_track')
            
            return jsonify({
                'url': download_url,
                'title': track.title,
                'artists': [artist.name for artist in track.artists],
                'duration': track.duration_ms,
                'cover_uri': track_data['cover_uri'],
                'service': 'yandex'
            })
        
        elif service == 'vk':
            vk_client = get_vk_client(user_id)
            if not vk_client:
                return jsonify({'error': 'Токен VK не настроен'}), 400
            
            try:
                track_info = vk_client.audio.getById(audios=track_id)
                if not track_info or 'url' not in track_info[0]:
                    return jsonify({'error': 'Не удалось получить информацию о треке'}), 404
                
                track_data = track_info[0]
                
                db = get_db()
                cursor = db.cursor()
                
                vk_track_data = {
                    'title': track_data['title'],
                    'artists': [track_data['artist']],
                    'album': track_data.get('album', {}).get('title', 'Unknown Album'),
                    'genre': 'Unknown',
                    'duration': track_data['duration'] * 1000,
                    'cover_uri': track_data.get('album', {}).get('thumb', {}).get('photo_300') if track_data.get('album') else None
                }
                
                cursor.execute(
                    'INSERT INTO listening_history (user_id, track_id, track_data) VALUES (?, ?, ?)',
                    (user_id, f"vk_{track_id}", json.dumps(vk_track_data))
                )
                
                activity_data = json.dumps({
                    'track': track_data['title'],
                    'artist': track_data['artist'],
                    'track_id': f"vk_{track_id}",
                    'service': 'vk'
                })
                cursor.execute(
                    'INSERT INTO user_activity (user_id, activity_type, activity_data) VALUES (?, ?, ?)',
                    (user_id, 'listen', activity_data)
                )
                
                db.commit()
                
                return jsonify({
                    'url': track_data['url'],
                    'title': track_data['title'],
                    'artists': [track_data['artist']],
                    'duration': track_data['duration'] * 1000,
                    'cover_uri': track_data.get('album', {}).get('thumb', {}).get('photo_300') if track_data.get('album') else None,
                    'service': 'vk'
                })
                
            except Exception as e:
                logger.error(f"VK track error: {e}")
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Неизвестный сервис'}), 400
        
    except Exception as e:
        logger.error(f"Track URL error: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    db = get_db()
    cursor = db.cursor()
    user_id = get_current_user_id()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
        settings = cursor.fetchone()
        
        if settings:
            return jsonify({
                'theme': settings[1],
                'language': settings[2],
                'auto_play': bool(settings[3]),
                'show_explicit': bool(settings[4]),
                'music_service': settings[5]
            })
        return jsonify({})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_settings 
            (user_id, theme, language, auto_play, show_explicit, music_service)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('theme', 'dark'),
            data.get('language', 'ru'),
            data.get('auto_play', True),
            data.get('show_explicit', True),
            data.get('music_service', 'yandex')
        ))
        db.commit()
        
        return jsonify({'success': True})

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

@app.route('/api/force_resend_verification', methods=['POST'])
def force_resend_verification():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email обязателен'})
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Пользователь не найден'})
        
        verification_code = str(uuid.uuid4())[:6].upper()
        code_expires = datetime.now() + timedelta(minutes=10)
        
        cursor.execute(
            'UPDATE users SET verification_code = ?, verification_code_expires = ? WHERE email = ?',
            (verification_code, code_expires, email)
        )
        db.commit()
        
        if send_verification_email(email, verification_code):
            return jsonify({'success': True, 'message': 'Новый код отправлен на вашу почту'})
        else:
            return jsonify({'success': False, 'message': 'Ошибка отправки email'})
            
    except Exception as e:
        logger.error(f"Force resend error: {e}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'})

@app.route('/api/friends')
@login_required
def get_friends():
    try:
        user_id = get_current_user_id()
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
        ''', (user_id, user_id, user_id, user_id))
        
        friends = []
        for row in cursor.fetchall():
            friends.append({
                'id': row[0],
                'username': row[1],
                'display_name': row[2],
                'avatar_url': row[3],
                'status': row[4],
                'taste_match': row[5],
                'created_at': row[6],
                'direction': row[7]
            })
        
        return jsonify(friends)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/friends/add/<int:friend_id>', methods=['POST'])
@login_required
def add_friend(friend_id):
    try:
        user_id = get_current_user_id()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT * FROM friends 
            WHERE (user_id = ? AND friend_id = ?) 
            OR (user_id = ? AND friend_id = ?)
        ''', (user_id, friend_id, friend_id, user_id))
        
        existing = cursor.fetchone()
        if existing:
            return jsonify({'error': 'Уже есть запрос на дружбу'}), 400
        
        taste_match = 75
        
        cursor.execute('''
            INSERT INTO friends (user_id, friend_id, taste_match, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, friend_id, taste_match))
        
        db.commit()
        
        cursor.execute('''
            INSERT INTO user_activity (user_id, activity_type, activity_data)
            VALUES (?, 'friend', ?)
        ''', (user_id, json.dumps({'friend_id': friend_id})))
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Запрос отправлен'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/activity')
@login_required
def get_user_activity():
    try:
        user_id = get_current_user_id()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT activity_type, activity_data, created_at 
            FROM user_activity 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 20
        ''', (user_id,))
        
        activities = []
        for row in cursor.fetchall():
            activity_type, activity_data, created_at = row
            data = json.loads(activity_data) if activity_data else {}
            
            activity = {
                'type': activity_type,
                'timestamp': created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
            }
            
            if activity_type == 'listen':
                activity.update({
                    'track': data.get('track', 'Неизвестный трек'),
                    'artist': data.get('artist', 'Неизвестный артист'),
                    'track_id': data.get('track_id'),
                    'service': data.get('service', 'unknown')
                })
            elif activity_type == 'friend':
                activity['friend_id'] = data.get('friend_id')
            
            activities.append(activity)
        
        return jsonify(activities)
    except Exception as e:
        logger.error(f"User activity error: {e}")
        return jsonify([])

@app.route('/api/themes', methods=['GET', 'POST'])
@login_required
def user_themes():
    db = get_db()
    cursor = db.cursor()
    user_id = get_current_user_id()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM user_themes WHERE user_id = ?', (user_id,))
        themes = cursor.fetchall()
        
        # Стандартные пресеты
        default_themes = {
            'spotify': {
                'name': 'Spotify',
                'colors': {
                    'bgPrimary': '#121212',
                    'bgSecondary': '#181818',
                    'bgTertiary': '#282828',
                    'textPrimary': '#ffffff',
                    'textSecondary': '#b3b3b3',
                    'accent': '#1db954',
                    'success': '#1db954',
                    'warning': '#ffa726',
                    'danger': '#e74c3c'
                }
            },
            'youtube': {
                'name': 'YouTube Music',
                'colors': {
                    'bgPrimary': '#0f0f0f',
                    'bgSecondary': '#1f1f1f',
                    'bgTertiary': '#2d2d2d',
                    'textPrimary': '#ffffff',
                    'textSecondary': '#aaaaaa',
                    'accent': '#ff0000',
                    'success': '#4caf50',
                    'warning': '#ff9800',
                    'danger': '#f44336'
                }
            },
            'apple': {
                'name': 'Apple Music',
                'colors': {
                    'bgPrimary': '#000000',
                    'bgSecondary': '#1a1a1a',
                    'bgTertiary': '#2a2a2a',
                    'textPrimary': '#ffffff',
                    'textSecondary': '#999999',
                    'accent': '#fa243c',
                    'success': '#4cd964',
                    'warning': '#ffcc00',
                    'danger': '#ff3b30'
                }
            }
        }
        
        return jsonify({
            'customThemes': [{
                'id': t[0],
                'name': t[2],
                'colors': json.loads(t[3]),
                'background_url': t[4],
                'is_default': t[5]
            } for t in themes],
            'defaultThemes': default_themes
        })
    
    elif request.method == 'POST':
        data = request.get_json()

        if not data or 'name' not in data or 'colors' not in data:
            return jsonify({'success': False, 'error': 'Отсутствуют обязательные поля: name и colors'}), 400
        
        try:
            cursor.execute('''
                INSERT INTO user_themes (user_id, name, colors, background_url, is_default)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                data['name'],
                json.dumps(data['colors']),
                data.get('background_url'),
                data.get('is_default', False)
            ))
            db.commit()
            
            return jsonify({'success': True, 'theme_id': cursor.lastrowid})
        except Exception as e:
            logger.error(f"Theme creation error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/themes/<int:theme_id>', methods=['DELETE'])
@login_required
def delete_theme(theme_id):
    db = get_db()
    cursor = db.cursor()
    user_id = get_current_user_id()
    
    cursor.execute('DELETE FROM user_themes WHERE id = ? AND user_id = ?', (theme_id, user_id))
    db.commit()
    
    return jsonify({'success': True})

@app.route('/api/listening_history')
@login_required
def get_listening_history():
    try:
        user_id = get_current_user_id()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT track_data, played_at 
            FROM listening_history 
            WHERE user_id = ? 
            ORDER BY played_at DESC 
            LIMIT 10
        ''', (user_id,))
        
        history = []
        for row in cursor.fetchall():
            try:
                track_data = json.loads(row[0])
                track_data['played_at'] = row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1])
                history.append(track_data)
            except:
                continue
        
        return jsonify(history)
    except Exception as e:
        logger.error(f"Listening history error: {e}")
        return jsonify([])

@app.route('/api/daily_reward', methods=['POST'])
@login_required
def daily_reward():
    try:
        user_id = get_current_user_id()
        db = get_db()
        cursor = db.cursor()
        
        # Проверяем, получал ли пользователь награду сегодня
        cursor.execute('''
            SELECT created_at FROM currency_transactions 
            WHERE user_id = ? AND reason = 'daily_reward' 
            AND date(created_at) = date('now')
        ''', (user_id,))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Вы уже получали награду сегодня'})
        
        # Добавляем награду
        amount = random.randint(10, 25)
        if add_currency(user_id, amount, 'daily_reward'):
            return jsonify({'success': True, 'message': f'Получено {amount} монет!', 'amount': amount})
        else:
            return jsonify({'success': False, 'message': 'Ошибка выдачи награды'})
            
    except Exception as e:
        logger.error(f"Daily reward error: {e}")
        return jsonify({'success': False, 'message': 'Ошибка сервера'})

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/debug/tables')
def debug_tables():
    try:
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)