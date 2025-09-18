# migrate_database.py
from app import app, db
from models import UserInventory, ShopItem
import sqlite3
import os

def migrate_database():
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            if 'user_inventory' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('user_inventory')]
                
                if 'equipped_at' not in columns:
                    print("Adding equipped_at column to user_inventory...")
                    db.engine.execute('ALTER TABLE user_inventory ADD COLUMN equipped_at DATETIME')
                    print("Column equipped_at added successfully!")
                else:
                    print("Column equipped_at already exists")
        except Exception as e:
            print(f"Error checking user_inventory: {e}")

        try:
            if 'shop_items' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('shop_items')]
                
                if 'is_active' not in columns:
                    print("Adding is_active column to shop_items...")
                    db.engine.execute('ALTER TABLE shop_items ADD COLUMN is_active BOOLEAN DEFAULT TRUE')
                    print("Column is_active added successfully!")
                else:
                    print("Column is_active already exists")
        except Exception as e:
            print(f"Error checking shop_items: {e}")

        try:
            conn = sqlite3.connect('itired.db')
            cursor = conn.cursor()
            
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
            
            print("SQLite tables checked/created successfully!")
            
        except Exception as e:
            print(f"Error with SQLite tables: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == '__main__':
    migrate_database()