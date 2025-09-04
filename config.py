import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    YANDEX_TOKEN = os.getenv('YANDEX_MUSIC_TOKEN')
    DEBUG = os.getenv('DEBUG', False)