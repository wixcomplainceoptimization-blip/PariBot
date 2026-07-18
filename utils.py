import re
from datetime import datetime
from typing import List, Dict, Any

class Utils:
    """Enhanced helper functions for PariBot"""
    
    @staticmethod
    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value, default=0):
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def extract_league(text):
        """Extract league from text with better matching"""
        text_lower = text.lower()
        
        # More comprehensive league mapping
        league_patterns = {
            'premier': 'england_premier_league',
            'epl': 'england_premier_league',
            'la liga': 'spain_la_liga',
            'laliga': 'spain_la_liga',
            'serie a': 'italy_serie_a',
            'bundesliga': 'germany_bundesliga',
            'ligue 1': 'france_ligue_one',
            'eredivisie': 'netherlands_eredivisie',
            'primeira': 'portugal_primeira_liga',
            'brasileirão': 'brazil_campeonato',
            'nba': 'usa_nba',
            'mlb': 'mlb',
            'atp': 'atp',
            'wta': 'wta'
        }
        
        for pattern, league in league_patterns.items():
            if pattern in text_lower:
                return league
        
        return None
    
    @staticmethod
    def extract_sport(text):
        """Extract sport from text"""
        text_lower = text.lower()
        
        sports = {
            'football': 'football',
            'soccer': 'football',
            'basketball': 'basketball',
            'bball': 'basketball',
            'tennis': 'tennis',
            'baseball': 'baseball'
        }
        
        for keyword, sport in sports.items():
            if keyword in text_lower:
                return sport
        
        return None
    
    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        """Format datetime for display"""
        return dt.strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def calculate_profit(odds: float, stake: float) -> float:
        """Calculate potential profit from bet"""
        return (odds - 1) * stake
    
    @staticmethod
    def is_valid_amount(text: str) -> bool:
        """Check if text is a valid amount"""
        try:
            amount = float(text)
            return amount > 0
        except:
            return False
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + '...'
    
    @staticmethod
    def create_keyboard(buttons: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Create a keyboard layout from buttons"""
        keyboard = []
        row = []
        for i, button in enumerate(buttons):
            row.append(button)
            if len(row) == 2 or i == len(buttons) - 1:
                keyboard.append(row)
                row = []
        return keyboard
