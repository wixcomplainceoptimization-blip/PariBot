import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://paribot.railway.app')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///paribot.db')
    
    INITIAL_BALANCE = 100
    MIN_BET = 1
    MAX_BET = 100
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'paribot-secret-key-2026')
    PORT = int(os.getenv('PORT', 8080))  # Changed to 8080 to match Railway
