import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    ODDS_API_KEY = os.getenv('ODDS_API_KEY')
    if not ODDS_API_KEY:
        raise ValueError("ODDS_API_KEY not found in environment variables")
    
    ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Betting settings
    INITIAL_BALANCE = 100
    MIN_BET = 1
    MAX_BET = 100
    
    # Supported leagues
    LEAGUES = {
        'epl': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League',
        'laliga': '🇪🇸 La Liga',
        'seriea': '🇮🇹 Serie A',
        'bundesliga': '🇩🇪 Bundesliga',
        'ligue1': '🇫🇷 Ligue 1',
    }
