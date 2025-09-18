from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import session
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(80), nullable=True)
    avatar_url = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    yandex_token = db.Column(db.String(500), nullable=True)
    vk_token = db.Column(db.String(500), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6), nullable=True)
    verification_code_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    currency = db.relationship('UserCurrency', backref='user', uselist=False)
    inventory = db.relationship('UserInventory', backref='user')
    transactions = db.relationship('CurrencyTransaction', backref='user')

    @classmethod
    def get_current(cls):
        """Получить текущего авторизованного пользователя"""
        if 'user_id' in session:
            return cls.query.get(session['user_id'])
        return None

    @classmethod
    def get_by_username_or_email(cls, username_or_email):
        """Найти пользователя по username или email"""
        return cls.query.filter(
            (cls.username == username_or_email) | (cls.email == username_or_email)
        ).first()

    def check_password(self, password):
        """Проверить пароль"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def get_currency_balance(self):
        """Получить баланс валюты пользователя"""
        if self.currency:
            return self.currency.balance
        return 0

    def get_inventory(self):
        """Получить инвентарь пользователя"""
        return UserInventory.query.filter_by(user_id=self.id).all()

class UserCurrency(db.Model):
    __tablename__ = 'user_currency'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShopCategory(db.Model):
    __tablename__ = 'shop_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    
    items = db.relationship('ShopItem', backref='category')

class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('shop_categories.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text, nullable=True)
    rarity = db.Column(db.String(20), default='common')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    inventory = db.relationship('UserInventory', backref='item')

    def get_data_dict(self):
        """Получить данные предмета в виде словаря"""
        import json
        try:
            return json.loads(self.data) if self.data else {}
        except:
            return {}

class UserInventory(db.Model):
    __tablename__ = 'user_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    equipped = db.Column(db.Boolean, default=False)

class CurrencyTransaction(db.Model):
    __tablename__ = 'currency_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

