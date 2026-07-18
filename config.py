import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for PariBot"""
    
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    # API Configuration
    ODDS_API_KEY = os.getenv('ODDS_API_KEY')
    if not ODDS_API_KEY:
        raise ValueError("ODDS_API_KEY not found in environment variables")
    
    ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Sports Configuration
    SPORTS = os.getenv('SPORTS', 'football,basketball,tennis,baseball').split(',')
    SPORT_MAPPING = {
        'football': 'soccer',
        'basketball': 'basketball',
        'tennis': 'tennis',
        'baseball': 'baseball'
    }
    
    # Region
    DEFAULT_REGION = os.getenv('DEFAULT_REGION', 'eu')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///paribot.db')
    
    # Bot Settings
    REFRESH_INTERVAL = int(os.getenv('REFRESH_INTERVAL', '300'))
    MAX_PREDICTIONS_DISPLAY = 5
    CACHE_TIMEOUT = 60
    
    # League Name Mappings
    LEAGUE_NAMES = {
        'england_premier_league': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League',
        'spain_la_liga': '🇪🇸 La Liga',
        'italy_serie_a': '🇮🇹 Serie A',
        'germany_bundesliga': '🇩🇪 Bundesliga',
        'france_ligue_one': '🇫🇷 Ligue 1',
        'netherlands_eredivisie': '🇳🇱 Eredivisie',
        'portugal_primeira_liga': '🇵🇹 Primeira Liga',
        'brazil_campeonato': '🇧🇷 Brasileirão',
        'usa_nba': '🏀 NBA',
        'usa_ncaa_basketball': '🏀 NCAA Basketball',
        'france_top14': '🏉 Top 14',
        'england_premier_league_rugby': '🏉 Premiership Rugby',
        'atp': '🎾 ATP Tennis',
        'wta': '🎾 WTA Tennis',
        'mlb': '⚾ MLB'
    }
    
    # Supported Bookmakers
    SUPPORTED_BOOKMAKERS = ['pinnacle', 'bet365', 'williamhill', 'unibet', 'betfair']
    
    # Emoji mappings
    SPORT_EMOJIS = {
        'soccer': '⚽',
        'football': '⚽',
        'basketball': '🏀',
        'tennis': '🎾',
        'baseball': '⚾',
        'rugby': '🏉'
    }
    
    OUTCOME_EMOJIS = {
        'home_win': '🏠',
        'away_win': '✈️',
        'draw': '🤝'
    }
