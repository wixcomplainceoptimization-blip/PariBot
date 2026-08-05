import requests
import json
import time
from datetime import datetime, timedelta
from cachetools import cached, TTLCache
from config import Config

# Cache to reduce API calls
cache = TTLCache(maxsize=100, ttl=Config.CACHE_TIMEOUT)

class OddsAPI:
    """Handles all API calls to The Odds API"""
    
    def __init__(self):
        self.api_key = Config.ODDS_API_KEY
        self.base_url = Config.ODDS_API_BASE_URL
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"⏳ Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    @cached(cache)
    def get_sports(self):
        """Get list of available sports"""
        self._rate_limit()
        url = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            print(f"📊 Sports API Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {len(data)} sports")
                return data
            else:
                print(f"❌ Sports API Error: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Error fetching sports: {e}")
            return []
    
    @cached(cache)
    def get_odds(self, sport='soccer', region='eu', markets='h2h'):
        """Get odds for a specific sport with better error handling"""
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/sports/{sport}/odds"
            params = {
                'apiKey': self.api_key,
                'region': region,
                'markets': markets,
                'dateFormat': 'iso'
            }
            
            print(f"🔍 Fetching odds from API...")
            response = self.session.get(url, params=params, timeout=15)
            print(f"📊 Odds API Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {len(data)} matches")
                return data
            elif response.status_code == 401:
                print("❌ Invalid API Key! Please check your ODDS_API_KEY")
                return []
            elif response.status_code == 429:
                print("⚠️ Rate limit hit! Waiting 5 seconds...")
                time.sleep(5)
                # Try one more time
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    return response.json()
                return []
            else:
                print(f"❌ API Error {response.status_code}: {response.text[:200]}")
                return []
                
        except requests.exceptions.Timeout:
            print("⚠️ API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON response: {e}")
            return []
    
    def get_predictions(self, matches):
        """Analyze matches and generate predictions with safe handling"""
        if not matches:
            print("⚠️ No matches provided for predictions")
            return []
        
        predictions = []
        
        for match in matches:
            try:
                # Skip if no bookmakers
                if not match.get('bookmakers'):
                    continue
                
                # Get the best odds for each outcome
                best_home = 0
                best_away = 0
                best_draw = 0
                
                for bookmaker in match['bookmakers']:
                    if bookmaker.get('key') not in Config.SUPPORTED_BOOKMAKERS:
                        continue
                    
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'h2h':
                            outcomes = market.get('outcomes', [])
                            for outcome in outcomes:
                                outcome_name = outcome.get('name', '')
                                price = outcome.get('price', 0)
                                
                                if outcome_name == match.get('home_team', ''):
                                    best_home = max(best_home, price)
                                elif outcome_name == match.get('away_team', ''):
                                    best_away = max(best_away, price)
                                elif outcome_name == 'Draw':
                                    best_draw = max(best_draw, price)
                
                # Calculate implied probabilities
                if best_home > 0 and best_away > 0 and best_draw > 0:
                    home_prob = (1 / best_home) * 100
                    draw_prob = (1 / best_draw) * 100
                    away_prob = (1 / best_away) * 100
                    
                    # Normalize to 100%
                    total = home_prob + draw_prob + away_prob
                    if total > 0:
                        home_prob = (home_prob / total) * 100
                        draw_prob = (draw_prob / total) * 100
                        away_prob = (away_prob / total) * 100
                    
                    # Determine prediction
                    outcomes = [
                        ('Home Win', home_prob, best_home),
                        ('Draw', draw_prob, best_draw),
                        ('Away Win', away_prob, best_away)
                    ]
                    outcomes.sort(key=lambda x: x[1], reverse=True)
                    
                    # Calculate confidence level
                    confidence = outcomes[0][1] - outcomes[1][1]
                    
                    predictions.append({
                        'match': f"{match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}",
                        'league': match.get('sport_title', 'Unknown League'),
                        'best_odds': {
                            'home': best_home,
                            'draw': best_draw,
                            'away': best_away
                        },
                        'probabilities': {
                            'home': round(home_prob, 1),
                            'draw': round(draw_prob, 1),
                            'away': round(away_prob, 1)
                        },
                        'prediction': outcomes[0][0],
                        'confidence': round(confidence, 1),
                        'commence_time': match.get('commence_time')
                    })
            
            except Exception as e:
                print(f"❌ Error analyzing match: {e}")
                continue
        
        # Sort by confidence (highest first)
        predictions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return predictions
    
    def format_prediction_message(self, prediction, index=0):
        """Format a single prediction for display with safe access"""
        try:
            emoji = '🏆' if index == 0 else '⭐'
            
            message = f"""
{emoji} *{prediction.get('match', 'Unknown Match')}*
📊 *League:* {prediction.get('league', 'Unknown League')}

*Best Odds:*
• Home: {prediction.get('best_odds', {}).get('home', 0):.2f}
• Draw: {prediction.get('best_odds', {}).get('draw', 0):.2f}
• Away: {prediction.get('best_odds', {}).get('away', 0):.2f}

*Probabilities:*
• Home: {prediction.get('probabilities', {}).get('home', 0)}%
• Draw: {prediction.get('probabilities', {}).get('draw', 0)}%
• Away: {prediction.get('probabilities', {}).get('away', 0)}%

🎯 *Prediction:* {prediction.get('prediction', 'Unknown')}
📈 *Confidence:* {prediction.get('confidence', 0)}%
"""
            
            if prediction.get('commence_time'):
                try:
                    start_time = datetime.fromisoformat(prediction['commence_time'].replace('Z', '+00:00'))
                    time_str = start_time.strftime('%Y-%m-%d %H:%M UTC')
                    message += f"\n⏰ *Match Time:* {time_str}"
                except:
                    pass
            
            return message
        except Exception as e:
            print(f"❌ Error formatting message: {e}")
            return "⚠️ Error formatting prediction"
