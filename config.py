import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    # WebApp URL (your Railway deployed URL)
    WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://paribot.railway.app')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///paribot.db')
    
    # Game Settings
    INITIAL_BALANCE = 100
    MIN_BET = 1
    MAX_BET = 100
    
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'paribot-secret-key-2026')
    PORT = int(os.getenv('PORT', 5000))
