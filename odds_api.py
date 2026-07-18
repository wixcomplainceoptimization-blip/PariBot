import requests
import json
import time
from datetime import datetime, timedelta
from cachetools import cached, TTLCache
from config import Config

cache = TTLCache(maxsize=200, ttl=Config.CACHE_TIMEOUT)

class OddsAPI:
    """Enhanced API handler for PariBot"""
    
    def __init__(self):
        self.api_key = Config.ODDS_API_KEY
        self.base_url = Config.ODDS_API_BASE_URL
        self.session = requests.Session()
        self.sport_mapping = Config.SPORT_MAPPING
    
    @cached(cache)
    def get_sports(self):
        """Get list of available sports"""
        url = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching sports: {e}")
            return []
    
    def get_odds(self, sport='soccer', region='eu', markets='h2h,spreads,totals'):
        """Get odds for a specific sport with multiple markets"""
        try:
            url = f"{self.base_url}/sports/{sport}/odds"
            params = {
                'apiKey': self.api_key,
                'region': region,
                'markets': markets,
                'dateFormat': 'iso'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                time.sleep(5)
                response = self.session.get(url, params=params, timeout=15)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error fetching odds: {e}")
            return []
    
    def get_all_sports_odds(self):
        """Get odds for all configured sports"""
        all_matches = []
        for sport in Config.SPORTS:
            api_sport = self.sport_mapping.get(sport, sport)
            matches = self.get_odds(api_sport, Config.DEFAULT_REGION)
            if matches:
                all_matches.extend(matches)
            time.sleep(0.5)  # Rate limiting
        return all_matches
    
    def analyze_match(self, match):
        """Analyze a single match and return prediction"""
        try:
            if not match.get('bookmakers'):
                return None
            
            best_home = 0
            best_away = 0
            best_draw = 0
            best_spread = None
            best_total = None
            
            for bookmaker in match['bookmakers']:
                if bookmaker['key'] not in Config.SUPPORTED_BOOKMAKERS:
                    continue
                
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'h2h':
                        outcomes = market.get('outcomes', [])
                        for outcome in outcomes:
                            name = outcome.get('name', '')
                            price = outcome.get('price', 0)
                            
                            if name == match.get('home_team', ''):
                                best_home = max(best_home, price)
                            elif name == match.get('away_team', ''):
                                best_away = max(best_away, price)
                            elif name == 'Draw':
                                best_draw = max(best_draw, price)
                    
                    elif market['key'] == 'spreads' and not best_spread:
                        outcomes = market.get('outcomes', [])
                        if len(outcomes) >= 2:
                            best_spread = {
                                'home': outcomes[0].get('point', 0),
                                'home_odds': outcomes[0].get('price', 0),
                                'away': outcomes[1].get('point', 0),
                                'away_odds': outcomes[1].get('price', 0)
                            }
                    
                    elif market['key'] == 'totals' and not best_total:
                        outcomes = market.get('outcomes', [])
                        if len(outcomes) >= 2:
                            best_total = {
                                'over': outcomes[0].get('point', 0),
                                'over_odds': outcomes[0].get('price', 0),
                                'under': outcomes[1].get('point', 0),
                                'under_odds': outcomes[1].get('price', 0)
                            }
            
            # Calculate probabilities
            if best_home > 0 and best_away > 0 and best_draw > 0:
                total_prob = (1/best_home) + (1/best_draw) + (1/best_away)
                home_prob = (1/best_home) / total_prob * 100
                draw_prob = (1/best_draw) / total_prob * 100
                away_prob = (1/best_away) / total_prob * 100
                
                outcomes = [
                    ('Home Win', home_prob, best_home),
                    ('Draw', draw_prob, best_draw),
                    ('Away Win', away_prob, best_away)
                ]
                outcomes.sort(key=lambda x: x[1], reverse=True)
                
                confidence = outcomes[0][1] - outcomes[1][1]
                
                # Determine value bet
                value_bet = None
                if outcomes[0][1] > 50 and outcomes[0][2] > 2.0:
                    value_bet = outcomes[0][0]
                
                return {
                    'match_id': match.get('id', ''),
                    'league': match.get('sport_title', 'Unknown'),
                    'home_team': match.get('home_team', ''),
                    'away_team': match.get('away_team', ''),
                    'prediction': outcomes[0][0],
                    'confidence': round(confidence, 1),
                    'probabilities': {
                        'home': round(home_prob, 1),
                        'draw': round(draw_prob, 1),
                        'away': round(away_prob, 1)
                    },
                    'best_odds': {
                        'home': best_home,
                        'draw': best_draw,
                        'away': best_away
                    },
                    'spread': best_spread,
                    'total': best_total,
                    'value_bet': value_bet,
                    'commence_time': match.get('commence_time'),
                    'sport': match.get('sport_key', '')
                }
            
            return None
            
        except Exception as e:
            print(f"Error analyzing match: {e}")
            return None
    
    def get_predictions(self, matches, sport_filter=None):
        """Get predictions for all matches"""
        predictions = []
        for match in matches:
            # Apply sport filter if specified
            if sport_filter and match.get('sport_key', '') != sport_filter:
                continue
                
            pred = self.analyze_match(match)
            if pred:
                predictions.append(pred)
        
        # Sort by confidence
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return predictions
    
    def format_prediction(self, prediction):
        """Format prediction for display with enhanced UI"""
        emoji = '🏆' if prediction['confidence'] > 15 else '⭐'
        
        # Sport emoji
        sport_emoji = Config.SPORT_EMOJIS.get(prediction.get('sport', ''), '⚽')
        
        message = f"""
{sport_emoji} *{prediction['match']}*
📊 *League:* {prediction['league']}

*Best Odds:*
🏠 Home: {prediction['best_odds']['home']:.2f}
🤝 Draw: {prediction['best_odds']['draw']:.2f}
✈️ Away: {prediction['best_odds']['away']:.2f}

*Probabilities:*
🏠 Home: {prediction['probabilities']['home']}%
🤝 Draw: {prediction['probabilities']['draw']}%
✈️ Away: {prediction['probabilities']['away']}%

🎯 *Prediction:* {prediction['prediction']}
📈 *Confidence:* {prediction['confidence']}% {emoji}
"""
        
        # Add spread info
        if prediction.get('spread'):
            spread = prediction['spread']
            message += f"\n📊 *Spread:* {spread['home']:.1f} ({spread['home_odds']:.2f}) / {spread['away']:.1f} ({spread['away_odds']:.2f})"
        
        # Add total info
        if prediction.get('total'):
            total = prediction['total']
            message += f"\n📈 *Total:* O{total['over']:.1f} ({total['over_odds']:.2f}) / U{total['under']:.1f} ({total['under_odds']:.2f})"
        
        # Add value bet indicator
        if prediction.get('value_bet'):
            message += f"\n💰 *Value Bet:* {prediction['value_bet']} 👀"
        
        # Add match time
        if prediction.get('commence_time'):
            try:
                start_time = datetime.fromisoformat(prediction['commence_time'].replace('Z', '+00:00'))
                time_str = start_time.strftime('%Y-%m-%d %H:%M UTC')
                message += f"\n⏰ *Match Time:* {time_str}"
            except:
                pass
        
        return message
